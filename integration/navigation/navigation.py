"""Physical differential drive, range sensing, incremental 2-D SLAM and navigation.

All control uses encoder/laser estimates. Ground truth is exposed only through
evaluation_truth(), never supplied to Slam2D or the path planner. This is a
custom lidar scan-to-map implementation, not ROS Nav2 or graph-loop-closure SLAM.
"""
from __future__ import annotations
import os
from pathlib import Path
ROOT = Path(r'D:\RoboticArm')
for _key, _value in {'TEMP': ROOT/'temp', 'TMP': ROOT/'temp', 'MPLCONFIGDIR': ROOT/'cache/matplotlib'}.items():
    os.environ[_key] = str(_value)
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
import json, math, heapq, argparse, time
import numpy as np
import mujoco
from scipy.spatial import cKDTree
from scipy.ndimage import binary_dilation

HERE = Path(__file__).resolve().parent
OUT = ROOT/'results/integration/navigation'
OUT.mkdir(parents=True, exist_ok=True)

def wrap(a): return (a+np.pi)%(2*np.pi)-np.pi
def transform(points, pose):
    c,s=np.cos(pose[2]),np.sin(pose[2])
    return points@np.array([[c,s],[-s,c]])+pose[:2]

XML = '''<mujoco model="Differential drive navigation laboratory">
<compiler angle="radian"/><option timestep="0.002" gravity="0 0 -9.81" integrator="implicitfast"/>
<visual><global offwidth="960" offheight="720"/><headlight ambient=".5 .5 .5" diffuse=".6 .6 .6"/></visual>
<default><geom friction="1.2 .002 .0001" condim="3" solref=".008 1"/><joint damping=".01"/></default>
<asset><texture name="floor" type="2d" builtin="checker" width="128" height="128" rgb1=".16 .22 .25" rgb2=".19 .26 .28"/>
<material name="floor" texture="floor" texrepeat="12 10"/></asset>
<worldbody><light pos="0 0 5"/>
<geom name="floor" type="plane" size="4 3 .1" material="floor"/>
<geom name="wall_south" type="box" pos="0 -2.55 .3" size="3.1 .05 .3" rgba=".45 .55 .59 1"/>
<geom name="wall_north" type="box" pos="0 2.55 .3" size="3.1 .05 .3" rgba=".45 .55 .59 1"/>
<geom name="wall_west" type="box" pos="-3.05 0 .3" size=".05 2.5 .3" rgba=".45 .55 .59 1"/>
<geom name="wall_east" type="box" pos="3.05 0 .3" size=".05 2.5 .3" rgba=".45 .55 .59 1"/>
<geom name="obstacle_a" type="box" pos="-.55 -.25 .3" size=".35 .58 .3" rgba=".87 .56 .25 1"/>
<geom name="obstacle_b" type="box" pos="1.25 .75 .3" size=".32 .5 .3" rgba=".36 .62 .7 1"/>
<geom name="obstacle_c" type="cylinder" pos="-.65 1.5 .3" size=".25 .3" rgba=".57 .46 .68 1"/>
<body name="base" pos="-2.2 -1.8 .162"><freejoint name="base_free"/>
<geom name="chassis" type="box" size=".19 .16 .055" pos="0 0 0" mass="3" rgba=".15 .76 .63 1"/>
<geom name="lidar_housing" type="cylinder" pos="0 0 .09" size=".055 .035" mass=".1" rgba=".07 .1 .12 1"/>
<geom name="front_marker" type="box" pos=".15 0 .06" size=".035 .08 .009" mass=".01" rgba=".95 .94 .75 1" contype="0" conaffinity="0"/>
<site name="lidar" pos="0 0 .12" size=".005"/>
<body name="left_wheel" pos="0 .185 -.057"><joint name="left_wheel" type="hinge" axis="0 1 0"/>
<geom name="left_tire" type="cylinder" quat=".70710678 .70710678 0 0" size=".105 .025" mass=".25" rgba=".05 .07 .08 1"/></body>
<body name="right_wheel" pos="0 -.185 -.057"><joint name="right_wheel" type="hinge" axis="0 1 0"/>
<geom name="right_tire" type="cylinder" quat=".70710678 .70710678 0 0" size=".105 .025" mass=".25" rgba=".05 .07 .08 1"/></body>
<geom name="caster_front" type="sphere" pos=".155 0 -.12" size=".04" mass=".03" friction=".005 .001 .00001" rgba=".6 .66 .68 1"/>
<geom name="caster_back" type="sphere" pos="-.155 0 -.12" size=".04" mass=".03" friction=".005 .001 .00001" rgba=".6 .66 .68 1"/>
</body></worldbody>
<actuator><velocity name="left_motor" joint="left_wheel" kv="4" forcerange="-2 2" ctrlrange="-12 12"/><velocity name="right_motor" joint="right_wheel" kv="4" forcerange="-2 2" ctrlrange="-12 12"/></actuator>
</mujoco>'''

class NavigationSimulation:
    wheel_radius=.105
    track=.37
    initial_world=np.array([-2.2,-1.8])
    def __init__(self, seed=10, render=False):
        self.rng=np.random.default_rng(seed)
        self.model=mujoco.MjModel.from_xml_string(XML)
        self.data=mujoco.MjData(self.model)
        self.base_id=self.model.body('base').id
        self.lidar_id=self.model.site('lidar').id
        self.left_adr=self.model.joint('left_wheel').qposadr[0]
        self.right_adr=self.model.joint('right_wheel').qposadr[0]
        self.angles=np.linspace(-np.pi,np.pi,180,endpoint=False)
        self.max_range=5.5
        self.renderer=mujoco.Renderer(self.model,720,960) if render else None
        self.camera=mujoco.MjvCamera()
        self.camera.lookat[:]=[0,0,0]
        self.camera.distance=8.1;self.camera.azimuth=90;self.camera.elevation=-65
        self.commanded=(0.,0.)
        self.reset()
    def reset(self):
        mujoco.mj_resetData(self.model,self.data)
        for _ in range(300):mujoco.mj_step(self.model,self.data)
        self.last_enc=self.encoders()
        self.odom=np.zeros(3);self.odometry_delta=np.zeros(3)
        self.collision_steps=0;self.collision_pairs=set();self.steps=0
        return self.observe()
    def encoders(self):return np.array([self.data.qpos[self.left_adr],self.data.qpos[self.right_adr]])
    def command(self,v_m_s,yaw_rate_rad_s):
        v=float(np.clip(v_m_s,-.4,.4));w=float(np.clip(yaw_rate_rad_s,-1.5,1.5))
        self.commanded=(v,w)
        self.data.ctrl[:]=[(v-w*self.track/2)/self.wheel_radius,(v+w*self.track/2)/self.wheel_radius]
    def step(self,dt=.1):
        for _ in range(round(dt/self.model.opt.timestep)):
            mujoco.mj_step(self.model,self.data)
            collision=False
            for k in range(self.data.ncon):
                con=self.data.contact[k]
                names=[self.model.geom(int(g)).name for g in [con.geom1,con.geom2]]
                if any(n.startswith(('wall_','obstacle_')) for n in names) and any(n in ('chassis','left_tire','right_tire','caster_front','caster_back','lidar_housing') for n in names):
                    collision=True;self.collision_pairs.add(tuple(names))
            self.collision_steps+=int(collision)
        enc=self.encoders();d=(enc-self.last_enc)*self.wheel_radius*1.008
        self.last_enc=enc
        d+=self.rng.normal(0,.00006,2)
        ds=d.mean();da=(d[1]-d[0])/self.track
        self.odometry_delta=np.array([ds,0,da])
        self.odom[:2]+=ds*np.array([np.cos(self.odom[2]+da/2),np.sin(self.odom[2]+da/2)])
        self.odom[2]=wrap(self.odom[2]+da);self.steps+=1
        return self.observe()
    def observe(self):
        origin=self.data.site_xpos[self.lidar_id].copy()
        matrix=self.data.site_xmat[self.lidar_id].reshape(3,3)
        ranges=[];geom_id=np.zeros(1,dtype=np.int32)
        for a in self.angles:
            direction=matrix@np.array([np.cos(a),np.sin(a),0.])
            dist=mujoco.mj_ray(self.model,self.data,origin,direction,None,1,self.base_id,geom_id)
            value=self.max_range if dist<0 else min(float(dist),self.max_range)
            ranges.append(float(np.clip(value+self.rng.normal(0,.006),.03,self.max_range)))
        return {'stamp':float(self.data.time),'ranges':np.array(ranges),'angle_min':float(self.angles[0]),'angle_increment':float(self.angles[1]-self.angles[0]),'range_min':.03,'range_max':self.max_range,'encoder_delta':self.odometry_delta.copy(),'wheel_odometry':self.odom.copy(),'wheel_positions':self.encoders()}
    def evaluation_truth(self):
        mat=self.data.xmat[self.base_id].reshape(3,3)
        return np.array([*(self.data.xpos[self.base_id,:2]-self.initial_world),np.arctan2(mat[1,0],mat[0,0])])
    def get_state(self):
        return {'stamp':float(self.data.time),'wheel_odometry':self.odom.tolist(),'cmd_vel':list(self.commanded),'contacts_with_environment':self.collision_steps,'ground_truth_for_evaluation_only':self.evaluation_truth().tolist()}
    def render(self):
        if self.renderer is None:self.renderer=mujoco.Renderer(self.model,720,960)
        self.renderer.update_scene(self.data,self.camera)
        return self.renderer.render()
    def close(self):
        if self.renderer:self.renderer.close()

class Slam2D:
    """Odometry-seeded ICP against accumulated laser endpoints + log-odds map.

    Initial pose defines the local map origin. No simulator state, wall geometry
    or goal coordinates enter the scan alignment. No global pose graph exists.
    """
    resolution=.08
    origin=np.array([-1.4,-1.2])
    shape=(78,94)
    def __init__(self,scan_matching=True):
        self.pose=np.zeros(3);self.cloud=np.zeros((0,2));self.tree=None
        self.logodds=np.zeros(self.shape,dtype=float)
        self.scan_matching=scan_matching;self.matches=[];self.rejected=0;self.update_count=0
    def world_to_cell(self,point):return np.floor((np.asarray(point)-self.origin)/self.resolution).astype(int)
    def cell_to_world(self,cell):return self.origin+(np.asarray(cell)+.5)*self.resolution
    def align(self,local,prediction):
        pose=prediction.copy()
        if self.tree is None or not self.scan_matching:return pose
        for _ in range(18):
            src=transform(local,pose)
            dist,idx=self.tree.query(src)
            good=dist<.45
            if good.sum()<35:self.rejected+=1;return prediction
            threshold=np.quantile(dist[good],.88)
            good&=dist<=max(threshold,.025)
            p,q=src[good],self.cloud[idx[good]]
            pc,qc=p.mean(0),q.mean(0)
            u,_,vt=np.linalg.svd((p-pc).T@(q-qc))
            rot=vt.T@u.T
            if np.linalg.det(rot)<0:vt[-1]*=-1;rot=vt.T@u.T
            translation=qc-rot@pc
            delta_angle=np.arctan2(rot[1,0],rot[0,0])
            pose[:2]=rot@pose[:2]+translation;pose[2]=wrap(pose[2]+delta_angle)
            if np.linalg.norm(translation)<.0005 and abs(delta_angle)<.0003:break
        if np.linalg.norm(pose[:2]-prediction[:2])>.22 or abs(wrap(pose[2]-prediction[2]))>.25:
            self.rejected+=1;return prediction
        self.matches.append(float(np.mean(dist[good])))
        return pose
    def update(self,obs):
        ds,_,da=obs['encoder_delta'];prediction=self.pose.copy()
        prediction[:2]+=ds*np.array([np.cos(prediction[2]+da/2),np.sin(prediction[2]+da/2)])
        prediction[2]=wrap(prediction[2]+da)
        angles=obs['angle_min']+np.arange(len(obs['ranges']))*obs['angle_increment']
        local=np.column_stack((np.cos(angles),np.sin(angles)))*obs['ranges'][:,None]
        hit=obs['ranges']<obs['range_max']-.025
        self.pose=self.align(local[hit],prediction)
        endpoints=transform(local,self.pose)
        start=self.world_to_cell(self.pose[:2]);h,w=self.shape
        free_cells=[];hit_cells=[]
        for endpoint,is_hit in zip(endpoints,hit):
            end=self.world_to_cell(endpoint);count=max(abs(end-start))+1
            ray=np.rint(np.linspace(start,end,count)).astype(int)
            ray=ray[(ray[:,0]>=0)&(ray[:,0]<w)&(ray[:,1]>=0)&(ray[:,1]<h)]
            if len(ray):
                free_cells.extend(ray[:-1] if is_hit else ray)
                if is_hit and np.all(ray[-1]==end):hit_cells.append(end)
        if free_cells:
            cells=np.unique(np.array(free_cells),axis=0);self.logodds[cells[:,1],cells[:,0]]-=.38
        if hit_cells:
            cells=np.unique(np.array(hit_cells),axis=0);self.logodds[cells[:,1],cells[:,0]]+=.95
        np.clip(self.logodds,-5,5,out=self.logodds)
        if self.update_count%3==0:
            merged=np.vstack((self.cloud,endpoints[hit]))
            key=np.floor(merged/.035).astype(int)
            _,idx=np.unique(key,axis=0,return_index=True)
            self.cloud=merged[idx];self.tree=cKDTree(self.cloud)
        self.update_count+=1
        return self.pose.copy()
    def occupancy(self):
        result=np.full(self.shape,-1,dtype=np.int16)
        result[self.logodds<-.55]=0;result[self.logodds>.65]=100
        return result
    def plan(self,goal,allow_unknown=False):
        occ=self.occupancy();radius=int(np.ceil(.31/self.resolution))
        yy,xx=np.ogrid[-radius:radius+1,-radius:radius+1]
        blocked=binary_dilation(occ==100,structure=xx*xx+yy*yy<=radius*radius)
        if not allow_unknown:blocked|=occ==-1
        start=tuple(self.world_to_cell(self.pose[:2]));end=tuple(self.world_to_cell(goal));h,w=occ.shape
        if not(0<=end[0]<w and 0<=end[1]<h) or blocked[end[1],end[0]]:return []
        blocked[start[1],start[0]]=False
        pq=[(0,start)];cost={start:0};came={}
        for _ in range(h*w*3):
            if not pq:break
            _,cur=heapq.heappop(pq)
            if cur==end:
                path=[cur]
                while cur in came:cur=came[cur];path.append(cur)
                return np.array([self.cell_to_world(c) for c in path[::-1]])
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
                nb=(cur[0]+dx,cur[1]+dy)
                if not(0<=nb[0]<w and 0<=nb[1]<h) or blocked[nb[1],nb[0]]:continue
                if dx and dy and(blocked[cur[1],nb[0]] or blocked[nb[1],cur[0]]):continue
                step=np.hypot(dx,dy)*(2.3 if occ[nb[1],nb[0]]==-1 else 1)
                new=cost[cur]+step
                if new<cost.get(nb,1e20):
                    cost[nb]=new;came[nb]=cur;heapq.heappush(pq,(new+np.hypot(end[0]-nb[0],end[1]-nb[1]),nb))
        return []

class MissionRunner:
    def __init__(self,seed=10,render=False):
        self.sim=NavigationSimulation(seed=seed,render=render);self.slam=Slam2D()
        self.observation=self.sim.observe();self.slam.update(self.observation)
        self.sensor_log=[self.sensor_record(self.observation)]
        self.path=[];self.trace=[];self.metrics=[];self.frames=[];self.goal=None;self.phase='initializing'
        self.emergency_stops=0;self.replans=0
    def controller(self,path,goal):
        pose=self.slam.pose
        if len(path)<2:return 0.,.45
        d=np.linalg.norm(path-pose[:2],axis=1);near=int(np.argmin(d));target=path[-1]
        for point in path[near:]:
            if np.linalg.norm(point-pose[:2])>=.32:target=point;break
        yaw=wrap(np.arctan2(*(target-pose[:2])[::-1])-pose[2])
        w=float(np.clip(2.6*yaw,-1.2,1.2))
        v=.32*max(0.,np.cos(yaw))**2
        if abs(yaw)>.75:v=0.
        angles=self.observation['angle_min']+np.arange(len(self.observation['ranges']))*self.observation['angle_increment']
        forward=self.observation['ranges'][np.abs(angles)<.36]
        nearest=float(forward.min())
        if v>0 and nearest<.40:v=0.;self.emergency_stops+=1
        elif nearest<.70:v=min(v,.14)
        return v,w
    @staticmethod
    def sensor_record(obs):
        return {key:(value.tolist() if isinstance(value,np.ndarray) else value) for key,value in obs.items()}
    def advance(self,goal,phase='navigation',allow_unknown=False):
        self.goal=np.array(goal);self.phase=phase
        if self.sim.steps%8==0 or len(self.path)<2:
            self.path=self.slam.plan(goal,allow_unknown=allow_unknown);self.replans+=1
        v,w=self.controller(self.path,goal)
        pose=self.drive(v,w,phase)
        return float(np.linalg.norm(pose[:2]-np.array(goal)))<.15
    def drive(self,v,w,phase='manual'):
        self.phase=phase
        self.sim.command(v,w);self.observation=self.sim.step(.1);pose=self.slam.update(self.observation)
        self.sensor_log.append(self.sensor_record(self.observation))
        truth=self.sim.evaluation_truth()
        sample={'time':float(self.sim.data.time),'phase':phase,'estimate':pose.tolist(),'wheel_odometry':self.sim.odom.tolist(),'evaluation_truth':truth.tolist(),'position_error_m':float(np.linalg.norm(pose[:2]-truth[:2])),'yaw_error_rad':float(abs(wrap(pose[2]-truth[2]))),'cmd_vel':[v,w]}
        self.trace.append(sample)
        return pose
    def get_state(self):
        return {'time':float(self.sim.data.time),'phase':self.phase,'estimated_pose':self.slam.pose.tolist(),'goal':None if self.goal is None else self.goal.tolist(),'cmd_vel':list(self.sim.commanded),'path':np.asarray(self.path).tolist(),'map':self.slam.occupancy().tolist(),'map_origin':self.slam.origin.tolist(),'map_resolution':self.slam.resolution,'scan':{'ranges':self.observation['ranges'].tolist(),'angle_min':self.observation['angle_min'],'angle_increment':self.observation['angle_increment'],'range_min':self.observation['range_min'],'range_max':self.observation['range_max']},'wheel_odometry':self.sim.odom.tolist()}

def jsonable(value):
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,np.generic):return value.item()
    raise TypeError(type(value).__name__)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--smoke',action='store_true');args=p.parse_args()
    sim=NavigationSimulation()
    sim.command(.2,0)
    for _ in range(40):sim.step()
    print(json.dumps(sim.get_state(),indent=2));sim.close()
