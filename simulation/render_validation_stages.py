"""Gallery evidence from the current simulated CAD, never a substitute mesh."""
from pathlib import Path
import sys,json
import numpy as np
import mujoco
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'simulation'))
from model import ArmSimulation
from grasp_demo import setup_seeded_grasp

OUT=ROOT/'results'/'design_stages';OUT.mkdir(exist_ok=True)
FONT=ROOT/'software'/'freecad'/'FreeCAD_1.1.4-Windows-x86_64-py311'/'data'/'fonts'/'osifont.ttf'
def font(size):
    try:return ImageFont.truetype(str(FONT),size)
    except OSError:return ImageFont.load_default(size=size)
F=font(23);SMALL=font(19);BIG=font(31)
def canvas(title,subtitle):
    image=Image.new('RGB',(1440,1120),(15,23,27));draw=ImageDraw.Draw(image)
    draw.text((28,20),title,font=BIG,fill=(233,245,246))
    draw.text((28,63),subtitle,font=SMALL,fill=(146,182,191))
    return image
def frame(sim,width=692,height=442,axes=False):
    body=mujoco.mj_name2id(sim.m,mujoco.mjtObj.mjOBJ_BODY,'palm_base')
    R=sim.d.xmat[body].reshape(3,3);normal=R@np.array([1,-.3,.17]);normal/=np.linalg.norm(normal)
    camera=mujoco.MjvCamera();mujoco.mjv_defaultCamera(camera)
    camera.lookat[:]=sim.d.xpos[body]+R@np.array([0,0,.095]);camera.distance=.36
    camera.azimuth=np.degrees(np.arctan2(-normal[1],-normal[0]));camera.elevation=-np.degrees(np.arcsin(normal[2]))
    options=mujoco.MjvOption();options.geomgroup[3]=0
    options.flags[mujoco.mjtVisFlag.mjVIS_JOINT]=bool(axes)
    renderer=mujoco.Renderer(sim.m,width=width,height=height)
    renderer.update_scene(sim.d,camera=camera,scene_option=options)
    result=Image.fromarray(renderer.render());renderer.close();return result
def panel(out,image,column,row,label,detail):
    x=22+column*708;y=110+row*487
    out.paste(image,(x,y));draw=ImageDraw.Draw(out)
    draw.text((x+10,y+8),label,font=F,fill=(242,246,247),stroke_width=2,stroke_fill=(18,28,34))
    draw.text((x+4,y+448),detail,font=SMALL,fill=(155,211,198))
def run():
    sim=ArmSimulation()
    image=canvas('06  |  Actual articulated CAD in MuJoCo',f'{sim.m.nmesh} CAD mesh components | 25 active joints | separate convex collision surfaces')
    for i,(name,title) in enumerate([('open','Open hand'),('fist','Finger closure'),('peace','Independent spread'),('pinch','Thumb-index pad contact')]):
        sim.reset();sim.preset(name);sim.step(2000)
        detail='Surface gap: %.2f mm (contact margin active)'%(sim.state()['pinch_surface_gap_m']*1000) if name=='pinch' else 'Rigid-body physics with gravity and bounded servo effort'
        panel(image,frame(sim),i%2,i//2,title,detail)
    image.save(OUT/'06_articulation.png')
    report=json.loads((ROOT/'results'/'v2_precision.json').read_text())
    tracking=report['checks']['all_25_independent_joint_tracking']
    repeat=report['checks']['loaded_cartesian_return_precision']
    if not (report['passed'] and tracking['max_joint_error_deg']<.01 and tracking['max_palm_target_error_mm']<.01 and repeat['repeatability_mm']<.01):
        raise RuntimeError('Precision captions require a current passing report below displayed bounds')
    sim.reset();sim.set_targets({'joint_1_waist':.15,'joint_2_shoulder':.7,'joint_3_elbow':.4,'joint_4_wrist_pitch':-.9,'joint_5_wrist_roll':.2});sim.step(2000)
    image=canvas('07  |  Measured digital-model accuracy','Independent joint moves and repeated loaded returns; hardware precision is not validated')
    image.paste(frame(sim,900,900,True),(20,110));draw=ImageDraw.Draw(image)
    rows=[('25 / 25','Independent servo checks'),('< 0.01 deg','Max measured free-space error'),('< 0.01 mm','Max measured palm target error'),('< 0.01 mm','Repeated palm return spread'),('Bounded effort','Gravity bias uses same actuators'),('Contacts active','Blocked targets may not be reached')]
    for i,(main,caption) in enumerate(rows):
        y=140+i*142;draw.text((954,y),main,font=BIG,fill=(86,217,184));draw.text((954,y+45),caption,font=SMALL,fill=(216,231,234))
    draw.text((28,1053),'Source: results/v2_precision.json | Blue axes show actual modeled joints.',font=F,fill=(146,182,191))
    image.save(OUT/'07_precision.png')
    sim.reset();setup_seeded_grasp(sim)
    image=canvas('08  |  Seeded grasp retention and lift','60 g object begins in the upward palm; physics only after reset; this is not autonomous pickup')
    samples=[]
    for i,(label,seconds,action) in enumerate([('1  Settle',.6,None),('2  Close fingers',1.8,lambda:sim.preset('fist')),('3  Lift',2.5,lambda:sim.set_targets({'joint_2_shoulder':-.3,'joint_3_elbow':-.55,'joint_4_wrist_pitch':.3})),('4  Hold',2,None)]):
        if action:action()
        sim.step(round(seconds/sim.m.opt.timestep));state=sim.state();z=state['object_position'][2]
        samples.append(dict(phase=label,object_z_m=z,time_s=state['time']))
        panel(image,frame(sim),i%2,i//2,label,'Object height: %.1f mm | No object pose edits after reset'%(1000*z))
    lift=1000*(samples[-1]['object_z_m']-samples[1]['object_z_m'])
    draw=ImageDraw.Draw(image);draw.text((28,1080),'Measured lift: %.1f mm | Retained by real modeled contacts | See v2_grasp_validation.json'%lift,font=SMALL,fill=(220,234,237))
    image.save(OUT/'08_grasp.png')
    (ROOT/'results'/'v2_gallery_evidence.json').write_text(json.dumps({'model':sim.spec['name'],'sources':['06_articulation.png','07_precision.png','08_grasp.png'],'precision_passed':report['passed'],'seeded_grasp_phases':samples,'lift_mm':lift,'render_source':'Current MuJoCo CAD mesh geometry; normally hidden collision group3 omitted'},indent=2))
    sim.close();print('Saved 06_articulation.png, 07_precision.png, 08_grasp.png')
if __name__=='__main__':run()
