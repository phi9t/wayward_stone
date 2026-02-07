#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <package> [package ...]" >&2
  exit 2
fi

if [[ -f "/opt/spack_src/share/spack/setup-env.sh" ]]; then
  source "/opt/spack_src/share/spack/setup-env.sh"
fi

ZEPHYR_ENV="${SYGALDRY_SPACK_ENV:-/opt/spack_env/zephyr}"
if [[ -f "${ZEPHYR_ENV}/spack.yaml" ]]; then
  spack env activate "${ZEPHYR_ENV}" >/dev/null 2>&1 || true
fi

SPACK_PY="/opt/spack_store/view/bin/python3"
if [[ ! -x "${SPACK_PY}" ]]; then
  SPACK_PY="$(command -v python3)"
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv not found in PATH" >&2
  exit 1
fi

normalize_name() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[-_.]+/-/g'
}

extract_pkg_name() {
  local spec="$1"
  spec="${spec%%[*}"
  spec="${spec%%[<>=!~]*}"
  normalize_name "${spec}"
}

is_forbidden_cuda_pkg() {
  local pkg="$1"
  case "${pkg}" in
    nvidia-*|cuda*|cupy*|triton*|xformers*|flash-attn*|bitsandbytes*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

VENV_DIR="${VENV_DIR:-.venv_audio}"
if [[ -d "${VENV_DIR}" ]] && [[ ! -f "${VENV_DIR}/bin/activate" ]]; then
  rm -rf "${VENV_DIR}"
fi
if [[ ! -f "${VENV_DIR}/bin/activate" ]]; then
  uv venv --python "${SPACK_PY}" --system-site-packages "${VENV_DIR}"
fi

PY_VER="$("${SPACK_PY}" - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)"
SITE_PACKAGES="${VENV_DIR}/lib/python${PY_VER}/site-packages"
mkdir -p "${SITE_PACKAGES}"
if [[ -d "/opt/spack_store/view/lib/python${PY_VER}/site-packages" ]]; then
  echo "/opt/spack_store/view/lib/python${PY_VER}/site-packages" > "${SITE_PACKAGES}/spack-view.pth"
fi

SPACK_LIST_FILE="${SPACK_LIST_FILE:-/tmp/spack-installed-names.txt}"
CONSTRAINTS_FILE="${CONSTRAINTS_FILE:-/tmp/spack-constraints.txt}"
EXCLUDES_FILE="${EXCLUDES_FILE:-/tmp/uv-policy-excludes.txt}"

"${SPACK_PY}" - <<'PY' > "${SPACK_LIST_FILE}"
import importlib.metadata as md
def norm(name: str) -> str:
    return "-".join(name.lower().replace("_", "-").split("-"))
names = set()
for dist in md.distributions():
    name = dist.metadata.get("Name")
    if name:
        names.add(norm(name))
for name in sorted(names):
    print(name)
PY

"${SPACK_PY}" - <<'PY' > "${CONSTRAINTS_FILE}"
import importlib.metadata as md
for dist in sorted(md.distributions(), key=lambda d: (d.metadata.get("Name", "").lower(), d.version)):
    name = dist.metadata.get("Name")
    if name:
        print(f"{name}=={dist.version}")
PY

{
  cat "${SPACK_LIST_FILE}"
  cat <<'EOF'
nvidia-cublas-cu12
nvidia-cuda-cupti-cu12
nvidia-cuda-nvrtc-cu12
nvidia-cuda-runtime-cu12
nvidia-cudnn-cu12
nvidia-cufft-cu12
nvidia-cufile-cu12
nvidia-curand-cu12
nvidia-cusolver-cu12
nvidia-cusparse-cu12
nvidia-cusparselt-cu12
nvidia-nccl-cu12
nvidia-nvjitlink-cu12
nvidia-nvtx-cu12
cuda-python
cuda-bindings
cuda-pathfinder
cuda-toolkit
triton
xformers
flash-attn
bitsandbytes
cupy
cupy-cuda11x
cupy-cuda12x
EOF
} | awk 'NF' | sort -u > "${EXCLUDES_FILE}"

SPACK_INSTALLED="$(cat "${SPACK_LIST_FILE}")"
declare -a BLOCKED=()
declare -a ALLOWED=()
for arg in "$@"; do
  pkg="$(extract_pkg_name "${arg}")"
  if [[ -z "${pkg}" ]]; then
    continue
  fi

  if is_forbidden_cuda_pkg "${pkg}"; then
    BLOCKED+=("${arg} (forbidden CUDA/NVIDIA package)")
    continue
  fi

  if echo "${SPACK_INSTALLED}" | grep -Fxq "${pkg}"; then
    BLOCKED+=("${arg} (already provided by Spack)")
    continue
  fi

  ALLOWED+=("${arg}")
done

if [[ "${#BLOCKED[@]}" -gt 0 ]]; then
  echo "Zephyr package policy filtered these package specs:" >&2
  printf '  - %s\n' "${BLOCKED[@]}" >&2
fi

if [[ "${#ALLOWED[@]}" -eq 0 ]]; then
  echo "No new packages to install; all requested packages are already satisfied by policy."
  exit 0
fi

echo "Verifying Spack provenance for torch and jax..."
"${SPACK_PY}" - <<'PY'
import sys
import torch
import jax

def from_spack(path: str) -> bool:
    return "/opt/spack_store/" in (path or "")

if not from_spack(sys.base_prefix):
    raise SystemExit(f"Spack base interpreter not detected: {sys.base_prefix}")
if not from_spack(torch.__file__):
    raise SystemExit(f"torch is not from Spack: {torch.__file__}")
if not from_spack(jax.__file__):
    raise SystemExit(f"jax is not from Spack: {jax.__file__}")
print("OK: base interpreter, torch, and jax are from Spack")
PY

SPACK_TORCH_VERSION="$("${SPACK_PY}" - <<'PY'
import torch
print(torch.__version__.split("+", 1)[0])
PY
)"
TORCHAUDIO_PIN="${TORCHAUDIO_PIN:-${SPACK_TORCH_VERSION}}"

if ! grep -Fxq "torchaudio" "${SPACK_LIST_FILE}"; then
  echo "Spack does not provide torchaudio; installing pinned torchaudio==${TORCHAUDIO_PIN} via uv (CPU backend)." >&2
  uv pip install \
    --python "${VENV_DIR}/bin/python" \
    --no-deps \
    --torch-backend cpu \
    "torchaudio==${TORCHAUDIO_PIN}"

  "${VENV_DIR}/bin/python" - <<'PY'
import importlib.metadata as md
import torch
import torchaudio
import torchaudio.compliance.kaldi as _kaldi  # noqa: F401

torch_v = torch.__version__.split("+", 1)[0]
ta_v = torchaudio.__version__.split("+", 1)[0]
if ta_v != torch_v:
    raise SystemExit(f"torchaudio/torch version mismatch: torchaudio={ta_v} torch={torch_v}")

reqs = md.distribution("torchaudio").requires or []
expected = f"torch=={torch_v}"
if not any(r.startswith(expected) for r in reqs):
    raise SystemExit(f"torchaudio requires unexpected torch spec: {reqs}")

print(f"OK: torchaudio {torchaudio.__version__} is ABI-compatible with torch {torch.__version__}")
PY
fi

if ! grep -Eiq '^torchaudio([<>=!~].*)?$' "${CONSTRAINTS_FILE}"; then
  echo "torchaudio==${TORCHAUDIO_PIN}" >> "${CONSTRAINTS_FILE}"
fi

UV_BASE=(
  uv pip install
  --python "${VENV_DIR}/bin/python"
  --torch-backend cpu
  --constraints "${CONSTRAINTS_FILE}"
  --excludes "${EXCLUDES_FILE}"
  --strict
)

echo "Running uv dry-run with policy enforcement..."
"${UV_BASE[@]}" --dry-run "${ALLOWED[@]}"

echo "Installing allowed packages with policy enforcement..."
"${UV_BASE[@]}" "${ALLOWED[@]}"

echo "Validating dependency closure across venv + Spack..."
"${VENV_DIR}/bin/python" - <<'PY'
import importlib.metadata as md
import re
import site
import sys
from pathlib import Path

def norm(name: str) -> str:
    return "-".join(name.lower().replace("_", "-").split("-"))

def parse_req_name(req_line: str) -> str | None:
    part = req_line.split(";", 1)[0].strip()
    if not part:
        return None
    match = re.match(r"^([A-Za-z0-9_.-]+)", part)
    if not match:
        return None
    return norm(match.group(1))

def marker_allows(req_line: str) -> bool:
    if ";" not in req_line:
        return True
    marker = req_line.split(";", 1)[1].strip()
    if not marker:
        return True
    try:
        from packaging.markers import Marker, default_environment
        return Marker(marker).evaluate(default_environment())
    except Exception:
        return True

venv_site = None
for p in site.getsitepackages():
    if "/.venv_audio/" in p.replace("\\", "/"):
        venv_site = Path(p)
        break
if venv_site is None:
    raise SystemExit("Unable to locate venv site-packages path for dependency check")

all_names = set()
for dist in md.distributions():
    name = dist.metadata.get("Name")
    if name:
        all_names.add(norm(name))

missing = []
for dist in md.distributions(path=[str(venv_site)]):
    dist_name = dist.metadata.get("Name")
    if not dist_name:
        continue
    for req_line in (dist.requires or []):
        if not marker_allows(req_line):
            continue
        dep_name = parse_req_name(req_line)
        if dep_name and dep_name not in all_names:
            missing.append((dist_name, dep_name, req_line))

if missing:
    print("Missing runtime dependencies after uv install:")
    for owner, dep, req in missing[:50]:
        print(f" - {owner} -> {dep} ({req})")
    raise SystemExit(f"Dependency closure failed with {len(missing)} missing requirements")

print("OK: dependency closure satisfied across venv + Spack")
PY

echo "Validating no Spack package override in venv..."
"${VENV_DIR}/bin/python" - <<'PY'
import importlib.metadata as md
import pathlib

def norm(name: str) -> str:
    return "-".join(name.lower().replace("_", "-").split("-"))

spack_names = set(pathlib.Path("/tmp/spack-installed-names.txt").read_text(encoding="utf-8").splitlines())
venv_site = pathlib.Path(".venv_audio").resolve() / "lib"
py_dirs = sorted(venv_site.glob("python*/site-packages"))
if not py_dirs:
    raise SystemExit("Unable to find venv site-packages path")
local_names = set()
for dist in md.distributions(path=[str(py_dirs[0])]):
    name = dist.metadata.get("Name")
    if name:
        local_names.add(norm(name))

overlap = sorted(local_names & spack_names)
if overlap:
    raise SystemExit(f"Policy violation: venv overrides Spack packages: {overlap}")
print("OK: venv does not override Spack-installed packages")
PY

echo "Validating forbidden CUDA/NVIDIA packages are absent in venv..."
forbidden_in_venv="$(find "${SITE_PACKAGES}" -maxdepth 1 -type d \( -iname 'nvidia*' -o -iname 'cuda*' \) 2>/dev/null || true)"
if [[ -n "${forbidden_in_venv}" ]]; then
  echo "ERROR: forbidden CUDA/NVIDIA packages were installed into venv:" >&2
  echo "${forbidden_in_venv}" >&2
  exit 4
fi

echo "Installed packages in ${VENV_DIR}: ${ALLOWED[*]}"
