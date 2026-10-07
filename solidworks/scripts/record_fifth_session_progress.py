"""Fifth-session snapshot: V6 static + remote ZIP PASS; local download unanswered."""
from pathlib import Path
import hashlib,json,zipfile
root=Path(r'D:\RoboticArm\solidworks');date='2026-10-06'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
state='FIFTH_SESSION_V6_NATIVE_STATIC_AND_REMOTE_ZIP_PASS_LOCAL_DOWNLOAD_PENDING'
zipname='AnthroArm27_Static_20261006_105654_39414012_NATIVE.zip'
evidence=['results/full_static_v6_native_result.png','results/native_v6_download_ready.png']
status_path=root/'results/trial_access_status.json';status=read(status_path)
archive={'filename':zipname,'session':5,'location':'Vendor cloud Temporary Files; not a D: file','contents':{'native_parts':28,'native_assemblies':1,'original_build_logs':1,'total_files':30},'approximately_MB':10,'remote_archive_verified':True,'verification_status':'PASS_REMOTE_ONLY','verification_basis':'V6 completed native save, CloseAllDocuments(True), no-open-document check and exact 30-file ZIP verification; success message and remote file listing captured. ZIP verification checks names, entry count, sizes and readable streams.','remote_sha256':None,'download_attempted':True,'download_result':'Automated README click test, downloadMedia attempt and download-event wait did not produce a confirmed local file. User manual-download question pending.','local_path':None,'local_sha256':None,'locally_reopened':False,'user_download_confirmation_received':False,'availability_note':'Archive visible during fifth-session snapshot. No availability beyond session expiry is promised.'}
status.update({'date':date,'status':state,'official_sessions_launched_observed':5,'latest_observed_session_expired':False,'current_session_active':True,'snapshot_is_live_state':False,'screenshot':evidence[0],'screenshot_scope':'Actual SOLIDWORKS V6 completion message confirms static native saves and verified ZIP; message explicitly states all-fixed/no mates/Motion/FEA.',
 'observed_controls':['V6 native static save and ZIP verified success message','Temporary Files listing of named 10 MB archive','Manual download requested from user; reply not received'],
 'native_geometry_outputs_verified':True,'native_geometry_outputs_verified_scope':'Native static output and archive verified remotely; no confirmed local native download.',
 'native_static_verification_status':'PASS_NATIVE_STATIC_ONLY','remote_archive_verification_status':'PASS_REMOTE_ONLY','native_full_static_assembly_built_in_cloud':True,'native_static_components':28,'native_imported_solids':293,
 'native_full_assembly_completed':False,'native_full_assembly_completed_scope':'All-fixed static assembly passed; requested 27-joint articulated assembly remains incomplete.',
 'native_solidworks_tests_run':True,'native_solidworks_tests_run_scope':'V6 native import/count/transform/rebuild/save, auto-close and remote ZIP gates completed. No DIP movement, Motion study or FEA was executed in this snapshot.',
 'native_engineering_studies_run':False,'native_macro_compile_success_verified':True,'native_macro_compile_success_scope':'V6 executed through final successful native static/ZIP message in fifth session.',
 'local_native_cad_files_recovered':0,'local_native_checkpoint_verified':False,
 'current_macro_source':'scripts/AutoFullArmStaticV6.swb','macro_source_note':'V6 successfully executed native static import/placement/save, automatic document closing and verified 30-file archive. Local recovery remains pending.',
 'remote_verified_archive':archive,'manual_download_question_pending':True,'manual_download_reply_received':False,
 'reported_session_expiry_local':'2026-10-06 19:36 Asia/Shanghai','reported_session_expiry_basis':'Operating agent report; user-facing expiry was 7:36 PM. This bookkeeping script did not inspect a live timer.',
 'cloud_temporary_files_status':'Named V6 archive visible in fifth-session Temporary Files at snapshot. Temporary files are subject to deletion on expiry; no local recovery confirmed.',
 'next_action':'Allow the user to answer the pending manual-download request; verify a completed local ZIP before recording recovery. DIP work may be attempted subsequently but has not happened in this snapshot.',
 'scope':'PASS is scoped to native static CAD and remote ZIP only. No user download reply, local checkpoint, 27-joint articulation, Motion or FEA completion is assumed.',
})
events=[{'id':'2026-10-06-session5-v6','date':date,'session':5,'event':'V6_NATIVE_STATIC_AND_AUTOMATIC_ZIP_PASS','observation':'V6 completed 28 native parts/293 solids, static assembly save, automatic close and verified 30-file ZIP. Native message explicitly labels all-fixed/static, no mates/Motion/FEA.','scoped_result':'PASS_NATIVE_STATIC_AND_REMOTE_ZIP_ONLY','evidence':evidence},
 {'id':'2026-10-06-session5-download-attempts','date':date,'session':5,'event':'AUTOMATED_DOWNLOAD_NO_CONFIRMED_FILE','observation':'Independent README click test produced no confirmed local file; downloadMedia failed and download-event wait timed out. Archive remains a remote artifact at snapshot.','engineering_result':None},
 {'id':'2026-10-06-session5-user-download','date':date,'session':5,'event':'USER_MANUAL_DOWNLOAD_QUESTION_PENDING','observation':'User asked to manually download the displayed archive before reported 19:36 local expiry. No reply or completed local download is recorded.','engineering_result':None}]
for field in ('session_history',):
 history={e.get('id','old-'+str(i)):e for i,e in enumerate(status.get(field,[]))};history.update({e['id']:e for e in events});status[field]=list(history.values())
macro={'name':'AutoFullArmStaticV6','status':'NATIVE_STATIC_AND_REMOTE_ARCHIVE_PASS_LOCAL_RECOVERY_PENDING','native_compiled':True,'native_run_completed':True,'native_geometry_stage_completed':True,'automatic_close_completed':True,'remote_archive_verified':True,'local_download_completed':False}
existing={m['name']:m for m in status.get('macro_sources',[])};existing[macro['name']]=macro;status['macro_sources']=list(existing.values());save(status_path,status)

ledger_path=root/'studies/native_results_ledger.json';ledger=read(ledger_path)
ledger['updated_date']=date;ledger['purpose']='V6 native static CAD and remote archive passed in fifth session. Local recovery is pending; articulation and engineering studies remain unfinished.'
ledger['trial'].update({'access_status':state,'official_sessions_launched_observed':5,'latest_session_expired':False,'native_macro_compile_success_verified':True,'native_files_recovered_locally':0,'native_static_geometry_saved_remotely':True,'remote_archive_verified':True,'file_download_completed_verified':False,'manual_download_question_pending':True,'manual_download_reply_received':False,'reported_session_expiry_local':'2026-10-06 19:36 Asia/Shanghai','capabilities_note':'V6 completed static native CAD, automatic document close and remote ZIP verification. Automated local download attempts did not confirm a file; user request remains unanswered. No native DIP/Motion/FEA executed in this snapshot.'})
ledger['trial']['evidence']=list(dict.fromkeys(ledger['trial'].get('evidence',[])+[(root/e).as_posix() for e in evidence]))
history={e.get('id','old-'+str(i)):e for i,e in enumerate(ledger.get('session_events',[]))};history.update({e['id']:e for e in events});ledger['session_events']=list(history.values())
existing={m['name']:m for m in ledger.get('macro_attempts',[])};existing[macro['name']]=macro;ledger['macro_attempts']=list(existing.values())
ledger['scoped_native_verification']={'static_cad':{'status':'PASS','scope':'V6 28 imported native parts, 293 source solids, all-fixed assembly, body/count/transform/rebuild/save gates','evidence':[(root/evidence[0]).as_posix()],'does_not_include':['27-joint mates','movement','engineering loads','local recovery/reopen']},'remote_zip':{'status':'PASS','scope':'Automatic close followed by exactly 30 named files in remote ZIP; names/counts/sizes/readable-stream verification','archive_filename':zipname,'evidence':[(root/e).as_posix() for e in evidence],'local_download_passed':False},'local_recovery':{'status':'PENDING_USER_DOWNLOAD_NO_CONFIRMED_FILE','passed':None}}
ledger['core_deliverable'].update({'native_static_assembly_built_in_cloud':True,'native_static_assembly_saved_in_cloud':True,'native_static_components_all_fixed':True,'native_static_archive_verified_remotely':True,'native_static_scoped_verification_passed':True,'local_native_checkpoint_verified':False,'full_native_assembly_completed':False,'native_motion_study_completed':False})
for stage in ledger['stages']:
 if stage['id'] in ('P0','P1','P2'):
  stage['status']='NATIVE_STATIC_AND_REMOTE_ZIP_PASS_LOCAL_CHECKPOINT_PENDING'
  stage['passed']=None;stage['finished_at']=None
  stage['observed']='V6 native static and remote archive gates passed; see scoped_native_verification. This broader stage still requires local recovery/reopen and, for P2, non-base components ready for articulation. Manual-download question is unanswered.'
  stage['evidence']=[(root/e).as_posix() for e in evidence]
for row in ledger['link_imports']:
 row.update({'status':'NATIVE_IMPORT_COUNT_SAVE_GATE_PASS_LOCAL_REOPEN_PENDING','native_import_count_save_gate_passed':True,'native_solid_count':row['expected_solid_count'],'native_solid_count_evidence_basis':'V6 strict per-part native count/save gate; full successful completion evidenced.','observed':'V6 native import/count/save completed and verified remote ZIP includes this part. No downloaded local file, SHA256 or independent native reopen yet.','passed':None,'native_part_path':None,'native_file_sha256':None,'evidence':[(root/e).as_posix() for e in evidence]})
archives={a['filename']:a for a in ledger.get('remote_artifacts',[])};archives[zipname]=archive;ledger['remote_artifacts']=list(archives.values())
ledger['recovery_status']={'status':'V6_REMOTE_ZIP_PASS_USER_DOWNLOAD_PENDING','archive_filename':zipname,'remote_archive_verified':True,'local_path':None,'downloaded_native_files':0,'user_question_pending':True,'user_reply_received':False,'next_action':'Confirm an actual downloaded ZIP, move to D: if browser temporarily stores elsewhere, verify archive/dependencies and reopen native CAD. Do not infer completion from elapsed time.'}
assert not ledger['downloaded_artifacts'] and not ledger['core_deliverable']['full_native_assembly_completed'] and not ledger['core_deliverable']['native_motion_study_completed'] and not ledger['fea_gate']['solver_run']
assert all(x['status']=='NOT_EXECUTED' for x in ledger['joint_tests'])
save(ledger_path,ledger)

summary='''SOLIDWORKS PROJECT — V6 NATIVE STATIC AND REMOTE ARCHIVE PASS; DOWNLOAD PENDING
Snapshot: 6 October 2026, fifth official cloud session

V6 successfully created and saved 28 native parts (293 source solid bodies) and
the complete all-fixed native assembly. It automatically closed the saved CAD
documents and verified a 30-file archive containing those parts, assembly and
original build log. This is actual SOLIDWORKS Design Premium 2026 SP0 execution.

REMOTE ZIP (about 10 MB)
'''+zipname+'''

AUTOMATED DOWNLOAD REMAINS UNCONFIRMED
The small README click test produced no confirmed local file, downloadMedia
failed and the download-event wait timed out. The user has been asked to download
the displayed ZIP manually before the reported 7:36 PM local session expiry.
No answer or actual local file is recorded at this snapshot. The request remains
pending; this document does not assume a reply or a successful download.

PASS SCOPE
Native static geometry and the remote ZIP passed their stated macro gates.
Local recovery/reopen, the 27-joint moving assembly, DIP movement, Motion studies
and FEA are still pending. The complete project is not finished.

FILES TO SHOW
results/full_static_v6_native_result.png — native success message.
results/native_v6_download_ready.png — actual archive listed in Temporary Files.
results/full_static_v5_native_result.png — full native arm visible from prior run.
docs/WHERE_THE_CODE_AND_RESULTS_ARE.txt — plain-language project explanation.
results/trial_access_status.json — detailed session and download evidence.
studies/native_results_ledger.json — scoped static/ZIP PASS and unfinished stages.

The user approved the free official trial, CAD upload, license and temporary
browser downloads followed by moving the deliverable to D:. A remote archive is
not a local D: deliverable until an actual download is verified. Existing MuJoCo
movement/camera results remain MuJoCo results. No local SOLIDWORKS installation
or purchase occurred.
'''
(root/'START HERE.txt').write_text(summary,encoding='utf-8')
explanation='''HOW TO EXPLAIN THIS ROBOTIC ARM PROJECT
Evidence snapshot: 6 October 2026, after fifth-session V6 native static success

WHAT TO SAY FIRST
"This is a human-shaped robotic arm and hand concept. We created its geometry,
tested 27 controlled joints in MuJoCo, and have now also built the full static
model natively in SOLIDWORKS. SOLIDWORKS articulation and engineering tests are
the next stage. The physical robot has not yet been built or qualified."

1. THE ORIGINAL 3D DESIGN
Software: FreeCAD, driven by Python.
Code: D:/RoboticArm/design/v3/build_reference_arm.py
Editable source CAD: D:/RoboticArm/design/v3/AnthroArm27_ReferenceV3.FCStd
The code defines smooth arm/palm/finger shells, pad recesses, hinge envelopes,
holes and internal layout concepts. The native CAD contains 293 solid bodies.
Component explanations: D:/RoboticArm/solidworks/transfer/component_inventory.csv
Design views: D:/RoboticArm/results/v3/design_stages/

2. THE TRANSFER TO SOLIDWORKS
Code: D:/RoboticArm/solidworks/scripts/export_transfer.py
Data: D:/RoboticArm/solidworks/transfer/assembly_manifest.json
This groups the 293 bodies into 28 rigid links, exports STEP in millimetres and
records link coordinate frames. The joint schedule describes seven arm axes and
20 finger/thumb axes. Importing these definitions does not automatically create
SOLIDWORKS mates. STEP also does not transfer the original Python feature history.

3. WHAT WAS ACTUALLY RUN IN SOLIDWORKS
Software: native SOLIDWORKS Design Premium 2026 SP0 in the official cloud trial.
Code: D:/RoboticArm/solidworks/scripts/AutoFullArmStaticV6.bas (VBA source)
The macro imports each rigid link as a native multibody part, checks expected
solid counts, saves the 28 SLDPRT files, places them using the documented home
transforms, and saves AnthroArm27_STATIC_HOME.SLDASM. It checks transformed points,
component count, rebuild and save returns. It then closes saved documents and
verifies a ZIP with 28 parts, one assembly and the original build log.

Actual completion proof:
D:/RoboticArm/solidworks/results/full_static_v6_native_result.png
Actual remote archive listing:
D:/RoboticArm/solidworks/results/native_v6_download_ready.png
Full arm visibly inside native SOLIDWORKS in an earlier successful geometry run:
D:/RoboticArm/solidworks/results/full_static_v5_native_result.png
That earlier screenshot has a packaging-failure dialog. V6 later fixed automatic
closing/packaging and reached its success message.

All native components are currently fixed in the reference pose. This preserves
their placement for the static checkpoint. To move them as a robot, the next
native assembly work must retain the fixed base, free the other links and create
the 27 revolute mates with correct axes, zero references and angular limits.

4. WHERE THE MOVEMENT AND CAMERA SIMULATION ALREADY WORK
Software: MuJoCo + Python; OpenCV processes the simulated RGB-D camera.
Robot physics/control: D:/RoboticArm/simulation/v3/model.py
Camera-guided reach: D:/RoboticArm/simulation/v3/vision_reach.py
Interactive local server: D:/RoboticArm/simulation/v3/server.py
Recorded joint movement: D:/RoboticArm/results/v3/full_arm_articulation.webm
Recorded camera-guided approach/contact: D:/RoboticArm/results/v3/camera_autonomy.webm
Results: D:/RoboticArm/results/v3/validation.json
These are actual MuJoCo results. They are not SOLIDWORKS motion/FEA results.
The simulated camera detects a known orange object, estimates its position, and
guides an approach that stops on contact. It is not autonomous object pickup.
The reported millimetre errors apply to that simulation, not a manufactured arm.

5. WHAT TO DOWNLOAD BEFORE THE CLOUD SESSION ENDS
In the trial's My Files > Temporary Files, the prepared archive is:
'''+zipname+'''
The current automation has not confirmed a local download. The user has a pending
manual-download request. After a successful download, move it to D:/RoboticArm/
solidworks/project/native_cloud/, verify the ZIP, and extract the complete folder.
Keep every SLDPRT beside its SLDASM so assembly references can resolve. Opening
the recovered SLDASM must be checked; native files have not yet been recovered
and reopened locally. Screenshots and the preparation ZIP are not substitutes
for this native CAD archive.

6. WHAT REMAINS BEFORE CLAIMING A WORKING PHYSICAL ARM
Inside SOLIDWORKS: create/audit joints, exercise each movement, inspect clearance,
then use available Motion/Simulation tools with defensible mass, material, load
and support inputs. Import/count/transform checks do not prove physical strength.
The actuator bodies/cable routes in the full arm are packaging concepts.
The existing single-finger prototype guide and Arduino firmware are on D:,
but no motor, printed part or complete physical robot has been tested here.

SHORT PRESENTATION ORDER
Show a CAD design-stage image; point to the component explanation.
Show the actual full arm in the SOLIDWORKS screenshot and V6 success evidence.
Play the MuJoCo articulation recording and label its software clearly.
Play the camera-contact recording and explain the detect/estimate/reach sequence.
Finish by identifying the pending native moving assembly and prototype work.
Never describe a static screenshot as motion simulation or a cloud file as a
downloaded local deliverable while the download remains unconfirmed.
'''
(root/'docs/WHERE_THE_CODE_AND_RESULTS_ARE.txt').write_text(explanation,encoding='utf-8')
access=root/'docs/installation_and_access.txt';old=access.read_text(encoding='utf-8-sig');sources=old[old.index('OFFICIAL SOURCES'):] if 'OFFICIAL SOURCES' in old else ''
access.write_text('SOLIDWORKS ACCESS AND EXECUTION STATUS — 6 October 2026\n\n'+summary+'\nLOCAL INSTALLATION\nNo installer ran. A desktop installation could put its main program on D:, but Windows-managed prerequisites and installer data cannot be promised exclusively on D:.\n\n'+sources,encoding='utf-8')
manifest_path=root/'preparation_manifest.json';manifest=read(manifest_path)
manifest.update({'updated_date':date,'status':'Fifth-session V6 native static CAD and remote ZIP PASS; manual-download question unanswered; zero confirmed local native files; articulation/studies unfinished','trial_access_status':state,'native_solidworks_tests_run':True,'native_solidworks_tests_run_scope':status['native_solidworks_tests_run_scope'],'native_engineering_studies_run':False,'native_static_scoped_verification_passed':True,'remote_native_archive_verified':True,'native_files_recovered_locally':0,'local_native_checkpoint_verified':False,'manual_download_question_pending':True})
included=[root/'START HERE.txt',status_path]
for folder in ('transfer','studies','docs'):
 included.extend(p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
for pattern in ('AutoFingerImportV2*','AutoFullArmStaticV*','ArchiveNativeResultsV1*'):
 included.extend((root/'scripts').glob(pattern))
included.extend(root/e for e in evidence+['results/full_static_v5_native_result.png'])
included=sorted(set(included));manifest['files']=[{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in included];save(manifest_path,manifest)
archive_path=root/'AnthroArm27_SOLIDWORKS_Preparation.zip'
with zipfile.ZipFile(archive_path,'w',zipfile.ZIP_DEFLATED) as z:
 for p in included+[manifest_path]:z.write(p,p.relative_to(root).as_posix())
with zipfile.ZipFile(archive_path) as z:assert z.testzip() is None
print(json.dumps({'status':state,'scoped_native_static':'PASS','scoped_remote_zip':'PASS','local_native_files':0,'manual_download_reply_assumed':False,'DIP_Motion_FEA':'NOT_EXECUTED','explanation':'docs/WHERE_THE_CODE_AND_RESULTS_ARE.txt','preparation_zip_checked':True},indent=2))
