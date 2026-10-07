"""Focused final-review fixtures. No running simulator is commanded or stopped."""
import argparse
import importlib.util
import json
from pathlib import Path
import queue
import threading
import time
from concurrent.futures import Future
from types import SimpleNamespace

ROOT=Path('D:/RoboticArm')
OUT=ROOT/'results/integration/runtime'


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def backend_checks():
    module=load('review_runtime_server',ROOT/'integration/runtime_server.py')
    tests=[]
    runtime=module.Runtime.__new__(module.Runtime)
    runtime.error=None
    runtime.worker=SimpleNamespace(is_alive=lambda:True)
    runtime.snapshot={'time':1.,'joints':[{'name':'fixture'}]}
    runtime.lock=threading.Lock()
    runtime.camera={'time':1.}
    runtime.frame=b'old frame'
    runtime.commands=queue.Queue()
    response={}
    handler=SimpleNamespace(server=SimpleNamespace(runtime=runtime),path='/health')
    handler.send=lambda data,kind='application/json',status=200:response.update(data=data,status=status)
    module.Handler.do_GET(handler)
    assert response['data']['ready'] is True
    tests.append('healthy worker with snapshot reports ready')
    runtime.error='Intentional fixture worker failure'
    module.Handler.do_GET(handler)
    assert response['data']['ready'] is False and response['data']['error']==runtime.error
    tests.append('failed worker reports unhealthy')
    for path in ('/state','/camera','/frame.jpg'):
        handler.path=path
        module.Handler.do_GET(handler)
        assert response['status']==503 and response['data']['error']==runtime.error
        tests.append('failed worker refuses stale '+path)
    begin=time.monotonic()
    try:
        runtime.request({'op':'reset'})
        raise AssertionError('request should reject failed worker')
    except RuntimeError:
        assert time.monotonic()-begin<.5 and runtime.commands.empty()
    tests.append('command rejects failed worker without enqueue or timeout')
    runtime.error=None
    runtime.worker=SimpleNamespace(is_alive=lambda:False)
    assert runtime.failure()=='Simulation worker is not running'
    tests.append('unexpected dead worker is detected even without stored exception')
    runtime.ready=threading.Event()
    pending=Future()
    runtime.commands.put(({'op':'reset'},pending))
    def fail_constructor():raise RuntimeError('Injected simulator construction failure')
    module.ArmSimulation=fail_constructor
    runtime.run()
    assert pending.done() and isinstance(pending.exception(),RuntimeError) and runtime.ready.is_set()
    tests.append('fatal worker exception resolves queued command failures')
    return tests


def ros_checks():
    module=load('review_arm_bridge',ROOT/'integration/ros2/anthro_bridge.py')
    from control_msgs.action import FollowJointTrajectory
    from control_msgs.msg import JointComponentTolerance
    from trajectory_msgs.msg import JointTrajectoryPoint,MultiDOFJointTrajectoryPoint
    fake=SimpleNamespace(busy=threading.Lock())
    def goal():
        request=FollowJointTrajectory.Goal()
        request.trajectory.joint_names=['shoulder_abduction']
        point=JointTrajectoryPoint();point.positions=[.1];point.time_from_start.sec=2
        request.trajectory.points=[point]
        return request
    tests=[]
    request=goal()
    assert module.ArmBridge.goal(fake,request)==module.GoalResponse.ACCEPT
    tests.append('supported position-only goal remains accepted')
    mutations=[
        ('multi_dof_joint_names',lambda g:setattr(g.multi_dof_trajectory,'joint_names',['floating_base'])),
        ('multi_dof_points',lambda g:setattr(g.multi_dof_trajectory,'points',[MultiDOFJointTrajectoryPoint()])),
        ('multi_dof_frame',lambda g:setattr(g.multi_dof_trajectory.header,'frame_id','world')),
        ('multi_dof_timestamp',lambda g:setattr(g.multi_dof_trajectory.header.stamp,'sec',1)),
        ('component_path_tolerance',lambda g:setattr(g,'component_path_tolerance',[JointComponentTolerance()])),
        ('component_goal_tolerance',lambda g:setattr(g,'component_goal_tolerance',[JointComponentTolerance()])),
    ]
    for name,mutate in mutations:
        request=goal();mutate(request)
        assert module.ArmBridge.goal(fake,request)==module.GoalResponse.REJECT,name
        tests.append('unsupported '+name+' rejected')
    published=[]
    state={'mode':'SIMULATION_ONLY','time':1.25,'task':'idle','task_result':{'phase':'failed','error':'fixture contact loss'},
           'trajectory':{'status':'idle'},'joints':[{'name':'shoulder_abduction','q':.1,'velocity':0.,'torque':1.}], 'bodies':[]}
    publishing=SimpleNamespace(backend=SimpleNamespace(get=lambda _:state),
                               clock_pub=SimpleNamespace(publish=lambda _:None),joints=SimpleNamespace(publish=lambda _:None),
                               status=SimpleNamespace(publish=lambda msg:published.append(json.loads(msg.data))),
                               tf=SimpleNamespace(sendTransform=lambda _:None))
    module.ArmBridge.publish_state(publishing)
    assert published[-1]['task_result']==state['task_result'] and published[-1]['grasp'] is None
    tests.append('ROS status exposes completed task failure details')
    state['task']='learned_grasp';state['grasp']={'phase':'hold','active':True,'error':''}
    module.ArmBridge.publish_state(publishing)
    assert published[-1]['grasp']==state['grasp']
    tests.append('ROS status exposes active grasp phase')
    return tests


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--part',choices=['backend','ros'],required=True)
    args=parser.parse_args()
    report={'part':args.part,'passed':False,'scope':'Focused local fixtures; no live simulation commands'}
    try:
        report['checks']=backend_checks() if args.part=='backend' else ros_checks()
        report['passed']=True
    except Exception as exc:
        report['error']=repr(exc)
        raise
    finally:
        (OUT/('review_'+args.part+'_checks.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report,indent=2))
