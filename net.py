from torch.nn.utils.rnn import *
import articulate as art
from articulate.utils.torch import *
from config import *
from utils import *
from dynamics import PhysicsOptimizer


class PMP:
    name = 'pmp'

    def __init__(self):
        body_model = art.ParametricModel(paths.smpl_file)
        self.inverse_kinematics_R = body_model.inverse_kinematics_R
        self.forward_kinematics = body_model.forward_kinematics
        self.dynamics_optimizer = PhysicsOptimizer(debug=True)

    def optimize(self, joint_pos, joint_rot, root_trans):
        r"""
        Predict the results for evaluation.

        :param pose: A tensor that can reshape to [num_frames, 24, 3].
        :return: Pose tensor in shape [num_frames, 24, 3, 3] and
                 translation tensor in shape [num_frames, 3].
        """
        self.dynamics_optimizer.reset_states()
        pose_opt, tran_opt = [], []

        for i in range(2, len(joint_rot)):
            p = joint_rot[i]
            t = torch.Tensor(root_trans[i])
            # p, t = self.dynamics_optimizer.optimize_frame(p, v, c, a)
            self.dynamics_optimizer.visualize_frame(p, t)
            pose_opt.append(p)
            tran_opt.append(t)
        pose_opt, tran_opt = torch.stack(pose_opt), torch.stack(tran_opt)
        return pose_opt, tran_opt
