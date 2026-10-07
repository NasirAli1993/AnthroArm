"""Record the operating agent's observed cloud progress, without inventing CAD results.

Evidence snapshot: 2026-10-06, second official session, V2 source open for editing.
This script performs local bookkeeping only; it never drives SOLIDWORKS/browser UI.
"""
from pathlib import Path
import hashlib, json, zipfile

root=Path(r'D:\RoboticArm\solidworks')
date='2026-10-06'
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def save(path,value):path.write_text(json.dumps(value,indent=2),encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

status_path=root/'results/trial_access_status.json'
status=read(status_path)
status.update({
 'date':date,
 'status':'SECOND_CLOUD_SESSION_NATIVE_MACRO_PREPARATION_IN_PROGRESS',
 'observed_page_title':'Try SOLIDWORKS | MySolidWorks',
 'observed_controls':['Official streaming toolbar and Temporary Files','Native SOLIDWORKS 2026 SP0','Macro editor with AutoFingerImportV2 open for editing'],
 'trial_session_launched':True,
 'official_sessions_launched_observed':2,
 'software_license_confirmation_received':True,
 'software_license_accepted':True,
 'software_license_confirmation_basis':'User approved the software license in the conversation; acceptance observed by the operating agent in both sessions.',
 'launch_agreement_accepted':None,
 'launch_agreement_acceptance_note':'Launch-page confirmation was authorized and launch succeeded; a separate checkbox-acceptance action is not independently recorded. Native software-license acceptance is recorded separately and is verified.',
 'launch_gate_observation':'The first official session launched after user approval. Following its timeout, the vendor offered Launch again and the second official session launched using the same account.',
 'cloud_upload_performed':True,
 'current_remote_folder':'Temporary Files',
 'product':'SOLIDWORKS',
 'version':'2026 SP0',
 'native_solidworks_tests_run':False,
 'native_geometry_import_verified':False,
 'native_geometry_outputs_verified':False,
 'native_macro_compile_attempts_performed':True,
 'native_macro_compile_success_verified':False,
 'current_macro_source':'scripts/AutoFingerImportV2.swb',
 'next_action':'Configure the required references and compile corrected AutoFingerImportV2 in the native editor. Then run the import only if compilation succeeds, inspect actual solids, save/download native checkpoints and logs. AutoFullArmStaticV1 remains staged until native compile/run.',
 'scope':'Actual cloud access, upload and macro preparation/compile-failure evidence. No native geometry import, articulated assembly, motion or FEA test has passed.',
 'observation_basis':'Operating agent report on 2026-10-06; this bookkeeping script did not operate the browser or native application.',
 'snapshot_is_live_state':False,
})
# Earlier screenshot remains useful history, but does not prove the current session.
status['screenshot_scope']='Earlier cloud/native application evidence only; current second-session macro-editor state is described by the operating agent.'
uploaded=[]
for p in sorted((root/'transfer/links').glob('*.step')):
 uploaded.append({'source':p.relative_to(root).as_posix(),'remote_folder':'Temporary Files','session':2,'upload_observed':True,'local_bytes':p.stat().st_size,'local_sha256':sha(p)})
for name in ('AutoFingerImportV2.swb','AutoFullArmStaticV1.swb'):
 p=root/'scripts'/name
 uploaded.append({'source':p.relative_to(root).as_posix(),'remote_folder':'Temporary Files','session':2,'upload_observed':True,'local_bytes':p.stat().st_size,'local_sha256':sha(p)})
status['uploaded_files']=uploaded
status['upload_note']='The recorded hashes identify local prepared sources. No remote checksum is available; upload observation is not native compilation/import evidence.'
events=[
 {'id':'2026-10-06-session1-native-open','date':date,'session':1,'event':'USER_APPROVED_LICENSE_ACCEPTED_NATIVE_APP_OPENED','observation':'Native SOLIDWORKS 2026 SP0 opened. Two finger STEP files and a macro were uploaded.','engineering_result':None},
 {'id':'2026-10-06-session1-compile-blocks','date':date,'session':1,'event':'MACRO_COMPILE_ATTEMPTS_BLOCKED','observation':'First macro encountered missing SOLIDWORKS type-library references, then an invalid assignment from a void setter. No native geometry output was verified.','engineering_result':None},
 {'id':'2026-10-06-session1-timeout','date':date,'session':1,'event':'SESSION_TIMED_OUT','observation':'First cloud session timed out before a verified native geometry checkpoint.','engineering_result':None},
 {'id':'2026-10-06-session2-open-upload','date':date,'session':2,'event':'SECOND_OFFICIAL_SESSION_OPENED_AND_FILES_UPLOADED','observation':'Vendor-offered Launch used the same account. Same user-approved software license accepted. 28 link STEP files, AutoFingerImportV2.swb and AutoFullArmStaticV1.swb uploaded to remote Temporary Files.','engineering_result':None},
 {'id':'2026-10-06-session2-v2-edit','date':date,'session':2,'event':'CORRECTED_MACRO_OPEN_FOR_EDITING','observation':'Native application is open with corrected V2 source being edited. V2 and full-static V1 have local source audits only; neither has a verified native compile or run.','engineering_result':None},
]
status['session_history']=events
status['macro_sources']=[
 {'name':'AutoFingerImportV2','status':'SOURCE_AUDITED_NATIVE_COMPILE_PENDING','source':'scripts/AutoFingerImportV2.swb','audit':'scripts/AutoFingerImportV2_AUDIT.txt','native_compiled':False,'native_run_completed':False},
 {'name':'AutoFullArmStaticV1','status':'SOURCE_AUDITED_STAGED_NATIVE_COMPILE_PENDING','source':'scripts/AutoFullArmStaticV1.swb','audit':'scripts/AutoFullArmStaticV1_source_audit.json','native_compiled':False,'native_run_completed':False},
]
save(status_path,status)

ledger_path=root/'studies/native_results_ledger.json'
ledger=read(ledger_path)
ledger['updated_date']=date
ledger['purpose']='Execution checklist and evidence ledger. Native cloud application opened and compiler blockers observed; no verified native CAD geometry or engineering study result exists yet.'
ledger['user_authorization']['software_license_approved']=True
ledger['trial'].update({'access_status':status['status'],'product':'SOLIDWORKS','version':'2026 SP0','api_or_macro_access_available':True,'file_upload_verified':True,'uploaded_source_files':[x['source'] for x in uploaded],'official_sessions_launched_observed':2,'native_macro_compile_success_verified':False,'capabilities_note':'Native macro editor and compiler access observed. Enabled Motion/Simulation products, native geometry export/recovery and corrected-macro success remain unverified.'})
ledger['trial']['evidence']=list(dict.fromkeys(ledger['trial'].get('evidence',[])+['D:/RoboticArm/solidworks/results/trial_access_status.json','D:/RoboticArm/solidworks/scripts/AutoFingerImportV2_AUDIT.txt','D:/RoboticArm/solidworks/scripts/AutoFullArmStaticV1_source_audit.json']))
old_events={e.get('id','legacy-'+str(i)):e for i,e in enumerate(ledger.get('session_events',[]))}
old_events.update({e['id']:e for e in events})
ledger['session_events']=list(old_events.values())
ledger['macro_attempts']=status['macro_sources']
for stage in ledger['stages']:
 if stage['id']=='P0':
  stage.update({'status':'IN_PROGRESS_NOT_PASSED','started_at':date+' (exact time not recorded)','observed':'Cloud native SOLIDWORKS 2026 SP0 opened and macro editor/compiler reached. Initial source failed compilation. Second official session has corrected V2 open and 28 STEP sources staged. Native smoke-test save/download, add-in inventory and successful compile remain unverified.','passed':None,'finished_at':None,'evidence':['D:/RoboticArm/solidworks/results/trial_access_status.json']})
ledger['completion_rule']='Change a state only after actual native action and measured evidence. Uploads, source audits, FreeCAD checks and MuJoCo results are not completed native SOLIDWORKS imports, articulated assemblies, or engineering studies.'
assert not ledger['core_deliverable']['full_native_assembly_completed']
assert not ledger['core_deliverable']['native_motion_study_completed']
assert all(s.get('passed') is None for s in ledger['stages'])
assert all(s['status']=='NOT_EXECUTED' for s in ledger['stages'] if s['id']!='P0')
assert not ledger['downloaded_artifacts']
save(ledger_path,ledger)

start=root/'START HERE.txt'
start.write_text('''SOLIDWORKS PROJECT — CLOUD ACCESS ACTIVE; NATIVE GEOMETRY RESULTS PENDING
Updated 6 October 2026

CURRENT EVIDENCE
The user approved the official free online trial, CAD upload and software license.
Native SOLIDWORKS 2026 SP0 opened in the vendor's cloud trial. No local SOLIDWORKS
installation or purchase has occurred. Local project files remain on D:.

The first session received two finger STEP files and a macro. Native compilation
was blocked first by missing type-library references and then by an invalid
assignment from a void setter. No native geometry output was verified. That
session timed out before a downloadable geometry checkpoint was obtained.

A second session was launched through the vendor's offered Launch control using
the same account and the same approved software license. All 28 link STEP files,
AutoFingerImportV2.swb and AutoFullArmStaticV1.swb were uploaded to remote Temporary
Files. At this evidence snapshot, corrected V2 is open for editing in the native
application. Both corrected sources have local audits; native compilation and
successful execution remain unverified. This document is not live session state.

NEXT CHECKPOINT
Compile V2 with its required native references. Only after compilation succeeds,
run the two-file import, inspect actual solids, and save/download native files and
logs to D:. Then compile/run the full static assembly source if the trial allows.
An all-fixed static assembly does not establish 27-joint articulation or motion.

FILES
transfer/: 28 rigid-link STEP files, 293 body descriptions, assembly transforms,
27 joint definitions, and successful FreeCAD/OpenCascade transfer checks.
scripts/AutoFingerImportV2*: corrected two-part import source and audit.
scripts/AutoFullArmStaticV1*: staged full-arm static import source and audit.
studies/execution_checklist.txt: ordered native execution and evidence criteria.
studies/native_results_ledger.json: access progress; no native engineering PASS.
results/trial_access_status.json: session/upload/compiler history and next action.

RESULT LIMITS
No native geometry import, articulated assembly, Motion Analysis or FEA has
passed. No verified native SLDPRT/SLDASM checkpoint has been downloaded. The actual
MuJoCo simulations remain in D:/RoboticArm/results/v3 and are not SOLIDWORKS tests.
The existing CAD remains a digital concept, with materials, loads, drive hardware
and some interfaces requiring engineering before quantitative qualification.

STORAGE
Cloud working files are remote until downloaded; Temporary Files may be erased
at session end or timeout. Download each verified checkpoint with dependencies.
The observed notice specifies a 15-minute idle timeout; this is not proof of a
fixed total trial duration. Paid products/purchases are not authorized.
''',encoding='utf-8')

access=root/'docs/installation_and_access.txt'
content=access.read_text(encoding='utf-8-sig')
# Preserve official source references while replacing obsolete current-state prose.
source_section=content[content.index('OFFICIAL SOURCES'):content.index('VERIFIED UPDATE')] if 'VERIFIED UPDATE' in content else content[content.index('OFFICIAL SOURCES'):]
access.write_text('''SOLIDWORKS ACCESS AND STORAGE — 6 October 2026

The user has no purchased local license and does not want a purchase. The official
free online trial, upload of this project and displayed software license were
approved. Native SOLIDWORKS 2026 SP0 opened in the vendor's cloud infrastructure;
no local installer was downloaded/run and no product purchase occurred.

Two official cloud sessions have been observed. The first ended by timeout after
macro compilation blockers (missing references, then void-setter assignment).
The second was launched using the same account through the vendor's offered
Launch control. The same approved software license was accepted. Its Temporary
Files received all 28 rigid-link STEP sources and the two corrected/staged macro
sources. Corrected V2 is being edited; no native compile success, geometry import,
native-file recovery, motion study or FEA result has been verified.

The trial's actual enabled Motion/Simulation capabilities and native download
workflow remain to be checked. A macro source audit is not native compilation.
The project is at access/preparation stage, not a completed native CAD result.
See results/trial_access_status.json for the evidence snapshot and history.

LOCAL STORAGE
All task-controlled local project files, downloads and evidence belong on D:.
The cloud workspace is remote until its files are downloaded. Temporary Files
may be erased at session end/timeout; the observed idle notice says 15 minutes.
This is not a confirmed total session-duration entitlement.

If a legitimate local installation is considered later, its main program can
target D:, but Windows-managed prerequisites and installer servicing data cannot
be promised to remain exclusively on D:. No such installation has been attempted.

ENGINEERING SCOPE
Motion Analysis, visual Animation and Basic Motion are distinct. Quantitative
torque/stress conclusions require the relevant solver plus defensible physical
mass, material, load, contact and actuator inputs. The current motor packages
and some interfaces are conceptual. Camera perception is external Python code;
importing STEP does not create a native vision/control bridge.

'''+source_section,encoding='utf-8')

manifest_path=root/'preparation_manifest.json'
manifest=read(manifest_path)
manifest.update({'updated_date':date,'status':'Second official cloud session opened; 28 STEP files and corrected/staged macros uploaded; native compilation/geometry results pending','trial_access_status':status['status'],'solidworks_installed':False,'native_solidworks_cloud_opened':True,'native_solidworks_version':'2026 SP0','native_solidworks_tests_run':False,'native_geometry_outputs_verified':False,'cloud_upload_performed':True,'cloud_upload_authorized':True,'software_license_approved':True,'transfer_checks_passed':True})
included=[start,status_path]
for folder in ('transfer','studies','docs'):
 included.extend(p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
for pattern in ('AutoFingerImportV2*','AutoFullArmStaticV1*'):
 included.extend((root/'scripts').glob(pattern))
included=sorted(set(included))
manifest['files']=[{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in included]
save(manifest_path,manifest)
archive=root/'AnthroArm27_SOLIDWORKS_Preparation.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in included+[manifest_path]:z.write(p,p.relative_to(root).as_posix())
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps({'status':status['status'],'uploaded_sources_recorded':len(uploaded),'P0':'IN_PROGRESS_NOT_PASSED','native_tests_passed':False,'archive_files':len(included)+1,'archive_integrity_checked':True},indent=2))
