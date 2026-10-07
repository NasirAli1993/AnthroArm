"""Free-base 3-D MuJoCo mobile manipulator; physical wheels, no world weld."""
from pathlib import Path
import sys,importlib.util,xml.etree.ElementTree as ET
import numpy as np,mujoco
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'integration/grasping'))
s=importlib.util.spec_from_file_location('mobile_v3_arm',ROOT/'simulation/v3/model.py');arm=importlib.util.module_from_spec(s);s.loader.exec_module(arm)

def generate(object_xy=(.4,0),start_x=-.6):
    source=ROOT/'simulation/v3/robot.xml';tree=ET.parse(source);root=tree.getroot()
    root.set('model','AnthroArm-27 on physical differential-drive base')
    for mesh in root.findall('./asset/mesh'):mesh.set('file',str((source.parent/mesh.get('file')).resolve()))
    keys=root.find('keyframe')
    if keys is not None:root.remove(keys)
    world=root.find('worldbody');limb=world.find("body[@name='base_link']");world.remove(limb)
    base=ET.SubElement(world,'body',name='mobile_base',pos=f'{start_x} 0 .162')
    ET.SubElement(base,'freejoint',name='mobile_free')
    ET.SubElement(base,'inertial',pos='0 0 0',mass='80',diaginertia='1.84 1.84 3.333')
    ET.SubElement(base,'geom',name='mobile_chassis',type='box',size='.25 .25 .08',rgba='.12 .62 .58 1',friction='1.2 .002 .0001',group='0')
    ET.SubElement(base,'geom',name='mobile_front_marker',type='box',pos='.235 0 .085',size='.015 .12 .009',rgba='.95 .91 .4 1',contype='0',conaffinity='0',group='0')
    post=ET.SubElement(base,'body',name='mounting_column',pos='-.18 0 .515')
    ET.SubElement(post,'inertial',pos='0 0 0',mass='6',diaginertia='.48475 .48475 .009075')
    ET.SubElement(post,'geom',name='column',type='cylinder',size='.055 .49',rgba='.3 .36 .4 1',group='0')
    ET.SubElement(base,'geom',name='shoulder_support',type='capsule',fromto='-.18 0 1.0 0 0 1.0',size='.025',rgba='.3 .36 .4 1',group='0')
    ET.SubElement(base,'geom',name='lidar_housing',type='cylinder',pos='.15 0 .135',size='.05 .025',rgba='.05 .1 .12 1',group='0')
    ET.SubElement(base,'site',name='mobile_lidar',pos='.15 0 .17',size='.007',rgba='.2 .8 .9 1')
    for side,y in [('left',.29),('right',-.29)]:
        wheel=ET.SubElement(base,'body',name=side+'_wheel',pos=f'0 {y} -.057')
        ET.SubElement(wheel,'inertial',pos='0 0 0',mass='2',diaginertia='.00593 .011025 .00593')
        ET.SubElement(wheel,'joint',name=side+'_wheel',type='hinge',axis='0 1 0',limited='false',damping='.04',armature='.002')
        ET.SubElement(wheel,'geom',name=side+'_tire',type='cylinder',quat='.70710678 .70710678 0 0',size='.105 .025',rgba='.035 .045 .055 1',friction='1.4 .002 .0001',condim='3',group='0')
    for i,(x,y) in enumerate([(.23,.18),(.23,-.18),(-.23,.18),(-.23,-.18)]):
        ET.SubElement(base,'geom',name=f'caster_{i}',type='sphere',pos=f'{x} {y} -.12',size='.04',rgba='.45 .5 .54 1',friction='.004 .0001 .00001',condim='3',group='0')
    limb.set('pos','0 0 .918')
    # Fixed bearing neck closes the visible support-to-flange connection.
    # Its mass is included in the original 3 kg fixed mounting assembly.
    ET.SubElement(limb,'geom',name='fixed_bearing_neck',type='cylinder',pos='0 0 -.066',size='.012 .026',rgba='.38 .44 .48 1',contype='0',conaffinity='0',group='0')
    base.append(limb)
    for name,pos,size in [('wall_north','0 1.4 .5','2 .04 .5'),('wall_south','0 -1.4 .5','2 .04 .5'),('wall_west','-1.8 0 .5','.04 1.4 .5'),('wall_east','1.8 0 .5','.04 1.4 .5')]:
        ET.SubElement(world,'geom',name=name,type='box',pos=pos,size=size,rgba='.25 .32 .37 1',group='2')
    obj=world.find("body[@name='object']");obj.set('pos',f'{object_xy[0]} {object_xy[1]} .619')
    geom=obj.find('geom');geom.set('size','.018 .018 .018')
    inertial=obj.find('inertial');inertial.set('mass','.06');inertial.set('diaginertia','.00001296 .00001296 .00001296')
    actuator=root.find('actuator')
    for side in ('left','right'):
        ET.SubElement(actuator,'velocity',name=side+'_drive',joint=side+'_wheel',kv='30',forcerange='-18 18',ctrlrange='-8 8',forcelimited='true',ctrllimited='true')
    path=HERE/'model.xml';ET.indent(tree,space='  ');tree.write(path,encoding='utf-8',xml_declaration=True);return path

class MobileSimulation(arm.ArmSimulation):
    radius=.105;track=.58
    def __init__(self,object_xy=(.4,0),start_x=-.6):
        super().__init__(generate(object_xy,start_x))
        self.kp=self.m.actuator_gainprm[:27,0].copy()
        self.base_id=self.m.body('mobile_base').id
        self.lidar_id=self.m.site('mobile_lidar').id
        self.wheel_q=np.array([self.m.joint(n+'_wheel').qposadr[0] for n in ('left','right')])
        self.wheel_v=np.array([self.m.joint(n+'_wheel').dofadr[0] for n in ('left','right')])
        self.drive=np.zeros(2);self.park_angles=None
        # A 270-degree front sensor leaves the mast behind its blind sector.
        self.angles=np.linspace(-.75*np.pi,.75*np.pi,180,endpoint=False)
        self.last_enc=self.d.qpos[self.wheel_q].copy()
        self.max_arm_effort=0.;self.max_wheel_effort=0.

    def reset(self):
        mujoco.mj_resetData(self.m,self.d)
        self.targets=np.array([j['home'] for j in self.joints],dtype=float)
        self.commanded=self.targets.copy();self.d.qpos[self.qadr]=self.targets
        self.d.ctrl[:27]=self.targets;mujoco.mj_forward(self.m,self.d)
        self.drive=np.zeros(2);self.park_angles=None
        return self.state()

    def state(self):
        return dict(time=float(self.d.time),total_dof=29,actuated_arm_dof=27,free_base=True)

    def command_drive(self,v,w):
        self.park_angles=None
        self.drive=np.array([(v-w*self.track/2)/self.radius,(v+w*self.track/2)/self.radius])

    def brake(self):
        self.park_angles=self.d.qpos[self.wheel_q].copy();self.drive[:]=0.

    def hold(self):
        self.targets=np.clip(self.d.qpos[self.qadr].copy(),self.low,self.high)
        self.commanded=self.targets.copy();self.d.ctrl[:27]=self.targets
        return dict(zip(self.names,self.targets.tolist()))

    def step(self,n=1):
        dt=self.m.opt.timestep
        for _ in range(int(n)):
            self.commanded+=np.clip(self.targets-self.commanded,-self.speed*dt,self.speed*dt)
            ff=np.clip(self.d.qfrc_bias[self.vadr],-self.effort,self.effort)
            self.d.ctrl[:27]=np.clip(self.commanded+ff/self.kp,self.m.actuator_ctrlrange[:27,0],self.m.actuator_ctrlrange[:27,1])
            wheel_ref=self.drive if self.park_angles is None else np.clip(20*(self.park_angles-self.d.qpos[self.wheel_q]),-2.,2.)
            self.d.ctrl[27:]=np.clip(wheel_ref,-8,8)
            mujoco.mj_step(self.m,self.d)
            self.max_arm_effort=max(self.max_arm_effort,float(np.max(abs(self.d.actuator_force[:27])/self.effort)))
            self.max_wheel_effort=max(self.max_wheel_effort,float(np.max(abs(self.d.actuator_force[27:])/18)))

    def observe(self):
        enc=self.d.qpos[self.wheel_q].copy();delta=(enc-self.last_enc)*self.radius;self.last_enc=enc
        origin=self.d.site_xpos[self.lidar_id];R=self.d.site_xmat[self.lidar_id].reshape(3,3)
        ranges=[];geom=np.zeros(1,dtype=np.int32)
        for angle in self.angles:
            distance=mujoco.mj_ray(self.m,self.d,origin,R@np.array([np.cos(angle),np.sin(angle),0.]),None,1,self.base_id,geom)
            ranges.append(4. if distance<0 else min(4.,float(distance)))
        return dict(ranges=np.array(ranges),angle_min=float(self.angles[0]),angle_increment=float(self.angles[1]-self.angles[0]),range_max=4.,encoder_delta=np.array([delta.mean(),0.,(delta[1]-delta[0])/self.track]))

    def truth(self):
        R=self.d.xmat[self.base_id].reshape(3,3)
        return dict(xyz_m=self.d.xpos[self.base_id].tolist(),yaw_rad=float(np.arctan2(R[1,0],R[0,0])),tilt_rad=float(np.arccos(np.clip(R[2,2],-1,1))))
