"""Record the verified launch page without accepting its agreement."""
from pathlib import Path
import hashlib
import json
import zipfile

root = Path('D:/RoboticArm/solidworks')
status_path = root / 'results/trial_access_status.json'
status = json.loads(status_path.read_text(encoding='utf-8-sig'))
status.update({
    'date': '2026-10-06',
    'status': 'AUTHENTICATED_AWAITING_LAUNCH_AGREEMENT_CONFIRMATION',
    'observed_page_title': 'Try SOLIDWORKS | MySolidWorks',
    'observed_controls': ['Signed-in account menu; identity not recorded', 'Launch your SOLIDWORKS Online Product Trial', 'Agreement checkbox unchecked', 'Language English', 'Launch button disabled'],
    'screenshot': 'results/trial_launch_agreement.png',
    'launch_agreement_accepted': False,
    'trial_session_launched': False,
    'agreement_condition': 'No confidential information or data, personal data, production data, or trade secrets may be uploaded. Any additional terms regarding these topics are not applicable.',
    'next_action': 'User confirmation is required at the time of accepting the displayed trial agreement. Then launch, inspect actual capabilities, and verify native file save/download.',
    'observed_storage_notice': 'Temporary files are erased at session end or timeout; an idle streaming session closes after 15 minutes. The page says clicking a saved temporary file downloads it.',
    'cloud_upload_performed': False,
    'native_solidworks_tests_run': False,
})
status_path.write_text(json.dumps(status, indent=2), encoding='utf-8')

ledger_path = root / 'studies/native_results_ledger.json'
ledger = json.loads(ledger_path.read_text(encoding='utf-8-sig'))
ledger['trial']['access_status'] = status['status']
ledger['trial']['evidence'] = ['D:/RoboticArm/solidworks/results/trial_launch_agreement.png', 'D:/RoboticArm/solidworks/results/trial_access_status.json']
ledger_path.write_text(json.dumps(ledger, indent=2), encoding='utf-8')

start_path = root / 'START HERE.txt'
content = start_path.read_text(encoding='utf-8-sig')
content = content.replace(
    'The official trial is open at the 3DEXPERIENCE sign-in screen; account login is the current blocker.',
    'Sign-in was verified on 6 October 2026. The Launch page requires a data-use agreement; confirmation is pending before accepting it. The streaming CAD session has not launched.'
)
start_path.write_text(content, encoding='utf-8')

access_path = root / 'docs/installation_and_access.txt'
content = access_path.read_text(encoding='utf-8-sig')
content += '\nVERIFIED UPDATE - 6 October 2026\nAccount sign-in succeeded. The trial Launch page shows an unchecked agreement prohibiting confidential, personal, production and trade-secret data. Confirmation was requested before accepting it. Launch remains disabled until agreement. No native CAD session or upload has occurred.\nThe page warns that temporary files are erased at session end/timeout and an idle session closes after 15 minutes; download checkpoints are therefore required. This is an idle timeout, not a confirmed total trial-duration limit.\n'
access_path.write_text(content, encoding='utf-8')

manifest_path = root / 'preparation_manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
manifest['status'] = 'Signed in to official trial; launch agreement confirmation pending; native execution not started'
manifest['trial_access_status'] = status['status']
included = [start_path]
for folder in ('transfer', 'studies', 'docs', 'project/trial_upload'):
    included += sorted(p for p in (root / folder).rglob('*') if p.is_file())
included += [status_path, root / 'results/trial_launch_agreement.png']
manifest['files'] = [{'path': p.relative_to(root).as_posix(), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in included]
manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
archive = root / 'AnthroArm27_SOLIDWORKS_Preparation.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in included + [manifest_path]:
        z.write(p, p.relative_to(root).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
assert all(s['status'] == 'NOT_EXECUTED' for s in ledger['stages'])
print(json.dumps({'access_status': status['status'], 'archive_files': len(included) + 1, 'integrity': 'PASS', 'native_tests_run': False}))
