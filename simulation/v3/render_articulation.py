"""Seven individually demonstrated arm axes, then actual articulated hand gestures."""
from pathlib import Path
import importlib.util,json
import numpy as np,mujoco,cv2
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'results'/'v3'
spec=importlib.util.spec_from_file_location('v3runtime',Path(__file__).with_name('model.py'));runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
FONT=ROOT/'software'/'freecad'/'FreeCAD_1.1.4-Windows-x86_64-py311'/'data'/'fonts'/'osifont.ttf'
def run():
    sim=runtime.ArmSimulation();renderer=mujoco.Renderer(sim.m,height=800,width=1200);camera=mujoco.MjvCamera();mujoco.mjv_defaultCamera(camera)
    options=mujoco.MjvOption();options.geomgroup[3]=0;options.geomgroup[4]=0
    fps=20;writer=cv2.VideoWriter(str(OUT/'full_arm_articulation.webm'),cv2.VideoWriter_fourcc(*'VP80'),fps,(1200,900))
    if not writer.isOpened():raise RuntimeError('VP8 encoder unavailable')
    try:font=ImageFont.truetype(str(FONT),27);small=ImageFont.truetype(str(FONT),21)
    except OSError:font=ImageFont.load_default(size=27);small=ImageFont.load_default(size=21)
    frames=0;phases=[];home=np.array([j['home'] for j in sim.joints])
    phasespec=[('Human-shaped full arm',None,None),('1 Shoulder abduction','shoulder_abduction',.45),('2 Shoulder flexion','shoulder_flexion',.65),('3 Humeral axial rotation','shoulder_rotation',-.60),('4 Elbow flexion','elbow_flexion',1.70),('5 Forearm pronation','forearm_pronation',1.30),('6 Wrist flexion','wrist_flexion',.70),('7 Wrist deviation','wrist_deviation',.40),('Hand: five articulated fingers','fist',None),('Hand: independent finger spread','peace',None),('Hand: open palm','open',None)]
    try:
        for index,(title,command,value) in enumerate(phasespec):
            sim.set_targets(dict(zip(sim.names[:7],home[:7])));sim.preset('open')
            if command in ('fist','peace','open'):sim.preset(command)
            elif command:sim.set_targets({command:value})
            phases.append(dict(start_s=frames/fps,title=title,command=command,target=value))
            for frame in range(fps*3):
                sim.step(25)
                if index<8:camera.lookat[:]=[.20,0,.89];camera.distance=1.02;camera.azimuth=120;camera.elevation=-12
                else:
                    body=mujoco.mj_name2id(sim.m,mujoco.mjtObj.mjOBJ_BODY,'palm_base');R=sim.d.xmat[body].reshape(3,3);normal=R@np.array([1,-.25,.15]);normal/=np.linalg.norm(normal);camera.lookat[:]=sim.d.xpos[body]+R@np.array([0,0,.09]);camera.distance=.36;camera.azimuth=np.degrees(np.arctan2(-normal[1],-normal[0]));camera.elevation=-np.degrees(np.arcsin(normal[2]))
                renderer.update_scene(sim.d,camera=camera,scene_option=options);renderer.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW]=False
                image=Image.new('RGB',(1200,900),(15,24,30));image.paste(Image.fromarray(renderer.render()),(0,85));draw=ImageDraw.Draw(image)
                draw.text((25,13),'ANTHROARM-27 | FULL HUMAN-SHAPED UPPER LIMB',font=font,fill=(230,240,244));draw.text((25,50),title,font=small,fill=(92,220,192));draw.rectangle((0,852,1200,900),fill=(15,24,30));draw.text((25,864),'Actual CAD meshes | 7 arm + 20 hand axes | gravity and bounded actuators',font=small,fill=(178,202,211))
                writer.write(cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR));frames+=1
                if frame==fps*2 and index in (0,4,8,9):image.save(OUT/('articulation_'+str(index)+'.png'))
    finally:writer.release();renderer.close();sim.close()
    (OUT/'articulation_video.json').write_text(json.dumps(dict(file='full_arm_articulation.webm',fps=fps,duration_s=frames/fps,phases=phases,source='Integrated MuJoCo dynamics with exact native CAD STL surfaces'),indent=2));print(OUT/'full_arm_articulation.webm')
if __name__=='__main__':run()
