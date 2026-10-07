"""Record observed trial access; does not claim native CAD execution."""
from pathlib import Path
import hashlib
import json
import zipfile

root = Path('D:/RoboticArm/solidworks')

start = root / 'START HERE.txt'
content = start.read_text(encoding='utf-8-sig')
content = content.replace(
    "Approval is pending for the official online trial because it would upload this CAD model outside the user's D:-only storage boundary.",
    "The user approved the official free online trial and CAD upload on 5 October 2026. Local files remain on D:. The official trial is open at the 3DEXPERIENCE sign-in screen; account login is the current blocker. No CAD upload or native SOLIDWORKS execution has occurred."
)
content = content.replace('the original293 component', 'the original 293 component')
if 'execution_checklist.txt' not in content:
    content += '\nNEXT CHECKPOINT\nstudies/execution_checklist.txt gives the ordered native execution steps.\nstudies/native_results_ledger.json records actual evidence only; all native studies remain NOT_EXECUTED.\nresults/trial_access_status.json records the browser handoff.\n'
start.write_text(content, encoding='utf-8')

access = root / 'docs/installation_and_access.txt'
content = access.read_text(encoding='utf-8-sig')
content = content.replace(
    "Using this arm in that trial requires uploading its CAD files to the vendor's trial environment. This is outside the current D:-only constraint; explicit user approval is pending.",
    "The user explicitly approved the official free online trial and uploading the prepared arm CAD on 5 October 2026. Vendor cloud processing is authorized for this trial; local project files and exports remain on D:. No purchase is authorized."
)
content = content.replace(
    'The public trial page was found; the follow-on my.solidworks.com/try-solidworks link returned an access error during this check. The browser control connection also timed out, so no logged-in trial session was verified.',
    'The official trial page loaded successfully after earlier connection delays. Its Log In link reached the official Dassault Systemes 3DEXPERIENCE sign-in screen. The page requests an email/username and offers Create your account. User sign-in is required; no authenticated trial session, current session quota, or enabled native add-ins has been verified. Evidence: results/trial_sign_in.png.'
)
access.write_text(content, encoding='utf-8')

status = {
    'date': '2026-10-05',
    'status': 'AWAITING_USER_ACCOUNT_SIGN_IN',
    'trial_url': 'https://my.solidworks.com/try-solidworks',
    'sign_in_host': 'eu1.iam.3dexperience.3ds.com',
    'observed_page_title': 'Login | 3DEXPERIENCE ID | Dassault Systemes',
    'observed_controls': ['Email or username', 'Continue', 'Create your account'],
    'user_authorized_free_trial_and_CAD_upload': True,
    'user_authorization_quote': 'Yes you can use the free online trial but I want this whole project to be done',
    'purchase_authorized': False,
    'local_root': str(root),
    'cloud_upload_performed': False,
    'native_solidworks_tests_run': False,
    'screenshot': 'results/trial_sign_in.png',
    'next_action': 'User completes official account sign-in. Then inspect trial terms/capabilities, verify native save/export, and follow studies/execution_checklist.txt.',
    'scope': 'Browser access evidence only; not a SOLIDWORKS engineering result.'
}
(root / 'results/trial_access_status.json').write_text(json.dumps(status, indent=2), encoding='utf-8')

ledger_path = root / 'studies/native_results_ledger.json'
ledger = json.loads(ledger_path.read_text(encoding='utf-8-sig'))
ledger['trial']['access_status'] = status['status']
ledger['trial']['evidence'] = ['D:/RoboticArm/solidworks/results/trial_sign_in.png', 'D:/RoboticArm/solidworks/results/trial_access_status.json']
ledger['user_authorization']['basis'] = status['user_authorization_quote']
ledger_path.write_text(json.dumps(ledger, indent=2), encoding='utf-8')

manifest_path = root / 'preparation_manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
manifest['status'] = 'SOLIDWORKS transfer prepared; free online trial and CAD upload approved; native execution awaiting user account sign-in'
manifest['cloud_upload_authorized'] = True
manifest['trial_access_status'] = status['status']
included = [start]
for directory in ('transfer', 'studies', 'docs'):
    included += sorted((root / directory).rglob('*'))
included += [root / 'results/trial_access_status.json', root / 'results/trial_sign_in.png']
included = [p for p in included if p.is_file()]
manifest['files'] = [{'path': p.relative_to(root).as_posix(), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in included]
manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
archive = root / 'AnthroArm27_SOLIDWORKS_Preparation.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in included + [manifest_path]:
        z.write(p, p.relative_to(root).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
assert not ledger['core_deliverable']['full_native_assembly_completed']
assert all(s['status'] == 'NOT_EXECUTED' for s in ledger['stages'])
print(json.dumps({'status': status['status'], 'files_in_archive': len(included) + 1, 'archive_bytes': archive.stat().st_size, 'zip_integrity': 'PASS', 'native_execution': False}, indent=2))
