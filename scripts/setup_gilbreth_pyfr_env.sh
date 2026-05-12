#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOC_FILE="${ROOT_DIR}/documentation_src/GPU_PYFR_PASS1_ENVIRONMENT.md"

if [[ "${HOSTNAME:-}" != gilbreth-* ]]; then
  echo "Run this script on Gilbreth after ssh gilbreth." >&2
  exit 1
fi

module load gcc/11.5.0 openmpi/4.1.6 cuda/12.6.0

WORK_BASE="${CLUSTER_SCRATCH:-$HOME}"
PASS_DIR="${WORK_BASE}/nasa-hump2-gpu-pyfr-pass1"
mkdir -p "${PASS_DIR}"
cd "${PASS_DIR}"

python3 -m venv pyfr-venv
source pyfr-venv/bin/activate

python -m pip install --upgrade pip wheel
python -m pip install 'setuptools<81' 'pyfr<2' mpi4py gmsh meshio matplotlib pandas scipy

{
  echo "# GPU PyFR PASS 1 Environment"
  echo
  echo "- Date: $(date -Is)"
  echo "- Host: $(hostname)"
  echo "- Scratch workspace: ${PASS_DIR}"
  echo "- Python: $(python --version 2>&1)"
  echo "- Pip: $(python -m pip --version)"
  echo "- PyFR: $(pyfr --version 2>&1 | tail -n 1)"
  echo "- sbatch: $(sbatch --version 2>&1)"
  echo "- squeue: $(which squeue)"
  echo "- sacct: $(which sacct)"
  echo "- nvidia-smi:"
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
  echo
  echo "## Loaded Modules"
  module list 2>&1
  echo
  echo "## Available Accounts"
  slist
} > "${DOC_FILE}"

echo "Environment ready at ${PASS_DIR}"
echo "Summary written to ${DOC_FILE}"
