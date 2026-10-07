"""End-to-end test through real DDS topics/services to physical navigation."""
from pathlib import Path
import time,json,math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import Odometry,OccupancyGrid
from geometry_msgs.msg import Twist,PoseStamped
from std_msgs.msg import String
from std_srvs.srv import Trigger
from tf2_msgs.msg import TFMessage
OUT=Path(r'D:\RoboticArm\results\integration\navigation')

class TestNode(Node):
    def __init__(self):
        super().__init__('navigation_pipeline_validation');self.scan=None;self.odom=None;self.map=None;self.status=None;self.transforms=set();self.received={'scan':0,'odom':0,'map':0,'status':0}
        self.create_subscription(LaserScan,'/scan',lambda m:self.receive('scan',m),10)
        self.create_subscription(Odometry,'/odom',lambda m:self.receive('odom',m),10)
        self.create_subscription(OccupancyGrid,'/map',lambda m:self.receive('map',m),10)
        self.create_subscription(String,'/mobile/status',lambda m:self.receive('status',json.loads(m.data)),10)
        self.create_subscription(TFMessage,'/tf',self.tf,20)
        self.cmd=self.create_publisher(Twist,'/cmd_vel',10);self.goal=self.create_publisher(PoseStamped,'/goal_pose',10)
        self.mission=self.create_client(Trigger,'/mobile/run_mission');self.stop=self.create_client(Trigger,'/mobile/stop');self.reset=self.create_client(Trigger,'/mobile/reset')
    def receive(self,name,value):setattr(self,name,value);self.received[name]+=1
    def tf(self,msg):self.transforms.update((tr.header.frame_id,tr.child_frame_id) for tr in msg.transforms)
    def wait(self,predicate,timeout):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            rclpy.spin_once(self,timeout_sec=.05)
            if predicate():return True
        return False
    def service(self,client):
        if not client.wait_for_service(timeout_sec=15):raise RuntimeError('ROS service unavailable')
        future=client.call_async(Trigger.Request())
        if not self.wait(future.done,10):raise RuntimeError('ROS service response timeout')
        result=future.result()
        if not result.success:raise RuntimeError(result.message)
        return json.loads(result.message)

def run():
    rclpy.init();node=TestNode();checks={}
    try:
        streams=node.wait(lambda:all(v>=3 for v in node.received.values()),20)
        checks['real_ros_streams']={'passed':streams,'received':dict(node.received),'laser_beams':None if node.scan is None else len(node.scan.ranges),'map_cells':None if node.map is None else len(node.map.data)}
        if not streams:raise RuntimeError('ROS stream test failed')
        before=(node.odom.pose.pose.position.x,node.odom.pose.pose.position.y)
        cmd=Twist();cmd.linear.x=.12
        for _ in range(7):node.cmd.publish(cmd);node.wait(lambda:False,.10)
        stopped=node.wait(lambda:node.status['task'].get('status')=='watchdog_stopped',4)
        after=(node.odom.pose.pose.position.x,node.odom.pose.pose.position.y);distance=math.hypot(after[0]-before[0],after[1]-before[1])
        checks['cmd_vel_and_watchdog']={'passed':bool(stopped and distance>.05),'odom_distance_m':distance,'watchdog_stopped':stopped,'messages_accepted':node.status.get('bridge_counts',{}).get('cmd_vel_received')}
        result=node.service(node.mission);ident=result['id'];print('ROS mission accepted id='+str(ident),flush=True)
        finished=node.wait(lambda:node.status['task'].get('id')==ident and node.status['task'].get('status') in ('succeeded','failed'),150)
        status=node.status['task'];success=bool(finished and status.get('status')=='succeeded' and status.get('completed_goals')==7 and node.status['contacts']==0)
        checks['mission_trigger_to_physics']={'passed':success,'task':status,'environment_contacts':node.status['contacts']}
        if not success:raise RuntimeError('ROS-triggered mission did not succeed')
        goal=PoseStamped();goal.header.frame_id='mobile_map';goal.pose.position.x=3.75;goal.pose.position.y=3.60;goal.pose.orientation.w=1.
        old_id=status['id'];node.goal.publish(goal)
        accepted=node.wait(lambda:node.status['task'].get('id',0)>old_id and node.status['task'].get('operation')=='goal',10)
        goal_id=node.status['task'].get('id');done=node.wait(lambda:node.status['task'].get('id')==goal_id and node.status['task'].get('status') in ('succeeded','failed'),60)
        checks['pose_goal_topic_to_physics']={'passed':bool(accepted and done and node.status['task'].get('status')=='succeeded'),'task':node.status['task'],'estimated_pose':node.status['estimated_pose']}
        expected={('mobile_map','mobile_odom'),('mobile_odom','mobile_base_link'),('mobile_base_link','mobile_laser')}
        checks['tf_tree']={'passed':expected.issubset(node.transforms),'navigation_transforms':[list(t) for t in sorted(node.transforms) if t[0].startswith('mobile_')]}
        checks['typed_sensor_messages']={'passed':bool(len(node.scan.ranges)==180 and len(node.map.data)==node.map.info.width*node.map.info.height and set(node.map.data).issubset({-1,0,100})),'scan_frame':node.scan.header.frame_id,'map_frame':node.map.header.frame_id,'odom_frame':node.odom.header.frame_id}
    except Exception as exc:checks['execution_error']={'passed':False,'error':str(exc)}
    finally:
        try:node.service(node.stop)
        except Exception:pass
        report={'passed':bool(checks and all(c['passed'] for c in checks.values())),'transport':'Actual rclpy ROS 2/DDS via isolated D: runtime to independent MuJoCo HTTP process','nav2_used':False,'arm_mounted':False,'checks':checks,'total_received':node.received}
        (OUT/'ros_pipeline_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2),flush=True)
        node.destroy_node();rclpy.shutdown()
    return report['passed']

if __name__=='__main__':raise SystemExit(0 if run() else 1)
