"""Stage DIP V4: retain V3 native logic; package only nine named deliverables."""
from pathlib import Path
import hashlib, json, re

root = Path(r'D:\RoboticArm\solidworks\scripts')
source = (root / 'AutoDIPMateV3.bas').read_text(encoding='ascii')
source = source.replace('AutoDIPMateV3', 'AutoDIPMateV4')
full = (root / 'AutoFullArmStaticV5.bas').read_text(encoding='ascii')
start = full.index('Private Function PowerShellLiteral(')
end = full.index('\nEnd Function', full.index('Private Function PackageNativeOutput(')) + len('\nEnd Function')
helpers = full[start:end]
required = ['index_intermediate.SLDPRT', 'index_distal.SLDPRT',
    'DIP_PLACEMENT_ONLY.SLDASM', 'DIP_HINGE_MATED.SLDASM',
    'DIP_DRIVEN_10DEG.SLDASM', 'DIP_DRIVEN_RETURN_ZERO.SLDASM',
    'DIP_LIMITED_0_TO_80DEG.SLDASM', 'Native_DIP_Mate.log',
    'native_pose_measurements.csv']
helpers = helpers.replace('Left$(leaf, 19) = "AnthroArm27_Static_"', 'Left$(leaf, 9) = "DIP_Mate_"')
a = helpers.index('    commandText = commandText & "    $files=@(')
b = helpers.index('    commandText = commandText & "    foreach($file in $files)', a)
validation = [
    "$required=@(" + ','.join("'" + n + "'" for n in required) + "); ",
    "$files=@(foreach($name in $required){Get-Item -LiteralPath (Join-Path $source $name) -Force -ErrorAction Stop}); ",
    "if($files.Count -ne 9){throw 'Expected exactly nine named native deliverables'}; ",
    "foreach($file in $files){if($file.PSIsContainer){throw 'Deliverable is a directory'}}; ",
]
helpers = helpers[:a] + ''.join('    commandText = commandText & "    ' + s + '"\n' for s in validation) + helpers[b:]
helpers = helpers.replace('Compress-Archive -LiteralPath $source', 'Compress-Archive -LiteralPath @($files.FullName)')
helpers = helpers.replace('$entries.Count -ne 30', '$entries.Count -ne 9')
helpers = helpers.replace('    commandText = commandText & "      $prefix=(Split-Path -Leaf $source)+\'/\'; "\n', '')
helpers = helpers.replace("-ceq ($prefix+$file.Name)", "-ceq $file.Name")
helpers = helpers.replace("28 native parts, one assembly and build log", "two parts, five assemblies, pose CSV and pre-package log snapshot")
helpers = helpers.replace('ZIP_VERIFIED_30_FILES_BYTES=', 'ZIP_VERIFIED_9_FILES_BYTES=')
source = source.replace('Public Sub main()', helpers + '\n\nPublic Sub main()', 1)
source = source.replace('Dim path As String, folder As String, stamp As String, template As String',
    'Dim path As String, folder As String, stamp As String, template As String, zipPath As String')
old = '    MsgBox "Native DIP mate stage saved parts, assemblies, log and measured pose CSV." & vbCrLf & outputFolder & vbCrLf & "No Motion Study, dynamics, contact or FEA run.", vbInformation'
new = ('    zipPath = PackageNativeOutput(outputFolder, folder)\n'
       '    MsgBox "Native DIP mate stage saved and ZIP verified." & vbCrLf & zipPath & vbCrLf & "No Motion Study, dynamics, contact or FEA run.", vbInformation')
assert old in source
source = source.replace(old, new)
source = source.replace('PARTIAL_OUTPUTS_RETAINED; full mate stage did not complete',
    'OUTPUTS_RETAINED; inspect completed mate stage and ZIP result separately')
assert 'Set comp.Transform2 =' not in source
assert 'comp.Transform2 = t' in source
assert 'If condition = False Then' in source
assert 'Check (result <> False)' in source
assert 'Check (errors = 0)' in source
assert '$prefix' not in helpers
assert max(map(len, source.splitlines())) < 1024
assert re.findall(r'^Public Sub (\w+)', source, re.M) == ['main']
for ext, text in [('bas', source), ('swb', source.split('\n', 1)[1])]:
    (root / ('AutoDIPMateV4.' + ext)).write_bytes(
        text.replace('\r\n', '\n').replace('\n', '\r\n').encode('ascii'))

readme = (root / 'AutoDIPMateV3_README.txt').read_text(encoding='ascii')
readme = readme.replace('AutoDIPMateV3', 'AutoDIPMateV4')
readme = readme.replace('V3 FIX\n', 'V4 ZIP EXPORT\n'
    'After native mate tests complete, built-in Windows PowerShell runs hidden\n'
    'to package nine explicitly named deliverables into a new sibling\n'
    'DIP_Mate_<timestamp>_NATIVE.zip beside the running SWP. Native files stay\n'
    'preserved if packaging fails. V3 is unchanged. No network access is used.\n'
    'The ZIP contains two native parts, five checkpoint assemblies, pose CSV\n'
    'and a pre-package log snapshot. SOLIDWORKS transient lock files are ignored.\n'
    'Exact names, uncompressed lengths and all entry streams are validated.\n'
    'Compression plus validation has a 60-second job wait; startup/cleanup may\n'
    'add time. The ZIP log ends before packaging finishes; its live original\n'
    'gets the final packaging result, which is also shown in the success dialog.\n'
    'Download the one ZIP to D: before trial expiry. It does not install software.\n\nV3 FIX\n', 1)
readme = readme.replace('run this V3 version', 'run this V4 version')
(root / 'AutoDIPMateV4_README.txt').write_text(readme, encoding='ascii')
audit = json.loads((root / 'AutoDIPMateV3_source_audit.json').read_text())
audit['files'] = [{'name': p.name, 'bytes': p.stat().st_size,
                   'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                  for p in [root / 'AutoDIPMateV4.bas', root / 'AutoDIPMateV4.swb']]
audit['packaging_required_filenames'] = required
audit['packaging_status'] = 'PAYLOAD_PREPARED_LOCAL_TEST_PENDING_NATIVE_EXECUTION_PENDING'
audit['checks']['max_line_length'] = max(map(len, source.splitlines()))
(root / 'AutoDIPMateV4_source_audit.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='ascii')
# Extract the actual literal VBA concatenation payload for isolated local tests.
pieces = re.findall(r'^    commandText = commandText & "(.*)"$', helpers, re.M)
payload = '\n'.join(p.replace('""', '"') for p in pieces)
assert "foreach($name in $required)" in payload
(root / 'test_dip_v4_zip_payload.ps1').write_text(
    'param([string]$source,[string]$target)\n' + payload + '\n', encoding='ascii')
print(json.dumps(audit, indent=2))
