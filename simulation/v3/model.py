"""27-axis anatomical limb runtime; bounded MuJoCo physics and 7-axis pose IK."""
from pathlib import Path
import importlib.util,json,math
import numpy as np
import mujoco
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[2]
module_spec=importlib.util.spec_from_file_location('v2_runtime',ROOT/'simulation'/'model.py')
v2=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(v2)

class ArmSimulation(v2.ArmSimulation):
    def __init__(self,model_path=None):
        self.spec=json.loads((ROOT/'design'/'v3'/'robot_spec.json').read_text(encoding='utf-8'))
        self.m=mujoco.MjModel.from_xml_path(str(model_path or ROOT/'simulation'/'v3'/'robot.xml'));self.d=mujoco.MjData(self.m)
        self.joints=[]
        for link in self.spec['links']:
            j=link['joint']
            if j:
                jid=mujoco.mj_name2id(self.m,mujoco.mjtObj.mjOBJ_JOINT,j['name'])
                self.joints.append(dict(name=j['name'],label=j['label'],group=j['group'],min=j['range'][0],max=j['range'][1],home=j['home'],effort=j['effort'],velocity_limit=j['velocity'],id=jid,qpos_address=int(self.m.jnt_qposadr[jid]),dof_address=int(self.m.jnt_dofadr[jid])))
        self.names=[j['name'] for j in self.joints];self.index={n:i for i,n in enumerate(self.names)}
        self.qadr=np.array([j['qpos_address'] for j in self.joints]);self.vadr=np.array([j['dof_address'] for j in self.joints]);self.low=np.array([j['min'] for j in self.joints]);self.high=np.array([j['max'] for j in self.joints]);self.speed=np.array([j['velocity_limit'] for j in self.joints])
        self.palm_id=mujoco.mj_name2id(self.m,mujoco.mjtObj.mjOBJ_SITE,'palm_site');self.object_id=mujoco.mj_name2id(self.m,mujoco.mjtObj.mjOBJ_BODY,'object');self.kp=self.m.actuator_gainprm[:,0].copy();self.effort=np.array([j['effort'] for j in self.joints])
        self.targets=np.zeros(27);self.commanded=np.zeros(27);self._renderer=None;self._render_size=None;self.target_data=mujoco.MjData(self.m);self.last_feedforward=np.zeros(27)
        self.tip_collision_geoms={finger:[i for i in range(self.m.ngeom) if self.m.geom_contype[i] and mujoco.mj_id2name(self.m,mujoco.mjtObj.mjOBJ_BODY,int(self.m.geom_bodyid[i]))==finger+'_distal'] for finger in ('index','thumb')}
        self.pinch_targets_path=ROOT/'design'/'v3'/'anatomical_pinch.json';self.reset()
    def state(self):
        state=super().state();errors=np.degrees(self.targets-self.d.qpos[self.qadr])
        state['precision'].update(arm_max_error_deg=float(np.max(abs(errors[:7]))),hand_max_error_deg=float(np.max(abs(errors[7:]))))
        state.update(arm_dof=7,hand_dof=20,total_dof=27)
        return state
    def forward_kinematics(self,positions=None):
        data=mujoco.MjData(self.m);data.qpos[:]=self.d.qpos
        if positions is not None:
            if isinstance(positions,dict):
                for name,q in positions.items():data.qpos[self.qadr[self.index[name]]]=float(q)
            else:
                values=np.asarray(positions,dtype=float)
                if len(values) not in (7,27):raise ValueError('Expected7 arm or27 joint positions')
                data.qpos[self.qadr[:len(values)]]=values
        mujoco.mj_forward(self.m,data)
        return dict(position=data.site_xpos[self.palm_id].tolist(),rotation=data.site_xmat[self.palm_id].reshape(3,3).tolist())
    def solve_ik(self,target_xyz,target_rotation=None,apply=True):
        target=np.asarray(target_xyz,dtype=float)
        if target.shape!=(3,) or not np.isfinite(target).all():raise ValueError('Expected3 finite target metres')
        desired_R=None if target_rotation is None else np.asarray(target_rotation,dtype=float).reshape(3,3)
        data=mujoco.MjData(self.m);data.qpos[:]=self.d.qpos
        initial=np.clip(self.d.qpos[self.qadr[:7]],self.low[:7]+1e-7,self.high[:7]-1e-7)
        def residual(q):
            data.qpos[self.qadr[:7]]=q;mujoco.mj_forward(self.m,data)
            position=data.site_xpos[self.palm_id]-target
            if desired_R is None:return np.r_[position,.00001*(q-initial)]
            actual=data.site_xmat[self.palm_id].reshape(3,3);orientation=Rotation.from_matrix(desired_R@actual.T).as_rotvec()
            return np.r_[position,.1*orientation,.00001*(q-initial)]
        seeds=[initial,[0,.7,0,1.3,3.0,0,0],[0,.2,0,1.8,3.,.4,0],[.3,1.2,-.2,.8,0,-.5,0],[-.3,.8,.3,1.5,-3.,0,.2]]
        best=None
        for seed in seeds:
            result=least_squares(residual,np.clip(seed,self.low[:7]+1e-7,self.high[:7]-1e-7),bounds=(self.low[:7],self.high[:7]),xtol=1e-9,ftol=1e-9,gtol=1e-9,max_nfev=300)
            r=residual(result.x);score=float(np.linalg.norm(r));error=float(np.linalg.norm(r[:3]));orientation_error=0 if desired_R is None else float(np.linalg.norm(r[3:6])/.1)
            if best is None or score<best[0]:best=(score,error,orientation_error,result.x.copy())
            if error<.0005 and orientation_error<.015:break
        _,error,orientation_error,q=best;success=error<.002 and orientation_error<.04;joints=dict(zip(self.names[:7],q.tolist()))
        if success and apply:self.set_targets(joints)
        return dict(success=bool(success),error_m=error,orientation_error_rad=orientation_error,target=target.tolist(),joints=joints,orientation_controlled=desired_R is not None,collision_checked=False,note='Numerical seven-axis IK; controller checks contact during motion. Not a global collision-free planner.')

if __name__=='__main__':
    sim=ArmSimulation();sim.step(1500);print(json.dumps(sim.state()['precision'],indent=2));sim.close()
