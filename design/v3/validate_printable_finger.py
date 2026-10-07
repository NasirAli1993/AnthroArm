from pathlib import Path
import json,math,traceback
import FreeCAD as App
import Part,Mesh
ROOT=Path(r'D:\RoboticArm');OUT=ROOT/'design'/'v3'/'printable_finger';RESULTS=ROOT/'results'/'v3'
try:
 manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
 doc=App.openDocument(str(OUT/'TendonFinger_FitTest.FCStd'))
 rows=[]
 for p in manifest['parts']:
  o=doc.getObject(p['name'])
  row={'name':p['name'],'native_valid':o.Shape.isValid(),'single_solid':len(o.Shape.Solids)==1,'positive_volume':o.Shape.Volume>0,'explanation_persisted':bool(o.Explanation)}
  if p['printable']:
   mesh=Mesh.Mesh(str(OUT/p['file']));row.update(stl_closed=mesh.isSolid(),stl_facets=mesh.CountFacets)
  rows.append(row)
 step=Part.read(str(OUT/'TendonFinger_FitTest.step'))
 sweep=[]
 for angle in [0,10,20]:
  shapes={o.Name:o.Shape.copy() for o in doc.Objects if getattr(o,'Printable',False)}
  pose=App.Placement(App.Vector(0,0,35),App.Rotation(App.Vector(0,1,0),angle))
  for name,L in [('ProximalPhalanx',40),('MiddlePhalanx',24),('DistalPhalanx',18)]:
   s=shapes[name];s.Placement=pose;shapes[name]=s
   pose=pose.multiply(App.Placement(App.Vector(0,0,L),App.Rotation(App.Vector(0,1,0),angle)))
  collisions=[];names=list(shapes)
  for i,a in enumerate(names):
   for b in names[i+1:]:
    common=shapes[a].common(shapes[b]);vol=common.Volume
    if vol>.05:collisions.append({'a':a,'b':b,'overlap_mm3':vol})
  sweep.append({'each_joint_angle_deg':angle,'hard_intersections':collisions})
 topology=all(r['native_valid'] and r['single_solid'] and r['positive_volume'] and r['explanation_persisted'] and r.get('stl_closed',True) for r in rows)
 report={'topology_passed':topology,'step_valid':step.isValid(),'step_solid_count':len(step.Solids),'native_component_count':len(rows),'printable_count':manifest['printable_count'],'no_hard_intersections_in_checked_poses':all(not r['hard_intersections'] for r in sweep),'checked_poses':sweep,'parts':rows,'scope':'Geometry/export validity and static Boolean overlap checks at 0,10,20 degrees per hinge. Excludes print tolerances, retained hardware, tendon wrap/contact forces, motor fit, loads and powered behavior.'}
 (RESULTS/'printable_finger_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print('PRINTABLE_FINGER_VALIDATION',topology,report['no_hard_intersections_in_checked_poses'])
except Exception:
 (RESULTS/'printable_finger_validation_error.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
