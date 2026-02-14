#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  publish_audiobooks.sh [--dry-run] [--help] [--published-root <dir>] [--pdf-root <dir>] [--audio-run <label>:<dir> ...]

Options:
  --dry-run                 Print planned sync/copy operations without writing.
  --published-root <dir>    Destination root (default: <repo>/outputs/published).
  --pdf-root <dir>          Source PDF root (default: <repo>/output/pdf).
  --audio-run <label>:<dir> Audio run to publish (repeatable).
                            <dir> should contain chapters/ and optional audiobook_all_chapters.wav.
  --help,-h                 Show this help text.
USAGE
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(realpath "${SCRIPT_DIR}/..")"

DRY_RUN=0
PUBLISHED_ROOT="${REPO_ROOT}/outputs/published"
PDF_ROOT="${REPO_ROOT}/output/pdf"
AUDIO_RUNS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --published-root)
      [[ -n "${2:-}" ]] || { echo "Missing value for --published-root" >&2; exit 1; }
      PUBLISHED_ROOT="$(realpath -m "$2")"
      shift 2
      ;;
    --published-root=*)
      PUBLISHED_ROOT="$(realpath -m "${1#*=}")"
      shift
      ;;
    --pdf-root)
      [[ -n "${2:-}" ]] || { echo "Missing value for --pdf-root" >&2; exit 1; }
      PDF_ROOT="$(realpath -m "$2")"
      shift 2
      ;;
    --pdf-root=*)
      PDF_ROOT="$(realpath -m "${1#*=}")"
      shift
      ;;
    --audio-run)
      [[ -n "${2:-}" ]] || { echo "Missing value for --audio-run" >&2; exit 1; }
      AUDIO_RUNS+=("$2")
      shift 2
      ;;
    --audio-run=*)
      AUDIO_RUNS+=("${1#*=}")
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ ${#AUDIO_RUNS[@]} -eq 0 ]]; then
  AUDIO_RUNS+=("book:$(realpath -m "${REPO_ROOT}/outputs/book_audio")")
fi

run_cmd() {
  if [[ "${DRY_RUN}" == "1" ]]; then
    echo "DRY RUN: $*"
  else
    "$@"
  fi
}

run_cmd mkdir -p "${PUBLISHED_ROOT}/pdf"
run_cmd mkdir -p "${PUBLISHED_ROOT}/audio"

if [[ -d "${PDF_ROOT}" ]]; then
  RSYNC_PDF_ARGS=(-a --ignore-existing)
  if [[ "${DRY_RUN}" == "1" ]]; then
    RSYNC_PDF_ARGS+=(-n)
  fi
  run_cmd rsync "${RSYNC_PDF_ARGS[@]}" "${PDF_ROOT}/" "${PUBLISHED_ROOT}/pdf/"
else
  echo "WARN: PDF source root does not exist, skipping: ${PDF_ROOT}" >&2
fi

sync_audio_run() {
  local label="$1"
  local src="$2"
  local dst="${PUBLISHED_ROOT}/audio/${label}"
  local chapters_src="${src}/chapters"
  local master_src="${src}/audiobook_all_chapters.wav"
  local manifest_src="${src}/manifest.json"

  run_cmd mkdir -p "${dst}/chapters"

  if [[ -d "${chapters_src}" ]]; then
    local rsync_args=(-a)
    if [[ "${DRY_RUN}" == "1" ]]; then
      rsync_args+=(-n)
    fi
    run_cmd rsync "${rsync_args[@]}" "${chapters_src}/" "${dst}/chapters/"
  else
    echo "WARN: chapter source missing, skipping: ${chapters_src}" >&2
  fi

  if [[ -f "${master_src}" ]]; then
    run_cmd cp -u "${master_src}" "${dst}/"
  else
    echo "WARN: master file missing, skipping: ${master_src}" >&2
  fi

  if [[ -f "${manifest_src}" ]]; then
    run_cmd cp -u "${manifest_src}" "${dst}/"
  fi
}

for run_spec in "${AUDIO_RUNS[@]}"; do
  if [[ "${run_spec}" != *:* ]]; then
    echo "Invalid --audio-run value (expected <label>:<dir>): ${run_spec}" >&2
    exit 1
  fi
  run_label="${run_spec%%:*}"
  run_dir="${run_spec#*:}"
  if [[ -z "${run_label}" || -z "${run_dir}" ]]; then
    echo "Invalid --audio-run value (expected <label>:<dir>): ${run_spec}" >&2
    exit 1
  fi
  sync_audio_run "${run_label}" "$(realpath -m "${run_dir}")"
done

if [[ "${DRY_RUN}" == "1" ]]; then
  echo "Dry-run complete at $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
else
  echo "Published assets synced at $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
fi
