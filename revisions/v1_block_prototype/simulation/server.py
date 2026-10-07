"""Local control desk for the MuJoCo arm. All HTTP access stays on loopback."""
from pathlib import Path
import sys, os
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'simulation'))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'cache'/'matplotlib'))
import json, time, threading, queue, io, math, socket, traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from PIL import Image
import mujoco
from model import ArmSimulation
from grasp_demo import setup_seeded_grasp

WEB = ROOT/'dashboard'
commands = queue.Queue(maxsize=128)
shared = {'state': {}, 'frame': b'', 'error': '', 'ready': False}
mutex = threading.Lock()
JOINT_NAMES = {x['joint']['name'] for x in json.loads((ROOT/'design'/'robot_spec.json').read_text(encoding='utf-8-sig'))['links'] if x.get('joint')}

def finite_number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(name+' must be a number')
    try: value = float(value)
    except (ValueError, OverflowError): raise ValueError(name+' must be finite')
    if not math.isfinite(value): raise ValueError(name+' must be finite')
    return value

def vector3(value, name, bound=2.):
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(name+' must contain three numbers')
    value = [finite_number(x, name) for x in value]
    if any(abs(x) > bound for x in value):
        raise ValueError(name+' is outside the supported workspace')
    return value

def checked_targets(value):
    if not isinstance(value, dict): raise ValueError('targets must map joint names to radians')
    unknown = set(value)-JOINT_NAMES
    if unknown: raise ValueError('Unknown joints: '+', '.join(sorted(unknown)))
    return {name:finite_number(angle, name) for name,angle in value.items()}

def checked_command(obj):
    if not isinstance(obj, dict): raise ValueError('Expected command object')
    action = obj.get('action')
    if action not in ('targets','preset','reset','pause','demo','grasp','teleop','ik','camera'):
        raise ValueError('Unknown command action')
    result = {'action':action}
    if action == 'targets': result['targets'] = checked_targets(obj.get('targets'))
    elif action == 'preset':
        if obj.get('name') not in ('open','fist','pinch','point','peace'): raise ValueError('Unknown preset')
        result['name'] = obj['name']
    elif action in ('pause','demo','teleop'):
        if not isinstance(obj.get('value'), bool): raise ValueError('value must be true or false')
        result['value'] = obj['value']
    elif action == 'ik': result['target'] = vector3(obj.get('target'), 'target')
    elif action == 'camera':
        for name in ('azimuth','elevation','distance'):
            if name in obj: result[name] = finite_number(obj[name], name)
        if 'lookat' in obj: result['lookat'] = vector3(obj['lookat'], 'lookat')
    return result

def checked_tracking(packet):
    if not isinstance(packet, dict): raise ValueError('Tracking packet must be an object')
    if 'timestamp' in packet:
        timestamp = finite_number(packet['timestamp'], 'timestamp')
        if abs(time.time()-timestamp) > 1.: raise ValueError('Tracking packet is stale')
    targets = checked_targets(packet.get('targets', packet))
    arm = None
    if 'arm_target' in packet:
        arm = vector3(packet['arm_target'], 'arm_target')
        if any(x < lo or x > hi for x,lo,hi in zip(arm, [.20,-.20,.30], [.52,.20,.70])):
            raise ValueError('arm_target is outside the relative webcam workspace')
    if not targets and arm is None: raise ValueError('Tracking packet has no targets')
    return targets, arm

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def send(self, body, content_type, status=200):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        try: self.wfile.write(body)
        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError): pass
    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/state':
            with mutex: payload = dict(shared['state'], server_error=shared['error'], ready=shared['ready'])
            self.send(json.dumps(payload, allow_nan=False).encode(), 'application/json')
        elif path == '/frame.jpg':
            with mutex: frame = shared['frame']
            self.send(frame, 'image/jpeg')
        elif path in ('/', '/index.html'):
            self.send((WEB/'index.html').read_bytes(), 'text/html; charset=utf-8')
        elif path == '/validation':
            p = ROOT/'results'/'validation.json'
            self.send(p.read_bytes() if p.exists() else b'{}', 'application/json')
        elif path == '/spec':
            self.send((ROOT/'design'/'robot_spec.json').read_bytes(), 'application/json')
        else: self.send(b'Not found', 'text/plain', 404)
    def do_POST(self):
        if self.path != '/command': return self.send(b'Not found', 'text/plain', 404)
        origin = self.headers.get('Origin', '')
        if origin and origin not in ('http://127.0.0.1:8765','http://localhost:8765'):
            return self.send(b'Origin rejected', 'text/plain', 403)
        try:
            length = int(self.headers.get('Content-Length', 0))
            if not 0 < length <= 16384: raise ValueError('Invalid payload size')
            obj = checked_command(json.loads(self.rfile.read(length)))
            commands.put_nowait(obj)
            self.send(b'{"queued":true}', 'application/json')
        except (ValueError, TypeError, OverflowError, RecursionError, queue.Full) as e:
            self.send(json.dumps({'error': str(e)}).encode(), 'application/json', 400)

def run():
    sim = ArmSimulation()
    m = sim.m
    d = sim.d
    renderer = mujoco.Renderer(m, height=800, width=1000)
    camera = mujoco.MjvCamera()
    mujoco.mjv_defaultCamera(camera)
    camera.lookat[:] = [0.20, 0, 0.37]
    camera.distance = 1.18
    camera.azimuth = 150
    camera.elevation = -12
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(('127.0.0.1', 5005))
    udp.setblocking(False)
    server = ThreadingHTTPServer(('127.0.0.1', 8765), Handler)
    (ROOT/'results'/'server.pid').write_text(str(os.getpid()))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    paused = False
    demo = True
    demo_start = float(d.time)
    grasp = False
    grasp_stage = -1
    grasp_start_z = 0
    last_stage = -1
    ik_status = {}
    teleop = False
    last_packet = 0
    last_arm_packet = 0
    tracking_was_fresh = False
    tracking_error = ''
    last_snapshot = 0
    last_frame = 0
    accumulator = 0
    previous = time.monotonic()
    print('Robotic Arm control desk http://127.0.0.1:8765', flush=True)
    try:
        while True:
            now = time.monotonic()
            accumulator += min(now-previous, .1)
            previous = now
            while not commands.empty():
                cmd = commands.get_nowait()
                try:
                    action = cmd.get('action')
                    if action in ('targets','preset','reset','demo','grasp','teleop'):
                        ik_status = {}
                    if action in ('targets','preset','reset','demo','ik','teleop'):
                        grasp = False
                    if action in ('targets','preset','reset','demo','ik','grasp'):
                        teleop = False; tracking_was_fresh = False; last_packet = 0; tracking_error = ''
                    if action == 'targets':
                        sim.set_targets(cmd['targets']); demo = False
                    elif action == 'preset':
                        sim.preset(cmd['name']); demo = False
                    elif action == 'reset':
                        sim.reset(); demo = False; paused = False; ik_status = {}
                    elif action == 'pause': paused = bool(cmd['value'])
                    elif action == 'demo':
                        demo = bool(cmd['value']); demo_start = float(d.time); last_stage = -1; paused = False
                    elif action == 'grasp':
                        setup_seeded_grasp(sim)
                        grasp = True; grasp_stage = -1; demo = False; teleop = False; paused = False
                        accumulator = 0
                        grasp_start_z = float(d.xpos[sim.object_id,2])
                        camera.lookat[:] = [-.25, 0, .35]
                        camera.distance = 1.50; camera.azimuth = 140; camera.elevation = -15
                    elif action == 'teleop':
                        teleop = cmd['value']; demo = False
                        tracking_was_fresh = False; last_packet = 0; last_arm_packet = 0; tracking_error = ''
                        sim.hold()
                    elif action == 'ik':
                        target = cmd['target']
                        ik_status = sim.solve_ik(target); demo = False
                    elif action == 'camera':
                        camera.azimuth = float(cmd.get('azimuth', camera.azimuth)) % 360
                        camera.elevation = max(-85, min(85, float(cmd.get('elevation', camera.elevation))))
                        camera.distance = max(.12, min(3.5, float(cmd.get('distance', camera.distance))))
                        if 'lookat' in cmd: camera.lookat[:] = cmd['lookat']
                    with mutex: shared['error'] = ''
                except Exception as e:
                    with mutex: shared['error'] = str(e)
            try:
                for _ in range(16):
                    packet, _ = udp.recvfrom(8193)
                    if teleop:
                        try:
                            if len(packet) > 8192: raise ValueError('Tracking packet too large')
                            targets, arm_target = checked_tracking(json.loads(packet))
                            # Validate the whole packet before applying any finger/arm command.
                            if arm_target is not None and now-last_arm_packet > .2:
                                ik_status = sim.solve_ik(arm_target)
                                last_arm_packet = now
                            sim.set_targets(targets)
                            last_packet = now
                            tracking_was_fresh = True
                            tracking_error = ''
                        except (ValueError, TypeError, KeyError, OverflowError, UnicodeError, RecursionError) as exc:
                            tracking_error = str(exc)
            except BlockingIOError: pass
            except OSError as exc:
                # Windows reports WSAEMSGSIZE for oversized datagrams; contain it.
                tracking_error = str(exc)
            if teleop and tracking_was_fresh and now-last_packet > .6:
                sim.hold()
                tracking_was_fresh = False
            if demo:
                stage = int((float(d.time)-demo_start)/3.5) % 6
                if stage != last_stage:
                    sim.preset(['open','fist','open','pinch','point','peace'][stage])
                    last_stage = stage
            if grasp:
                stage = 0 if d.time < .6 else 1 if d.time < 2.4 else 2 if d.time < 4.9 else 3
                if stage != grasp_stage:
                    if stage == 1: sim.preset('fist')
                    if stage == 2:
                        grasp_start_z = float(d.xpos[sim.object_id,2])
                        sim.set_targets({'joint_2_shoulder':-.3,'joint_3_elbow':-.55,'joint_4_wrist_pitch':.3})
                    grasp_stage = stage
            if not paused:
                count = min(50, int(accumulator/m.opt.timestep))
                if count: sim.step(count); accumulator -= count*m.opt.timestep
            else: accumulator = 0
            if now-last_snapshot >= .10:
                state = sim.state()
                if ik_status.get('success'):
                    ik_status['actual_position_error_m'] = math.dist(state['palm_position'],ik_status['target'])
                state.update(paused=paused, demo=demo, teleop=teleop,
                    grasp=grasp, grasp_phase=['Settle','Close fingers','Lift','Hold'][max(grasp_stage,0)] if grasp else '',
                    grasp_lift_m=float(d.xpos[sim.object_id,2])-grasp_start_z if grasp else 0,
                    tracking_fresh=teleop and tracking_was_fresh and now-last_packet<.6,
                    tracking_error=tracking_error, ik=ik_status,
                    camera={'azimuth':camera.azimuth,'elevation':camera.elevation,'distance':camera.distance,'lookat':camera.lookat.tolist()})
                with mutex: shared['state'] = state; shared['ready'] = True
                last_snapshot = now
            if now-last_frame >= 1/20:
                renderer.update_scene(d, camera=camera)
                pixels = renderer.render()
                buffer = io.BytesIO()
                Image.fromarray(pixels).save(buffer, format='JPEG', quality=87)
                with mutex: shared['frame'] = buffer.getvalue()
                last_frame = now
            time.sleep(.001)
    finally:
        renderer.close(); udp.close(); server.shutdown()

if __name__ == '__main__': run()
