# Setup and reproduction

This guide reconstructs the tested Windows x64 layout without bundling installed software, caches, installers, or the large SmolVLM weights. The source and saved evidence were exercised on the original workstation; a fresh installation from this export has **not** been executed. Preserve the existing reports before rerunning tests, because the scripts write to the same result paths.

## 1. Restore the source layout

Use a separate machine or a fresh workspace at **`D:\RoboticArm`**. Extract or clone the repository so that `D:\RoboticArm\START_SIMULATION.cmd` exists directly at that location. Do not overwrite an existing working project. An export stored at `D:\RoboticArm_GitHub` is an archive/repository copy, not a validated alternate execution root: several CAD, navigation, and launch scripts still refer to `D:\RoboticArm`.

After the repository is published, a machine with Git can create the fresh checkout with `git clone https://github.com/NasirAli1993/AnthroArm.git D:\RoboticArm`. Use that command only when the destination does not already contain a project. Alternatively, extract the repository archive and remove any extra outer folder level.

Windows PowerShell is sufficient for the launchers. The local browser is optional; the launcher prints a loopback URL if no supported existing browser is found. Neither a browser nor a SOLIDWORKS license is bundled. ROS and MuJoCo run natively on Windows; WSL, Docker, a system Python installation, and a new compiler installation were not required for the tested precompiled runtime.

Open a new PowerShell window and initialize project-local directories and process environment:

```powershell
Set-Location -LiteralPath 'D:\RoboticArm'
. .\scripts\environment.ps1
New-Item -ItemType Directory -Force -Path '.\downloads', '.\software\python', '.\software\ros2', '.\software\vision_language', '.\results\integration' | Out-Null
```

The environment script redirects configured Python/package/model caches, temporary directories, and child-process profile paths to D:. It limits BLAS/OpenMP/MKL threads to one to avoid native-library startup stalls observed on this host. It does not change the system PATH or move Windows itself. Use a fresh shell when switching between the main and ROS environments.

## 2. Restore the simulation Python

The tested interpreter is the official **Python 3.12.10 embeddable Windows x64** distribution. The project enables `site` and installs packages into that local directory. These commands are for a new empty `software\python` destination:

```powershell
$projectPythonArchive = 'D:\RoboticArm\downloads\python-3.12.10-embed-amd64.zip'
Invoke-WebRequest 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip' -OutFile $projectPythonArchive
$projectPythonHash = (Get-FileHash -LiteralPath $projectPythonArchive -Algorithm SHA256).Hash.ToLowerInvariant()
if ($projectPythonHash -ne '4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3') { throw 'Python archive checksum mismatch' }
Expand-Archive -LiteralPath $projectPythonArchive -DestinationPath 'D:\RoboticArm\software\python'
@('python312.zip', '.', '', 'import site') | Set-Content -LiteralPath 'D:\RoboticArm\software\python\python312._pth' -Encoding ascii
Invoke-WebRequest 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'D:\RoboticArm\downloads\get-pip.py'
$py = 'D:\RoboticArm\software\python\python.exe'
& $py 'D:\RoboticArm\downloads\get-pip.py' 'pip==26.2.1'
& $py -m pip install --requirement 'D:\RoboticArm\docs\dependencies\requirements-simulation.txt'
& $py -m pip check
& $py -c "import mujoco,numpy,scipy,cv2; print(mujoco.__version__,numpy.__version__,scipy.__version__,cv2.__version__)"
```

Expected core versions: `3.14.0 2.5.3 1.18.1 5.0.0`. The package snapshot includes historical optional libraries such as MediaPipe, Gymnasium, and pyserial so that preserved modules can be inspected and run. Do not install both `opencv-python` and `opencv-contrib-python` into the same environment; the snapshot chooses the latter. `get-pip.py` is an upstream bootstrap endpoint, not an immutable archived file; package versions are pinned separately. Package availability and network access are still required.

## 3. Restore the isolated ROS 2 runtime

ROS uses **Pixi 0.81.0**, the RoboStack Jazzy community channel, and its own **Python 3.12.15**. Do not install MuJoCo packages into this environment or merge its `site-packages` with the main interpreter. The saved [`pixi.lock`](dependencies/ros2/pixi.lock) records exact resolved packages, URLs, and hashes; [`pixi.toml`](dependencies/ros2/pixi.toml) alone is not an exact version pin.

In a fresh PowerShell window:

```powershell
Set-Location -LiteralPath 'D:\RoboticArm'
. .\integration\runtime\environment.ps1
New-Item -ItemType Directory -Force -Path '.\software\ros2' | Out-Null
Copy-Item -LiteralPath '.\docs\dependencies\ros2\pixi.toml', '.\docs\dependencies\ros2\pixi.lock' -Destination '.\software\ros2'
$projectPixi = 'D:\RoboticArm\software\ros2\pixi.exe'
Invoke-WebRequest 'https://github.com/prefix-dev/pixi/releases/download/v0.81.0/pixi-x86_64-pc-windows-msvc.exe' -OutFile $projectPixi
$projectPixiHash = (Get-FileHash -LiteralPath $projectPixi -Algorithm SHA256).Hash.ToLowerInvariant()
if ($projectPixiHash -ne '1b989b152ea13e881a641a112c7ea59c51818fd5ba84924c763b40b9b157dab9') { throw 'Pixi executable checksum mismatch' }
& $projectPixi install --manifest-path 'D:\RoboticArm\software\ros2\pixi.toml' --locked
& .\integration\runtime\run_ros2.ps1 probe
& .\integration\runtime\run_ros2.ps1 smoke
```

The wrapper sets local-only ROS domain 27 and `rmw_fastrtps_cpp`. It locates the restored environment through the manifest. The arm uses `/clock` and its world frame; the separate navigation simulation uses `/mobile/clock` and `mobile_*` frames. Time-aware arm consumers should set `use_sim_time=true` and handle backward clock jumps on reset. No full Nav2 or MoveIt installation is implied by the standard messages. Navigation uses `PoseStamped` goals and `Trigger` services because `nav2_msgs` was absent in the tested environment.

## 4. Launch and inspect

In a fresh PowerShell window after both environments are ready:

```powershell
& 'D:\RoboticArm\START_SIMULATION.ps1'
```

This starts the arm HTTP backend at `127.0.0.1:8770`, its ROS bridge, the mobile-base backend at `127.0.0.1:8771`, and the mobile ROS bridge. Open `http://127.0.0.1:8770`. The initial dashboard presents saved evidence; live tabs let the simulation be reset, stopped, or run. The mounted mobile-arm recording is a separate validated mission, not the same live world as the arm and navigation tabs.

Use `START_SIMULATION.ps1 -NoBrowser` to launch without opening a browser. Run `STOP_SIMULATION.ps1` to stop these integration services. Inspect `results\integration\runtime_server_error.log`, `arm_ros_error.log`, and the navigation logs if startup fails. Keep ports 8770 and 8771 free; do not run duplicate bridges publishing the same topics.

## 5. Optional CAD tools

Install or extract **FreeCAD 1.1.4** from its [official release](https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.4) under:

```text
D:\RoboticArm\software\freecad\FreeCAD_1.1.4-Windows-x86_64-py311
```

The recorded Windows `.7z` archive SHA256 is `4828741fc91ee37fafcdb97a1abacb18b04ba451ac4372d9ff7a7349b36f4d6d`. Preserve the archive's internal folder structure when extracting. Open `design\v3\AnthroArm27_ReferenceV3.FCStd` for the editable native assembly or the companion STEP for exchange. CAD regeneration uses the macros/scripts alongside those files and writes the project CAD/mesh outputs; it is unnecessary merely to replay the saved simulation. The grasp video recorder also references FreeCAD's `data\fonts\osifont.ttf`, so install this layout before regenerating that recording.

**OpenSCAD 2021.01** is an optional dependency for the earlier parametric concept. Restore it from the [official downloads](https://openscad.org/downloads.html) to `software\openscad\openscad-2021.01` if using those scripts. It is not required for the current MuJoCo meshes.

SOLIDWORKS macros and transfer material require a separately licensed compatible SOLIDWORKS environment. The historical test used Design Premium 2026 SP0. The local source archive does not contain the unrecovered native assembly ZIP and does not reproduce a validated Motion/FEA study. Read `solidworks\START HERE.txt` before treating these assets as a working native assembly.

## 6. Optional local vision-language experiment

The runtime dashboard can show the saved report without downloading weights. To rerun inference, restore a separate target directory instead of changing the simulation or ROS environments. The CPU PyTorch pair is taken from the [official previous-version instructions](https://pytorch.org/get-started/previous-versions/).

```powershell
Set-Location -LiteralPath 'D:\RoboticArm'
. .\scripts\environment.ps1
$py = 'D:\RoboticArm\software\python\python.exe'
New-Item -ItemType Directory -Force -Path '.\software\vision_language' | Out-Null
& $py -m pip install --no-deps --target '.\software\vision_language' --index-url 'https://download.pytorch.org/whl/cpu' --requirement '.\docs\dependencies\requirements-vlm-cpu.txt'
& $py -m pip install --no-deps --target '.\software\vision_language' --requirement '.\docs\dependencies\requirements-vlm.txt'
& $py '.\integration\download_vlm.py'
& $py '.\integration\capture_vlm_input.py'
& $py '.\integration\vision_language.py'
```

The downloader pins `HuggingFaceTB/SmolVLM-256M-Instruct` revision `7e3e67edbbed1bf9888184d9df282b700a323964`, obtains files from its official Hugging Face repository, and verifies the safetensors LFS hash. Its [saved download manifest](dependencies/smolvlm-download-manifest.json) records the original files and checksums. Inference is local CPU float32, uses local files, and does not enable remote model code. The experiment's wrong raw-scene answer and correct cropped-cube answer must both remain visible when presenting the result. It does not drive the robot.

## 7. Reproduce the measured simulation tests

These scripts move only simulated bodies. Stop live commands before running tests, retain the frozen `integration\grasping\policy.json`, and copy important result reports before a rerun. Run compute-intensive suites sequentially; their wall-clock duration depends on the host. No clean-install rerun or cross-platform numerical equivalence is claimed.

In the main project Python environment:

```powershell
. 'D:\RoboticArm\scripts\environment.ps1'
$py = 'D:\RoboticArm\software\python\python.exe'
& $py '.\integration\grasping\validate.py'
& $py '.\integration\grasping\test_camera.py'
& $py '.\integration\navigation\run_mission.py' --no-video
& $py '.\integration\navigation\validate_navigation.py'
& $py '.\integration\mobile_manipulation\validate.py'
```

Expected saved results are 10/10 grasp cases plus the lifecycle checks, 6/6 camera cases, seven navigation goals, sensor-only replay agreement, and 3/3 mounted-arm trials. Inspect the result JSON fields rather than assuming successful completion from process exit alone. `train.py` can regenerate the grasp search/training output but changes the frozen policy and associated evidence; retraining is a separate experiment.

To regenerate recordings, run `integration\grasping\record.py`, `integration\navigation\run_mission.py` without `--no-video`, and `integration\mobile_manipulation\record.py`. These render actual simulated trajectories. Media validation scripts and JSON files report decoded-frame checks; recording availability does not replace physical scoring.

For arm ROS validation, stop the standard launcher first, start only the arm backend, then run the ROS test in another shell. The test creates and terminates its own arm bridge:

```powershell
# Shell A: main interpreter; keep running while the ROS test executes.
. 'D:\RoboticArm\scripts\environment.ps1'
& 'D:\RoboticArm\software\python\python.exe' 'D:\RoboticArm\integration\runtime_server.py'
```

```powershell
# Shell B: isolated ROS interpreter.
& 'D:\RoboticArm\integration\runtime\run_ros2.ps1' python -B -u 'D:\RoboticArm\integration\runtime\test_arm_bridge.py'
```

After that test, stop Shell A with Ctrl+C before restarting the full launcher. For the separate navigation ROS pipeline test, start the standard launcher and run:

```powershell
& 'D:\RoboticArm\integration\runtime\run_ros2.ps1' python 'D:\RoboticArm\integration\navigation\test_ros_pipeline.py'
```

This test resets/drives the simulated base through ROS commands; do not issue dashboard commands concurrently. The expected arm report has 23 passing checks; the navigation ROS report has six. Saved evidence lives under `results\integration\runtime` and `results\integration\navigation`.

## 8. What the export excludes

Installed Python/FreeCAD/OpenSCAD/ROS environments, installers, caches, browser profiles, the large SmolVLM weights, and temporary files are recreated rather than committed. The smaller MediaPipe hand-landmark task asset is included with its upstream provenance and license notice. The dependency directory preserves exact package snapshots, ROS lock data, model revision/hashes, and source URLs. It does not grant redistribution rights for proprietary SOLIDWORKS software or third-party model/software assets. Physical prototype wiring plans and firmware are historical planning material, not a completed or validated hardware build.

See [software sources](dependencies/SOFTWARE_SOURCES.md), [tested environment](dependencies/tested-environment.json), and the root README for evidence boundaries.
