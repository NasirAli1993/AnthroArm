"""Read-only STEP bore preflight in FreeCAD; NOT a SOLIDWORKS test."""
from pathlib import Path
import json
import FreeCAD as App
import Part

root = Path(r'D:\RoboticArm\solidworks')
report = {'scope': 'FREECAD_SOURCE_STEP_GEOMETRY_ONLY',
          'native_solidworks_status': 'NOT_EXECUTED', 'links': []}
for name, expected in [('index_intermediate', 12), ('index_distal', 10)]:
    path = root / 'transfer' / 'links' / (name + '.step')
    shape = Part.Shape()
    shape.read(str(path))
    candidates = []
    for n, face in enumerate(shape.Faces, 1):
        surface = face.Surface
        if type(surface).__name__ != 'Cylinder':
            continue
        axis = surface.Axis
        center = surface.Center
        if (abs(abs(axis.y)-1) < 1e-8 and abs(axis.x) < 1e-8
                and abs(axis.z) < 1e-8 and abs(center.x) < 1e-6
                and abs(center.z) < 1e-6 and abs(surface.Radius-1.2) < 1e-6):
            candidates.append({'face_index_1based': n, 'radius_mm': surface.Radius,
                               'axis': list(axis), 'center_mm': list(center),
                               'area_mm2': face.Area, 'area_m2': face.Area * 1e-6})
    record = {'name': name, 'source': str(path), 'solids': len(shape.Solids),
              'expected_solids': expected, 'is_valid': shape.isValid(),
              'largest_dimension_mm': max(shape.BoundBox.XLength,
                                           shape.BoundBox.YLength,
                                           shape.BoundBox.ZLength),
              'root_Y_bore_2p4mm_candidates': candidates}
    report['links'].append(record)
    assert len(shape.Solids) == expected, record
    assert candidates, record
    assert max(x['area_m2'] for x in candidates) > 1e-5, record
report['status'] = 'SOURCE_GEOMETRY_PASSED_NO_NATIVE_EXECUTION'
out = root / 'studies' / 'dip_source_bore_audit.json'
out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(str(out))
