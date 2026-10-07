ANTHRO / 25 — Editable CAD

Open the native model:
  powershell -ExecutionPolicy Bypass -File D:\RoboticArm\scripts\open_cad.ps1

Open the parametric OpenSCAD model:
  powershell -ExecutionPolicy Bypass -File D:\RoboticArm\scripts\open_openscad.ps1

FreeCAD:
  AnthroArm25.FCStd is a native, named solid assembly.
  Select a component in the tree. Component > Explanation states its purpose.
  Kinematics properties identify its robot joint, local axis, home and limits.
  Shapes and placements are editable native solids. These properties document the
  geometry; changing a documentation property alone does not rebuild a shape.
  Edit build_freecad.py and robot_spec.json, then run scripts/build_cad.ps1 to
  regenerate the full assembly, STEP and individual STL files.

OpenSCAD:
  arm_hand.scad contains editable modules for base, waist, upper arm, forearm,
  wrist, palm, knuckles and all 15 finger segments. Variables set hinge/tendon
  bores and display options. The Customizer exposes home/zero/grasp pose.
  Use export_part = "index_proximal" or another canonical link name to isolate
  that link. Set show_hardware=false / show_pads=false to inspect a bare shell.
  robot_parameters.scad is generated from robot_spec.json. Regenerate it with
  design/generate_scad_parameters.py after changing the canonical hierarchy.

Exports:
  AnthroArm25.step: full assembly, in its home pose, millimetres.
  parts/*.stl: individual CAD components in their own link-local coordinates.
  cad_manifest.json: shape validity, volumes, identities, explanations and files.
  results/cad_assembly.png and results/cad_scad_preview.png: model previews.
  results/cad_hand_detail.png: enlarged view of all five digits.
  results/cad_validation.json: native/STEP/STL round-trip and metadata checks.
  Recheck with scripts/validate_cad.ps1. It leaves the live CAD window untouched.

Geometry / physics relationship:
  300 mm upper arm; 250 mm forearm; 60 mm wrist stage.
  100 mm palm; 90 mm middle finger; adult-scale 190 mm hand.
  Five arm axes + four axes per digit = 25 independently controlled axes.
  CAD and the simulator use identical canonical link frames and pivot spacing.
  Physics uses simplified collision geometry, not the detailed STEP solids.
  Estimated mass/inertia are specified in the simulation model, not inferred
  from the unselected CAD materials.

Physical design status:
  The geometry illustrates a plausible mechanical layout and service access.
  2.1 mm pin bores, 1.4 mm tendon guides and mounting holes are exploratory.
  A complete cable transmission over all rotating joints is NOT engineered.
  Motors, reducers, bearings, controller electronics, tolerances, strength,
  payload rating, safety and fabrication all require independent validation.
  STL exports are provided for design inspection, not certified manufacturing.
