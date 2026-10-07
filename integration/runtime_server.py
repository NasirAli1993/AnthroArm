"""Loopback-only simulated robot backend. No physical actuator interfaces."""
from pathlib import Path
import os, sys, time, json, math, queue, threading, base64, argparse
import mimetypes,urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from concurrent.futures import Future

ROOT = Path(__file__).resolve().parents[1]
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'): os.environ[key]='1'
os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'cache'/'matplotlib'))
os.environ.setdefault('PYTHONDONTWRITEBYTECODE','1')
sys.path.insert(0, str(ROOT/'simulation'/'v3'))
import numpy as np
import mujoco
import cv2
from model import ArmSimulation
from vision_reach import VisionReach
sys.path.insert(0,str(ROOT/'integration'/'grasping'))
from controller import LearnedGraspController, configure_episode
from vision import KnownSizeRGBDCamera


def validate_trajectory(names, points, joints):
    """Strict position trajectory contract; reject invalid commands atomically."""
    lookup={j['name']:j for j in joints}
    if not names or len(names)!=len(set(names)) or any(n not in lookup for n in names):
        raise ValueError('Unique known joint names are required')
    if not points or len(points)>2000: raise ValueError('Expected 1..2000 points')
    previous=0.; previous_q=None; clean=[]
    for p in points:
        t=float(p['time']); q=np.asarray(p['positions'],dtype=float)
        if not math.isfinite(t) or t<=previous or t>120: raise ValueError('Times must increase within 0..120 seconds')
        if q.shape!=(len(names),) or not np.isfinite(q).all(): raise ValueError('Invalid position vector')
        for k,n in enumerate(names):
            if not lookup[n]['min']<=q[k]<=lookup[n]['max']: raise ValueError('Joint limit: '+n)
            if previous_q is not None and abs(q[k]-previous_q[k])/(t-previous)>lookup[n]['velocity_limit']+1e-6:
                raise ValueError('Velocity limit: '+n)
        clean.append({'time':t,'positions':q.tolist()}); previous=t; previous_q=q
    return clean


class Runtime:
    def __init__(self):
        self.commands=queue.Queue(128); self.lock=threading.Lock(); self.ready=threading.Event()
        self.snapshot={}; self.frame=b''; self.camera={}; self.error=None; self.quit=False
        self.worker=threading.Thread(target=self.run,daemon=True); self.worker.start()
        if not self.ready.wait(60): raise RuntimeError('Simulation initialization timed out')
        if self.error: raise RuntimeError(self.error)
    def failure(self):
        return self.error or (None if self.worker.is_alive() else 'Simulation worker is not running')
    def request(self,command,timeout=30):
        if self.failure():raise RuntimeError(self.failure())
        future=Future(); self.commands.put_nowait((command,future)); return future.result(timeout)
    def run(self):
        sim=None; vision=None
        try:
            sim=ArmSimulation(); self.object_size=.036
            configure_episode(sim,size=self.object_size,mass=.06,x=.4,y=0.)
            vision=VisionReach(sim); self.sim=sim; self.vision=vision
            vision.camera.close();vision.camera=KnownSizeRGBDCamera(sim,self.object_size)
            self.trajectory=None; self.trajectory_id=0; self.task='idle'; self.result={}; self.grasp=None
            self.trajectory_state={'status':'idle'}; last_state=last_frame=last_camera=-100.
            self.ready.set()
            while not self.quit:
                begin=time.monotonic()
                for _ in range(16):
                    try: cmd,future=self.commands.get_nowait()
                    except queue.Empty: break
                    try: future.set_result(self.command(cmd))
                    except Exception as exc: future.set_exception(exc)
                if self.task=='vision_reach' and vision.active:
                    vision.step(10)
                    if not vision.active: self.result=vision.state; self.task='idle'
                elif self.task=='learned_grasp' and self.grasp is not None:
                    self.grasp.step(10)
                    if not self.grasp.state.get('active',False): self.result=self.grasp.state; self.task='idle'
                else:
                    self.advance_trajectory(); sim.step(10)
                now=float(sim.d.time)
                # Reset rewinds simulation time; invalidate all publication deadlines.
                if now < last_state:
                    last_state=last_frame=last_camera=-100.
                if now-last_state>=.04:
                    state=sim.state(); state.update(mode='SIMULATION_ONLY',task=self.task,task_result=self.result,trajectory=self.trajectory_state)
                    if self.grasp is not None and self.task=='learned_grasp': state['grasp']=self.grasp.state
                    with self.lock: self.snapshot=state
                    last_state=now
                if now-last_frame>=.20:
                    rgb=sim.render(960,720,camera={'azimuth':135,'elevation':-15,'distance':1.65,'lookat':[.20,0,.70]})
                    ok,jpg=cv2.imencode('.jpg',cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR),[cv2.IMWRITE_JPEG_QUALITY,82])
                    if ok:
                        with self.lock:self.frame=jpg.tobytes()
                    last_frame=now
                if now-last_camera>=1.:
                    detection=vision.camera.capture(); cam=vision.camera
                    rotation=sim.d.cam_xmat[cam.camera_id].reshape(3,3)@np.diag([1.,-1.,-1.])
                    quaternion=np.zeros(4);mujoco.mju_mat2Quat(quaternion,rotation.ravel())
                    ok,jpg=cv2.imencode('.jpg',cv2.cvtColor(cam.latest_rgb,cv2.COLOR_RGB2BGR))
                    camera={'time':now,'width':cam.width,'height':cam.height,'fx':cam.fx,'fy':cam.fy,'cx':cam.cx,'cy':cam.cy,
                            'frame_id':'vision_camera_optical','detection':detection,
                            'position':sim.d.cam_xpos[cam.camera_id].tolist(),'optical_quaternion_xyzw':quaternion[[1,2,3,0]].tolist(),
                            'jpeg':base64.b64encode(jpg.tobytes()).decode(),
                            'depth_f32':base64.b64encode(cam.latest_depth.astype('<f4').tobytes()).decode()}
                    with self.lock:self.camera=camera
                    last_camera=now
                time.sleep(max(0,.02-(time.monotonic()-begin)))
        except Exception as exc:
            self.error=repr(exc); self.ready.set()
            while True:
                try: _,future=self.commands.get_nowait()
                except queue.Empty: break
                if not future.done():future.set_exception(RuntimeError(self.error))
        finally:
            if vision:vision.close()
            if sim:sim.close()
    def stop(self):
        self.trajectory=None
        if self.vision.active:self.vision.stop()
        if self.grasp is not None and self.grasp.state.get('active',False):self.grasp.cancel()
        self.sim.hold();self.task='idle';self.trajectory_state={'status':'cancelled','id':self.trajectory_id}
    def command(self,c):
        op=c.get('op'); sim=self.sim
        if op=='stop':self.stop();return {'stopped':True}
        if op=='reset':
            self.stop();configure_episode(sim,size=self.object_size,mass=.06,x=.4,y=0.);self.grasp=None;self.result={}
            return {'reset':True,'known_object_size_m':self.object_size}
        if op=='trajectory':
            names=c['joint_names']; points=validate_trajectory(names,c['points'],sim.joints)
            initial=np.array([sim.d.qpos[sim.qadr[sim.index[n]]] for n in names])
            for i,n in enumerate(names):
                if abs(points[0]['positions'][i]-initial[i])/points[0]['time']>sim.speed[sim.index[n]]+1e-6:
                    raise ValueError('First segment exceeds velocity limit: '+n)
            self.stop();self.trajectory_id+=1
            self.trajectory={'names':names,'points':[{'time':0.,'positions':initial.tolist()}]+points,'started':float(sim.d.time)}
            self.trajectory_state={'status':'active','id':self.trajectory_id};self.task='trajectory'
            return self.trajectory_state
        if op=='ik':return sim.solve_ik(c['position'],c.get('rotation'),apply=False)
        if op=='vision_reach':self.stop();self.task='vision_reach';self.result={};return self.vision.start()
        if op=='learned_grasp':
            detection=self.vision.camera.capture()
            if not detection.get('detected'):raise ValueError('No visible RGB-D target')
            self.stop();self.grasp=LearnedGraspController(sim)
            self.grasp.start(detection['center_world_m'],object_size_m=self.object_size)
            self.task='learned_grasp';self.result={};return self.grasp.state
        raise ValueError('Unsupported command')
    def advance_trajectory(self):
        if self.trajectory is None:return
        tr=self.trajectory;elapsed=float(self.sim.d.time)-tr['started'];points=tr['points']
        if elapsed>=points[-1]['time']:
            self.sim.set_targets(dict(zip(tr['names'],points[-1]['positions'])))
            error=max(abs(self.sim.d.qpos[self.sim.qadr[self.sim.index[n]]]-q) for n,q in zip(tr['names'],points[-1]['positions']))
            if error<.01:
                self.trajectory_state={'status':'succeeded','id':self.trajectory_id,'max_error_rad':float(error)};self.trajectory=None;self.task='idle'
            elif elapsed>points[-1]['time']+5:
                self.stop();self.trajectory_state={'status':'failed','id':self.trajectory_id,'reason':'tracking timeout','max_error_rad':float(error)}
            return
        for a,b in zip(points,points[1:]):
            if a['time']<=elapsed<b['time']:
                alpha=(elapsed-a['time'])/(b['time']-a['time']);q=(1-alpha)*np.array(a['positions'])+alpha*np.array(b['positions'])
                self.sim.set_targets(dict(zip(tr['names'],q)));return


class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def send(self,data,kind='application/json',status=200):
        payload=data if isinstance(data,bytes) else json.dumps(data,allow_nan=False).encode()
        self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(payload)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(payload)
    def do_GET(self):
        rt=self.server.runtime;path=self.path.split('?')[0]
        if path=='/health':return self.send({'ready':bool(rt.snapshot) and not rt.failure(),'error':rt.failure(),'mode':'SIMULATION_ONLY'})
        if path in ('/state','/camera','/frame.jpg') and rt.failure():
            return self.send({'error':rt.failure(),'mode':'SIMULATION_ONLY'},status=503)
        if path=='/state':
            with rt.lock:data=rt.snapshot
            return self.send(data)
        if path=='/camera':
            with rt.lock:data=rt.camera
            return self.send(data)
        if path=='/frame.jpg':
            with rt.lock:data=rt.frame
            return self.send(data,'image/jpeg')
        if path=='/':return self.send((ROOT/'integration'/'dashboard.html').read_bytes(),'text/html; charset=utf-8')
        if path.startswith('/artifacts/'):
            base=(ROOT/'results'/'integration').resolve();file=(base/path.removeprefix('/artifacts/')).resolve()
            if file.is_relative_to(base) and file.is_file():return self.send(file.read_bytes(),mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
            return self.send({'error':'not found'},status=404)
        if path in ('/mobile/state','/mobile/frame.jpg','/mobile/map.png'):
            try:
                with urllib.request.urlopen('http://127.0.0.1:8771'+path.removeprefix('/mobile'),timeout=4) as response:
                    return self.send(response.read(),response.headers.get('Content-Type','application/json'))
            except Exception:return self.send({'error':'Navigation backend is not running'},status=503)
        return self.send({'error':'not found'},status=404)
    def do_POST(self):
        try:
            length=int(self.headers.get('Content-Length',0))
            if not 0<length<=1024*1024:raise ValueError('Invalid request size')
            command=json.loads(self.rfile.read(length))
            if self.path=='/mobile/command':
                request=urllib.request.Request('http://127.0.0.1:8771/command',json.dumps(command).encode(),{'Content-Type':'application/json'},method='POST')
                with urllib.request.urlopen(request,timeout=30) as response:return self.send(response.read())
            if self.server.runtime.failure():return self.send({'error':self.server.runtime.failure()},status=503)
            return self.send(self.server.runtime.request(command))
        except Exception as exc:return self.send({'error':str(exc)},status=400)


def main():
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8770);args=p.parse_args()
    runtime=Runtime();server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);server.runtime=runtime
    print('Simulation runtime http://127.0.0.1:%d'%args.port,flush=True)
    try:server.serve_forever()
    finally:runtime.quit=True;runtime.worker.join(5)
if __name__=='__main__':main()
