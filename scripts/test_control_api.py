"""Local control API integration tests. Run while dashboard is otherwise idle.

This changes simulation targets/modes and always attempts to restore home with
demo and teleoperation disabled. It does not access camera or physical hardware.
"""
from pathlib import Path
import json
import math
import socket
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
URL = 'http://127.0.0.1:8765'
results = []


def state():
    with urlopen(URL+'/state', timeout=4) as response:
        return json.loads(response.read())


def request(payload, expected=200, origin=None):
    raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    headers = {'Content-Type':'application/json'}
    if origin is not None: headers['Origin'] = origin
    try:
        with urlopen(Request(URL+'/command', data=raw, headers=headers), timeout=4) as response:
            status, body = response.status, response.read()
    except HTTPError as exc:
        status, body = exc.code, exc.read()
    assert status == expected, (status, expected, body)
    return body


def until(predicate, timeout=3):
    deadline = time.monotonic()+timeout
    last = None
    while time.monotonic() < deadline:
        try: last = state()
        except (URLError, TimeoutError):
            time.sleep(.10); continue
        if predicate(last): return last
        time.sleep(.04)
    raise AssertionError('Timed out waiting for expected state: '+str(last and {
        k:last.get(k) for k in ['paused','demo','teleop','tracking_fresh','server_error','tracking_error']}))


def target(snapshot, name='index_pip'):
    return next(j['target'] for j in snapshot['joints'] if j['name'] == name)


def udp(payload):
    raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as channel:
        channel.sendto(raw, ('127.0.0.1', 5005))


def fresh():
    udp({'timestamp':time.time(), 'targets':{'index_pip':.25}})
    return until(lambda s: s['tracking_fresh'] and abs(target(s)-.25)<1e-8)


def check(name, operation):
    try:
        detail = operation()
        results.append({'test':name, 'passed':True, 'detail':detail})
        print('PASS', name, flush=True)
    except Exception as exc:
        results.append({'test':name, 'passed':False, 'error':str(exc)})
        print('FAIL', name, str(exc), flush=True)


def bad_packet(payload):
    fresh()
    udp(payload)
    snapshot = until(lambda s: bool(s.get('tracking_error')))
    assert abs(target(snapshot)-.25)<1e-8, 'Rejected packet changed finger target'
    return snapshot['tracking_error']


def run():
    initial = until(lambda s:s.get('ready'), timeout=45)
    assert len(initial['joints']) == 25
    try:
        request({'action':'reset'})
        until(lambda s:not s['demo'] and not s['teleop'] and not s['paused'])
        for name,payload in [('invalid_json',b'{'), ('wrong_root',b'[]'), ('empty_payload',b''),
            ('unknown_action',{'action':'bogus'}), ('unknown_joint',{'action':'targets','targets':{'bogus':1}}),
            ('nonfinite_joint',{'action':'targets','targets':{'index_pip':float('nan')}}),
            ('bad_boolean',{'action':'pause','value':'false'}),
            ('nonfinite_camera',{'action':'camera','azimuth':float('nan'),'lookat':[0,0,.5]}),
            ('bad_camera_vector',{'action':'camera','lookat':[0,0]}),
            ('nonfinite_ik',{'action':'ik','target':[float('inf'),0,.4]}),
            ('enormous_camera_integer',{'action':'camera','azimuth':10**400})]:
            check('http_'+name, lambda p=payload: request(p, expected=400).decode())
        check('cross_origin_rejected',lambda:request({'action':'reset'},403,origin='https://example.com').decode())

        def pause_check():
            request({'action':'pause','value':True})
            before = until(lambda s:s['paused'])['time']
            time.sleep(.30)
            assert state()['time'] == before
            request({'action':'reset'})
            until(lambda s:not s['paused'])
            return 'Time freezes while paused; reset resumes.'
        check('pause_reset',pause_check)

        def clamp_check():
            request({'action':'targets','targets':{'index_pip':999}})
            snapshot = until(lambda s:target(s)>1)
            row=next(j for j in snapshot['joints'] if j['name']=='index_pip')
            assert row['target']==row['max'] and not snapshot['demo']
            request({'action':'reset'}); until(lambda s:abs(target(s))<1e-8)
            return row['target']
        check('joint_clamp',clamp_check)

        request({'action':'teleop','value':True}); until(lambda s:s['teleop'])
        check('udp_valid',lambda:fresh()['tracking_fresh'])
        invalid = [
            ('stale',{'timestamp':time.time()-20,'targets':{'index_pip':.7}}),
            ('nan_timestamp',{'timestamp':float('nan'),'targets':{'index_pip':.7}}),
            ('infinite_timestamp',{'timestamp':float('inf'),'targets':{'index_pip':.7}}),
            ('enormous_integer',{'timestamp':10**400,'targets':{'index_pip':.7}}),
            ('nonfinite_target',{'targets':{'index_pip':float('nan')}}),
            ('bad_arm_shape',{'targets':{'index_pip':.7},'arm_target':[.3,.1]}),
            ('arm_out_of_bounds',{'targets':{'index_pip':.7},'arm_target':[1.5,0,.5]}),
            ('unknown_joint',{'targets':{'index_pip':.7,'not_a_joint':.2}}),
            ('empty',{'targets':{}}), ('malformed',b'{'), ('invalid_utf8',b'\xff\xfe'),
            ('deep_nesting',(b'['*1100)+b'0'+(b']'*1100)),
            ('oversized',b' '*10000),
        ]
        for name,payload in invalid:
            check('udp_reject_'+name,lambda p=payload:bad_packet(p))

        def watchdog():
            fresh()
            for _ in range(10):
                udp({'timestamp':time.time()-20,'targets':{'index_pip':.7}})
                time.sleep(.09)
            snapshot=until(lambda s:not s['tracking_fresh'])
            assert all(math.isfinite(j['target']) for j in snapshot['joints'])
            return 'Invalid packets do not prolong freshness; stale stream holds.'
        check('udp_watchdog',watchdog)

        def arm_check():
            udp({'timestamp':time.time(),'targets':{'index_pip':.25},'arm_target':[.30,.10,.55]})
            snapshot=until(lambda s:s.get('ik',{}).get('target')==[.30,.10,.55])
            assert snapshot['ik']['success']
            return {'ik_error_m':snapshot['ik']['error_m']}
        check('udp_arm_target',arm_check)

        def exclusive():
            request({'action':'demo','value':True})
            until(lambda s:s['demo'] and not s['teleop'])
            request({'action':'targets','targets':{'index_pip':.15}})
            until(lambda s:not s['demo'] and not s['teleop'] and abs(target(s)-.15)<1e-8)
            request({'action':'teleop','value':True}); until(lambda s:s['teleop'])
            request({'action':'reset'})
            snapshot=until(lambda s:not s['teleop'] and not s['demo'])
            assert all(abs(j['target']-j['home'])<1e-8 for j in snapshot['joints'])
            return 'Demo, manual and tracking modes are exclusive; reset returns home.'
        check('exclusive_modes',exclusive)
    finally:
        try:
            request({'action':'reset'})
            restored=until(lambda s:not s['demo'] and not s['teleop'] and not s['paused'])
            restoration={'home_targets':all(abs(j['target']-j['home'])<1e-8 for j in restored['joints']),
                         'demo':restored['demo'],'teleop':restored['teleop'],'paused':restored['paused']}
        except Exception as exc:
            restoration={'error':str(exc)}
        report={'passed':all(x['passed'] for x in results), 'test_count':len(results),
                'restored_state':restoration,'tests':results}
        (ROOT/'results/control_api_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps({'passed':report['passed'],'test_count':len(results),'restored_state':restoration}),flush=True)
    return report


if __name__ == '__main__':
    raise SystemExit(0 if run()['passed'] else 1)
