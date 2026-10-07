MOBILE ANTHROARM: CONTINUOUS PHYSICAL SIMULATION

This demonstration combines the existing exact-mesh V3 humanoid arm with a
new physical differential-drive chassis in one MuJoCo model and one continuous
trajectory. The base drives to the table using encoder-seeded 270-degree lidar
scan-to-map SLAM. After parking, the fixed RGB-D camera observes an upright
36 mm cube. The frozen supervised grasp policy closes the real simulated hand,
lifts, holds, sets down, releases, and retreats.

The chassis has a free joint. Its wheel motors remain effort-bounded at 18 Nm
each. Parking uses wheel encoder feedback, not a world weld or direct body
force. The 27 original arm motors retain their original effort limits. The
cube has a free joint, and there are no equality constraints or object-pose
edits during a mission. The arm is mechanically mounted on a rear column and
overhead support; arm-column collision remains enabled.

The chassis is a deliberate 80 kg, 0.50 m square concept, with a 6 kg mounting
assembly, 0.58 m wheel track, 0.105 m wheel radius, and low-friction caster
contacts. It differs from the standalone 3 kg navigation robot. Rigid contact,
ideal joints, and ideal base pose for arm IK are assumptions. Docking control
uses the lidar-map pose. Arm IK uses ideal simulated base pose and joint
proprioception; the object target itself comes only from image/depth pixels.

This is an unobstructed straight docking lane. It does not combine the full
standalone obstacle-navigation benchmark with pickup, and it does not claim
whole-body learned locomotion or dynamic grasping while driving. The external
camera is fixed and calibrated, and cube size/orientation are known priors.

RUN (PowerShell, all project paths/caches on D:)

. D:\RoboticArm\scripts\environment.ps1
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
& D:\RoboticArm\software\python\python.exe D:\RoboticArm\integration\mobile_manipulation\mission.py

validate.py repeats three different start-distance/cube-location cases.
record.py generates actual physics footage. Outputs are in:
D:\RoboticArm\results\integration\mobile_manipulation

validation.json: per-case pass, lift, release, wheel/arm bounds, base drift.
trial_0.json through trial_2.json: complete measured trajectories.
mobile_camera_grasp.webm: complete recorded mission with arm close-up/map.
video_trial.json: quantitative report for the recorded run.
video.json: frame count, decode verification, timestamps and source.

The preexisting V3 model, learned grasp files, and standalone navigation files
are not modified. The XML here references their original CAD mesh assets.
