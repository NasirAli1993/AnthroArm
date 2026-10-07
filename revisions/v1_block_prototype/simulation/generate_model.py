"""Single-source robot specification and matched MJCF / URDF exporters.
All dimensions SI. Educational mechanical concept, not manufacturing certification.
"""
from pathlib import Path
import json, math
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SPEC_PATH=ROOT/'design'/'robot_spec.json'
BLUE=[.07,.25,.42,1]; WHITE=[.80,.86,.90,1]; METAL=[.24,.30,.36,1]; TEAL=[.08,.74,.63,1]; DARK=[.055,.08,.11,1]

def geom(name, kind, size, pos=(0,0,0), rgba=WHITE, collision=True, rpy=(0,0,0)):
    return dict(name=name,type=kind,size=list(size),pos=list(pos),rpy=list(rpy),rgba=rgba,collision=collision)

def joint(name,label,group,axis,lo,hi,home=0,effort=1,kp=4,kv=.16):
    return dict(name=name,label=label,group=group,axis=list(axis),range=[lo,hi],home=home,effort=effort,kp=kp,kv=kv,velocity=2 if group=='Arm' else 5)

def make_spec():
    links=[]
    def link(name,parent,xyz=(0,0,0),rpy=(0,0,0),j=None,mass=.05,com=(0,0,0),dims=(.02,.02,.02),geoms=(),description=''):
        inertia=[mass*(dims[1]**2+dims[2]**2)/12,mass*(dims[0]**2+dims[2]**2)/12,mass*(dims[0]**2+dims[1]**2)/12]
        row=dict(name=name,parent=parent,origin_xyz=list(xyz),origin_rpy=list(rpy),joint=j,mass=mass,com=list(com),inertia=inertia,geoms=list(geoms),description=description)
        links.append(row);return row
    link('base_link',None,mass=3,com=(0,0,.04),dims=(.24,.24,.08),geoms=[geom('base_plate','cylinder',[.12,.04],(0,0,.04),DARK),geom('base_trim','cylinder',[.105,.008],(0,0,.086),BLUE,False)],description='Bench-mounted base; conceptual plate requires bolts to a rigid work surface.')
    link('waist_link','base_link',(0,0,.08),j=joint('joint_1_waist','Waist rotation','Arm',[0,0,1],-2.8,2.8,0,60,400,40),mass=.65,com=(0,0,.025),dims=(.08,.08,.05),geoms=[geom('waist_shell','cylinder',[.046,.024],(0,0,.026),BLUE)],description='Vertical yaw axis turns the entire arm left and right.')
    for name,parent,z,L,width,mass,j,desc in [
      ('upper_arm','waist_link',.06,.30,.052,1.20,joint('joint_2_shoulder','Shoulder pitch','Arm',[0,1,0],-1.75,1.75,.5,60,400,40),'300 mm upper arm transfers shoulder torque to the elbow.'),
      ('forearm','upper_arm',.30,.25,.042,.85,joint('joint_3_elbow','Elbow pitch','Arm',[0,1,0],-2.3,2.3,.65,35,300,28),'250 mm forearm extends the elbow toward the wrist.'),
      ('wrist_link','forearm',.25,.06,.038,.22,joint('joint_4_wrist_pitch','Wrist pitch','Arm',[0,1,0],-1.57,1.57,-.75,8,100,8),'Wrist pitch tilts the palm; a five-axis arm cannot independently achieve every 6D pose.')]:
        gs=[geom(name+'_shell','box',[width/2,width/2,(L-.052)/2 if L>.1 else .012],(0,0,L/2),WHITE),geom(name+'_spine','box',[.005,width*.37,(L-.066)/2 if L>.1 else .010],(-width/2-.003,0,L/2),BLUE,False),geom(name+'_hub','cylinder',[width*.67,width*.68],(0,0,0),BLUE,False,(math.pi/2,0,0))]
        if name=='wrist_link':gs.append(geom('wrist_roll_shaft','cylinder',[.016,.015],(0,0,.05),METAL,False))
        for sy in [-1,1]: gs.append(geom(name+('_cap_a' if sy<0 else '_cap_b'),'cylinder',[width*.37,.003],(0,sy*(width*.68+.004),0),METAL,False,(math.pi/2,0,0)))
        link(name,parent,(0,0,z),j=j,mass=mass,com=(0,0,L*.45),dims=(width,width,L),geoms=gs,description=desc)
    link('palm_base','wrist_link',(0,0,.06),j=joint('joint_5_wrist_roll','Wrist roll','Arm',[0,0,1],-2.8,2.8,0,5,65,5),mass=.35,com=(0,0,.05),dims=(.032,.084,.1),geoms=[geom('palm_shell','box',[.015,.039,.044],(0,0,.048),WHITE),geom('palm_pad','box',[.003,.032,.031],(.017,0,.052),DARK),geom('palm_backplate','box',[.004,.034,.035],(-.018,0,.047),BLUE,False),geom('palm_status','box',[.001,.015,.0025],(-.023,0,.063),TEAL,False)],description='100 mm palm houses tendon paths and supports four finger bases and the opposable thumb. Palmar surface is +X.')
    lengths={'index':[.04,.024,.018],'middle':[.045,.025,.020],'ring':[.04,.024,.018],'pinky':[.033,.020,.017]}
    for finger,y in [('index',.03),('middle',.01),('ring',-.01),('pinky',-.03)]:
        Ls=lengths[finger];z=.095 if finger=='pinky' else .1
        link(finger+'_knuckle','palm_base',(0,y,z),j=joint(finger+'_mcp_abduction',finger.title()+' spread',finger.title(),[1,0,0],-.30,.30,0,.65,3,.10),mass=.008,dims=(.01,.01,.01),geoms=[geom(finger+'_knuckle_bearing','sphere',[.0065],rgba=METAL,collision=False)],description='Co-located MCP spread carrier. Flexion hinge is at the same knuckle, not at the distal end of the proximal phalanx.')
        parent=finger+'_knuckle'
        for i,(part,L) in enumerate(zip(['proximal','intermediate','distal'],Ls)):
            jname=finger+['_mcp_flexion','_pip','_dip'][i]; name=finger+'_'+part
            width=.0135-i*.0008
            gs=[geom(name+'_shell','box',[.006,width/2,max(.002,L/2-.004)],(0,0,L/2),WHITE),geom(name+'_pad','box',[.002,width*.43,max(.001,L/2-.006)],(.0075,0,L/2),TEAL if i==2 else DARK),geom(name+'_hinge','cylinder',[.006,.0073],(0,0,0),METAL,False,(math.pi/2,0,0)),geom(name+'_back','box',[.0015,width*.32,max(.001,L/2-.006)],(-.007,0,L/2),BLUE,False)]
            j=joint(jname,finger.title()+' '+['MCP curl','PIP curl','DIP curl'][i],finger.title(),[0,1,0],0,[1.50,1.70,1.40][i],0,[1.1,.85,.55][i],5,.16)
            link(name,parent,(0,0,0 if i==0 else Ls[i-1]),j=j,mass=[.035,.024,.016][i],com=(0,0,L/2),dims=(.012,width,L),geoms=gs,description=f'{finger.title()} {part} phalanx, {L*1000:.0f} mm hinge spacing; dark/teal pad contacts objects.')
            parent=name
    link('thumb_opposition','palm_base',(0,.048,.025),j=joint('thumb_cmc_opposition','Thumb opposition','Thumb',[0,0,-1],-.2,1.6,0,1.1,5,.18),mass=.015,dims=(.014,.014,.014),geoms=[geom('thumb_cmc_bearing','sphere',[.009],rgba=BLUE,collision=False)],description='Thumb CMC opposition rotates the thumb plane across the palm.')
    parent='thumb_opposition';tls=[.030,.020,.015]
    for i,(part,L) in enumerate(zip(['metacarpal','proximal','distal'],tls)):
        name='thumb_'+part;jname=['thumb_cmc_flexion','thumb_mcp_flexion','thumb_ip'][i]
        gs=[geom(name+'_shell','box',[.007,.0075,max(.002,L/2-.004)],(0,0,L/2),WHITE),geom(name+'_pad','box',[.002,.006,max(.001,L/2-.005)],(.008,0,L/2),TEAL if i==2 else DARK),geom(name+'_hinge','cylinder',[.0065,.008],(0,0,0),METAL,False,(math.pi/2,0,0))]
        link(name,parent,(0,0,0 if i==0 else tls[i-1]),(-.75,0,0) if i==0 else (0,0,0),j=joint(jname,['Thumb CMC flexion','Thumb MCP curl','Thumb IP curl'][i],'Thumb',[0,1,0],-.25 if i==0 else 0,[1.3,1.4,1.4][i],0,1 if i==0 else .7,5,.18),mass=[.038,.026,.02][i],com=(0,0,L/2),dims=(.014,.015,L),geoms=gs,description=f'Thumb {part}, {L*1000:.0f} mm; independent flexion with an additional CMC opposition axis.')
        parent=name
    return dict(name='Aster-25',version='1.0',units={'length':'m','angle':'rad','mass':'kg'},description='Fixed-base five-axis arm with twenty independently actuated hand joints. Concept design with physically simulated rigid bodies; hardware engineering remains unvalidated.',arm_dof=5,hand_dof=20,total_dof=25,hand_length_m=.19,arm_lengths_m=[.30,.25],palm_dimensions_m=[.032,.084,.1],finger_lengths_m=lengths,thumb_lengths_m=tls,coordinate_convention='Right handed; local +Z along each link; palm +X palmar; +Y index/thumb side. Joint origins are parent-local; origin_rpy fixed XYZ roll pitch yaw.',links=links)

def s(v):return ' '.join(f'{x:.10g}' for x in v)
def add(parent,tag,**attrs):return ET.SubElement(parent,tag,{k:str(v) for k,v in attrs.items()})
def save_xml(root,path):
    ET.indent(root,space='  ');ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)

def write_mjcf(spec):
    root=ET.Element('mujoco',model=spec['name'])
    add(root,'compiler',angle='radian',inertiafromgeom='false',autolimits='true')
    add(root,'option',timestep='.002',gravity='0 0 -9.81',integrator='implicitfast',cone='elliptic',iterations='80')
    add(root,'size',njmax='2000',nconmax='600')
    visual=add(root,'visual');add(visual,'global',offwidth='1600',offheight='1200');add(visual,'quality',shadowsize='2048');add(visual,'headlight',diffuse='.6 .6 .6',ambient='.25 .25 .25',specular='.2 .2 .2')
    asset=add(root,'asset');add(asset,'texture',name='sky',type='skybox',builtin='gradient',rgb1='.035 .055 .09',rgb2='.14 .19 .26',width='128',height='768');add(asset,'texture',name='groundgrid',type='2d',builtin='checker',rgb1='.16 .19 .23',rgb2='.20 .23 .27',width='512',height='512');add(asset,'material',name='groundmat',texture='groundgrid',texrepeat='10 10',reflectance='.12')
    default=add(root,'default');add(default,'joint',damping='.04',armature='.0005',frictionloss='.015',solreflimit='.004 1',solimplimit='.99 .999 .0001');add(default,'geom',friction='1.2 .015 .001',condim='4',solref='.008 1',solimp='.95 .99 .001',margin='.0002')
    world=add(root,'worldbody');add(world,'light',name='key',pos='1 -1 2',dir='-.4 .4 -1',castshadow='true');add(world,'light',name='fill',pos='-1 1 1.5',dir='.5 -.4 -1',diffuse='.5 .6 .7');add(world,'geom',name='floor',type='plane',size='2 2 .1',material='groundmat')
    bodies={}
    for link in spec['links']:
        parent=world if link['parent'] is None else bodies[link['parent']]
        body=add(parent,'body',name=link['name'],pos=s(link['origin_xyz']),euler=s(link['origin_rpy']))
        bodies[link['name']]=body
        add(body,'inertial',pos=s(link['com']),mass=link['mass'],diaginertia=s(link['inertia']))
        j=link['joint']
        if j:add(body,'joint',name=j['name'],type='hinge',axis=s(j['axis']),range=s(j['range']),actuatorfrclimited='true',actuatorfrcrange=s([-j['effort'],j['effort']]),armature='.01' if j['group']=='Arm' else '.000015',damping='.12' if j['group']=='Arm' else '.008',frictionloss='.015' if j['group']=='Arm' else '.001')
        for g in link['geoms']:
            add(body,'geom',name=g['name'],type=g['type'],size=s(g['size']),pos=s(g['pos']),euler=s(g['rpy']),rgba=s(g['rgba']),contype='1' if g['collision'] else '0',conaffinity='1' if g['collision'] else '0',group='0' if g['collision'] else '1')
        if link['name']=='palm_base':add(body,'site',name='palm_site',pos='0 0 .05',size='.004',rgba='0 0 0 0')
        if link['name'].endswith('_distal'):add(body,'site',name=link['name'].replace('_distal','_tip'),pos=s([0,0,(spec['thumb_lengths_m'] if link['name'].startswith('thumb') else spec['finger_lengths_m'][link['name'].split('_')[0]])[-1]]),size='.002',rgba='0 0 0 0')
    block=add(world,'body',name='object',pos='.36 -.15 .020');add(block,'freejoint',name='object_free');add(block,'inertial',pos='0 0 0',mass='.060',diaginertia='.00001296 .00001296 .00001296');add(block,'geom',name='object_geom',type='box',size='.018 .018 .018',rgba='.96 .51 .12 1',friction='1.5 .02 .002')
    contact=add(root,'contact')
    # Dummy co-located knuckles must not create artificial self collisions.
    for f in ['index','middle','ring','pinky']:add(contact,'exclude',body1='palm_base',body2=f+'_proximal')
    add(contact,'exclude',body1='palm_base',body2='thumb_metacarpal')
    actuators=add(root,'actuator')
    for link in spec['links']:
        j=link['joint']
        if j:add(actuators,'position',name='motor_'+j['name'],joint=j['name'],kp=j['kp'],kv=j['kv'],ctrlrange=s(j['range']),forcerange=s([-j['effort'],j['effort']]))
    sensors=add(root,'sensor');add(sensors,'framepos',name='palm_position',objtype='site',objname='palm_site');add(sensors,'gyro',name='palm_gyro',site='palm_site');add(sensors,'accelerometer',name='palm_accelerometer',site='palm_site');add(sensors,'force',name='wrist_force',site='palm_site');add(sensors,'torque',name='wrist_torque',site='palm_site')
    k=add(root,'keyframe');q=[l['joint']['home'] for l in spec['links'] if l['joint']];add(k,'key',name='home',qpos=s(q+[.36,-.15,.02,1,0,0,0]),ctrl=s(q))
    save_xml(root,ROOT/'simulation'/'robot.xml')

def write_urdf(spec):
    robot=ET.Element('robot',name=spec['name'])
    for link in spec['links']:
        body=add(robot,'link',name=link['name']);inertial=add(body,'inertial');add(inertial,'origin',xyz=s(link['com']),rpy='0 0 0');add(inertial,'mass',value=link['mass']);ii=link['inertia'];add(inertial,'inertia',ixx=ii[0],iyy=ii[1],izz=ii[2],ixy=0,ixz=0,iyz=0)
        for g in link['geoms']:
            for typ in ['visual']+(['collision'] if g['collision'] else []):
                el=add(body,typ,name=g['name']+'_'+typ);add(el,'origin',xyz=s(g['pos']),rpy=s(g['rpy']));shape=add(el,'geometry')
                if g['type']=='box':add(shape,'box',size=s([2*x for x in g['size']]))
                elif g['type']=='cylinder':add(shape,'cylinder',radius=g['size'][0],length=2*g['size'][1])
                elif g['type']=='sphere':add(shape,'sphere',radius=g['size'][0])
                if typ=='visual':mat=add(el,'material',name=g['name']+'_material');add(mat,'color',rgba=s(g['rgba']))
        j=link['joint']
        if link['parent']:
            el=add(robot,'joint',name=j['name'] if j else link['name']+'_fixed',type='revolute' if j else 'fixed');add(el,'parent',link=link['parent']);add(el,'child',link=link['name']);add(el,'origin',xyz=s(link['origin_xyz']),rpy=s(link['origin_rpy']))
            if j:add(el,'axis',xyz=s(j['axis']));add(el,'limit',lower=j['range'][0],upper=j['range'][1],effort=j['effort'],velocity=j['velocity']);add(el,'dynamics',damping=.12 if j['group']=='Arm' else .008,friction=.015 if j['group']=='Arm' else .001)
    save_xml(robot,ROOT/'design'/'robot.urdf')

def generate():
    spec=make_spec();SPEC_PATH.write_text(json.dumps(spec,indent=2),encoding='utf-8');write_mjcf(spec);write_urdf(spec);return spec
if __name__=='__main__':
    spec=generate();print(f"Generated {len(spec['links'])} links / 25 actuators: {SPEC_PATH}")



