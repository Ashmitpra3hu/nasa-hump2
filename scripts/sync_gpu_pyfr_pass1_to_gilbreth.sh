#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE_BASE="${1:-gilbreth:/scratch/gilbreth/prabhu56/nasa-hump2-gpu-pyfr-pass1/repo_git}"

rsync -az \
  --delete \
  --exclude '.git/' \
  --exclude 'data/NASA_2DWMH/' \
  --exclude 'runs/gpu_pyfr_pass1/' \
  --exclude 'documentation/*.pdf' \
  "${ROOT_DIR}/" "${REMOTE_BASE}/"

echo "Synced repo subset to ${REMOTE_BASE}"
