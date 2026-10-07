AutoFingerImportV2 - staged replacement source
STATUS: NOT_COMPILED / NOT_EXECUTED by this preparation step.

This repairs a real compile error observed by the operator in the older macro:
ISldWorks.SetUserPreferenceToggle is a Sub (void), not a Boolean Function.
All six toggle calls now use Call, followed by GetUserPreferenceToggle readback.
Both integer calls likewise discard the documented Boolean return and verify
GetUserPreferenceIntegerValue readback. Restoration uses the same pattern.

Files: AutoFingerImportV2.bas and AutoFingerImportV2.swb.
Exact sibling inputs: index_intermediate.step (12 solids), index_distal.step
(10 solids). No assembly, motion study or FEA is created by this macro.

Native repair route (keeps existing corrected VBA references):
1. Save the current SWP project if useful as evidence.
2. Remove old AutoFingerImport module. Existing source is preserved locally.
3. VBA File > Import File: choose AutoFingerImportV2.bas.
4. Save SWP in the same remote Temporary Files directory as both STEP files.
5. Debug > Compile; only proceed on successful compile.
6. Run main. Capture actual success/error dialog and generated log, then
   download native parts and log to D:/RoboticArm/solidworks/native_results.
7. Reopen saved parts; independently measure dimensions and inspect geometry.

Alternative: Tools > Macro > Edit AutoFingerImportV2.swb converts it to SWP,
then enable the SOLIDWORKS and SOLIDWORKS constants type library references.
Do not interpret a closed Run dialog without output as a successful run.

Authoritative signatures checked (official SOLIDWORKS API Help):
- ISldWorks.SetUserPreferenceToggle: Sub, two arguments.
  https://help.solidworks.com/2022/english/api/sldworksapi/SolidWorks.interop.sldworks~SolidWorks.interop.sldworks.ISldworks~SetUserPreferenceToggle.html
- ISldWorks.SetUserPreferenceIntegerValue: Boolean Function, two arguments.
  https://help.solidworks.com/2024/english/api/sldworksapi/SolidWorks.interop.sldworks~SolidWorks.interop.sldworks.ISldWorks~SetUserPreferenceIntegerValue.html
- ISldWorks.GetUserPreferenceIntegerValue: integer Function, one argument.
  https://help.solidworks.com/2022/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.ISldWorks~GetUserPreferenceIntegerValue.html
- IModelDoc2.ClearSelection2: Sub, Boolean argument (already used correctly).
  https://help.solidworks.com/2023/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IModelDoc2~ClearSelection2.html
- IModelDocExtension.SaveAs: Boolean Function, six arguments; errors/warnings
  are output arguments. This is the older compatibility method, not SaveAs3.
  https://help.solidworks.com/2022/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IModelDocExtension~SaveAs.html
- ISldWorks.LoadFile4: returns ModelDoc2; four arguments, last is output error.
  Classic-import argument r requests a new document. Runtime validation needed.
  https://help.solidworks.com/2015/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISldWorks~LoadFile4.html
- IImportStepData.MapConfigurationData: Boolean get/set property; false imports
  geometric data only. Assignment is correct and does not return a status.
  https://help.solidworks.com/2023/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IImportStepData~MapConfigurationData.html
- IPartDoc.GetBodies2: body-array Function with body-type and visible-only args.
  https://help.solidworks.com/2022/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IPartDoc~GetBodies2.html
- IBody2.GetBodyBox: returns array of six approximate extents; not a precision
  measurement. Macro uses only a gross 5-to-100 mm scale plausibility gate.
  https://help.solidworks.com/2018/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IBody2~GetBodyBox.html
- IMathPoint.MultiplyTransform: returns a newly transformed math point.
  https://help.solidworks.com/2015/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IMathPoint~MultiplyTransform.html
- ISldWorks.GetCurrentMacroPathName: String Function, no arguments.
  https://help.solidworks.com/2026/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.ISldWorks~GetCurrentMacroPathName.html

The checked documentation establishes API declarations; it does not substitute
for compilation/execution in this actual SOLIDWORKS 2026 trial. Original source
and native-results ledger were not altered by this V2 preparation.
