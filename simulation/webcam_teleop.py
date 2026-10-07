"""Local MediaPipe hand-to-Aster-25 retargeting. No images are saved or sent.

Run after enabling Teleoperation in the dashboard. Q exits, C calibrates neutral
finger offsets. --arm adds a bounded, monocular relative-control heuristic.
"""
from pathlib import Path
import os
ROOT = Path(__file__).resolve().parents[1]
for key, folder in [('TEMP', 'temp'), ('TMP', 'temp'), ('MPLCONFIGDIR', 'cache/matplotlib')]:
    os.environ[key] = str(ROOT / folder)
import argparse
import json
import math
import socket
import time
import numpy as np

SPEC = json.loads((ROOT / 'design/robot_spec.json').read_text(encoding='utf-8-sig'))
JOINTS = {link['joint']['name']: link['joint'] for link in SPEC['links'] if link.get('joint')}
FINGERS = {'index': (5, 6, 7, 8), 'middle': (9, 10, 11, 12),
           'ring': (13, 14, 15, 16), 'pinky': (17, 18, 19, 20)}
EDGES = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
         (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15),
         (15, 16), (13, 17), (0, 17), (17, 18), (18, 19), (19, 20)]


def unit(v):
    n = float(np.linalg.norm(v))
    if n < 1e-8:
        raise ValueError('Degenerate landmark segment')
    return v / n


def flexion(a, b, c):
    """Zero for a straight a-b-c chain, positive when bent; radians."""
    cosine = float(np.dot(unit(a-b), unit(c-b)))
    return math.pi - math.acos(float(np.clip(cosine, -1.0, 1.0)))


def landmark_targets(points):
    p = np.asarray(points, dtype=float)
    if p.shape != (21, 3) or not np.isfinite(p).all():
        raise ValueError('Expected 21 finite three-dimensional hand landmarks')
    along = unit(p[9]-p[0])
    across = unit((p[5]-p[17]) - along*np.dot(p[5]-p[17], along))
    values = {}
    for finger, (mcp, pip, dip, tip) in FINGERS.items():
        direction = unit(p[pip]-p[mcp])
        spread = math.atan2(float(np.dot(direction, across)), float(np.dot(direction, along)))
        # The robot's +X knuckle axis rotates local +Z toward -Y.
        values[f'{finger}_mcp_abduction'] = -spread
        values[f'{finger}_mcp_flexion'] = flexion(p[0], p[mcp], p[pip])
        values[f'{finger}_pip'] = flexion(p[mcp], p[pip], p[dip])
        values[f'{finger}_dip'] = flexion(p[pip], p[dip], p[tip])
    palm_width = max(float(np.linalg.norm(p[5]-p[17])), .001)
    # Thumb base joints have no one-to-one anatomical landmark correspondence.
    # Opposition is a bounded pinch-distance heuristic; the other axes use bends.
    opposition = np.clip(1.0 - np.linalg.norm(p[4]-p[5]) / (1.5*palm_width), 0, 1)
    values['thumb_cmc_opposition'] = float(opposition) * JOINTS['thumb_cmc_opposition']['range'][1]
    values['thumb_cmc_flexion'] = flexion(p[0], p[1], p[2])
    values['thumb_mcp_flexion'] = flexion(p[1], p[2], p[3])
    values['thumb_ip'] = flexion(p[2], p[3], p[4])
    return values


class Retargeter:
    def __init__(self):
        self.previous = None
        self.neutral = {}
        self.origin = None

    def targets(self, raw, dt):
        dt = float(np.clip(dt, .001, .1))
        output = {}
        for name, value in raw.items():
            low, high = JOINTS[name]['range']
            value = float(np.clip(value-self.neutral.get(name, 0), low, high))
            if self.previous is not None:
                old = self.previous[name]
                smoothed = old + (1-math.exp(-dt/.10))*(value-old)
                max_delta = min(float(JOINTS[name]['velocity']), 2.5)*dt
                value = float(np.clip(smoothed, old-max_delta, old+max_delta))
            output[name] = value
        self.previous = output
        return output

    def arm_target(self, image_points):
        p = np.asarray(image_points)
        hand_scale = float(np.linalg.norm(p[9, :2]-p[0, :2]))
        sample = np.array([p[0, 0], p[0, 1], hand_scale])
        if self.origin is None:
            self.origin = sample.copy()
        delta = sample-self.origin
        # Apparent hand scale, NOT metric camera depth. Target is in robot meters.
        position = np.array([.36, 0, .50]) + np.array([delta[2]*.8, -delta[0]*.5, -delta[1]*.5])
        return np.clip(position, [.20, -.20, .30], [.52, .20, .70]).tolist()


def camera_probe(index):
    import cv2
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    try:
        ok, frame = cap.read() if cap.isOpened() else (False, None)
        return {'camera_index': index, 'opened': bool(cap.isOpened()), 'frame_received': bool(ok),
                'frame_shape': list(frame.shape) if ok else None,
                'image_saved': False, 'live_hand_tracking_verified': False}
    finally:
        cap.release()


def self_test():
    assert abs(flexion(np.array([0., 0, 0]), np.array([0., 1, 0]), np.array([0., 2, 0]))) < 1e-7
    assert abs(flexion(np.array([0., 0, 0]), np.array([0., 1, 0]), np.array([1., 1, 0]))-math.pi/2) < 1e-7
    p = np.zeros((21, 3))
    for x, ids in zip([-.03, -.01, .01, .03], FINGERS.values()):
        for j, idx in enumerate(ids):
            p[idx] = [x, .08+j*.025, 0]
    p[1:5] = [[-.03, .025, 0], [-.05, .04, 0], [-.065, .055, 0], [-.08, .065, 0]]
    values = landmark_targets(p)
    tracker = Retargeter()
    first = tracker.targets(values, .02)
    second = tracker.targets({k: 10 for k in values}, .02)
    assert len(values) == 20 and set(values) == {k for k in JOINTS if not k.startswith('joint_')}
    assert all(JOINTS[k]['range'][0] <= v <= JOINTS[k]['range'][1] for k, v in second.items())
    assert max(abs(second[k]-first[k]) for k in first) <= .050001
    return {'retargeted_joints': 20, 'geometric_flexion': 'passed', 'bounds_and_rate_limit': 'passed',
            'live_hand_tracking_verified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--camera', type=int, default=0)
    parser.add_argument('--model', type=Path, default=ROOT/'models/hand_landmarker.task')
    parser.add_argument('--arm', action='store_true', help='Enable bounded relative wrist motion (uncalibrated monocular heuristic)')
    parser.add_argument('--probe-camera', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--model-test', action='store_true', help='Load model and infer on blank image without camera')
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2)); return
    if args.probe_camera:
        print(json.dumps(camera_probe(args.camera), indent=2)); return
    import cv2
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    if not args.model.is_file():
        raise SystemExit(f'Missing model: {args.model}; see docs/teleop_rl.txt')
    options = vision.HandLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(args.model)),
        running_mode=vision.RunningMode.VIDEO, num_hands=1,
        min_hand_detection_confidence=.65, min_hand_presence_confidence=.65,
        min_tracking_confidence=.65)
    with vision.HandLandmarker.create_from_options(options) as detector:
        if args.model_test:
            result = detector.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,
                data=np.zeros((240, 320, 3), dtype=np.uint8)), 0)
            print(json.dumps({'model_loaded': True, 'blank_frame_hand_count': len(result.hand_landmarks)})); return
        cap = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release(); raise SystemExit('Camera unavailable. Dashboard/manual demo still works.')
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tracker = Retargeter()
        started = previous = time.monotonic()
        failures = 0
        print('Enable Teleoperation in dashboard. Q: quit, C: neutral calibration. Camera images remain local and unsaved.')
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    failures += 1
                    if failures > 15:
                        raise RuntimeError('Camera stopped delivering frames; commands stopped.')
                    time.sleep(.03); continue
                failures = 0
                frame = cv2.flip(frame, 1)
                now = time.monotonic()
                result = detector.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,
                    data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)), int((now-started)*1000))
                raw = None
                status = 'No hand: commands paused; robot holds last target'
                if result.hand_landmarks and result.hand_world_landmarks:
                    points = np.array([[v.x, v.y, v.z] for v in result.hand_world_landmarks[0]])
                    normalized = np.array([[v.x, v.y, v.z] for v in result.hand_landmarks[0]])
                    try:
                        raw = landmark_targets(points)
                        targets = tracker.targets(raw, now-previous)
                        packet = {'targets': targets, 'timestamp': time.time(), 'source': 'webcam'}
                        if args.arm:
                            packet['arm_target'] = tracker.arm_target(normalized)
                        udp.sendto(json.dumps(packet, allow_nan=False).encode(), ('127.0.0.1', 5005))
                        status = 'Tracking: all 20 finger joints' + (' + relative arm' if args.arm else '')
                    except ValueError:
                        status = 'Landmark geometry invalid: commands paused'
                    h, w = frame.shape[:2]
                    pixels = [(int(x*w), int(y*h)) for x, y, _ in normalized]
                    for a, b in EDGES:
                        cv2.line(frame, pixels[a], pixels[b], (80, 220, 170), 2)
                    for pixel in pixels:
                        cv2.circle(frame, pixel, 3, (60, 150, 255), -1)
                previous = now
                cv2.putText(frame, status, (12, 25), cv2.FONT_HERSHEY_SIMPLEX, .5, (40, 240, 210), 1)
                cv2.putText(frame, 'Q quit | C neutral calibration', (12, 48), cv2.FONT_HERSHEY_SIMPLEX, .5, (240, 240, 240), 1)
                cv2.imshow('Aster-25 webcam teleoperation', frame)
                key = cv2.waitKey(1) & 0xff
                if key == ord('q'):
                    break
                if key == ord('c') and raw is not None:
                    tracker.neutral = dict(raw)
                    tracker.origin = None
        finally:
            cap.release(); udp.close(); cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
