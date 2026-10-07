"""Inspect actual installed ROS types and native serialization support."""
import json
import platform
import sys
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError
import rclpy
from rclpy.serialization import serialize_message, deserialize_message
from rclpy.utilities import get_rmw_implementation_identifier
from std_msgs.msg import String
from std_srvs.srv import Trigger
from sensor_msgs.msg import JointState, Imu, Image
from trajectory_msgs.msg import JointTrajectory
from control_msgs.action import FollowJointTrajectory
from geometry_msgs.msg import TransformStamped, PoseStamped
import tf2_ros

ROOT = Path('D:/RoboticArm/results/integration/runtime')
ROOT.mkdir(parents=True, exist_ok=True)


def main():
    ctx = rclpy.Context()
    rclpy.init(context=ctx)
    checked = {}
    try:
        for cls in [String, JointState, Imu, Image, JointTrajectory, TransformStamped,
                    PoseStamped, Trigger.Request, Trigger.Response, FollowJointTrajectory.Goal]:
            data = serialize_message(cls())
            recovered = deserialize_message(data, cls)
            checked[cls.__module__+'.'+cls.__name__] = {'serialized_bytes':len(data), 'roundtrip':isinstance(recovered,cls)}
        report = {'passed':all(x['roundtrip'] for x in checked.values()),
                  'python':sys.version, 'executable':sys.executable,
                  'platform':platform.platform(), 'rmw':get_rmw_implementation_identifier(),
                  'rclpy_path':rclpy.__file__, 'tf2_ros_path':tf2_ros.__file__,
                  'message_checks':checked}
        (ROOT/'runtime_probe.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report,indent=2))
        return report
    finally:
        rclpy.shutdown(context=ctx)


if __name__ == '__main__':
    main()
