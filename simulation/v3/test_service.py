"""Lightweight localhost integration checks; leaves the virtual arm reset/manual."""
from pathlib import Path
import urllib.request,json,time,io
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];BASE='http://127.0.0.1:8766'
def get(path):
    with urllib.request.urlopen(BASE+path,timeout=10) as r:return r.read()
def state():return json.loads(get('/state'))
def post(command):
    request=urllib.request.Request(BASE+'/command',data=json.dumps(command).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(request,timeout=10) as r:return json.loads(r.read())
def until(predicate,timeout=6):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        s=state()
        if predicate(s):return s
        time.sleep(.12)
    raise AssertionError('Service did not reach expected state')
def run():
    report={'passed':False,'checks':{},'physical_camera_toggled':False}
    post({'action':'reset'});s=until(lambda x:x.get('mode')=='manual' and not x['vision']['active'])
    assert len(s['joints'])==27 and s['total_dof']==27 and not s['server_error'];report['checks']['loaded_model']={'passed':True,'dof':27,'version':s['version']}
    post({'action':'vision','value':True});s=until(lambda x:x.get('mode')=='vision' and x['vision']['active']);s=until(lambda x:x['vision']['target_estimate'] is not None)
    assert not s['tracking_fresh'] and not s['webcam']['enabled'];report['checks']['vision_start']={'passed':True,'phase':s['vision']['phase'],'target_estimate':s['vision']['target_estimate']}
    dimensions={p:Image.open(io.BytesIO(get(p))).size for p in ('/frame.jpg','/vision.jpg')};assert dimensions['/frame.jpg']==(1000,800) and dimensions['/vision.jpg']==(640,480);report['checks']['live_frames']={'passed':True,'dimensions':dimensions}
    post({'action':'vision','value':False});s=until(lambda x:x['mode']=='manual' and not x['vision']['active']);targets=np.array([j['target'] for j in s['joints']]);time.sleep(.65);later=state();drift=float(np.max(abs(np.array([j['target'] for j in later['joints']])-targets)));assert drift<1e-10 and not later['tracking_fresh'];report['checks']['vision_cancel_holds_targets']={'passed':True,'max_target_change_rad':drift}
    post({'action':'vision','value':True});until(lambda x:x['mode']=='vision');post({'action':'preset','name':'fist'});s=until(lambda x:x['mode']=='manual' and not x['vision']['active']);assert s['joints'][s['joints'].index(next(j for j in s['joints'] if j['name']=='index_mcp_flexion'))]['target']>1;report['checks']['manual_preset_cancels_vision']={'passed':True}
    post({'action':'reset'});s=until(lambda x:x['mode']=='manual' and all(abs(j['target']-j['home'])<1e-8 for j in x['joints']));assert not s['vision']['active'] and not s['tracking_fresh'] and not s['server_error'];report['checks']['reset_clears_control_modes']={'passed':True}
    report['passed']=True;(ROOT/'results'/'v3'/'service_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));return report
if __name__=='__main__':run()
