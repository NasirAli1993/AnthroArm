"""Solve V3 pinch against the actual inset-pad convex CAD surfaces."""
from pathlib import Path
import importlib.util,json
import numpy as np,mujoco
from scipy.optimize import least_squares
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('v3runtime',Path(__file__).with_name('model.py'));runtime=importlib.util.module_from_spec(s);s.loader.exec_module(runtime)
def run():
    sim=runtime.ArmSimulation();data=mujoco.MjData(sim.m);data.qpos[:]=sim.d.qpos
    names=['index_mcp_abduction','index_mcp_flexion','index_pip','index_dip','thumb_cmc_opposition','thumb_cmc_flexion','thumb_mcp_flexion','thumb_ip'];idx=np.array([sim.index[n] for n in names]);adr=sim.qadr[idx]
    prior_dict=json.loads((ROOT/'design'/'anatomical_pinch.json').read_text())['targets'];prior=np.array([prior_dict[n] for n in names]);low=sim.low[idx]+1e-6;high=sim.high[idx]-1e-6
    a=mujoco.mj_name2id(sim.m,mujoco.mjtObj.mjOBJ_GEOM,'index_distalInsetPad_collision');b=mujoco.mj_name2id(sim.m,mujoco.mjtObj.mjOBJ_GEOM,'thumb_distalInsetPad_collision')
    def residual(q):
        data.qpos[adr]=q;mujoco.mj_forward(sim.m,data);gap=mujoco.mj_geomDistance(sim.m,data,a,b,.2,None)
        return np.r_[10*(gap+.00025),.0001*(q-prior)]
    r=least_squares(residual,np.clip(prior,low,high),bounds=(low,high),max_nfev=600,xtol=1e-11,ftol=1e-11,gtol=1e-11)
    report={'targets':dict(zip(names,r.x.tolist())),'method':'Closest distance between actual V3 inset-pad convex CAD surfaces; small commanded compression; effort limits and collision solver retained'}
    path=ROOT/'design'/'v3'/'anatomical_pinch.json';path.write_text(json.dumps(report,indent=2));sim.preset('pinch');sim.step(2000);state=sim.state()
    contacts=[c for c in state['contacts'] if any(str(c[g]).startswith('index_distal') for g in ('geom1','geom2')) and any(str(c[g]).startswith('thumb_distal') for g in ('geom1','geom2')) and c['normal_force']>.01]
    report.update(passed=bool(contacts),actual_surface_gap_m=state['pinch_surface_gap_m'],contacts=contacts,contact_location='Distal flexor shell convex hulls',limitation='Convex shell hulls fill the inset pad pockets. Fingertip contact is demonstrated; isolated rubber-pad deformation/contact is not.');path.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sim.close();return report
if __name__=='__main__':run()
