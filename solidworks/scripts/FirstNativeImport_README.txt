FIRST NATIVE IMPORT MACRO - STAGED, NOT COMPILED OR EXECUTED
Prepared 2026-10-06. This agent has not run native SOLIDWORKS.

Purpose: one STEP -> one native multibody SLDPRT, solid-count evidence,
MathPoint transform convention checks and runtime log. No assembly or mates.

SUPPORTED EDITOR ROUTE
1. Upload FirstNativeImport.bas to the trial's observed file-upload location.
2. SOLIDWORKS: Tools > Macro > New. Save a new .swp in a runtime folder the trial
   actually supports. The trial desktop path must be observed, not guessed.
3. VBA editor: File > Import File (Ctrl+M), select FirstNativeImport.bas.
   Verify references to the SOLIDWORKS type library and SOLIDWORKS constants
   type library. Avoid an ambiguous generated main: run FirstNativeImport.main
   explicitly from the editor, or remove only the unused empty generated module.
4. Debug > Compile before execution. This source was not compiled locally.
5. Set STEP import units to File specified unit in SOLIDWORKS import options.
   Source STEP files are millimetres. The macro logs the current unit enum but
   does not guess an undocumented numeric value for the unit preference.
6. Run main. Supply the full observed runtime STEP path, an existing runtime
   output folder, and the expected count: index_intermediate=12, index_distal=10,
   full_arm_home_reference=293. The macro detects those filename defaults.
7. It saves <source_stem>_native.SLDPRT and a timestamped .log. Download both to D:.
   Preserve existing work: the macro refuses an already-open source and refuses
   existing output filenames. It never overwrites source files or closes models.

OPTIONAL LEGACY TEXT ROUTE
FirstNativeImport.swb has identical staged code without the VBA Attribute header.
SOLIDWORKS documentation recognizes .swb in Tools > Macro > Run/Edit and describes
conversion to .swp. Its Task Scheduler documentation describes .swb text files.
Try the legacy path only if the actual 2026 trial exposes it; conversion/runtime
compatibility has NOT been tested. A .bas file is a module, not a runnable .swp;
renaming a .bas to .swp does not create a VBA project.

WHAT THE CODE DOES
- Prompts for actual runtime/cloud paths; there is no C:/D:/Temporary Files guess.
- Logs SOLIDWORKS revision, source, destination, API return/error/warning codes.
- Checks MathPoint.MultiplyTransform against a +90-degree Y rotation and known
  metre translations using origin and three 10 mm basis points; tolerance 1e-9 m.
- Temporarily disables 3D Interconnect and automatic healing; selects neutral
  multibody-part mapping and solid/surface import. Restores preferences afterward,
  including on runtime errors. A restore failure is logged.
- GetImportFileData returns ImportStepData; MapConfigurationData=False; imports
  through LoadFile4(path, "r", importData, errors).
- Requires document type Part, exact expected solid count and no sheet bodies,
  using PartDoc.GetBodies2(swSolidBody/SheetBody, False) to include hidden bodies.
- Saves using the documented compatibility ModelDocExtension.SaveAs overload
  used in the official STEP example. It is superseded by SaveAs3 but was chosen
  here because its complete signature was verified from primary documentation.
- Retains all model content with ClearSelection2(True) before native SaveAs.
- Stops on error and writes the error number/description to the log if possible.

LIMITS
Body count + saved bytes do not prove dimensional accuracy or flawless geometry.
Approximate body boxes are logged in metres as a unit sanity aid, not toleranced
measurements. Run native Measure/Import Diagnostics and reopen the saved file.
No automated healing is attempted. Inspect save warnings even if save succeeds.
No staged log/result is claimed; only actual execution creates a runtime log.

OFFICIAL RESEARCH
SOLIDWORKS new macro / .swb and .swp workflow:
https://help.solidworks.com/2019/english/SolidWorks/sldworks/c_recording_playing_macros.htm?id=5.21
https://help.solidworks.com/2022/english/api/sldworksapiprogguide/GettingStarted/Edit_or_Debug_SolidWorks_Macro.htm?id=1.2.1.3
https://help.solidworks.com/2020/English/SolidWorks/sldworks/t_Creating_a_SOLIDWORKS_Macro_Template.htm
VBA import module menu and supported extensions:
https://learn.microsoft.com/en-us/office/vba/language/reference/user-interface-help/file-menu
https://learn.microsoft.com/en-us/office/vba/language/reference/user-interface-help/import-file-dialog-box
STEP import and SaveAs compatibility sample:
https://help.solidworks.com/2018/english/api/sldworksapi/Import_STEP_File_Example_CSharp.htm
https://help.solidworks.com/2015/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISldWorks~LoadFile4.html
https://help.solidworks.com/2018/english/api/swconst/FileOpenOptionsSTEPIGESACIS.htm
https://help.solidworks.com/2026/English/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swImportNeutralAssemblyStructureMapping_e.html
https://help.solidworks.com/2019/English/api/swconst/FileOpenOptionsGeneral.htm
Body enumeration:
https://help.solidworks.com/2022/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IPartDoc~GetBodies2.html
Transform convention and actual MathPoint pattern:
https://help.solidworks.com/2019/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IMathTransform.html
https://help.solidworks.com/2016/english/api/sldworksapi/Transform_Point_from_Component_Space_to_Assembly_Space_Example_CSharp.htm
