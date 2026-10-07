Attribute VB_Name = "ArchiveNativeResultsV2"
Option Explicit
' STAGED SOURCE: no SOLIDWORKS compile/execution claimed here.
' Archive fallback: after saved-file/log preflight, closes this dedicated trial session's documents.
' CloseAllDocuments(True) includes dirty docs; no automatic save is performed.
' No STEP imports, geometry changes, save/rebuild or preferences.
' Save its SWP beside the V5 output folder, then run main.
' Uses late-bound Windows automation objects; no added references are needed.
Private runtimeLog As String
Private logReady As Boolean
Private recoveryStamp As String

Private Sub Check(ByVal condition As Boolean, ByVal message As String)
    If condition = False Then Err.Raise vbObjectError + 770, "ArchiveNativeResultsV2", message
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

Private Function PowerShellLiteral(ByVal value As String) As String
    Check InStr(value, Chr$(34)) = 0, "Unexpected double quote in Windows path"
    Check InStr(value, vbCr) = 0 And InStr(value, vbLf) = 0, "Unexpected newline in Windows path"
    PowerShellLiteral = "'" & Replace(value, "'", "''") & "'"
End Function

Private Function PackageNativeOutput(ByVal outputFolder As String, ByVal macroFolder As String) As String
    Dim fso As Object, runner As Object
    Dim sourcePath As String, parentPath As String, zipPath As String, leaf As String
    Dim powerShellPath As String, commandText As String, commandLine As String
    Dim exitCode As Long
    Set fso = CreateObject("Scripting.FileSystemObject")
    sourcePath = fso.GetAbsolutePathName(Left$(outputFolder, Len(outputFolder) - 1))
    parentPath = fso.GetAbsolutePathName(Left$(macroFolder, Len(macroFolder) - 1))
    Check StrComp(fso.GetParentFolderName(sourcePath), parentPath, vbTextCompare) = 0, "ZIP source must be the new direct child of the macro folder"
    leaf = fso.GetFileName(sourcePath)
    Check Left$(leaf, 19) = "AnthroArm27_Static_", "ZIP source has unexpected folder prefix"
    Check fso.FolderExists(sourcePath) <> False, "Native source folder missing for packaging"
    zipPath = parentPath & "\" & leaf & "_NATIVE_RECOVERED_" & recoveryStamp & ".zip"
    Check fso.FileExists(zipPath) = False, "Refusing existing ZIP"
    powerShellPath = Environ$("SystemRoot") & "\System32\WindowsPowerShell\v1.0\powershell.exe"
    Check fso.FileExists(powerShellPath) <> False, "Built-in Windows PowerShell is unavailable"
    commandText = "$source=" & PowerShellLiteral(sourcePath) & "; $target=" & PowerShellLiteral(zipPath) & "; "
    commandText = commandText & "$ErrorActionPreference='Stop'; $job=$null; "
    commandText = commandText & "try { "
    commandText = commandText & "  if(Test-Path -LiteralPath $target){throw 'Refusing an existing ZIP'}; "
    commandText = commandText & "  $job=Start-Job -ScriptBlock { param($source,$target) "
    commandText = commandText & "    $ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; "
    commandText = commandText & "    if(Test-Path -LiteralPath $target){throw 'Refusing an existing ZIP'}; "
    commandText = commandText & "    $required=@('base_link.SLDPRT','shoulder_abduction.SLDPRT','shoulder_flexion.SLDPRT','upper_arm.SLDPRT','elbow_link.SLDPRT','forearm.SLDPRT','wrist_pitch.SLDPRT','palm_base.SLDPRT','index_knuckle.SLDPRT','index_proximal.SLDPRT','index_intermediate.SLDPRT','index_distal.SLDPRT','middle_knuckle.SLDPRT','middle_proximal.SLDPRT','middle_intermediate.SLDPRT','middle_distal.SLDPRT','ring_knuckle.SLDPRT','ring_proximal.SLDPRT','ring_intermediate.SLDPRT','ring_distal.SLDPRT','pinky_knuckle.SLDPRT','pinky_proximal.SLDPRT','pinky_intermediate.SLDPRT','pinky_distal.SLDPRT','thumb_opposition.SLDPRT','thumb_metacarpal.SLDPRT','thumb_proximal.SLDPRT','thumb_distal.SLDPRT','AnthroArm27_STATIC_HOME.SLDASM','Native_Static_Build.log'); "
    commandText = commandText & "    $files=@(foreach($name in $required){Get-Item -LiteralPath (Join-Path $source $name) -Force -ErrorAction Stop}); "
    commandText = commandText & "    if($files.Count -ne 30){throw 'Expected exactly 30 named native deliverables'}; "
    commandText = commandText & "    foreach($file in $files){if($file.PSIsContainer){throw 'Deliverable is a directory'}}; "
    commandText = commandText & "    foreach($file in $files){if($file.Length -le 0){throw 'Empty source file'}}; "
    commandText = commandText & "    Compress-Archive -LiteralPath @($files.FullName) -DestinationPath $target -CompressionLevel Optimal -ErrorAction Stop; "
    commandText = commandText & "    Add-Type -AssemblyName System.IO.Compression.FileSystem; "
    commandText = commandText & "    $zip=[System.IO.Compression.ZipFile]::OpenRead($target); "
    commandText = commandText & "    try { "
    commandText = commandText & "      $entries=@($zip.Entries|Where-Object {$_.Name.Length -gt 0}); "
    commandText = commandText & "      if($entries.Count -ne 30){throw 'ZIP file-entry count mismatch'}; "
    commandText = commandText & "      foreach($file in $files){ "
    commandText = commandText & "        $match=@($entries|Where-Object {$_.FullName.Replace('\','/') -ceq $file.Name}); "
    commandText = commandText & "        if($match.Count -ne 1){throw 'ZIP expected filename mismatch'}; "
    commandText = commandText & "        if($match[0].Length -ne $file.Length){throw 'ZIP entry length mismatch'}; "
    commandText = commandText & "        $stream=$match[0].Open(); try {$stream.CopyTo([System.IO.Stream]::Null)} finally {$stream.Dispose()}; "
    commandText = commandText & "      }; "
    commandText = commandText & "    } finally {$zip.Dispose()}; "
    commandText = commandText & "    if((Get-Item -LiteralPath $target).Length -le 0){throw 'ZIP is empty'}; "
    commandText = commandText & "  } -ArgumentList $source,$target; "
    commandText = commandText & "  $done=Wait-Job -Job $job -Timeout 60; "
    commandText = commandText & "  if($null -eq $done){Stop-Job -Job $job; Remove-Job -Job $job; exit 124}; "
    commandText = commandText & "  if($job.State -ne 'Completed'){Receive-Job -Job $job -ErrorAction Stop|Out-Null; throw 'ZIP job failed'}; "
    commandText = commandText & "  Receive-Job -Job $job -ErrorAction Stop|Out-Null; Remove-Job -Job $job; exit 0; "
    commandText = commandText & "} catch { if($null -ne $job){Stop-Job -Job $job -ErrorAction SilentlyContinue; Remove-Job -Job $job -Force -ErrorAction SilentlyContinue}; exit 1 }; "
    commandLine = Chr$(34) & powerShellPath & Chr$(34) & " -NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -Command " & Chr$(34) & commandText & Chr$(34)
    Check Len(commandLine) < 30000, "PowerShell command line is too long"
    LogLine "ZIP_REQUESTED=" & zipPath
    LogLine "ZIP_SCOPE=explicit 28 native parts, assembly and existing native build log snapshot; temporary lock files excluded; no network"
    LogLine "ZIP_WAIT=Wait-Job timeout 60 seconds; process startup/cleanup can add time"
    Set runner = CreateObject("WScript.Shell")
    exitCode = runner.Run(commandLine, 0, True)
    LogLine "ZIP_PROCESS_EXIT_CODE=" & CStr(exitCode)
    Check exitCode = 0, "ZIP packaging/validation failed; code 124 means bounded job wait expired. Native files remain preserved."
    Check fso.FileExists(zipPath) <> False, "ZIP output missing"
    Check FileLen(zipPath) > 0, "ZIP output empty"
    LogLine "ZIP_VERIFIED_30_FILES_BYTES=" & CStr(FileLen(zipPath)) & " PATH=" & zipPath
    PackageNativeOutput = zipPath
End Function


Public Sub main()
    Dim swApp As Object, fso As Object, openDocument As Object
    Dim path As String, folder As String, outputFolder As String, zipPath As String
    Dim failureNumber As Long, failureText As String
    Dim closeResult As Boolean, required As Variant, filename As Variant
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
    LogLine "ARCHIVE_RECOVERY_STARTED; saved-file/log preflight then close documents; no imports, CAD edits, rebuilds or saves"
    LogLine "MACRO_PATH=" & path
    outputFolder = LatestSuccessfulV5Folder(folder)
    LogLine "SELECTED_LATEST_SUCCESSFUL_V5=" & outputFolder
    required = Array("base_link.SLDPRT", "shoulder_abduction.SLDPRT", "shoulder_flexion.SLDPRT", "upper_arm.SLDPRT", "elbow_link.SLDPRT", "forearm.SLDPRT", "wrist_pitch.SLDPRT", "palm_base.SLDPRT", "index_knuckle.SLDPRT", "index_proximal.SLDPRT", "index_intermediate.SLDPRT", "index_distal.SLDPRT", "middle_knuckle.SLDPRT", "middle_proximal.SLDPRT", "middle_intermediate.SLDPRT", "middle_distal.SLDPRT", "ring_knuckle.SLDPRT", "ring_proximal.SLDPRT", "ring_intermediate.SLDPRT", "ring_distal.SLDPRT", "pinky_knuckle.SLDPRT", "pinky_proximal.SLDPRT", "pinky_intermediate.SLDPRT", "pinky_distal.SLDPRT", "thumb_opposition.SLDPRT", "thumb_metacarpal.SLDPRT", "thumb_proximal.SLDPRT", "thumb_distal.SLDPRT", "AnthroArm27_STATIC_HOME.SLDASM", "Native_Static_Build.log")
    For Each filename In required
        Check fso.FileExists(outputFolder & CStr(filename)) <> False, "Missing saved deliverable before closing: " & CStr(filename)
        Check FileLen(outputFolder & CStr(filename)) > 0, "Empty saved deliverable before closing: " & CStr(filename)
    Next filename
    LogLine "SAVED_DELIVERABLE_PREFLIGHT_PASS=30 files; successful native V5 build log already verified"
    LogLine "CLOSE_ALL_DOCUMENTS_BEGIN IncludeUnsaved=True; no automatic save requested"
    closeResult = swApp.CloseAllDocuments(True)
    LogLine "CLOSE_ALL_DOCUMENTS_RETURN=" & CStr(closeResult)
    Check (closeResult <> False), "CloseAllDocuments returned False; do not package potentially locked files"
    Set openDocument = swApp.GetFirstDocument()
    Check openDocument Is Nothing, "A CAD document remains open after CloseAllDocuments"
    LogLine "NO_OPEN_CAD_DOCUMENTS_VERIFIED; beginning archive"
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
