"""Integration checks for the new anatomical walkthrough and display controls."""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import json,time,hashlib
ROOT=Path(__file__).resolve().parents[1]
URL='http://127.0.0.1:8765'
checks=[]
def get(path):
    with urlopen(URL+path,timeout=8) as r:return r.read(),r.headers.get('Content-Type')
def command(data):
    with urlopen(Request(URL+'/command',data=json.dumps(data).encode(),headers={'Content-Type':'application/json'}),timeout=8) as r:return json.loads(r.read())
def check(name,test):
    try:
        detail=test();checks.append({'test':name,'passed':True,'detail':detail})
    except Exception as e:checks.append({'test':name,'passed':False,'detail':str(e)})
def gallery():
    body,_=get('/design');assert b'Design walkthrough' in body
    stages=json.loads(get('/stages/stages.json')[0])['stages'];assert len(stages)==8
    for s in stages:
        content,typ=get('/stages/'+s['image']);assert typ=='image/png' and content.startswith(b'\x89PNG') and len(content)>10000
    return 'Eight actual stage images served with explanations'
def reports():
    for route in ('/precision','/grasp-results'):
        report=json.loads(get(route)[0]);assert report.get('passed'),route
    return 'Current precision and grasp reports pass'
def video():
    data,typ=get('/motion.webm');assert typ=='video/webm' and data[:4]==b'\x1aE\xdf\xa3' and len(data)>100000
    return {'bytes':len(data),'format':'WebM/VP8'}
def layers():
    for layer in ('surface','collision','joints','surface'):
        command({'action':'layer','name':layer})
        deadline=time.monotonic()+2
        while time.monotonic()<deadline:
            s=json.loads(get('/state')[0])
            if s.get('display_layer')==layer:break
            time.sleep(.04)
        assert s['display_layer']==layer and not s['server_error']
        frame,typ=get('/frame.jpg');assert typ=='image/jpeg' and len(frame)>1000
    return 'Surface, collision and joint overlays render without server errors'
def rejected():
    for route in ('/stages/../server.py','/stages/%2e%2e%2fserver.py'):
        try:get(route);raise AssertionError('Invalid path accepted')
        except HTTPError as e:assert e.code==404
    try:command({'action':'layer','name':'unknown'});raise AssertionError('Invalid layer accepted')
    except HTTPError as e:assert e.code==400
    return 'Invalid paths and display options rejected'
check('walkthrough_and_eight_images',gallery)
check('current_physics_reports',reports)
check('browser_video_file',video)
check('display_layers',layers)
check('request_validation',rejected)
report={'passed':all(c['passed'] for c in checks),'checks':checks}
(ROOT/'results'/'v2_delivery_api.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
raise SystemExit(0 if report['passed'] else 1)
