from roboschool.scene_abstract import SingleRobotEmptyScene
from roboschool.gym_mujoco_xml_env import RoboschoolMujocoXmlEnv
import gym
import gym.spaces
import gym.utils
import gym.utils.seeding
import numpy as np
import os
import sys


class RoboschoolReacher3d3(RoboschoolMujocoXmlEnv):
    _DOF = 3
    _ROBOT_DESCRIPTION = 'reacher3d3.xml'
    _OBS_DIMS = 6 + _DOF * 3
    _CAM_POS  = 0.3
    TARG_LIMIT   = 0.16
    TARG_LIMIT_Z = 0.05

    def __init__(self):
        RoboschoolMujocoXmlEnv.__init__(
            self, self._ROBOT_DESCRIPTION, 'body0', action_dim=self._DOF, obs_dim=self._OBS_DIMS)

    def create_single_player_scene(self):
        return SingleRobotEmptyScene(gravity=0.0, timestep=0.0165, frame_skip=1)

    def robot_specific_reset(self):
        self.jdict["target_x"].reset_current_position(
            self.np_random.uniform(low=-self.TARG_LIMIT, high=self.TARG_LIMIT), 0)
        self.jdict["target_y"].reset_current_position(
            self.np_random.uniform(low=-self.TARG_LIMIT, high=self.TARG_LIMIT), 0)
        self.jdict["target_z"].reset_current_position(
            self.np_random.uniform(low=0, high=self.TARG_LIMIT_Z), 0)

        self.fingertip = self.parts["fingertip"]
        self.target = self.parts["target"]

        self.joints = []
        for i in range(self._DOF):
            self.joints.append(self.jdict["joint{}".format(i)])
            self.joints[i].reset_current_position(
                self.np_random.uniform(low=-1.5, high=1.5), 0)

        self.theta, self.theta_dot = [None] * self._DOF, [None] * self._DOF

    def apply_action(self, a):
        assert(np.isfinite(a).all())
        for i in range(len(self.joints)):
            self.joints[i].set_motor_torque(
                0.1 * float(np.clip(a[i], -1.0, +1.0)))

    def calc_state(self):
        target_x, _ = self.jdict["target_x"].current_position()
        target_y, _ = self.jdict["target_y"].current_position()
        target_z, _ = self.jdict["target_z"].current_position()
        self.to_target_vec = np.array(
            self.fingertip.pose().xyz()) - np.array(self.target.pose().xyz())

        state = np.array([
            target_x,
            target_y,
            target_z,
            self.to_target_vec[0],
            self.to_target_vec[1],
            self.to_target_vec[2],
        ])
        for i in range(len(self.joints)):
            self.theta[i], self.theta_dot[i] = self.joints[i].current_relative_position()
            state = np.append(state, [np.cos(self.theta[i]), np.sin(
                self.theta[i]), self.theta_dot[i]])

        # total of state is 15
        return state

    def calc_potential(self):
        # return -100 * np.linalg.norm(self.to_target_vec)
        return - np.linalg.norm(self.to_target_vec)

    def _step(self, a):
        assert(not self.scene.multiplayer)
        self.apply_action(a)
        self.scene.global_step()

        state = self.calc_state()  # sets self.to_target_vec

        potential_old = self.potential
        self.potential = self.calc_potential()

        work = 0.0
        stall = 0.0
        for i in range(len(self.joints)):
            # work torque*angular_velocity
            work += np.abs(a[i] * self.theta_dot[i])
            # stall torque require some energy
            stall += np.abs(a[i])
        electricity_cost = (
            -.10 * work
            -.01 * stall
        )

        # stuck_joint_cost = []
        # for theta in self.theta:
        #     stuck_joint_cost.append(
        #         -0.01 if np.abs(np.abs(theta) - 1) < 0.01 else 0.0)

        self.rewards = [float(self.potential),#float(self.potential - potential_old),
                        float(electricity_cost)]#, sum(stuck_joint_cost)]
        self.frame += 1
        self.done += 0
        self.reward += sum(self.rewards)
        self.HUD(state, a, False)
        return state, sum(self.rewards), False, {}

    def camera_adjust(self):
        x, y, z = self.fingertip.pose().xyz()
        x *= 0.5
        y *= 0.5
        self.camera.move_and_look_at(self._CAM_POS, self._CAM_POS, self._CAM_POS, x, y, z)


class RoboschoolReacher3d7(RoboschoolReacher3d3):
    _DOF = 7
    _ROBOT_DESCRIPTION = 'reacher3d7.xml'
    _OBS_DIMS = 6 + _DOF * 3
    _CAM_POS  = 0.3
    TARG_LIMIT   = 0.18
    TARG_LIMIT_Z = 0.08

    def __init__(self):
        super().__init__()


class RoboschoolReacher3d6(RoboschoolReacher3d3):
    _DOF = 6
    _ROBOT_DESCRIPTION = 'reacher3d6.xml'
    _OBS_DIMS = 6 + _DOF * 3
    _CAM_POS  = 0.5
    TARG_LIMIT   = 0.5
    TARG_LIMIT_Z = 0.1

    def __init__(self):
        super().__init__()
