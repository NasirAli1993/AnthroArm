"""Reproducible physical trials. Ground-truth object state is used only for scoring."""
from pathlib import Path
import sys, json, time
import numpy as np
import mujoco
sys.path.insert(0, str(Path(__file__).parent))
from experiment import initialize, runtime, OUT
from controller import LearnedGraspController, object_contacts, BASE

def trial(sim, size=.036, mass=.06, xy=(.4,0), parameters=None, estimated_error=(0,0,0), callback=None, estimate_provider=None):
    estimate = initialize(sim, size, mass, xy) + np.asarray(estimated_error)
    if estimate_provider is not None:
        estimate=np.asarray(estimate_provider(sim,size),dtype=float)
    actual_estimate_error=estimate-sim.d.xpos[sim.object_id].copy()
    controller = LearnedGraspController(sim, parameters=parameters)
    controller.start(estimate, size)
    samples=[]
    step=0
    obj_jid=mujoco.mj_name2id(sim.m,mujoco.mjtObj.mjOBJ_JOINT,'object_free')
    va=int(sim.m.jnt_dofadr[obj_jid])
    max_effort=0.;max_external=0.;max_joint_violation=0.
    while controller.active and step<13000:
        phase=controller.phase
        controller.step()
        step+=1
        max_effort=max(max_effort,float(np.max(abs(sim.d.actuator_force)/sim.effort)))
        max_external=max(max_external,float(np.max(abs(sim.d.qfrc_applied))),float(np.max(abs(sim.d.xfrc_applied))))
        q=sim.d.qpos[sim.qadr]
        max_joint_violation=max(max_joint_violation,float(np.max(np.maximum(sim.low-q,q-sim.high))))
        if step%50==0:
            pos=sim.d.xpos[sim.object_id].copy()
            palm=sim.d.site_xpos[sim.palm_id].copy()
            R=sim.d.site_xmat[sim.palm_id].reshape(3,3)
            samples.append(dict(phase=phase,time_s=float(sim.d.time),object_xyz_m=pos.tolist(),
              palm_xyz_m=palm.tolist(),object_in_palm_m=(R.T@(pos-palm)).tolist(),
              contacts=object_contacts(sim),object_speed_m_s=float(np.linalg.norm(sim.d.qvel[va:va+3]))))
        if callback is not None:
            callback(sim,controller,step)
    hold=[s for s in samples if s['phase']=='hold']
    release=[s for s in samples if s['phase']=='settle']
    supported=lambda s:any(c['geom']=='worktable' for c in s['contacts'])
    hand=lambda s:any(c['geom']!='worktable' for c in s['contacts'])
    lift=min([s['object_xyz_m'][2]-(.6+size/2) for s in hold],default=0.)
    contact_fraction=sum(hand(s) for s in hold)/max(len(hold),1)
    slip=max([np.linalg.norm(np.array(s['object_in_palm_m'])-hold[0]['object_in_palm_m']) for s in hold],default=0.)
    released=bool(release and all(supported(s) and not hand(s) and s['object_speed_m_s']<.03 for s in release[-5:]))
    max_penetration=max([c['penetration_m'] for s in samples for c in s['contacts']],default=0.)
    max_force=max([c['normal_force_n'] for s in samples for c in s['contacts']],default=0.)
    grasp=lift>.10 and contact_fraction>.9
    return dict(success=bool(grasp and released and max_effort<=1.00001 and max_external==0),
       grasp_success=bool(grasp),release_success=released,phase=controller.phase,error=controller.error,
       size_m=size,mass_kg=mass,xy=list(xy),estimate_error_m=list(estimated_error),parameters=controller.parameters.tolist(),
       object_estimate_xyz_m=estimate.tolist(),measured_initial_estimate_error_m=actual_estimate_error.tolist(),
       minimum_hold_lift_m=lift,hold_duration_s=len(hold)*.1,hold_hand_contact_fraction=contact_fraction,
       hold_slip_m=float(slip),max_effort_fraction=max_effort,max_external_force=max_external,
       mean_hold_normal_force_n=float(np.mean([sum(c['normal_force_n'] for c in s['contacts'] if c['geom']!='worktable') for s in hold])) if hold else 0.,
       max_joint_limit_violation_rad=max_joint_violation,max_contact_penetration_m=max_penetration,
       max_normal_contact_force_n=max_force,object_is_free=bool(sim.m.jnt_type[obj_jid]==mujoco.mjtJoint.mjJNT_FREE),
       equality_constraints=int(sim.m.neq),body_gravcomp_max=float(np.max(sim.m.body_gravcomp)),
       stages=controller.history,samples=samples)

if __name__=='__main__':
    sim=runtime.ArmSimulation()
    sizes=[.032,.034,.036,.038,.040,.042]
    rows=[]
    for size in sizes:
        r=trial(sim,size=size,parameters=BASE)
        rows.append(r)
        print(json.dumps({k:v for k,v in r.items() if k not in ('samples','stages')}),flush=True)
        (OUT/'size_probe.json').write_text(json.dumps(rows,indent=2))
    sim.close()
