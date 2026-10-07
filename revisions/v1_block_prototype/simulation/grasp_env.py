"""Gymnasium MuJoCo task scaffold for Aster-25. No trained policy is included.

Actions are bounded joint target increments, observations include robot, object,
contact and target state. Smoke tests validate the interface, not grasp learning.
"""
from pathlib import Path
import os
ROOT = Path(__file__).resolve().parents[1]
os.environ['TEMP'] = os.environ['TMP'] = str(ROOT/'temp')
os.environ['MPLCONFIGDIR'] = str(ROOT/'cache/matplotlib')
import argparse
import json
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import mujoco


class ArmHandGraspEnv(gym.Env):
    metadata = {'render_modes': ['rgb_array'], 'render_fps': 50}

    def __init__(self, render_mode=None, max_steps=500, frame_skip=10):
        super().__init__()
        if render_mode not in (None, 'rgb_array'):
            raise ValueError('Supported render_mode: None or rgb_array')
        self.render_mode = render_mode
        self.m = mujoco.MjModel.from_xml_path(str(ROOT/'simulation/robot.xml'))
        self.d = mujoco.MjData(self.m)
        self.robot_spec = json.loads((ROOT/'design/robot_spec.json').read_text(encoding='utf-8-sig'))
        joint_specs = {x['joint']['name']: x['joint'] for x in self.robot_spec['links'] if x.get('joint')}
        self.joint_ids = self.m.actuator_trnid[:, 0].copy()
        self.names = [mujoco.mj_id2name(self.m, mujoco.mjtObj.mjOBJ_JOINT, int(j)) for j in self.joint_ids]
        self.qadr = self.m.jnt_qposadr[self.joint_ids]
        self.vadr = self.m.jnt_dofadr[self.joint_ids]
        self.low = self.m.jnt_range[self.joint_ids, 0].copy()
        self.high = self.m.jnt_range[self.joint_ids, 1].copy()
        self.home = np.array([joint_specs[name]['home'] for name in self.names])
        self.velocity = np.array([min(joint_specs[name]['velocity'], 1.5) for name in self.names])
        self.object_id = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, 'object')
        self.object_geom = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_GEOM, 'object_geom')
        object_joint = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_JOINT, 'object_free')
        self.object_qadr = int(self.m.jnt_qposadr[object_joint])
        self.object_vadr = int(self.m.jnt_dofadr[object_joint])
        self.palm_site = mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_SITE, 'palm_site')
        self.fingers = ('index', 'middle', 'ring', 'pinky', 'thumb')
        self.tip_sites = [mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_SITE, f'{name}_tip') for name in self.fingers]
        self.geom_finger = {}
        for geom in range(self.m.ngeom):
            name = mujoco.mj_id2name(self.m, mujoco.mjtObj.mjOBJ_GEOM, geom) or ''
            for index, finger in enumerate(self.fingers):
                if name.startswith(finger+'_') and (name.endswith('_shell') or name.endswith('_pad')):
                    self.geom_finger[geom] = index
        self.frame_skip = int(frame_skip)
        self.max_steps = int(max_steps)
        if self.frame_skip < 1 or self.max_steps < 1:
            raise ValueError('frame_skip and max_steps must be positive')
        self.control_dt = float(self.m.opt.timestep*self.frame_skip)
        self.action_space = spaces.Box(-1, 1, shape=(self.m.nu,), dtype=np.float32)
        self.targets = self.home.copy()
        self.last_action = np.zeros(self.m.nu)
        self.step_count = 0
        self.hold_count = 0
        self.rest_height = 0.0
        self.renderer = None
        self.reset()
        self.observation_space = spaces.Box(-np.inf, np.inf, shape=self._observation().shape, dtype=np.float32)

    def finger_object_contacts(self):
        """Count distinct digits with nontrivial normal force on target object."""
        contacts = np.zeros(5)
        force = np.zeros(6)
        for index in range(self.d.ncon):
            contact = self.d.contact[index]
            a, b = int(contact.geom1), int(contact.geom2)
            other = b if a == self.object_geom else a if b == self.object_geom else -1
            if other not in self.geom_finger:
                continue
            mujoco.mj_contactForce(self.m, self.d, index, force)
            if force[0] > .01:
                contacts[self.geom_finger[other]] = 1.0
        return contacts

    def _observation(self):
        obj = self.d.xpos[self.object_id]
        palm = self.d.site_xpos[self.palm_site]
        return np.concatenate([
            self.d.qpos[self.qadr], self.d.qvel[self.vadr], self.targets,
            self.d.qpos[self.object_qadr:self.object_qadr+7],
            self.d.qvel[self.object_vadr:self.object_vadr+6], palm, obj-palm,
            (self.d.site_xpos[self.tip_sites]-obj).flatten(),
            self.finger_object_contacts(), self.last_action,
            [self.rest_height, self.step_count/self.max_steps, self.hold_count/25],
        ]).astype(np.float32)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.m, self.d)
        self.d.qpos[self.qadr] = self.home
        self.targets = self.home.copy()
        self.d.ctrl[:] = self.targets
        if options and options.get('randomize_object', False):
            self.d.qpos[self.object_qadr:self.object_qadr+2] += self.np_random.uniform(-.015, .015, size=2)
        self.last_action = np.zeros(self.m.nu)
        self.step_count = self.hold_count = 0
        mujoco.mj_forward(self.m, self.d)
        for _ in range(150):
            mujoco.mj_step(self.m, self.d)
        self.rest_height = float(self.d.xpos[self.object_id, 2])
        return self._observation(), {'resting_object_z': self.rest_height, 'trained_policy': False}

    def step(self, action):
        action = np.asarray(action, dtype=float)
        if action.shape != (self.m.nu,) or not np.isfinite(action).all():
            raise ValueError(f'Expected {self.m.nu} finite action values')
        action = np.clip(action, -1, 1)
        self.targets = np.clip(self.targets+action*self.velocity*self.control_dt, self.low, self.high)
        self.d.ctrl[:] = self.targets
        for _ in range(self.frame_skip):
            mujoco.mj_step(self.m, self.d)
        self.step_count += 1
        obj = self.d.xpos[self.object_id].copy()
        distance = float(np.linalg.norm(obj-self.d.site_xpos[self.palm_site]))
        contacts = self.finger_object_contacts()
        lift = max(0., float(obj[2]-self.rest_height))
        grasp_contact = bool(contacts.sum() >= 2)
        reach_reward = float(np.exp(-6*distance))
        contact_reward = float(contacts.sum()/5)
        lift_reward = min(lift/.10, 1.) if grasp_contact else 0.
        action_rate_penalty = float(np.mean((action-self.last_action)**2))
        velocity_penalty = float(np.mean(self.d.qvel[self.vadr]**2))
        object_speed = float(np.linalg.norm(self.d.qvel[self.object_vadr:self.object_vadr+3]))
        holding = grasp_contact and lift >= .05 and object_speed < .2 and distance < .16
        self.hold_count = self.hold_count+1 if holding else 0
        success = self.hold_count >= 25
        reward = 2*reach_reward+2*contact_reward+8*lift_reward-.05*action_rate_penalty-.002*velocity_penalty
        if success:
            reward += 10
        finite = bool(np.isfinite(self.d.qpos).all() and np.isfinite(self.d.qvel).all())
        dropped = bool(obj[2] < self.rest_height-.15 or np.linalg.norm(obj[:2]) > 1.5)
        terminated = bool(success or dropped or not finite)
        truncated = bool(self.step_count >= self.max_steps and not terminated)
        self.last_action = action.copy()
        info = {'success': bool(success), 'dropped': dropped, 'finite': finite,
                'lift_m': lift, 'palm_distance_m': distance, 'finger_object_contacts': int(contacts.sum()),
                'reach_reward': reach_reward, 'contact_reward': contact_reward, 'lift_reward': lift_reward,
                'action_rate_penalty': action_rate_penalty, 'hold_steps': self.hold_count,
                'trained_policy': False}
        return self._observation(), float(reward), terminated, truncated, info

    def render(self):
        if self.render_mode != 'rgb_array':
            return None
        if self.renderer is None:
            self.renderer = mujoco.Renderer(self.m, height=480, width=640)
        camera = mujoco.MjvCamera()
        mujoco.mjv_defaultCamera(camera)
        camera.lookat[:] = [.18, 0, .45]
        camera.distance, camera.azimuth, camera.elevation = 1.3, 135, -20
        self.renderer.update_scene(self.d, camera=camera)
        return self.renderer.render()

    def close(self):
        if self.renderer is not None:
            self.renderer.close()
            self.renderer = None


def smoke_test(steps=100):
    from gymnasium.utils.env_checker import check_env
    env = ArmHandGraspEnv(max_steps=steps)
    check_env(env, skip_render_check=True)
    observation, reset_info = env.reset(seed=17)
    rng = np.random.default_rng(17)
    rewards = []
    info = {}
    for _ in range(steps):
        observation, reward, terminated, truncated, info = env.step(rng.uniform(-.08, .08, env.m.nu))
        assert env.observation_space.contains(observation)
        assert np.isfinite(reward)
        rewards.append(reward)
        if terminated or truncated:
            break
    result = {'gymnasium_check_env': 'passed', 'steps': len(rewards),
              'observation_size': len(observation), 'action_size': env.m.nu,
              'all_rewards_finite': True, 'final_info': info,
              'trained_policy': False, 'grasp_success_demonstrated': bool(info.get('success', False))}
    env.close()
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--smoke-test', action='store_true')
    parser.add_argument('--steps', type=int, default=100)
    args = parser.parse_args()
    print(json.dumps(smoke_test(args.steps), indent=2))
