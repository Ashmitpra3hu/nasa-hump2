#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="${ROOT_DIR}/documentation_src"
OUTPUT_DIR="${ROOT_DIR}/documentation"

mkdir -p "${OUTPUT_DIR}"

compile_tex() {
  local tex_file="$1"
  local output_name="$2"
  if command -v tectonic >/dev/null 2>&1; then
    tectonic -X compile "${tex_file}" --outdir "${OUTPUT_DIR}"
  elif command -v latexmk >/dev/null 2>&1; then
    latexmk -pdf -interaction=nonstopmode -output-directory="${OUTPUT_DIR}" "${tex_file}"
  elif command -v pdflatex >/dev/null 2>&1; then
    pdflatex -interaction=nonstopmode -output-directory="${OUTPUT_DIR}" "${tex_file}"
    pdflatex -interaction=nonstopmode -output-directory="${OUTPUT_DIR}" "${tex_file}"
  else
    echo "No LaTeX engine found. Install tectonic, latexmk, or pdflatex to build reports." >&2
    exit 1
  fi

  local compiled_pdf
  compiled_pdf="${OUTPUT_DIR}/$(basename "${tex_file%.*}").pdf"
  mv "${compiled_pdf}" "${OUTPUT_DIR}/${output_name}"
}

compile_tex "${SOURCE_DIR}/main.tex" "pass_one.pdf"
if [[ -f "${SOURCE_DIR}/nasa_hump_second_pass_report.tex" ]]; then
  compile_tex "${SOURCE_DIR}/nasa_hump_second_pass_report.tex" "pass_two.pdf"
fi
if [[ -f "${SOURCE_DIR}/nasa_hump_third_pass_report.tex" ]]; then
  compile_tex "${SOURCE_DIR}/nasa_hump_third_pass_report.tex" "pass_three.pdf"
fi
if [[ -f "${SOURCE_DIR}/nasa_hump_pass4_report.tex" ]]; then
  compile_tex "${SOURCE_DIR}/nasa_hump_pass4_report.tex" "pass4.pdf"
fi
