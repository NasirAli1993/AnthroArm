"""Archive-only recovery VBA: no CAD rebuild, no imports, no native edits."""
from pathlib import Path
import json,re,hashlib
ROOT=Path('D:/RoboticArm/solidworks')
S=ROOT/'scripts'
dip=(S/'AutoDIPMateV4.swb').read_text()
helpers=dip[dip.index('Private Function PowerShellLiteral'):dip.index('Public Sub main()')]
manifest=json.loads((ROOT/'transfer/assembly_manifest.json').read_text())
names=[link['name']+'.SLDPRT' for link in manifest['links']]+['AnthroArm27_STATIC_HOME.SLDASM','Native_Static_Build.log']
assert len(names)==30 and len(set(names))==30
required="    $required=@("+','.join("'"+name+"'" for name in names)+"); "
helpers=re.sub(r'^    commandText = commandText & "    \$required=.*$', '    commandText = commandText & "'+required+'"', helpers, flags=re.M)
helpers=helpers.replace('Left$(leaf, 9) = "DIP_Mate_"','Left$(leaf, 19) = "AnthroArm27_Static_"')
helpers=helpers.replace('zipPath = parentPath & "\\" & leaf & "_NATIVE.zip"','zipPath = parentPath & "\\" & leaf & "_NATIVE_RECOVERED_" & recoveryStamp & ".zip"')
helpers=helpers.replace('$files.Count -ne 9','$files.Count -ne 30').replace('$entries.Count -ne 9','$entries.Count -ne 30')
helpers=helpers.replace('Expected exactly nine named native deliverables','Expected exactly 30 named native deliverables')
helpers=helpers.replace('ZIP_VERIFIED_9_FILES_BYTES','ZIP_VERIFIED_30_FILES_BYTES')
helpers=helpers.replace("only this run's two parts, five assemblies, pose CSV and pre-package log snapshot",'explicit 28 native parts, assembly and existing native build log snapshot; temporary lock files excluded')
prefix=r'''Option Explicit
' STAGED SOURCE: no SOLIDWORKS compile/execution claimed here.
' Archive-only fallback: no STEP imports, geometry changes, save/rebuild or preferences.
' Save its SWP beside the V5 output folder, then run main.
' Uses late-bound Windows automation objects; no added references are needed.
Private runtimeLog As String
Private logReady As Boolean
Private recoveryStamp As String

Private Sub Check(ByVal condition As Boolean, ByVal message As String)
    If condition = False Then Err.Raise vbObjectError + 770, "ArchiveNativeResultsV1", message
End Sub

Private Sub LogLine(ByVal message As String)
    Dim channel As Integer, entry As String
    entry = Format$(Now, "yyyy-mm-dd hh:nn:ss") & " | " & message
    Debug.Print entry
    If logReady Then
        channel = FreeFile
        Open runtimeLog For Append As #channel
        Print #channel, entry
        Close #channel
    End If
End Sub

Private Function LatestSuccessfulV5Folder(ByVal macroFolder As String) As String
    Dim fso As Object, parent As Object, child As Object, stream As Object
    Dim contents As String, path As String, selectedName As String
    Set fso = CreateObject("Scripting.FileSystemObject")
    Set parent = fso.GetFolder(macroFolder)
    For Each child In parent.SubFolders
        If Left$(CStr(child.Name), 19) = "AnthroArm27_Static_" Then
            path = fso.BuildPath(child.Path, "Native_Static_Build.log")
            If fso.FileExists(path) <> False Then
                Set stream = fso.OpenTextFile(path, 1, False)
                contents = stream.ReadAll
                stream.Close
                If InStr(1, contents, "MACRO_VERSION=AutoFullArmStaticV5", vbBinaryCompare) > 0 Then
                    If InStr(1, contents, "STATIC_ASSEMBLY_SAVED: 28 fixed components, 293 source solids; NO MATES OR MOTION", vbBinaryCompare) > 0 Then
                        If InStr(1, contents, "COMPLETED_STATIC_STAGE_ONLY", vbBinaryCompare) > 0 Then
                            LogLine "SUCCESSFUL_V5_CANDIDATE=" & child.Path
                            If StrComp(CStr(child.Name), selectedName, vbBinaryCompare) > 0 Then
                                selectedName = CStr(child.Name)
                                LatestSuccessfulV5Folder = CStr(child.Path) & "\"
                            End If
                        End If
                    End If
                End If
            End If
        End If
    Next child
    Check Len(LatestSuccessfulV5Folder) > 0, "No sibling V5 output folder has the successful native static-build log checkpoints; nothing was archived"
End Function

'''
main=r'''
Public Sub main()
    Dim swApp As Object, fso As Object
    Dim path As String, folder As String, outputFolder As String, zipPath As String
    Dim failureNumber As Long, failureText As String
    On Error GoTo Failed
    Set swApp = Application.SldWorks
    path = swApp.GetCurrentMacroPathName()
    Check InStrRev(path, "\") > 0, "Save this SWP beside the native V5 output folder first"
    folder = Left$(path, InStrRev(path, "\"))
    recoveryStamp = Format$(Now, "yyyymmdd_hhnnss") & "_" & CStr(CLng(Timer * 1000#))
    runtimeLog = folder & "ArchiveNativeResults_" & recoveryStamp & ".log"
    Set fso = CreateObject("Scripting.FileSystemObject")
    Check fso.FileExists(runtimeLog) = False, "Refusing an existing archive recovery log"
    logReady = True
    LogLine "ARCHIVE_ONLY_STARTED; no imports, CAD edits, rebuilds or saves"
    LogLine "MACRO_PATH=" & path
    outputFolder = LatestSuccessfulV5Folder(folder)
    LogLine "SELECTED_LATEST_SUCCESSFUL_V5=" & outputFolder
    zipPath = PackageNativeOutput(outputFolder, folder)
    LogLine "ARCHIVE_ONLY_COMPLETED; original native files unchanged"
    MsgBox "Verified native archive ready: 28 parts, assembly and original build log." & vbCrLf & zipPath & vbCrLf & "Download this ZIP before the trial session expires.", vbInformation
    logReady = False
    Exit Sub
Failed:
    failureNumber = Err.Number: failureText = Err.Description
    On Error Resume Next
    LogLine "FAIL " & CStr(failureNumber) & " | " & failureText
    MsgBox "Archive-only recovery stopped " & CStr(failureNumber) & vbCrLf & failureText & vbCrLf & runtimeLog, vbExclamation
    logReady = False
End Sub
'''
source=prefix+helpers+main
assert len(names)==30
assert max(map(len,source.splitlines()))<1024
assert re.findall(r'^Public Sub (\w+)',source,re.M)==['main']
assert 'Get-ChildItem' not in source and '$required=@(' in source
assert 'LoadFile4' not in source and 'SaveAs(' not in source
assert 'Set comp.Transform2' not in source
for ext in ['swb','bas']:
    p=S/('ArchiveNativeResultsV1.'+ext)
    assert not p.exists(),'Do not replace existing source'
    p.write_text(('Attribute VB_Name = "ArchiveNativeResultsV1"\n' if ext=='bas' else '')+source,encoding='ascii',newline='\r\n')
ps=[]
for line in helpers.splitlines():
    m=re.match(r'    commandText = commandText & "(.*)"$',line)
    if m: ps.append(m.group(1).replace('""','"'))
(S/'test_archive_native_results_v1_payload.ps1').write_text('param([string]$source,[string]$target)\n'+'\n'.join(ps),encoding='ascii')
audit={'status':'Staged archive-only source; not executed in native SOLIDWORKS','public_entrypoints':['main'],'required_files':names,
'selection':'Lexically latest timestamped sibling V5 folder whose native log contains both static-save and completed-static checkpoints',
'no_cad_changes':True,'explicit_allowlist_excludes_temporary_locks':True,'output':'Unique flat 30-file ZIP beside macro; existing ZIPs and native files preserved',
'maximum_physical_line_length':max(map(len,source.splitlines())),
'macro_sha256':hashlib.sha256((S/'ArchiveNativeResultsV1.swb').read_bytes()).hexdigest()}
(S/'ArchiveNativeResultsV1_source_audit.json').write_text(json.dumps(audit,indent=2))
print(json.dumps({'macro':str(S/'ArchiveNativeResultsV1.bas'),'bytes':(S/'ArchiveNativeResultsV1.bas').stat().st_size,'audit':audit},indent=2))
