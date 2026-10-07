"""Historical snapshot after third cloud session expired, before fourth launch.

Records source-control-flow inference separately from directly visible geometry.
No native SOLIDWORKS or browser commands run here; no engineering PASS is created.
"""
from pathlib import Path
import hashlib,json,zipfile
root=Path(r'D:\RoboticArm\solidworks')
date='2026-10-06'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
status_path=root/'results/trial_access_status.json'
status=read(status_path)
state='THIRD_SESSION_EXPIRED_PARTIAL_NATIVE_IMPORT_EVIDENCE_NO_RECOVERED_CAD'
status.update({
 'date':date,'status':state,'official_sessions_launched_observed':3,
 'product':'SOLIDWORKS','edition':'Design Premium','version':'2026 SP0',
 'trial_session_launched':True,'latest_observed_session_expired':True,
 'current_session_active':False,'snapshot_is_live_state':False,
 'software_license_confirmation_received':True,'software_license_accepted':True,
 'observed_controls':['Native SOLIDWORKS Design Premium 2026 SP0','VBA compiler and macro runtime','Imported part trees with Solid Bodies(12)','Native assembly with base_link component and runtime error 438','Third session expired before download'],
 'screenshot':'results/full_static_v3_result.png',
 'screenshot_scope':'Native partial assembly showing base_link and error 438. Does not establish a completed full-arm assembly.',
 'native_solidworks_tests_run':True,
 'native_solidworks_tests_run_scope':'Native import/save/macro attempts only. No completed acceptance check, articulated motion or FEA study.',
 'native_import_attempts_run':True,'native_engineering_studies_run':False,
 'native_geometry_import_verified':True,
 'native_geometry_import_verified_scope':'Partial direct screenshot evidence: index_intermediate and thumb_proximal each show 12 solid bodies. Completion of all 28 import/save iterations is inferred from reaching the assembly stage in the audited V3 control flow.',
 'native_geometry_outputs_verified':False,
 'native_geometry_outputs_verified_scope':'No native CAD files were downloaded or reopened locally. Screenshot/control-flow evidence does not constitute a recoverable native deliverable.',
 'native_macro_compile_success_verified':True,
 'native_macro_compile_success_scope':'Full static V1 compiled; V2/V3 ran. Later corrected V4 and planned V5 remain unverified in native execution.',
 'local_native_cad_files_recovered':0,'native_full_assembly_completed':False,
 'cloud_temporary_files_status':'Not recovered before expiry; deleted under the advertised session-end/timeout policy. No post-expiry filesystem inspection is claimed.',
 'next_action':'Prepare/review full-static V5 with automatic single-ZIP preservation; use the next vendor-offered official trial launch if available, execute and download a checkpoint promptly. Fourth session has not yet been recorded as launched.',
 'scope':'Native import/save attempts and partial geometry are now evidenced. Full native assembly, 27-joint articulation, motion and FEA remain incomplete/unexecuted. No CAD checkpoint survives locally.',
 'planned_next_session':4,
 'temporary_browser_download_exception_authorized':True,
 'temporary_browser_download_exception_scope':'User approved browser temporary download followed by moving the project deliverable to D:. No actual download is recorded in this snapshot.',
 'current_macro_source':'scripts/AutoFullArmStaticV4.swb',
 'macro_source_note':'V4 corrects Transform2 property assignment and is staged. V5 with automatic single-ZIP packaging is planned/in preparation; native execution not verified.',
 'observation_basis':'Operating agent report plus locally inspected screenshots and V3 source control flow on 2026-10-06. Bookkeeping script performs no browser/native actions.',
})
for row in status.get('uploaded_files',[]):
 row['remote_availability']='Historical upload; not a current-session availability claim.'
events=[
 {'id':'2026-10-06-session3-license','date':date,'session':3,'event':'THIRD_NATIVE_SESSION_LICENSE_ACCEPTED','observation':'User-approved software license accepted; native SOLIDWORKS Design Premium 2026 SP0 available.','engineering_result':None},
 {'id':'2026-10-06-session3-v1','date':date,'session':3,'event':'V1_NATIVE_COMPILE_SUCCEEDED_RUNTIME_PREF_FAILURE','observation':'Full-static V1 compiled natively, then stopped at preference readback.','engineering_result':None,'evidence':['results/full_static_native_attempt.png']},
 {'id':'2026-10-06-session3-v2','date':date,'session':3,'event':'V2_BASE_IMPORTED_SAVE_TRUE_FALSE_FAILURE_CHECK','observation':'V2 imported base_link. Save returned True, errors 0, warnings 0; an incorrect Boolean check falsely reported save failure. This is API evidence in the cloud, not a locally recovered file.','engineering_result':None,'evidence':['results/native_save_error_tail.png','results/full_static_v2_save_error.png']},
 {'id':'2026-10-06-session3-v3','date':date,'session':3,'event':'V3_IMPORT_LOOP_REACHED_ASSEMBLY_RUNTIME_438','observation':'V3 corrected Boolean checks and reached the first-component assembly stage after its 28-part import/save loop. Screenshots directly show index_intermediate and thumb_proximal with 12 solid bodies. Assembly stopped with runtime error 438 at Transform2 assignment; all-28 completion is control-flow inference, not individually recovered evidence.','engineering_result':None,'evidence':['results/full_static_v3_native_outcome.png','results/full_static_v3_progress.png','results/full_static_v3_result.png']},
 {'id':'2026-10-06-session3-v4','date':date,'session':3,'event':'V4_TRANSFORM_SETTER_CORRECTION_STAGED','observation':'V4 replaces Set comp.Transform2 = transform with the officially verified plain property assignment comp.Transform2 = transform. Native V4 compile/run not verified.','engineering_result':None,'evidence':['scripts/AutoFullArmStaticV4_source_audit.json']},
 {'id':'2026-10-06-session3-expiry','date':date,'session':3,'event':'EXPIRED_BEFORE_DOWNLOAD','observation':'Third session expired before native CAD was downloaded. Temporary Files are deleted under the published trial policy. No recoverable local native CAD artifact exists.','engineering_result':None},
 {'id':'2026-10-06-session4-plan','date':date,'session':4,'event':'FOURTH_SESSION_PLANNED_NOT_LAUNCHED','observation':'Plan full-static V5 automatic single-ZIP packaging for prompt download. User approved a temporary browser download followed by move to D:. No fourth-session execution or download is claimed here.','engineering_result':None},
]
history={e.get('id','legacy-'+str(i)):e for i,e in enumerate(status.get('session_history',[]))}
history.update({e['id']:e for e in events});status['session_history']=list(history.values())
macro_states=[
 {'name':'AutoFullArmStaticV1','status':'NATIVE_COMPILED_RUNTIME_PREF_READBACK_FAILURE','native_compiled':True,'native_run_completed':False},
 {'name':'AutoFullArmStaticV2','status':'NATIVE_BASE_IMPORT_SAVE_TRUE_CHECK_BUG','native_compiled':True,'native_run_completed':False},
 {'name':'AutoFullArmStaticV3','status':'NATIVE_IMPORT_LOOP_COMPLETED_ASSEMBLY_RUNTIME_438','native_compiled':True,'native_run_completed':False},
 {'name':'AutoFullArmStaticV4','status':'SOURCE_CORRECTED_STAGED_NATIVE_EXECUTION_UNVERIFIED','native_compiled':False,'native_run_completed':False},
 {'name':'AutoFullArmStaticV5','status':'PLANNED_AUTOMATIC_ZIP_NATIVE_EXECUTION_UNVERIFIED','native_compiled':False,'native_run_completed':False},
]
status['macro_sources']=macro_states
write(status_path,status)

ledger_path=root/'studies/native_results_ledger.json';ledger=read(ledger_path)
ledger['updated_date']=date
ledger['purpose']='Actual native partial-import evidence and uncompleted study ledger. Third session expired before any native CAD checkpoint was recovered locally; no full assembly or engineering study has passed.'
ledger['user_authorization']['temporary_browser_download_then_move_to_D']=True
ledger['storage']['temporary_browser_download_exception']='User approved temporary browser download followed by moving the deliverable to D:. No download has yet occurred in this snapshot.'
ledger['trial'].update({'access_status':state,'product':'SOLIDWORKS','edition':'Design Premium','version':'2026 SP0','official_sessions_launched_observed':3,'latest_session_expired':True,'native_macro_compile_success_verified':True,'file_download_supported':None,'native_files_recovered_locally':0,'capabilities_note':'Native VBA compile/run and partial STEP import/save observed. Design Premium edition visible. Enabled engineering add-ins, full native assembly, download/recovery and any engineering study remain unverified.'})
evidence=['results/full_static_native_attempt.png','results/native_save_error_tail.png','results/full_static_v3_native_outcome.png','results/full_static_v3_progress.png','results/full_static_v3_result.png','scripts/AutoFullArmStaticV4_source_audit.json']
ledger['trial']['evidence']=list(dict.fromkeys(ledger['trial'].get('evidence',[])+[(root/e).as_posix() for e in evidence]))
history={e.get('id','legacy-'+str(i)):e for i,e in enumerate(ledger.get('session_events',[]))};history.update({e['id']:e for e in events});ledger['session_events']=list(history.values());ledger['macro_attempts']=macro_states
for stage in ledger['stages']:
 if stage['id']=='P0':
  stage.update({'status':'PARTIAL_ACCESS_NO_RECOVERED_CHECKPOINT','observed':'Native app/compiler and partial import/save reached; third session expired before any native save/download smoke checkpoint was recovered.','passed':None,'finished_at':None,'evidence':[(root/'results/trial_access_status.json').as_posix()]})
 elif stage['id']=='P1':
  stage.update({'status':'NOT_COMPLETED_PARTIAL_LINK_IMPORT_EVIDENCE','started_at':date+' (exact time not recorded)','observed':'Separate rigid-link STEP imports ran in the cloud; no full-arm static checkpoint, aggregate diagnostics or downloaded native geometry was obtained.','passed':None,'finished_at':None,'evidence':[(root/'results/full_static_v3_native_outcome.png').as_posix(),(root/'results/full_static_v3_progress.png').as_posix()]})
 elif stage['id']=='P2':
  stage.update({'status':'ATTEMPTED_BLOCKED_RUNTIME_438_NOT_RECOVERED','started_at':date+' (exact time not recorded)','observed':'V3 reached assembly creation after its 28 import/save iterations, then failed on first-component Transform2 assignment. Completed import/save loop is inferred from audited source control flow. No full static assembly was completed or downloaded.','passed':None,'finished_at':None,'evidence':[(root/'results/full_static_v3_result.png').as_posix()]})
for row in ledger['link_imports']:
 row.update({'status':'PARTIAL_CLOUD_IMPORT_EVIDENCE_NOT_RECOVERED','started_at':date+' (exact time not recorded)','finished_at':None,'observed':'V3 reached CreateStaticAssembly after its sequential 28-part import/save loop. This supports transient cloud import/save by control-flow inference. Individual diagnostics, downloaded native bytes and reopen checks are unavailable; no acceptance PASS assigned.','passed':None,'evidence':[(root/'results/full_static_v3_result.png').as_posix(),(root/'scripts/AutoFullArmStaticV3.bas').as_posix()]})
 if row['link'] in ('index_intermediate','thumb_proximal'):
  filename='full_static_v3_native_outcome.png' if row['link']=='index_intermediate' else 'full_static_v3_progress.png'
  row['native_solid_count']=12
  row['observed']+=' A screenshot directly shows this part with Solid Bodies(12).'
  row['evidence'].append((root/'results'/filename).as_posix())
 if row['link']=='base_link':
  row['observed']+=' V2 save diagnostic directly reports RETURN=True, ERRORS=0, WARNINGS=0; V3 assembly screenshot shows base_link inserted.'
  row['evidence'].append((root/'results/native_save_error_tail.png').as_posix())
 row['native_part_path']=None;row['native_file_sha256']=None
ledger['recovery_status']={'status':'NO_NATIVE_CAD_RECOVERED_BEFORE_THIRD_SESSION_EXPIRY','downloaded_native_files':0,'cloud_temporary_output_status':'Deleted per advertised session policy; no post-expiry filesystem inspection claimed.','next_action':'Execute corrected packaging-capable macro in next offered session, then promptly download and verify a native checkpoint.'}
assert all(s.get('passed') is None for s in ledger['stages'])
assert all(r.get('passed') is None for r in ledger['link_imports'])
assert all(r['status']=='NOT_EXECUTED' and r.get('passed') is None for r in ledger['joint_tests'])
assert not ledger['downloaded_artifacts'] and not ledger['core_deliverable']['full_native_assembly_completed'] and not ledger['core_deliverable']['native_motion_study_completed'] and not ledger['fea_gate']['solver_run']
write(ledger_path,ledger)

summary='''SOLIDWORKS PROJECT — PARTIAL NATIVE IMPORT EVIDENCE; NO RECOVERED CAD CHECKPOINT
Updated 6 October 2026, after third cloud session expired

Native SOLIDWORKS Design Premium 2026 SP0 ran in the approved official cloud trial.
The user approved its software license and project uploads. Local source files
remain on D:. No local SOLIDWORKS installation or purchase occurred.

THIRD-SESSION RESULTS
Full-static V1 compiled natively but stopped on preference readback. V2 imported
base_link and its SaveAs diagnostic reported True, zero errors, zero warnings;
an incorrect VBA Boolean check then falsely treated that return as failure.

V3 corrected those checks and reached assembly creation after its 28-part
import/save loop. Screenshots directly show index_intermediate and thumb_proximal
with 12 solid bodies. All-28 import/save completion is supported by audited source
control flow, not by 28 individually recovered native files. Assembly placement
then stopped at the first component with runtime error 438 on Transform2.

V4 corrects that property assignment using comp.Transform2 = transform without
Set. It is staged; its native execution is unverified. Third session expired
before any native CAD file could be downloaded. Remote Temporary Files are deleted
under the trial's session-end policy. The screenshots preserve partial evidence,
but there is no locally recovered SLDPRT/SLDASM checkpoint and no full assembly.

NEXT ACTION — TASK REMAINS INCOMPLETE
Prepare/review V5 with automatic single-ZIP preservation, use the next official
vendor-offered session if available, and download a verified checkpoint promptly.
The fourth session is planned at this snapshot, not yet recorded as launched.
The user approved browser temporary downloads followed by moving results to D:.

UNEXECUTED ENGINEERING WORK
27-joint mates and motion, interference acceptance, quantitative dynamics and FEA
have not passed or been completed. An imported part or an all-fixed static
assembly does not establish articulation. Source audits and MuJoCo results must
not be presented as native SOLIDWORKS engineering studies.

EVIDENCE AND FILES
results/full_static_v3_result.png: base_link assembly and runtime error 438.
results/full_static_v3_native_outcome.png: index_intermediate, Solid Bodies(12).
results/full_static_v3_progress.png: thumb_proximal, Solid Bodies(12).
results/native_save_error_tail.png: V2 save returned True / 0 errors / 0 warnings.
results/trial_access_status.json: chronological session and failure evidence.
studies/native_results_ledger.json: partial imports recorded; no test PASS.
transfer/: 28 STEP sources, 293-body inventory, 27-joint definition and validated
FreeCAD/OpenCascade transfer data. This remains the reproducible local source.
scripts/AutoFullArmStaticV4*: corrected staged source; later V5 is for packaging.

STORAGE
Remote cloud files are not D: files. Recover each milestone with dependencies.
No native engineering completion is claimed by this status update.
'''
(root/'START HERE.txt').write_text(summary,encoding='utf-8')
access=root/'docs/installation_and_access.txt';old=access.read_text(encoding='utf-8-sig');sources=old[old.index('OFFICIAL SOURCES'):] if 'OFFICIAL SOURCES' in old else ''
access.write_text('SOLIDWORKS ACCESS, STORAGE AND EXECUTION STATUS — 6 October 2026\n\n'+summary+'\nLOCAL INSTALLATION\nA desktop installation could place its main program on D:, but Windows-managed prerequisites and installer data cannot be promised exclusively on D:. No installer ran. The approved cloud trial is the active route.\n\n'+sources,encoding='utf-8')
manifest_path=root/'preparation_manifest.json';manifest=read(manifest_path)
manifest.update({'updated_date':date,'status':'Third cloud session expired after partial native imports and first-component assembly error; no recovered native CAD; V4 staged, V5 packaging and fourth session planned','trial_access_status':state,'native_solidworks_cloud_opened':True,'native_solidworks_version':'Design Premium 2026 SP0','native_solidworks_tests_run':True,'native_solidworks_tests_run_scope':status['native_solidworks_tests_run_scope'],'native_engineering_studies_run':False,'native_geometry_outputs_verified':False,'native_geometry_partial_import_evidence':True,'native_files_recovered_locally':0,'temporary_browser_download_then_move_to_D_authorized':True})
included=[root/'START HERE.txt',status_path]
for folder in ('transfer','studies','docs'):
 included.extend(p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
for pattern in ('AutoFingerImportV2*','AutoFullArmStaticV*'):
 included.extend((root/'scripts').glob(pattern))
included.extend(root/e for e in evidence if (root/e).exists())
included=sorted(set(included));manifest['files']=[{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in included];write(manifest_path,manifest)
archive=root/'AnthroArm27_SOLIDWORKS_Preparation.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in included+[manifest_path]:z.write(p,p.relative_to(root).as_posix())
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps({'status':state,'native_partial_import_evidence':True,'local_native_CAD_recovered':0,'engineering_tests_passed':False,'articulation_motion_fea':'NOT_EXECUTED','preparation_zip_integrity':True},indent=2))
