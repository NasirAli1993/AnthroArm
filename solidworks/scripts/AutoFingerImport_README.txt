AUTO FINGER IMPORT - STAGED SOURCE, NOT COMPILED OR EXECUTED
Prepared 2026-10-06.

Upload AutoFingerImport.swb beside the exact sibling files:
  index_intermediate.step (12 solids)
  index_distal.step       (10 solids)
Use SOLIDWORKS Tools > Macro > Run if the actual trial accepts legacy .swb.
The .bas alternative is for File > Import File in a new VBA .swp project.

The macro resolves its runtime directory using documented
ISldWorks.GetCurrentMacroPathName() As String. It assumes no particular cloud
drive, profile, or Temporary Files path. If conversion moves the running macro
away from its siblings, it reports the actual folder and stops on missing files.
There are no InputBox prompts. Both exact source files must be beside the running
macro; source documents already open cause a clear stop so work is preserved.

It creates unique timestamped SLDPRT files and a log in that same runtime folder.
Download those outputs to D:. The remote cloud folder is not the user's D: drive.
The original STEP files and original FirstNativeImport sources are unchanged.

It checks native transform maths, temporarily selects classic single multibody
part import, imports and checks 12/10 solid bodies with zero sheet bodies, checks
gross 5..100 mm size, logs approximate extents, and saves native parts. Preferences
are restored, including on errors. No automatic geometry healing occurs.
Exact dimensional accuracy and geometry diagnostics remain pending after a pass.
No assembly, mates, motion study, FEA or physical test is created by this macro.

Source has not been compiled against this trial's type libraries. If compilation
fails, inspect the displayed message and line before editing; do not claim a run.
Runtime failures include a MsgBox and timestamped log whenever log creation works.
An earlier successfully saved part remains if importing the second part fails.

Path API signature verified against official 2026 documentation:
https://help.solidworks.com/2026/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.ISldWorks~GetCurrentMacroPathName.html
Other import/macro/body/MathPoint source links are in FirstNativeImport_README.txt.
