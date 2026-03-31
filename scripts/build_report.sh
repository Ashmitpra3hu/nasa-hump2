#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="${ROOT_DIR}/documentation"

mkdir -p "${REPORT_DIR}/build"

if command -v tectonic >/dev/null 2>&1; then
  tectonic -X compile "${REPORT_DIR}/main.tex" --outdir "${REPORT_DIR}/build"
elif command -v latexmk >/dev/null 2>&1; then
  latexmk -pdf -interaction=nonstopmode -output-directory="${REPORT_DIR}/build" "${REPORT_DIR}/main.tex"
elif command -v pdflatex >/dev/null 2>&1; then
  pdflatex -interaction=nonstopmode -output-directory="${REPORT_DIR}/build" "${REPORT_DIR}/main.tex"
  pdflatex -interaction=nonstopmode -output-directory="${REPORT_DIR}/build" "${REPORT_DIR}/main.tex"
else
  echo "No LaTeX engine found. Install tectonic, latexmk, or pdflatex to build documentation/main.tex." >&2
  exit 1
fi
