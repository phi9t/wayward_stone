#!/usr/bin/env bash
set -euo pipefail

if [[ -f "/opt/spack_src/share/spack/setup-env.sh" ]]; then
  # shellcheck disable=SC1091
  source "/opt/spack_src/share/spack/setup-env.sh"
fi

if [[ -d "/usr/local/cuda" ]]; then
  export CUDA_HOME="/usr/local/cuda"
  export PATH="${CUDA_HOME}/bin:${PATH}"
  export LD_LIBRARY_PATH="${CUDA_HOME}/lib64:${LD_LIBRARY_PATH:-}"
fi

_activated=false
_zephyr_env="${SYGALDRY_SPACK_ENV:-/opt/spack_env/zephyr}"
_repo_zephyr_env="${SYGALDRY_ROOT:-/workspace}/audiobook/zephyr_spack_env"

if [[ -f "spack.yaml" || -f "spack.lock" ]]; then
  spack env activate . 2>/dev/null && _activated=true || true
fi

if [[ "${_activated}" != "true" && -d "${_zephyr_env}" ]]; then
  if [[ ! -f "${_zephyr_env}/spack.yaml" && -f "${_zephyr_env}/spack_src.yaml" ]]; then
    cp "${_zephyr_env}/spack_src.yaml" "${_zephyr_env}/spack.yaml" 2>/dev/null || true
  fi
  if [[ -f "${_zephyr_env}/spack.yaml" ]]; then
    spack env activate "${_zephyr_env}" 2>/dev/null && _activated=true || true
  fi
fi

if [[ "${_activated}" != "true" && -d "${_repo_zephyr_env}" && -f "${_repo_zephyr_env}/spack.yaml" ]]; then
  spack env activate "${_repo_zephyr_env}" 2>/dev/null && _activated=true || true
fi

if [[ "${_activated}" != "true" && -d "/opt/spack_store/view" ]]; then
  echo "[run-job] WARNING: Spack env activation failed; using view fallback" >&2
  export PATH="/opt/spack_store/view/bin:${PATH}"
  _py_ver="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "3.12")"
  export PYTHONPATH="/opt/spack_store/view/lib/python${_py_ver}/site-packages:${PYTHONPATH:-}"
  export LD_LIBRARY_PATH="/opt/spack_store/view/lib:/opt/spack_store/view/lib64:${LD_LIBRARY_PATH:-}"
fi

unset _activated _zephyr_env _repo_zephyr_env _py_ver

if [[ $# -lt 1 ]]; then
  echo "Usage: run-job.sh <command...>" >&2
  exit 2
fi

exec "$@"
