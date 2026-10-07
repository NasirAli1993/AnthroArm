"""Export existing V3 solids as local-coordinate rigid-link STEP files.

Run only inside the existing portable FreeCADCmd runtime. No source CAD is modified.
The resulting neutral geometry has no SOLIDWORKS feature history, mates or studies.
"""
from pathlib import Path
import csv, hashlib, json, math, re, shutil, traceback
import FreeCAD as App
import Part, Import

ROOT = Path(r'D:\RoboticArm')
SOURCE = ROOT / 'design' / 'v3'
OUT = ROOT / 'solidworks' / 'transfer'
LINK_DIR = OUT / 'links'
LOG = ROOT / 'solidworks' / 'logs'
for folder in (OUT, LINK_DIR, LOG):
    folder.mkdir(parents=True, exist_ok=True)

def dump(path, data):
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')

def bounds(shape):
    b = shape.BoundBox
    return [getattr(b, key) for key in ('XMin','YMin','ZMin','XMax','YMax','ZMax')]

def matrix(placement):
    m = placement.toMatrix()
    return [[getattr(m, 'A%d%d' % (i,j)) for j in range(1,5)] for i in range(1,5)]

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def centroid(shape):
    total = sum(s.Volume for s in shape.Solids)
    center = App.Vector()
    for solid in shape.Solids:
        center += solid.CenterOfMass * (solid.Volume / total)
    return center

try:
    spec = json.loads((SOURCE / 'robot_spec.json').read_text(encoding='utf-8'))
    source_manifest = json.loads((SOURCE / 'anatomical_manifest.json').read_text(encoding='utf-8'))
    links = {l['name']: l for l in spec['links']}
    source_doc = App.openDocument(str(SOURCE / 'AnthroArm27_ReferenceV3.FCStd'))
    objects = {o.Name:o for o in source_doc.Objects}
    frames = {}
    V = App.Vector

    def origin_placement(link):
        r,p,y = [math.degrees(v) for v in link.get('origin_rpy',[0,0,0])]
        rot = App.Rotation(V(0,0,1),y).multiply(App.Rotation(V(0,1,0),p)).multiply(App.Rotation(V(1,0,0),r))
        return App.Placement(V(*[v*1000 for v in link.get('origin_xyz',[0,0,0])]),rot)

    def frame(name, home=True):
        key = (name,home)
        if key in frames:
            return frames[key]
        link = links[name]
        parent = frame(link['parent'],home) if link.get('parent') else App.Placement()
        local = origin_placement(link)
        j = link.get('joint') or {}
        if home and j:
            local = local.multiply(App.Placement(V(),App.Rotation(V(*j['axis']),math.degrees(j.get('home',0)))))
        frames[key] = parent.multiply(local)
        return frames[key]

    # AP214 retains named components and appearances; solids remain exact B-reps.
    App.ParamGet('User parameter:BaseApp/Preferences/Mod/Part/STEP').SetString('Scheme','AP214IS')
    rows, components, checks = [], [], []
    for link in spec['links']:
        name = link['name']
        members = [c for c in source_manifest['components'] if c['link'] == name]
        if not members:
            raise RuntimeError('Rigid link has no CAD bodies: '+name)
        export_doc = App.newDocument('Export_'+name)
        export_objects = []
        original_world = []
        inverse = frame(name).inverse()
        for component in members:
            source = objects[component.get('cad_name',re.sub(r'[^A-Za-z0-9_]','_',component['name']))]
            shape = source.Shape.copy()
            original_world.append(shape.copy())
            # Source shapes carry the home-pose link placement. Undo that transform.
            shape.Placement = inverse.multiply(shape.Placement)
            target = export_doc.addObject('Part::Feature',component['name'])
            target.Label = component['name']
            target.Shape = shape
            export_objects.append(target)
            components.append(dict(name=component['name'],link=name,step_file='links/'+name+'.step',label=component['label'],category=component['category'],explanation=component['explanation'],volume_mm3=shape.Volume))
        export_doc.recompute()
        export_path = LINK_DIR / (name+'.step')
        Import.export(export_objects,str(export_path))
        expected = Part.makeCompound([o.Shape for o in export_objects])
        roundtrip = Part.read(str(export_path))
        volume_error = abs(roundtrip.Volume - expected.Volume)/max(expected.Volume,1e-12)
        bound_error = max(abs(a-b) for a,b in zip(bounds(roundtrip),bounds(expected)))
        world_copy = roundtrip.copy()
        world_copy.Placement = frame(name).multiply(world_copy.Placement)
        original = Part.makeCompound(original_world)
        center_error = (centroid(world_copy)-centroid(original)).Length
        check = dict(link=name,source_solid_count=len(members),reimport_solid_count=len(roundtrip.Solids),valid=bool(roundtrip.isValid()),positive_volume=roundtrip.Volume>0,volume_relative_error=volume_error,max_local_bound_error_mm=bound_error,reconstructed_world_centroid_error_mm=center_error,sha256=sha256(export_path))
        # OCC re-integrates trimmed B-spline volumes after STEP import; sub-ppm
        # integration differences do not imply changed dimensions. Use 10 ppm,
        # while also checking topology, bounds and reconstructed centroid.
        check['passed'] = check['valid'] and check['positive_volume'] and check['reimport_solid_count']==len(members) and volume_error<1e-5 and bound_error<0.01 and center_error<0.01
        checks.append(check)
        j = link.get('joint')
        origin = origin_placement(link)
        row = dict(name=name,parent=link.get('parent'),step_file='links/'+name+'.step',body_names=[c['name'] for c in members],body_count=len(members),origin_xyz_mm=[v*1000 for v in link['origin_xyz']],origin_rpy_deg=[math.degrees(v) for v in link.get('origin_rpy',[0,0,0])],parent_to_child_zero_matrix_mm=matrix(origin),world_from_link_home_matrix_mm=matrix(frame(name)),world_from_link_zero_matrix_mm=matrix(frame(name,False)))
        if j:
            # Axis is expressed in the joint/child frame before the joint rotates.
            axis = V(*j['axis'])
            axis_parent = origin.Rotation.multVec(axis)
            row['joint'] = dict(name=j['name'],label=j['label'],type='revolute',group=j['group'],axis_joint_local=list(j['axis']),axis_parent=[axis_parent.x,axis_parent.y,axis_parent.z],limits_rad=j['range'],limits_deg=[math.degrees(v) for v in j['range']],home_rad=j.get('home',0),home_deg=math.degrees(j.get('home',0)),simulation_effort_limit_Nm=j['effort'],simulation_velocity_limit_rad_s=j['velocity'],hardware_rating_validated=False)
        else:
            row['joint'] = None
        rows.append(row)
        App.closeDocument(export_doc.Name)
        print('EXPORTED',name,len(members),check['passed'])

    # This is the already assembled, visual reference in home pose, not a mated assembly.
    assembled = OUT / 'full_arm_home_reference.step'
    shutil.copy2(SOURCE / 'AnthroArm27_ReferenceV3.step',assembled)
    assembled_shape = Part.read(str(assembled))
    report = dict(passed=all(c['passed'] for c in checks) and assembled_shape.isValid() and len(assembled_shape.Solids)==source_manifest['count'],scope='FreeCAD/OpenCascade export and STEP reimport only. No SOLIDWORKS import, mates, Motion Analysis, FEA, hardware or collision validation has run.',criteria=dict(volume_relative_tolerance=1e-5,local_bound_tolerance_mm=0.01,world_centroid_tolerance_mm=0.01,volume_note='Trimmed B-spline volume integration is recomputed after STEP translation; tolerance is 10 ppm. Solid count, validity and dimensions checked independently.'),export_units='mm',rigid_links=len(rows),revolute_joints=sum(r['joint'] is not None for r in rows),component_solids=len(components),reference_step_solid_count=len(assembled_shape.Solids),reference_step_valid=bool(assembled_shape.isValid()),source_fcstd_sha256=sha256(SOURCE/'AnthroArm27_ReferenceV3.FCStd'),source_spec_sha256=sha256(SOURCE/'robot_spec.json'),links=checks)
    dump(OUT/'transfer_validation.json',report)
    (LOG/'transfer_error.txt').unlink(missing_ok=True)
    dump(OUT/'assembly_manifest.json',dict(schema='anthro27.solidworks-transfer.v1',length_units='mm',angle_units='explicit rad and deg',matrix_convention='4x4 row-major, column-vector: p_parent=R*p_child+t; translations are mm. Apply parent_to_child_zero then local joint-axis rotation. Home-world matrix includes home rotations.',geometry='28 rigid links with 293 named solid bodies in local frames. Imported B-rep geometry; no native SOLIDWORKS sketches/features/mates.',status='SOLIDWORKS validation pending licensed installation.',root_world_origin_mm=[0,0,1080],coordinate_convention=spec['coordinate_convention'],links=rows))
    with (OUT/'component_inventory.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=list(components[0]));writer.writeheader();writer.writerows(components)
    with (OUT/'joint_schedule.csv').open('w',newline='',encoding='utf-8-sig') as f:
        fields=['joint','parent','child','group','axis_joint_x','axis_joint_y','axis_joint_z','origin_parent_x_mm','origin_parent_y_mm','origin_parent_z_mm','origin_roll_deg','origin_pitch_deg','origin_yaw_deg','minimum_deg','maximum_deg','home_deg','simulation_effort_limit_Nm','hardware_rating_validated']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for row in rows:
            j=row['joint']
            if not j:continue
            values=[j['name'],row['parent'],row['name'],j['group'],*j['axis_joint_local'],*row['origin_xyz_mm'],*row['origin_rpy_deg'],*j['limits_deg'],j['home_deg'],j['simulation_effort_limit_Nm'],False]
            writer.writerow(dict(zip(fields,values)))
    App.closeDocument(source_doc.Name)
    print('TRANSFER_VALIDATION',report['passed'],len(rows),len(components))
except Exception:
    (LOG/'transfer_error.txt').write_text(traceback.format_exc(),encoding='utf-8')
    raise
