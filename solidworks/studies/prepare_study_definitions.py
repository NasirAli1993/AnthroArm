"""Build an UNEXECUTED study handoff from the existing robot definition.

This uses only the standard library. It does not start or call SOLIDWORKS.
"""
from pathlib import Path
import hashlib
import json
import math

ROOT = Path('D:/RoboticArm')
OUT = ROOT / 'solidworks/studies'
source = ROOT / 'design/v3/robot_spec.json'
spec = json.loads(source.read_text(encoding='utf-8'))
rows = []
for link in spec['links']:
    joint = link.get('joint')
    if not joint:
        continue
    lo, hi = joint['range']
    home = joint['home']
    excursion = .15 * (hi - lo)
    low, high = max(lo, home - excursion), min(hi, home + excursion)
    rows.append({
        'name': joint['name'], 'label': joint['label'], 'group': joint['group'],
        'parent_link': link['parent'], 'child_link': link['name'],
        'origin_xyz_m': link['origin_xyz'], 'origin_rpy_rad': link['origin_rpy'],
        'axis_in_local_joint_frame': joint['axis'],
        'limits_rad': [lo, hi],
        'limits_deg': [math.degrees(lo), math.degrees(hi)],
        'home_rad': home, 'home_deg': math.degrees(home),
        'mate_type': 'revolute; axial location plus one remaining rotation; limit-angle mate',
        'sign_verification': 'PENDING +5 degree comparison with source local axis',
        'conservative_sweep_rad': [home, low, home, high, home],
        'conservative_sweep_deg': [math.degrees(q) for q in [home, low, home, high, home]],
        'sweep_times_s': [0, 2, 4, 6, 8],
        'all_other_joints': 'hold their source home; document any clearance-driven exception',
        'status': 'UNEXECUTED', 'actual_result': None,
    })
assert len(rows) == 27
assert len({r['name'] for r in rows}) == 27
register = {
    'status': 'UNEXECUTED - no SOLIDWORKS execution or native study creation',
    'source': str(source), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'coordinate_convention': spec['coordinate_convention'],
    'root_frame': {'xyz_m': [0, 0, 1.08], 'rpy_rad': [math.pi, 0, 0]},
    'arm_dof': 7, 'hand_dof': 20,
    'warning': 'Conceptual effort, kp, kv, mass and inertia values are NOT verified physical motor/material ratings and are intentionally not imported into these study inputs.',
    'joints': rows,
}
(OUT/'joint_register.json').write_text(json.dumps(register, indent=2), encoding='utf-8')

def study(study_id, name, tool, inputs, outputs, criteria, settings=None):
    return {'id': study_id, 'name': name, 'status': 'UNEXECUTED',
            'native_solidworks_study_created': False, 'executed': False,
            'tool_required': tool, 'inputs_required': inputs,
            'planned_settings': settings or {}, 'outputs_required': outputs,
            'acceptance_criteria': criteria, 'actual_result': None,
            'passed': None}

definitions = {
  'project': 'AnthroArm-27 SOLIDWORKS study handoff',
  'prepared_date': '2026-10-05', 'status': 'ALL STUDIES UNEXECUTED',
  'purpose': 'Test specification only. JSON files do not import as native SOLIDWORKS studies.',
  'studies': [
    study('SW00', 'Import, units, axes and mate audit', 'SOLIDWORKS CAD assembly',
      ['STEP geometry', 'joint_register.json', 'link-to-component mapping', 'authorized SOLIDWORKS access'],
      ['scale measurements', 'mate tree', '27-axis sign audit', 'rebuild log'],
      ['300/250/40 mm arm spans within 0.1 mm import check', '27 intended rotations and no unintended translation with driving mates suppressed', 'no import or rebuild errors']),
    study('SW01', '27 individual conservative sweeps', 'Animation for kinematic review; Motion Analysis add-in for quantitative dynamics',
      ['SW00 passed', 'joint_register.json', 'mass/inertia/friction/drive evidence for dynamics only'],
      ['27 joint-angle curves', '27 videos', 'wrist and fingertip paths', 'solver warnings', 'required torque/reaction curves only if defensible dynamics inputs exist'],
      ['angle deviation <= 0.5 degrees from scheduled values', 'correct sign and continuous paths', 'no unexplained motion or solver error', 'motor torque/speed/payload acceptance remains pending actual drive ratings'],
      {'duration_per_joint_s': 8, 'smooth_transitions': True, 'complete_range_sweep': 'follow only after conservative sweep, with interference review'}),
    study('SW02', 'Shell clearance and interference', 'Interference Detection and Clearance Verification; collision/contact review for moving edges',
      ['SW00 passed', 'pose sample set', 'documented intended-contact/exclusion list', 'manufacturing-specific fit requirements'],
      ['component-pair intersections and volumes', 'minimum distances', 'joint poses', 'screenshots', 'reason for each excluded pair'],
      ['zero unexplained intersections', '>=0.5 mm nominal non-contacting shell gap as provisional design-review target', 'pin/pad/bearing fit criteria separately specified', 'sampling alone does not prove continuous clearance'],
      {'maximum_joint_sample_interval_deg': 5, 'refine_near_contact': True, 'nominal_shell_review_target_mm': .5}),
    study('SW03', 'Single tendon finger small-angle fit', 'SOLIDWORKS assembly and Animation; Motion Analysis for modeled tendon dynamics',
      ['TendonFinger_FitTest.step', 'physical servo/horn measurements before transmission fit claim', 'real cord routing/stiffness/pretension and elastic return for coupled study'],
      ['each hinge-angle plot', 'min-clearance table', 'stop-tab review', 'tendon travel', 'torque/tension only after transmission model exists'],
      ['free 0/5/10/15 degree individual hinge movement and return without unintended contact', 'retainer/screw envelopes clear', 'modeled transmission explains all 3 hinge motions', 'physical printed fit and stop angle remain unvalidated'],
      {'hinge_targets_deg': [0, 5, 10, 15, 0], 'sample_interval_deg': 1, 'subsequent_virtual_drum_range_deg': [-5, 5],
       'bore_diameter_mm': 2.3, 'reference_pin_diameter_mm': 2, 'clevis_gap_mm': 6,
       'tongue_width_mm': 5.2, 'tendon_channel_diameter_mm': 1.4, 'drum_radius_mm': 7,
       'warning': 'Straight cord reference solids do not implement a deformable tendon. PWM microseconds are not calibrated joint degrees.'}),
    study('SW04', 'Structural load cases and actuator sizing', 'Appropriate SOLIDWORKS Simulation; SimulationXpress only for a separate single solid-body linear first pass',
      ['final load-bearing geometry and supports', 'material/process/print-orientation properties', 'payload and COM', 'target fingertip force', 'tendon pretension and max tension', 'drive/transmission/thermal ratings', 'duty cycle and acceleration', 'allowable stress/deflection/fatigue criteria'],
      ['stress/strain/displacement fields with units', 'reaction forces', '3-level mesh-convergence report', 'load/support/material sources', 'peak/RMS/holding drive comparisons', 'solver warnings'],
      ['reaction balance <=1% proposed numerical review target', 'meaningful non-singular stress and deflection last-refinement change <5%', 'hardware-specific safety/deflection/fatigue criteria satisfied only after selected', 'correct linear/nonlinear/dynamic assumptions'],
      {'payload_kg': None, 'fingertip_force_N': None, 'cord_pretension_N': None, 'cord_max_tension_N': None,
       'material': None, 'allowable_deflection_mm': None, 'required_safety_factor': None,
       'mesh_levels_min': 3, 'physical_approval': 'NOT ESTABLISHED'}),
    study('SW05', 'Vision/controller replay boundary', 'Separate documented API/co-simulation bridge would be needed',
      ['authorized coupling design', 'time synchronization', 'camera/controller interface', 'collision policy'],
      ['coupling test log', 'latency/dropout metrics', 'closed-loop evidence'],
      ['trajectory playback labeled replay, never autonomous vision proof', 'existing MuJoCo camera results remain labeled MuJoCo results'],
      {'bridge_implemented': False, 'live_camera_solidworks_test': False}),
  ],
  'results_root': 'D:/RoboticArm/solidworks/results',
  'official_sources': [
    'https://help.solidworks.com/2026/english/SolidWorks/motionstudies/c_Introduction_to_Motion_Studies.htm?id=22.0',
    'https://help.solidworks.com/2026/english/SolidWorks/motionstudies/c_motion_study_elements_overview.htm?id=22.3.0',
    'https://blogs.solidworks.com/products/solidworks/solidworks-motion-analysis-use-cases/',
    'https://help.solidworks.com/2022/english/SolidWorks/cosmosxpresshelp/c_Overview_of_SOLIDWORKS_SimulationXpress.htm?id=32.0',
    'https://help.solidworks.com/2026/english/SolidWorks/sldworks/t_detecting_interferences.htm?id=7.14.3.0',
    'https://help.solidworks.com/2026/english/SolidWorks/sldworks/c_Clearance_Verification_SWassy.htm?id=7.14.0',
    'https://help.solidworks.com/2026/English/SolidWorks/Cworks/c_When_to_Use_Nonlinear_Analysis.htm',
  ],
}
(OUT/'study_definitions.json').write_text(json.dumps(definitions, indent=2), encoding='utf-8')
print(json.dumps({'specification_files_written': 2, 'joint_definitions': len(rows),
                  'study_definitions': len(definitions['studies']),
                  'solidworks_executed': False, 'status': 'UNEXECUTED'}))
