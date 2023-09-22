r"""
    Config for paths, joint set, and normalizing scales.
"""


class configs:
    input_dir = 'data/dataset/timestamp'                      # output path for the preprocessed TotalCapture dataset
    result_dir = 'data/result'                      # output directory for the evaluation results

    smpl_file = 'models/SMPL_male.pkl'              # official SMPL model path
    physics_model_file = 'models/physics.urdf'      # physics body model path
    plane_file = 'models/plane.urdf'                # (for debug) path to plane.urdf    Please put plane.obj next to it.

    physics_parameter_file = 'physics_parameters.json'   # physics hyperparameters

    joint_index_map = [16, 20, 19, 15, 24, 23, 12, 26, 25, 11, 28, 27, 6, 10, 9, 5, 8, 7, 14, 13, 18, 17, 22, 21]
