"""Record actual integrated MuJoCo contact dynamics, never keyframe animation."""
from pathlib import Path
import sys, json
sys.path.insert(0,str(Path(__file__).parent))
import numpy as np, mujoco, cv2
from PIL import Image,ImageDraw,ImageFont
from evaluate import trial,runtime,OUT
from controller import object_contacts
from vision import KnownSizeRGBDCamera

ROOT=Path(__file__).resolve().parents[2]
FONT=ROOT/'software/freecad/FreeCAD_1.1.4-Windows-x86_64-py311/data/fonts/osifont.ttf'
def font(size):
    try:return ImageFont.truetype(str(FONT),size)
    except OSError:return ImageFont.load_default(size=size)

def main():
    sim=runtime.ArmSimulation()
    full=mujoco.Renderer(sim.m,height=720,width=840)
    detail=mujoco.Renderer(sim.m,height=450,width=560)
    camera=mujoco.MjvCamera();mujoco.mjv_defaultCamera(camera)
    camera.lookat[:]=[.25,0,.82];camera.distance=1.27;camera.azimuth=110;camera.elevation=-16
    close=mujoco.MjvCamera();mujoco.mjv_defaultCamera(close)
    close.distance=.38;close.azimuth=115;close.elevation=-20
    opt=mujoco.MjvOption();opt.geomgroup[3]=0;opt.geomgroup[4]=0
    path=OUT/'learned_contact_grasp.webm';fps=20
    writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'VP80'),fps,(1440,900))
    if not writer.isOpened():raise RuntimeError('WebM writer failed')
    frames=0;phase_images={};heights=[];events=[];prior='';camera_rgb=None;detection={}
    def estimate(sim,size):
        nonlocal camera_rgb
        sensor=KnownSizeRGBDCamera(sim,size)
        try:
            detection.update(sensor.capture())
            if not detection['detected']:raise RuntimeError('Camera did not detect target')
            camera_rgb=sensor.latest_rgb.copy()
            return detection['center_world_m']
        finally:sensor.close()
    def capture(sim,ctl,step):
        nonlocal frames,prior
        if step%25:return
        full.update_scene(sim.d,camera=camera,scene_option=opt);full.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW]=False
        close.lookat[:]=[.38,0,max(.66,float(sim.d.xpos[sim.object_id,2])+.025)]
        detail.update_scene(sim.d,camera=close,scene_option=opt);detail.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW]=False
        canvas=Image.new('RGB',(1440,900),(15,24,30));draw=ImageDraw.Draw(canvas)
        canvas.paste(Image.fromarray(full.render()),(14,112));canvas.paste(Image.fromarray(detail.render()),(866,112))
        draw.text((24,14),'ANTHROARM-27 | LEARNED CONTACT GRASP',font=font(28),fill=(236,246,251))
        draw.text((24,57),ctl.phase.upper()+' | actual integrated rigid-body physics',font=font(24),fill=(99,221,187))
        cs=object_contacts(sim);hand=[c for c in cs if c['geom']!='worktable']
        height=float(sim.d.xpos[sim.object_id,2]-(.600+.037/2));heights.append(height)
        lines=[f'Cube: 37 mm | 60 g',f'Lift: {height*1000:.1f} mm',f'Hand contacts: {len(hand)}',f'Effort: {max(abs(sim.d.actuator_force)/sim.effort)*100:.0f}% of bound', 'Free object | No weld']
        for i,text in enumerate(lines):draw.text((875,578+i*33),text,font=font(22),fill=(215,232,239))
        if camera_rgb is not None:
            canvas.paste(Image.fromarray(camera_rgb).resize((224,168)),(1200,578))
        draw.rectangle((880,758,1410,818),outline=(60,83,93))
        if len(heights)>1:
            points=[(882+i/max(1,len(heights)-1)*526,816-min(.2,max(0,h))/.2*54) for i,h in enumerate(heights)]
            draw.line(points,fill=(255,170,74),width=2)
        draw.text((24,846),'RGB-D estimate -> learned grasp | scripted stages + IK | force-bounded actuators',font=font(23),fill=(211,226,232))
        draw.text((24,875),'Simulated contact model; no hardware operation or general-object capability is claimed.',font=font(19),fill=(150,173,185))
        writer.write(cv2.cvtColor(np.asarray(canvas),cv2.COLOR_RGB2BGR));frames+=1
        if ctl.phase!=prior:
            events.append(dict(phase=ctl.phase,video_time_s=frames/fps,simulation_time_s=float(sim.d.time)));prior=ctl.phase
        if ctl.phase in ('hold','settle'):
            phase_images[ctl.phase]=canvas.copy()
    try:
        result=trial(sim,size=.037,mass=.06,xy=(.4,0),callback=capture,estimate_provider=estimate)
        result['initial_detection']=detection
    finally:
        writer.release();full.close();detail.close();sim.close()
    for phase,img in phase_images.items():img.save(OUT/f'learned_grasp_{phase}.png')
    cap=cv2.VideoCapture(str(path));decoded=0
    while True:
        ok,frame=cap.read()
        if not ok:break
        decoded+=1
    cap.release()
    metadata=dict(file=path.name,fps=fps,frames=frames,decoded_frames=decoded,duration_s=frames/fps,events=events,result={k:v for k,v in result.items() if k not in ('samples','stages')},source='MuJoCo physics frames with exact V3 CAD mesh surfaces')
    (OUT/'video.json').write_text(json.dumps(metadata,indent=2))
    (OUT/'video_trial.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(metadata),flush=True)

if __name__=='__main__':main()
