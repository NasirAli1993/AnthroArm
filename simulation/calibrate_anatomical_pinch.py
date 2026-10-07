"""Calibrate an empty thumb-index pinch using CAD pad surface geometry.

This is a numerical preset solve. It is not motion planning or learned grasping.
"""
from pathlib import Path
import json
import numpy as np
import mujoco
from scipy.optimize import least_squares
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from model import ArmSimulation

ROOT=Path(__file__).resolve().parents[1]

def run():
    sim=ArmSimulation();data=mujoco.MjData(sim.m);data.qpos[:]=sim.d.qpos
    names=['index_mcp_abduction','index_mcp_flexion','index_pip','index_dip','thumb_cmc_opposition','thumb_cmc_flexion','thumb_mcp_flexion','thumb_ip']
    indices=np.array([sim.index[n] for n in names]);adr=sim.qadr[indices]
    bi=mujoco.mj_name2id(sim.m,mujoco.mjtObj.mjOBJ_BODY,'index_distal');bt=mujoco.mj_name2id(sim.m,mujoco.mjtObj.mjOBJ_BODY,'thumb_distal')
    # Native CAD ellipsoid support points on local +X palmar side, in metres.
    pi=np.array([.006524,0,.00918]);pt=np.array([.007384,0,.00765])
    prior=np.array([0,1.2,1.2,.5,1.4,.25,.15,.1])
    def residual(q):
        data.qpos[adr]=q;mujoco.mj_forward(sim.m,data)
        Ri=data.xmat[bi].reshape(3,3);Rt=data.xmat[bt].reshape(3,3)
        vi=data.xpos[bi]+Ri@pi;vt=data.xpos[bt]+Rt@pt
        ni=Ri[:,0];nt=Rt[:,0]
        return np.r_[vi-vt+.00010*ni,.010*(ni+nt),.00005*(q-prior)]
    low=sim.low[indices]+1e-5;high=sim.high[indices]-1e-5
    solutions=[]
    for seed in [prior,[.1,1.1,1.4,.2,1.5,.15,.2,.2],[-.2,1.35,1.,.2,1.55,.1,.3,.3],[.1,1.4,.5,.6,1.5,.1,.5,.1]]:
        r=least_squares(residual,np.clip(seed,low,high),bounds=(low,high),xtol=1e-12,ftol=1e-12,gtol=1e-12,max_nfev=800)
        solutions.append((float(np.linalg.norm(residual(r.x)[:3])),r.x.copy(),float(np.linalg.norm(residual(r.x)[3:6]))))
    solutions.sort(key=lambda row:row[0]+row[2])
    position_error,q,normal_error=solutions[0]
    out={'method':'Numerical pad-contact preset using native CAD support points and opposing palmar normals','targets':dict(zip(names,q.tolist())),'geometric_pad_alignment_error_m':position_error,'normal_residual':normal_error,'index_pad_local_surface_m':pi.tolist(),'thumb_pad_local_surface_m':pt.tolist(),'requires_dynamic_validation':True}
    (ROOT/'design'/'anatomical_pinch.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    sim.reset();sim.preset('pinch');sim.step(2000);state=sim.state()
    out['dynamic_surface_gap_m']=state['pinch_surface_gap_m'];out['dynamic_contacts']=[c for c in state['contacts'] if c['geom1']!='floor' and c['geom2']!='floor']
    out['requires_dynamic_validation']=False
    (ROOT/'design'/'anatomical_pinch.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps(out,indent=2));sim.close();return out

if __name__=='__main__':run()
