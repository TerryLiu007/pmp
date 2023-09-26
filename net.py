from torch.nn.utils.rnn import *
import articulate as art
from config import *
from dynamics import PhysicsOptimizer
import numpy as np

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
            c = torch.Tensor([1, 1])
            t = torch.Tensor((np.array(root_trans[i]) - np.array(root_trans[0]))/100)
            jt = torch.Tensor(joint_pos[i])
            p, t = self.dynamics_optimizer.optimize_frame(p, c, jt)
            # self.dynamics_optimizer.visualize_frame(p, t)
            pose_opt.append(p)
            tran_opt.append(t)
        pose_opt, tran_opt = torch.stack(pose_opt), torch.stack(tran_opt)
        return pose_opt, tran_opt
