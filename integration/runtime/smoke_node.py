"""Cross-process native DDS test: 27 joint states, Trigger service and TF."""
import argparse
import json
import os
import time
from pathlib import Path
import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from rclpy.time import Time
from sensor_msgs.msg import JointState
from std_msgs.msg import String
from std_srvs.srv import Trigger
from geometry_msgs.msg import TransformStamped
from tf2_ros import Buffer, TransformListener, TransformBroadcaster


def server(args):
    rclpy.init()
    node = Node('runtime_server_'+args.token)
    acknowledgements = node.create_publisher(String, args.topic+'/ack', 10)
    received = []
    calls = []
    broadcaster = TransformBroadcaster(node)

    def on_state(msg):
        valid = len(msg.name)==27 and len(msg.position)==27 and all(abs(x-i*.01)<1e-9 for i,x in enumerate(msg.position))
        received.append({'joint_count':len(msg.name),'valid':valid})
        out = String(); out.data=json.dumps({'token':args.token,'valid':valid,'count':len(msg.position)})
        acknowledgements.publish(out)

    def on_trigger(req,response):
        calls.append(True)
        response.success=True; response.message='ROS2 service response '+args.token
        return response

    def publish_tf():
        transform=TransformStamped()
        transform.header.stamp=node.get_clock().now().to_msg()
        transform.header.frame_id='base_'+args.token
        transform.child_frame_id='palm_'+args.token
        transform.transform.translation.x=.30
        transform.transform.translation.y=.10
        transform.transform.translation.z=.50
        transform.transform.rotation.w=1.
        broadcaster.sendTransform(transform)

    subscription=node.create_subscription(JointState,args.topic+'/joint_states',on_state,10)
    service=node.create_service(Trigger,args.topic+'/ready',on_trigger)
    timer=node.create_timer(.05,publish_tf)
    start=time.monotonic()
    report={'pid':os.getpid(),'role':'server','token':args.token}
    (args.output/'server_ready.json').write_text(json.dumps(report),encoding='utf-8')
    try:
        while time.monotonic()-start<25:
            rclpy.spin_once(node,timeout_sec=.05)
            if (args.output/'client.json').exists():
                break
        report.update(received_messages=len(received),valid_messages=sum(x['valid'] for x in received),service_calls=len(calls),
                      passed=bool(received and all(x['valid'] for x in received) and calls))
        (args.output/'server.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report),flush=True)
        return 0 if report['passed'] else 1
    finally:
        node.destroy_node();rclpy.shutdown()


def client(args):
    rclpy.init()
    node=Node('runtime_client_'+args.token)
    publisher=node.create_publisher(JointState,args.topic+'/joint_states',10)
    acks=[]
    subscription=node.create_subscription(String,args.topic+'/ack',lambda msg:acks.append(json.loads(msg.data)),10)
    client_service=node.create_client(Trigger,args.topic+'/ready')
    buffer=Buffer()
    listener=TransformListener(buffer,node)
    report={'pid':os.getpid(),'role':'client','token':args.token,'passed':False}
    start=time.monotonic()
    try:
        if not client_service.wait_for_service(timeout_sec=10):
            raise RuntimeError('Trigger service did not become available')
        future=client_service.call_async(Trigger.Request())
        transform=None
        while time.monotonic()-start<20:
            message=JointState()
            message.header.stamp=node.get_clock().now().to_msg()
            message.name=['axis_'+str(i) for i in range(27)]
            message.position=[i*.01 for i in range(27)]
            publisher.publish(message)
            rclpy.spin_once(node,timeout_sec=.10)
            try:
                transform=buffer.lookup_transform('base_'+args.token,'palm_'+args.token,Time())
            except Exception:
                pass
            if acks and future.done() and transform is not None:
                break
        response=future.result() if future.done() else None
        translation=([transform.transform.translation.x,transform.transform.translation.y,transform.transform.translation.z]
                     if transform is not None else None)
        report.update(acknowledgements=len(acks),valid_ack=any(a.get('token')==args.token and a.get('valid') and a.get('count')==27 for a in acks),
                      service_success=bool(response and response.success),service_message=response.message if response else None,
                      transform_translation=translation)
        report['passed']=bool(report['valid_ack'] and report['service_success'] and translation==[.3,.1,.5])
        return 0 if report['passed'] else 1
    except Exception as exc:
        report['error']=repr(exc)
        return 1
    finally:
        (args.output/'client.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report),flush=True)
        node.destroy_node();rclpy.shutdown()


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('role',choices=['server','client'])
    parser.add_argument('--token',required=True)
    parser.add_argument('--topic',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    raise SystemExit(server(args) if args.role=='server' else client(args))
