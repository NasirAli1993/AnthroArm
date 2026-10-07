"""Generate V5 with bounded-wait local ZIP packaging; never runs SOLIDWORKS."""
from pathlib import Path
import hashlib, json, re, shutil, zipfile

ROOT = Path('D:/RoboticArm/solidworks')
SCRIPTS = ROOT / 'scripts'
source = (SCRIPTS / 'AutoFullArmStaticV4.swb').read_text(encoding='ascii')
source = source.replace('AutoFullArmStaticV4', 'AutoFullArmStaticV5')
source = source.replace("' No shell/network calls or account operations.", "' After native success only: hidden local PowerShell ZIP packaging; no network/account operations.")
source = source.replace('If comp.IsFixed Then assembly.UnfixComponent', 'If (comp.IsFixed <> False) Then assembly.UnfixComponent')
source = source.replace('Check comp.IsFixed,', 'Check (comp.IsFixed <> False),')
source = source.replace('Check components(i).IsFixed,', 'Check (components(i).IsFixed <> False),')

# All PowerShell strings are single quoted; inserted file paths are escaped by
# doubling apostrophes. No cmd.exe layer, downloads or outside-file operations.
ps_lines = [
    "$ErrorActionPreference='Stop'; $job=$null;",
    "try {",
    "  if(Test-Path -LiteralPath $target){throw 'Refusing an existing ZIP'};",
    "  $job=Start-Job -ScriptBlock { param($source,$target)",
    "    $ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue';",
    "    if(Test-Path -LiteralPath $target){throw 'Refusing an existing ZIP'};",
    "    $files=@(Get-ChildItem -LiteralPath $source -File -Force);",
    "    if($files.Count -ne 30){throw 'Expected exactly 28 native parts, one assembly and one log'};",
    "    if(@($files|Where-Object {$_.Extension -ieq '.SLDPRT'}).Count -ne 28){throw 'Wrong native part file count'};",
    "    if(@($files|Where-Object {$_.Name -ieq 'AnthroArm27_STATIC_HOME.SLDASM'}).Count -ne 1){throw 'Missing native assembly'};",
    "    if(@($files|Where-Object {$_.Name -ieq 'Native_Static_Build.log'}).Count -ne 1){throw 'Missing build log'};",
    "    foreach($file in $files){if($file.Length -le 0){throw 'Empty source file'}};",
    "    Compress-Archive -LiteralPath $source -DestinationPath $target -CompressionLevel Optimal -ErrorAction Stop;",
    "    Add-Type -AssemblyName System.IO.Compression.FileSystem;",
    "    $zip=[System.IO.Compression.ZipFile]::OpenRead($target);",
    "    try {",
    "      $entries=@($zip.Entries|Where-Object {$_.Name.Length -gt 0});",
    "      if($entries.Count -ne 30){throw 'ZIP file-entry count mismatch'};",
    "      $prefix=(Split-Path -Leaf $source)+'/';",
    "      foreach($file in $files){",
    "        $match=@($entries|Where-Object {$_.FullName.Replace('\\','/') -ceq ($prefix+$file.Name)});",
    "        if($match.Count -ne 1){throw 'ZIP expected filename mismatch'};",
    "        if($match[0].Length -ne $file.Length){throw 'ZIP entry length mismatch'};",
    "        $stream=$match[0].Open(); try {$stream.CopyTo([System.IO.Stream]::Null)} finally {$stream.Dispose()};",
    "      };",
    "    } finally {$zip.Dispose()};",
    "    if((Get-Item -LiteralPath $target).Length -le 0){throw 'ZIP is empty'};",
    "  } -ArgumentList $source,$target;",
    "  $done=Wait-Job -Job $job -Timeout 60;",
    "  if($null -eq $done){Stop-Job -Job $job; Remove-Job -Job $job; exit 124};",
    "  if($job.State -ne 'Completed'){Receive-Job -Job $job -ErrorAction Stop|Out-Null; throw 'ZIP job failed'};",
    "  Receive-Job -Job $job -ErrorAction Stop|Out-Null; Remove-Job -Job $job; exit 0;",
    "} catch { if($null -ne $job){Stop-Job -Job $job -ErrorAction SilentlyContinue; Remove-Job -Job $job -Force -ErrorAction SilentlyContinue}; exit 1 };",
]

def vb_string(s):
    return '"' + s.replace('"', '""') + '"'

ps_vba = '\n'.join('    commandText = commandText & ' + vb_string(line + ' ') for line in ps_lines)
helpers = r'''
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
    zipPath = parentPath & "\" & leaf & "_NATIVE.zip"
    Check fso.FileExists(zipPath) = False, "Refusing existing ZIP"
    powerShellPath = Environ$("SystemRoot") & "\System32\WindowsPowerShell\v1.0\powershell.exe"
    Check fso.FileExists(powerShellPath) <> False, "Built-in Windows PowerShell is unavailable"
    commandText = "$source=" & PowerShellLiteral(sourcePath) & "; $target=" & PowerShellLiteral(zipPath) & "; "
__PS_VBA__
    commandLine = Chr$(34) & powerShellPath & Chr$(34) & " -NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -Command " & Chr$(34) & commandText & Chr$(34)
    Check Len(commandLine) < 30000, "PowerShell command line is too long"
    LogLine "ZIP_REQUESTED=" & zipPath
    LogLine "ZIP_SCOPE=only this run's 28 native parts, one assembly and build log; no network"
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

'''.replace('__PS_VBA__', ps_vba)

source = source.replace("' Sole public no-argument entry point.", helpers + "' Sole public no-argument entry point.")
source = source.replace('Dim macroPath As String, folder As String, outputFolder As String, runStamp As String', 'Dim macroPath As String, folder As String, outputFolder As String, runStamp As String, zipPath As String')
old = '    MsgBox "Static native arm saved: 28 parts + assembly + log." & vbCrLf & outputFolder & vbCrLf & "All components fixed. No mates, Motion or FEA performed.", vbInformation'
new = '    zipPath = PackageNativeOutput(outputFolder, folder)\n    MsgBox "Static native arm saved and ZIP verified: 28 parts + assembly + log." & vbCrLf & zipPath & vbCrLf & "All components fixed. No mates, Motion or FEA performed.", vbInformation'
assert old in source
source = source.replace(old, new)
source = source.replace('Partial outputs preserved; complete static stage did not pass.', 'Outputs preserved; this run did not complete every stage. Inspect prior STATIC_ASSEMBLY_SAVED and ZIP log entries separately.')
assert len('AnthroArm27_Static_') == 19
assert 'Set comp.Transform2 =' not in source
assert 'comp.Transform2 = transform' in source
assert 'Check (comp.IsFixed <> False)' in source
assert re.findall(r'^Public Sub (\w+)', source, re.M) == ['main']
assert max(map(len, source.splitlines())) < 1024
assert len(re.findall(r'^Private (?:Sub|Function) ',source,re.M)) == len(re.findall(r'^End (?:Sub|Function)$',source,re.M)) - 1
for suffix in ['swb', 'bas']:
    text = ('Attribute VB_Name = "AutoFullArmStaticV5"\n' if suffix == 'bas' else '') + source
    (SCRIPTS / f'AutoFullArmStaticV5.{suffix}').write_text(text, encoding='ascii', newline='\r\n')
audit = json.loads((SCRIPTS/'AutoFullArmStaticV4_source_audit.json').read_text())
audit.update(macro_sha256=hashlib.sha256((SCRIPTS/'AutoFullArmStaticV5.swb').read_bytes()).hexdigest(),
             maximum_physical_line_length=max(map(len,source.splitlines())),
             packaging='Hidden Windows PowerShell Compress-Archive after successful native assembly save; 60-second Wait-Job bound; exact 30 ZIP file entries and uncompressed sizes, all streams read to EOF',
             only_behavior_change_from_v4='Automatic verified ZIP plus explicit normalization of all IsFixed checks',
             source_policy='No downloads, network, source file modifications or overwrites by packaging',
             native_execution=False)
(SCRIPTS/'AutoFullArmStaticV5_source_audit.json').write_text(json.dumps(audit,indent=2))
# Testable equivalent of the exact VBA-constructed command body, with parameter
# declarations in place of runtime literal paths. This file is not uploaded.
(SCRIPTS/'test_full_v5_zip_payload.ps1').write_text('param([string]$source,[string]$target)\n'+'\n'.join(ps_lines),encoding='ascii')

out = ROOT/'upload_full_static_v5'
assert not out.exists(), 'Refusing to replace existing upload package'
out.mkdir()
for p in (ROOT/'transfer/links').glob('*.step'):
    shutil.copy2(p,out/p.name)
assert len(list(out.glob('*.step'))) == 28
for name in ['AutoFullArmStaticV5.swb','AutoFullArmStaticV5.bas','AutoFullArmStaticV5_source_audit.json']:
    shutil.copy2(SCRIPTS/name,out/name)
(out/'READ_ME_V5.txt').write_text('''AnthroArm27 full native static build V5: STAGED SOURCE, native run unverified.

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
''',encoding='ascii')
inventory=[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(out.iterdir())]
(out/'upload_inventory.json').write_text(json.dumps({'status':'STAGED SOURCE ONLY','files':inventory},indent=2))
archive=ROOT/'AnthroArm27_FullStaticV5_Upload.zip'
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(out.iterdir()): z.write(p,p.name)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None and len(z.namelist()) == 33
print(json.dumps({'macro':str(SCRIPTS/'AutoFullArmStaticV5.bas'),'folder':str(out),'zip':str(archive),'audit':audit},indent=2))
