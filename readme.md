# PIP

Code originated from CVPR 2022 [paper](https://arxiv.org/abs/2203.08528) "Physical Inertial Poser (PIP): Physics-aware Real-time Human Motion Tracking from Sparse Inertial Sensors". See [Project Page](https://xinyu-yi.github.io/PIP/).

## Usage

### Install dependencies

- Python-3.9

- [Torch-1.9.1+cpu](https://download.pytorch.org/whl/cpu/torch-1.9.1%2Bcpu-cp39-cp39-win_amd64.whl)

- [Torchvision-0.10.1+cpu](https://download.pytorch.org/whl/cpu/torchvision-0.10.1%2Bcpu-cp39-cp39-win_amd64.whl)

#### PIP: Install correct version in requirements.txt

```
git clone https://github.com/TerryLiu007/pmp.git
pip install "torch-1.9.1+cpu-cp39-cp39-win_amd64.whl"
pip install "torchvision-0.10.1+cpu-cp39-cp39-win_amd64.whl"
pip install -r requirements.txt
```

#### RBDL:

```
git clone https://github.com/SlimeVRX/rbdl.git
python setup.py install
```

### Run the evaluation

```
python evaluate.py
```

### About the codes

- In `dynamics.py`, there are many disabled options for the physics optimization. You can try different combinations of the energy terms by enabling the corresponding terms. 

- In Line ~44 in `net.py`:

  ```python
  self.dynamics_optimizer = PhysicsOptimizer(debug=False)
  ```

  set `debug=True` to visualize the estimated motions using pybullet. You may need to clean the cached results and rerun the `evaluate.py`. (e.g., set `flush_cache=True` in `evaluate()` and rerun.)

- In Line ~244 in `dynamics.py`:

  ```python
  if False:   # visualize GRF (no smoothing)
      p.removeAllUserDebugItems()
      for point, force in zip(collision_points, GRF.reshape(-1, 3)):
          p.addUserDebugLine(point, point + force * 1e-2, [1, 0, 0])
  ```

  Enabling this to visualize the ground reaction force. (You also need to set `debug=True` as stated above.) Note that rendering the force lines can be very slow in pybullet. 

- The hyperparameters for the physics optimization are all in `physics_parameters.json`.  If you set `debug=True`, you can adjust these parameters interactively in the pybullet window.

