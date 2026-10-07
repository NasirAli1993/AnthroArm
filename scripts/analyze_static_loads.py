"""Report gravity loads from the generated rigid-body model; no hardware rating."""
from pathlib import Path
import sys, json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'simulation'))
from model import ArmSimulation
import numpy as np
import mujoco
sim=ArmSimulation()
sim.d.qpos[sim.qadr]=0
sim.d.qpos[sim.qadr[1]]=np.pi/2
sim.d.qvel[:]=0
mujoco.mj_forward(sim.m,sim.d)
jac=np.zeros((3,sim.m.nv))
tip=mujoco.mj_name2id(sim.m,mujoco.mjtObj.mjOBJ_SITE,'middle_tip')
mujoco.mj_jacSite(sim.m,sim.d,jac,None,tip)
payload_mass=.06
payload_torque=jac.T@np.array([0,0,payload_mass*9.81])
rows=[]
for i in range(5):
    address=sim.vadr[i]
    rows.append({'joint':sim.joints[i]['name'],'robot_gravity_Nm':float(sim.d.qfrc_bias[address]),
                 'additional_60g_at_middle_tip_Nm':float(payload_torque[address]),
                 'simulation_effort_limit_Nm':sim.joints[i]['effort']})
report={'posture':'Upper arm, forearm and hand extended horizontally with shoulder pi/2; fixed base.',
        'notes':'Quasistatic model calculation. Assumed masses/inertias and actuator caps; no CAD density calibration or hardware certification. Payload is illustrative, not attached in this calculation.',
        'links':{x['name']:x['mass'] for x in sim.spec['links']},'arm_joints':rows}
(ROOT/'results'/'static_load_analysis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
text='GRAVITY LOADS FROM THE CURRENT SIMULATION MODEL\n\n'+report['posture']+'\n'+report['notes']+'\n\n'
for x in rows:
    text+=f"{x['joint']}: robot gravity {x['robot_gravity_Nm']:.3f} Nm; additional 60 g at extended middle fingertip {x['additional_60g_at_middle_tip_Nm']:.3f} Nm; configured simulator cap {x['simulation_effort_limit_Nm']:.1f} Nm.\n"
text+='\nThese numbers replace the document example for this model only. They omit acceleration loads, duty cycle, gearbox efficiency, transmission compliance, backlash, measured friction and component strength. They do not select or certify a physical motor.\n'
(ROOT/'docs'/'current_model_loads.txt').write_text(text,encoding='utf-8')
print(text)
