AnthroArm27 full native static build V5: STAGED SOURCE, native run unverified.

Upload the macro source and all 28 STEP files FLAT in one folder. Import BAS
into a SOLIDWORKS VBA project with SOLIDWORKS type and constants references.
Save its SWP in that folder, then run main. The source is not a binary SWP.

V5 retains V4 imports, strict 293-solid/zero-sheet checks, corrected Transform2
setter, native MathPoint placement checks and fixed 28-component assembly.
After successful native save it runs Windows built-in PowerShell invisibly to
ZIP only this unique output folder. The ZIP is placed beside the running macro.
The compression/ZIP validation job has a 60-second wait timeout (startup and
cleanup may add time). Exact 30 filenames/sizes and ZIP streams are checked.
No network is used. Existing files are never replaced. A failed ZIP step leaves
the native parts, assembly, build log and any partial ZIP available for inspection.

The ZIP build log ends at ZIP_REQUESTED; post-packaging result is logged to the
original live folder after compression, not retroactively inserted in the ZIP.
The final success message identifies the ZIP to download before session expiry.
All components remain fixed. No mates, Motion Analysis, FEA or hardware test.

Official references:
https://help.solidworks.com/2021/english/api/sldworksapi/Align_Assembly_Component_to_Assembly_Origin_and_Planes_Example_VB.htm
https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.archive/compress-archive?view=powershell-5.1
https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/wait-job
