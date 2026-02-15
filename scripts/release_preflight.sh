#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  release_preflight.sh [--help] [--no-docker]

Options:
  --no-docker  Skip docker command presence checks.
  --help,-h    Show this help text.
USAGE
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(realpath "${SCRIPT_DIR}/..")"
SKIP_DOCKER=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-docker)
      SKIP_DOCKER=1
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

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

pass() {
  echo "PASS: $*"
}

require_cmd() {
  local cmd="$1"
  command -v "${cmd}" >/dev/null 2>&1 || fail "missing command '${cmd}'"
  pass "command '${cmd}' available"
}

require_file() {
  local path="$1"
  [[ -f "${path}" ]] || fail "missing file ${path}"
  pass "file present ${path}"
}

require_exec() {
  local path="$1"
  [[ -x "${path}" ]] || fail "not executable ${path}"
  pass "executable ${path}"
}

check_help() {
  local label="$1"
  shift
  local output
  output="$($@ 2>&1)" || fail "${label} --help failed"
  echo "${output}" | rg -qi "usage:" || fail "${label} --help missing Usage output"
  pass "${label} --help"
}

require_cmd bash
require_cmd rg
require_cmd sed
require_cmd rsync

if [[ "${SKIP_DOCKER}" != "1" ]]; then
  require_cmd docker
fi

require_file "${REPO_ROOT}/README.md"
require_file "${REPO_ROOT}/RELEASE.md"
require_file "${REPO_ROOT}/CHANGELOG.md"
require_file "${REPO_ROOT}/blog_zephyr_qwen3_tts_audiobook.md"
require_file "${REPO_ROOT}/audiobook/README.md"
require_file "${REPO_ROOT}/LICENSE"
require_file "${REPO_ROOT}/CONTRIBUTING.md"
require_file "${REPO_ROOT}/SECURITY.md"
require_file "${REPO_ROOT}/pyproject.toml"

rg -q '\.env' "${REPO_ROOT}/.gitignore" || fail ".gitignore missing .env pattern"
pass ".gitignore contains .env pattern"

require_exec "${REPO_ROOT}/audiobook/zephyr_launch_container.sh"
require_exec "${REPO_ROOT}/audiobook/run_audiobook_zephyr.sh"
require_exec "${REPO_ROOT}/audiobook/run_book_batch_zephyr.sh"
require_exec "${REPO_ROOT}/audiobook/verify_zephyr_spack_provenance.sh"
require_exec "${REPO_ROOT}/scripts/publish_audiobooks.sh"
require_exec "${REPO_ROOT}/scripts/inkforge_loop.py"
require_exec "${REPO_ROOT}/scripts/supervise_inkforge_agent.sh"

check_help "run_audiobook_zephyr.sh" "${REPO_ROOT}/audiobook/run_audiobook_zephyr.sh" --help
check_help "run_book_batch_zephyr.sh" "${REPO_ROOT}/audiobook/run_book_batch_zephyr.sh" --help
check_help "publish_audiobooks.sh" "${REPO_ROOT}/scripts/publish_audiobooks.sh" --help
check_help "inkforge_loop.py run" python "${REPO_ROOT}/scripts/inkforge_loop.py" run --help
check_help "supervise_inkforge_agent.sh" "${REPO_ROOT}/scripts/supervise_inkforge_agent.sh" --help

AUDIOBOOK_USE_GPU=1 AUDIOBOOK_SKIP_BUILD=1 \
  "${REPO_ROOT}/audiobook/run_audiobook_zephyr.sh" --dry-run \
  "${REPO_ROOT}/README.md" "${REPO_ROOT}/outputs/preflight_dry_run.wav" >/dev/null
pass "run_audiobook_zephyr.sh --dry-run"

AUDIOBOOK_USE_GPU=1 AUDIOBOOK_SKIP_BUILD=1 \
  "${REPO_ROOT}/audiobook/run_book_batch_zephyr.sh" --dry-run >/dev/null
pass "run_book_batch_zephyr.sh --dry-run"

"${REPO_ROOT}/scripts/publish_audiobooks.sh" --dry-run >/dev/null
pass "publish_audiobooks.sh --dry-run"

echo "Release preflight complete"
