"""End-to-end HTTP tests against real running MuJoCo physics."""
from pathlib import Path
import urllib.request, urllib.error, json, time, base64, math, struct
ROOT=Path(__file__).resolve().parents[1];BASE='http://127.0.0.1:8770'
def get(path):
    with urllib.request.urlopen(BASE+path,timeout=10) as r:return json.load(r)
def cmd(value):
    req=urllib.request.Request(BASE+'/command',json.dumps(value).encode(),{'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
def main():
    results={'simulation_only':True,'checks':{}}
    cmd({'op':'reset'});time.sleep(.3);s=get('/state');assert len(s['joints'])==27
    results['checks']['27_joint_feedback']=True
    j=next(j for j in s['joints'] if j['name']=='wrist_deviation');target=j['q']+.12
    command={'op':'trajectory','joint_names':[j['name']],'points':[{'time':1.,'positions':[target]}]}
    reply=cmd(command);ident=reply['id'];deadline=time.monotonic()+25
    while time.monotonic()<deadline:
        state=get('/state');tr=state['trajectory']
        if tr.get('id')==ident and tr.get('status')=='succeeded':break
        time.sleep(.1)
    else:raise AssertionError('Trajectory did not complete')
    actual=next(x['q'] for x in state['joints'] if x['name']==j['name']);assert abs(actual-target)<.01 and abs(actual-j['q'])>.08
    results['checks']['physical_trajectory']={'target':target,'actual':actual,'error_rad':abs(actual-target)}
    for label,payload in [('unknown_joint',{'op':'trajectory','joint_names':['unknown'],'points':[{'time':1.,'positions':[0]}]}),('out_of_range',{'op':'trajectory','joint_names':[j['name']],'points':[{'time':1.,'positions':[99]}]}),('nonincreasing_time',{'op':'trajectory','joint_names':[j['name']],'points':[{'time':0.,'positions':[0]}]}),('overspeed',{'op':'trajectory','joint_names':[j['name']],'points':[{'time':.0001,'positions':[0]}]})]:
        try:cmd(payload);raise AssertionError(label+' was accepted')
        except urllib.error.HTTPError as exc:assert exc.code==400
        results['checks'][label+'_rejected']=True
    cmd({'op':'trajectory','joint_names':[j['name']],'points':[{'time':5.,'positions':[0]}]});cmd({'op':'stop'});time.sleep(.15)
    assert get('/state')['trajectory']['status']=='cancelled';results['checks']['stop_and_hold']=True
    cmd({'op':'reset'});time.sleep(1.5);camera=get('/camera');depth=base64.b64decode(camera['depth_f32']);assert len(depth)==camera['width']*camera['height']*4
    assert base64.b64decode(camera['jpeg'])[:2]==b'\xff\xd8';assert camera['detection']['detected'];assert camera['detection']['ground_truth_object_pose_used'] is False
    results['checks']['rendered_rgbd_camera']={'width':camera['width'],'height':camera['height'],'detection':camera['detection']['center_world_m']}
    results['passed']=True;out=ROOT/'results'/'integration'/'runtime_validation.json';out.write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
if __name__=='__main__':main()
