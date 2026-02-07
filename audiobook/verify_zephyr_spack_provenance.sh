#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(realpath "${SCRIPT_DIR}/..")"
LAUNCHER="${ZEPHYR_LAUNCHER:-${SCRIPT_DIR}/zephyr_launch_container.sh}"
IMAGE_NAME="${AUDIOBOOK_IMAGE_NAME:-${SYGALDRY_IMAGE:-sygaldry/zephyr:spack}}"

if [[ ! -x "${LAUNCHER}" ]]; then
  echo "Missing Zephyr launcher: ${LAUNCHER}" >&2
  exit 1
fi

SYGALDRY_IMAGE="${IMAGE_NAME}" \
  "${LAUNCHER}" \
  --repo "${REPO_ROOT}" \
  --entrypoint run-job \
  -- bash -lc '
cat > /tmp/verify_spack_provenance.py <<'"'"'PY'"'"'
import sys
import torch
import jax

def in_spack(path: str) -> bool:
    return "/opt/spack_store/" in (path or "")

print("sys.executable:", sys.executable)
print("sys.base_prefix:", sys.base_prefix)
print("torch:", torch.__file__)
print("jax:", jax.__file__)

if not in_spack(sys.base_prefix):
    raise SystemExit("Spack base interpreter not detected")
if not in_spack(torch.__file__):
    raise SystemExit("torch is not from Spack")
if not in_spack(jax.__file__):
    raise SystemExit("jax is not from Spack")

print("OK: torch and jax are from Spack")
PY
/opt/spack_store/view/bin/python3 /tmp/verify_spack_provenance.py
'
