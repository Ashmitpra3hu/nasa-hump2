#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE_BASE="${1:-gilbreth:/scratch/gilbreth/prabhu56/nasa-hump2-gpu-pyfr-pass1/repo_git}"

mkdir -p "${ROOT_DIR}/runs/gpu_pyfr_pass5"

rsync -az \
  --include '*/' \
  --include '*.csv' \
  --include '*.json' \
  --include '*.out' \
  --include '*.err' \
  --include '*.log' \
  --include '*.vtu' \
  --include '*.pvtu' \
  --include '*.pyfrs' \
  --exclude '*' \
  "${REMOTE_BASE}/runs/gpu_pyfr_pass5/" "${ROOT_DIR}/runs/gpu_pyfr_pass5/"

echo "Fetched GPU PyFR PASS 5 results into runs/gpu_pyfr_pass5"
