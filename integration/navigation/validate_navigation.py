"""Checks sensing, physical drive and exact sensor-only SLAM replay."""
from pathlib import Path
import os,sys,json,gzip
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
from navigation import NavigationSimulation,Slam2D,OUT,wrap

def main():
    checks={}
    sim=NavigationSimulation(seed=88)
    obs=sim.observe();angles=obs['angle_min']+np.arange(len(obs['ranges']))*obs['angle_increment']
    expected=[(0,5.2),(np.pi/2,4.3),(-np.pi/2,.7),(-np.pi,.8)]
    errors=[]
    for angle,distance in expected:
        index=np.argmin(np.abs(wrap(angles-angle)))
        errors.append(abs(float(obs['ranges'][index])-distance))
    checks['ray_sensor_against_known_test_fixture']={'passed':bool(max(errors)<.025),'four_cardinal_range_errors_m':errors,'note':'Expected wall distances are used only by this sensor test, never by mapping/control.'}
    initial=sim.evaluation_truth();sim.command(.2,0)
    for _ in range(40):sim.step(.1)
    travel=float(np.linalg.norm(sim.evaluation_truth()[:2]-initial[:2]));wheeltravel=float(np.linalg.norm(sim.odom[:2]))
    checks['contact_driven_wheel_motion']={'passed':bool(.5<travel<.9 and sim.collision_steps==0),'actual_travel_m':travel,'encoder_travel_m':wheeltravel,'command_m_s':.2,'duration_s':4,'note':'Free-joint chassis is moved by wheel actuators and ground contacts; no pose teleportation.'}
    sim.close()
    with gzip.open(OUT/'sensor_observations.json.gz','rt',encoding='utf-8') as stream:sensors=json.load(stream)
    trace=json.loads((OUT/'trajectory.json').read_text())
    allowed={'stamp','ranges','angle_min','angle_increment','range_min','range_max','encoder_delta','wheel_odometry','wheel_positions'}
    assert all(set(obs)<=allowed for obs in sensors),'Sensor log contains a non-sensor field'
    slam=Slam2D();maxerror=0.
    for index,obs in enumerate(sensors):
        obs['ranges']=np.array(obs['ranges']);obs['encoder_delta']=np.array(obs['encoder_delta'])
        pose=slam.update(obs)
        if index:
            error=float(np.max(np.abs(pose-np.array(trace[index-1]['estimate']))));maxerror=max(maxerror,error)
    saved=np.load(OUT/'measured_map.npz')
    exact_map=bool(np.array_equal(saved['logodds'],slam.logodds))
    checks['sensor_only_replay']={'passed':bool(maxerror<1e-10 and exact_map),'observation_count':len(sensors),'maximum_replayed_pose_component_error':maxerror,'occupancy_logodds_exactly_reproduced':exact_map,'input_fields':sorted(allowed),'note':'Replay receives no simulator, true pose, obstacle model or goal data.'}
    # A goal inside an observed occupied cell must be refused.
    occupied=np.argwhere(slam.occupancy()==100)
    target=slam.cell_to_world(occupied[len(occupied)//2][::-1])
    route=slam.plan(target,allow_unknown=False)
    checks['occupied_goal_rejected']={'passed':len(route)==0,'occupied_goal_m':target.tolist()}
    report={'passed':all(c['passed'] for c in checks.values()),'checks':checks}
    (OUT/'implementation_checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)
    return report['passed']

if __name__=='__main__':raise SystemExit(0 if main() else 1)
