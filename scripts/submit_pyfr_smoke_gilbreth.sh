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

python scripts/pyfr/generate_pyfr_meshes.py smoke
python scripts/pyfr/build_gpu_pyfr_pass1_case.py --variant smoke
pyfr import data/NASA_2DWMH_PyFR/meshes/smoke_rect.msh data/NASA_2DWMH_PyFR/meshes/smoke_rect.pyfrm

mkdir -p runs/gpu_pyfr_pass1/smoke_test
mkdir -p runs/gpu_pyfr_pass1/smoke_test/solutions

sbatch <<'EOF'
#!/bin/bash
#SBATCH -A rmaulik
#SBATCH -p a100-40gb
#SBATCH -J pyfr-smoke
#SBATCH -N 1
#SBATCH --ntasks=1
#SBATCH --gpus-per-node=1
#SBATCH --mem=240G
#SBATCH -t 00:10:00
#SBATCH -o runs/gpu_pyfr_pass1/smoke_test/slurm-%j.out
#SBATCH -e runs/gpu_pyfr_pass1/smoke_test/slurm-%j.err

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
mkdir -p runs/gpu_pyfr_pass1/smoke_test/solutions
module load gcc/11.5.0 openmpi/4.1.6 cuda/12.6.0
source "$(cd "$SLURM_SUBMIT_DIR/.." && pwd)/pyfr-venv/bin/activate"
hostname
date
nvidia-smi
module list 2>&1
python --version
pyfr --version
pyfr run -b cuda data/NASA_2DWMH_PyFR/meshes/smoke_rect.pyfrm data/NASA_2DWMH_PyFR/configs/smoke.ini
EOF
