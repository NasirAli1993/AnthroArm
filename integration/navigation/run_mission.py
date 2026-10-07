"""Run the sensor-driven survey, then held-out A* navigation missions."""
from pathlib import Path
import argparse,json,time,sys,os,gzip
sys.path.insert(0,str(Path(__file__).resolve().parent))
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFont
from navigation import NavigationSimulation,MissionRunner,Slam2D,OUT,XML,wrap

FONT=ImageFont.load_default(size=18)
SMALL=ImageFont.load_default(size=14)

def map_image(runner,size=(520,440),evaluation=False):
    slam=runner.slam;occ=slam.occupancy()
    rgb=np.zeros((*occ.shape,3),dtype=np.uint8);rgb[:]=[85,99,107]
    rgb[occ==0]=[224,233,229];rgb[occ==100]=[27,44,51]
    image=Image.fromarray(rgb[::-1]).resize(size,resample=Image.Resampling.NEAREST)
    draw=ImageDraw.Draw(image)
    def pixel(point):
        cell=slam.world_to_cell(point)
        return(float((cell[0]+.5)/occ.shape[1]*size[0]),float((occ.shape[0]-cell[1]-.5)/occ.shape[0]*size[1]))
    if len(runner.trace)>1:
        draw.line([pixel(row['estimate'][:2]) for row in runner.trace],fill='#119879',width=3)
        if evaluation:draw.line([pixel(row['evaluation_truth'][:2]) for row in runner.trace],fill='#d77b3f',width=1)
    if len(runner.path)>1:draw.line([pixel(p) for p in runner.path],fill='#5485d1',width=2)
    if runner.goal is not None:
        x,y=pixel(runner.goal);draw.ellipse((x-6,y-6,x+6,y+6),outline='#c34743',width=3)
    x,y=pixel(slam.pose[:2]);a=slam.pose[2]
    draw.ellipse((x-7,y-7,x+7,y+7),fill='#22bf99',outline='#093d39',width=2)
    draw.line((x,y,x+17*np.cos(a),y-17*np.sin(a)),fill='#093d39',width=3)
    return image

def video_frame(runner,playback_label='playback 5x'):
    canvas=Image.new('RGB',(1440,800),'#0d1a20');canvas.paste(Image.fromarray(runner.sim.render()).resize((960,720)),(0,60))
    draw=ImageDraw.Draw(canvas)
    draw.text((25,17),'PHYSICS + MEASURED LIDAR MAP',font=FONT,fill='#75e5c6')
    draw.text((650,20),f"Simulation time {runner.sim.data.time:.1f} s | {playback_label}",font=SMALL,fill='#c4d3d7')
    canvas.paste(map_image(runner,(445,380)),(978,75))
    draw.text((983,475),'Sensor map and estimated trajectory',font=FONT,fill='#d6e5e7')
    draw.text((983,511),'Gray: unseen   Dark: laser occupied',font=SMALL,fill='#aabfc6')
    draw.text((983,540),'Blue: A* route   Red: goal',font=SMALL,fill='#aabfc6')
    draw.text((983,585),runner.phase.replace('_',' ').upper(),font=FONT,fill='#75e5c6')
    draw.text((983,625),f'v={runner.sim.commanded[0]:.2f} m/s  yaw={runner.sim.commanded[1]:.2f} rad/s',font=SMALL,fill='#d6e5e7')
    draw.text((983,655),f'Environment contact steps: {runner.sim.collision_steps}',font=SMALL,fill='#d6e5e7')
    draw.text((28,780),'Separate mobile-base simulation. The humanoid arm is not mounted or validated on this chassis.',font=SMALL,fill='#bdcdd1')
    return np.array(canvas)

def save_map(runner,filename):
    canvas=Image.new('RGB',(1100,900),'#0d1a20');draw=ImageDraw.Draw(canvas)
    draw.text((35,22),'ONLINE LIDAR MAPPING + CLOSED-LOOP NAVIGATION',font=FONT,fill='#75e5c6')
    canvas.paste(map_image(runner,(1020,735),evaluation=True),(40,75))
    draw.text((40,832),'Teal: estimated trajectory | Orange: true pose (evaluation only) | Blue: planned path',font=SMALL,fill='#d5e0e4')
    draw.text((40,865),'Occupancy comes from simulated laser observations. Unknown cells remain gray.',font=SMALL,fill='#a5bac2')
    canvas.save(filename)

def run(seed=10,record=True,max_steps=650):
    started=time.perf_counter();runner=MissionRunner(seed=seed,render=record)
    writer=None
    if record:
        writer=cv2.VideoWriter(str(OUT/'navigation_demo.webm'),cv2.VideoWriter_fourcc(*'VP80'),10,(1440,800))
        if not writer.isOpened():raise RuntimeError('VP8 recording could not be opened')
    episodes=[];frame_count=0
    missions=[('mapping_east',[4.35,.10],True),('mapping_north',[4.35,3.50],True),('mapping_west',[.15,3.45],True),('mapping_loop',[.0,.0],True),('heldout_goal_1',[3.90,.15],False),('heldout_goal_2',[.25,3.35],False),('heldout_goal_3',[4.10,3.60],False)]
    try:
        for phase,goal,allow_unknown in missions:
            start_t=runner.sim.data.time;start_collisions=runner.sim.collision_steps;start_idx=len(runner.trace)
            runner.path=[];reached=False
            for k in range(max_steps):
                reached=runner.advance(goal,phase,allow_unknown)
                if writer and runner.sim.steps%5==0:
                    frame=video_frame(runner);writer.write(cv2.cvtColor(frame,cv2.COLOR_RGB2BGR));frame_count+=1
                    if frame_count==5:Image.fromarray(frame).save(OUT/'navigation_poster.png')
                if k%100==0:print(f'{phase} step={k} pose={np.round(runner.slam.pose,3)} goal_error={np.linalg.norm(runner.slam.pose[:2]-goal):.3f} map_points={len(runner.slam.cloud)}',flush=True)
                if reached:break
            for _ in range(5):
                runner.drive(0,0,phase+'_braking')
                if writer and runner.sim.steps%5==0:
                    frame=video_frame(runner);writer.write(cv2.cvtColor(frame,cv2.COLOR_RGB2BGR));frame_count+=1
            truth=runner.sim.evaluation_truth();rows=runner.trace[start_idx:]
            ep={'name':phase,'goal_map_xy_m':goal,'unknown_cells_allowed_in_plan':allow_unknown,'reached_estimated_tolerance':reached,'duration_s':float(runner.sim.data.time-start_t),'goal_error_estimated_m':float(np.linalg.norm(runner.slam.pose[:2]-goal)),'goal_error_true_m':float(np.linalg.norm(truth[:2]-goal)),'position_rmse_m':float(np.sqrt(np.mean([r['position_error_m']**2 for r in rows]))),'max_pose_error_m':float(max(r['position_error_m'] for r in rows)),'environment_contact_steps':runner.sim.collision_steps-start_collisions}
            ep['settled_speed_m_s']=float(np.linalg.norm(runner.sim.data.qvel[:2]))
            ep['passed']=bool(reached and ep['goal_error_true_m']<.28 and ep['environment_contact_steps']==0 and ep['settled_speed_m_s']<.025)
            episodes.append(ep);print(json.dumps(ep),flush=True)
            if phase=='mapping_loop':save_map(runner,OUT/'survey_map.png')
            if not reached:break
        save_map(runner,OUT/'navigation_map.png')
        rows=runner.trace
        position_errors=np.array([r['position_error_m'] for r in rows]);odom_errors=np.array([np.linalg.norm(np.array(r['wheel_odometry'])[:2]-np.array(r['evaluation_truth'])[:2]) for r in rows])
        navigation=[ep for ep in episodes if ep['name'].startswith('heldout')]
        checks={'sensor_based_mapping':{'passed':bool(len(runner.slam.cloud)>300 and runner.slam.update_count>100),'accepted_scan_matches':len(runner.slam.matches),'rejected_scan_matches':runner.slam.rejected,'map_points':len(runner.slam.cloud),'observed_cells':int(np.count_nonzero(runner.slam.occupancy()!=-1))},'localization':{'passed':bool(np.sqrt(np.mean(position_errors**2))<.18),'position_rmse_m':float(np.sqrt(np.mean(position_errors**2))),'position_max_error_m':float(position_errors.max()),'wheel_odometry_rmse_m':float(np.sqrt(np.mean(odom_errors**2))),'final_yaw_error_deg':float(np.rad2deg(abs(wrap(runner.slam.pose[2]-runner.sim.evaluation_truth()[2]))))},'heldout_goals':{'passed':bool(len(navigation)==3 and all(ep['passed'] for ep in navigation)),'episodes':navigation},'obstacle_contacts':{'passed':runner.sim.collision_steps==0,'physics_steps_in_contact':runner.sim.collision_steps,'pairs':list(runner.sim.collision_pairs)}}
        report={'passed':all(c['passed'] for c in checks.values()),'implementation':'Custom incremental scan-to-map ICP + differential-wheel odometry + log-odds occupancy + inflated-grid A* + feedback drive','scope':'Simulation only. Separate base. No mounted humanoid arm, ROS Nav2, graph optimization or global loop closure is claimed.','seed':seed,'simulated_duration_s':float(runner.sim.data.time),'wall_elapsed_s':time.perf_counter()-started,'sensor':{'beams':180,'max_range_m':runner.sim.max_range,'range_noise_std_m':.006,'scan_rate_hz':10,'odometry_scale_bias':1.008,'encoder_distance_noise_std_m':.00006},'initialization':'Local pose origin set at the known initial base pose; no later ground-truth correction.','controller_truth_access':'Ground truth used only after control for scoring and orange evaluation trace. Planning and SLAM use observations.','checks':checks,'episodes':episodes,'emergency_forward_stops':runner.emergency_stops,'planning_calls':runner.replans,'video':{'filename':'navigation_demo.webm' if writer else None,'frames':frame_count,'fps':10,'playback_simulation_speed':5}}
        (OUT/'navigation_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        (OUT/'trajectory.json').write_text(json.dumps(rows,separators=(',',':')),encoding='utf-8')
        with gzip.open(OUT/'sensor_observations.json.gz','wt',encoding='utf-8') as stream:json.dump(runner.sensor_log,stream,separators=(',',':'))
        np.savez_compressed(OUT/'measured_map.npz',logodds=runner.slam.logodds,occupancy=runner.slam.occupancy(),origin=runner.slam.origin,resolution=runner.slam.resolution)
        (OUT/'latest_state.json').write_text(json.dumps(runner.get_state()),encoding='utf-8')
        (Path(__file__).parent/'world.xml').write_text(XML,encoding='utf-8')
        print(json.dumps({'passed':report['passed'],'checks':checks,'wall_seconds':report['wall_elapsed_s']},indent=2),flush=True)
        return report
    finally:
        if writer:writer.release()
        runner.sim.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--seed',type=int,default=10);parser.add_argument('--no-video',action='store_true');parser.add_argument('--max-steps',type=int,default=650);args=parser.parse_args()
    result=run(args.seed,not args.no_video,args.max_steps)
    raise SystemExit(0 if result['passed'] else 1)
