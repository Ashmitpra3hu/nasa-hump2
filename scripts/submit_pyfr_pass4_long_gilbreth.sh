#!/usr/bin/env bash
set -euo pipefail

if [[ "${HOSTNAME:-}" != gilbreth-* ]]; then
  echo "Run this on Gilbreth after ssh gilbreth." >&2
  exit 1
fi

PYFR_PARTITION="${PYFR_PARTITION:-a100-40gb}"
PYFR_MEM="${PYFR_MEM:-16G}"
PYFR_WALLTIME="${PYFR_WALLTIME:-00:10:00}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="$(cd "${ROOT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

module load gcc/11.5.0 openmpi/4.1.6 cuda/12.6.0
source "${WORK_DIR}/pyfr-venv/bin/activate"

python scripts/pyfr/generate_pyfr_meshes.py medium
python scripts/pyfr/check_pyfr_hump_mesh.py --variant minimal > "runs/gpu_pyfr_pass4_meshcheck.json" 2>/dev/null || true
python scripts/pyfr/build_gpu_pyfr_pass4_case.py
pyfr import data/NASA_2DWMH_PyFR/meshes/nasa_hump_medium.msh data/NASA_2DWMH_PyFR/meshes/nasa_hump_medium.pyfrm

mkdir -p "runs/gpu_pyfr_pass4/long/solutions"

sbatch <<EOF
#!/bin/bash
#SBATCH -A rmaulik
#SBATCH -p ${PYFR_PARTITION}
#SBATCH -J pyfr-p4-long
#SBATCH -N 1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --gpus-per-node=1
#SBATCH --mem=${PYFR_MEM}
#SBATCH -t ${PYFR_WALLTIME}
#SBATCH -o runs/gpu_pyfr_pass4/long/slurm-%j.out
#SBATCH -e runs/gpu_pyfr_pass4/long/slurm-%j.err

set -euo pipefail
cd "\$SLURM_SUBMIT_DIR"
mkdir -p runs/gpu_pyfr_pass4/long/solutions
module load gcc/11.5.0 openmpi/4.1.6 cuda/12.6.0
source "\$(cd "\$SLURM_SUBMIT_DIR/.." && pwd)/pyfr-venv/bin/activate"
hostname
date
nvidia-smi
module list 2>&1
python --version
pyfr --version
pyfr run -b cuda data/NASA_2DWMH_PyFR/meshes/nasa_hump_medium.pyfrm data/NASA_2DWMH_PyFR/configs/pass4_long.ini
latest_soln=\$(ls -1 runs/gpu_pyfr_pass4/long/solutions/*.pyfrs | sort | tail -n 1)
pyfr export -d 3 data/NASA_2DWMH_PyFR/meshes/nasa_hump_medium.pyfrm "\$latest_soln" runs/gpu_pyfr_pass4/long/pass4_long_latest.vtu
EOF
