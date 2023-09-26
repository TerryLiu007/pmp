r"""
    Config for paths, joint set, and normalizing scales.
"""


class paths:
    input_dir = 'data/dataset/table_tennis'         # output path for the preprocessed TotalCapture dataset
    result_dir = 'data/result'                      # output directory for the evaluation results

    smpl_file = 'models/SMPL_male.pkl'              # official SMPL model path
    physics_model_file = 'models/physics.urdf'      # physics body model path
    plane_file = 'models/plane.urdf'                # (for debug) path to plane.urdf    Please put plane.obj next to it.

    physics_parameter_file = 'physics_parameters.json'   # physics hyperparameters


class joint_set:
    joint_index_map = [16, 20, 19, 15, 24, 23, 12, 26, 25, 11, 28, 27, 6, 10, 9, 5, 8, 7, 14, 13, 18, 17, 22, 21]
    model_joint_map = [2, 4, 5, 3, 7, 8, 6, 10, 11, 9, 16, 18, 12, 13, 14, 19, 20, 21, 31, 32, 33, 34, 36, 38]

    leaf = [7, 8, 12, 20, 21]
    full = list(range(1, 24))
    reduced = [1, 2, 3, 4, 5, 6, 9, 12, 13, 14, 15, 16, 17, 18, 19]
    ignored = [0, 7, 8, 10, 11, 20, 21, 22, 23]

    n_leaf = len(leaf)
    n_full = len(full)
    n_reduced = len(reduced)
    n_ignored = len(ignored)