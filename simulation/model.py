"""MuJoCo runtime for Aster-25. Units: metres, radians, seconds.
Position actuators are effort limited; robot gravity acts on all moving links.
The IK solver controls palm position only (a five-axis arm is orientation-underactuated).
"""
from pathlib import Path
import json, math
import numpy as np
import mujoco
from scipy.optimize import least_squares

ROOT=Path(__file__).resolve().parents[1]
PRESETS=('open','fist','pinch','point','peace')

class ArmSimulation:
    def __init__(self, model_path=None):
        self.spec=json.loads((ROOT/'design'/'robot_spec.json').read_text(encoding='utf-8'))
        self.m=mujoco.MjModel.from_xml_path(str(model_path or ROOT/'simulation'/'robot.xml'))
        self.d=mujoco.MjData(self.m)
        self.joints=[]
        for link in self.spec['links']:
            j=link['joint']
            if j:
                jid=mujoco.mj_name2id(self.m,mujoco.mjtObj.mjOBJ_JOINT,j['name'])
                self.joints.append(dict(name=j['name'],label=j['label'],group=j['group'],min=j['range'][0],max=j['range'][1],home=j['home'],effort=j['effort'],velocity_limit=j['velocity'],id=jid,qpos_address=int(self.m.jnt_qposadr[jid]),dof_address=int(self.m.jnt_dofadr[jid])))
        self.names=[j['name'] for j in self.joints]
        self.index={n:i for i,n in enumerate(self.names)}
        self.qadr=np.array([j['qpos_address'] for j in self.joints]);self.vadr=np.array([j['dof_address'] for j in self.joints])
        self.low=np.array([j['min'] for j in self.joints]);self.high=np.array([j['max'] for j in self.joints]);self.speed=np.array([j['velocity_limit'] for j in self.joints])
        self.palm_id=mujoco.mj_name2id(self.m,mujoco.mjtObj.mjOBJ_SITE,'palm_site')
        self.object_id=mujoco.mj_name2id(self.m,mujoco.mjtObj.mjOBJ_BODY,'object')
        self.kp=self.m.actuator_gainprm[:,0].copy()
        self.effort=np.array([j['effort'] for j in self.joints])
        self.targets=np.zeros(25);self.commanded=np.zeros(25);self._renderer=None;self._render_size=None
        self.target_data=mujoco.MjData(self.m)
        self.tip_collision_geoms={finger:[i for i in range(self.m.ngeom) if self.m.geom_contype[i] and mujoco.mj_id2name(self.m,mujoco.mjtObj.mjOBJ_BODY,int(self.m.geom_bodyid[i]))==finger+'_distal'] for finger in ('index','thumb')}
        self.last_feedforward=np.zeros(25)
        self.pinch_targets_path=ROOT/'design'/'anatomical_pinch.json'
        self.reset()
    @property
    def model(self):return self.m
    @property
    def data(self):return self.d
    def reset(self):
        mujoco.mj_resetDataKeyframe(self.m,self.d,0)
        self.targets=np.array([j['home'] for j in self.joints],dtype=float)
        self.commanded=self.targets.copy()
        self.d.ctrl[:]=self.targets
        mujoco.mj_forward(self.m,self.d)
        return self.state()
    def hold(self):
        self.targets=np.clip(self.d.qpos[self.qadr].copy(),self.low,self.high)
        self.commanded=self.targets.copy()
        self.d.ctrl[:]=self.targets
        return dict(zip(self.names,self.targets.tolist()))
    def set_targets(self,targets):
        if not isinstance(targets,dict):raise ValueError('targets must map joint names to radians')
        unknown=set(targets)-set(self.index)
        if unknown:raise ValueError('Unknown joints: '+', '.join(sorted(unknown)))
        parsed={}
        for name,value in targets.items():
            value=float(value)
            if not math.isfinite(value):raise ValueError('Joint targets must be finite')
            i=self.index[name];parsed[name]=float(np.clip(value,self.low[i],self.high[i]))
        for name,value in parsed.items():self.targets[self.index[name]]=value
        return parsed
    def preset(self,name):
        if name not in PRESETS:raise ValueError('Preset must be '+', '.join(PRESETS))
        q={j['name']:0. for j in self.joints if j['group']!='Arm'}
        close={'fist':['index','middle','ring','pinky'],'point':['middle','ring','pinky'],'peace':['ring','pinky'],'pinch':['middle','ring','pinky'],'open':[]}[name]
        for finger in close:
            for suffix,value in [('_mcp_flexion',1.15),('_pip',1.35),('_dip',.9)]:q[finger+suffix]=value
        if name=='fist':q.update(thumb_cmc_opposition=1.0,thumb_cmc_flexion=.8,thumb_mcp_flexion=.85,thumb_ip=.65)
        if name in ('point','peace'):q.update(thumb_cmc_opposition=.95,thumb_cmc_flexion=.95,thumb_mcp_flexion=.8,thumb_ip=.6)
        if name=='peace':q.update(index_mcp_abduction=-.13,middle_mcp_abduction=.10)
        if name=='pinch':
            if self.pinch_targets_path.exists():q.update(json.loads(self.pinch_targets_path.read_text(encoding='utf-8'))['targets'])
            else:q.update(index_mcp_flexion=1.34676,index_pip=1.35168,index_dip=.74148,thumb_cmc_opposition=1.46774,thumb_cmc_flexion=.34829,thumb_mcp_flexion=0,thumb_ip=.00615)
        return self.set_targets(q)
    def step(self,n=1):
        n=int(n)
        if n<0 or n>100000:raise ValueError('n outside 0..100000')
        dt=self.m.opt.timestep
        for _ in range(n):
            delta=np.clip(self.targets-self.commanded,-self.speed*dt,self.speed*dt)
            self.commanded[:]+=delta
            # Feed model bias through the SAME effort-limited servo. There are no
            # unbounded qfrc_applied forces and no body gravcomp. References are
            # rate-limited independently so gravity compensation cannot wind up.
            self.last_feedforward=np.clip(self.d.qfrc_bias[self.vadr],-self.effort,self.effort)
            self.d.ctrl[:]=np.clip(self.commanded+self.last_feedforward/self.kp,self.m.actuator_ctrlrange[:,0],self.m.actuator_ctrlrange[:,1])
            mujoco.mj_step(self.m,self.d)
        if not np.isfinite(self.d.qpos).all():raise RuntimeError('Nonfinite simulation state')
    def state(self):
        joints=[]
        for i,j in enumerate(self.joints):
            row={k:v for k,v in j.items() if k not in ('id','qpos_address','dof_address')}
            row.update(q=float(self.d.qpos[self.qadr[i]]),target=float(self.targets[i]),commanded=float(self.commanded[i]),error_deg=float(np.degrees(self.targets[i]-self.d.qpos[self.qadr[i]])),velocity=float(self.d.qvel[self.vadr[i]]),torque=float(self.d.actuator_force[i]),effort_fraction=float(abs(self.d.actuator_force[i])/self.effort[i]))
            joints.append(row)
        contacts=[]
        for cidx in range(self.d.ncon):
            c=self.d.contact[cidx];force=np.zeros(6);mujoco.mj_contactForce(self.m,self.d,cidx,force)
            contacts.append(dict(geom1=mujoco.mj_id2name(self.m,mujoco.mjtObj.mjOBJ_GEOM,int(c.geom1)),geom2=mujoco.mj_id2name(self.m,mujoco.mjtObj.mjOBJ_GEOM,int(c.geom2)),distance=float(c.dist),normal_force=float(force[0]),position=c.pos.tolist()))
        bodies=[dict(name=mujoco.mj_id2name(self.m,mujoco.mjtObj.mjOBJ_BODY,i),position=self.d.xpos[i].tolist(),quaternion=self.d.xquat[i].tolist()) for i in range(1,self.m.nbody)]
        sensors={}
        for i in range(self.m.nsensor):
            a=int(self.m.sensor_adr[i]);n=int(self.m.sensor_dim[i]);name=mujoco.mj_id2name(self.m,mujoco.mjtObj.mjOBJ_SENSOR,i);sensors[name]=self.d.sensordata[a:a+n].tolist()
        tips={finger:self.d.site_xpos[mujoco.mj_name2id(self.m,mujoco.mjtObj.mjOBJ_SITE,finger+'_tip')].tolist() for finger in ['index','middle','ring','pinky','thumb']}
        errors=np.degrees(self.targets-self.d.qpos[self.qadr])
        self.target_data.qpos[:]=self.d.qpos
        self.target_data.qpos[self.qadr]=self.targets
        mujoco.mj_forward(self.m,self.target_data)
        precision=dict(joint_max_error_deg=float(np.max(np.abs(errors))),joint_rms_error_deg=float(np.sqrt(np.mean(errors**2))),arm_max_error_deg=float(np.max(np.abs(errors[:5]))),hand_max_error_deg=float(np.max(np.abs(errors[5:]))),palm_target_error_mm=float(1000*np.linalg.norm(self.target_data.site_xpos[self.palm_id]-self.d.site_xpos[self.palm_id])),max_effort_fraction=float(np.max(np.abs(self.d.actuator_force)/self.effort)),nominal_reference_reached=bool(np.max(np.abs(self.commanded-self.targets))<1e-6),note='Command tracking under current loads; contact-blocked fingers can have a large intentional target error.')
        pinch=self.pinch_surface_distance()
        return dict(fingertip_positions=tips,pinch_gap_m=float(np.linalg.norm(np.array(tips['index'])-np.array(tips['thumb']))),pinch_surface_gap_m=pinch['distance_m'],pinch_surface=pinch,precision=precision,name=self.spec['name'],version=self.spec.get('version'),time=float(self.d.time),joints=joints,palm_position=self.d.site_xpos[self.palm_id].tolist(),object_position=self.d.xpos[self.object_id].tolist(),contacts=contacts,bodies=bodies,sensors=sensors,gravity_compensation=False,actuator_bias_feedforward=True,controller='Effort-limited servo with model bias feedforward',collision_model=self.spec.get('collision_representation','primitive concept'),timestep=float(self.m.opt.timestep),presets=list(PRESETS))
    def pinch_surface_distance(self,data=None):
        """Signed closest distance between index/thumb distal convex CAD hulls.

        This is a collision-surface gap, unlike the historical endpoint-site gap.
        A negative value indicates compliant contact penetration in the solver.
        """
        data=self.d if data is None else data
        best=.5;segment=np.zeros(6);names=[]
        for a in self.tip_collision_geoms['index']:
            for b in self.tip_collision_geoms['thumb']:
                points=np.zeros(6);gap=mujoco.mj_geomDistance(self.m,data,a,b,.5,points)
                if gap<best:
                    best=float(gap);segment=points.copy();names=[mujoco.mj_id2name(self.m,mujoco.mjtObj.mjOBJ_GEOM,k) for k in (a,b)]
        return dict(distance_m=best,closest_points=segment.reshape(2,3).tolist(),geoms=names,representation='Convex hulls of the actual CAD distal shells and pads')
    def forward_kinematics(self,positions=None):
        data=mujoco.MjData(self.m);data.qpos[:]=self.d.qpos
        if positions is not None:
            if isinstance(positions,dict):
                for name,q in positions.items():data.qpos[self.qadr[self.index[name]]]=float(q)
            else:
                values=np.asarray(positions,dtype=float)
                if len(values) not in (5,25):raise ValueError('Expected 5 arm or 25 joint values')
                data.qpos[self.qadr[:len(values)]]=values
        mujoco.mj_forward(self.m,data)
        return dict(position=data.site_xpos[self.palm_id].tolist(),rotation=data.site_xmat[self.palm_id].reshape(3,3).tolist())
    def solve_ik(self,target_xyz):
        target=np.asarray(target_xyz,dtype=float)
        if target.shape!=(3,) or not np.isfinite(target).all():raise ValueError('Target must contain three finite metres')
        data=mujoco.MjData(self.m);data.qpos[:]=self.d.qpos
        def residual(q):
            data.qpos[self.qadr[:5]]=q;mujoco.mj_forward(self.m,data)
            return data.site_xpos[self.palm_id]-target
        initial=np.clip(self.d.qpos[self.qadr[:5]],self.low[:5]+1e-8,self.high[:5]-1e-8)
        seeds=[initial,np.array([math.atan2(target[1],target[0]),.6,1.2,-1.,0]),np.array([math.atan2(target[1],target[0]),1.3,-1.4,.3,0])]
        best=None
        for seed in seeds:
            result=least_squares(residual,np.clip(seed,self.low[:5]+1e-8,self.high[:5]-1e-8),bounds=(self.low[:5],self.high[:5]),xtol=1e-10,ftol=1e-10,gtol=1e-10,max_nfev=250)
            error=float(np.linalg.norm(result.fun))
            if best is None or error<best[0]:best=(error,result.x.copy())
            if error<.0002:break
        error,q=best;success=error<.002
        joints=dict(zip(self.names[:5],[float(x) for x in q]))
        if success:self.set_targets(joints)
        return dict(success=success,error_m=error,target=target.tolist(),joints=joints,orientation_controlled=False,collision_checked=False,note='Palm-position IK only; motion path and requested orientation are not constrained. Targets are applied only when error is below 2 mm.')
    def render(self,width=960,height=720,camera=None):
        width=int(width);height=int(height)
        if not 64<=width<=1600 or not 64<=height<=1200:raise ValueError('Render size must be 64..1600 x 64..1200')
        if self._renderer is None or self._render_size!=(width,height):
            if self._renderer is not None:self._renderer.close()
            self._renderer=mujoco.Renderer(self.m,height=height,width=width);self._render_size=(width,height)
        cam=mujoco.MjvCamera();mujoco.mjv_defaultCamera(cam)
        settings=camera or {};cam.azimuth=float(settings.get('azimuth',135));cam.elevation=float(settings.get('elevation',-20));cam.distance=float(settings.get('distance',1.40));cam.lookat[:]=settings.get('lookat',[.20,0,.36])
        options=mujoco.MjvOption();options.geomgroup[3]=0
        self._renderer.update_scene(self.d,camera=cam,scene_option=options)
        return self._renderer.render().copy()
    def close(self):
        if self._renderer is not None:self._renderer.close();self._renderer=None

if __name__=='__main__':
    sim=ArmSimulation();sim.step(500);print(json.dumps(sim.state(),indent=2));sim.close()


