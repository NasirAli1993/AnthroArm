# Dependency provenance

These manifests describe the tested installation. Installed applications, package caches, browser profiles, model weights, and downloaded installers are excluded from the repository. A fresh reconstruction has not yet been validated; consult [Setup](../SETUP.md) for the exact D: layout and commands.

| Component | Tested version / pin | Upstream source |
|---|---|---|
| Python simulation interpreter | 3.12.10, Windows x64 embeddable archive | [Python release directory](https://www.python.org/ftp/python/3.12.10/) |
| Python simulation packages | [Exact package snapshot](requirements-simulation.txt) | [Python Package Index](https://pypi.org/) and each package's upstream metadata |
| MuJoCo | 3.14.0 | [Python documentation](https://mujoco.readthedocs.io/en/stable/python.html), [source](https://github.com/google-deepmind/mujoco) |
| FreeCAD | 1.1.4, Windows x64 portable archive | [Official release](https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.4) |
| OpenSCAD, earlier design only | 2021.01 | [Official downloads](https://openscad.org/downloads.html) |
| Pixi | 0.81.0 | [Official release](https://github.com/prefix-dev/pixi/releases/tag/v0.81.0) |
| Native Windows ROS 2 Jazzy | [Manifest](ros2/pixi.toml) and [exact solved lock](ros2/pixi.lock), separate Python 3.12.15 | [RoboStack setup](https://robostack.github.io/GettingStarted.html), [RoboStack Jazzy channel](https://prefix.dev/channels/robostack-jazzy), [ROS Jazzy documentation](https://docs.ros.org/en/jazzy/) |
| PyTorch / torchvision | 2.8.0+cpu / 0.23.0+cpu | [Official version pairing and CPU index instructions](https://pytorch.org/get-started/previous-versions/) |
| VLM support packages | [Exact non-PyTorch snapshot](requirements-vlm.txt) | [Transformers](https://github.com/huggingface/transformers) and upstream package metadata |
| SmolVLM-256M-Instruct | `HuggingFaceTB/SmolVLM-256M-Instruct`, revision `7e3e67edbbed1bf9888184d9df282b700a323964` | [Official model repository](https://huggingface.co/HuggingFaceTB/SmolVLM-256M-Instruct), [saved download manifest](smolvlm-download-manifest.json) |

RoboStack is a community distribution of ROS packages. The project does not label it as the official ROS Windows installer, and it does not contain full Nav2 or MoveIt. The Python package requirements pin versions; they are not a universal cross-platform binary lock. The Pixi lock includes exact package URLs and hashes for the tested Windows environment.

FreeCAD's `osifont.ttf` is referenced by the grasp recording script through the restored FreeCAD installation. Its license and attribution remain those of the upstream distribution. Model weights are obtained separately, along with their upstream model card and license. SOLIDWORKS is proprietary software requiring an appropriate separate license; it is not included in these manifests or redistributed by this repository.

For archive hashes, paths, and environment versions, see [tested-environment.json](tested-environment.json). Third-party license terms remain applicable to the components and assets they govern. No new project license is assigned by this document.
