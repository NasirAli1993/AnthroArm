"""Contact grasp experiments on the unchanged V3 robot. Initial conditions only."""
from pathlib import Path
import importlib.util,json,time
import numpy as np,mujoco
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results'/'integration'/'grasping'
s=importlib.util.spec_from_file_location('grasp_v3_runtime',ROOT/'simulation/v3/model.py');runtime=importlib.util.module_from_spec(s);s.loader.exec_module(runtime)
R_DOWN=np.array([[0,0,1],[0,1,0],[-1,0,0]],float)
def initialize(sim,size=.036,mass=.06,xy=(.4,0)):
    sim.reset();gid=mujoco.mj_name2id(sim.m,mujoco.mjtObj.mjOBJ_GEOM,'object_geom');bid=sim.object_id;jid=mujoco.mj_name2id(sim.m,mujoco.mjtObj.mjOBJ_JOINT,'object_free');a=sim.m.jnt_qposadr[jid]
    sim.m.geom_size[gid]=size/2;sim.m.body_mass[bid]=mass;sim.m.body_inertia[bid]=mass*size*size/6
    mujoco.mj_setConst(sim.m,sim.d);sim.reset()
    sim.d.qpos[a:a+7]=[*xy,.600+size/2+.001,1,0,0,0];sim.d.qvel[:]=0;mujoco.mj_forward(sim.m,sim.d);sim.commanded=sim.targets.copy();sim.step(300)
    return np.array([*xy,.600+size/2])
def contacts(sim):
    out=[];obj=mujoco.mj_name2id(sim.m,mujoco.mjtObj.mjOBJ_GEOM,'object_geom')
    for i in range(sim.d.ncon):
        c=sim.d.contact[i]
        if obj not in (c.geom1,c.geom2):continue
        force=np.zeros(6);mujoco.mj_contactForce(sim.m,sim.d,i,force);other=c.geom2 if c.geom1==obj else c.geom1;name=mujoco.mj_id2name(sim.m,mujoco.mjtObj.mjOBJ_GEOM,int(other))
        if force[0]>.005:out.append((name,float(force[0]),float(c.dist)))
    return out
def execute(sim,p,size=.036,mass=.06,xy=(.4,0),render=False):
    object_est=initialize(sim,size,mass,xy);samples=[];phase=''
    def run(label,seconds):
        nonlocal phase
        phase=label
        for i in range(round(seconds/.002)):
            sim.step()
            if i%50==0:samples.append(dict(phase=label,time=float(sim.d.time),object=sim.d.xpos[sim.object_id].tolist(),palm=sim.d.site_xpos[sim.palm_id].tolist(),contacts=contacts(sim)))
    # Raise first, then approach with downward palm; no object pose writes follow initialization.
    palm=sim.d.site_xpos[sim.palm_id].copy();palm[2]=.90;sim.solve_ik(palm);run('raise',1.5)
    goal=object_est+np.array([p[0],p[1],size/2+p[2]+.15]);ik=sim.solve_ik(goal,R_DOWN)
    if not ik['success']:return dict(success=False,reason='approach_ik',ik=ik)
    run('approach',2)
    goal[2]-=.15;ik=sim.solve_ik(goal,R_DOWN)
    if not ik['success']:return dict(success=False,reason='descend_ik',ik=ik)
    run('descend',2)
    q={}
    for finger in ('index','middle','ring','pinky'):
        for suffix,val in zip(('mcp_flexion','pip','dip'),p[3:6]):q[finger+'_'+suffix]=float(val)
    q.update(thumb_cmc_opposition=float(p[6]),thumb_cmc_flexion=float(p[7]),thumb_mcp_flexion=float(p[8]),thumb_ip=float(p[9]))
    sim.set_targets(q);run('close',1.8);before=sim.d.xpos[sim.object_id].copy();close_contacts=contacts(sim)
    goal[2]+=.15;ik=sim.solve_ik(goal,R_DOWN);run('lift',2.5);run('hold',1.5)
    after=sim.d.xpos[sim.object_id].copy();hold=[x for x in samples if x['phase']=='hold'];handfraction=sum(any(c[0]!='worktable' for c in x['contacts']) for x in hold)/len(hold)
    lift=float(after[2]-(.600+size/2));success=lift>.10 and handfraction>.8
    result=dict(success=success,params=list(map(float,p)),size_m=size,mass_kg=mass,xy=list(xy),lift_m=lift,hand_contact_fraction=handfraction,close_contacts=close_contacts,final_contacts=contacts(sim),before=before.tolist(),after=after.tolist(),samples=samples)
    return result
if __name__=='__main__':
    sim=runtime.ArmSimulation()
    for p in [[-.024,0,.021,1.15,1.35,.9,1,.8,.85,.65],[-.035,0,.022,1.4,1.6,1.3,1.3,.5,.7,.7],[-.020,0,.017,1.4,1.5,1.1,1.3,.6,.8,.6]]:
        r=execute(sim,p);print(json.dumps({k:v for k,v in r.items() if k!='samples'}),flush=True)
        (OUT/f"trial_{int(time.time()*1000)}.json").write_text(json.dumps(r,indent=2))
    sim.close()
