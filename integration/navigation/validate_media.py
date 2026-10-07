"""Decode actual recorded navigation frames and save proof metadata."""
from pathlib import Path
import os,json,hashlib
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
import cv2
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(r'D:\RoboticArm');OUT=ROOT/'results/integration/navigation'
video=OUT/'navigation_demo.webm';capture=cv2.VideoCapture(str(video))
count=int(capture.get(cv2.CAP_PROP_FRAME_COUNT));fps=float(capture.get(cv2.CAP_PROP_FPS))
positions=[0,count//2,count-1];frames=[];checks=[]
for index in positions:
    capture.set(cv2.CAP_PROP_POS_FRAMES,index);ok,frame=capture.read()
    checks.append({'frame':index,'decoded':bool(ok),'width':None if not ok else frame.shape[1],'height':None if not ok else frame.shape[0]})
    if ok:frames.append(Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).resize((720,400)))
capture.release()
sheet=Image.new('RGB',(720,3*430),'#0d1a20');draw=ImageDraw.Draw(sheet);font=ImageFont.load_default(size=16)
for slot,(index,frame) in enumerate(zip(positions,frames)):
    draw.text((14,slot*430+6),f'Actual recorded frame {index} / {count-1}',font=font,fill='#75e5c6');sheet.paste(frame,(0,slot*430+30))
sheet.save(OUT/'navigation_video_contact_sheet.png')
files=['navigation_demo.webm','navigation_validation.json','implementation_checks.json','sensor_observations.json.gz','trajectory.json','navigation_map.png']
report={'passed':bool(count>100 and fps==10 and all(c['decoded'] for c in checks)),'video_frames':count,'fps':fps,'duration_s':count/fps,'frame_checks':checks,'file_sha256':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in files},'source_sha256':{name:hashlib.sha256((ROOT/'integration/navigation'/name).read_bytes()).hexdigest() for name in ['navigation.py','run_mission.py','validate_navigation.py']}}
(OUT/'media_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
raise SystemExit(0 if report['passed'] else 1)
