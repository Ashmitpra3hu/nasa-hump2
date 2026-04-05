#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python3 -u scripts/run_nasa_hump_mlpass2.py
