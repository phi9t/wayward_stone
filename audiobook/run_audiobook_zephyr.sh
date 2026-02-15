#!/bin/bash

set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  run_audiobook_zephyr.sh [--dry-run] [--help] <input_text_file> <output_wav> [extra script args...]

Options:
  --dry-run   Print resolved configuration and exit without build or run.
  --help,-h   Show this help text.
USAGE
}

DRY_RUN=0
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
      break
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -lt 2 ]]; then
  usage >&2
  exit 1
fi

INPUT_FILE="$1"
OUTPUT_WAV="$2"
shift 2

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(realpath "${SCRIPT_DIR}/..")"
REPO_NAME="$(basename "${REPO_ROOT}")"
LAUNCHER="${ZEPHYR_LAUNCHER:-${SCRIPT_DIR}/zephyr_launch_container.sh}"

if [[ ! -x "${LAUNCHER}" ]]; then
  echo "Missing Zephyr launcher: ${LAUNCHER}" >&2
  exit 1
fi

if [[ ! -f "${INPUT_FILE}" ]]; then
  echo "Input file not found: ${INPUT_FILE}" >&2
  exit 1
fi

INPUT_ABS="$(realpath "${INPUT_FILE}")"
OUTPUT_ABS="$(realpath -m "${OUTPUT_WAV}")"

case "${INPUT_ABS}" in
  "${REPO_ROOT}"/*) ;;
  *)
    echo "Input must be inside repo root: ${REPO_ROOT}" >&2
    exit 1
    ;;
esac

case "${OUTPUT_ABS}" in
  "${REPO_ROOT}"/*) ;;
  *)
    echo "Output must be inside repo root: ${REPO_ROOT}" >&2
    exit 1
    ;;
esac

REL_INPUT="$(realpath --relative-to "${REPO_ROOT}" "${INPUT_ABS}")"
REL_OUTPUT="$(realpath -m --relative-to "${REPO_ROOT}" "${OUTPUT_ABS}")"

if [[ "${AUDIOBOOK_USE_GPU:-1}" != "1" ]]; then
  echo "Zephyr infra is GPU-only. Set AUDIOBOOK_USE_GPU=1." >&2
  exit 1
fi

IMAGE_NAME="${AUDIOBOOK_IMAGE_NAME:-wayward-stone-audio-zephyr:gpu}"
DOCKERFILE_PATH="${AUDIOBOOK_DOCKERFILE:-${SCRIPT_DIR}/Dockerfile.zephyr-gpu}"
DEVICE_MAP_DEFAULT="cuda"

BASE_IMAGE_REF="${ZEPHYR_SNAPSHOT_BASE:-ghcr.io/phi9t/sygaldry/zephyr:hf}"
if [[ -n "${ZEPHYR_SNAPSHOT_DIGEST:-}" ]]; then
  BASE_IMAGE_REF="${BASE_IMAGE_REF}@${ZEPHYR_SNAPSHOT_DIGEST}"
fi

HAS_CHUNKS_DIR=0
HAS_DEVICE_MAP=0
for arg in "$@"; do
  case "${arg}" in
    --chunks-dir|--chunks-dir=*)
      HAS_CHUNKS_DIR=1
      ;;
    --device-map|--device-map=*)
      HAS_DEVICE_MAP=1
      ;;
  esac
done

EXTRA_ARGS=()
if [[ "${HAS_CHUNKS_DIR}" -eq 0 ]]; then
  output_name="$(basename "${REL_OUTPUT}")"
  output_stem="${output_name%.*}"
  chunks_rel="${AUDIOBOOK_CHUNKS_DIR:-$(dirname "${REL_OUTPUT}")/${output_stem}_chunks}"
  EXTRA_ARGS+=(--chunks-dir "/workspace/${REPO_NAME}/${chunks_rel}")
fi

if [[ "${HAS_DEVICE_MAP}" -eq 0 ]]; then
  EXTRA_ARGS+=(--device-map "${DEVICE_MAP_DEFAULT}")
fi

CMD="set -euo pipefail; cd /workspace/${REPO_NAME}; bash /opt/audiobook/zephyr_uv_guard_install.sh qwen-tts soundfile; ./.venv_audio/bin/python /opt/audiobook/qwen3_tts_audiobook.py --input /workspace/${REPO_NAME}/${REL_INPUT} --output /workspace/${REPO_NAME}/${REL_OUTPUT}"
for arg in "${EXTRA_ARGS[@]}" "$@"; do
  CMD+=" $(printf "%q" "${arg}")"
done

if [[ "${DRY_RUN}" == "1" ]]; then
  echo "DRY RUN: single chapter synthesis wrapper"
  echo "repo_root=${REPO_ROOT}"
  echo "launcher=${LAUNCHER}"
  echo "image=${IMAGE_NAME}"
  echo "dockerfile=${DOCKERFILE_PATH}"
  echo "snapshot_base_ref=${BASE_IMAGE_REF}"
  echo "input=${INPUT_ABS}"
  echo "output=${OUTPUT_ABS}"
  echo "skip_build=${AUDIOBOOK_SKIP_BUILD:-0}"
  echo "resolved_cmd=${CMD}"
  exit 0
fi

mkdir -p "$(dirname "${OUTPUT_ABS}")"
if [[ "${HAS_CHUNKS_DIR}" -eq 0 ]]; then
  mkdir -p "${REPO_ROOT}/${chunks_rel}"
fi

if [[ "${AUDIOBOOK_SKIP_BUILD:-0}" != "1" ]]; then
  echo "[1/2] Building Zephyr audio image: ${IMAGE_NAME}"
  docker build \
    --file "${DOCKERFILE_PATH}" \
    --build-arg "ZEPHYR_SNAPSHOT_BASE=${BASE_IMAGE_REF}" \
    --tag "${IMAGE_NAME}" \
    "${SCRIPT_DIR}"
fi

echo "[2/2] Running audiobook generation in Zephyr container"
SYGALDRY_IMAGE="${IMAGE_NAME}" \
  "${LAUNCHER}" \
  --repo "${REPO_ROOT}" \
  --entrypoint run-job \
  -- bash -lc "${CMD}"

echo "Done: ${OUTPUT_ABS}"
