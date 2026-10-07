"""Round-trip topology, metadata and metre-scale STL validation in FreeCADCmd."""
from pathlib import Path
import json, traceback, struct, math, re
import FreeCAD as App
import Part, Mesh, MeshPart
ROOT=Path(r'D:\RoboticArm')
try:
    m=json.loads((ROOT/'design'/'v3'/'anatomical_manifest.json').read_text(encoding='utf-8'))
    doc=App.openDocument(str(ROOT/'design'/'v3'/'AnthroArm27_ReferenceV3.FCStd'))
    named={o.Name:o for o in doc.Objects}
    spec=json.loads((ROOT/'design'/'v3'/'robot_spec.json').read_text(encoding='utf-8'))
    links={l['name']:l for l in spec['links']}; placements={}
    def frame(name):
        if name in placements:return placements[name]
        l=links[name];V=App.Vector
        parent=frame(l['parent']) if l.get('parent') else App.Placement()
        r,p,y=[math.degrees(v) for v in l['origin_rpy']]
        rot=App.Rotation(V(0,0,1),y).multiply(App.Rotation(V(0,1,0),p)).multiply(App.Rotation(V(1,0,0),r))
        j=l.get('joint') or {};rot=rot.multiply(App.Rotation(V(*j.get('axis',[0,0,1])),math.degrees(j.get('home',0))))
        placements[name]=parent.multiply(App.Placement(V(*[v*1000 for v in l['origin_xyz']]),rot))
        return placements[name]
    rows=[]
    for c in m['components']:
        o=named[c.get('cad_name',re.sub(r'[^A-Za-z0-9_]','_',c['name']))]
        path=ROOT/'design'/'v3'/c['file']
        mesh=Mesh.Mesh(str(path))
        data=path.read_bytes()
        facets=struct.unpack('<I',data[80:84])[0]
        expected_size=84+50*facets
        b=mesh.BoundBox
        actual=[b.XMin,b.YMin,b.ZMin,b.XMax,b.YMax,b.ZMax]
        maxerr=max(abs(a-b) for a,b in zip(actual,c['bounds_m']))
        mat=App.Matrix();mat.A11=1000;mat.A22=1000;mat.A33=1000
        world_mesh=Mesh.Mesh(mesh);world_mesh.transform(mat);world_mesh.transform(frame(c['link']).toMatrix())
        # OCC's rotated B-spline control-hull bound is conservative. Compare the
        # tessellated native surface with the exported surface at equal deflection.
        native_mesh=MeshPart.meshFromShape(Shape=o.Shape,LinearDeflection=.07,AngularDeflection=.13,Relative=False)
        wb=world_mesh.BoundBox;nb=native_mesh.BoundBox
        keys=['XMin','YMin','ZMin','XMax','YMax','ZMax']
        worlderr=max(abs(getattr(wb,k)-getattr(nb,k)) for k in keys)
        rows.append(dict(name=c['name'],solid_valid=o.Shape.isValid(),solid_count=len(o.Shape.Solids),positive_volume=o.Shape.Volume>0,explanation_persisted=bool(o.Explanation),joint_metadata_persisted='JointName' in o.PropertiesList,binary_stl=len(data)==expected_size,facets=facets,mesh_closed=bool(mesh.isSolid()),max_bound_error_m=maxerr,metre_scale_correct=maxerr<.00025,native_vs_mesh_world_bound_error_mm=worlderr,native_mesh_alignment_correct=worlderr<.3))
    step=Part.read(str(ROOT/'design'/'v3'/'AnthroArm27_ReferenceV3.step'))
    all_native=all(r['solid_valid'] and r['solid_count']==1 and r['positive_volume'] and r['explanation_persisted'] and r['joint_metadata_persisted'] for r in rows)
    all_mesh=all(r['binary_stl'] and r['mesh_closed'] and r['metre_scale_correct'] and r['facets']>0 and r['native_mesh_alignment_correct'] for r in rows)
    report=dict(passed=all_native and all_mesh and step.isValid() and len(step.Solids)==m['count'],component_count=m['count'],native_freecad_valid=all_native,mesh_exports_valid=all_mesh,step_valid=step.isValid(),step_solid_count=len(step.Solids),scope='Single-solid topology; FCStd/STEP reopen; embedded component explanations; binary STL closure and exact metre conversion. Excludes hardware engineering validation and assembly interference.',components=rows)
    (ROOT/'results'/'v3'/'anatomical_cad_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('ANATOMICAL_CAD_VALIDATION',report['passed'],m['count'])
except Exception:
    (ROOT/'results'/'v3'/'anatomical_cad_validation_error.txt').write_text(traceback.format_exc(),encoding='utf-8')
    raise
