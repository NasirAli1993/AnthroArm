"""Actual ROS 2 interfaces to the local simulated arm; no physical commands."""
import os, json, time, base64, threading, urllib.request, argparse
os.environ.setdefault('ROS_LOCALHOST_ONLY','1')
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, GoalResponse, CancelResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from sensor_msgs.msg import JointState, CompressedImage, Image, CameraInfo
from std_msgs.msg import String
from std_srvs.srv import Trigger
from control_msgs.action import FollowJointTrajectory
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster
from rosgraph_msgs.msg import Clock
from builtin_interfaces.msg import Time


class Backend:
    def __init__(self,url):self.url=url.rstrip('/')
    def get(self,path):
        with urllib.request.urlopen(self.url+path,timeout=4) as r:return json.load(r)
    def command(self,body):
        req=urllib.request.Request(self.url+'/command',data=json.dumps(body,allow_nan=False).encode(),headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)


class ArmBridge(Node):
    def __init__(self,url):
        super().__init__('anthro_sim_bridge');self.backend=Backend(url);self.group=ReentrantCallbackGroup();self.busy=threading.Lock()
        self.joints=self.create_publisher(JointState,'/joint_states',10)
        self.status=self.create_publisher(String,'/anthro/status',10)
        self.rgb=self.create_publisher(CompressedImage,'/camera/color/image_raw/compressed',2)
        self.depth=self.create_publisher(Image,'/camera/depth/image_raw',2)
        self.info=self.create_publisher(CameraInfo,'/camera/color/camera_info',2)
        self.clock_pub=self.create_publisher(Clock,'/clock',10);self.tf=TransformBroadcaster(self)
        self.create_timer(.05,self.publish_state,callback_group=self.group)
        self.create_timer(1.,self.publish_camera,callback_group=self.group)
        self.service_handles=[]
        for op in ('stop','reset','vision_reach','learned_grasp'):
            self.service_handles.append(self.create_service(Trigger,'/anthro/'+op,self.service_handler(op),callback_group=self.group))
        self.action=ActionServer(self,FollowJointTrajectory,'/arm_controller/follow_joint_trajectory',execute_callback=self.execute,
                                 goal_callback=self.goal,cancel_callback=lambda _:CancelResponse.ACCEPT,callback_group=self.group)
        self.latest={};self.get_logger().info('SIMULATION ONLY: ROS 2 arm bridge ready')
    def service_handler(self,op):
        def handler(req,res):
            try:res.message=json.dumps(self.backend.command({'op':op}));res.success=True
            except Exception as exc:res.message=str(exc);res.success=False
            return res
        return handler
    def publish_state(self):
        try:
            state=self.backend.get('/state');self.latest=state
            if not state.get('joints'):return
            stamp=Time(sec=int(state['time']),nanosec=int((state['time']%1)*1e9))
            clock=Clock();clock.clock=stamp;self.clock_pub.publish(clock)
            msg=JointState();msg.header.stamp=stamp;msg.header.frame_id='world'
            msg.name=[j['name'] for j in state['joints']];msg.position=[j['q'] for j in state['joints']]
            msg.velocity=[j['velocity'] for j in state['joints']];msg.effort=[j['torque'] for j in state['joints']];self.joints.publish(msg)
            status=String();status.data=json.dumps({'mode':state['mode'],'task':state['task'],'task_result':state.get('task_result',{}),
                                                   'grasp':state.get('grasp'),'trajectory':state['trajectory'],'time':state['time']});self.status.publish(status)
            transforms=[]
            for body in state['bodies']:
                if body['name']=='object':continue
                transform=TransformStamped();transform.header.stamp=stamp;transform.header.frame_id='world';transform.child_frame_id=body['name']
                transform.transform.translation.x,transform.transform.translation.y,transform.transform.translation.z=body['position']
                q=body['quaternion'];transform.transform.rotation.x=q[1];transform.transform.rotation.y=q[2];transform.transform.rotation.z=q[3];transform.transform.rotation.w=q[0];transforms.append(transform)
            self.tf.sendTransform(transforms)
        except Exception as exc:self.get_logger().warning('Backend state unavailable: '+str(exc),throttle_duration_sec=5)
    def publish_camera(self):
        try:
            c=self.backend.get('/camera')
            if not c:return
            rgb=CompressedImage();rgb.header.stamp=Time(sec=int(c['time']),nanosec=int((c['time']%1)*1e9));rgb.header.frame_id=c['frame_id'];rgb.format='jpeg';rgb.data=base64.b64decode(c['jpeg']);self.rgb.publish(rgb)
            depth=Image();depth.header=rgb.header;depth.height=c['height'];depth.width=c['width'];depth.encoding='32FC1';depth.is_bigendian=0;depth.step=c['width']*4;depth.data=base64.b64decode(c['depth_f32']);self.depth.publish(depth)
            info=CameraInfo();info.header=rgb.header;info.width=c['width'];info.height=c['height'];info.distortion_model='plumb_bob';info.d=[0.]*5
            info.k=[c['fx'],0.,c['cx'],0.,c['fy'],c['cy'],0.,0.,1.];info.r=[1.,0.,0.,0.,1.,0.,0.,0.,1.]
            info.p=[c['fx'],0.,c['cx'],0.,0.,c['fy'],c['cy'],0.,0.,0.,1.,0.];self.info.publish(info)
            tf=TransformStamped();tf.header.stamp=rgb.header.stamp;tf.header.frame_id='world';tf.child_frame_id=c['frame_id']
            tf.transform.translation.x,tf.transform.translation.y,tf.transform.translation.z=c['position']
            tf.transform.rotation.x,tf.transform.rotation.y,tf.transform.rotation.z,tf.transform.rotation.w=c['optical_quaternion_xyzw'];self.tf.sendTransform(tf)
        except Exception as exc:self.get_logger().warning('Camera unavailable: '+str(exc),throttle_duration_sec=5)
    def goal(self,request):
        if self.busy.locked() or not request.trajectory.points:return GoalResponse.REJECT
        # Only position trajectories are implemented; reject unsupported fields.
        for point in request.trajectory.points:
            if point.velocities or point.accelerations or point.effort:return GoalResponse.REJECT
        if request.path_tolerance or request.goal_tolerance:return GoalResponse.REJECT
        if request.component_path_tolerance or request.component_goal_tolerance:return GoalResponse.REJECT
        multi=request.multi_dof_trajectory
        if multi.joint_names or multi.points or multi.header.frame_id or multi.header.stamp.sec or multi.header.stamp.nanosec:
            return GoalResponse.REJECT
        if request.trajectory.header.stamp.sec or request.trajectory.header.stamp.nanosec:return GoalResponse.REJECT
        if request.goal_time_tolerance.sec or request.goal_time_tolerance.nanosec:return GoalResponse.REJECT
        return GoalResponse.ACCEPT
    def execute(self,handle):
        result=FollowJointTrajectory.Result()
        if not self.busy.acquire(blocking=False):
            handle.abort();result.error_code=result.INVALID_GOAL;result.error_string='Another trajectory is active';return result
        try:
            tr=handle.request.trajectory
            points=[{'time':p.time_from_start.sec+p.time_from_start.nanosec/1e9,'positions':list(p.positions)} for p in tr.points]
            started=self.backend.command({'op':'trajectory','joint_names':list(tr.joint_names),'points':points});ident=started['id'];deadline=time.monotonic()+max(30,points[-1]['time']*5+15)
            while time.monotonic()<deadline:
                if handle.is_cancel_requested:
                    self.backend.command({'op':'stop'});handle.canceled();result.error_code=0;result.error_string='Cancelled and held';return result
                state=self.backend.get('/state');status=state.get('trajectory',{})
                if status.get('id')==ident and status.get('status')=='succeeded':handle.succeed();result.error_code=0;return result
                if status.get('id',0)>ident or (status.get('id')==ident and status.get('status') in ('failed','cancelled')):
                    handle.abort();result.error_code=result.GOAL_TOLERANCE_VIOLATED;result.error_string=json.dumps(status);return result
                actual={j['name']:j['q'] for j in state['joints']};fb=FollowJointTrajectory.Feedback();fb.joint_names=list(tr.joint_names);fb.actual.positions=[actual[n] for n in tr.joint_names];handle.publish_feedback(fb)
                time.sleep(.05)
            self.backend.command({'op':'stop'});handle.abort();result.error_code=result.GOAL_TOLERANCE_VIOLATED;result.error_string='Execution timed out';return result
        except Exception as exc:
            handle.abort();result.error_code=result.INVALID_GOAL;result.error_string=str(exc);return result
        finally:self.busy.release()


def main():
    p=argparse.ArgumentParser();p.add_argument('--backend',default='http://127.0.0.1:8770');args,rosargs=p.parse_known_args()
    rclpy.init(args=rosargs);node=ArmBridge(args.backend);executor=MultiThreadedExecutor(num_threads=4);executor.add_node(node)
    try:executor.spin()
    finally:executor.shutdown();node.destroy_node();rclpy.shutdown()
if __name__=='__main__':main()
