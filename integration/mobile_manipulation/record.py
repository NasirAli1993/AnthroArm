from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).parent))
import numpy as np,mujoco,cv2
from PIL import Image,ImageDraw,ImageFont
from mission import mission,OUT,ROOT
FONT=ROOT/'software/freecad/FreeCAD_1.1.4-Windows-x86_64-py311/data/fonts/osifont.ttf'
def font(size):
    try:return ImageFont.truetype(str(FONT),size)
    except OSError:return ImageFont.load_default(size=size)

def main():
    renderer=None;detail=None;writer=cv2.VideoWriter(str(OUT/'mobile_camera_grasp.webm'),cv2.VideoWriter_fourcc(*'VP80'),10,(1440,900))
    frames=0;events=[];last='';posters={}
    if not writer.isOpened():raise RuntimeError('WebM writer unavailable')
    def capture(sim,phase,step,slam):
        nonlocal renderer,detail,frames,last
        if renderer is None:
            renderer=mujoco.Renderer(sim.m,height=720,width=840);detail=mujoco.Renderer(sim.m,height=450,width=560)
        cam=mujoco.MjvCamera();mujoco.mjv_defaultCamera(cam);cam.lookat[:]=[-.08,0,.65];cam.distance=2.05;cam.azimuth=110;cam.elevation=-18
        close=mujoco.MjvCamera();mujoco.mjv_defaultCamera(close);close.lookat[:]=[.38,0,max(.66,float(sim.d.xpos[sim.object_id,2])+.025)];close.distance=.42;close.azimuth=115;close.elevation=-20
        opt=mujoco.MjvOption();opt.geomgroup[2]=0;opt.geomgroup[3]=0;opt.geomgroup[4]=0
        renderer.update_scene(sim.d,camera=cam,scene_option=opt);renderer.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW]=False
        detail.update_scene(sim.d,camera=close,scene_option=opt);detail.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW]=False
        canvas=Image.new('RGB',(1440,900),(15,24,30));canvas.paste(Image.fromarray(renderer.render()),(14,110));canvas.paste(Image.fromarray(detail.render()),(866,110));draw=ImageDraw.Draw(canvas)
        draw.text((24,14),'MOBILE ANTHROARM | ONE CONTINUOUS PHYSICS MISSION',font=font(27),fill=(230,244,249))
        draw.text((24,58),phase.upper()+' | wheel drive -> RGB-D -> learned contact grasp',font=font(23),fill=(93,218,188))
        lift=(sim.d.xpos[sim.object_id,2]-.618)*1000
        lines=[f'Simulation time: {sim.d.time:.1f} s',f'Lidar-map X: {slam.pose[0]:.3f} m',f'Cube lift: {lift:.1f} mm','29 bounded motors','Free base and free cube']
        for i,text in enumerate(lines):draw.text((875,578+i*33),text,font=font(23),fill=(215,232,239))
        occ=slam.occupancy();rgb=np.empty((*occ.shape,3),dtype=np.uint8);rgb[:]=[80,95,105];rgb[occ==0]=[222,232,235];rgb[occ==100]=[22,28,32]
        grid=Image.fromarray(np.flipud(rgb)).resize((215,175),resample=Image.Resampling.NEAREST);canvas.paste(grid,(1204,585));draw.text((1206,768),'Actual lidar map',font=font(18),fill=(170,208,218))
        draw.text((24,846),'Motor-braked 80 kg chassis | 27-axis CAD arm | no world weld or object attachment',font=font(23),fill=(210,227,235))
        draw.text((24,877),'Straight docking lane; fixed calibrated external camera; known 36 mm cube. Simulation only.',font=font(19),fill=(150,174,187))
        writer.write(cv2.cvtColor(np.asarray(canvas),cv2.COLOR_RGB2BGR));frames+=1
        if phase!=last:events.append(dict(phase=phase,video_time_s=(frames-1)/10,simulation_time_s=float(sim.d.time)));last=phase
        if phase in ('drive','hold','settle'):posters[phase]=canvas.copy()
    try:result=mission(callback=capture,report_name='video_trial.json')
    finally:
        writer.release()
        if renderer:renderer.close()
        if detail:detail.close()
    for phase,img in posters.items():img.save(OUT/f'mobile_{phase}.png')
    cap=cv2.VideoCapture(str(OUT/'mobile_camera_grasp.webm'));decoded=0
    while True:
        ok,_=cap.read()
        if not ok:break
        decoded+=1
    cap.release()
    report=dict(file='mobile_camera_grasp.webm',frames=frames,decoded_frames=decoded,fps=10,duration_s=frames/10,success=result['success'],events=events,source='Actual integrated MuJoCo frames; lidar walls hidden visually for an unobstructed view, still physically present')
    (OUT/'video.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)

if __name__=='__main__':main()
