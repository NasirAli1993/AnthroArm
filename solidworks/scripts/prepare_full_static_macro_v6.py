"""V6: preserve proven native static geometry; close saved docs, freeze log, ZIP."""
from pathlib import Path
import re,json,hashlib,shutil,zipfile
ROOT=Path('D:/RoboticArm/solidworks')
S=ROOT/'scripts'
v5=(S/'AutoFullArmStaticV5.swb').read_text(encoding='ascii')
archive=(S/'ArchiveNativeResultsV1.swb').read_text(encoding='ascii')
source=v5.replace('AutoFullArmStaticV5','AutoFullArmStaticV6')
helpers=archive[archive.index('Private Function PowerShellLiteral'):archive.index('Public Sub main()')]
helpers=helpers.replace('zipPath = parentPath & "\\" & leaf & "_NATIVE_RECOVERED_" & recoveryStamp & ".zip"', 'zipPath = parentPath & "\\" & leaf & "_NATIVE.zip"')
assert 'recoveryStamp' not in helpers
start=source.index('Private Function PowerShellLiteral')
end=source.index("' Sole public no-argument entry point.")
source=source[:start]+helpers+source[end:]

close_and_image=r'''
Private Sub SaveOptionalOverview(ByVal model As SldWorks.ModelDoc2, ByVal destination As String)
    Dim result As Boolean, failureNumber As Long, failureText As String
    On Error GoTo OptionalImageFailed
    Check Len(Dir$(destination)) = 0, "Refusing existing overview image"
    ' Current native assembly viewport: actual CAD pixels, no synthetic rendering.
    result = model.SaveBMP(destination, 0, 0)
    LogLine "OPTIONAL_NATIVE_OVERVIEW_RETURN=" & CStr(result) & " PATH=" & destination
    If (result <> False) Then
        If Len(Dir$(destination)) > 0 Then
            LogLine "OPTIONAL_NATIVE_OVERVIEW_BYTES=" & CStr(FileLen(destination))
        Else
            LogLine "WARNING optional overview API returned True but file not found"
        End If
    Else
        LogLine "WARNING optional overview was not saved; native CAD and ZIP stages continue"
    End If
    Exit Sub
OptionalImageFailed:
    failureNumber = Err.Number: failureText = Err.Description
    On Error Resume Next
    LogLine "WARNING optional overview failed " & CStr(failureNumber) & " | " & failureText
End Sub

Private Sub CloseSavedNativeDocuments(ByVal outputFolder As String)
    Dim result As Boolean, firstDocument As Object, i As Long
    For i = 0 To 27
        Check Len(Dir$(nativePaths(i))) > 0, "Saved native part missing before closing: " & linkNames(i)
        Check FileLen(nativePaths(i)) > 0, "Saved native part empty before closing: " & linkNames(i)
    Next i
    Check Len(Dir$(outputFolder & "AnthroArm27_STATIC_HOME.SLDASM")) > 0, "Saved static assembly missing before closing"
    Check FileLen(outputFolder & "AnthroArm27_STATIC_HOME.SLDASM") > 0, "Saved static assembly empty before closing"
    LogLine "SAVED_NATIVE_FILE_PREFLIGHT_PASS: 28 parts and one assembly on disk"
    LogLine "CLOSE_ALL_DOCUMENTS_BEGIN IncludeUnsaved=True; dedicated project trial; no automatic save requested"
    result = swApp.CloseAllDocuments(True)
    LogLine "CLOSE_ALL_DOCUMENTS_RETURN=" & CStr(result)
    Check (result <> False), "CloseAllDocuments returned False; files may remain locked"
    Set firstDocument = swApp.GetFirstDocument()
    Check firstDocument Is Nothing, "A CAD document remains open; do not archive potentially locked files"
    LogLine "NO_OPEN_CAD_DOCUMENTS_VERIFIED"
    ' Drop stale references after SOLIDWORKS confirms all documents are closed.
    For i = 0 To 27
        Set importedModels(i) = Nothing
        Set components(i) = Nothing
    Next i
End Sub

'''
source=source.replace('Private Function PowerShellLiteral',close_and_image+'Private Function PowerShellLiteral',1)
source=source.replace('Private Sub CreateStaticAssembly(ByVal outputFolder As String, ByVal templatePath As String)', 'Private Sub CreateStaticAssembly(ByVal outputFolder As String, ByVal templatePath As String, ByVal overviewPath As String)')
source=source.replace('    LogLine "STATIC_ASSEMBLY_SAVED: 28 fixed components, 293 source solids; NO MATES OR MOTION"', '    LogLine "STATIC_ASSEMBLY_SAVED: 28 fixed components, 293 source solids; NO MATES OR MOTION"\n    SaveOptionalOverview model, overviewPath')
source=source.replace('Dim templatePath As String, failureText As String, failureNumber As Long', 'Dim templatePath As String, failureText As String, failureNumber As Long\n    Dim overviewPath As String, buildLogPath As String, packageLogPath As String')
source=source.replace('    CreateStaticAssembly outputFolder, templatePath', '    overviewPath = folder & "AnthroArm27_Static_" & runStamp & "_OVERVIEW.bmp"\n    CreateStaticAssembly outputFolder, templatePath, overviewPath')
needle='    zipPath = PackageNativeOutput(outputFolder, folder)'
replacement=r'''    CloseSavedNativeDocuments outputFolder
    LogLine "NATIVE_STATIC_RESULTS_READY: all native saves passed; documents closed; build log is now frozen"
    buildLogPath = runtimeLog
    packageLogPath = folder & "Native_Static_Package_" & runStamp & ".log"
    Check Len(Dir$(packageLogPath)) = 0, "Refusing existing packaging receipt log"
    ' All archive messages go outside the native folder. Its 30-file payload is immutable during ZIP.
    runtimeLog = packageLogPath
    LogLine "PACKAGING_STARTED_AFTER_SAVED_DOCUMENTS_CLOSED"
    LogLine "FROZEN_NATIVE_BUILD_LOG=" & buildLogPath
    LogLine "OPTIONAL_OVERVIEW_OUTSIDE_ARCHIVE=" & overviewPath
    zipPath = PackageNativeOutput(outputFolder, folder)
    LogLine "VERIFIED_NATIVE_ARCHIVE_READY=" & zipPath'''
assert source.count(needle)==1
source=source.replace(needle,replacement)
source=source.replace('"All components fixed. No mates, Motion or FEA performed.", vbInformation','"Download ZIP now. All components fixed; no mates, Motion or FEA performed.", vbInformation')
source=source.replace("' After native success only: hidden local PowerShell ZIP packaging; no network/account operations.","' After native saves: optional BMP, close all trial CAD documents, freeze build log, hidden local ZIP.\n' Dedicated project trial only. No network/account operations; no auto-save on close.")

init=lambda text: re.search(r'Private Sub InitData\(\)(.*?)End Sub',text,re.S).group(1)
assert init(source)==init(v5)
assert '$required=@(' in source and 'Get-ChildItem' not in source
assert 'Set comp.Transform2 =' not in source and 'comp.Transform2 = transform' in source
assert re.findall(r'^Public Sub (\w+)',source,re.M)==['main']
assert max(map(len,source.splitlines()))<1024
assert len(re.findall(r'^Private (?:Sub|Function) ',source,re.M)) == len(re.findall(r'^End (?:Sub|Function)$',source,re.M))-1
for ext in ['swb','bas']:
    p=S/('AutoFullArmStaticV6.'+ext)
    assert not p.exists(),'Preserve existing source'
    p.write_text(('Attribute VB_Name = "AutoFullArmStaticV6"\n' if ext=='bas' else '')+source,encoding='ascii',newline='\r\n')
audit=json.loads((S/'AutoFullArmStaticV5_source_audit.json').read_text())
audit.update(status='STAGED V6 source; native V6 execution pending. Root reports V5 static geometry succeeded and ArchiveV1 succeeded after manual close-all.',
    macro_sha256=hashlib.sha256((S/'AutoFullArmStaticV6.swb').read_bytes()).hexdigest(),
    maximum_physical_line_length=max(map(len,source.splitlines())),
    only_behavior_change_from_v5='Optional nonblocking native BMP, close saved documents, frozen native build log, allowlist archive with external packaging receipt',
    geometry_initializers_unchanged=True,
    packaging='Exact 30 named files to flat ZIP after CloseAllDocuments(True) and GetFirstDocument Nothing; 60-second Wait-Job bound, exact filenames/sizes/all streams checked',
    log_freeze='Native_Static_Build.log is not modified during/after compression; package messages use sibling Native_Static_Package_<stamp>.log',
    evidence='Optional SaveBMP current native viewport outside output folder/ZIP. Image failure does not block archive.',
    native_execution=False)
(S/'AutoFullArmStaticV6_source_audit.json').write_text(json.dumps(audit,indent=2))
out=ROOT/'upload_full_static_v6'
assert not out.exists()
out.mkdir()
for p in (ROOT/'transfer/links').glob('*.step'): shutil.copy2(p,out/p.name)
assert len(list(out.glob('*.step')))==28
for name in ['AutoFullArmStaticV6.swb','AutoFullArmStaticV6.bas','AutoFullArmStaticV6_source_audit.json']: shutil.copy2(S/name,out/name)
(out/'READ_ME_V6.txt').write_text('''AnthroArm27 native static build V6. V6 native execution is pending.

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
''',encoding='ascii')
inventory=[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(out.iterdir())]
(out/'upload_inventory.json').write_text(json.dumps({'status':'STAGED V6 SOURCE; native run pending','files':inventory},indent=2))
archivePath=ROOT/'AnthroArm27_FullStaticV6_Upload.zip'
with zipfile.ZipFile(archivePath,'x',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(out.iterdir()): z.write(p,p.name)
with zipfile.ZipFile(archivePath) as z: assert z.testzip() is None and len(z.namelist())==33
print(json.dumps({'macro':str(S/'AutoFullArmStaticV6.bas'),'upload_folder':str(out),'zip':str(archivePath),'swb_sha256':audit['macro_sha256'],'zip_bytes':archivePath.stat().st_size},indent=2))
