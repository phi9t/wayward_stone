#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  zephyr_launch_container.sh [--repo <path>] [--entrypoint <name>] [--] [command...]

Environment:
  SYGALDRY_IMAGE             Container image to run (required)
  SYGALDRY_PROJECT_ID        Optional project id for repo-local runtime roots
  ZEPHYR_SHARED_HF_CACHE     Host-shared HuggingFace cache root (required)
  ZEPHYR_SHARED_UV_CACHE     Host-shared uv cache root (required)
  SYGALDRY_NET               Docker network mode (default: host)
  SYGALDRY_IPC               Docker IPC mode (default: host)
  SYGALDRY_EXTRA_DOCKER_ARGS Extra docker args split on spaces
USAGE
}

error() {
  echo "ERROR: $*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || error "Missing required command: $1"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_REPO_ROOT="$(realpath "${SCRIPT_DIR}/..")"

ENTRYPOINT_NAME="default"
REPO_PATH="${DEFAULT_REPO_ROOT}"
PASSTHROUGH=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO_PATH="${2:-}"
      [[ -n "${REPO_PATH}" ]] || error "Missing value for --repo"
      shift 2
      ;;
    --repo=*)
      REPO_PATH="${1#*=}"
      shift
      ;;
    --entrypoint|-e)
      ENTRYPOINT_NAME="${2:-}"
      [[ -n "${ENTRYPOINT_NAME}" ]] || error "Missing value for --entrypoint"
      shift 2
      ;;
    --entrypoint=*)
      ENTRYPOINT_NAME="${1#*=}"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      PASSTHROUGH+=("$@")
      break
      ;;
    *)
      PASSTHROUGH+=("$1")
      shift
      ;;
  esac
done

ENTRYPOINT_NAME="${ENTRYPOINT_NAME%.sh}"
REPO_PATH="$(realpath "${REPO_PATH}")"
[[ -d "${REPO_PATH}" ]] || error "Repo path does not exist: ${REPO_PATH}"

require_cmd docker
docker info >/dev/null 2>&1 || error "Docker daemon is not accessible"
docker info 2>/dev/null | grep -q nvidia || error "NVIDIA Docker runtime not detected"

IMAGE="${SYGALDRY_IMAGE:-}"
[[ -n "${IMAGE}" ]] || error "SYGALDRY_IMAGE is required"

HF_CACHE="${ZEPHYR_SHARED_HF_CACHE:-/mnt/data_infra/zephyr_container_infra/sygaldry/hf_cache}"
UV_CACHE="${ZEPHYR_SHARED_UV_CACHE:-/mnt/data_infra/zephyr_container_infra/sygaldry/uv_cache}"

HF_CACHE="$(realpath -m "${HF_CACHE}")"
UV_CACHE="$(realpath -m "${UV_CACHE}")"
mkdir -p "${HF_CACHE}" "${UV_CACHE}"

PROJECT_ID="${SYGALDRY_PROJECT_ID:-$(basename "${REPO_PATH}")}"
RUNTIME_ROOT="$(realpath -m "${REPO_PATH}/outputs/zephyr_infra/${PROJECT_ID}")"
HOME_DIR="${RUNTIME_ROOT}/home"
mkdir -p "${HOME_DIR}"

REPO_NAME="$(basename "${REPO_PATH}")"
CONTAINER_REPO="/workspace/${REPO_NAME}"

ENTRYPOINT_HOST_FALLBACK="${SCRIPT_DIR}/zephyr_entrypoints/${ENTRYPOINT_NAME}.sh"
ENTRYPOINT_CONTAINER=""
FALLBACK_DIR_MOUNT=""

if docker run --rm --entrypoint /bin/sh "${IMAGE}" -lc "test -x /opt/spack_env/entrypoints/${ENTRYPOINT_NAME}.sh" >/dev/null 2>&1; then
  ENTRYPOINT_CONTAINER="/opt/spack_env/entrypoints/${ENTRYPOINT_NAME}.sh"
else
  [[ -x "${ENTRYPOINT_HOST_FALLBACK}" ]] || error "Entrypoint '${ENTRYPOINT_NAME}' not found in image and fallback missing: ${ENTRYPOINT_HOST_FALLBACK}"
  FALLBACK_DIR_MOUNT="${SCRIPT_DIR}/zephyr_entrypoints:/opt/wayward_entrypoints:ro"
  ENTRYPOINT_CONTAINER="/opt/wayward_entrypoints/${ENTRYPOINT_NAME}.sh"
fi

NET_MODE="${SYGALDRY_NET:-host}"
IPC_MODE="${SYGALDRY_IPC:-host}"

DOCKER_ARGS=(
  --rm
  --init
)
if [[ -t 0 ]]; then
  DOCKER_ARGS+=(--interactive --tty)
fi

DOCKER_ARGS+=(
  "--net=${NET_MODE}"
  "--ipc=${IPC_MODE}"
  --gpus=all
  "--entrypoint=${ENTRYPOINT_CONTAINER}"
  "--workdir=${CONTAINER_REPO}"
  "--volume=${HOME_DIR}:/home/kvothe"
  "--volume=${HF_CACHE}:/opt/hf_cache"
  "--volume=${UV_CACHE}:/opt/uv_cache"
  "--volume=${REPO_PATH}:${CONTAINER_REPO}"
  "--env=SYGALDRY_IN_CONTAINER=1"
  "--env=SYGALDRY_ROOT=${CONTAINER_REPO}"
  "--env=HOME=/home/kvothe"
  "--env=USER=kvothe"
  "--env=HF_HOME=/opt/hf_cache"
  "--env=HUGGINGFACE_HUB_CACHE=/opt/hf_cache/hub"
  "--env=UV_CACHE_DIR=/opt/uv_cache"
)

if docker info 2>/dev/null | grep -q ' Runtimes:.*nvidia'; then
  DOCKER_ARGS+=(--runtime=nvidia)
fi

if [[ -n "${FALLBACK_DIR_MOUNT}" ]]; then
  DOCKER_ARGS+=("--volume=${FALLBACK_DIR_MOUNT}")
fi

for var in TERM LANG LC_ALL; do
  if [[ -n "${!var:-}" ]]; then
    DOCKER_ARGS+=("--env=${var}=${!var}")
  fi
done

if [[ -n "${SYGALDRY_EXTRA_DOCKER_ARGS:-}" ]]; then
  EXTRA_ARGS=()
  read -r -a EXTRA_ARGS <<<"${SYGALDRY_EXTRA_DOCKER_ARGS}"
  DOCKER_ARGS+=("${EXTRA_ARGS[@]}")
fi

exec docker run "${DOCKER_ARGS[@]}" "${IMAGE}" "${PASSTHROUGH[@]}"
