#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="${ROOT_DIR}/documentation"

mkdir -p "${REPORT_DIR}/build"

compile_tex() {
  local tex_file="$1"
  if command -v tectonic >/dev/null 2>&1; then
    tectonic -X compile "${tex_file}" --outdir "${REPORT_DIR}/build"
  elif command -v latexmk >/dev/null 2>&1; then
    latexmk -pdf -interaction=nonstopmode -output-directory="${REPORT_DIR}/build" "${tex_file}"
  elif command -v pdflatex >/dev/null 2>&1; then
    pdflatex -interaction=nonstopmode -output-directory="${REPORT_DIR}/build" "${tex_file}"
    pdflatex -interaction=nonstopmode -output-directory="${REPORT_DIR}/build" "${tex_file}"
  else
    echo "No LaTeX engine found. Install tectonic, latexmk, or pdflatex to build reports." >&2
    exit 1
  fi
}

compile_tex "${REPORT_DIR}/main.tex"
if [[ -f "${REPORT_DIR}/nasa_hump_second_pass_report.tex" ]]; then
  compile_tex "${REPORT_DIR}/nasa_hump_second_pass_report.tex"
fi
