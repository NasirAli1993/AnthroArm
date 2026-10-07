"""Physics-only seeded grasp test. The object starts in an upward palm.
No object teleports, welds, or equality constraints occur after initial reset.
This measures grip retention and lift from the seeded grasp, not autonomous pickup.
"""
from pathlib import Path
import json
import numpy as np
import mujoco
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from model import ArmSimulation
ROOT=Path(__file__).resolve().parents[1]

def setup_seeded_grasp(sim):
    sim.reset()
    arm=[0,-.7,-.75,-.1207963268,0]
    sim.d.qpos[sim.qadr[:5]]=arm;sim.targets[:5]=arm;sim.d.ctrl[:]=sim.targets
    mujoco.mj_forward(sim.m,sim.d)
    bid=mujoco.mj_name2id(sim.m,mujoco.mjtObj.mjOBJ_BODY,'palm_base')
    jid=mujoco.mj_name2id(sim.m,mujoco.mjtObj.mjOBJ_JOINT,'object_free');adr=sim.m.jnt_qposadr[jid]
    R=sim.d.xmat[bid].reshape(3,3);pos=sim.d.xpos[bid]+R@np.array([.040,0,.074])
    sim.d.qpos[adr:adr+3]=pos;sim.d.qpos[adr+3:adr+7]=sim.d.xquat[bid]
    sim.d.qvel[:]=0;mujoco.mj_forward(sim.m,sim.d)
    return pos.tolist()

def run(save=True,frames=False):
    sim=ArmSimulation();initial=setup_seeded_grasp(sim);samples=[]
    def phase(name,seconds,command=None):
        if command:command()
        for k in range(round(seconds/.002)):
            sim.step()
            if k%50==0:
                state=sim.state();contacts=[c for c in state['contacts'] if 'object_geom' in [c['geom1'],c['geom2']]]
                tips=state['fingertip_positions'];samples.append(dict(phase=name,time=state['time'],object_position=state['object_position'],palm_position=state['palm_position'],object_contacts=contacts,pinch_gap_m=state['pinch_gap_m']))
        if frames:
            from PIL import Image
            Image.fromarray(sim.render(camera={'azimuth':140,'elevation':-15,'distance':1.5,'lookat':[-.25,0,.35]})).save(ROOT/'results'/('grasp_'+name+'.png'))
    phase('settle',.6)
    phase('close',1.8,lambda:sim.preset('fist'))
    before=np.array(sim.state()['object_position'])
    phase('lift',2.5,lambda:sim.set_targets({'joint_2_shoulder':-.3,'joint_3_elbow':-.55,'joint_4_wrist_pitch':.3}))
    phase('hold',2.)
    after=np.array(sim.state()['object_position']);last=[s for s in samples if s['phase']=='hold'];lastcontacts=[c for s in last for c in s['object_contacts']]
    handcontacts=[c for c in lastcontacts if c['geom1']!='floor' and c['geom2']!='floor']
    floorcontacts=[c for c in lastcontacts if 'floor' in [c['geom1'],c['geom2']]]
    lift=float(after[2]-before[2]);palmdistance=float(np.linalg.norm(after-np.array(sim.state()['palm_position'])))
    digits=['index','middle','ring','pinky','thumb']
    sampled_digits=[]
    for sample in last:
        active={finger for contact in sample['object_contacts'] if contact['normal_force']>.01 for finger in digits if any(str(contact[g]).startswith(finger+'_') for g in ['geom1','geom2'])}
        sampled_digits.append(active)
    sustained_fraction=sum(len(active)>=2 for active in sampled_digits)/max(1,len(sampled_digits))
    retained_digits=sorted(set().union(*sampled_digits))
    passed=lift>.04 and palmdistance<.12 and sustained_fraction>=.8 and not floorcontacts
    report=dict(passed=passed,test='Seeded palm grasp retention and lift; not autonomous pickup',initial_position=initial,pre_lift_position=before.tolist(),final_position=after.tolist(),vertical_lift_m=lift,final_object_palm_distance_m=palmdistance,finger_contact_digits=retained_digits,multi_digit_contact_fraction=sustained_fraction,retention_observation_seconds=2.0,hand_contact_samples=len(handcontacts),floor_contact_samples=len(floorcontacts),object_mass_kg=.06,gravity_compensation=False,object_pose_changed_only_at_initial_reset=True,weld_constraints=False,samples=samples)
    if save:(ROOT/'results'/'grasp_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2));sim.close();return report
if __name__=='__main__':
    import sys
    run(frames='--frames' in sys.argv)



