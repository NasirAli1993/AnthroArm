"""Record the shipped files and explicitly bounded verification evidence."""
from pathlib import Path
import hashlib, json, urllib.request, datetime
R=Path('D:/RoboticArm')
state=json.load(urllib.request.urlopen('http://127.0.0.1:8766/state'))
paths=['design/v3/AnthroArm27_ReferenceV3.FCStd','design/v3/AnthroArm27_ReferenceV3.step','design/v3/printable_finger/TendonFinger_FitTest.FCStd','results/v3/full_arm_articulation.webm','results/v3/camera_autonomy.webm','hardware/single_finger/single_finger.ino','share/HumanArm_Demonstration.zip']
report={
 'recorded_at':datetime.datetime.now().astimezone().isoformat(),
 'project_root':str(R),'version':3,
 'physics_validation_passed':json.loads((R/'results/v3/validation.json').read_text())['passed'],
 'service_validation_passed':json.loads((R/'results/v3/service_validation.json').read_text())['passed'],
 'media_validation_passed':json.loads((R/'results/v3/media_validation.json').read_text())['passed'],
 'browser_checks':['Live frame visible','Index PIP requested35degrees and reached35degrees','Layer switching visible','Live camera-guided reach contact_stop success','Both WebM recordings readyState4;33and10.05seconds','Presentation and responsive wiring visually inspected'],
 'firmware':{'board':'Arduino UNO R3','compiled':True,'flash_bytes':4900,'ram_bytes':314,'uploaded':False,'physical_actuation_tested':False},
 'camera_diagnosis':json.loads((R/'results/v3/camera_diagnosis.json').read_text()),
 'current_service':{'ready':state['ready'],'server_error':state['server_error'],'mode':state['mode'],'webcam_enabled':state['webcam']['enabled']},
 'offline_package':{'structurally_verified':True,'visually_opened_from_file_url':False,'reason':'Browser tool blocks file URLs; live presentation was visually inspected.'},
 'limits':['Physical full arm has not been built.','Full-arm internal motors and load ratings remain conceptual.','Printable finger has not been fabricated or tested with a real servo.','Autonomy is calibrated known-object approach and touch, not autonomous pickup.','Physical hand imitation unverified because only unusable ToDesk virtual-camera feed is available.'],
 'files':[{'path':p,'bytes':(R/p).stat().st_size,'sha256':hashlib.sha256((R/p).read_bytes()).hexdigest()} for p in paths]
}
(R/'results/v3/handoff.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:report[k] for k in ('physics_validation_passed','service_validation_passed','media_validation_passed','current_service')}))
