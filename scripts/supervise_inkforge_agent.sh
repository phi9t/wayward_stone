#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  supervise_inkforge_agent.sh --run-id <id> [options]

Description:
  Launch and monitor inkforge_loop continuously via a coding agent launcher
  (codex/opencode/claude). Reports health issues to console and
  <run_root>/logs/supervisor_alerts.jsonl.

Required:
  --run-id <id>                   Run identifier under workspace root.

Options:
  --workspace-root <path>         Root path for runs (default: inkforge)
  --target-chapter <n>            Initial target chapter (default: 3)
  --step <n>                      Target increment after successful cycle (default: 1)
  --supervisor-agent <name>       Launcher agent: codex|opencode|claude (default: codex)
  --supervisor-model <name>       Supervisor model alias (default: gpt-5)
  --opencode-supervisor-agent <id>
                                  OpenCode agent id for supervision (default: build)
  --writer-agent <id>             Inkforge writer agent id (default: writer)
  --critic-model <name>           Inkforge critic model alias (default: sonnet)
  --reviser-model <name>          Inkforge reviser model alias (default: gpt-5)
  --max-revision-loops <n>        Max revise/re-critique loops per chapter (default: 8)
  --quality-overall-min <f>       Quality gate overall min (default: 7.5)
  --quality-category-min <f>      Quality gate category min (default: 7.0)
  --max-total-failures <n>        Max chapter restarts before abort (default: 200)
  --stale-minutes <n>             Alert/restart if no new events for N minutes (default: 15)
  --max-same-phase-checks <n>     Alert/restart if chapter+phase unchanged too long (default: 20)
  --poll-seconds <n>              Monitoring poll interval (default: 30)
  --sleep-between-cycles <n>      Delay before relaunch (default: 3)
  --help,-h                       Show help text
USAGE
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(realpath "${SCRIPT_DIR}/..")"
INKFORGE_ENTRY="${REPO_ROOT}/scripts/inkforge_loop.py"

WORKSPACE_ROOT="inkforge"
RUN_ID=""
START_TARGET=3
STEP=1
SUPERVISOR_AGENT="codex"
SUPERVISOR_MODEL="gpt-5"
OPENCODE_SUPERVISOR_AGENT="build"
WRITER_AGENT="writer"
CRITIC_MODEL="sonnet"
REVISER_MODEL="gpt-5"
MAX_REVISION_LOOPS=8
QUALITY_OVERALL_MIN="7.5"
QUALITY_CATEGORY_MIN="7.0"
MAX_TOTAL_FAILURES=200
STALE_MINUTES=15
MAX_SAME_PHASE_CHECKS=20
POLL_SECONDS=30
SLEEP_BETWEEN_CYCLES=3

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace-root)
      WORKSPACE_ROOT="$2"
      shift 2
      ;;
    --run-id)
      RUN_ID="$2"
      shift 2
      ;;
    --target-chapter)
      START_TARGET="$2"
      shift 2
      ;;
    --step)
      STEP="$2"
      shift 2
      ;;
    --supervisor-agent)
      SUPERVISOR_AGENT="$2"
      shift 2
      ;;
    --supervisor-model)
      SUPERVISOR_MODEL="$2"
      shift 2
      ;;
    --opencode-supervisor-agent)
      OPENCODE_SUPERVISOR_AGENT="$2"
      shift 2
      ;;
    --writer-agent)
      WRITER_AGENT="$2"
      shift 2
      ;;
    --critic-model)
      CRITIC_MODEL="$2"
      shift 2
      ;;
    --reviser-model)
      REVISER_MODEL="$2"
      shift 2
      ;;
    --max-revision-loops)
      MAX_REVISION_LOOPS="$2"
      shift 2
      ;;
    --quality-overall-min)
      QUALITY_OVERALL_MIN="$2"
      shift 2
      ;;
    --quality-category-min)
      QUALITY_CATEGORY_MIN="$2"
      shift 2
      ;;
    --max-total-failures)
      MAX_TOTAL_FAILURES="$2"
      shift 2
      ;;
    --stale-minutes)
      STALE_MINUTES="$2"
      shift 2
      ;;
    --max-same-phase-checks)
      MAX_SAME_PHASE_CHECKS="$2"
      shift 2
      ;;
    --poll-seconds)
      POLL_SECONDS="$2"
      shift 2
      ;;
    --sleep-between-cycles)
      SLEEP_BETWEEN_CYCLES="$2"
      shift 2
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

if [[ -z "${RUN_ID}" ]]; then
  echo "--run-id is required" >&2
  usage >&2
  exit 1
fi

if ! [[ "${START_TARGET}" =~ ^[0-9]+$ ]] || (( START_TARGET <= 0 )); then
  echo "--target-chapter must be a positive integer" >&2
  exit 1
fi
if ! [[ "${STEP}" =~ ^[0-9]+$ ]] || (( STEP <= 0 )); then
  echo "--step must be a positive integer" >&2
  exit 1
fi
if ! [[ "${MAX_REVISION_LOOPS}" =~ ^[0-9]+$ ]] || (( MAX_REVISION_LOOPS <= 0 )); then
  echo "--max-revision-loops must be a positive integer" >&2
  exit 1
fi
if ! [[ "${MAX_TOTAL_FAILURES}" =~ ^[0-9]+$ ]] || (( MAX_TOTAL_FAILURES <= 0 )); then
  echo "--max-total-failures must be a positive integer" >&2
  exit 1
fi
if ! [[ "${STALE_MINUTES}" =~ ^[0-9]+$ ]] || (( STALE_MINUTES <= 0 )); then
  echo "--stale-minutes must be a positive integer" >&2
  exit 1
fi
if ! [[ "${MAX_SAME_PHASE_CHECKS}" =~ ^[0-9]+$ ]] || (( MAX_SAME_PHASE_CHECKS <= 0 )); then
  echo "--max-same-phase-checks must be a positive integer" >&2
  exit 1
fi
if ! [[ "${POLL_SECONDS}" =~ ^[0-9]+$ ]] || (( POLL_SECONDS <= 0 )); then
  echo "--poll-seconds must be a positive integer" >&2
  exit 1
fi
if ! [[ "${SLEEP_BETWEEN_CYCLES}" =~ ^[0-9]+$ ]] || (( SLEEP_BETWEEN_CYCLES < 0 )); then
  echo "--sleep-between-cycles must be a non-negative integer" >&2
  exit 1
fi

case "${SUPERVISOR_AGENT}" in
  codex|opencode|claude)
    ;;
  *)
    echo "--supervisor-agent must be one of: codex|opencode|claude" >&2
    exit 1
    ;;
esac

require_cmd() {
  local cmd="$1"
  command -v "${cmd}" >/dev/null 2>&1 || {
    echo "Missing required command: ${cmd}" >&2
    exit 1
  }
}

require_cmd python
require_cmd jq
require_cmd tail
require_cmd stat
require_cmd date

case "${SUPERVISOR_AGENT}" in
  codex)
    require_cmd codex
    ;;
  opencode)
    require_cmd opencode
    ;;
  claude)
    require_cmd claude
    ;;
esac

[[ -f "${INKFORGE_ENTRY}" ]] || {
  echo "Missing inkforge entrypoint: ${INKFORGE_ENTRY}" >&2
  exit 1
}

RUN_ROOT="${WORKSPACE_ROOT}/${RUN_ID}"
LOGS_DIR="${RUN_ROOT}/logs"
EVENTS_FILE="${LOGS_DIR}/events.jsonl"
RUN_STATE_FILE="${RUN_ROOT}/state/run_state.json"
ALERTS_FILE="${LOGS_DIR}/supervisor_alerts.jsonl"

mkdir -p "${LOGS_DIR}"
touch "${ALERTS_FILE}"

now_iso() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

now_epoch() {
  date +%s
}

log() {
  echo "[$(now_iso)] $*"
}

emit_alert() {
  local severity="$1"
  local code="$2"
  local message="$3"
  local chapter_json="${4:-null}"
  local phase="${5:-}"
  local context_json="${6-}"
  if [[ -z "${context_json}" ]]; then
    context_json='{}'
  fi
  local payload

  payload="$({
    jq -cn \
      --arg ts "$(now_iso)" \
      --arg severity "${severity}" \
      --arg run_id "${RUN_ID}" \
      --arg code "${code}" \
      --arg message "${message}" \
      --arg phase "${phase}" \
      --argjson chapter "${chapter_json}" \
      --argjson context "${context_json}" \
      '{ts:$ts,severity:$severity,run_id:$run_id,chapter:$chapter,phase:$phase,code:$code,message:$message,context:$context}'
  } 2>/dev/null)"

  if [[ -z "${payload}" ]]; then
    payload="{\"ts\":\"$(now_iso)\",\"severity\":\"${severity}\",\"run_id\":\"${RUN_ID}\",\"code\":\"${code}\",\"message\":\"${message}\"}"
  fi

  echo "${payload}" >> "${ALERTS_FILE}"
  echo "[$(now_iso)] [${severity}] [${code}] ${message}"
}

event_count() {
  if [[ -f "${EVENTS_FILE}" ]]; then
    wc -l < "${EVENTS_FILE}" | tr -d ' '
  else
    echo 0
  fi
}

file_mtime_epoch() {
  local path="$1"
  stat -c %Y "${path}" 2>/dev/null || echo 0
}

last_event_compact() {
  if [[ -f "${EVENTS_FILE}" ]]; then
    tail -n 1 "${EVENTS_FILE}" 2>/dev/null | tr -d '\n' || true
  fi
}

current_chapter_json() {
  if [[ -f "${RUN_STATE_FILE}" ]]; then
    jq -c '.current_chapter // null' "${RUN_STATE_FILE}" 2>/dev/null || echo null
  else
    echo null
  fi
}

current_phase_text() {
  local chapter
  chapter="$(current_chapter_json)"
  if [[ "${chapter}" == "null" ]]; then
    echo ""
    return 0
  fi
  local chapter_file
  chapter_file="${RUN_ROOT}/state/chapter_$(printf '%03d' "${chapter}")_state.json"
  if [[ ! -f "${chapter_file}" ]]; then
    echo ""
    return 0
  fi
  jq -r '.phase // ""' "${chapter_file}" 2>/dev/null || echo ""
}

current_phase_key() {
  local chapter
  chapter="$(current_chapter_json)"
  local phase
  phase="$(current_phase_text)"
  if [[ "${chapter}" == "null" || -z "${phase}" ]]; then
    echo ""
  else
    echo "${chapter}:${phase}"
  fi
}

target_completed() {
  local target="$1"
  if [[ ! -f "${RUN_STATE_FILE}" ]]; then
    return 1
  fi
  jq -e --argjson target "${target}" '(.completed_chapters // []) | index($target) != null' "${RUN_STATE_FILE}" >/dev/null 2>&1
}

calculate_initial_target() {
  local target="$START_TARGET"
  if [[ -f "${RUN_STATE_FILE}" ]]; then
    local completed_max
    completed_max="$(jq -r '(.completed_chapters // []) | (max // 0)' "${RUN_STATE_FILE}" 2>/dev/null || echo 0)"
    if [[ "${completed_max}" =~ ^[0-9]+$ ]]; then
      local candidate=$((completed_max + STEP))
      if (( candidate > target )); then
        target="${candidate}"
      fi
    else
      emit_alert "warn" "STATE_READ_ERROR" "Unable to parse completed_chapters; using provided initial target" "null" "" '{}'
    fi
  fi
  echo "${target}"
}

build_inkforge_cmd() {
  local target="$1"
  local cmd=(
    python "${INKFORGE_ENTRY}" run
    --workspace-root "${WORKSPACE_ROOT}"
    --run-id "${RUN_ID}"
    --target-chapter "${target}"
    --max-revision-loops "${MAX_REVISION_LOOPS}"
    --max-total-failures "${MAX_TOTAL_FAILURES}"
    --quality-overall-min "${QUALITY_OVERALL_MIN}"
    --quality-category-min "${QUALITY_CATEGORY_MIN}"
    --writer-agent "${WRITER_AGENT}"
    --critic-model "${CRITIC_MODEL}"
    --reviser-model "${REVISER_MODEL}"
    --resume
  )
  printf '%q ' "${cmd[@]}"
}

launch_via_agent() {
  local inkforge_cmd="$1"
  local worker_log="$2"
  local prompt

  prompt="Run the following shell command exactly and wait for completion.\n"
  prompt+="Do not modify files manually and do not ask follow-up questions.\n"
  prompt+="Command:\n${inkforge_cmd}\n"

  case "${SUPERVISOR_AGENT}" in
    codex)
      codex exec \
        --json \
        --dangerously-bypass-approvals-and-sandbox \
        --model "${SUPERVISOR_MODEL}" \
        -C "${REPO_ROOT}" \
        "${prompt}" >"${worker_log}" 2>&1 &
      ;;
    opencode)
      opencode run --format json --agent "${OPENCODE_SUPERVISOR_AGENT}" "${prompt}" >"${worker_log}" 2>&1 &
      ;;
    claude)
      claude -p --output-format json --model "${SUPERVISOR_MODEL}" --permission-mode default "${prompt}" >"${worker_log}" 2>&1 &
      ;;
  esac
}

report_worker_log_issues() {
  local worker_log="$1"
  local chapter_json="$2"
  local phase="$3"

  if [[ ! -f "${worker_log}" ]]; then
    return 0
  fi

  if rg -qi "missing required schema fields|output was not valid JSON|AgentInvocationError|Writer produced event telemetry|Writer produced empty draft_text|did not resemble a chapter draft" "${worker_log}"; then
    emit_alert "error" "SCHEMA_OR_PARSE_ERROR" "Worker reported agent output schema/parse failure" "${chapter_json}" "${phase}" '{}'
  fi

  if rg -qi "permission requested|auto-rejecting|permission_denials|denied" "${worker_log}"; then
    emit_alert "error" "AGENT_PERMISSION_DENIED" "Worker reported agent permission denial" "${chapter_json}" "${phase}" '{}'
  fi
}

MONITOR_SHUTDOWN=0
WORKER_PID=""

handle_shutdown() {
  MONITOR_SHUTDOWN=1
  if [[ -n "${WORKER_PID}" ]] && kill -0 "${WORKER_PID}" 2>/dev/null; then
    kill "${WORKER_PID}" 2>/dev/null || true
  fi
  log "Shutdown requested; exiting supervisor"
}
trap handle_shutdown INT TERM

monitor_worker() {
  local pid="$1"
  local target="$2"
  local worker_log="$3"

  local stale_seconds=$((STALE_MINUTES * 60))
  local last_events
  last_events="$(event_count)"
  local last_mtime
  last_mtime="$(file_mtime_epoch "${EVENTS_FILE}")"
  local last_progress_epoch
  last_progress_epoch="$(now_epoch)"
  local phase_key_prev=""
  local same_phase_checks=0
  local revision_pressure_alerted=0

  while kill -0 "${pid}" 2>/dev/null; do
    sleep "${POLL_SECONDS}"

    local now
    now="$(now_epoch)"
    local events_now
    events_now="$(event_count)"
    local mtime_now
    mtime_now="$(file_mtime_epoch "${EVENTS_FILE}")"

    if (( events_now > last_events )) || (( mtime_now > last_mtime )); then
      last_events="${events_now}"
      last_mtime="${mtime_now}"
      last_progress_epoch="${now}"
      local event_line
      event_line="$(last_event_compact)"
      if [[ -n "${event_line}" ]]; then
        log "progress target=${target} event=${event_line}"
      else
        log "progress target=${target} events=${events_now}"
      fi
    fi

    local chapter_json
    chapter_json="$(current_chapter_json)"
    local phase
    phase="$(current_phase_text)"
    local phase_key
    phase_key="$(current_phase_key)"

    if [[ -n "${phase_key}" ]]; then
      if [[ "${phase_key}" == "${phase_key_prev}" ]]; then
        same_phase_checks=$((same_phase_checks + 1))
      else
        phase_key_prev="${phase_key}"
        same_phase_checks=0
      fi
    fi

    if [[ "${chapter_json}" != "null" ]]; then
      local chapter_file
      chapter_file="${RUN_ROOT}/state/chapter_$(printf '%03d' "${chapter_json}")_state.json"
      if [[ -f "${chapter_file}" ]]; then
        local revision_count
        revision_count="$(jq -r '.revision_count // 0' "${chapter_file}" 2>/dev/null || echo 0)"
        if [[ "${revision_count}" =~ ^[0-9]+$ ]] && (( revision_count >= MAX_REVISION_LOOPS - 1 )) && (( revision_pressure_alerted == 0 )); then
          emit_alert "warn" "REVISION_PRESSURE" "Chapter revision count is near max-revision-loops" "${chapter_json}" "${phase}" "{\"revision_count\":${revision_count},\"max_revision_loops\":${MAX_REVISION_LOOPS}}"
          revision_pressure_alerted=1
        fi
      fi
    fi

    if (( now - last_progress_epoch > stale_seconds )); then
      emit_alert "error" "STALE_EVENTS" "No new events for ${STALE_MINUTES} minutes; restarting worker" "${chapter_json}" "${phase}" "{\"target\":${target},\"stale_minutes\":${STALE_MINUTES}}"
      kill "${pid}" 2>/dev/null || true
      wait "${pid}" 2>/dev/null || true
      return 124
    fi

    if (( same_phase_checks >= MAX_SAME_PHASE_CHECKS )); then
      emit_alert "error" "LOOP_STUCK" "Chapter phase unchanged for too many checks; restarting worker" "${chapter_json}" "${phase}" "{\"target\":${target},\"max_same_phase_checks\":${MAX_SAME_PHASE_CHECKS}}"
      kill "${pid}" 2>/dev/null || true
      wait "${pid}" 2>/dev/null || true
      return 125
    fi

    if (( MONITOR_SHUTDOWN == 1 )); then
      kill "${pid}" 2>/dev/null || true
      wait "${pid}" 2>/dev/null || true
      return 130
    fi
  done

  wait "${pid}" 2>/dev/null
}

TARGET="$(calculate_initial_target)"
ATTEMPT=0

log "Starting supervisor agent=${SUPERVISOR_AGENT} run_id=${RUN_ID} workspace_root=${WORKSPACE_ROOT} target=${TARGET}"
emit_alert "info" "SUPERVISOR_START" "Supervisor started" "null" "" "{\"agent\":\"${SUPERVISOR_AGENT}\",\"target\":${TARGET}}"

while (( MONITOR_SHUTDOWN == 0 )); do
  ATTEMPT=$((ATTEMPT + 1))
  TS="$(date -u +%Y%m%dT%H%M%SZ)"
  WORKER_LOG="${LOGS_DIR}/supervisor_worker_${TS}.log"
  INKFORGE_CMD="$(build_inkforge_cmd "${TARGET}")"

  log "launch attempt=${ATTEMPT} target=${TARGET} run_id=${RUN_ID}"
  launch_via_agent "${INKFORGE_CMD}" "${WORKER_LOG}"
  WORKER_PID="$!"
  log "worker pid=${WORKER_PID} log=${WORKER_LOG}"

  set +e
  monitor_worker "${WORKER_PID}" "${TARGET}" "${WORKER_LOG}"
  RC=$?
  set -e

  CHAPTER_JSON="$(current_chapter_json)"
  PHASE="$(current_phase_text)"

  if (( MONITOR_SHUTDOWN == 1 )); then
    break
  fi

  if (( RC == 0 )); then
    if target_completed "${TARGET}"; then
      emit_alert "info" "TARGET_COMPLETED" "Target chapter reached; extending target" "${CHAPTER_JSON}" "${PHASE}" "{\"target\":${TARGET},\"step\":${STEP}}"
      TARGET=$((TARGET + STEP))
      sleep "${SLEEP_BETWEEN_CYCLES}"
      continue
    fi

    emit_alert "warn" "TARGET_NOT_COMPLETED" "Worker exited 0 but target not completed; retrying same target" "${CHAPTER_JSON}" "${PHASE}" "{\"target\":${TARGET}}"
    sleep "${SLEEP_BETWEEN_CYCLES}"
    continue
  fi

  if (( RC == 124 || RC == 125 )); then
    emit_alert "warn" "WORKER_RESTART" "Worker restarted due to health checks" "${CHAPTER_JSON}" "${PHASE}" "{\"target\":${TARGET},\"monitor_rc\":${RC}}"
    sleep "${SLEEP_BETWEEN_CYCLES}"
    continue
  fi

  if (( RC == 130 )); then
    break
  fi

  report_worker_log_issues "${WORKER_LOG}" "${CHAPTER_JSON}" "${PHASE}"
  emit_alert "error" "NONZERO_EXIT" "Worker exited non-zero; retrying same target" "${CHAPTER_JSON}" "${PHASE}" "{\"target\":${TARGET},\"exit_code\":${RC}}"
  sleep "${SLEEP_BETWEEN_CYCLES}"
done

emit_alert "info" "SUPERVISOR_STOP" "Supervisor stopped" "null" "" '{}'
log "Supervisor stopped"
