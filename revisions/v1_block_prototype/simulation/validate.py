"""Independent structural, kinematic, contact and dynamic acceptance checks."""
from pathlib import Path
import json, math
import xml.etree.ElementTree as ET
import numpy as np
import mujoco
from scipy.spatial.transform import Rotation
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from model import ArmSimulation
ROOT=Path(__file__).resolve().parents[1]

def run():
    sim=ArmSimulation();report={'model':sim.spec['name'],'checks':{},'limitations':['Rigid-body concept: not validated hardware or manufacturing release.','Position-only IK does not certify collision-free trajectories or arbitrary orientation.']}
    c=report['checks']
    urdf=ET.parse(ROOT/'design'/'robot.urdf').getroot();links={e.attrib['name']:e for e in urdf.findall('link')};edges=urdf.findall('joint');children=[e.find('child').attrib['link'] for e in edges]
    assert len(links)==26 and len(edges)==25 and len(set(children))==25
    roots=set(links)-set(children);assert roots=={'base_link'}
    visited=set(roots)
    while True:
        reached={e.find('child').attrib['link'] for e in edges if e.find('parent').attrib['link'] in visited}
        old=len(visited);visited|=reached
        if len(visited)==old:break
    assert visited==set(links)
    for e in edges:
        assert e.find('limit') is not None
    for link in sim.spec['links']:
        ii=link['inertia'];assert link['mass']>0 and min(ii)>0 and max(ii)<=sum(ii)-max(ii)+1e-12
    c['urdf_graph']={'passed':True,'links':26,'revolute_joints':25,'root':'base_link','positive_physical_inertias':True}
    # Independently reconstruct URDF world transforms; compare every link to MuJoCo.
    world={};err=0
    for link in sim.spec['links']:
        T=np.eye(4);T[:3,:3]=Rotation.from_euler('xyz',link['origin_rpy']).as_matrix();T[:3,3]=link['origin_xyz']
        j=link['joint']
        if j:
            J=np.eye(4);J[:3,:3]=Rotation.from_rotvec(np.array(j['axis'])*j['home']).as_matrix();T=T@J
        if link['parent']:T=world[link['parent']]@T
        world[link['name']]=T;bid=mujoco.mj_name2id(sim.m,mujoco.mjtObj.mjOBJ_BODY,link['name'])
        err=max(err,float(np.max(np.abs(T[:3,3]-sim.d.xpos[bid]))),float(np.max(np.abs(T[:3,:3]-sim.d.xmat[bid].reshape(3,3)))))
    assert err<1e-8;c['urdf_mjcf_frames']={'passed':True,'max_absolute_error':err}
    initial=sim.state()['contacts'];penetrations=[x for x in initial if x['distance']<-.00005]
    assert not penetrations,penetrations
    c['initial_contacts']={'passed':True,'count':len(initial),'penetrations_deeper_than_50_um':len(penetrations)}
    moves=[]
    for j in sim.joints:
        sim.reset();i=sim.index[j['name']];before=float(sim.d.qpos[sim.qadr[i]])
        delta_command=.075 if 'abduction' in j['name'] else .15;desired=min(j['max']-.001,before+delta_command);sim.set_targets({j['name']:desired});sim.step(900)
        actual=float(sim.d.qpos[sim.qadr[i]]);delta=abs(actual-before);error=abs(actual-desired)
        assert delta>delta_command*.45,(j['name'],delta,error)
        assert error<.06,(j['name'],delta,error)
        assert np.isfinite(sim.d.qpos).all() and np.isfinite(sim.d.qvel).all()
        assert abs(sim.d.time-1.8)<1e-8 and all(w.number==0 for w in sim.d.warning)
        assert all(abs(sim.d.actuator_force[k])<=jj['effort']+1e-8 for k,jj in enumerate(sim.joints))
        moves.append({'joint':j['name'],'movement_rad':delta,'steady_error_rad':error})
    c['independent_actuation']={'passed':True,'actuators':sim.m.nu,'joint_results':moves}
    presets=[]
    for name in ['open','fist','pinch','point','peace']:
        sim.reset();sim.preset(name);sim.step(1500)
        q=sim.d.qpos[sim.qadr];violation=float(max(0,np.max(sim.low-q),np.max(q-sim.high)))
        assert np.isfinite(q).all() and violation<.02
        assert abs(sim.d.time-3.0)<1e-8 and all(w.number==0 for w in sim.d.warning)
        assert all(abs(sim.d.actuator_force[k])<=jj['effort']+1e-8 for k,jj in enumerate(sim.joints))
        contacts=sim.state()['contacts'];deepest=min([x['distance'] for x in contacts]+[0])
        presets.append({'name':name,'max_joint_limit_violation_rad':violation,'contacts':len(contacts),'deepest_contact_m':deepest,'max_speed_rad_s':float(np.max(np.abs(sim.d.qvel[sim.vadr]))),'thumb_index_endpoint_gap_m':sim.state()['pinch_gap_m']})
    c['presets_finite_limits']={'passed':True,'results':presets}
    ik=[]
    for q in [[.15,.7,.4,-.9,0],[-.4,.6,1.1,-1.,.2],[.5,-.4,.9,.3,-.3],[0,.2,-.8,.6,0]]:
        sim.reset();xyz=sim.forward_kinematics(q)['position'];result=sim.solve_ik(xyz)
        assert result['success'] and result['error_m']<.002
        ik.append({'target':xyz,'error_m':result['error_m']})
    impossible=sim.solve_ik([5,0,5]);assert not impossible['success']
    c['position_ik']={'passed':True,'reachable_tests':ik,'unreachable_rejected':True}
    sim.reset();sim.step(2000);contacts=sim.state()['contacts'];ground=[x for x in contacts if set([x['geom1'],x['geom2']])==set(['floor','object_geom'])]
    assert len(ground)>0 and all(x['normal_force']>=0 for x in ground)
    total_force=sum(x['normal_force'] for x in ground);assert abs(total_force-.06*9.81)<.04
    c['object_contact_physics']={'passed':True,'normal_force_N':total_force,'expected_weight_N':.06*9.81,'contact_points':len(ground)}
    sim.close();report['passed']=True;(ROOT/'results'/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));return report
if __name__=='__main__':run()





