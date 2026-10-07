"""Exercise the actual ROS 2 arm bridge against the running MuJoCo HTTP backend.

This test only operates the simulation. It starts and stops its own bridge process,
uses real DDS subscriptions, services and actions, then restores the simulation.
"""
import faulthandler
faulthandler.enable()
faulthandler.dump_traceback_later(45, repeat=True)
print('Importing native ROS 2 interfaces...', flush=True)
from pathlib import Path
import argparse
import json
import math
import os
import struct
import subprocess
import sys
import time
import urllib.request

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.action import ActionClient
from rclpy.time import Time
from action_msgs.msg import GoalStatus
from control_msgs.action import FollowJointTrajectory
from sensor_msgs.msg import JointState, CompressedImage, Image, CameraInfo
from rosgraph_msgs.msg import Clock
from std_srvs.srv import Trigger
from trajectory_msgs.msg import JointTrajectoryPoint
from tf2_ros import Buffer, TransformListener
print('Native ROS 2 imports ready', flush=True)

ROOT = Path('D:/RoboticArm')
OUT = ROOT/'results/integration/runtime'


def read_state(url):
    with urllib.request.urlopen(url+'/state', timeout=5) as response:
        return json.load(response)


def command(url, op):
    req = urllib.request.Request(url+'/command', data=json.dumps({'op':op}).encode(),
                                 headers={'Content-Type':'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


class Probe(Node):
    def __init__(self):
        super().__init__('anthro_arm_bridge_test', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.received = {}
        self.counts = {}
        self.subscriptions_owned = []
        for key, cls, topic in [
            ('joints', JointState, '/joint_states'),
            ('rgb', CompressedImage, '/camera/color/image_raw/compressed'),
            ('depth', Image, '/camera/depth/image_raw'),
            ('info', CameraInfo, '/camera/color/camera_info'),
            ('clock', Clock, '/clock'),
        ]:
            def callback(message, key=key):
                self.received[key] = message
                self.counts[key] = self.counts.get(key, 0)+1
            self.subscriptions_owned.append(self.create_subscription(cls, topic, callback, 10))
        self.buffer = Buffer(node=self)
        self.listener = TransformListener(self.buffer, self)
        self.reset = self.create_client(Trigger, '/anthro/reset')
        self.stop = self.create_client(Trigger, '/anthro/stop')
        self.grasp = self.create_client(Trigger, '/anthro/learned_grasp')
        self.action = ActionClient(self, FollowJointTrajectory, '/arm_controller/follow_joint_trajectory')

    def until(self, predicate, timeout=20):
        deadline = time.monotonic()+timeout
        while not predicate() and time.monotonic()<deadline:
            rclpy.spin_once(self, timeout_sec=.1)
        if not predicate():
            raise TimeoutError('ROS 2 condition did not complete in '+str(timeout)+' seconds')

    def wait(self, seconds):
        deadline = time.monotonic()+seconds
        while time.monotonic()<deadline:
            rclpy.spin_once(self, timeout_sec=.05)

    def result(self, future, timeout=30):
        self.until(future.done, timeout)
        value = future.result()
        if value is None:
            raise RuntimeError('ROS 2 future returned None')
        return value


def trajectory(joints, positions, seconds):
    goal = FollowJointTrajectory.Goal()
    goal.trajectory.joint_names = list(joints)
    point = JointTrajectoryPoint()
    point.positions = list(positions)
    point.time_from_start.sec = int(seconds)
    point.time_from_start.nanosec = int((seconds % 1)*1e9)
    goal.trajectory.points = [point]
    return goal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--backend', default='http://127.0.0.1:8770')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    report = {'passed':False, 'backend':args.backend, 'simulation_only':True, 'checks':[]}
    bridge = None
    node = None
    log = (OUT/'arm_bridge_process.log').open('w', encoding='utf-8')

    def record(name, passed, **evidence):
        report['checks'].append({'name':name, 'passed':bool(passed), **evidence})
        print(name+': '+('PASS' if passed else 'FAIL'), flush=True)
        if not passed:
            raise AssertionError(name+' failed')

    try:
        initial = read_state(args.backend)
        record('backend_27_dof', len(initial['joints'])==27 and initial['mode']=='SIMULATION_ONLY')
        command(args.backend,'reset')
        bridge = subprocess.Popen([sys.executable, '-B', '-u', str(ROOT/'integration/ros2/anthro_bridge.py'),
                                   '--backend', args.backend], cwd=str(ROOT), env=os.environ.copy(),
                                  stdout=log, stderr=subprocess.STDOUT,
                                  creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        report['bridge_pid'] = bridge.pid
        report['test_pid'] = os.getpid()
        rclpy.init()
        node = Probe()
        record('reset_service_discovered', node.reset.wait_for_service(timeout_sec=25))
        reset = node.result(node.reset.call_async(Trigger.Request()))
        record('reset_service_success', reset.success, response=reset.message[:500])
        node.until(lambda: 'clock' in node.received and node.received['clock'].clock.sec<5,15)
        node.wait(1.)
        node.buffer.clear()
        node.until(lambda: len(node.received)==5, 30)
        joints = node.received['joints']
        expected_names = [j['name'] for j in initial['joints']]
        record('joint_state_27_names_positions_velocities_efforts', joints.name==expected_names and
               all(len(getattr(joints, field))==27 and all(math.isfinite(x) for x in getattr(joints, field))
                   for field in ('position','velocity','effort')), count=len(joints.name))
        rgb, depth, info = (node.received[x] for x in ('rgb','depth','info'))
        record('rgb_jpeg', rgb.format=='jpeg' and bytes(rgb.data).startswith(b'\xff\xd8') and len(rgb.data)>100,
               bytes=len(rgb.data), frame=rgb.header.frame_id)
        samples = struct.unpack('<'+'f'*(len(depth.data)//4), bytes(depth.data))
        record('metric_depth_32fc1', depth.encoding=='32FC1' and len(depth.data)==depth.width*depth.height*4
               and all(math.isfinite(x) and x>0 for x in samples), width=depth.width, height=depth.height,
               min_m=min(samples), max_m=max(samples))
        record('calibrated_camera_info', info.width==depth.width and info.height==depth.height and
               info.k[0]>0 and info.k[4]>0 and info.k[8]==1 and info.header.frame_id==rgb.header.frame_id,
               intrinsic=list(info.k))
        old_clock=node.received['clock'].clock
        old_seconds=old_clock.sec+old_clock.nanosec/1e9
        node.wait(.4)
        new_clock=node.received['clock'].clock
        new_seconds=new_clock.sec+new_clock.nanosec/1e9
        record('simulation_clock_advances', new_seconds>old_seconds,
               start_s=old_seconds, end_s=new_seconds)
        for frame in ('palm_base',rgb.header.frame_id):
            node.until(lambda: node.buffer.can_transform('world',frame,Time()),15)
            tf=node.buffer.lookup_transform('world',frame,Time())
            record('tf_world_to_'+frame, math.isfinite(tf.transform.translation.x),
                   position=[tf.transform.translation.x,tf.transform.translation.y,tf.transform.translation.z])
        record('trajectory_action_discovered', node.action.wait_for_server(timeout_sec=15))
        state=read_state(args.backend)
        target=state['joints'][0]['q']+.06
        feedback=[]
        goal=trajectory([expected_names[0]],[target],2.)
        handle=node.result(node.action.send_goal_async(goal,feedback_callback=lambda msg:feedback.append(msg.feedback)))
        record('trajectory_goal_accepted',handle.accepted)
        outcome=node.result(handle.get_result_async(),35)
        actual=read_state(args.backend)['joints'][0]['q']
        record('trajectory_succeeds_and_moves_simulated_joint',outcome.status==GoalStatus.STATUS_SUCCEEDED
               and outcome.result.error_code==0 and abs(actual-target)<.025,
               action_status=outcome.status,error_code=outcome.result.error_code,target_rad=target,
               actual_rad=actual,error_rad=abs(actual-target))
        record('trajectory_feedback_received',bool(feedback) and feedback[-1].joint_names==[expected_names[0]]
               and len(feedback[-1].actual.positions)==1, messages=len(feedback))
        # Unsupported velocity requests must be refused at the ROS interface.
        invalid=trajectory([expected_names[0]],[target],2.)
        invalid.trajectory.points[0].velocities=[.1]
        rejected=node.result(node.action.send_goal_async(invalid))
        record('unsupported_velocity_goal_rejected',not rejected.accepted)
        # Backend limit validation must become a failed ROS action, not a silent move.
        invalid=trajectory([expected_names[0]],[99.],2.)
        bad=node.result(node.action.send_goal_async(invalid))
        if bad.accepted:
            failure=node.result(bad.get_result_async())
            record('out_of_range_goal_fails',failure.status==GoalStatus.STATUS_ABORTED and failure.result.error_code!=0,
                   action_status=failure.status,error_code=failure.result.error_code)
        else:
            record('out_of_range_goal_fails',True,rejected=True)
        feedback=[]
        goal=trajectory([expected_names[0]],[target+.25],8.)
        active=node.result(node.action.send_goal_async(goal,feedback_callback=lambda msg:feedback.append(msg.feedback)))
        record('cancel_test_goal_accepted',active.accepted)
        node.until(lambda: bool(feedback),10)
        cancelled=node.result(active.cancel_goal_async())
        result=node.result(active.get_result_async(),15)
        node.wait(.5)
        hold1=read_state(args.backend)
        node.wait(.5)
        hold2=read_state(args.backend)
        drift=abs(hold2['joints'][0]['q']-hold1['joints'][0]['q'])
        record('action_cancel_stops_and_holds',bool(cancelled.goals_canceling)
               and result.status==GoalStatus.STATUS_CANCELED and drift<.01,
               action_status=result.status,drift_rad=drift,trajectory=hold2['trajectory'])
        reset=node.result(node.reset.call_async(Trigger.Request()))
        record('reset_after_test',reset.success)
        node.wait(.5)
        support_z=read_state(args.backend)['object_position'][2]
        record('learned_grasp_service_discovered',node.grasp.wait_for_service(timeout_sec=10))
        started=node.result(node.grasp.call_async(Trigger.Request()))
        record('learned_grasp_trigger_accepted',started.success,response=started.message[:600])
        phases=[]
        samples=[]
        deadline=time.monotonic()+120
        completed=None
        while time.monotonic()<deadline:
            node.wait(.1)
            state=read_state(args.backend)
            grasp=state.get('grasp',state.get('task_result',{}))
            phase=grasp.get('phase','unknown')
            if not phases or phases[-1]!=phase:
                phases.append(phase)
                print('Learned grasp phase: '+phase,flush=True)
            contacts=[c for c in state['contacts'] if 'object_geom' in (c['geom1'],c['geom2'])
                      and c['normal_force']>.005 and 'worktable' not in (c['geom1'],c['geom2'])]
            names=' '.join(c['geom1']+' '+c['geom2'] for c in contacts)
            samples.append({'time_s':state['time'],'phase':phase,'object_z_m':state['object_position'][2],
                            'opposed_contacts':('thumb' in names and any(f in names for f in ('index','middle','ring','pinky'))),
                            'hand_contact_count':len(contacts)})
            if phase in ('complete','failed'):
                completed=grasp
                break
        holds=[s for s in samples if s['phase']=='hold']
        min_hold_lift=min((s['object_z_m']-support_z for s in holds),default=0.)
        opposed_fraction=sum(s['opposed_contacts'] for s in holds)/max(1,len(holds))
        hold_duration=(holds[-1]['time_s']-holds[0]['time_s']) if len(holds)>1 else 0.
        (OUT/'arm_bridge_grasp_samples.json').write_text(json.dumps(samples,indent=2),encoding='utf-8')
        record('learned_grasp_physical_lift_and_completion',bool(completed and completed.get('completed_sequence'))
               and not completed.get('error') and min_hold_lift>.03 and hold_duration>1 and opposed_fraction>.9,
               phases=phases,controller_result=completed,support_center_z_m=support_z,
               min_hold_lift_m=min_hold_lift,hold_sample_span_s=hold_duration,
               opposed_contact_hold_fraction=opposed_fraction,sample_count=len(samples))
        reset=node.result(node.reset.call_async(Trigger.Request()))
        record('reset_after_grasp',reset.success)
        report['subscription_counts']=node.counts
        report['passed']=all(c['passed'] for c in report['checks'])
    except Exception as exc:
        report['error']=repr(exc)
        print('ERROR: '+repr(exc),flush=True)
    finally:
        faulthandler.cancel_dump_traceback_later()
        try:
            command(args.backend,'stop')
            command(args.backend,'reset')
            report['restored_home']=True
        except Exception as exc:
            report['restore_error']=repr(exc)
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        if bridge is not None and bridge.poll() is None:
            bridge.terminate()
            try: bridge.wait(timeout=5)
            except subprocess.TimeoutExpired: bridge.kill();bridge.wait(timeout=5)
        report['bridge_process_stopped']=bridge is None or bridge.poll() is not None
        log.close()
        (OUT/'arm_bridge_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report,indent=2),flush=True)
    return 0 if report['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
