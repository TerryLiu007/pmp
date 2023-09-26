import torch
import tqdm
from config import *
from utils import *
import os
import numpy as np
import shutil
from matplotlib import pyplot as plt
import articulate as art
from articulate.utils.rbdl import *
from net import PMP
import json


torch.set_printoptions(sci_mode=False)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = 'Times New Roman'
plt.figure(dpi=200)
plt.grid(linestyle='-.')
plt.xlabel('Real travelled distance (m)', fontsize=16)
plt.ylabel('Mean translation error (m)', fontsize=16)
plt.title('Cumulative Translation Error', fontsize=18)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


class FullPoseEvaluator:
    names = ['Absolute Jitter Error (km/s^3)']

    def __init__(self):
        self._base_motion_loss_fn = art.FullMotionEvaluator(paths.smpl_file, device=device)

    def __call__(self, pose_p, pose_t, tran_p, tran_t):
        errs = self._base_motion_loss_fn(pose_p=pose_p, pose_t=pose_t, tran_p=tran_p, tran_t=tran_t)
        return torch.stack([errs[4] / 1000])


def evaluate_zmp_distance(poses, trans, fps=60, foot_radius=0.1):
    qs = smpl_to_rbdl(poses, trans)
    qdots = np.empty_like(qs)
    qdots[1:, :3] = (qs[1:, :3] - qs[:-1, :3]) * fps
    qdots[1:, 3:] = art.math.angle_difference(qs[1:, 3:], qs[:-1, 3:]) * fps
    qdots[0] = qdots[1]
    qddots = (qdots[1:] - qdots[:-1]) * fps
    qddots = np.concatenate((qddots[:1], qddots))
    rbdl_model = RBDLModel(paths.physics_model_file)

    floor_height = []
    for q in qs[2:30]:
        lp = rbdl_model.calc_body_position(q, Body.LFOOT)
        rp = rbdl_model.calc_body_position(q, Body.RFOOT)
        floor_height.append(lp[1])
        floor_height.append(rp[1])
    floor_height = torch.tensor(floor_height).mean() + 0.01

    dists = []
    for q, qdot, qddot in zip(qs, qdots, qddots):
        lp = rbdl_model.calc_body_position(q, Body.LFOOT)
        rp = rbdl_model.calc_body_position(q, Body.RFOOT)
        if lp[1] > floor_height and rp[1] > floor_height:
            continue

        zmp = rbdl_model.calc_zero_moment_point(q, qdot, qddot)
        ap = (zmp - lp)[[0, 2]]
        ab = (rp - lp)[[0, 2]]
        bp = (zmp - rp)[[0, 2]]
        if lp[1] <= floor_height and rp[1] <= floor_height:
            # point to line segment distance
            r = (ap * ab).sum() / (ab * ab).sum()
            if r < 0:
                d = np.linalg.norm(ap)
            elif r > 1:
                d = np.linalg.norm(bp)
            else:
                d = np.sqrt((ap * ap).sum() - r * r * (ab * ab).sum())
        else:
            # point to point distance
            d = np.linalg.norm(ap if lp[1] <= floor_height else bp)
        dists.append(max(d - foot_radius, 0))

    return sum(dists) / len(dists)


def gen_pose_from_quats(joint_tree):
    joint_names = []
    quats = []
    for k in joint_tree.keys():
        quats.append(joint_tree[k])
        joint_names.append(k)
    joint_names = np.array(joint_names)[joint_set.model_joint_map]
    quats = torch.Tensor([i for i in np.array(quats, dtype=object)[joint_set.model_joint_map]])
    pose = art.math.quaternion_to_rotation_matrix(quats)
    return pose


def run_pipeline(net, data_dir, id):
    r"""
    Run `net` using the imu data loaded from `data_dir`.
    Save the estimated [Pose[num_frames, 24, 3, 3], Tran[num_frames, 3]] for each of `sequence_ids`.
    """
    print('Loading data from "%s"' % data_dir)
    frames = open(os.path.join(data_dir, 'exp_player.json'), 'r').readlines()
    pos_sequence = {}
    rot_sequence = {}
    trans_sequence = {}
    for line in frames:
        frame = json.loads(line)
        for target in frame['targets_3d']:
            id = target['trackid_3d']
            if id not in pos_sequence.keys():
                pos_sequence[id] = []
                pos_sequence[id].append(np.array(target['keypoints_3d'])[joint_set.joint_index_map][:, :3])
                rot_sequence[id] = []
                rot_sequence[id].append(gen_pose_from_quats(target['model']))
                trans_sequence[id] = []
                trans_sequence[id].append(target['model']['_root_translate'])
            else:
                pos_sequence[id].append(np.array(target['keypoints_3d'])[joint_set.joint_index_map][:, :3])
                rot_sequence[id].append(gen_pose_from_quats(target['model']))
                trans_sequence[id].append(target['model']['_root_translate'])

    data_name = os.path.basename(data_dir)
    output_dir = os.path.join(paths.result_dir, data_name, net.name)
    os.makedirs(output_dir, exist_ok=True)

    print('Saving the results at "%s"' % output_dir)
    torch.save(net.optimize(pos_sequence[id], rot_sequence[id], trans_sequence[id]), os.path.join(output_dir, '%d.pt' % id))


def evaluate(net, data_dir, sequence_ids=None, flush_cache=False, pose_evaluator=FullPoseEvaluator(), evaluate_pose=False, evaluate_tran=False, evaluate_zmp=False):
    r"""
    Evaluate poses and translations of `net` on all sequences in `sequence_ids` from `data_dir`.
    `net` should implement `net.name` and `net.predict(glb_acc, glb_rot)`.
    """
    data_name = os.path.basename(data_dir)
    result_dir = os.path.join(paths.result_dir, data_name, net.name)
    print_title('Evaluating "%s" on "%s"' % (net.name, data_name))

    _, _, pose_t_all, tran_t_all = torch.load(os.path.join(data_dir, 'test.pt')).values()

    if sequence_ids is None:
        sequence_ids = list(range(len(pose_t_all)))
    if flush_cache and os.path.exists(result_dir):
        shutil.rmtree(result_dir)

    missing_ids = [i for i in sequence_ids if not os.path.exists(os.path.join(result_dir, '%d.pt' % i))]
    cached_ids = [i for i in sequence_ids if os.path.exists(os.path.join(result_dir, '%d.pt' % i))]
    print('Cached ids: %s\nMissing ids: %s' % (cached_ids, missing_ids))
    if len(missing_ids) > 0:
        run_pipeline(net, data_dir, missing_ids)

    pose_errors = []
    tran_errors = {window_size: [] for window_size in list(range(1, 8))}
    zmp_errors = []
    for i in tqdm.tqdm(sequence_ids):
        result = torch.load(os.path.join(result_dir, '%d.pt' % i))
        pose_p, tran_p = result[0], result[1]
        pose_t, tran_t = pose_t_all[i], tran_t_all[i]
        if evaluate_pose:
            pose_t = art.math.axis_angle_to_rotation_matrix(pose_t).view_as(pose_p)
            pose_errors.append(pose_evaluator(pose_p, pose_t, tran_p, tran_t))
        if evaluate_tran:
            # compute gt move distance at every frame
            move_distance_t = torch.zeros(tran_t.shape[0])
            v = (tran_t[1:] - tran_t[:-1]).norm(dim=1)
            for j in range(len(v)):
                move_distance_t[j + 1] = move_distance_t[j] + v[j]

            for window_size in tran_errors.keys():
                # find all pairs of start/end frames where gt moves `window_size` meters
                frame_pairs = []
                start, end = 0, 1
                while end < len(move_distance_t):
                    if move_distance_t[end] - move_distance_t[start] < window_size:
                        end += 1
                    else:
                        if len(frame_pairs) == 0 or frame_pairs[-1][1] != end:
                            frame_pairs.append((start, end))
                        start += 1

                # calculate mean distance error
                errs = []
                for start, end in frame_pairs:
                    vel_p = tran_p[end] - tran_p[start]
                    vel_t = tran_t[end] - tran_t[start]
                    errs.append((vel_t - vel_p).norm() / (move_distance_t[end] - move_distance_t[start]) * window_size)
                if len(errs) > 0:
                    tran_errors[window_size].append(sum(errs) / len(errs))

        if evaluate_zmp:
            zmp_errors.append(evaluate_zmp_distance(pose_p, tran_p))

    if evaluate_pose:
        pose_errors = torch.stack(pose_errors).mean(dim=0)
        for name, error in zip(pose_evaluator.names, pose_errors):
            print('%s: %.4f' % (name, error[0]))
    if evaluate_zmp:
        print('ZMP Distance (m): %.4f' % (sum(zmp_errors) / len(zmp_errors)))
    if evaluate_tran:
        plt.plot([0] + [_ for _ in tran_errors.keys()], [0] + [torch.tensor(_).mean() for _ in tran_errors.values()], label=net.name)
        plt.legend(fontsize=15)
        plt.show()


if __name__ == '__main__':
    net = PMP()
    run_pipeline(net, paths.input_dir, 0)
