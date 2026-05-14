#!/usr/bin/env bash
set -euo pipefail

if [[ "${HOSTNAME:-}" != gilbreth-* ]]; then
  echo "Run this on Gilbreth after ssh gilbreth." >&2
  exit 1
fi

if ! command -v module >/dev/null 2>&1; then
  set +u
  source /etc/profile.d/modules.sh
  set -u
fi

PYFR_PARTITION="${PYFR_PARTITION:-a100-40gb}"
PYFR_MEM="${PYFR_MEM:-16G}"
PYFR_WALLTIME="${PYFR_WALLTIME:-00:10:00}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="$(cd "${ROOT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

module load gcc/11.5.0 openmpi/4.1.6 cuda/12.6.0
source "${WORK_DIR}/pyfr-venv/bin/activate"

python scripts/pyfr/generate_pyfr_meshes.py smoke
python scripts/pyfr/generate_pyfr_meshes.py medium
python scripts/pyfr/check_pyfr_hump_mesh.py --variant minimal > "runs/gpu_pyfr_pass6/stability/meshcheck_medium.json" 2>/dev/null || true
python scripts/pyfr/build_gpu_pyfr_pass6_cases.py
pyfr import data/NASA_2DWMH_PyFR/meshes/smoke_rect.msh data/NASA_2DWMH_PyFR/meshes/smoke_rect.pyfrm
pyfr import data/NASA_2DWMH_PyFR/meshes/nasa_hump_medium.msh data/NASA_2DWMH_PyFR/meshes/nasa_hump_medium.pyfrm

declare -a CASES=(
  pass6_smoke_ns_sub
  pass6_hump_ns_sub_dt1e4
  pass6_hump_ns_sub_dt5e5
  pass6_hump_ns_char_dt1e4
  pass6_hump_ns_char_dt5e5
)

for CASE in "${CASES[@]}"; do
  if [[ "${CASE}" == pass6_smoke_* ]]; then
    MESH="smoke_rect.pyfrm"
  else
    MESH="nasa_hump_medium.pyfrm"
  fi

  mkdir -p "runs/gpu_pyfr_pass6/stability/${CASE}/solutions"

  sbatch <<EOF
#!/bin/bash
#SBATCH -A rmaulik
#SBATCH -p ${PYFR_PARTITION}
#SBATCH -J ${CASE}
#SBATCH -N 1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --gpus-per-node=1
#SBATCH --mem=${PYFR_MEM}
#SBATCH -t ${PYFR_WALLTIME}
#SBATCH -o runs/gpu_pyfr_pass6/stability/${CASE}/slurm-%j.out
#SBATCH -e runs/gpu_pyfr_pass6/stability/${CASE}/slurm-%j.err

set -euo pipefail
cd "\$SLURM_SUBMIT_DIR"
if ! command -v module >/dev/null 2>&1; then
  set +u
  source /etc/profile.d/modules.sh
  set -u
fi
module load gcc/11.5.0 openmpi/4.1.6 cuda/12.6.0
source "\$(cd "\$SLURM_SUBMIT_DIR/.." && pwd)/pyfr-venv/bin/activate"
mkdir -p runs/gpu_pyfr_pass6/stability/${CASE}/solutions documentation_src/gpu_pyfr_pass6/data/stability_audits
hostname
date
nvidia-smi
module list 2>&1
python --version
pyfr --version
pyfr run -b cuda data/NASA_2DWMH_PyFR/meshes/${MESH} data/NASA_2DWMH_PyFR/configs/${CASE}.ini
latest_soln=\$(ls -1 runs/gpu_pyfr_pass6/stability/${CASE}/solutions/*.pyfrs | sort | tail -n 1)
pyfr export -d 3 data/NASA_2DWMH_PyFR/meshes/${MESH} "\$latest_soln" runs/gpu_pyfr_pass6/stability/${CASE}/${CASE}_latest.vtu
module purge --force || true
module load ngc/default paraview/5.11.0
pvpython scripts/inspect_pyfr_vtu_fields.py runs/gpu_pyfr_pass6/stability/${CASE}/${CASE}_latest.vtu documentation_src/gpu_pyfr_pass6/data/stability_audits/${CASE}.json
EOF
done
