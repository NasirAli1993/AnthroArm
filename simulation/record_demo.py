"""Record authentic MuJoCo motion. No edits to object pose after demo reset."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
import cv2
from PIL import Image
from model import ArmSimulation
from grasp_demo import setup_seeded_grasp
ROOT=Path(__file__).resolve().parents[1]

def record():
 s=ArmSimulation();frames=[];width,height=800,600;fps=20
 video=cv2.VideoWriter(str(ROOT/'results'/'robot_demo.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),fps,(width,height))
 if not video.isOpened():raise RuntimeError('Video writer unavailable')
 framecount=0
 def clip(seconds,title,subtitle,camera):
  nonlocal framecount
  for k in range(round(seconds*fps)):
   s.step(round(1/fps/s.m.opt.timestep))
   cam=camera(k/max(1,round(seconds*fps)-1)) if callable(camera) else camera
   rgb=s.render(width,height,cam);bgr=cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR)
   overlay=bgr.copy();cv2.rectangle(overlay,(0,0),(width,78),(18,24,34),-1);bgr=cv2.addWeighted(overlay,.91,bgr,.09,0)
   cv2.putText(bgr,title,(22,32),cv2.FONT_HERSHEY_SIMPLEX,.70,(235,245,250),1,cv2.LINE_AA)
   cv2.putText(bgr,subtitle,(22,60),cv2.FONT_HERSHEY_SIMPLEX,.44,(175,209,220),1,cv2.LINE_AA)
   video.write(bgr)
   if framecount%2==0:frames.append(Image.fromarray(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)).resize((640,480)))
   framecount+=1
 home={'azimuth':150,'elevation':-12,'distance':1.30,'lookat':[.20,0,.38]}
 clip(1.5,'ASTER-25 | 5 arm axes + 20 hand axes','MuJoCo rigid-body simulation | Adult-scale 190 mm hand',home)
 s.preset('peace');clip(1.5,'All five fingers move independently','20 effort-limited hand actuators | 25 robot actuators total',home)
 setup_seeded_grasp(s)
 view={'azimuth':140,'elevation':-15,'distance':1.5,'lookat':[-.25,0,.35]}
 clip(.6,'Seeded grasp: 60 g cube starts in the palm','Demonstrates grip retention and lift; autonomous pickup is not included',view)
 s.preset('fist');clip(1.8,'Close the fingers around the cube','Contacts and friction support the object | No weld or attachment',view)
 s.set_targets({'joint_2_shoulder':-.3,'joint_3_elbow':-.55,'joint_4_wrist_pitch':.3})
 clip(2.5,'Lift the object through physical contact','Gravity remains active | Bounded motor effort',view)
 clip(2.,'29.4 cm lift | Sustained grip for 2 seconds','Middle finger + thumb maintain object contact throughout the hold',view)
 clip(2.,'Grip detail | Fully simulated finger contact','Concept model: manufacturing and physical hardware remain unvalidated',lambda t:{'azimuth':140+65*t,'elevation':-20,'distance':.38,'lookat':s.state()['palm_position']})
 video.release();frames[0].save(ROOT/'results'/'robot_demo.gif',save_all=True,append_images=frames[1:],duration=100,loop=0,optimize=False)
 s.close();print(f'Recorded {framecount} frames, {framecount/fps:.1f}s to results/robot_demo.mp4 and robot_demo.gif')
if __name__=='__main__':record()


