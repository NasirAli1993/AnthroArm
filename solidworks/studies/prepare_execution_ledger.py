"""Prepare, but do not execute, a cloud SOLIDWORKS evidence ledger."""
from pathlib import Path
import hashlib
import json

ROOT = Path('D:/RoboticArm/solidworks')
OUT = ROOT/'studies'
manifest_path = ROOT/'transfer/assembly_manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
joint_path = OUT/'joint_register.json'
joints = json.loads(joint_path.read_text(encoding='utf-8'))['joints']

def pending():
    return {'status': 'NOT_EXECUTED', 'started_at': None, 'finished_at': None,
            'observed': None, 'passed': None, 'evidence': []}

def stage(id, priority, name, prerequisites, evidence, acceptance):
    return dict(id=id, priority=priority, name=name,
                prerequisites=prerequisites, required_evidence=evidence,
                acceptance=acceptance, **pending())

stages = [
    stage('P0', 0, 'Record trial capabilities and export a smoke-test native file',
      ['Official trial access'],
      ['actual product/version/edition shown', 'remaining session time and quota if displayed',
       'Motion study type menu and Simulation add-in availability', 'successful native test-file save/download and local path'],
      ['record capabilities without guessing', 'prove export/recovery before spending the trial on the full assembly']),
    stage('P1', 1, 'Static full-arm import and native checkpoint',
      ['P0 export verified'],
      ['import options and diagnostics', 'body/component count', 'known 300/250/40 mm joint spans',
       'full arm screenshot in SOLIDWORKS', 'downloaded native file and SHA256'],
      ['293 source solids accounted for; explain any import restructuring', 'units/scale correct within 0.1 mm import comparison',
       'no unresolved import errors', 'native geometry saved; does not count as articulated assembly']),
    stage('P2', 2, '28 rigid-link native parts and assembled home pose',
      ['P1 checkpoint'],
      ['28 native SLDPRT files', 'SLDASM with link-named components', 'transform/placement audit',
       'fixed base and remaining free component status', 'complete native dependency package downloaded'],
      ['all 28 links and 293 bodies accounted for', 'source mm transforms preserved', 'home pose matches source',
       'imported B-rep parts identified honestly; no native sketch-history claim']),
    stage('P3', 3, '27 revolute joints, limits and individual jogs',
      ['P2 native link assembly'],
      ['joint-by-joint mate/axis and angular-zero record', 'positive-jog direction evidence',
       'each measured actual joint angle', 'moving parent/child propagation', 'rebuild log',
       '27 intended free rotations audit before drive constraints'],
      ['all 27 joints recorded', 'no unintended translations/axis tilt', 'correct sign, limits and parent-child behavior',
       'no unresolved mate error; no unintentional locked rotation']),
    stage('P4', 4, 'Native Motion study and collision/clearance review',
      ['P3 joint audit', 'confirmed available study type'],
      ['saved native study type and timeline', '27 joint sweeps angle/time measurements', 'native recording',
       'interference pair/volume/pose report', 'minimum clearance evidence and exclusions'],
      ['label Animation/Basic Motion/Motion Analysis correctly', 'conservative schedules followed within 0.5 degrees',
       'no unexplained motion or interference', 'dynamic loads not asserted from Animation or unverified masses']),
    stage('P5', 5, 'Separate tendon-finger fit study',
      ['native starter-finger import', 'available trial time after core full-arm checkpoints'],
      ['three individual 0/5/10/15 degree hinge sweeps', '1 degree sample interference/clearance report',
       'pin, stop-tab, screw-head and retainer review', 'native file and recording'],
      ['no unintended contact within tested sweep', 'illustrative cord solids not reported as a transmission simulation',
       'physical fit and motor output-offset compatibility remain unverified']),
    stage('P6', 6, 'Quantitative dynamics and structural analysis gate',
      ['P4 geometry/motion issues resolved', 'licensed feature availability', 'documented physical inputs and criteria'],
      ['mass/material/drive/load/support sources', 'solver settings/logs', 'charts', 'mesh convergence and reaction checks for FEA'],
      ['execute only after gates filled', 'otherwise record NOT_EXECUTED with missing inputs',
       'no inferred torque/payload/strength qualification from appearance or solver availability']),
]

ledger = {
    'schema': 'anthro27.solidworks-native-results-ledger.v1',
    'prepared_date': '2026-10-05',
    'purpose': 'Execution checklist and empty evidence ledger; no native SOLIDWORKS result exists in this ledger yet.',
    'user_authorization': {'official_free_online_trial': True, 'upload_project_CAD': True,
                           'account_purchase': False, 'basis': 'parent relayed explicit current user approval'},
    'storage': {'local_root': 'D:/RoboticArm/solidworks',
                'suggested_download_checkpoint_root': 'D:/RoboticArm/solidworks/project/native_cloud',
                'suggested_evidence_root': 'D:/RoboticArm/solidworks/results/native_cloud',
                'note': 'Native cloud working files are remote until downloaded. Record actual destination; never describe remote workspace as D:.'},
    'trial': {'access_status': 'UNKNOWN_TO_THIS_LEDGER', 'product': None, 'version': None,
              'edition': None, 'expires_at': None, 'time_remaining_displayed': None,
              'file_upload_limit': None, 'file_download_supported': None,
              'motion_types_available': None, 'simulation_addins_available': None,
              'api_or_macro_access_available': None, 'evidence': []},
    'input_sources': [
        {'path': str(manifest_path), 'sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest()},
        {'path': str(joint_path), 'sha256': hashlib.sha256(joint_path.read_bytes()).hexdigest()},
    ],
    'completion_rule': 'Change a state only after actual native action and measured evidence. An upload/import, generated schedule, FreeCAD check or MuJoCo result is not native SOLIDWORKS execution.',
    'core_deliverable': {'expected_rigid_link_parts': 28, 'expected_source_solid_bodies': 293,
                         'expected_revolute_joints': 27, 'expected_arm_joints': 7, 'expected_hand_joints': 20,
                         'full_native_assembly_completed': False, 'native_motion_study_completed': False},
    'stages': stages,
    'link_imports': [dict(link=l['name'], source_step='D:/RoboticArm/solidworks/transfer/'+l['step_file'],
                           expected_solid_count=l['body_count'], native_part_path=None,
                           native_component_name=None, native_solid_count=None, import_diagnostics=None,
                           native_file_sha256=None, **pending()) for l in manifest['links']],
    'joint_tests': [dict(joint=j['name'], parent_link=j['parent_link'], child_link=j['child_link'],
                         axis_local=j['axis_in_local_joint_frame'], expected_limit_deg=j['limits_deg'],
                         expected_home_deg=j['home_deg'], sweep_time_s=j['sweep_times_s'],
                         sweep_target_deg=j['conservative_sweep_deg'], mate_names=[], measured_zero_definition=None,
                         actual_limit_deg=None, positive_jog_passed=None, measured_angles_deg=[],
                         maximum_schedule_error_deg=None, unintended_translation_mm=None,
                         interference_findings=[], **pending()) for j in joints],
    'fea_gate': {'status': 'MISSING_INPUTS_NOT_EXECUTED', 'physical_material_properties': None,
                 'manufacturing_process_and_orientation': None, 'actual_load_bearing_geometry': None,
                 'payload_and_center_of_mass': None, 'fingertip_force': None,
                 'cord_tension_and_pretension': None, 'support_and_contact_definition': None,
                 'required_safety_factor': None, 'allowable_deflection': None,
                 'duty_cycle_and_fatigue_target': None, 'linear_assumptions_review': None,
                 'entitlement': None, 'solver_run': False, 'structural_pass': None,
                 'note': 'SimulationXpress supports a single solid body, not this full arm assembly. Numerical settings are not material/load approval.'},
    'quantitative_motion_gate': {'status': 'MISSING_INPUTS_NOT_EXECUTED',
                                 'motion_analysis_available': None, 'physical_mass_inertia_sources': None,
                                 'actuator_gear_ratio_efficiency_ratings': None,
                                 'friction_contact_model': None, 'duty_cycle': None,
                                 'physical_motor_capacity_pass': None},
    'camera_control': {'native_bridge_implemented': False, 'native_live_vision_test_executed': False,
                       'note': 'Joint-trajectory replay is not native autonomous camera control.'},
    'downloaded_artifacts': [], 'session_events': [],
}
assert len(ledger['link_imports']) == 28
assert sum(x['expected_solid_count'] for x in ledger['link_imports']) == 293
assert len(ledger['joint_tests']) == 27
(OUT/'native_results_ledger.json').write_text(json.dumps(ledger, indent=2), encoding='utf-8')

checklist = '''NATIVE SOLIDWORKS CLOUD EXECUTION CHECKLIST
Prepared 2026-10-05 | ALL NATIVE ACTIONS IN THIS CHECKLIST: NOT EXECUTED

The user has approved the official free online trial and uploading this CAD.
This checklist does not assert that the trial opened, accepted uploads, or ran.
Its state is an empty ledger for the operator to fill using actual evidence.
Local downloads/evidence belong under D:\\RoboticArm\\solidworks. The trial's
remote working files are cloud files, not local D: files until downloaded.

PRIORITY ORDER FOR UNKNOWN TRIAL LIMITS
P0  Record product/version, time/quotas, native save/export ability, Motion study
    menu, Simulation add-ins and API/macro availability. Export a small native
    smoke-test file first; verify it is recoverable on D:. Do not spend the
    whole trial on a model that cannot be downloaded.
P1  Import transfer/full_arm_home_reference.step. Check Import Diagnostics,
    293 solids and known 300/250/40 mm joint spans. Capture a SOLIDWORKS view.
    Save/export the static native checkpoint. This is not an articulated arm.
P2  Import the 28 files in transfer/links as 28 rigid multibody SLDPRT parts.
    Preserve origins; create an SLDASM. Apply manifest home transforms in mm,
    fix only base_link and verify the silhouette. Download the assembly with
    ALL native part dependencies at this milestone.
P3  Recreate 27 revolute joints from transfer/joint_schedule.csv and the manifest.
    Define angular zero and signs; audit +5 degree jogs where limits allow.
    Confirm limits, one free rotation per joint and no unintended translation.
    Inspect shoulder carriers and thumb frame carefully; do not guess axes from
    decorative shell faces. Record each joint in native_results_ledger.json.
P4  Create a native Motion study using the ACTUAL available study type. Run all
    27 conservative per-joint schedules in joint_register.json, holding the
    other joints at home. Save measured angles, warnings, timeline and recording.
    Compare scheduled/actual angles within 0.5 degrees for this import check.
    Inspect interference at endpoints and <=5-degree intermediate samples;
    refine around suspected contact. Record each excluded pair and why.
P5  If trial time permits, import the separate tendon finger. Test each hinge
    0/5/10/15 degrees independently, sampling at 1 degree. Check pins, stop tabs
    and retainer envelopes. Straight cord solids are illustrations, not tendons.
P6  Quantitative dynamics / FEA only after the prerequisite gates below pass.

CHECKPOINT POLICY
Save native parts + assembly + study after P1, P2, P3 and P4. Download dependents
with the assembly; a lone SLDASM may lose its referenced parts. Record file paths,
sizes and SHA256 on D:. Reopen a downloaded checkpoint if the trial allows.
Capture progress before a displayed timeout. Prioritize the native full arm and
27-joint study over cosmetic rendering or optional FEA. If a capability is absent,
record the actual limitation; never relabel another tool's results as SOLIDWORKS.

REQUIRED EVIDENCE FOR EACH JOINT
Mate/axis names; angular-zero definition; source and measured limits; observed
positive direction; measured angles for the five 8-second schedule points;
parent-child movement; solver warnings; interference findings; screenshot/curve
or recording path. If the interface cannot export a curve, record how angles
were measured and the limitation. Do not substitute target values for readings.

DYNAMICS AND FEA GATES
Animation proves only prescribed geometry/mate motion. Basic Motion is an
approximate preview. Required-torque/reactive-force reporting needs Motion
Analysis and defensible mass, inertia, friction, contact and drive inputs.
Prescribed motion does not prove that a physical motor can achieve it.

Before structural FEA: select the actual load-bearing part, material/process,
print orientation if applicable, pin/support/contact model, tendon load or
payload/COM, safety factor, allowed deflection and duty/fatigue criteria. These
inputs remain missing. Decorative shells and conceptual actuator envelopes
do not establish the arm's strength. SimulationXpress can analyze one solid
body, not the assembled arm. Confirm the available product before proceeding.
If eligible, keep mesh refinement, equilibrium and assumption checks with the
result. Three mesh levels and <5% last-refinement change are proposed numerical
review targets; they do not replace physical design criteria.

TRUTHFUL COMPLETION LABELS
Uploaded -> files accepted only.
Native static import -> geometry saved in native format; no joint movement.
Native articulated assembly -> 28 rigid links and 27 audited revolute joints.
Native motion demonstration -> actual saved study and measured motion evidence.
Native quantitative dynamics / FEA -> actual executed solver plus input sources.
Physical prototype validated -> cannot be concluded from any of the above alone.

The existing MuJoCo camera/controller result stays labeled MuJoCo. A replay in
SOLIDWORKS is not live vision. No SOLIDWORKS camera-control bridge is implemented.

FILES
native_results_ledger.json: 7 priority stages, 28 part imports, 27 joint tests,
empty evidence fields and dynamics/FEA gates. All results are null / NOT_EXECUTED.
STUDY_PLAN.txt: detailed test procedure and official reference URLs.
joint_register.json: source axes, limits, homes and conservative motion schedules.
study_definitions.json: the six underlying study specifications.

Update state only after the action occurred and evidence was recorded. Preserve
unknowns and failures explicitly. This preparation script never calls SOLIDWORKS.
'''
(OUT/'execution_checklist.txt').write_text(checklist, encoding='utf-8')
print(json.dumps({'files_written': ['execution_checklist.txt', 'native_results_ledger.json'],
                  'priority_stages': len(stages), 'links': 28, 'source_solids': 293,
                  'joints': 27, 'solidworks_executed': False}))
