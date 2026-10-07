ROS 2 Jazzy runtime on D:

This is a working native Windows runtime from the recognized RoboStack
community distribution. It is isolated from the existing MuJoCo Python.
It does not enable WSL, install system services, or change the system PATH.

Runtime: D:\RoboticArm\software\ros2\.pixi\envs\default
Manifest and exact dependency lock: D:\RoboticArm\software\ros2\pixi.toml
                                  D:\RoboticArm\software\ros2\pixi.lock
Package manager: portable Pixi 0.81.0 from its official GitHub release.
Its SHA256 was checked against GitHub release asset metadata:
1b989b152ea13e881a641a112c7ea59c51818fd5ba84924c763b40b9b157dab9

The 486-package environment includes Python 3.12.15, ROS Jazzy rclpy,
Fast DDS RMW, standard messages/services, JointState, images and CameraInfo,
JointTrajectory, FollowJointTrajectory, geometry messages, TF2 and nav_msgs.
Full MoveIt and Nav2 are not installed. The navigation demonstration uses its
documented local planner interfaces; it must not be described as Nav2.

Run from PowerShell:
  & D:\RoboticArm\integration\runtime\run_ros2.ps1 ros2 --help
  & D:\RoboticArm\integration\runtime\run_ros2.ps1 probe
  & D:\RoboticArm\integration\runtime\run_ros2.ps1 smoke
  & D:\RoboticArm\integration\runtime\run_ros2.ps1 python D:\RoboticArm\integration\ros2\anthro_bridge.py

The arm bridge requires the separate MuJoCo HTTP backend on 127.0.0.1:8770.
It communicates through HTTP; do not add MuJoCo's site-packages to ROS Python
or overwrite the ROS environment with packages from the original Python.

environment.ps1 sets all configured download/package/ROS/log/Python caches,
temporary directories and the child-process user profile to D:. It also
limits BLAS/OpenMP/MKL threads to 1; this resolves lengthy native startup on
this host. Always launch via run_ros2.ps1 to preserve that environment.

ROS domain 27 is local-only, with rmw_fastrtps_cpp. It does not discover a
physical robot on the LAN. ROS_LOCALHOST_ONLY generates a deprecation warning
but is deliberately retained for the tested local transport configuration.
For time-based ROS consumers, set use_sim_time=true. Simulation reset rewinds
/clock, and consumers must clear time-indexed buffers; TF2 Buffer(node=node)
handles the backward clock jump when the node uses simulation time.

Validation evidence:
  results\integration\runtime\runtime_probe.json
    Native imports, ROS type serialization/deserialization and DDS RMW init.
  results\integration\runtime\ros2_smoke.json
    Two independent processes, 90 valid 27-joint DDS messages, response on
    Trigger service, and a received TF transform. Both processes exited 0.
  results\integration\runtime\arm_bridge_validation.json
    Actual HTTP-backed arm ROS interfaces, action result/feedback/cancellation,
    camera messages, reset and physically evaluated simulated learned grasp.
    Inspect the passed fields; a failed report is never proof of completion.

The final 7 October 2026 arm test passed all 23 checks. The action ended with
1.825 mrad position error and 38 feedback messages. Cancellation held the joint
with 9.79 microrad sampled drift. The ROS-triggered 36 mm simulated cube grasp
held at least 153.559 mm above its initial support height over a 1.48-second
sampled hold interval, with opposing thumb/finger contacts in every hold sample.
It then lowered/released the cube, completed without controller error, and
reset. These measurements validate that simulated example, not a physical
robot or arbitrary-object grasping. Samples are in arm_bridge_grasp_samples.json.

Rerun arm integration test (it resets and moves only the simulation):
  & D:\RoboticArm\integration\runtime\run_ros2.ps1 python -B -u D:\RoboticArm\integration\runtime\test_arm_bridge.py

The test starts/stops its own bridge and restores the simulated arm. Do not
run another arm bridge on the same topics, or issue concurrent arm commands.
The navigation bridge uses /mobile/clock and mobile_* TF frames, so it is
separate from the fixed-arm simulation's /clock and world frame.

RoboStack's Windows development guide calls for Visual Studio C++ tools for
building packages. This project proved the precompiled runtime without a new
compiler installation; it does not claim a custom ROS C++ build was tested.
See sources.txt for download provenance and isaac_feasibility.txt for the
hardware limitation preventing a supported local Isaac Sim/Lab workflow.
