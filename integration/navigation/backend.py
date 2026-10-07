"""Local HTTP transport for the real MuJoCo navigation process (port 8771)."""
from pathlib import Path
import os,sys,json,time,threading,queue,math,io,argparse
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
sys.path.insert(0,str(Path(__file__).resolve().parent))
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
import numpy as np
from PIL import Image
from navigation import MissionRunner,OUT,wrap
from run_mission import map_image,video_frame

SURVEY=[('mapping_east',[4.35,.10],True),('mapping_north',[4.35,3.50],True),('mapping_west',[.15,3.45],True),('mapping_loop',[0.,0.],True),('heldout_goal_1',[3.90,.15],False),('heldout_goal_2',[.25,3.35],False),('heldout_goal_3',[4.1,3.60],False)]

class Backend:
    def __init__(self,speed=2):
        self.speed=speed;self.lock=threading.Lock();self.commands=queue.Queue();self.state={'ready':False};self.jpeg=b'';self.map_png=b'';self.running=True;self.ident=0
        self.thread=threading.Thread(target=self.work,daemon=True);self.thread.start()
    def command(self,command):
        op=command.get('op');allowed=('mission','goal','cmd_vel','stop','reset')
        if op not in allowed:raise ValueError('op must be '+', '.join(allowed))
        if op=='goal':
            goal=command.get('goal',[])
            if len(goal)!=2 or not all(isinstance(n,(int,float)) and math.isfinite(n) for n in goal):raise ValueError('goal must be two finite map coordinates')
            if command.get('yaw') is not None and not math.isfinite(command['yaw']):raise ValueError('yaw must be finite')
        if op=='cmd_vel':
            if not all(isinstance(command.get(k),(int,float)) and math.isfinite(command[k]) for k in ('v','w')):raise ValueError('cmd_vel needs finite v and w')
            if abs(command['v'])>.4 or abs(command['w'])>1.5:raise ValueError('velocity exceeds simulated base limits')
        with self.lock:self.ident+=1;identifier=self.ident
        self.commands.put((identifier,command))
        return {'accepted':True,'id':identifier,'simulation_only':True}
    def work(self):
        runner=MissionRunner(render=True);mode='idle';task={'id':0,'status':'idle'};goals=[];index=0;goal=None;yaw=None;manual=(0.,0.);manual_expiry=0;steps=0;braking=0;progress=[]
        try:
            while self.running:
                started=time.monotonic()
                while not self.commands.empty():
                    ident,cmd=self.commands.get();op=cmd['op']
                    if op in ('reset','mission'):
                        runner.sim.close();runner=MissionRunner(render=True);progress=[];index=0
                    braking=0
                    if op=='mission':goals=SURVEY;mode='mission';goal=None;task={'id':ident,'status':'running','operation':'mission','completed_goals':0}
                    elif op=='goal':mode='goal';goal=np.array(cmd['goal']);yaw=cmd.get('yaw');runner.path=[];task={'id':ident,'status':'running','operation':'goal','goal':list(goal)}
                    elif op=='cmd_vel':mode='manual';manual=(cmd['v'],cmd['w']);manual_expiry=time.monotonic()+.6;task={'id':ident,'status':'running','operation':'cmd_vel'}
                    elif op=='stop':mode='idle';task={'id':ident,'status':'cancelled','operation':'stop'}
                    else:mode='idle';task={'id':ident,'status':'idle','operation':'reset'}
                    steps=0
                if mode=='mission':
                    phase,target,unknown=goals[index]
                    if braking:
                        runner.drive(0,0,phase+'_braking');braking-=1
                        if not braking:
                            truth=runner.sim.evaluation_truth();result={'name':phase,'estimated_goal_error_m':float(np.linalg.norm(runner.slam.pose[:2]-target)),'evaluation_goal_error_m':float(np.linalg.norm(truth[:2]-target)),'contacts':runner.sim.collision_steps,'settled_speed_m_s':float(np.linalg.norm(runner.sim.data.qvel[:2]))};progress.append(result)
                            index+=1;steps=0;runner.path=[];task['completed_goals']=index
                            if index==len(goals):
                                mode='idle';task['status']='succeeded';task['results']=progress
                                (OUT/'live_backend_mission.json').write_text(json.dumps({'task':task,'contacts':runner.sim.collision_steps,'true_pose_used_only_for_results':True},indent=2),encoding='utf-8')
                    else:
                        if runner.advance(target,phase,unknown):braking=5
                        steps+=1
                        if steps>650:mode='idle';task['status']='failed';task['reason']='Goal did not converge within 65 simulated seconds'
                elif mode=='goal':
                    if braking:
                        runner.drive(0,0,'goal_braking');braking-=1
                        if not braking:mode='idle';task['status']='succeeded';task['estimated_goal_error_m']=float(np.linalg.norm(runner.slam.pose[:2]-goal))
                    elif np.linalg.norm(runner.slam.pose[:2]-goal)<.15:
                        if yaw is not None and abs(wrap(yaw-runner.slam.pose[2]))>.08:runner.drive(0,float(np.clip(2*wrap(yaw-runner.slam.pose[2]),-1,1)),'goal_heading')
                        else:braking=5
                    else:
                        runner.advance(goal,'requested_goal',False)
                    steps+=1
                    if steps>650:mode='idle';task['status']='failed';task['reason']='Goal is blocked, unobserved or did not converge'
                elif mode=='manual':
                    if time.monotonic()>manual_expiry:manual=(0.,0.);mode='idle';task['status']='watchdog_stopped'
                    runner.drive(*manual,'manual_cmd_vel')
                else:runner.drive(0,0,'idle')
                state=runner.get_state();state.update({'ready':True,'mode':mode,'task':dict(task),'simulation_only':True,'arm_mounted':False,'environment_contact_steps':runner.sim.collision_steps,'wheel_twist':{'linear_x':float(runner.observation['encoder_delta'][0]/.1),'angular_z':float(runner.observation['encoder_delta'][2]/.1)}})
                if runner.sim.steps%5==0 or not self.jpeg:
                    frame=video_frame(runner,playback_label=f'live target {self.speed:g}x');buf=io.BytesIO();Image.fromarray(frame).save(buf,format='JPEG',quality=85);jpeg=buf.getvalue();buf=io.BytesIO();map_image(runner).save(buf,format='PNG');png=buf.getvalue()
                    with self.lock:self.jpeg=jpeg;self.map_png=png
                with self.lock:self.state=state
                # Bound memory for long-running live servers; batch CLI retains full logs.
                if len(runner.trace)>4000:runner.trace=runner.trace[-3500:]
                if len(runner.sensor_log)>4000:runner.sensor_log=runner.sensor_log[-3500:]
                time.sleep(max(0,.1/self.speed-(time.monotonic()-started)))
        except Exception as exc:
            import traceback
            traceback.print_exc()
            with self.lock:self.state={'ready':False,'error':str(exc)}
        finally:runner.sim.close()

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*_):pass
    def reply(self,status,body,kind='application/json'):
        if kind=='application/json':body=json.dumps(body,allow_nan=False).encode()
        self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
    def do_GET(self):
        with self.server.backend.lock:
            if self.path=='/state':return self.reply(200,self.server.backend.state)
            if self.path=='/frame.jpg':return self.reply(200,self.server.backend.jpeg,'image/jpeg')
            if self.path=='/map.png':return self.reply(200,self.server.backend.map_png,'image/png')
        self.reply(404,{'error':'Use /state, /frame.jpg, /map.png or POST /command'})
    def do_POST(self):
        try:
            if self.path!='/command':return self.reply(404,{'error':'Unknown endpoint'})
            length=int(self.headers.get('Content-Length','0'))
            if length>8192:raise ValueError('Command too large')
            command=json.loads(self.rfile.read(length));self.reply(200,self.server.backend.command(command))
        except Exception as exc:self.reply(400,{'error':str(exc)})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8771);parser.add_argument('--speed',type=float,default=2);args=parser.parse_args()
    backend=Backend(args.speed);server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);server.backend=backend
    print(f'SIMULATION ONLY navigation backend http://127.0.0.1:{args.port}',flush=True)
    try:server.serve_forever()
    finally:backend.running=False;backend.thread.join(5);server.server_close()
