#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_REL="${1:-data/NASA_2DWMH_sweep/pass4_uniform_sst_650}"
SOURCE_DIR="${ROOT_DIR}/${SOURCE_REL}"
TARGET_DIR="${ROOT_DIR}/data/NASA_2DWMH"
BACKUP_DIR="${ROOT_DIR}/data/NASA_2DWMH_backup_before_promotion"

if [[ ! -d "${SOURCE_DIR}" ]]; then
  echo "Source case does not exist: ${SOURCE_DIR}" >&2
  exit 1
fi

rm -rf "${BACKUP_DIR}"
if [[ -d "${TARGET_DIR}" ]]; then
  mv "${TARGET_DIR}" "${BACKUP_DIR}"
fi

cp -R "${SOURCE_DIR}" "${TARGET_DIR}"
touch "${TARGET_DIR}/foam.foam"

echo "Promoted ${SOURCE_REL} -> data/NASA_2DWMH"
echo "Previous main case backup: data/NASA_2DWMH_backup_before_promotion"
