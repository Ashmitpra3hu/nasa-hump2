#!/usr/bin/env bash
set -euo pipefail

if [[ "${HOSTNAME:-}" != gilbreth-* ]]; then
  echo "Run this on Gilbreth after ssh gilbreth." >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="$(cd "${ROOT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

module load gcc/11.5.0 openmpi/4.1.6 cuda/12.6.0
source "${WORK_DIR}/pyfr-venv/bin/activate"

python scripts/pyfr/generate_pyfr_meshes.py medium
python scripts/pyfr/build_gpu_pyfr_pass1_case.py --variant medium
pyfr import data/NASA_2DWMH_PyFR/meshes/nasa_hump_medium.msh data/NASA_2DWMH_PyFR/meshes/nasa_hump_medium.pyfrm

mkdir -p runs/gpu_pyfr_pass1/medium

sbatch <<'EOF'
#!/bin/bash
#SBATCH -A rmaulik
#SBATCH -J pyfr-hump-med
#SBATCH -N 1
#SBATCH --ntasks=1
#SBATCH --gpus-per-node=1
#SBATCH -t 00:30:00
#SBATCH -o runs/gpu_pyfr_pass1/medium/slurm-%j.out
#SBATCH -e runs/gpu_pyfr_pass1/medium/slurm-%j.err

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
module load gcc/11.5.0 openmpi/4.1.6 cuda/12.6.0
source "$(cd "$SLURM_SUBMIT_DIR/.." && pwd)/pyfr-venv/bin/activate"
hostname
date
nvidia-smi
module list 2>&1
python --version
pyfr --version
pyfr run -b cuda data/NASA_2DWMH_PyFR/meshes/nasa_hump_medium.pyfrm data/NASA_2DWMH_PyFR/configs/medium.ini
latest_soln=$(ls -1 runs/gpu_pyfr_pass1/medium/solutions/*.pyfrs | sort | tail -n 1)
pyfr export -d 3 data/NASA_2DWMH_PyFR/meshes/nasa_hump_medium.pyfrm "$latest_soln" runs/gpu_pyfr_pass1/medium/medium_latest.vtu
EOF
