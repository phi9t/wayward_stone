#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  run_book_batch_zephyr.sh [--dry-run] [--help] [--] [render_book_zephyr.py args...]

Options:
  --dry-run   Print resolved configuration and exit without building or running.
  --help,-h   Show this help text.

Environment:
  AUDIOBOOK_USE_GPU=1                Required (Zephyr infra is GPU-only).
  AUDIOBOOK_IMAGE_NAME               Container image tag (default: wayward-stone-audio-zephyr:gpu).
  AUDIOBOOK_DOCKERFILE               Dockerfile path (default: audiobook/Dockerfile.zephyr-gpu).
  AUDIOBOOK_SKIP_BUILD=1             Skip docker image build step.
  ZEPHYR_SNAPSHOT_BASE               Snapshot base image (default: sygaldry/zephyr:spack).
  ZEPHYR_SNAPSHOT_DIGEST             Optional digest pin for snapshot base.
  ZEPHYR_LAUNCHER                    Launcher override (default: audiobook/zephyr_launch_container.sh).
USAGE
}

DRY_RUN=0
FORWARD_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h)
      usage
      exit 0
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --)
      shift
      FORWARD_ARGS+=("$@")
      break
      ;;
    *)
      FORWARD_ARGS+=("$1")
      shift
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(realpath "${SCRIPT_DIR}/..")"
REPO_NAME="$(basename "${REPO_ROOT}")"
LAUNCHER="${ZEPHYR_LAUNCHER:-${SCRIPT_DIR}/zephyr_launch_container.sh}"

if [[ ! -x "${LAUNCHER}" ]]; then
  echo "Missing Zephyr launcher: ${LAUNCHER}" >&2
  exit 1
fi

if [[ "${AUDIOBOOK_USE_GPU:-1}" != "1" ]]; then
  echo "Zephyr infra is GPU-only. Set AUDIOBOOK_USE_GPU=1." >&2
  exit 1
fi

IMAGE_NAME="${AUDIOBOOK_IMAGE_NAME:-wayward-stone-audio-zephyr:gpu}"
DOCKERFILE_PATH="${AUDIOBOOK_DOCKERFILE:-${SCRIPT_DIR}/Dockerfile.zephyr-gpu}"
DEVICE_MAP_DEFAULT="cuda"

BASE_IMAGE_REF="${ZEPHYR_SNAPSHOT_BASE:-sygaldry/zephyr:spack}"
if [[ -n "${ZEPHYR_SNAPSHOT_DIGEST:-}" ]]; then
  BASE_IMAGE_REF="${BASE_IMAGE_REF}@${ZEPHYR_SNAPSHOT_DIGEST}"
fi

HAS_DEVICE_MAP=0
for arg in "${FORWARD_ARGS[@]}"; do
  case "${arg}" in
    --device-map|--device-map=*)
      HAS_DEVICE_MAP=1
      ;;
  esac
done

CMD="set -euo pipefail; cd /workspace/${REPO_NAME}; bash /opt/audiobook/zephyr_uv_guard_install.sh qwen-tts soundfile; ./.venv_audio/bin/python /opt/audiobook/render_book_zephyr.py"
if [[ "${#FORWARD_ARGS[@]}" -gt 0 ]]; then
  for arg in "${FORWARD_ARGS[@]}"; do
    CMD+=" $(printf "%q" "${arg}")"
  done
fi
if [[ "${HAS_DEVICE_MAP}" -eq 0 ]]; then
  CMD+=" --device-map $(printf "%q" "${DEVICE_MAP_DEFAULT}")"
fi

if [[ "${DRY_RUN}" == "1" ]]; then
  echo "DRY RUN: generic book batch synthesis wrapper"
  echo "repo_root=${REPO_ROOT}"
  echo "launcher=${LAUNCHER}"
  echo "image=${IMAGE_NAME}"
  echo "dockerfile=${DOCKERFILE_PATH}"
  echo "snapshot_base_ref=${BASE_IMAGE_REF}"
  echo "skip_build=${AUDIOBOOK_SKIP_BUILD:-0}"
  echo "forward_args=${FORWARD_ARGS[*]:-<none>}"
  echo "resolved_cmd=${CMD}"
  exit 0
fi

if [[ "${AUDIOBOOK_SKIP_BUILD:-0}" != "1" ]]; then
  echo "[1/2] Building Zephyr audio image: ${IMAGE_NAME}"
  docker build \
    --file "${DOCKERFILE_PATH}" \
    --build-arg "ZEPHYR_SNAPSHOT_BASE=${BASE_IMAGE_REF}" \
    --tag "${IMAGE_NAME}" \
    "${SCRIPT_DIR}"
fi

echo "[2/2] Running generic batch synthesis in Zephyr container"
SYGALDRY_IMAGE="${IMAGE_NAME}" \
  "${LAUNCHER}" \
  --repo "${REPO_ROOT}" \
  --entrypoint run-job \
  -- bash -lc "${CMD}"

echo "Done"
