"""Actual rclpy topics/services/actions for the separate simulated mobile base."""
import os,json,math,time,threading,urllib.request,argparse
os.environ.setdefault('ROS_LOCALHOST_ONLY','1')
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.qos import QoSProfile,DurabilityPolicy,ReliabilityPolicy
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry,OccupancyGrid
from geometry_msgs.msg import Twist,PoseStamped,TransformStamped
from std_msgs.msg import String
from std_srvs.srv import Trigger
from builtin_interfaces.msg import Time
from rosgraph_msgs.msg import Clock
from tf2_ros import TransformBroadcaster
try:
    from nav2_msgs.action import NavigateToPose
    from rclpy.action import ActionServer,GoalResponse,CancelResponse
except ImportError:NavigateToPose=None

def quat_yaw(pose):
    q=pose.orientation
    norm=q.x*q.x+q.y*q.y+q.z*q.z+q.w*q.w
    if norm<1e-10:return None
    if abs(norm-1)>.01:raise ValueError('Goal quaternion must be unit length or all zero for no heading constraint')
    if abs(q.x)>.001 or abs(q.y)>.001:raise ValueError('The base accepts planar yaw goals only')
    return math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))

class MobileBridge(Node):
    def __init__(self,url):
        super().__init__('mobile_navigation_bridge');self.url=url.rstrip('/');self.group=ReentrantCallbackGroup();self.busy=threading.Lock();self.latest={};self.last_stamp=None;self.counts={'state_publications':0,'scans':0,'cmd_vel_received':0,'goals_received':0}
        self.scan=self.create_publisher(LaserScan,'/scan',10);self.odom=self.create_publisher(Odometry,'/odom',10)
        mapqos=QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL,reliability=ReliabilityPolicy.RELIABLE)
        self.map=self.create_publisher(OccupancyGrid,'/map',mapqos);self.status=self.create_publisher(String,'/mobile/status',10)
        self.clock=self.create_publisher(Clock,'/mobile/clock',10);self.tf=TransformBroadcaster(self)
        self.create_subscription(Twist,'/cmd_vel',self.velocity,10,callback_group=self.group)
        self.create_subscription(PoseStamped,'/goal_pose',self.pose_goal,10,callback_group=self.group)
        self.service_handles=[self.create_service(Trigger,'/mobile/'+name,self.service(op),callback_group=self.group) for name,op in [('run_mission','mission'),('stop','stop'),('reset','reset')]]
        self.timer=self.create_timer(.1,self.publish,callback_group=self.group)
        self.action=None
        if NavigateToPose is not None:
            self.action=ActionServer(self,NavigateToPose,'/navigate_to_pose',execute_callback=self.execute,goal_callback=self.accept_goal,cancel_callback=lambda _:CancelResponse.ACCEPT,callback_group=self.group)
        self.get_logger().info('Simulation-only mobile bridge ready; custom ICP/A*, not Nav2. NavigateToPose interface available: '+str(self.action is not None))
    def get(self):
        with urllib.request.urlopen(self.url+'/state',timeout=3) as response:return json.load(response)
    def command(self,body):
        request=urllib.request.Request(self.url+'/command',data=json.dumps(body,allow_nan=False).encode(),headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(request,timeout=4) as response:return json.load(response)
    def service(self,op):
        def handler(_,response):
            try:response.message=json.dumps(self.command({'op':op}));response.success=True
            except Exception as exc:response.message=str(exc);response.success=False
            return response
        return handler
    def velocity(self,msg):
        try:
            if any(abs(x)>1e-9 for x in (msg.linear.y,msg.linear.z,msg.angular.x,msg.angular.y)):raise ValueError('Only linear.x and angular.z are supported')
            self.command({'op':'cmd_vel','v':float(msg.linear.x),'w':float(msg.angular.z)});self.counts['cmd_vel_received']+=1
        except Exception as exc:self.get_logger().warning('Velocity rejected: '+str(exc))
    def goal_command(self,pose):
        if pose.header.frame_id not in ('','mobile_map'):raise ValueError('Goal must be in mobile_map')
        if abs(pose.pose.position.z)>.01:raise ValueError('Goal z must be zero in the planar map')
        return {'op':'goal','goal':[float(pose.pose.position.x),float(pose.pose.position.y)],'yaw':quat_yaw(pose.pose)}
    def pose_goal(self,msg):
        try:self.command(self.goal_command(msg));self.counts['goals_received']+=1
        except Exception as exc:self.get_logger().warning('Goal rejected: '+str(exc))
    @staticmethod
    def transform(stamp,parent,child,x,y,z,yaw):
        tr=TransformStamped();tr.header.stamp=stamp;tr.header.frame_id=parent;tr.child_frame_id=child
        tr.transform.translation.x=float(x);tr.transform.translation.y=float(y);tr.transform.translation.z=float(z)
        tr.transform.rotation.z=math.sin(yaw/2);tr.transform.rotation.w=math.cos(yaw/2);return tr
    def publish(self):
        try:
            state=self.get();self.latest=state
            if not state.get('ready') or state['time']==self.last_stamp:return
            self.last_stamp=state['time'];stamp=Time(sec=int(state['time']),nanosec=int((state['time']%1)*1e9))
            scan=LaserScan();scan.header.stamp=stamp;scan.header.frame_id='mobile_laser';source=state['scan']
            scan.angle_min=float(source['angle_min']);scan.angle_increment=float(source['angle_increment']);scan.angle_max=scan.angle_min+(len(source['ranges'])-1)*scan.angle_increment
            scan.range_min=float(source['range_min']);scan.range_max=float(source['range_max']);scan.scan_time=.1;scan.time_increment=0.;scan.ranges=[float(v) for v in source['ranges']];self.scan.publish(scan);self.counts['scans']+=1
            pose=state['wheel_odometry'];odom=Odometry();odom.header.stamp=stamp;odom.header.frame_id='mobile_odom';odom.child_frame_id='mobile_base_link'
            odom.pose.pose.position.x=float(pose[0]);odom.pose.pose.position.y=float(pose[1]);odom.pose.pose.position.z=.162
            odom.pose.pose.orientation.z=math.sin(pose[2]/2);odom.pose.pose.orientation.w=math.cos(pose[2]/2)
            odom.twist.twist.linear.x=float(state['wheel_twist']['linear_x']);odom.twist.twist.angular.z=float(state['wheel_twist']['angular_z']);self.odom.publish(odom)
            grid=OccupancyGrid();grid.header.stamp=stamp;grid.header.frame_id='mobile_map';grid.info.resolution=float(state['map_resolution']);grid.info.height=len(state['map']);grid.info.width=len(state['map'][0]);grid.info.origin.position.x=float(state['map_origin'][0]);grid.info.origin.position.y=float(state['map_origin'][1]);grid.info.origin.orientation.w=1.;grid.data=[int(c) for row in state['map'] for c in row];self.map.publish(grid)
            estimate=state['estimated_pose'];yaw=estimate[2]-pose[2];c,s=math.cos(yaw),math.sin(yaw)
            tx=estimate[0]-(c*pose[0]-s*pose[1]);ty=estimate[1]-(s*pose[0]+c*pose[1])
            self.tf.sendTransform([self.transform(stamp,'mobile_map','mobile_odom',tx,ty,0.,yaw),self.transform(stamp,'mobile_odom','mobile_base_link',pose[0],pose[1],.162,pose[2]),self.transform(stamp,'mobile_base_link','mobile_laser',0.,0.,.12,0.)])
            clock=Clock();clock.clock=stamp;self.clock.publish(clock)
            status=String();status.data=json.dumps({'time':state['time'],'mode':state['mode'],'task':state['task'],'estimated_pose':estimate,'cmd_vel':state['cmd_vel'],'contacts':state['environment_contact_steps'],'bridge_counts':self.counts,'nav2_stack_used':False,'navigate_to_pose_interface':self.action is not None});self.status.publish(status);self.counts['state_publications']+=1
        except Exception as exc:self.get_logger().warning('Navigation backend unavailable: '+str(exc),throttle_duration_sec=5)
    def accept_goal(self,request):
        try:
            if self.busy.locked() or request.behavior_tree:return GoalResponse.REJECT
            self.goal_command(request.pose);return GoalResponse.ACCEPT
        except Exception:return GoalResponse.REJECT
    def execute(self,handle):
        result=NavigateToPose.Result()
        if not self.busy.acquire(False):handle.abort();return result
        try:
            response=self.command(self.goal_command(handle.request.pose));identifier=response['id'];self.counts['goals_received']+=1;deadline=time.monotonic()+150
            while time.monotonic()<deadline:
                if handle.is_cancel_requested:self.command({'op':'stop'});handle.canceled();return result
                state=self.get();task=state.get('task',{})
                if task.get('id')==identifier and task.get('status')=='succeeded':handle.succeed();return result
                if task.get('id',0)>identifier or task.get('status') in ('failed','cancelled'):handle.abort();return result
                feedback=NavigateToPose.Feedback();feedback.distance_remaining=float(math.hypot(state['estimated_pose'][0]-handle.request.pose.pose.position.x,state['estimated_pose'][1]-handle.request.pose.pose.position.y));handle.publish_feedback(feedback);time.sleep(.1)
            self.command({'op':'stop'});handle.abort();return result
        except Exception as exc:self.get_logger().warning(str(exc));handle.abort();return result
        finally:self.busy.release()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--backend',default='http://127.0.0.1:8771');args,rosargs=parser.parse_known_args()
    rclpy.init(args=rosargs);node=MobileBridge(args.backend);executor=MultiThreadedExecutor(num_threads=4);executor.add_node(node)
    try:executor.spin()
    finally:executor.shutdown();node.destroy_node();rclpy.shutdown()
