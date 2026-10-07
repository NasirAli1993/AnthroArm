"""Canonical V3 anatomical upper limb, 7 arm + 20 hand axes, SI units."""
from pathlib import Path
import sys,copy,json,math,xml.etree.ElementTree as ET
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'simulation'))
import generate_model as v2
DESIGN=ROOT/'design'/'v3';SIM=ROOT/'simulation'/'v3'

def make_spec():
    old=v2.make_spec();links=[]
    def link(name,parent,xyz=(0,0,0),rpy=(0,0,0),j=None,mass=.1,com=(0,0,0),dims=(.03,.03,.03),description=''):
        inertia=[mass*(dims[1]**2+dims[2]**2)/12,mass*(dims[0]**2+dims[2]**2)/12,mass*(dims[0]**2+dims[1]**2)/12]
        links.append(dict(name=name,parent=parent,origin_xyz=list(xyz),origin_rpy=list(rpy),joint=j,mass=mass,com=list(com),inertia=inertia,geoms=[],description=description))
    def j(name,label,axis,lo,hi,home,effort,kp,kv):
        result=v2.joint(name,label,'Arm',axis,lo,hi,home,effort,kp,kv);result['velocity']=1.25;return result
    link('base_link',None,(0,0,1.08),(math.pi,0,0),mass=3,dims=(.20,.20,.15),description='Fixed shoulder anchor. Neutral limb hangs downward; no moving pedestal.')
    link('shoulder_abduction','base_link',j=j('shoulder_abduction','Shoulder side raise',[1,0,0],-1.35,1.35,.10,70,550,48),mass=.2,description='Glenohumeral abduction/adduction axis.')
    link('shoulder_flexion','shoulder_abduction',j=j('shoulder_flexion','Shoulder forward raise',[0,1,0],-1.2,2.3,.25,70,550,48),mass=.2,description='Glenohumeral flexion/extension axis.')
    link('upper_arm','shoulder_flexion',j=j('shoulder_rotation','Upper arm rotation',[0,0,1],-2.6,2.6,0,40,400,32),mass=1.45,com=(0,0,.135),dims=(.10,.095,.3),description='Contoured 300 mm upper arm; humeral axial rotation at the shoulder.')
    link('elbow_link','upper_arm',(0,0,.3),j=j('elbow_flexion','Elbow flexion',[0,1,0],0,2.45,1.1,40,400,32),mass=.14,dims=(.06,.07,.055),description='Single-axis anatomical elbow; ulnohumeral flexion with no reverse bend.')
    link('forearm','elbow_link',j=j('forearm_pronation','Forearm pronation',[0,0,1],-3.14,3.14,0,12,150,12),mass=.9,com=(0,0,.11),dims=(.078,.071,.25),description='250 mm tapered forearm with independent pronation/supination.')
    link('wrist_pitch','forearm',(0,0,.25),j=j('wrist_flexion','Wrist flexion',[0,1,0],-1.25,1.25,.20,8,120,9),mass=.15,com=(0,0,.02),dims=(.052,.062,.04),description='40 mm wrist transition; wrist flexion/extension.')
    palm=copy.deepcopy(next(l for l in old['links'] if l['name']=='palm_base'))
    palm.update(parent='wrist_pitch',origin_xyz=[0,0,.04],joint=j('wrist_deviation','Wrist deviation',[1,0,0],-.65,.65,0,6,100,8));links.append(palm)
    links.extend(copy.deepcopy(old['links'][6:]))
    return dict(name='AnthroArm-27',version='3.0',units=old['units'],description='Human-shaped shoulder, upper arm, forearm, wrist and independently articulated five-digit hand. Digital engineering concept.',arm_dof=7,hand_dof=20,total_dof=27,hand_length_m=.19,arm_lengths_m=[.3,.25],wrist_length_m=.04,palm_dimensions_m=old['palm_dimensions_m'],finger_lengths_m=old['finger_lengths_m'],thumb_lengths_m=old['thumb_lengths_m'],coordinate_convention='Link local +Z points distally, +X is palmar, +Y is thumb/index side. Shoulder anchor rotates pi around X in world, so neutral arm hangs down.',links=links)

def s(values):return ' '.join(f'{x:.10g}' for x in values)
def add(parent,tag,**attrs):return ET.SubElement(parent,tag,{k:str(v) for k,v in attrs.items()})
def save(element,path):ET.indent(element,space='  ');ET.ElementTree(element).write(path,encoding='utf-8',xml_declaration=True)

def attach_meshes(spec):
    manifest=json.loads((DESIGN/'anatomical_manifest.json').read_text(encoding='utf-8-sig'))
    if manifest.get('mesh_units')!='m' or not manifest.get('valid'):raise ValueError('Expected validated metre CAD meshes')
    for link in spec['links']:
        link['geoms']=[]
        for c in manifest['components']:
            if c['link']==link['name']:
                if not (DESIGN/c['file']).is_file():raise FileNotFoundError(c['file'])
                link['geoms'].append(dict(name=c['name'],type='mesh',mesh_file=c['file'],pos=[0,0,0],rpy=[0,0,0],size=[],rgba=list(c['rgba'][:3])+[1],collision=bool(c.get('collision_candidate')),category=c.get('category','external'),description=c['explanation']))
    spec['collision_representation']='Per-component convex hulls of anatomical CAD shells and pads; exact visual meshes separate.'
    return spec

def write_mjcf(spec):
    root=ET.Element('mujoco',model=spec['name']);add(root,'compiler',angle='radian',inertiafromgeom='false',autolimits='true')
    add(root,'option',timestep='.002',gravity='0 0 -9.81',integrator='implicitfast',cone='elliptic',iterations='100')
    visual=add(root,'visual');add(visual,'global',offwidth='1600',offheight='1200');add(visual,'quality',shadowsize='2048');add(visual,'headlight',ambient='.35 .35 .35',diffuse='.65 .65 .65')
    asset=add(root,'asset');add(asset,'texture',name='sky',type='skybox',builtin='gradient',rgb1='.04 .065 .095',rgb2='.16 .21 .27',width='128',height='768')
    for l in spec['links']:
        for g in l['geoms']:add(asset,'mesh',name=g['name']+'_mesh',file='../../design/v3/'+g['mesh_file'],smoothnormal='true')
    defaults=add(root,'default');add(defaults,'geom',friction='1.2 .015 .001',condim='4',solref='.008 1',solimp='.95 .99 .001',margin='.0002');add(defaults,'joint',solreflimit='.004 1',solimplimit='.99 .999 .0001')
    world=add(root,'worldbody');add(world,'light',pos='1 -1 2',dir='-.3 .4 -1');add(world,'light',pos='-.8 .8 1.8',dir='.3 -.3 -1',diffuse='.5 .6 .7')
    add(world,'geom',name='floor',type='plane',size='2 2 .1',rgba='.14 .19 .23 1')
    add(world,'geom',name='worktable',type='box',size='.30 .32 .025',pos='.40 0 .575',rgba='.24 .31 .35 1')
    camera_pos=np.array([.76,-.9,1.3]);target=np.array([.42,0,.62]);forward=target-camera_pos;forward/=np.linalg.norm(forward);right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,forward)
    add(world,'camera',name='vision_camera',pos=s(camera_pos),xyaxes=s(np.r_[right,up]),fovy='48')
    bodies={}
    for link in spec['links']:
        body=add(world if link['parent'] is None else bodies[link['parent']],'body',name=link['name'],pos=s(link['origin_xyz']),euler=s(link['origin_rpy']));bodies[link['name']]=body
        add(body,'inertial',pos=s(link['com']),mass=link['mass'],diaginertia=s(link['inertia']))
        j=link['joint']
        if j:add(body,'joint',name=j['name'],type='hinge',axis=s(j['axis']),range=s(j['range']),actuatorfrclimited='true',actuatorfrcrange=s([-j['effort'],j['effort']]),armature='.01' if j['group']=='Arm' else '.000015',damping='.12' if j['group']=='Arm' else '.008',frictionloss='.015' if j['group']=='Arm' else '.001')
        for g in link['geoms']:
            add(body,'geom',name=g['name'],type='mesh',mesh=g['name']+'_mesh',rgba=s(g['rgba']),contype='0',conaffinity='0',group='4' if g.get('category')=='internal' else '1')
            if g['collision']:add(body,'geom',name=g['name']+'_collision',type='mesh',mesh=g['name']+'_mesh',rgba='.12 .88 .45 .3',group='3')
        if link['name']=='palm_base':add(body,'site',name='palm_site',pos='0 0 .05',size='.003',rgba='0 0 0 0')
        if link['name'].endswith('_distal'):
            finger=link['name'].split('_')[0];length=(spec['thumb_lengths_m'] if finger=='thumb' else spec['finger_lengths_m'][finger])[-1]
            add(body,'site',name=finger+'_tip',pos=s([0,0,length]),size='.002',rgba='0 0 0 0')
    object_body=add(world,'body',name='object',pos='.44 -.04 .6255');add(object_body,'freejoint',name='object_free');add(object_body,'inertial',mass='.06',pos='0 0 0',diaginertia='.000025 .000025 .000025');add(object_body,'geom',name='object_geom',type='box',size='.025 .025 .025',rgba='1 .35 .025 1',friction='1.5 .02 .002')
    contact=add(root,'contact')
    for a,b in [('base_link','shoulder_abduction'),('base_link','shoulder_flexion'),('base_link','upper_arm'),('shoulder_abduction','upper_arm'),('upper_arm','forearm'),('forearm','palm_base')]+[('palm_base',f+'_proximal') for f in ('index','middle','ring','pinky')]+[('palm_base','thumb_metacarpal')]:add(contact,'exclude',body1=a,body2=b)
    actuators=add(root,'actuator')
    for link in spec['links']:
        j=link['joint']
        if j:
            h=j['effort']/j['kp'];add(actuators,'position',name='motor_'+j['name'],joint=j['name'],kp=j['kp'],kv=j['kv'],ctrlrange=s([j['range'][0]-h,j['range'][1]+h]),forcerange=s([-j['effort'],j['effort']]))
    sensors=add(root,'sensor');add(sensors,'framepos',name='palm_position',objtype='site',objname='palm_site');add(sensors,'gyro',name='palm_gyro',site='palm_site');add(sensors,'accelerometer',name='palm_accelerometer',site='palm_site')
    q=[l['joint']['home'] for l in spec['links'] if l['joint']];keys=add(root,'keyframe');add(keys,'key',name='home',qpos=s(q+[.44,-.04,.6255,1,0,0,0]),ctrl=s(q))
    save(root,SIM/'robot.xml')

def generate(meshes=True):
    spec=make_spec()
    if meshes:spec=attach_meshes(spec)
    (DESIGN/'robot_spec.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
    if meshes:
        write_mjcf(spec)
        # Reuse the general URDF exporter with a temporary direct output root.
        original_save=v2.save_xml
        def save_urdf(element,path):
            # URDF has no root-link pose attribute; explicitly retain the fixed
            # shoulder anchor transform so CAD, URDF and MJCF world frames match.
            add(element,'link',name='world')
            anchor=add(element,'joint',name='shoulder_anchor',type='fixed');add(anchor,'parent',link='world');add(anchor,'child',link='base_link');add(anchor,'origin',xyz=s(spec['links'][0]['origin_xyz']),rpy=s(spec['links'][0]['origin_rpy']))
            save(element,DESIGN/'robot.urdf')
        v2.save_xml=save_urdf
        try:v2.write_urdf(spec)
        finally:v2.save_xml=original_save
    print('V3 canonical spec:',DESIGN/'robot_spec.json');return spec
if __name__=='__main__':generate('--spec-only' not in sys.argv)
