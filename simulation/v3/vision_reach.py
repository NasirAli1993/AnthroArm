"""Autonomous reach/touch driven by actual rendered RGB-D pixels.

Known camera calibration and known upright 50 mm orange target are assumptions.
Object body position is deliberately never read by this control module.
"""
from pathlib import Path
import importlib.util,json
import cv2,numpy as np,mujoco
ROOT=Path(__file__).resolve().parents[2]

class RGDBCamera:
    def __init__(self,sim,width=640,height=480):
        self.sim=sim;self.width=width;self.height=height;self.renderer=mujoco.Renderer(sim.m,height=height,width=width)
        self.camera_id=mujoco.mj_name2id(sim.m,mujoco.mjtObj.mjOBJ_CAMERA,'vision_camera')
        fovy=np.deg2rad(sim.m.cam_fovy[self.camera_id]);self.fy=.5*height/np.tan(.5*fovy);self.fx=self.fy;self.cx=(width-1)/2;self.cy=(height-1)/2
        self.latest_rgb=None;self.latest_depth=None;self.last_detection={}
    def capture(self):
        option=mujoco.MjvOption();option.geomgroup[3]=0;option.geomgroup[4]=0
        self.renderer.update_scene(self.sim.d,camera='vision_camera',scene_option=option)
        self.renderer.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW]=False
        self.renderer.disable_depth_rendering();rgb=self.renderer.render().copy()
        self.renderer.enable_depth_rendering();depth=self.renderer.render().copy();self.renderer.disable_depth_rendering()
        hsv=cv2.cvtColor(rgb,cv2.COLOR_RGB2HSV);mask=cv2.inRange(hsv,np.array([2,125,80],dtype=np.uint8),np.array([23,255,255],dtype=np.uint8))
        # Choose the orange connected component in the calibrated worktable ROI.
        count,labels,stats,centroids=cv2.connectedComponentsWithStats(mask)
        candidates=[]
        R=self.sim.d.cam_xmat[self.camera_id].reshape(3,3);position=self.sim.d.cam_xpos[self.camera_id]
        for i in range(1,count):
            if stats[i,cv2.CC_STAT_AREA]<=45:continue
            yy,xx=np.where(labels==i);zz=depth[yy,xx]
            pts=np.c_[(xx-self.cx)*zz/self.fx,-(yy-self.cy)*zz/self.fy,-zz]@R.T+position
            center=np.median(pts,axis=0);top=np.quantile(pts[:,2],.98)
            if .14<center[0]<.68 and abs(center[1])<.29 and .62<top<.665:candidates.append(i)
        result={'detected':False,'source':'rendered RGB segmentation + metric depth','ground_truth_object_pose_used':False}
        overlay=rgb.copy()
        if candidates:
            c=max(candidates,key=lambda i:stats[i,cv2.CC_STAT_AREA]);ys,xs=np.where(labels==c);z=depth[ys,xs]
            camera_points=np.c_[(xs-self.cx)*z/self.fx,-(ys-self.cy)*z/self.fy,-z]
            world=camera_points@R.T+position
            # Top surface is visible before reach. Use its centre and known half-height.
            top_z=float(np.quantile(world[:,2],.98));top=world[world[:,2]>top_z-.003]
            if len(top)>15:
                lower=np.quantile(top[:,:2],.02,axis=0);upper=np.quantile(top[:,:2],.98,axis=0);center=np.r_[(lower+upper)/2,top_z-.025]
                x,y,w,h,area=stats[c];cv2.rectangle(overlay,(x,y),(x+w,y+h),(65,255,130),2);cv2.circle(overlay,tuple(np.rint(centroids[c]).astype(int)),4,(255,255,255),-1)
                text='RGB-D target (m): %.3f %.3f %.3f'%tuple(center);cv2.putText(overlay,text,(15,25),cv2.FONT_HERSHEY_SIMPLEX,.55,(240,255,240),2,cv2.LINE_AA)
                result.update(detected=True,center_world_m=center.tolist(),top_surface_z_m=top_z,bbox_pixels=[int(x),int(y),int(w),int(h)],orange_pixels=int(area),top_surface_pixels=len(top),calibration={'fx':self.fx,'fy':self.fy,'cx':self.cx,'cy':self.cy,'width':self.width,'height':self.height,'camera_world_position_m':position.tolist(),'camera_world_rotation':R.tolist()},assumptions='Known upright 50 mm orange cube; top surface visible; camera extrinsics calibrated.')
        if not result['detected']:cv2.putText(overlay,'No fresh target estimate (occluded or absent)',(15,25),cv2.FONT_HERSHEY_SIMPLEX,.50,(255,200,120),2,cv2.LINE_AA)
        self.latest_rgb=overlay;self.latest_depth=depth;self.last_detection=result;return result
    def close(self):self.renderer.close()

class VisionReach:
    def __init__(self,sim):
        self.sim=sim;self.camera=RGDBCamera(sim);self.active=False;self.phase='idle';self.result={};self.target=None;self.waypoint=None;self.events=[];self.started=0;self.phase_started=0
        self.downward_palm_rotation=np.array([[0,0,1],[0,1,0],[-1,0,0]],dtype=float)
        self.object_geom=mujoco.mj_name2id(sim.m,mujoco.mjtObj.mjOBJ_GEOM,'object_geom');self.table_geom=mujoco.mj_name2id(sim.m,mujoco.mjtObj.mjOBJ_GEOM,'worktable')
        self.initial_detection={};self.initial_rgb=None;self.initial_depth=None;self.control_counter=0
    @property
    def latest_rgb(self):return self.camera.latest_rgb
    @property
    def latest_depth(self):return self.camera.latest_depth
    @property
    def state(self):return dict(active=self.active,phase=self.phase,target_estimate=self.target,waypoint=self.waypoint,result=self.result,events=self.events,detection=self.camera.last_detection,initial_detection=self.initial_detection,method='Actual virtual RGB-D camera -> OpenCV segmentation -> calibrated 3D backprojection -> IK -> effort-limited physics -> contact stop',autonomous_pickup=False)
    def start(self):
        self.sim.hold();self.sim.preset('open');self.active=True;self.phase='detect';self.started=float(self.sim.d.time);self.phase_started=self.started;self.events=[];self.result={};self.target=None;self.waypoint=None;self.control_counter=0;self.initial_detection={};return self.state
    def stop(self,reason='Stopped by user'):
        self.active=False;self.sim.hold();self.phase='stopped';self.result=dict(success=False,reason=reason);return self.state
    def _transition(self,phase):
        self.phase=phase;self.phase_started=float(self.sim.d.time);self.events.append(dict(time_s=float(self.sim.d.time),phase=phase))
    def _command(self,point,oriented=True):
        result=self.sim.solve_ik(point,self.downward_palm_rotation if oriented else None)
        if not result['success']:
            self.stop('IK target unreachable: '+str(result['error_m']));return False
        self.waypoint=list(map(float,point));return True
    def _arrived(self):
        return self.waypoint is not None and np.linalg.norm(self.sim.d.site_xpos[self.sim.palm_id]-self.waypoint)<.004 and np.max(abs(self.sim.d.qvel[self.sim.vadr[:7]]))<.08
    def step(self,n=1):
        """Use instead of sim.step while active: contact stop checked every 2 ms."""
        for _ in range(int(n)):
            self.sim.step();self.control_counter+=1
            if self.active and self.phase!='detect':
                for ci in range(self.sim.d.ncon):
                    contact=self.sim.d.contact[ci];a,b=int(contact.geom1),int(contact.geom2)
                    if self.object_geom not in (a,b) or self.table_geom in (a,b):continue
                    force=np.zeros(6);mujoco.mj_contactForce(self.sim.m,self.sim.d,ci,force)
                    if force[0]>.03:self.tick();break
            if self.active and self.control_counter%50==0:self.tick()
    def tick(self):
        if not self.active:return self.state
        elapsed=float(self.sim.d.time)-self.started
        if elapsed>32:return self.stop('Vision reach timeout')
        # Touch safety is derived from physical contact forces, never object pose.
        contacts=self.sim.state()['contacts']
        object_contacts=[c for c in contacts if 'object_geom' in (c['geom1'],c['geom2']) and 'worktable' not in (c['geom1'],c['geom2']) and c['normal_force']>.03]
        table_contacts=[c for c in contacts if 'worktable' in (c['geom1'],c['geom2']) and 'object_geom' not in (c['geom1'],c['geom2']) and c['normal_force']>1]
        if object_contacts:
            if self.target is None or self.phase in ('detect','raise_clearance'):
                return self.stop('Object contact before camera-guided approach; no autonomous reach credited')
            for contact in object_contacts:
                other=contact['geom2'] if contact['geom1']=='object_geom' else contact['geom1']
                geom=mujoco.mj_name2id(self.sim.m,mujoco.mjtObj.mjOBJ_GEOM,other);body=mujoco.mj_id2name(self.sim.m,mujoco.mjtObj.mjOBJ_BODY,int(self.sim.m.geom_bodyid[geom]))
                if body!='palm_base' and not any(body.startswith(f+'_') for f in ('index','middle','ring','pinky','thumb')):
                    return self.stop('Unexpected arm contact with target; no hand reach credited')
            self.sim.hold();self.active=False;self._transition('contact_stop');self.result=dict(success=True,task='Vision-guided approach and touch',autonomous_pickup=False,contacts=object_contacts,elapsed_seconds=elapsed,ground_truth_object_pose_used_for_control=False);self.camera.capture();return self.state
        if table_contacts:return self.stop('Worktable contact detected; held joint positions')
        if self.phase=='detect':
            detection=self.camera.capture()
            if not detection['detected']:
                if elapsed>3:return self.stop('No orange target detected')
                return self.state
            self.target=detection['center_world_m'];palm=self.sim.d.site_xpos[self.sim.palm_id].copy();palm[2]=max(.90,palm[2]+.12)
            self.initial_detection=detection.copy();self.initial_rgb=self.camera.latest_rgb.copy();self.initial_depth=self.camera.latest_depth.copy()
            if self._command(palm,False):self._transition('raise_clearance')
        elif self.phase=='raise_clearance' and self._arrived():
            goal=np.array(self.target);goal[2]+=.22
            if self._command(goal,True):self._transition('align_above_target')
        elif self.phase=='align_above_target' and self._arrived():
            self._transition('descend_to_touch')
        elif self.phase=='descend_to_touch' and self._arrived():
            goal=np.array(self.waypoint);goal[2]-=.008
            if goal[2]<self.target[2]+.034:return self.stop('Reached visual depth limit without target contact')
            self._command(goal,True)
        return self.state
    def close(self):self.camera.close()

if __name__=='__main__':
    spec=importlib.util.spec_from_file_location('v3model',ROOT/'simulation'/'v3'/'model.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    sim=module.ArmSimulation();controller=VisionReach(sim);controller.start()
    while controller.active:controller.step(50)
    print(json.dumps(controller.state,indent=2));controller.close();sim.close()
