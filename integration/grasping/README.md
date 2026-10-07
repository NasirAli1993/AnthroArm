# Learned contact grasping

This module operates the existing 27-axis V3 humanoid arm in MuJoCo. A free upright orange cube is detected from rendered RGB and metric depth. A fitted size-conditioned policy supplies ten grasp parameters. Scripted task stages and numerical seven-axis IK drive the original rate-limited, effort-bounded motors through approach, closure, lift, hold, set-down, release, and retreat.

The learned part is **ordinary least-squares affine regression**, fitted to six successful demonstration vectors selected from 42 physically simulated candidate grasps. This is small-data supervised learning, not an end-to-end neural policy or reinforcement learning. `policy.json` contains the fitted coefficients and training error. Candidate failures remain in the reports. The model conditions on the declared cube edge length; arbitrary shape recognition and size estimation are not implemented.

## Run

From PowerShell on D:, load the project environment and execute:

```powershell
. D:\RoboticArm\scripts\environment.ps1
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
& D:\RoboticArm\software\python\python.exe D:\RoboticArm\integration\grasping\run.py
```

`--size-mm 37 --mass-g 60 --x 0.4 --y 0` selects another tabletop episode. The learned size domain is 32–42 mm; validated masses are 40–60 g. Unseen geometry, substantially different positions, or other masses are not promised to work.

## Integrate

```python
from controller import configure_episode, LearnedGraspController
from vision import KnownSizeRGBDCamera

configure_episode(sim, size=.036, mass=.06, x=.4, y=0)
camera = KnownSizeRGBDCamera(sim, object_size_m=.036)
detection = camera.capture()
assert detection['detected']
controller = LearnedGraspController(sim)
controller.start(detection['center_world_m'], .036)
while controller.active:
    controller.step(25)  # This advances MuJoCo; do not also call sim.step.
print(controller.state)
camera.close()
```

`configure_episode` changes object geometry, mass, inertia, and starting pose **before** an episode. The controller never changes object pose, adds constraints, or applies body/generalized forces. Its only physical commands are the existing bounded joint targets. It refuses lift without opposing thumb/finger contact and stops if contact is lost for 0.25 s during lift/hold. `cancel()` holds current joints and clears the active sequence. Reset a scene only after cancellation.

The camera adapter uses OpenCV orange segmentation and calibrated depth backprojection. It replaces the baseline camera's known 50 mm cube height prior with the supplied edge length; it never reads object ground-truth pose. Ground truth is read separately by evaluation code for errors, height, slip, and release scoring.

`controller.state.completed_sequence` means the command sequence finished. Quantitative physical success is separately checked in trial reports, requiring over 100 mm retained lift, sustained hand contacts, and eventual table-supported release with no hand contact and low object velocity. A completed command sequence alone is not a success claim.

## Evidence and limits

Results live in `D:\RoboticArm\results\integration\grasping`. `report.json` records the frozen training split and ten held-out tests; `camera_report.json` records six image-derived control tests; `final_validation.json` verifies the current controller and cancellation/empty-target behavior. Full time series include contacts, normal forces, translational slip relative to the palm, and object speed. `learned_contact_grasp.webm` records actual physics frames, with a hand close-up and initial camera detection inset.

Contact is simulated using rigid convex hulls of the CAD parts. Finger-pad deformation, friction uncertainty, and real sensors/motors are not modeled. Actuators can saturate at their original effort bounds, and MuJoCo's compliant joint/contact constraints allow measured small penetrations and angular overshoot; reports disclose both. These results support this restricted simulated cube task, not physical-hardware readiness or general robotic grasping.

Reproduction: `train.py` reruns optimization and fitting; `validate.py` tests the frozen policy; `test_camera.py` runs camera trials; `record.py` recreates the video. All files and caches remain under D: when the project environment is loaded.
