"""Real 27-axis physics and real RGB-D vision video evidence, encoded WebM."""
from pathlib import Path
import importlib.util,json
import numpy as np,mujoco,cv2
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results'/'v3'
def load(name,file):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
runtime=load('v3runtime','model.py');vision=load('v3vision','vision_reach.py')
FONT=ROOT/'software'/'freecad'/'FreeCAD_1.1.4-Windows-x86_64-py311'/'data'/'fonts'/'osifont.ttf'
def font(size):
    try:return ImageFont.truetype(str(FONT),size)
    except OSError:return ImageFont.load_default(size=size)

def run():
    sim=runtime.ArmSimulation();control=vision.VisionReach(sim);renderer=mujoco.Renderer(sim.m,height=720,width=960)
    camera=mujoco.MjvCamera();mujoco.mjv_defaultCamera(camera);camera.lookat[:]=[.25,0,.84];camera.distance=1.35;camera.azimuth=115;camera.elevation=-15
    option=mujoco.MjvOption();option.geomgroup[3]=0;option.geomgroup[4]=0
    fps=20;steps=25;size=(1440,900);writer=cv2.VideoWriter(str(OUT/'camera_autonomy.webm'),cv2.VideoWriter_fourcc(*'VP80'),fps,size)
    if not writer.isOpened():raise RuntimeError('VP8 WebM encoder is unavailable')
    f=font(25);small=font(20);frames=0;events=[];lastphase=None
    def capture(title):
        nonlocal frames
        renderer.update_scene(sim.d,camera=camera,scene_option=option);renderer.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW]=False;main=Image.fromarray(renderer.render())
        canvas=Image.new('RGB',size,(15,24,30));draw=ImageDraw.Draw(canvas);canvas.paste(main,(12,95))
        draw.text((25,15),'ANTHROARM-27 | ACTUAL CAMERA-GUIDED MOTION',font=f,fill=(226,242,246));draw.text((25,51),title,font=small,fill=(93,218,188))
        if control.latest_rgb is not None:
            rgb=Image.fromarray(control.latest_rgb).resize((448,336));canvas.paste(rgb,(980,100))
            depth=np.clip(control.latest_depth,.4,2);gray=np.uint8(255*(1-(depth-.4)/1.6));col=cv2.applyColorMap(gray,cv2.COLORMAP_TURBO);depth_im=Image.fromarray(cv2.cvtColor(col,cv2.COLOR_BGR2RGB)).resize((448,336));canvas.paste(depth_im,(980,490))
        draw.text((985,453),'Real virtual RGB | OpenCV detection',font=small,fill=(200,224,232));draw.text((985,845),'Metric depth | calibrated camera',font=small,fill=(200,224,232))
        draw.text((24,828),'RGB-D pixels -> 3D estimate -> IK -> bounded motors -> contact stop',font=small,fill=(201,219,227));draw.text((24,858),'Autonomous reach/touch demonstration. Pickup is not claimed.',font=small,fill=(151,176,188))
        writer.write(cv2.cvtColor(np.asarray(canvas),cv2.COLOR_RGB2BGR));frames+=1
        return canvas
    sim.step(300);control.start();control.tick();control.camera.capture()
    try:
        while control.active and frames<fps*35:
            control.step(steps)
            if frames%4==0:control.camera.capture()
            title=control.phase.replace('_',' ').title();canvas=capture(title)
            if control.phase!=lastphase:
                events.append({'video_time_s':frames/fps,'phase':control.phase,'simulation_time_s':float(sim.d.time)});canvas.save(OUT/('vision_'+control.phase+'.png'));lastphase=control.phase
        for _ in range(fps*2):sim.step(steps);capture('CONTACT STOP | '+('PASS' if control.result.get('success') else 'NOT COMPLETED'))
        canvas.save(OUT/'vision_autonomy_poster.png')
    finally:writer.release();renderer.close();control.close();sim.close()
    (OUT/'camera_autonomy_video.json').write_text(json.dumps({'file':'camera_autonomy.webm','fps':fps,'duration_s':frames/fps,'events':events,'result':control.result,'source':'Actual current CAD meshes and integrated MuJoCo physics; true RGB and metric depth renders from calibrated fixed camera'},indent=2))
    print('Camera autonomy video:',OUT/'camera_autonomy.webm',control.result)

if __name__=='__main__':run()
