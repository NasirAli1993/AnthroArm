AnthroArm27 native static build V6. V6 native execution is pending.

Upload macro source and 28 STEP files FLAT beside the saved SWP. The native
VBA project needs SOLIDWORKS type and constants references. Run main once in
the dedicated project trial session. Existing input/output files are preserved.

V6 retains V5 geometry, exact 293-solid/zero-sheet tests, native transforms and
fixed 28-component assembly. After all native saves it optionally captures the
actual assembly viewport as BMP beside the macro (not in the ZIP), closes all
CAD documents without saving changes, and verifies no document remains open.
This close-all step is for the dedicated trial containing this project only.

Then it freezes Native_Static_Build.log and writes packaging messages to a new
sibling receipt log. A hidden local Windows PowerShell job archives only the
28 named SLDPRTs, assembly, and frozen build log. Temporary locks are excluded.
The flat ZIP is beside the macro: AnthroArm27_Static_<stamp>_NATIVE.zip.
The final success message identifies the ZIP. Download it before trial expiry.

Archive validation checks exact 30 filenames, uncompressed sizes and reads all
entry streams. Wait-Job timeout is 60 seconds; startup/cleanup may add time.
Original build files are not altered during or after compression. Optional BMP
failure does not block native saving/archiving. Packaging failure preserves all
native results and logs for diagnosis. No automatic save occurs when closing.

This is STATIC geometry. No mates, Motion Analysis, FEA or hardware test passed.
Official APIs: CloseAllDocuments(True), GetFirstDocument(), SaveBMP(path,0,0).
https://help.solidworks.com/2021/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISldWorks~CloseAllDocuments.html
https://help.solidworks.com/2023/english/api/sldworksapi/Save_Model_as_Bitmap_Example_VB.htm
