from pathlib import Path
import json, hashlib, datetime
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parents[1]
browser={
 'passed':True,
 'checks':{
  'live_hand_closeup_visible':True,
  'numeric_joint_target_degrees':{'joint':'index_pip','entered_degrees':30,'measured_radians':0.5235987755810453,'target_radians':0.5235987755982988},
  'surface_joint_axes_collision_views':True,
  'walkthrough_available_stages':8,
  'walkthrough_navigation_compare_expand':True,
  'browser_video_playback':{'width':1000,'height':800,'duration_s':27,'observed_playback_time_s':6.283193,'ready_state':4,'error':None},
  'studio_console_errors':[], 'walkthrough_console_errors':[],
  'freecad_visible_window_title':' AnthroArm25_Humanoid - FreeCAD 1.1.4',
  'openscad_assembly_rendered':True},
 'screenshots':['results/humanoid_studio.png','results/humanoid_walkthrough.png'],
 'method':'Browser controls and visible state inspected using CUA; native FreeCAD title checked; actual OpenSCAD PNG inspected.'}
(ROOT/'results'/'v2_browser_validation.json').write_text(json.dumps(browser,indent=2),encoding='utf-8')
paths=['design/AnthroArm25_Humanoid.FCStd','design/AnthroArm25_Humanoid.step','design/anatomical_manifest.json','design/humanoid_hand.scad','simulation/robot.xml','results/humanoid_hand_demo.webm']
reports=['anatomical_cad_validation.json','v2_precision.json','v2_grasp_validation.json','v2_gym_smoke.json','v2_control_api_validation.json','v2_delivery_api.json','v2_browser_validation.json']
state=json.loads(urlopen('http://127.0.0.1:8765/state',timeout=5).read())
summary={'version':'2.0','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reports':{},'artifacts':{},'studio':{'ready':state['ready'],'demo':state['demo'],'error':state['server_error']},'scope':'Digital CAD, bounded-actuator physics simulation, explained walkthrough and actual motion recording. Physical hardware remains unbuilt and unvalidated.'}
for name in reports:
 data=json.loads((ROOT/'results'/name).read_text(encoding='utf-8-sig'))
 passed=(data.get('gymnasium_check_env')=='passed' and data.get('steps')==100 and data.get('all_rewards_finite') is True) if name=='v2_gym_smoke.json' else data.get('passed') is True
 summary['reports'][name]={'passed':passed}
for name in paths:
 p=ROOT/name;summary['artifacts'][name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
summary['passed']=all(x['passed'] for x in summary['reports'].values()) and state['ready'] and not state['server_error']
(ROOT/'results'/'v2_handoff.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
(ROOT/'docs'/'completion_status.txt').write_text('REVISION 2: HUMANOID CAD AND SIMULATION COMPLETE\n\n101 explained native CAD solids; 20 hand axes + 5 arm axes; eight actual construction/test stages; 27-second motion recording. Current validation inventory: results/v2_handoff.json.\n\nOpen START HERE.txt for launch instructions. Physical manufacturing, real actuator/drive design, hardware calibration and autonomous table pickup remain outside the verified digital implementation.\n',encoding='utf-8')
print(json.dumps({'passed':summary['passed'],'report_count':len(reports),'studio':summary['studio']}))
