"""Record fourth-session native static success and unconfirmed local recovery.

This is a historical evidence snapshot, not browser control or native execution.
"""
from pathlib import Path
import hashlib,json,zipfile
root=Path(r'D:\RoboticArm\solidworks');date='2026-10-06'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
status_path=root/'results/trial_access_status.json';status=read(status_path)
state='FOURTH_SESSION_ENDED_NATIVE_STATIC_BUILT_REMOTE_ZIP_VERIFIED_LOCAL_RECOVERY_UNCONFIRMED'
archive_name='AnthroArm27_Static_20261006_095036_35436562_NATIVE_RECOVERED_20261006_102327_37407207.zip'
evidence=['results/full_static_v5_native_result.png','results/native_archive_recovered.png']
archive={'filename':archive_name,'location':'Vendor cloud Temporary Files; not a local D: path','contents':{'native_parts':28,'native_assemblies':1,'original_build_logs':1,'total_files':30},'approximately_MB':10,'remote_archive_verified':True,'verification_basis':'ArchiveNativeResultsV1 reported a verified archive after manual Window > Close All. Screenshot preserves the success message; source validates the 30 allowlisted entries and contents.','remote_sha256':None,'download_attempted':True,'download_result':'Browser waitForEvent/download click timed out before session expiry. No local completed download was confirmed.','local_path':None,'local_sha256':None,'locally_reopened':False,'availability_after_session_end':'Not recoverable through the expired session; Temporary Files subject to vendor deletion policy. No post-expiry remote filesystem inspection claimed.'}
status.update({'date':date,'status':state,'official_sessions_launched_observed':4,'latest_observed_session_expired':True,'current_session_active':False,'snapshot_is_live_state':False,'observed_controls':['Native SOLIDWORKS Design Premium 2026 SP0 full arm assembly','V5 geometry saved; automatic ZIP packaging failure','Manual Window > Close All','ArchiveNativeResultsV1 verified native archive message','Download attempt timeout; fourth session ended'],
 'screenshot':evidence[0],'screenshot_scope':'Completed all-fixed native full arm visible behind a ZIP-packaging failure dialog. This is a static assembly, not articulated motion.',
 'native_geometry_import_verified':True,'native_geometry_import_verified_scope':'Native V5 passed required 28-part/293-solid import and static placement/save gates before entering packaging; full assembly visible in native screenshot.',
 'native_geometry_outputs_verified':True,'native_geometry_outputs_verified_scope':'Saved geometry and a verified 30-file archive existed in remote cloud Temporary Files. No local native CAD checkpoint is confirmed.',
 'native_full_static_assembly_built_in_cloud':True,'native_static_components':28,'native_imported_solids':293,'native_full_assembly_completed':False,'native_full_assembly_completed_scope':'Requested articulated assembly with 27 joints remains incomplete; all-fixed static assembly was built.',
 'local_native_cad_files_recovered':0,'local_native_checkpoint_verified':False,'native_engineering_studies_run':False,
 'native_solidworks_tests_run':True,'native_solidworks_tests_run_scope':'Native import/count/transform/save gates and remote archive verification executed. Articulation, DIP test, Motion and FEA did not execute.',
 'native_macro_compile_success_verified':True,'native_macro_compile_success_scope':'Full-static V5 executed through successful geometry save; ArchiveNativeResultsV1 executed successfully after closing documents. V6 remains under preparation.',
 'current_macro_source':'scripts/AutoFullArmStaticV5.swb','macro_source_note':'Executed V5 produced a complete static cloud assembly but packaging failed while files remained open. ArchiveNativeResultsV1 later produced a verified remote ZIP. V6 is being prepared to close saved documents before robust packaging.',
 'remote_verified_archive':archive,'cloud_temporary_files_status':'Fourth session ended before local recovery. Remote files are subject to vendor session-end deletion policy; no current availability is claimed.',
 'next_action':'Finish/review V6 auto-close and robust ZIP preparation; obtain and verify an actual local native checkpoint before proceeding to joint/motion work. Any further official session is a future action, not recorded as launched here.',
 'scope':'Native static geometry was built/saved and its remote archive verified. Local recovery is unconfirmed. Requested articulated robot, simulation/testing and complete project remain unfinished.',
 'observation_basis':'Operating agent report, locally viewed native screenshots, and audited macro sequencing. No browser/native actions are performed by this recording script.',
})
status.pop('planned_next_session',None)
events=[
 {'id':'2026-10-06-session4-v5-static','date':date,'session':4,'event':'V5_NATIVE_STATIC_GEOMETRY_BUILT_AND_SAVED','observation':'V5 completed the native 28-part/293-solid import, placement, rebuild and save gates. Full all-fixed arm and SLDASM visible. No mates, articulated movement or engineering study are implied.','engineering_result':None,'evidence':[evidence[0]]},
 {'id':'2026-10-06-session4-v5-zip','date':date,'session':4,'event':'V5_AUTOMATIC_ZIP_PACKAGING_FAILED','observation':'V5 stopped after saving geometry because ZIP packaging/validation failed; dialog noted code 124 denotes the bounded job wait expiring. Geometry remained in cloud at that point.','engineering_result':None,'evidence':[evidence[0]]},
 {'id':'2026-10-06-session4-archive','date':date,'session':4,'event':'DOCUMENTS_CLOSED_REMOTE_30_FILE_ARCHIVE_VERIFIED','observation':'After manual Window > Close All, ArchiveNativeResultsV1 succeeded and verified a remote archive of 28 parts, one assembly and original build log. Approximately 10 MB.','engineering_result':None,'evidence':[evidence[1]],'archive_filename':archive_name},
 {'id':'2026-10-06-session4-download','date':date,'session':4,'event':'DOWNLOAD_TIMEOUT_BEFORE_SESSION_END','observation':'Browser download waitForEvent/click timed out; no completed local download confirmed before the fourth trial ended. No D: native CAD checkpoint is recovered.','engineering_result':None},
 {'id':'2026-10-06-v6-preparation','date':date,'event':'V6_AUTO_CLOSE_ZIP_SOURCE_IN_PREPARATION','observation':'V6 is being prepared to close saved project documents before robust allowlisted ZIP packaging. Native V6 execution has not been verified.','engineering_result':None},
]
history={e.get('id','old-'+str(i)):e for i,e in enumerate(status.get('session_history',[]))};history.update({e['id']:e for e in events});status['session_history']=list(history.values())
newmacros=[{'name':'AutoFullArmStaticV5','status':'NATIVE_STATIC_SAVE_SUCCEEDED_AUTOMATIC_ZIP_FAILED','native_compiled':True,'native_geometry_stage_completed':True,'native_run_completed':False},{'name':'ArchiveNativeResultsV1','status':'NATIVE_REMOTE_ARCHIVE_VERIFIED_AFTER_CLOSE_ALL','native_compiled':True,'native_run_completed':True,'local_download_completed':False},{'name':'AutoFullArmStaticV6','status':'SOURCE_IN_PREPARATION_NATIVE_EXECUTION_UNVERIFIED','native_compiled':False,'native_run_completed':False}]
existing={m['name']:m for m in status.get('macro_sources',[])};existing.update({m['name']:m for m in newmacros});status['macro_sources']=list(existing.values());save(status_path,status)

ledger_path=root/'studies/native_results_ledger.json';ledger=read(ledger_path)
ledger['updated_date']=date;ledger['purpose']='Native static assembly and remote archive are evidenced; local recovery remains unconfirmed. Articulated assembly and engineering studies remain unfinished.'
ledger['trial'].update({'access_status':state,'official_sessions_launched_observed':4,'latest_session_expired':True,'native_macro_compile_success_verified':True,'native_files_recovered_locally':0,'native_static_geometry_saved_remotely':True,'remote_archive_verified':True,'file_download_supported':None,'file_download_attempt_observed':True,'file_download_completed_verified':False,'capabilities_note':'Native Design Premium 2026 SP0 built/saved the all-fixed full arm. Remote ZIP verified after closing documents. Browser download timed out; local recovery and engineering add-in/study execution remain unverified.'})
ledger['trial']['evidence']=list(dict.fromkeys(ledger['trial'].get('evidence',[])+[(root/e).as_posix() for e in evidence]))
history={e.get('id','old-'+str(i)):e for i,e in enumerate(ledger.get('session_events',[]))};history.update({e['id']:e for e in events});ledger['session_events']=list(history.values())
existing={m['name']:m for m in ledger.get('macro_attempts',[])};existing.update({m['name']:m for m in newmacros});ledger['macro_attempts']=list(existing.values())
ledger['core_deliverable'].update({'native_static_assembly_built_in_cloud':True,'native_static_assembly_saved_in_cloud':True,'native_static_part_count':28,'native_static_solid_count':293,'native_static_components_all_fixed':True,'native_static_archive_verified_remotely':True,'local_native_checkpoint_verified':False,'full_native_assembly_completed':False,'full_native_assembly_completed_note':'The requested 27-joint articulated assembly remains incomplete; current successful native build is all-fixed/static.','native_motion_study_completed':False})
for stage in ledger['stages']:
 if stage['id']=='P0':
  stage.update({'status':'NATIVE_SAVE_REMOTE_ZIP_VERIFIED_LOCAL_DOWNLOAD_UNCONFIRMED','observed':'Native static output and remote archive were created and verified. Local smoke-checkpoint download/reopen requirement remains unmet after browser timeout and session end.','passed':None,'finished_at':None,'evidence':[(root/evidence[1]).as_posix()]})
 elif stage['id']=='P1':
  stage.update({'status':'NATIVE_STATIC_BUILT_SAVED_NOT_RECOVERED_LOCALLY','observed':'V5 built/saved complete native static arm from 28 parts/293 source solids; native screenshot and subsequent archive verification evidence cloud output. Local native checkpoint and independent reopen are missing.','passed':None,'finished_at':None,'evidence':[(root/e).as_posix() for e in evidence]})
 elif stage['id']=='P2':
  stage.update({'status':'ALL_FIXED_NATIVE_STATIC_CLOUD_BUILD_VERIFIED_RECOVERY_PENDING','observed':'28 native parts and all-fixed SLDASM passed V5 count, placement, rebuild and save gates, then were included in verified remote ZIP. Required local dependency download and free/non-base component setup for articulation remain undone.','passed':None,'finished_at':None,'evidence':[(root/e).as_posix() for e in evidence]})
for row in ledger['link_imports']:
 row.update({'status':'NATIVE_CLOUD_IMPORTED_SAVED_ARCHIVED_NOT_LOCALLY_RECOVERED','native_solid_count':row['expected_solid_count'],'native_solid_count_evidence_basis':'V5 strict per-part import/body-count gates completed before static assembly and verified archive; not independently remeasured from downloaded files.','native_part_path':None,'native_file_sha256':None,'observed':'V5 completed this part import, expected solid-count and save gates; ArchiveNativeResultsV1 verified its inclusion in the 28-part remote package. No local file/reopen/diagnostic record recovered.','passed':None,'finished_at':None,'evidence':[(root/e).as_posix() for e in evidence]})
ledger['remote_artifacts']=[archive]
ledger['recovery_status']={'status':'VERIFIED_REMOTE_NATIVE_ARCHIVE_DOWNLOAD_UNCONFIRMED_SESSION_ENDED','downloaded_native_files':0,'archive_filename':archive_name,'remote_archive_verified':True,'local_path':None,'download_attempt':'Browser waitForEvent/click timed out before session end.','next_action':'Use corrected automatic close/packaging source, then confirm actual local download and ZIP/native dependency integrity before claiming a recovered deliverable.'}
assert not ledger['downloaded_artifacts']
assert all(r['status']=='NOT_EXECUTED' and r.get('passed') is None for r in ledger['joint_tests'])
assert not ledger['core_deliverable']['full_native_assembly_completed'] and not ledger['core_deliverable']['native_motion_study_completed'] and not ledger['fea_gate']['solver_run']
assert all(s.get('passed') is None for s in ledger['stages'])
save(ledger_path,ledger)

summary='''SOLIDWORKS PROJECT — NATIVE STATIC ARM BUILT; LOCAL RECOVERY STILL UNCONFIRMED
Updated 6 October 2026, after fourth official trial session ended

ACTUAL NATIVE RESULT
SOLIDWORKS Design Premium 2026 SP0 built and saved the complete static arm: 28
native multibody parts, 293 source solids, and AnthroArm27_STATIC_HOME.SLDASM.
V5 passed its per-part count, transform/placement, rebuild and save gates before
packaging. The native screenshot shows the complete arm and its component tree.
All components are fixed: this is static CAD, not the 27-joint moving assembly.

ARCHIVE AND DOWNLOAD RESULT
V5 automatic ZIP packaging failed after the geometry had been saved. After manual
Window > Close All, ArchiveNativeResultsV1 succeeded: a verified remote archive
contained 28 parts, the assembly and its original build log (30 files, about 10 MB).
The browser download waitForEvent/click then timed out. The fourth session ended
before a completed local download was confirmed. No native CAD checkpoint has
been recovered on D:, and remote Temporary Files are subject to deletion on expiry.
The archive's word RECOVERED refers to creation in the cloud, not a local download.

REMOTE ARCHIVE NAME
'''+archive_name+'''

WHAT IS STILL REQUIRED
V6 is being prepared to close saved documents automatically before robust ZIP
packaging. Obtain and verify the actual local native archive/dependencies first.
Then build/audit the 27 revolute joints and run the requested movement and tests.
No DIP articulation demonstration, Motion study, interference acceptance or FEA
has been executed. The whole project is not complete.

LOCAL EVIDENCE
results/full_static_v5_native_result.png: full native arm behind ZIP failure dialog.
results/native_archive_recovered.png: verified remote archive success message.
results/trial_access_status.json: chronological sessions, outcomes and limitations.
studies/native_results_ledger.json: cloud static success; local checkpoint pending.
transfer/: reproducible STEP geometry, 293-body inventory and 27-joint definition.
scripts/AutoFullArmStaticV5*: executed static build source.
scripts/ArchiveNativeResultsV1*: executed archive recovery source.
V6 source is in preparation; native V6 execution remains unverified.

AUTHORIZATION AND STORAGE
The official cloud trial, CAD upload and software license were approved. The user
also approved temporary browser downloads followed by moving results to D:.
No product purchase or local SOLIDWORKS installation occurred. Cloud files are
remote until a completed download is verified; screenshots alone are not editable
native CAD deliverables. Existing MuJoCo demonstrations remain labelled MuJoCo.
'''
(root/'START HERE.txt').write_text(summary,encoding='utf-8')
access=root/'docs/installation_and_access.txt';old=access.read_text(encoding='utf-8-sig');sources=old[old.index('OFFICIAL SOURCES'):] if 'OFFICIAL SOURCES' in old else ''
access.write_text('SOLIDWORKS ACCESS, STORAGE AND EXECUTION — 6 October 2026\n\n'+summary+'\nLOCAL INSTALLATION\nNo installer ran. A future desktop installation could put its main program on D:, but Windows-managed prerequisites and installer data cannot be promised exclusively on D:.\n\n'+sources,encoding='utf-8')
manifest_path=root/'preparation_manifest.json';manifest=read(manifest_path)
manifest.update({'updated_date':date,'status':'Fourth session built/saved 28-part native static arm and verified remote ZIP; download timed out and no local native checkpoint confirmed; articulation/studies incomplete','trial_access_status':state,'native_solidworks_tests_run':True,'native_solidworks_tests_run_scope':status['native_solidworks_tests_run_scope'],'native_engineering_studies_run':False,'native_geometry_outputs_verified':True,'native_geometry_outputs_verified_scope':'Remote static files and archive only; local recovery unconfirmed.','native_static_assembly_built_in_cloud':True,'remote_native_archive_verified':True,'native_files_recovered_locally':0,'local_native_checkpoint_verified':False})
included=[root/'START HERE.txt',status_path]
for folder in ('transfer','studies','docs'):
 included.extend(p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
for pattern in ('AutoFingerImportV2*','AutoFullArmStaticV*','ArchiveNativeResultsV1*'):
 included.extend((root/'scripts').glob(pattern))
included.extend(root/e for e in evidence)
included=sorted(set(included));manifest['files']=[{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in included];save(manifest_path,manifest)
archive_path=root/'AnthroArm27_SOLIDWORKS_Preparation.zip'
with zipfile.ZipFile(archive_path,'w',zipfile.ZIP_DEFLATED) as z:
 for p in included+[manifest_path]:z.write(p,p.relative_to(root).as_posix())
with zipfile.ZipFile(archive_path) as z:assert z.testzip() is None
print(json.dumps({'status':state,'native_static_cloud_build':True,'remote_archive_verified':True,'local_native_recovered':False,'articulation_motion_fea':'NOT_EXECUTED','whole_project_complete':False,'preparation_zip_checked':True},indent=2))
