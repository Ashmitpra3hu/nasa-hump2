# GPU PyFR PASS 1 Environment

This file records the Gilbreth environment that was actually used during GPU PyFR PASS 1 setup.

## Access Pattern

- Local access command: `ssh gilbreth`
- Login host reached during setup: `gilbreth-fe00.rcac.purdue.edu`
- Scratch base detected from the shell environment: `/scratch/gilbreth/prabhu56`
- PASS 1 working directory created on Gilbreth: `/scratch/gilbreth/prabhu56/nasa-hump2-gpu-pyfr-pass1`

## Scheduler / Cluster Tools

- `sbatch`: `/usr/bin/sbatch`
- `srun`: `/usr/bin/srun`
- `squeue`: `/usr/bin/squeue`
- `sacct`: `/usr/bin/sacct`

## Modules Loaded for PyFR

- `gcc/11.5.0`
- `openmpi/4.1.6`
- `cuda/12.6.0`

Module discovery was checked with:

- `module avail gcc`
- `module avail openmpi`
- `module avail cuda`

## Python / PyFR Environment

- System Python on Gilbreth during setup: `Python 3.9.25`
- Virtual environment created at: `/scratch/gilbreth/prabhu56/nasa-hump2-gpu-pyfr-pass1/pyfr-venv`
- Installed PyFR command version: `pyfr 1.15.0`

### Installed user-space packages

- `setuptools<81`
- `pyfr<2`
- `mpi4py`
- `gmsh`
- `meshio`
- `matplotlib`
- `pandas`
- `scipy`

## GPU Observation on the Front-End

The setup session queried `nvidia-smi` and observed:

- GPU model reported: `NVIDIA A30`
- Driver version reported: `590.48.01`
- Total device memory reported: `24576 MiB`

This observation came from the accessible environment during setup. Production runs are still required to go through Slurm on a compute allocation rather than relying on the login node.

## Slurm / Account Notes

The available account listing during setup showed:

- account: `rmaulik`
- visible GPU partition entry included `A100-40gb`

The scheduler partition inventory also showed GPU partitions including:

- `a10`
- `a30`
- `a100-40gb`
- `a100-80gb`
- `h100`

## Important Compatibility Note

The PyFR installation initially failed at runtime because `pkg_resources` was unavailable in the venv after upgrading packaging tools. The environment was made functional by pinning:

- `setuptools<81`

This is documented because it is part of the actual reproducible setup path, not an incidental local workaround.
