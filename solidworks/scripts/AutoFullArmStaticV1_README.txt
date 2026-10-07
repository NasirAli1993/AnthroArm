AUTO FULL ARM STATIC V1 - STAGED SOURCE, NOT A NATIVE TEST RESULT

Purpose
Import the 28 local-coordinate STEP links as 28 multibody native parts,
then position them in one native static SOLIDWORKS assembly at the manifest
home pose. Expected total: 293 solid bodies. All 28 components are fixed
after placement to preserve this initial static geometry stage.

This does not create revolute mates, moving joints, Motion studies, contact
tests, structural studies, or validated manufacturing details.

Cloud session setup
1. Upload all 28 transfer/links/*.step files FLAT into the same directory.
   Do not upload the already assembled full_arm_home_reference.step instead.
2. Upload AutoFullArmStaticV1.swb (plain VBA source), or import the .bas module
   into a new .swp project. Save the executing macro in that same directory.
   The code resolves GetCurrentMacroPathName; no cloud drive is hard-coded.
3. Add both SOLIDWORKS type library and SOLIDWORKS constants type library
   in the VBA editor Tools > References. Ensure there is only one public
   no-argument main in the selected module/project.
4. Compile in the actual SOLIDWORKS VBA editor before executing. Offline
   source checks are not a substitute for this step. In particular confirm
   AddComponent5 is available with its expected eight arguments.
5. Close prior imported STEP documents, preserving any needed user work.
   An already open source STEP aborts the fresh import instead of reusing it.
   A valid default assembly template must already be configured.
6. Run main. A unique sibling AnthroArm27_Static_DATE_TIME_TIMER folder is
   created. No pre-existing output is overwritten. Each imported native
   part is saved immediately, then the complete static assembly is saved.
7. Download the entire output folder, including every referenced SLDPRT,
   the SLDASM and Native_Static_Build.log, to D:/RoboticArm/solidworks/results.
   Downloading only the SLDASM will leave its external component references
   missing on another machine. Keep the native parts beside the assembly.

Runtime checks
- 28 required flat sibling STEP files are present before import.
- Native MathPoint.MultiplyTransform is exercised on local origin and
  three 10 mm axis points for every link before geometry imports.
- Classic STEP importer, multibody mapping, file-specified units (mm),
  solids/surfaces enabled, automatic healing disabled. Previous application
  preferences are captured and restored; setter success is read back.
- Each imported document is a Part with its exact expected solid count and
  zero sheet bodies. Approximate bounding boxes are logged in mm. A broad
  3-500 mm largest-span gate rejects gross unit scaling mistakes only.
- Each part save is checked for return/error status and non-empty file.
- Imported native parts remain open because AddComponent5 requires the
  component models in memory.
- Any default fixed state is removed before Transform2 is assigned.
- Component placement is checked through actual native MathPoint values,
  then fixed. Placement is checked again after rebuilding the assembly.
- Assembly has exactly 28 top-level components; final native save checked.
- Log is opened/appended/closed for every line to retain progress if the
  time-limited remote trial ends unexpectedly.

Numerical conventions
Manifest: p_world = R * p_local + t, source translation in millimetres.
SOLIDWORKS ArrayData:
[M00,M10,M20,M01,M11,M21,M02,M12,M22,M03/1000,M13/1000,M23/1000,1,0,0,0]
Imported geometry is already correctly sized; scale remains 1.
Component.Transform2 is the world transform relative to assembly root.
The root's 1080 mm translation and 180-degree X rotation are included once.
Only local-frame link files receive these transforms.

Evidence limits
GetBodyBox is approximate. This macro does not prove exact dimensional
accuracy, healed B-rep quality, correct material properties, interference
freedom, joint behavior, static strength, torque feasibility, or hardware
function. Native reopen/measure/diagnostics checks must follow execution.
Mates and all engineering studies remain separate subsequent stages.

Files
AutoFullArmStaticV1.swb                 plain VBA source
AutoFullArmStaticV1.bas                 importable VBA module equivalent
prepare_full_static_macro.py           reproducible source generator
AutoFullArmStaticV1_source_audit.json   OFFLINE checks only

Official API references checked 2026-10-06
NewDocument(TemplateName, PaperSize, Width, Height):
https://help.solidworks.com/2021/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.ISldWorks~NewDocument.html
GetDocumentTemplate(Mode, TemplateName, PaperSize, Width, Height):
https://help.solidworks.com/2016/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISldWorks~GetDocumentTemplate.html
AddComponent5 existence and current interface:
https://help.solidworks.com/2026/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IAssemblyDoc_members.html
Expected eight-argument signature must be confirmed in actual VBA compiler:
AddComponent5(CompName, ConfigOption, NewConfigName,
UseConfigForPartReferences, ExistingConfigName, X, Y, Z)
The direct official AddComponent5 detail page returned only a generic
portal shell during this preparation; do not call it verified compilation.
Current configuration enum:
https://help.solidworks.com/2026/english/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swAddComponentConfigOptions_e.html
File units enum:
https://help.solidworks.com/2024/english/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swImportNeutralUnits_e.html
Select4(Append, Data, ShowPopup):
https://help.solidworks.com/2024/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IComponent2~Select4.html
FixComponent and UnfixComponent are parameterless Subs:
https://help.solidworks.com/2024/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IAssemblyDoc~FixComponent.html
https://help.solidworks.com/2024/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IAssemblyDoc~UnfixComponent.html
