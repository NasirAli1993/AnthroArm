"""Supervised grasp policy + contact-gated task controller for the V3 arm.

No object poses, constraints, or external forces are changed by this controller.
Input is an estimated upright cube centre and known/detected cube edge length.
The trajectory stages are scripted; the ten grasp parameters are learned.
"""
from pathlib import Path
import json
import numpy as np
import mujoco

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = Path(__file__).with_name('policy.json')
R_DOWN = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]], dtype=float)
BASE = np.array([-.035, 0, .022, 1.4, 1.6, 1.3, 1.3, .5, .7, .7])

def configure_episode(sim, size=.036, mass=.06, x=.4, y=0.):
    """Configure a new tabletop trial BEFORE sensing/control, then settle physics.

    This is the sole intentional object-pose initialization. Never call while
    a grasp controller is active. Centre returned is spawn metadata, not a
    camera detection; a vision-integrated caller must observe the settled cube.
    """
    if not .032 <= size <= .042 or not .02 <= mass <= .10:
        raise ValueError('Demo domain: 32..42 mm cubes, 20..100 g')
    sim.reset()
    gid=mujoco.mj_name2id(sim.m,mujoco.mjtObj.mjOBJ_GEOM,'object_geom')
    jid=mujoco.mj_name2id(sim.m,mujoco.mjtObj.mjOBJ_JOINT,'object_free')
    addr=int(sim.m.jnt_qposadr[jid])
    sim.m.geom_size[gid]=size/2
    sim.m.body_mass[sim.object_id]=mass
    sim.m.body_inertia[sim.object_id]=mass*size*size/6
    mujoco.mj_setConst(sim.m,sim.d)
    sim.reset()
    sim.d.qpos[addr:addr+7]=[x,y,.600+size/2+.001,1.,0.,0.,0.]
    sim.d.qvel[:]=0.
    mujoco.mj_forward(sim.m,sim.d)
    sim.commanded=sim.targets.copy()
    sim.step(300)
    return dict(size_m=size,mass_kg=mass,spawn_centre_m=[x,y,.600+size/2],table_top_z_m=.600)

def object_contacts(sim):
    gid = mujoco.mj_name2id(sim.m, mujoco.mjtObj.mjOBJ_GEOM, 'object_geom')
    result = []
    for index in range(sim.d.ncon):
        c = sim.d.contact[index]
        if gid not in (c.geom1, c.geom2):
            continue
        f = np.zeros(6)
        mujoco.mj_contactForce(sim.m, sim.d, index, f)
        other = c.geom2 if c.geom1 == gid else c.geom1
        name = mujoco.mj_id2name(sim.m, mujoco.mjtObj.mjOBJ_GEOM, int(other))
        if f[0] > .005:
            result.append(dict(geom=name, normal_force_n=float(f[0]), penetration_m=max(0., -float(c.dist))))
    return result

class LearnedGraspController:
    def __init__(self, sim, policy_path=None, parameters=None):
        self.sim = sim
        self.override = None if parameters is None else np.asarray(parameters, dtype=float)
        self.policy_path = Path(policy_path or POLICY_PATH)
        self.policy = None if self.override is not None else json.loads(self.policy_path.read_text())
        self.active = False
        self.phase = 'idle'
        self.error = ''
        self.phase_steps = 0
        self.history = []
        self.parameters = None
        self.contacts_at_close = []
        self.contact_loss_steps = 0

    def predict(self, size):
        if self.override is not None:
            return self.override.copy()
        domain = self.policy['size_domain_m']
        if not domain[0] <= size <= domain[1]:
            raise ValueError(f'Cube size outside trained domain {domain}')
        x = (size - self.policy['size_center_m']) / self.policy['size_scale_m']
        return np.array([1., x]) @ np.asarray(self.policy['coefficients'])

    def start(self, object_estimate_xyz, object_size_m=.036):
        estimate = np.asarray(object_estimate_xyz, dtype=float)
        if estimate.shape != (3,) or not np.isfinite(estimate).all():
            raise ValueError('Expected a finite estimated cube centre, in world metres')
        self.cancel()
        self.parameters = self.predict(float(object_size_m))
        self.estimate = estimate.copy()
        self.size = float(object_size_m)
        self.goal = estimate + np.array([self.parameters[0], self.parameters[1], self.size/2 + self.parameters[2]])
        self.error = ''
        self.history = []
        self.contacts_at_close = []
        self.contact_loss_steps = 0
        self.active = True
        self.sim.preset('open')
        self._enter('raise')
        return self.state

    def cancel(self):
        if self.active:
            self.sim.hold()
        self.active = False
        self.phase = 'idle'
        self.phase_steps = 0

    def _enter(self, phase):
        self.phase = phase
        self.phase_steps = 0
        self.history.append(dict(phase=phase, time_s=float(self.sim.d.time)))
        target = None
        rotation = R_DOWN
        if phase == 'raise':
            target = self.sim.d.site_xpos[self.sim.palm_id].copy()
            target[2] = .90
            rotation = None
        elif phase in ('approach', 'lift', 'retreat'):
            target = self.goal + [0, 0, .15]
        elif phase in ('descend', 'lower'):
            target = self.goal.copy()
        elif phase == 'close':
            q = {}
            for finger in ('index', 'middle', 'ring', 'pinky'):
                for suffix, value in zip(('mcp_flexion', 'pip', 'dip'), self.parameters[3:6]):
                    q[finger + '_' + suffix] = float(value)
            q.update(zip(('thumb_cmc_opposition', 'thumb_cmc_flexion', 'thumb_mcp_flexion', 'thumb_ip'), self.parameters[6:10].tolist()))
            self.sim.set_targets(q)
        elif phase == 'release':
            self.sim.preset('open')
        if target is not None:
            ik = self.sim.solve_ik(target, rotation)
            if not ik['success']:
                self.error = phase + '_ik_failed'
                self.active = False
                self.phase = 'failed'
                self.sim.hold()

    def step(self, n=1):
        n=int(n)
        if n<0 or n>100000:
            raise ValueError('Step count outside 0..100000')
        stages = [('raise',1.5), ('approach',2.), ('descend',2.), ('close',1.8), ('lift',2.5), ('hold',1.5), ('lower',2.5), ('release',1.8), ('retreat',2.), ('settle',1.)]
        for _ in range(n):
            self.sim.step()
            if not self.active:
                continue
            self.phase_steps += 1
            if self.phase in ('lift','hold'):
                has_hand_contact=any(c['geom']!='worktable' for c in object_contacts(self.sim))
                self.contact_loss_steps=0 if has_hand_contact else self.contact_loss_steps+1
                if self.contact_loss_steps*self.sim.m.opt.timestep>.25:
                    self.error='Hand contact lost during lift/hold'
                    self.active=False
                    self.phase='failed'
                    self.sim.hold()
                    continue
            index = next(i for i, row in enumerate(stages) if row[0] == self.phase)
            if self.phase_steps < round(stages[index][1] / self.sim.m.opt.timestep):
                continue
            if self.phase == 'close':
                self.contacts_at_close = object_contacts(self.sim)
                names = [c['geom'] for c in self.contacts_at_close]
                opposed = any('thumb' in name for name in names) and any(any(f in name for f in ('index','middle','ring','pinky')) for name in names)
                if not opposed:
                    self.error = 'No opposing thumb/finger contacts; pickup refused'
                    self.sim.preset('open')
                    self.phase = 'failed'
                    self.active = False
                    continue
            if index == len(stages)-1:
                self.phase = 'complete'
                self.active = False
            else:
                self._enter(stages[index+1][0])
        return self.state

    @property
    def state(self):
        return dict(active=self.active, phase=self.phase, error=self.error,
                    parameters=None if self.parameters is None else self.parameters.tolist(),
                    policy='optimization demonstration override' if self.override is not None else 'supervised affine regression',
                    contact_count=len(object_contacts(self.sim)),
                    completed_sequence=self.phase=='complete',
                    physical_success_requires_evaluation=True,
                    note='Learned size-conditioned grasp; scripted stages and numerical IK; simulated upright cubes only')
