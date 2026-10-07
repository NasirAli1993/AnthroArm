AutoDIPMateV3 - staged native two-link index DIP mate test
STATUS: NOT_COMPILED_IN_SOLIDWORKS / NOT_EXECUTED_IN_SOLIDWORKS
The source and its official API usage have been reviewed. No native result,
native assembly, solved angle, or successful test is claimed by this file.

V3 FIX
Transform2 property setter uses comp.Transform2 = t without Set, matching
official VBA examples. Full-arm native V3 failed with error 438 at the
Set form after all 28 STEP parts imported. Getter Set t = comp.Transform2
remains unchanged. DIP V1 and V2 sources are preserved.

V2 FIX
Uses explicit zero/nonzero Boolean comparisons for native COM returns.
Native V2 full-arm execution showed SaveAs success, zero errors, and an
incorrect failure from bitwise Not applied to a noncanonical true value.
This repair changes only result interpretation, not geometry acceptance.
DIP V1 remains preserved; run this V3 version for the native finger test.

PURPOSE
Create a real SOLIDWORKS two-component assembly from intact multibody STEP
links; constrain a hinge; command and measure a small repeatable native mate
solve; finally configure a limited hinge. This tests native assembly kinematics.
It does not create a Motion Study timeline, run Motion Analysis dynamics,
validate collisions or forces, run FEA, or prove a physical mechanism works.

INPUTS AND RUN
1. Keep these exact files together in the trial's uploaded file folder:
   AutoDIPMateV3.swb (or a converted/saved AutoDIPMateV3.swp)
   index_intermediate.step  [12 solid bodies]
   index_distal.step        [10 solid bodies]
   The STEP sources are D:\RoboticArm\solidworks\transfer\links\ locally.
2. In native SOLIDWORKS, Tools > Macro > Edit the SWB and save its conversion
   to SWP in that same folder. Alternatively import AutoDIPMateV3.bas into a
   native VBA project with its old module removed. The BAS has a module-name
   attribute; the SWB does not. Do not paste the BAS attribute into the editor.
3. VBA Tools > References: select the SOLIDWORKS 2026 Type Library and
   SOLIDWORKS 2026 Constant type library. Compile before Run main.
4. A configured assembly template is required. Close either source STEP if
   already open before running; existing native output parts need not be edited.
5. The running macro resolves GetCurrentMacroPathName, not a hard-coded cloud
   path. New parts, checkpoint assemblies, CSV and log go in one newly created
   sibling DIP_Mate_<timestamp> folder. Existing outputs are never overwritten.
6. Download that whole output folder to D: promptly during the live trial.
   Preserve the CSV/log even if the macro stops. The main project ledger is
   deliberately not modified by this staged macro.

GEOMETRY AND MATES
STEP units are file-specified mm; native SOLIDWORKS API lengths are metres.
The isolated intermediate link is fixed at identity. The distal link starts
with translation [0,0,0.024] m and rotation +10 degrees about local Y.
Source joint limits are 0 to 1.4 rad = 0 to 80.214091 degrees.

The macro finds the native default planes by their measured transforms,
renames them DIP_YZ, DIP_XZ, DIP_XY, and creates a parent plane 24 mm along +Z.
A parent datum axis through that station and the YZ plane defines the hinge.
The part has no physical distal barrel at that station; this datum is based on
the source joint definition and does not add a physical bearing design.

It then creates these actual SOLIDWORKS mate features:
- Concentric: parent datum axis to distal link's real analytic 2.4 mm root bore.
  Rotation remains unlocked. The largest matching cylindrical bore face is
  selected geometrically, not by unstable face number.
- Coincident: parent and child XZ planes, removing translation along the axis.
- Standard angle: assembly-context YZ reference planes with parent Y axis as
  direction reference. This is the driven scalar constraint for the sweep.

Read-only FreeCAD STEP preflight confirmed 12/10 valid solids. The largest
distal root bore face has area 67.1312608483 mm2, exceeding the two 12.0637157898
mm2 cheek bore faces. See ..\studies\dip_source_bore_audit.json. This is source
geometry evidence only; the native importer and mate solver remain untested.

NATIVE CHECKS TO BE EXECUTED
Each STEP must actually import as one Part, exact expected solid count, zero
sheet bodies, and pass a gross size check. No bodies are fused or removed.
Datums must have their expected measured origins/axes. Selected assembly
references must report the correct owning component. Mate feature errors or
warnings stop the run. A preference readback for SolidandSurface known to
disagree with the native UI is logged; the actual geometry gates remain strict.

Two repeats of 0, 10, 0 degrees are rebuilt and measured. These are ordered
samples, not 0/2/4-second motion keyframes. The CSV derives actual signed angle
from the solved distal component transform, not the commanded dimension.
Acceptance: angle error <=0.5 deg; hinge origin drift <1 micrometre; normalized
Y-axis deviation <1e-6; child floating; parent origin unchanged; all mates clean.
These are numerical smoke-test tolerances, not manufacturing specifications.

After the sweeps, the standard angle is converted to an advanced limit angle,
0..1.4 rad. The readback and current pose are checked. This does NOT establish
that dragging or a motor obeys the endpoint stops; that needs a separate test.

OUTPUTS IF EXECUTION REACHES EACH STAGE
index_intermediate.SLDPRT, index_distal.SLDPRT: intact bodies + reference datums.
DIP_PLACEMENT_ONLY.SLDASM: initial fixed/floating placement.
DIP_HINGE_MATED.SLDASM: concentric and axial coincidence only.
DIP_DRIVEN_10DEG.SLDASM: constrained positive flexion pose.
DIP_DRIVEN_RETURN_ZERO.SLDASM: standard-angle result after two sweeps.
DIP_LIMITED_0_TO_80DEG.SLDASM: configured 0..80.214091 degree limited hinge.
Native_DIP_Mate.log: timestamped native operations, return/error codes, failures.
native_pose_measurements.csv: commanded and actual angles and axis/origin errors.

REQUIRED REVIEW AFTER A SUCCESSFUL RUN
Reopen the final assembly and verify both references resolve. Capture the native
mate tree and 10-degree / returned-zero states; native Measure should confirm
dimensions. Read the complete log and CSV. Then test limit endpoints, drag DOF,
interference across the range, and a genuine Motion Study as separate studies.
Do not infer physical bearing clearance, motor torque, strength, camera control
or prototype readiness from this small kinematic test.

OFFICIAL API BASIS (checked 2026-10-06)
CreateMateData / CreateMate and typed mate feature creation:
https://help.solidworks.com/2020/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IAssemblyDoc~CreateMateData.html
https://help.solidworks.com/2023/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IAssemblyDoc~CreateMate.html
Angle entities mark 1, direction reference mark 67108864; edit via GetDefinition
and ModifyDefinition:
https://help.solidworks.com/2022/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IAngleMateFeatureData.html?id=2.2.1.4
https://help.solidworks.com/2020/English/api/sldworksapi/Create_Limit_Angle_Mate_Example_VB.htm
Advanced angle value is a starting angle, not a forced target:
https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IAngleMateFeatureData~Angle.html
Plane transform and axis creation:
https://help.solidworks.com/2022/english/api/sldworksapi/get_the_normal_and_origin_of_a_reference_plane_using_its_transform_example_vb.htm
https://help.solidworks.com/2016/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.imodeldoc2~insertaxis2.html
https://help.solidworks.com/2021/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IFeatureManager~InsertRefPlane.html
Actual feature errors after rebuilding:
https://help.solidworks.com/2024/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IFeature~GetErrorCode2.html

Official Transform2 setter example:
https://help.solidworks.com/2021/english/api/sldworksapi/Align_Assembly_Component_to_Assembly_Origin_and_Planes_Example_VB.htm
