"""Measured v2 CAD identity, joint tracking and contact checks.

Run after building anatomical CAD and generate_model.py. Tests run with gravity,
bounded actuator effort, anatomical convex collision hulls and the normal runtime.
"""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
import numpy as np
import mujoco
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from model import ArmSimulation

ROOT=Path(__file__).resolve().parents[1]

def run():
    sim=ArmSimulation()
    report={'model':sim.spec['name'],'version':sim.spec['version'],'passed':False,
            'method':'Normal 2 ms MuJoCo integration with gravity, effort-limited servos and actuator bias feedforward; no external forces or body gravity cancellation.',
            'collision_model':sim.spec['collision_representation'],'checks':{},
            'limitations':['Digital model precision is not evidence of physical actuator accuracy.','CAD collision uses convex hulls per shell or pad, so a concavity can be filled.','Contacts intentionally prevent targets inside solid objects from being reached.','Mass/inertia remain conceptual estimates; hardware strength, tendon drive and tolerances need validation.']}
    checks=report['checks'];failures=[]
    def check(name,passed,**data):
        checks[name]=dict(passed=bool(passed),**data)
        if not passed:failures.append(name)
    manifest=json.loads((ROOT/'design'/'anatomical_manifest.json').read_text(encoding='utf-8-sig'))
    xml=ET.parse(ROOT/'simulation'/'robot.xml').getroot()
    meshfiles={x.attrib['file'] for x in xml.findall('./asset/mesh')}
    expected={'../design/'+x['file'] for x in manifest['components']}
    visible=[g for g in xml.findall('.//geom') if g.attrib.get('group')=='1']
    collision=[g for g in xml.findall('.//geom') if g.attrib.get('group')=='3']
    check('cad_mesh_identity',meshfiles==expected and len(visible)==len(manifest['components']) and all(g.attrib.get('type')=='mesh' and g.attrib.get('contype')=='0' for g in visible),visible_components=len(visible),collision_hulls=len(collision),mesh_files_match_manifest=meshfiles==expected,units='m',visible_geometry='Exact CAD STL meshes')
    check('bounded_controller',np.all(sim.m.body_gravcomp==0) and np.all(sim.m.actuator_forcelimited) and np.all(sim.m.jnt_actfrclimited[:25]) and np.all(sim.d.qfrc_applied==0),body_gravcomp_zero=bool(np.all(sim.m.body_gravcomp==0)),external_applied_forces_zero=bool(np.all(sim.d.qfrc_applied==0)),actuator_bias_feedforward=True,total_effort_limited=True)
    contacts=sim.state()['contacts'];deep=[c for c in contacts if c['distance']<-.00005]
    check('open_initial_collision_audit',not deep,contacts=len(contacts),penetrations_deeper_than_50um=deep)
    rows=[];max_effort=0
    for j in sim.joints:
        sim.reset();index=sim.index[j['name']]
        # Anatomically broad digits touch neighbors during isolated inward spread.
        # Use a 0.025 rad free-space spread perturbation for accuracy; full gesture
        # closure/contact behavior is audited separately below.
        desired=min(j['max']-.02,j['home']+(.025 if 'abduction' in j['name'] else .15))
        sim.set_targets({j['name']:desired})
        for _ in range(200):
            sim.step(10);max_effort=max(max_effort,float(np.max(np.abs(sim.d.actuator_force)/sim.effort)))
        state=sim.state();row=dict(joint=j['name'],command_rad=desired,measured_rad=float(sim.d.qpos[sim.qadr[index]]),error_deg=float(abs(state['joints'][index]['error_deg'])),palm_target_error_mm=state['precision']['palm_target_error_mm'],contacts=[c for c in state['contacts'] if c['geom1']!='floor' and c['geom2']!='floor'])
        rows.append(row)
    max_error=max(r['error_deg'] for r in rows);max_palm=max(r['palm_target_error_mm'] for r in rows)
    check('all_25_independent_joint_tracking',max_error<.25 and max_palm<.30 and max_effort<=1.00000001,max_joint_error_deg=max_error,max_palm_target_error_mm=max_palm,max_effort_fraction=max_effort,settle_seconds=4,acceptance_joint_deg=.25,acceptance_palm_mm=.30,results=rows)
    # Repeated deterministic positioning from different positions (rather than
    # repeating the same initial condition) tests the loaded closed-loop return.
    target=np.array([.15,.7,.4,-.9,.2]);returns=[];ik=[]
    for start in [[-.1,.3,.8,-.6,-.2],[.3,.9,-.1,.2,.4],[-.3,-.2,1.0,-.3,-.3]]:
        sim.reset();sim.set_targets(dict(zip(sim.names[:5],start)));sim.step(1500)
        sim.set_targets(dict(zip(sim.names[:5],target)));sim.step(2000)
        returns.append(sim.d.site_xpos[sim.palm_id].copy())
        xyz=sim.forward_kinematics(target)['position']
        ik.append({'goal':xyz,'measured':sim.d.site_xpos[sim.palm_id].tolist(),'error_mm':float(1000*np.linalg.norm(sim.d.site_xpos[sim.palm_id]-xyz))})
    repeat=max(float(1000*np.linalg.norm(a-b)) for a in returns for b in returns)
    check('loaded_cartesian_return_precision',repeat<.1 and max(x['error_mm'] for x in ik)<.3,repeatability_mm=repeat,trials=ik)
    presets=[]
    for name in ('open','fist','pinch','point','peace'):
        sim.reset();sim.preset(name);sim.step(2000)
        state=sim.state();q=sim.d.qpos[sim.qadr]
        violation=float(max(0,np.max(sim.low-q),np.max(q-sim.high)))
        robot_contacts=[c for c in state['contacts'] if c['geom1'] not in ('floor','object_geom') and c['geom2'] not in ('floor','object_geom')]
        presets.append(dict(name=name,finite=bool(np.isfinite(q).all()),joint_limit_violation_deg=float(np.degrees(violation)),max_effort_fraction=state['precision']['max_effort_fraction'],maximum_penetration_mm=float(-1000*min([0]+[c['distance'] for c in robot_contacts])),robot_contacts=robot_contacts,pinch_surface=state['pinch_surface'],endpoint_gap_mm=1000*state['pinch_gap_m']))
    check('gesture_contact_and_joint_limit_audit',all(r['finite'] and r['joint_limit_violation_deg']<1.15 and r['max_effort_fraction']<=1.00000001 and r['maximum_penetration_mm']<1.5 for r in presets),results=presets,contact_penetration_acceptance_mm=1.5)
    pinch=next(r for r in presets if r['name']=='pinch')
    pinch_contacts=[c for c in pinch['robot_contacts'] if any(str(c[g]).startswith('index_distal') for g in ('geom1','geom2')) and any(str(c[g]).startswith('thumb_distal') for g in ('geom1','geom2')) and c['normal_force']>.01]
    check('anatomical_thumb_index_pinch',abs(pinch['pinch_surface']['distance_m'])<.0015 and bool(pinch_contacts),pinch_surface=pinch['pinch_surface'],distal_contact_points=len(pinch_contacts),distal_contact_total_normal_force_N=sum(c['normal_force'] for c in pinch_contacts),endpoint_site_gap_mm=pinch['endpoint_gap_mm'],note='Closest collision surface gap, not centreline-tip distance. Actual nonzero thumb-index distal contact is required. Combined 0.4 mm contact margin permits positive near-zero gaps; this is not an object pickup.')
    report.update(passed=not failures,failed_checks=failures)
    (ROOT/'results'/'v2_precision.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='checks'},indent=2))
    for name,item in checks.items():print(name,item['passed'])
    sim.close();return report

if __name__=='__main__':
    report=run()
    raise SystemExit(0 if report['passed'] else 1)
