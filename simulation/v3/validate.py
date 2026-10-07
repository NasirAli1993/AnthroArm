"""V3 final-model structure, loaded actuation, and three RGB-D autonomous trials."""
from pathlib import Path
import importlib.util,json,sys
import numpy as np,mujoco
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
runtime=load('v3runtime',Path(__file__).with_name('model.py'));vision=load('v3vision',Path(__file__).with_name('vision_reach.py'))

def run(model_path=None,provisional=False):
    sim=runtime.ArmSimulation(model_path);report={'model':sim.spec['name'],'version':'3.0','provisional':provisional,'passed':False,'checks':{},'limitations':['A simulated human-shaped upper limb, not a fabricated robot.','Camera autonomy is controlled-environment orange-cube approach and touch; autonomous pickup is not demonstrated.','Vision assumes calibrated fixed RGB-D camera and upright 50 mm orange cube on the known worktable.','Collision shapes are separate convex hulls; mass and motor parameters are conceptual.']};checks=report['checks']
    checks['degrees_of_freedom']={'passed':sim.m.nu==27,'arm':7,'hand':20,'actuators':sim.m.nu}
    sim.step(1500);initial=sim.state();bad=[c for c in initial['contacts'] if c['geom1']!='object_geom' and c['geom2']!='object_geom' and c['distance']<-.0001]
    checks['initial_clearance']={'passed':not bad,'deep_robot_contacts':bad,'steady_joint_error_deg':initial['precision']['joint_max_error_deg']}
    rows=[]
    for j in sim.joints:
        sim.reset();delta=.025 if 'abduction' in j['name'] and j['group']!='Arm' else .08 if j['group']=='Arm' else .15
        goal=min(j['max']-.01,j['home']+delta);sim.set_targets({j['name']:goal});sim.step(1800);state=sim.state();i=sim.index[j['name']]
        rows.append(dict(joint=j['name'],error_deg=abs(state['joints'][i]['error_deg']),effort_fraction=state['precision']['max_effort_fraction'],finite=bool(np.isfinite(sim.d.qpos).all())))
    checks['independent_27_axis_motion']={'passed':all(r['finite'] and r['error_deg']<.5 and r['effort_fraction']<=1.000001 for r in rows),'max_error_deg':max(r['error_deg'] for r in rows),'results':rows}
    checks['bounded_physics']={'passed':bool(np.all(sim.m.body_gravcomp==0) and np.all(sim.d.qfrc_applied==0) and np.all(sim.m.actuator_forcelimited)),'gravity_active':True,'actuator_bias_feedforward':True,'external_control_forces':False}
    gestures=[]
    for preset in ('open','fist','point','peace','pinch'):
        sim.reset();sim.preset(preset);sim.step(1800);state=sim.state();q=sim.d.qpos[sim.qadr]
        contacts=[c for c in state['contacts'] if 'object_geom' not in (c['geom1'],c['geom2'])]
        pinch_contacts=[c for c in contacts if any(str(c[g]).startswith('index_distal') for g in ('geom1','geom2')) and any(str(c[g]).startswith('thumb_distal') for g in ('geom1','geom2')) and c['normal_force']>.01]
        limit_error=float(np.degrees(max(0,np.max(sim.low-q),np.max(q-sim.high))))
        gestures.append(dict(preset=preset,finite=bool(np.isfinite(q).all()),joint_limit_violation_deg=limit_error,deepest_penetration_mm=-1000*min([0]+[c['distance'] for c in contacts]),pinch_contact_count=len(pinch_contacts),pinch_surface_gap_mm=1000*state['pinch_surface_gap_m']))
    checks['hand_articulation_and_fingertip_contact']={'passed':all(g['finite'] and g['joint_limit_violation_deg']<1 and g['deepest_penetration_mm']<1.5 for g in gestures) and gestures[-1]['pinch_contact_count']>0,'gestures':gestures,'pinch_contact_model':'Distal shell convex hulls. Inset rubber-pad deformation is not simulated.'}
    trials=[]
    for trial,(x,y) in enumerate([(.37,-.08),(.42,0),(.43,.075)]):
        sim.reset();joint=mujoco.mj_name2id(sim.m,mujoco.mjtObj.mjOBJ_JOINT,'object_free');address=sim.m.jnt_qposadr[joint]
        sim.d.qpos[address:address+3]=[x,y,.6255];mujoco.mj_forward(sim.m,sim.d);sim.step(300)
        # Ground truth is used solely here for assessment, not passed to controller.
        true_initial=sim.d.xpos[sim.object_id].copy();control=vision.VisionReach(sim);control.start()
        while control.active:control.step(50)
        state=control.state;estimate=np.asarray(state['target_estimate']) if state['target_estimate'] is not None else np.array([np.nan]*3);err=float(np.linalg.norm(estimate-true_initial))
        contact=bool(state['result'].get('success'));record=dict(trial=trial+1,configured_target_xy=[x,y],ground_truth_initial_for_scoring_m=true_initial.tolist(),camera_estimate_m=estimate.tolist(),estimation_error_mm=err*1000,success=contact and err<.008,control=state)
        trials.append(record)
        if not provisional:
            if control.initial_rgb is not None:Image.fromarray(control.initial_rgb).save(ROOT/'results'/'v3'/f'camera_trial_{trial+1}.png')
            np.save(ROOT/'results'/'v3'/f'depth_trial_{trial+1}.npy',control.initial_depth)
        control.close()
    checks['rgbd_autonomous_reach']={'passed':all(t['success'] for t in trials),'trials':trials,'ground_truth_used_for_control':False,'autonomous_pickup':False}
    # Negative vision case: geometry unchanged but target is blue, so no valid
    # orange observation can justify motion. This tests perception gating.
    sim.reset();geom=mujoco.mj_name2id(sim.m,mujoco.mjtObj.mjOBJ_GEOM,'object_geom');color=sim.m.geom_rgba[geom].copy();sim.m.geom_rgba[geom]=[.02,.12,.85,1]
    starting=sim.d.qpos[sim.qadr].copy();control=vision.VisionReach(sim);control.start()
    while control.active:control.step(50)
    travel=float(np.max(abs(sim.d.qpos[sim.qadr]-starting)))
    checks['vision_rejects_missing_target']={'passed':not control.result.get('success') and control.target is None and travel<.001,'result':control.result,'max_joint_motion_rad':travel,'test':'Blue target is outside the known orange detector; controller must hold.'}
    control.close();sim.m.geom_rgba[geom]=color
    report['passed']=all(c['passed'] for c in checks.values());report['failed_checks']=[k for k,c in checks.items() if not c['passed']]
    name='provisional_validation.json' if provisional else 'validation.json';(ROOT/'results'/'v3'/name).write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
    for name,c in checks.items():print(name,c['passed'])
    for t in trials:print('Vision trial',t['trial'],t['success'],'error mm',t['estimation_error_mm'],t['control']['phase'],t['control']['result'].get('reason',''))
    sim.close();return report
if __name__=='__main__':
    provisional='--provisional' in sys.argv
    r=run(ROOT/'simulation'/'v3'/'provisional.xml' if provisional else None,provisional)
    raise SystemExit(0 if r['passed'] else 1)
