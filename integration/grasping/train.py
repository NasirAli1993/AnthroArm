"""Fit an affine size-conditioned policy to successful contact-optimization demos.

This is supervised learning from a small synthetic dataset, not reinforcement
learning and not general-purpose robotic grasping. Held-out trials are run only
after the training dataset has been closed and coefficients saved.
"""
from pathlib import Path
import json, time, sys
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
from evaluate import trial, runtime, OUT
from controller import BASE, POLICY_PATH

def compact(row):
    return {k:v for k,v in row.items() if k not in ('samples','stages')}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    sim=runtime.ArmSimulation()
    training=[];demonstrations=[]
    sizes=[.032,.034,.036,.038,.040,.042]
    # Deterministic finite search about the first successful contact grasp.
    variants=[(0,0,1.),(0,0,.92),(0,0,.96),(-.002,0,.96),(.002,0,.96),(0,-.002,.96),(0,.002,.96)]
    for size in sizes:
        choices=[]
        for vi,(dx,dz,scale) in enumerate(variants):
            p=BASE.copy();p[0]+=dx;p[2]+=dz;p[3:]*=scale
            result=trial(sim,size=size,parameters=p)
            result['candidate']=vi
            result['objective']=float((100 if result['success'] else -100) - result['mean_hold_normal_force_n']*.05 - result['hold_slip_m']*1000 - result['max_contact_penetration_m']*500)
            training.append(result);choices.append(result)
            print(json.dumps(dict(stage='training',size=size,candidate=vi,success=result['success'],objective=result['objective'])),flush=True)
            (OUT/'training_progress.json').write_text(json.dumps([compact(r) for r in training],indent=2))
        best=max(choices,key=lambda row:row['objective'])
        if not best['success']:raise RuntimeError(f'No successful training grasp for {size}')
        demonstrations.append(best)
    X=np.array([[1.,(r['size_m']-.037)/.005] for r in demonstrations])
    Y=np.array([r['parameters'] for r in demonstrations])
    coefficients=np.linalg.lstsq(X,Y,rcond=None)[0]
    predictions=X@coefficients
    policy=dict(schema_version=1,algorithm='ordinary least squares affine regression',
      learned_outputs=['palm_x_offset_m','palm_y_offset_m','palm_clearance_m','finger_mcp_rad','finger_pip_rad','finger_dip_rad','thumb_opposition_rad','thumb_cmc_rad','thumb_mcp_rad','thumb_ip_rad'],
      size_domain_m=[.032,.042],size_center_m=.037,size_scale_m=.005,
      coefficients=coefficients.tolist(),training_examples=len(demonstrations),optimization_trials=len(training),
      training_parameter_rmse=np.sqrt(np.mean((predictions-Y)**2,axis=0)).tolist(),
      explanation='Actual regression fitted to six successful demonstration parameter vectors selected by contact simulation search. Only cube size conditions the grasp; world position is handled by IK. Stage timing and IK are scripted.')
    POLICY_PATH.write_text(json.dumps(policy,indent=2))
    (OUT/'training_demonstrations.json').write_text(json.dumps(demonstrations,indent=2))
    (OUT/'training_trials.json').write_text(json.dumps(training,indent=2))
    heldout=[]
    for i,size in enumerate([.033,.035,.037,.039,.041]):
        for repeat in range(2):
            xy=(.385+.03*repeat,(-1 if repeat==0 else 1)*(.012+.003*i))
            mass=.04+.02*repeat
            r=trial(sim,size=size,mass=mass,xy=xy)
            r['case_id']=f'heldout_{i}_{repeat}'
            heldout.append(r)
            print(json.dumps(dict(stage='heldout',id=r['case_id'],success=r['success'],lift=r['minimum_hold_lift_m'],error=r['error'])),flush=True)
            (OUT/'heldout_progress.json').write_text(json.dumps([compact(r) for r in heldout],indent=2))
    report=dict(schema_version=1,scope='Full 27-axis anatomical arm; free upright cubes on a known table; simulation only',
      algorithm=policy,training_successes=sum(r['success'] for r in training),training_trials=len(training),
      selected_demonstrations=[compact(r) for r in demonstrations],heldout_trials=len(heldout),
      heldout_successes=sum(r['success'] for r in heldout),heldout_results=[compact(r) for r in heldout],
      all_heldout_passed=all(r['success'] for r in heldout),
      no_constraints=all(r['equality_constraints']==0 for r in heldout),no_external_assistance=all(r['max_external_force']==0 and r['body_gravcomp_max']==0 for r in heldout),
      limitations=['The learned component is a small supervised grasp-parameter regressor, not an end-to-end neural or reinforcement policy.','Evaluation uses known cube size and supplied object-centre estimates; no inference of arbitrary shape.','Rigid convex CAD collision hulls and compliant MuJoCo contact do not represent deformable skin.','Contact forces and actuator saturation are logged; this is not hardware validated.','MuJoCo joint limits are compliant, so transient angular overshoot is measured rather than assumed zero.'])
    (OUT/'heldout_trajectories.json').write_text(json.dumps(heldout,indent=2))
    (OUT/'report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(dict(finished=True,passed=report['all_heldout_passed'],successes=report['heldout_successes'],trials=len(heldout))),flush=True)
    sim.close()

if __name__=='__main__':main()
