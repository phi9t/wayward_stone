#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <input_text_file> <output_wav> [extra script args...]"
  echo "Example: $0 chapter_01.md audiobook_ch01.wav --speaker Ryan --language English"
  exit 1
fi

INPUT_FILE="$1"
OUTPUT_WAV="$2"
shift 2

IMAGE_NAME="${AUDIOBOOK_IMAGE_NAME:-}"
AUDIOBOOK_DOCKERFILE="${AUDIOBOOK_DOCKERFILE:-}"
CACHE_HOST_DIR="${HF_CACHE_DIR:-${HOME}/.cache/huggingface}"

if [[ "${AUDIOBOOK_USE_GPU:-0}" == "1" ]]; then
  IMAGE_NAME="${IMAGE_NAME:-qwen3-tts-gpu:latest}"
  AUDIOBOOK_DOCKERFILE="${AUDIOBOOK_DOCKERFILE:-audiobook/Dockerfile.gpu}"
else
  IMAGE_NAME="${IMAGE_NAME:-qwen3-tts-cpu:latest}"
  AUDIOBOOK_DOCKERFILE="${AUDIOBOOK_DOCKERFILE:-audiobook/Dockerfile}"
fi

if [[ ! -d "$CACHE_HOST_DIR" ]]; then
  echo "Missing Hugging Face cache directory: $CACHE_HOST_DIR"
  exit 1
fi

if [[ ! -f "$INPUT_FILE" ]]; then
  echo "Input file not found: $INPUT_FILE"
  exit 1
fi

INPUT_ABS="$(realpath "$INPUT_FILE")"
OUTPUT_ABS="$(realpath -m "$OUTPUT_WAV")"
INPUT_DIR="$(dirname "$INPUT_ABS")"
INPUT_BASENAME="$(basename "$INPUT_ABS")"
OUTPUT_DIR="$(dirname "$OUTPUT_ABS")"
OUTPUT_BASENAME="$(basename "$OUTPUT_ABS")"
mkdir -p "$OUTPUT_DIR"

HAS_CHUNKS_DIR=0
HAS_DEVICE_MAP=0
for arg in "$@"; do
  case "$arg" in
    --chunks-dir|--chunks-dir=*)
      HAS_CHUNKS_DIR=1
      ;;
    --device-map|--device-map=*)
      HAS_DEVICE_MAP=1
      ;;
  esac
done

EXTRA_ARGS=()
VOLUME_ARGS=(
  -v "$CACHE_HOST_DIR:/root/.cache/huggingface"
  -v "$INPUT_DIR:/input:ro"
  -v "$OUTPUT_DIR:/output"
)
if [[ $HAS_CHUNKS_DIR -eq 0 ]]; then
  OUTPUT_STEM="${OUTPUT_BASENAME%.*}"
  CHUNKS_HOST_DIR="${AUDIOBOOK_CHUNKS_DIR:-$OUTPUT_DIR/${OUTPUT_STEM}_chunks}"
  mkdir -p "$CHUNKS_HOST_DIR"
  VOLUME_ARGS+=(-v "$CHUNKS_HOST_DIR:/chunks")
  EXTRA_ARGS+=(--chunks-dir /chunks)
fi

DOCKER_RUN_ARGS=()
if [[ "${AUDIOBOOK_USE_GPU:-0}" == "1" ]]; then
  DOCKER_RUN_ARGS+=(--gpus all)
  if [[ $HAS_DEVICE_MAP -eq 0 ]]; then
    EXTRA_ARGS+=(--device-map cuda)
  fi
fi

echo "[1/2] Building container image: $IMAGE_NAME"
docker build -f "$AUDIOBOOK_DOCKERFILE" -t "$IMAGE_NAME" audiobook

echo "[2/2] Running audiobook generation"
# HF_TOKEN is optional; pass through if set in host env.
DOCKER_ENV=()
if [[ -n "${HF_TOKEN:-}" ]]; then
  DOCKER_ENV+=("-e" "HF_TOKEN=$HF_TOKEN")
fi

docker run --rm \
  "${DOCKER_RUN_ARGS[@]}" \
  "${VOLUME_ARGS[@]}" \
  "${DOCKER_ENV[@]}" \
  "$IMAGE_NAME" \
  --input "/input/$INPUT_BASENAME" \
  --output "/output/$OUTPUT_BASENAME" \
  "${EXTRA_ARGS[@]}" \
  "$@"

echo "Done: $OUTPUT_ABS"
