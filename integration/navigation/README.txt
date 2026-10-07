SIMULATED MOBILE BASE: MEASURED LIDAR MAPPING AND NAVIGATION

This is a separate wheeled robot. The humanoid arm is not mounted on this
base, and the combination's balance, reach or navigation has not been tested.
No hardware is commanded. This is custom Python/MuJoCo navigation, not Nav2.

WHAT ACTUALLY RUNS
1. Two wheel velocity actuators move a free chassis through contact forces.
   Wheel spin and ground slip are physical simulation outcomes.
2. A simulated 180-beam 360-degree range sensor raycasts the MuJoCo world at
   10 Hz. Gaussian range noise has standard deviation 6 mm.
3. Wheel encoders predict incremental pose. A 0.8% odometry scale bias and
   small encoder noise supplement the actual wheel slip.
4. Point-to-point ICP aligns the scan with accumulated measured endpoints.
   This corrects the pose estimate using range observations. The laser pose
   and map are estimated together: incremental scan-to-map 2-D SLAM.
5. Log-odds ray updates mark measured free and occupied cells at 8 cm spacing.
6. A* plans on the map with a circular 32 cm discretized obstacle inflation.
   The feedback controller follows the route using estimated pose. Near-front
   laser observations stop forward travel when a range is below 40 cm.
7. Four survey goals precede three previously unused navigation goals.
   Survey planning can enter unobserved cells at an added cost. Later goals
   require known free space. Every drive step still uses current scans.

GROUND-TRUTH BOUNDARY
The initial known position establishes local map coordinate (0,0,0). Later
simulator true pose is used only for scoring and the orange evaluation trace.
Slam2D.update receives range and encoder observations, without simulator or
obstacle geometry. The planner receives the measured map and selected goal.
The complete sensor log can reconstruct all saved pose estimates and the map
exactly without a simulator; validate_navigation.py checks this separation.

LIMITATIONS
This implementation has no global pose-graph optimization, explicit loop-
closure detector, kidnapped-robot recovery, multi-floor mapping or Nav2 stack.
Scan-to-map alignment naturally revisits prior measurements, but it is not
a production mapping system. The map is a static indoor test scene; dynamic
people and moving obstacles are not validated. Goals and initial orientation
are supplied. These numerical tests do not establish real-robot accuracy.
The original failed tuning report is retained as initial_tuning_validation.json.
The final navigation_validation.json is the authoritative mission result.

RUN (POWERSHELL, ALL PROJECT FILES ON D:)
  . D:\RoboticArm\scripts\environment.ps1
  $env:OPENBLAS_NUM_THREADS='1'
  $env:OMP_NUM_THREADS='1'
  $env:MKL_NUM_THREADS='1'
  D:\RoboticArm\software\python\python.exe -u D:\RoboticArm\integration\navigation\run_mission.py
  D:\RoboticArm\software\python\python.exe -u D:\RoboticArm\integration\navigation\validate_navigation.py
Use --no-video for a faster mission run. Default seed is 10. --seed changes
sensor noise; it does not change the environment or supply obstacle locations.

SOURCE/API
navigation.py: NavigationSimulation, Slam2D and MissionRunner.
run_mission.py: survey, held-out goal evaluation, native physics/map recording.
validate_navigation.py: sensor fixture, wheel dynamics, truth-free replay and
occupied-goal refusal checks.
world.xml: exact generated MuJoCo scene for inspection.

NavigationSimulation.command(v_m_s, yaw_rate_rad_s): wheel velocity targets.
NavigationSimulation.step(dt=0.1): advances physics, returns observations.
NavigationSimulation.observe(): range array and wheel-encoder observations.
NavigationSimulation.evaluation_truth(): evaluation-only pose.
MissionRunner.advance(goal_xy_m, phase, allow_unknown): one control cycle.
MissionRunner.get_state(): serializable laser scan, wheel odometry, estimated
pose, occupancy grid, current command and planned path, without truth pose.

For a ROS adapter: use scan as LaserScan in base/laser frame; wheel_odometry
as odom; estimated_pose as map->base pose; publish the occupancy with origin
and resolution. cmd_vel is in m/s and rad/s. Do not feed evaluation_truth back
into SLAM or the controller. Use one owner for stepping the physics engine.

OUTPUTS: D:\RoboticArm\results\integration\navigation
navigation_demo.webm     Actual physics + measured map, playback 5x sim time.
navigation_poster.png    Frame from that actual simulation.
survey_map.png          Map following survey goals.
navigation_map.png      Map and complete estimated/true evaluation traces.
navigation_validation.json  Mission conditions, outcomes, errors and contacts.
implementation_checks.json  Independent checks including sensor-only replay.
sensor_observations.json.gz  All laser/encoder inputs, without ground truth.
trajectory.json         Estimates, evaluation truth and cmd_vel over time.
measured_map.npz         Measured grid and log-odds state.
latest_state.json       Last serializable state for adapters/viewers.

REAL ROS 2 INTEGRATION (IMPLEMENTED AND EXECUTED)
Launch both long-running processes, without opening console windows:
  & D:\RoboticArm\integration\navigation\launch.ps1
The idempotent launcher reuses existing navigation processes.
backend.py runs the actual MuJoCo physics, sensing, mapping and controller in
the D: simulation Python. ros_bridge.py runs in the separate native ROS2 Jazzy
runtime through integration/runtime/run_ros2.ps1 and talks to port8771.
The background worker is the single owner of physics stepping and rendering.

Actual DDS topics:
  /scan           sensor_msgs/LaserScan, 180 measured noisy ranges
  /odom           nav_msgs/Odometry, wheel encoder odometry (can drift)
  /map            nav_msgs/OccupancyGrid, measured log-odds map
  /cmd_vel        geometry_msgs/Twist input; linear.x and angular.z only
  /goal_pose      geometry_msgs/PoseStamped input in mobile_map
  /mobile/status  std_msgs/String JSON, current goal/mission outcome
  /mobile/clock   This simulation's clock, separate from the arm's /clock
  /tf             mobile_map -> mobile_odom -> mobile_base_link -> mobile_laser
ROS consumers needing simulated time should remap their /clock to
/mobile/clock for this separate simulation. The arm and base clocks are not
represented as a synchronized combined physical world by this component.

Actual std_srvs/Trigger services:
  /mobile/run_mission  Resets, maps the room and drives all seven goals.
                      Response acknowledges the task; status reports completion.
  /mobile/reset       Resets the local simulated base and measured map.
  /mobile/stop        Stops the simulated wheel command and cancels the task.
Manual cmd_vel must be refreshed within 0.6 wall-clock seconds; otherwise
the backend commands zero velocity. The tested runtime has no nav2_msgs, so
NavigateToPose is not advertised. The bridge supports that action type if it
is later installed, but that alone would still not mean the Nav2 stack is used.

PoseStamped goal x/y are map meters, z must be zero. A normalized planar
quaternion requests a final yaw; an all-zero quaternion leaves yaw unconstrained.
Only mobile_map (or an empty frame ID interpreted as mobile_map) is accepted.
Goal success waits for the 15 cm estimated-position tolerance, requested yaw
tolerance if present, and five simulated braking/settling cycles.

END-TO-END VALIDATION
  & D:\RoboticArm\integration\runtime\run_ros2.ps1 python D:\RoboticArm\integration\navigation\test_ros_pipeline.py
The test is a separate real rclpy node. It receives typed messages, sends
cmd_vel, observes the watchdog stop, invokes the mission service, waits for
all seven goals, publishes another pose goal and checks the TF tree.
ros_pipeline_validation.json contains the result. live_backend_mission.json
records the ROS-triggered physical navigation outcomes. No hardware is involved.

HTTP ADAPTER (127.0.0.1 ONLY)
GET /state: current measured scan, encoder odometry, SLAM pose/map and task.
GET /frame.jpg: actual physics and map frame; GET /map.png: measured map.
POST /command JSON examples:
  {"op":"mission"}
  {"op":"goal","goal":[3.75,3.6],"yaw":0.0}
  {"op":"cmd_vel","v":0.12,"w":0.0}
  {"op":"stop"}
  {"op":"reset"}
All coordinates/commands use the local map and simulated SI units.

FINAL RECORDED CONDITIONS (7 OCTOBER 2026)
122.2 simulated seconds; four survey goals and three held-out goals passed.
No wheel/chassis contacts with room obstacles or walls were recorded.
Position estimate RMSE 0.0080 m; maximum position error 0.0235 m in this run.
Held-out final true goal errors: 0.127, 0.133 and 0.127 m; the commanded stop
tolerance is 0.15 m in estimated position. These are different measurements:
localization RMSE is not the final goal distance.
All 1,217 sensor observations reproduced the saved poses/map exactly without
ground-truth input. The 24.3-second video is actual physics at 5x playback.
The real ROS pipeline separately passed six checks and received 496 messages
on each tested scan/odom/map/status stream. Consult JSON for exact conditions.
