"""Numerical source-frame audit; never calls SOLIDWORKS or edits result ledger."""
from pathlib import Path
import hashlib
import json
import math
import numpy as np

ROOT = Path('D:/RoboticArm')
OUT = ROOT/'solidworks/studies'
manifest_path = ROOT/'solidworks/transfer/assembly_manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
spec = json.loads((ROOT/'design/v3/robot_spec.json').read_text(encoding='utf-8'))
ledger_path = OUT/'native_results_ledger.json'
ledger_before = hashlib.sha256(ledger_path.read_bytes()).hexdigest()

def rot(axis, angle):
    v = np.asarray(axis, dtype=float)
    v /= np.linalg.norm(v)
    x,y,z = v
    k = np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    return np.eye(3) + math.sin(angle)*k + (1-math.cos(angle))*(k@k)

frames = {}
source = {x['name']: x for x in spec['links']}
def frame(name):
    if name in frames:
        return frames[name]
    link = source[name]
    parent = frame(link['parent']) if link['parent'] else np.eye(4)
    r,p,y = link['origin_rpy']
    local = np.eye(4)
    local[:3,:3] = rot([0,0,1],y) @ rot([0,1,0],p) @ rot([1,0,0],r)
    local[:3,3] = np.asarray(link['origin_xyz'])*1000
    if link['joint']:
        local[:3,:3] = local[:3,:3] @ rot(link['joint']['axis'],link['joint']['home'])
    frames[name] = parent@local
    return frames[name]

rows = []
points_mm = np.array([[0,0,0],[10,0,0],[0,10,0],[0,0,10]],dtype=float)
for link in manifest['links']:
    name = link['name']
    m = np.asarray(link['world_from_link_home_matrix_mm'],dtype=float)
    r = m[:3,:3]
    expected = frame(name)
    array = list(r.T.reshape(-1)) + list(m[:3,3]/1000) + [1.,0.,0.,0.]
    array_rotation = np.array(array[:9]).reshape(3,3)
    sw_row_vector_predictions_m = (points_mm/1000)@array_rotation + np.array(array[9:12])
    column_vector_predictions_m = (r@points_mm.T).T/1000 + m[:3,3]/1000
    rotation_error = float(np.max(np.abs(r.T@r-np.eye(3))))
    frame_error_mm = float(np.max(np.abs(m-expected)))
    point_error_m = float(np.max(np.abs(sw_row_vector_predictions_m-column_vector_predictions_m)))
    rows.append({'link':name,'source_frame_max_element_error':frame_error_mm,
                 'orthonormal_error':rotation_error,'determinant':float(np.linalg.det(r)),
                 'row_column_point_equivalence_error_m':point_error_m,
                 'sw_array_data_derived_NOT_NATIVE_TESTED':array,
                 'verification_local_points_mm':points_mm.tolist(),
                 'expected_world_points_m':column_vector_predictions_m.tolist(),
                 'numerical_pass':frame_error_mm<1e-9 and rotation_error<1e-10 and abs(np.linalg.det(r)-1)<1e-10 and point_error_m<1e-12})
ledger_after = hashlib.sha256(ledger_path.read_bytes()).hexdigest()
assert ledger_before == ledger_after
report = {'status':'SOURCE NUMERICAL AUDIT ONLY; SOLIDWORKS API NOT EXECUTED',
          'checked_date':'2026-10-06',
          'manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
          'native_results_ledger_preserved':True,'native_results_ledger_sha256':ledger_after,
          'all_source_numerical_checks_passed':all(row['numerical_pass'] for row in rows),
          'links_checked':len(rows),
          'mapping':'ArrayData = [M00,M10,M20,M01,M11,M21,M02,M12,M22,M03/1000,M13/1000,M23/1000,1,0,0,0]',
          'important':'Array interpretation is derived from official MathTransform axis storage. Confirm by MathPoint.MultiplyTransform in the actual session before relying on it. Do not call the numerical pass a native import test.',
          'source_composition':'Rz(yaw) @ Ry(pitch) @ Rx(roll); parent-world @ origin-local @ joint-axis-rotation(home). All manifest translations mm; API translations m.',
          'pitfalls':['Do not flatten the 4x4 source matrix directly into ArrayData.',
                      'Do not forget rotation transpose or mm-to-m translation conversion.',
                      'Keep scale=1; do not scale already imported STEP geometry.',
                      'Component.Transform2 is relative to assembly root, not immediate parent.',
                      'Use local link STEP with home world matrix; do not transform full_arm_home_reference.step again.',
                      'The shoulder root is already [0,0,1080] mm, rotated pi about X.',
                      'Thumb metacarpal origin includes -0.75 rad roll; axis is in joint-local coordinates.',
                      'Placement through Transform2 is not mates or a Motion study; rebuild may move constrained components.',
                      'PresentationTransform changes display only.'],
          'links':rows}
(OUT/'coordinate_transform_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:report[k] for k in ['status','all_source_numerical_checks_passed','links_checked','native_results_ledger_preserved']}))
