"""Local dummy-file ZIP tests only. These are not native SOLIDWORKS results."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess, time, zipfile

root = Path(r'D:\RoboticArm\solidworks\scripts')
audit_path = root / 'AutoDIPMateV4_source_audit.json'
audit = json.loads(audit_path.read_text())
required = audit['packaging_required_filenames']
fixture = root / 'packaging_tests' / ("DIP V4 O'Brien " + datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
fixture.mkdir(parents=True)
runner = fixture / 'hidden_runner.ps1'
runner.write_text(r'''param([string]$source,[string]$target,[string]$payloadFile)
$ErrorActionPreference='Stop'
function Literal([string]$s){return "'"+$s.Replace("'","''")+"'"}
$payload=((Get-Content -LiteralPath $payloadFile | Select-Object -Skip 1) -join ' ')
$text='$source='+(Literal $source)+'; $target='+(Literal $target)+'; '+$payload
$exe=$env:SystemRoot+'\System32\WindowsPowerShell\v1.0\powershell.exe'
$command='"'+$exe+'" -NoLogo -NoProfile -NonInteractive -WindowStyle Hidden -Command "'+$text+'"'
$shell=New-Object -ComObject WScript.Shell
$code=$shell.Run($command,0,$true)
Write-Output $code
exit $code
''', encoding='ascii')
powershell = str(Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe')
payload = root / 'test_dip_v4_zip_payload.ps1'
def create_source(name, omit=None):
    folder = fixture / name
    folder.mkdir()
    for i, filename in enumerate(required):
        if filename != omit:
            (folder / filename).write_bytes((('TEST FIXTURE ONLY: ' + filename + '\n') * (i+1)).encode())
    (folder / '~$index_distal.SLDPRT').write_text('transient lock fixture; exclude', encoding='ascii')
    return folder

def run(label, source, target):
    started = time.monotonic()
    result = subprocess.run([powershell, '-NoLogo', '-NoProfile', '-NonInteractive',
        '-WindowStyle', 'Hidden', '-File', str(runner), str(source), str(target), str(payload)],
        capture_output=True, text=True, timeout=90,
        creationflags=subprocess.CREATE_NO_WINDOW)
    return {'case': label, 'exit_code': result.returncode,
            'elapsed_seconds': round(time.monotonic()-started, 3),
            'stdout': result.stdout.strip(), 'stderr': result.stderr.strip()}

source = create_source('DIP_Mate_good')
target = fixture / 'good_NATIVE.zip'
cases = [run('success_with_space_apostrophe_and_extra_lock_file', source, target)]
assert cases[-1]['exit_code'] == 0, cases
with zipfile.ZipFile(target) as archive:
    assert archive.testzip() is None
    assert sorted(archive.namelist()) == sorted(required)
    assert all(archive.read(n) == (source/n).read_bytes() for n in required)
before = hashlib.sha256(target.read_bytes()).hexdigest()
cases.append(run('existing_zip_refused_without_overwrite', source, target))
assert cases[-1]['exit_code'] != 0
assert hashlib.sha256(target.read_bytes()).hexdigest() == before
bad_source = create_source('DIP_Mate_missing', 'DIP_LIMITED_0_TO_80DEG.SLDASM')
bad_target = fixture / 'missing_NATIVE.zip'
cases.append(run('missing_required_assembly_refused', bad_source, bad_target))
assert cases[-1]['exit_code'] != 0
assert not bad_target.exists()
report = {'scope': 'LOCAL_DUMMY_FIXTURES_ONLY_NOT_SOLIDWORKS_RESULTS',
          'status': 'THREE_LOCAL_PACKAGING_CASES_PASSED',
          'native_execution': False, 'fixture_folder': str(fixture),
          'payload_sha256': hashlib.sha256(payload.read_bytes()).hexdigest(),
          'archive_filenames': required, 'archive_sha256': before,
          'case_results': cases}
(root / 'AutoDIPMateV4_packaging_test_report.json').write_text(json.dumps(report, indent=2)+'\n')
audit['packaging_status'] = 'THREE_LOCAL_DUMMY_FIXTURE_CASES_PASSED_NATIVE_EXECUTION_PENDING'
audit_path.write_text(json.dumps(audit, indent=2)+'\n')
print(json.dumps(report, indent=2))
