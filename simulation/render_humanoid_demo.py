"""Render the actual current MuJoCo model, with measured motion and no pose animation."""
from pathlib import Path
import sys, json
import numpy as np
import mujoco
import cv2
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'simulation'))
from model import ArmSimulation

def run():
    sim=ArmSimulation()
    manifest=json.loads((ROOT/'design'/'anatomical_manifest.json').read_text(encoding='utf-8-sig'))
    if not manifest.get('valid'): raise RuntimeError('Anatomical CAD must be validated before rendering')
    renderer=mujoco.Renderer(sim.m,height=800,width=1000)
    option=mujoco.MjvOption(); option.geomgroup[3]=0
    camera=mujoco.MjvCamera(); mujoco.mjv_defaultCamera(camera)
    fps=24
    steps=round(1/fps/sim.m.opt.timestep)
    output=ROOT/'results'/'humanoid_hand_demo.webm'
    writer=cv2.VideoWriter(str(output),cv2.VideoWriter_fourcc(*'VP80'),fps,(1000,800))
    if not writer.isOpened(): raise RuntimeError('Video encoder unavailable')
    try: font=ImageFont.truetype(str(ROOT/'software'/'openscad'/'openscad-2021.01'/'fonts'/'Liberation-2.00.1'/'ttf'/'LiberationSans-Regular.ttf'),23)
    except OSError: font=ImageFont.load_default(size=23)
    captions=[]
    phases=[('Open hand · smooth shells and finger pads','open',3),
            ('Index · independent joints','index',3),
            ('Middle · independent joints','middle',3),
            ('Ring · independent joints','ring',3),
            ('Little finger · independent joints','pinky',3),
            ('Thumb · opposition and flexion','thumb',3),
            ('Five fingers · closing together','fist',3),
            ('Five fingers · reopening','open',3),
            ('Spread and gesture control','peace',3)]
    elapsed=0
    try:
        for title,name,seconds in phases:
            sim.preset('open')
            if name in ('index','middle','ring','pinky'):
                sim.set_targets({name+'_mcp_flexion':.95,name+'_pip':1.15,name+'_dip':.70})
            elif name=='thumb':
                sim.set_targets({'thumb_cmc_opposition':.55,'thumb_cmc_flexion':.55,'thumb_mcp_flexion':.7,'thumb_ip':.6})
            else: sim.preset(name)
            for frame in range(fps*seconds):
                sim.step(steps)
                b=mujoco.mj_name2id(sim.m,mujoco.mjtObj.mjOBJ_BODY,'palm_base')
                R=sim.d.xmat[b].reshape(3,3); n=R@np.array([1,-.3,.17]); n/=np.linalg.norm(n)
                camera.lookat[:]=sim.d.xpos[b]+R@np.array([0,0,.097])
                camera.distance=.41; camera.azimuth=np.degrees(np.arctan2(-n[1],-n[0])); camera.elevation=-np.degrees(np.arcsin(n[2]))
                renderer.update_scene(sim.d,camera=camera,scene_option=option)
                pixels=renderer.render()
                im=Image.fromarray(pixels); draw=ImageDraw.Draw(im)
                draw.rectangle((0,0,1000,82),fill=(16,23,25))
                draw.text((25,14),'ANTHRO / ARM  |  HUMANOID HAND',font=font,fill=(98,219,192))
                draw.text((25,46),title,font=font,fill=(234,240,242))
                draw.rectangle((0,756,1000,800),fill=(16,23,25))
                draw.text((25,766),'Actual MuJoCo physics | 25 joints | 190 mm nominal hand',font=font,fill=(175,196,202))
                writer.write(cv2.cvtColor(np.asarray(im),cv2.COLOR_RGB2BGR))
                if name=='open' and frame==fps*2 and elapsed==0:
                    im.save(ROOT/'results'/'humanoid_hand_closeup.png')
            captions.append({'start_s':elapsed,'duration_s':seconds,'title':title})
            elapsed+=seconds
    finally:
        writer.release(); renderer.close()
    (ROOT/'results'/'humanoid_video.json').write_text(json.dumps({'file':str(output),'fps':fps,'duration_s':elapsed,'source':'Actual current MuJoCo mesh model; dynamics integrated every frame','phases':captions},indent=2),encoding='utf-8')
    print(output)

if __name__=='__main__':run()
