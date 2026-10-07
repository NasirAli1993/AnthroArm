"""Local V3 humanoid studio. Only a virtual robot is actuated."""
from pathlib import Path
import sys, os, json, time, threading, queue, io, math
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'simulation'/'v3'))
sys.path.append(str(ROOT/'simulation'))
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import numpy as np
import mujoco
from PIL import Image
from model import ArmSimulation
from vision_reach import VisionReach
from probe_camera import device_names

commands=queue.Queue(maxsize=128)
shared={'state':{},'frame':b'','vision':b'','error':''}
lock=threading.Lock()

def jpeg(rgb):
    b=io.BytesIO();Image.fromarray(np.asarray(rgb,dtype=np.uint8)).save(b,format='JPEG',quality=88);return b.getvalue()

class Webcam:
    """Local video in memory only. No recordings or external image transmission."""
    def __init__(self):
        self.thread=None;self.stop_event=threading.Event();self.frame=b''
        self.status={'enabled':False,'hand_detected':False,'frames':0,'error':'','recording':False}
        sources=device_names();virtual_only=bool(sources) and all('todesk' in name.lower() or 'virtual' in name.lower() for name in sources)
        self.status.update(registered_video_sources=sources,source_type='virtual' if virtual_only else 'unverified',physical_camera_verified=False,backend='DirectShow / MJPG',source_note='Only the ToDesk virtual camera is registered; a physical webcam feed has not been verified.' if virtual_only else 'Camera source must be verified by a visible live hand.')
        self.latest=None;self.last_detection=0
        self.guard=threading.RLock();self.generation=0
    def start(self):
        old=self.thread
        if old and old.is_alive():
            if not self.stop_event.is_set():return
            old.join(timeout=2.)
            if old.is_alive():raise RuntimeError('Previous webcam session is still releasing the device')
        with self.guard:
            self.generation+=1;generation=self.generation;event=threading.Event();self.stop_event=event
            self.latest=None;self.last_detection=0;self.frame=b''
            self.status.update(enabled=True,error='',hand_detected=False,frames=0)
            self.thread=threading.Thread(target=self.run,args=(generation,event),daemon=True);self.thread.start()
    def stop(self):
        with self.guard:
            self.generation+=1;self.stop_event.set()
            self.status.update(enabled=False,hand_detected=False)
            self.latest=None;self.last_detection=0;self.frame=b''
        if self.thread and self.thread.is_alive() and self.thread is not threading.current_thread():self.thread.join(timeout=1.)
    def sample(self):
        with self.guard:
            if self.stop_event.is_set() or not self.status['enabled'] or not self.status['hand_detected']:return None,0
            return dict(self.latest) if self.latest is not None else None,self.last_detection
    def run(self,generation,event):
        cap=None
        try:
            import cv2,mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            from webcam_teleop import Retargeter,landmark_targets,EDGES
            sources=device_names()
            virtual_only=bool(sources) and all('todesk' in name.lower() or 'virtual' in name.lower() for name in sources)
            with self.guard:
                if generation==self.generation:
                    self.status.update(registered_video_sources=sources,source_type='virtual' if virtual_only else 'unverified',physical_camera_verified=False,backend='DirectShow / MJPG',source_note='Only the ToDesk virtual camera is registered; a physical webcam feed has not been verified.' if virtual_only else 'Camera source must be verified by a visible live hand.')
            cap=cv2.VideoCapture(0,cv2.CAP_DSHOW)
            if not cap.isOpened():raise RuntimeError('Camera 0 is unavailable or in use')
            cap.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*'MJPG'))
            options=vision.HandLandmarkerOptions(base_options=python.BaseOptions(model_asset_path=str(ROOT/'models'/'hand_landmarker.task')),running_mode=vision.RunningMode.VIDEO,num_hands=1,min_hand_detection_confidence=.65,min_hand_presence_confidence=.65,min_tracking_confidence=.65)
            tracker=Retargeter();start=previous=time.monotonic();failures=0;unusable_frames=0
            with vision.HandLandmarker.create_from_options(options) as detector:
                while not event.is_set():
                    ok,frame=cap.read()
                    if event.is_set():break
                    if not ok:
                        failures+=1
                        if failures>15:raise RuntimeError('Camera stopped delivering frames')
                        time.sleep(.03);continue
                    failures=0;frame=cv2.flip(frame,1);now=time.monotonic()
                    if virtual_only:
                        gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
                        grayscale_fraction=float(np.mean((frame[:,:,0]==frame[:,:,1])&(frame[:,:,1]==frame[:,:,2])))
                        unusable=grayscale_fraction>.995 and float(np.std(gray,axis=1).mean())<2
                        unusable_frames=unusable_frames+1 if unusable else 0
                        if unusable_frames>=8:
                            raise RuntimeError('ToDesk virtual camera is returning blank/striped frames. Enable a real camera feed in ToDesk or connect a physical webcam, then restart camera control. Live hand tracking is not verified.')
                    result=detector.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,data=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)),int((now-start)*1000))
                    if event.is_set():break
                    detected=bool(result.hand_world_landmarks and result.hand_landmarks)
                    targets=None
                    status='Camera live | Show an open hand to begin'
                    if detected:
                        points=np.array([[p.x,p.y,p.z] for p in result.hand_world_landmarks[0]])
                        norm=np.array([[p.x,p.y,p.z] for p in result.hand_landmarks[0]])
                        try:
                            targets=tracker.targets(landmark_targets(points),now-previous)
                            h,w=frame.shape[:2];px=[(int(p[0]*w),int(p[1]*h)) for p in norm]
                            for a,b in EDGES:cv2.line(frame,px[a],px[b],(90,220,170),2)
                            for p in px:cv2.circle(frame,p,3,(30,150,255),-1)
                            status='Tracking 20 finger targets | Virtual hand only'
                        except ValueError:detected=False
                    previous=now
                    cv2.putText(frame,status,(12,25),cv2.FONT_HERSHEY_SIMPLEX,.53,(40,240,210),1)
                    encoded=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,85])[1].tobytes()
                    with self.guard:
                        if event.is_set() or generation!=self.generation:break
                        self.latest=targets if detected else None;self.last_detection=now if detected else 0;self.frame=encoded
                        self.status.update(hand_detected=detected,frames=self.status['frames']+1,width=frame.shape[1],height=frame.shape[0])
        except Exception as e:
            with self.guard:
                if generation==self.generation:self.status['error']=str(e)
        finally:
            if cap is not None:cap.release()
            with self.guard:
                if generation==self.generation:
                    self.status['enabled']=False;self.status['hand_detected']=False;self.latest=None;self.last_detection=0;self.frame=b''

webcam=Webcam()

def checked(obj):
    if not isinstance(obj,dict):raise ValueError('Expected command object')
    action=obj.get('action')
    if action not in ('reset','pause','demo','preset','targets','camera','layer','vision','webcam','ik'):raise ValueError('Unknown command')
    if action in ('pause','demo','vision','webcam') and not isinstance(obj.get('value'),bool):raise ValueError('value must be boolean')
    if action=='targets':
        if not isinstance(obj.get('targets'),dict):raise ValueError('Expected joint targets')
        for n,v in obj['targets'].items():
            if not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v):raise ValueError('Nonfinite target')
    if action=='layer' and obj.get('name') not in ('surface','joints','collision','inside'):raise ValueError('Unknown layer')
    if action=='camera':
        for k in ('distance','azimuth','elevation'):
            if k in obj and (not isinstance(obj[k],(int,float)) or isinstance(obj[k],bool) or not math.isfinite(obj[k])):raise ValueError('Invalid camera value')
        if 'lookat' in obj and (not isinstance(obj['lookat'],list) or len(obj['lookat'])!=3 or not all(isinstance(v,(int,float)) and math.isfinite(v) and abs(v)<5 for v in obj['lookat'])):raise ValueError('Invalid camera point')
    return obj

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def send(self,data,typ,status=200):
        self.send_response(status);self.send_header('Content-Type',typ);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers()
        try:self.wfile.write(data)
        except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):pass
    def do_GET(self):
        path=self.path.split('?')[0]
        if path in ('/','/index.html'):return self.send((ROOT/'dashboard'/'v3.html').read_bytes(),'text/html; charset=utf-8')
        if path=='/state':
            with lock:data=dict(shared['state'],server_error=shared['error'],webcam=dict(webcam.status))
            return self.send(json.dumps(data,allow_nan=False).encode(),'application/json')
        if path in ('/frame.jpg','/vision.jpg','/webcam.jpg'):
            with lock:data=webcam.frame if path=='/webcam.jpg' else shared['frame' if path=='/frame.jpg' else 'vision']
            if not data:data=jpeg(np.full((240,320,3),[17,26,30],dtype=np.uint8))
            return self.send(data,'image/jpeg')
        self.send(b'Not found','text/plain',404)
    def do_POST(self):
        if self.path!='/command':return self.send(b'Not found','text/plain',404)
        origin=self.headers.get('Origin','')
        if origin and origin not in ('http://127.0.0.1:8766','http://localhost:8766'):return self.send(b'Origin rejected','text/plain',403)
        try:
            n=int(self.headers.get('Content-Length',0))
            if not 0<n<=16384:raise ValueError('Invalid request size')
            commands.put_nowait(checked(json.loads(self.rfile.read(n))))
            self.send(b'{"queued":true}','application/json')
        except (ValueError,TypeError,OverflowError,RecursionError,queue.Full) as e:self.send(json.dumps({'error':str(e)}).encode(),'application/json',400)

def run():
    sim=ArmSimulation();vision=VisionReach(sim)
    renderer=mujoco.Renderer(sim.m,height=800,width=1000)
    option=mujoco.MjvOption();option.geomgroup[3]=0;option.geomgroup[4]=0
    camera=mujoco.MjvCamera();mujoco.mjv_defaultCamera(camera)
    camera.lookat[:]=[.25,0,.84];camera.distance=1.35;camera.azimuth=135;camera.elevation=-10
    server=ThreadingHTTPServer(('127.0.0.1',8766),Handler)
    (ROOT/'results'/'v3'/'server.pid').write_text(str(os.getpid()))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    paused=False;mode='manual';layer='surface';demo_start=0;last_stage=-1;ik={};tracking=False
    previous=time.monotonic();acc=0;last_frame=last_state=last_vision=0
    print('Human Arm V3 http://127.0.0.1:8766',flush=True)
    try:
        while True:
            now=time.monotonic();acc+=min(now-previous,.1);previous=now
            while not commands.empty():
                c=commands.get_nowait()
                try:
                    a=c['action']
                    if a in ('reset','targets','preset','demo','ik','vision'):
                        webcam.stop();tracking=False
                    if a in ('reset','targets','preset','demo','ik','webcam'):
                        vision.stop('Manual control selected');mode='manual';ik={};tracking=False
                    if a=='reset':sim.reset();paused=False
                    elif a=='pause':paused=c['value']
                    elif a=='demo':mode='demo' if c['value'] else 'manual';demo_start=float(sim.d.time);last_stage=-1;paused=False
                    elif a=='targets':sim.set_targets(c['targets'])
                    elif a=='preset':sim.preset(c['name'])
                    elif a=='ik':ik=sim.solve_ik(c['target'])
                    elif a=='webcam':
                        if c['value']:webcam.start();mode='webcam';sim.hold();paused=False
                        else:webcam.stop();sim.hold()
                    elif a=='vision':
                        if c['value']:mode='vision';paused=False;vision.start()
                        else:vision.stop('Stopped from studio');mode='manual';sim.hold()
                    elif a=='camera':
                        camera.azimuth=float(c.get('azimuth',camera.azimuth))%360
                        camera.elevation=max(-85,min(85,float(c.get('elevation',camera.elevation))))
                        camera.distance=max(.18,min(4,float(c.get('distance',camera.distance))))
                        if 'lookat' in c:camera.lookat[:]=c['lookat']
                    elif a=='layer':
                        layer=c['name'];option.geomgroup[1]=int(layer not in ('collision','inside'));option.geomgroup[3]=int(layer=='collision');option.geomgroup[4]=int(layer=='inside')
                        option.flags[mujoco.mjtVisFlag.mjVIS_JOINT]=layer=='joints'
                        option.flags[mujoco.mjtVisFlag.mjVIS_CONTACTPOINT]=layer=='collision'
                    with lock:shared['error']=''
                except Exception as e:
                    with lock:shared['error']=str(e)
            if mode=='demo':
                stage=int((float(sim.d.time)-demo_start)/4)%6
                if stage!=last_stage:sim.preset(['open','fist','open','pinch','point','peace'][stage]);last_stage=stage
            if mode=='webcam':
                targets,timestamp=webcam.sample()
                fresh=targets is not None and now-timestamp<.6
                if fresh:sim.set_targets(targets);tracking=True
                elif tracking:sim.hold();tracking=False
            if not paused:
                n=min(50,int(acc/sim.m.opt.timestep))
                if n:
                    if mode=='vision':vision.step(n)
                    else:sim.step(n)
                    acc-=n*sim.m.opt.timestep
            else:acc=0
            if now-last_state>.1:
                state=sim.state()
                vs=vision.state() if callable(vision.state) else vision.state
                state.update(ready=True,paused=paused,mode=mode,demo=mode=='demo',vision=vs,tracking_fresh=tracking,display_layer=layer,ik=ik,camera={'azimuth':camera.azimuth,'elevation':camera.elevation,'distance':camera.distance,'lookat':camera.lookat.tolist()})
                with lock:shared['state']=state
                if vision.latest_rgb is not None:
                    with lock:shared['vision']=jpeg(vision.latest_rgb)
                last_state=now
            if now-last_frame>.06:
                renderer.update_scene(sim.d,camera=camera,scene_option=option)
                renderer.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW]=False
                frame=jpeg(renderer.render())
                with lock:shared['frame']=frame
                last_frame=now
            time.sleep(.001)
    finally:webcam.stop();vision.close();renderer.close();server.shutdown()

if __name__=='__main__':run()
