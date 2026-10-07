"""One continuous SLAM-observed wheel-docking and camera-contact grasp mission."""
from pathlib import Path
import sys,importlib.util,json
sys.path.insert(0,str(Path(__file__).parent))
import numpy as np,mujoco
from model import MobileSimulation,ROOT
from controller import LearnedGraspController,object_contacts
from vision import KnownSizeRGBDCamera
s=importlib.util.spec_from_file_location('mobile_navigation',ROOT/'integration/navigation/navigation.py');nav=importlib.util.module_from_spec(s);s.loader.exec_module(nav)
OUT=ROOT/'results/integration/mobile_manipulation'

def mission(callback=None,object_xy=(.4,0),start_x=-.6,report_name='report.json'):
    sim=MobileSimulation(object_xy,start_x);sim.brake();sim.step(800)
    initial=sim.truth();slam=nav.Slam2D();slam.update(sim.observe());route=[];phase='drive';step=0
    goal=np.array([-start_x,0.])
    try:
        for i in range(180):
            error=goal-slam.pose[:2];distance=np.linalg.norm(error)
            if distance<.009 and abs(slam.pose[2])<.04:break
            yaw=np.arctan2(error[1],error[0]) if distance>.025 else 0.
            yaw_error=nav.wrap(yaw-slam.pose[2])
            v=min(.16,distance*.85)*max(0.,np.cos(yaw_error));w=np.clip(2.5*yaw_error,-.7,.7)
            sim.command_drive(v,w);sim.step(50);step+=50
            pose=slam.update(sim.observe());route.append(dict(time_s=float(sim.d.time),estimated_pose=pose.tolist(),truth=sim.truth(),cmd_v=float(v),cmd_w=float(w)))
            if callback:callback(sim,'drive',step,slam)
        sim.brake()
        for _ in range(12):
            sim.step(50);step+=50
            if callback:callback(sim,'park',step,slam)
        parked=sim.truth();dock_error=float(np.linalg.norm(slam.pose[:2]-goal))
        if dock_error>.025:raise RuntimeError('Docking estimate did not converge: '+str(dock_error))
        sensor=KnownSizeRGBDCamera(sim,.036)
        try:
            detection=sensor.capture()
            if not detection['detected']:raise RuntimeError('No target visible after docking')
            import cv2
            cv2.imwrite(str(OUT/'detection_after_docking.png'),cv2.cvtColor(sensor.latest_rgb,cv2.COLOR_RGB2BGR))
        finally:sensor.close()
        est_error=float(np.linalg.norm(np.array(detection['center_world_m'])-sim.d.xpos[sim.object_id]))
        ctl=LearnedGraspController(sim);ctl.start(detection['center_world_m'],.036);samples=[]
        max_drift=0.;max_tilt=0.;max_external=0.
        while ctl.active and step<20000:
            current=ctl.phase;ctl.step();step+=1
            truth=sim.truth();max_drift=max(max_drift,float(np.linalg.norm(np.array(truth['xyz_m'])[:2]-parked['xyz_m'][:2])))
            max_tilt=max(max_tilt,truth['tilt_rad']);max_external=max(max_external,float(np.max(abs(sim.d.qfrc_applied))),float(np.max(abs(sim.d.xfrc_applied))))
            if step%50==0:
                cs=object_contacts(sim);samples.append(dict(time_s=float(sim.d.time),phase=current,object_xyz_m=sim.d.xpos[sim.object_id].tolist(),palm_xyz_m=sim.d.site_xpos[sim.palm_id].tolist(),contacts=cs,base_truth=truth))
                if callback:callback(sim,current,step,slam)
        hold=[r for r in samples if r['phase']=='hold'];settle=[r for r in samples if r['phase']=='settle']
        lift=min([r['object_xyz_m'][2]-.618 for r in hold],default=0.)
        held=bool(hold and all(any(c['geom']!='worktable' for c in r['contacts']) for r in hold))
        released=bool(settle and all(any(c['geom']=='worktable' for c in r['contacts']) and not any(c['geom']!='worktable' for c in r['contacts']) for r in settle[-5:]))
        result=dict(success=bool(lift>.1 and held and released and max_drift<.025),
          task='Continuous physical wheel docking, RGB-D detection, learned arm grasp/lift/hold/set-down/release',
          navigation='Local encoder-seeded 2-D lidar scan-to-map SLAM with direct dock controller on an unobstructed lane; not a combined obstacle-navigation benchmark',
          arm_ik_base_pose_source='Ideal simulated base pose and joint proprioception; object target comes only from RGB-D pixels',
          initial_base=initial,parked_base=parked,estimated_dock_error_m=dock_error,
          base_travel_m=float(np.linalg.norm(np.array(parked['xyz_m'])[:2]-initial['xyz_m'][:2])),
          max_base_drift_during_manipulation_m=max_drift,max_base_tilt_during_manipulation_deg=float(np.degrees(max_tilt)),
          minimum_hold_lift_m=lift,continuous_hold_contacts=held,release_success=released,
          camera_detection=detection,camera_estimate_error_m=est_error,
          max_arm_effort_fraction=sim.max_arm_effort,max_wheel_effort_fraction=sim.max_wheel_effort,
          max_applied_external_force=max_external,equality_constraints=int(sim.m.neq),
          base_free_joint=True,object_free_joint=True,brake='Encoder-position feedback through effort-bounded wheel velocity motors; no world constraint',
          cube_size_m=.036,cube_mass_kg=.06,chassis_mass_kg=80,column_mass_kg=6,track_m=.58,wheel_radius_m=.105,
          final_controller=ctl.state,route=route,samples=samples,
          limitations=['Heavy 80 kg chassis was selected for stability and differs from the standalone 3 kg navigation robot.','Straight docking lane only; the full navigation benchmark and combined manipulation are distinct tests.','Stationary calibrated external RGB-D camera and known upright cube size.','Arm IK uses ideal simulated base pose and joint proprioception, while base docking is controlled from the lidar-map estimate.','No learned whole-body locomotion policy or dynamic manipulation while driving.'])
        (OUT/report_name).write_text(json.dumps(result,indent=2));np.save(OUT/'occupancy_grid.npy',slam.occupancy())
        print(json.dumps({k:v for k,v in result.items() if k not in ('route','samples','camera_detection')},indent=2),flush=True)
        return result
    except Exception as exc:
        failure=dict(success=False,error=str(exc),initial_base=initial,latest_base=sim.truth(),route=route)
        (OUT/'failed_trial.json').write_text(json.dumps(failure,indent=2));raise
    finally:sim.close()

if __name__=='__main__':mission()
