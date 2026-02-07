#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  zephyr_gpu_lease.sh acquire [options]
  zephyr_gpu_lease.sh release --gpu-index <idx> [options]
  zephyr_gpu_lease.sh status [options]
  zephyr_gpu_lease.sh gc [options]

Options:
  --lock-dir <path>           Lease root directory (default: outputs/.gpu_leases)
  --job-id <id>               Logical job id for metadata
  --project-id <id>           Zephyr project id for metadata
  --owner-pid <pid>           Stable owner PID recorded in lease metadata
  --preferred-gpus <csv>      Preferred GPU indexes (example: 1,0)
  --timeout-seconds <n>       Max wait to acquire a GPU (default: 21600)
  --poll-seconds <n>          Poll interval while waiting (default: 15)
  --verbose                   Print extra logs to stderr

Acquire output:
  Prints selected GPU index to stdout.
USAGE
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(realpath "${SCRIPT_DIR}/..")"

LOCK_DIR_DEFAULT="${REPO_ROOT}/outputs/.gpu_leases"
LOCK_DIR="${LOCK_DIR_DEFAULT}"
JOB_ID="${JOB_ID:-}"
PROJECT_ID="${PROJECT_ID:-}"
OWNER_PID="${OWNER_PID:-}"
PREFERRED_GPUS="${PREFERRED_GPUS:-}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-21600}"
POLL_SECONDS="${POLL_SECONDS:-15}"
VERBOSE=0

log() {
  if [[ "${VERBOSE}" -eq 1 ]]; then
    echo "[gpu-lease] $*" >&2
  fi
}

err() {
  echo "[gpu-lease] ERROR: $*" >&2
}

ensure_nvidia_smi() {
  if ! command -v nvidia-smi >/dev/null 2>&1; then
    err "nvidia-smi not found in PATH"
    exit 1
  fi
}

parse_common_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --lock-dir)
        LOCK_DIR="$2"
        shift 2
        ;;
      --job-id)
        JOB_ID="$2"
        shift 2
        ;;
      --project-id)
        PROJECT_ID="$2"
        shift 2
        ;;
      --preferred-gpus)
        PREFERRED_GPUS="$2"
        shift 2
        ;;
      --owner-pid)
        OWNER_PID="$2"
        shift 2
        ;;
      --timeout-seconds)
        TIMEOUT_SECONDS="$2"
        shift 2
        ;;
      --poll-seconds)
        POLL_SECONDS="$2"
        shift 2
        ;;
      --verbose)
        VERBOSE=1
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        err "Unknown argument: $1"
        usage
        exit 2
        ;;
    esac
  done
}

pid_starttime() {
  local pid="$1"
  local stat_path="/proc/${pid}/stat"
  if [[ ! -r "${stat_path}" ]]; then
    return 1
  fi
  awk '{print $22}' "${stat_path}" 2>/dev/null
}

pid_alive_with_starttime() {
  local pid="$1"
  local expected_start="$2"
  if [[ -z "${pid}" ]] || [[ -z "${expected_start}" ]]; then
    return 1
  fi
  if ! kill -0 "${pid}" 2>/dev/null; then
    return 1
  fi
  local actual_start
  actual_start="$(pid_starttime "${pid}" || true)"
  [[ -n "${actual_start}" && "${actual_start}" == "${expected_start}" ]]
}

gpu_indexes() {
  nvidia-smi --query-gpu=index --format=csv,noheader,nounits | tr -d ' ' | sed '/^$/d'
}

gpu_uuid_to_index_map() {
  nvidia-smi --query-gpu=index,uuid --format=csv,noheader,nounits | sed '/^$/d'
}

busy_gpus() {
  local map
  map="$(gpu_uuid_to_index_map)"
  local compute_rows
  compute_rows="$(nvidia-smi --query-compute-apps=gpu_uuid,pid --format=csv,noheader,nounits 2>/dev/null || true)"
  if [[ -z "${compute_rows}" ]]; then
    return 0
  fi
  while IFS= read -r row; do
    local gpu_uuid pid
    gpu_uuid="$(echo "${row}" | cut -d',' -f1 | tr -d ' ')"
    pid="$(echo "${row}" | cut -d',' -f2 | tr -d ' ')"
    [[ -z "${gpu_uuid}" || -z "${pid}" ]] && continue
    local idx
    idx="$(echo "${map}" | awk -F',' -v u="${gpu_uuid}" '
      {
        gsub(/^[ \t]+|[ \t]+$/, "", $1);
        gsub(/^[ \t]+|[ \t]+$/, "", $2);
        if ($2 == u) print $1;
      }' | head -n1)"
    [[ -n "${idx}" ]] && echo "${idx}"
  done < <(printf '%s\n' "${compute_rows}")
}

lease_path_for_gpu() {
  local idx="$1"
  echo "${LOCK_DIR}/gpu${idx}.lock"
}

write_lease_metadata() {
  local idx="$1"
  local lease_path
  lease_path="$(lease_path_for_gpu "${idx}")"
  local owner_pid="${OWNER_PID:-$$}"
  local owner_start
  owner_start="$(pid_starttime "${owner_pid}" || true)"
  local now_iso
  now_iso="$(date -Is)"
  cat > "${lease_path}/meta.env" <<EOF
GPU_INDEX=${idx}
OWNER_PID=${owner_pid}
OWNER_STARTTIME=${owner_start}
JOB_ID=${JOB_ID}
PROJECT_ID=${PROJECT_ID}
HOSTNAME=$(hostname)
ACQUIRED_AT=${now_iso}
EOF
}

read_meta_value() {
  local file="$1"
  local key="$2"
  awk -F'=' -v k="${key}" '$1 == k {print substr($0, index($0, "=") + 1)}' "${file}" 2>/dev/null | head -n1
}

remove_stale_lock_if_needed() {
  local idx="$1"
  local lease_path
  lease_path="$(lease_path_for_gpu "${idx}")"
  local meta="${lease_path}/meta.env"
  if [[ ! -d "${lease_path}" ]]; then
    return 0
  fi
  if [[ ! -f "${meta}" ]]; then
    log "Removing malformed lease for GPU ${idx} (missing meta)"
    rm -rf "${lease_path}"
    return 0
  fi
  local pid starttime
  pid="$(read_meta_value "${meta}" "OWNER_PID")"
  starttime="$(read_meta_value "${meta}" "OWNER_STARTTIME")"
  if pid_alive_with_starttime "${pid}" "${starttime}"; then
    return 1
  fi
  log "GC stale lease for GPU ${idx} (pid=${pid}, start=${starttime})"
  rm -rf "${lease_path}"
  return 0
}

acquire_gpu() {
  ensure_nvidia_smi
  mkdir -p "${LOCK_DIR}"
  local start_epoch
  start_epoch="$(date +%s)"

  local -a preferred=()
  if [[ -n "${PREFERRED_GPUS}" ]]; then
    IFS=',' read -r -a preferred <<< "${PREFERRED_GPUS}"
  fi

  while true; do
    local -a all_gpus=()
    mapfile -t all_gpus < <(gpu_indexes)
    if [[ "${#all_gpus[@]}" -eq 0 ]]; then
      err "No GPUs found via nvidia-smi"
      exit 1
    fi

    local -a ordered=()
    if [[ "${#preferred[@]}" -gt 0 ]]; then
      for idx in "${preferred[@]}"; do
        for g in "${all_gpus[@]}"; do
          if [[ "${idx}" == "${g}" ]]; then
            ordered+=("${g}")
          fi
        done
      done
      for g in "${all_gpus[@]}"; do
        local seen=0
        for o in "${ordered[@]}"; do
          if [[ "${o}" == "${g}" ]]; then
            seen=1
            break
          fi
        done
        [[ "${seen}" -eq 0 ]] && ordered+=("${g}")
      done
    else
      ordered=("${all_gpus[@]}")
    fi

    local -A busy=()
    while IFS= read -r idx; do
      [[ -n "${idx}" ]] && busy["${idx}"]=1
    done < <(busy_gpus | sort -u)

    for idx in "${ordered[@]}"; do
      if [[ -n "${busy[${idx}]:-}" ]]; then
        log "GPU ${idx} busy by active compute process"
        continue
      fi
      remove_stale_lock_if_needed "${idx}" || true
      local lease_path
      lease_path="$(lease_path_for_gpu "${idx}")"
      if mkdir "${lease_path}" 2>/dev/null; then
        write_lease_metadata "${idx}"
        log "Acquired GPU ${idx}"
        echo "${idx}"
        return 0
      fi
    done

    local now_epoch
    now_epoch="$(date +%s)"
    local elapsed=$((now_epoch - start_epoch))
    if (( elapsed >= TIMEOUT_SECONDS )); then
      err "Timed out after ${TIMEOUT_SECONDS}s waiting for a free GPU"
      return 3
    fi
    log "No free GPU, waiting ${POLL_SECONDS}s (elapsed=${elapsed}s)"
    sleep "${POLL_SECONDS}"
  done
}

release_gpu() {
  local gpu_index=""
  local owner_pid=""
  local force_release=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --gpu-index)
        gpu_index="$2"
        shift 2
        ;;
      --owner-pid)
        owner_pid="$2"
        shift 2
        ;;
      --force)
        force_release=1
        shift
        ;;
      --lock-dir|--verbose|-h|--help)
        break
        ;;
      *)
        err "Unknown argument for release: $1"
        usage
        exit 2
        ;;
    esac
  done
  parse_common_args "$@"

  if [[ -z "${gpu_index}" ]]; then
    err "release requires --gpu-index"
    exit 2
  fi

  local lease_path
  lease_path="$(lease_path_for_gpu "${gpu_index}")"
  local meta="${lease_path}/meta.env"
  if [[ ! -d "${lease_path}" ]]; then
    return 0
  fi

  if [[ -f "${meta}" ]]; then
    local pid starttime expected_start
    pid="$(read_meta_value "${meta}" "OWNER_PID")"
    starttime="$(read_meta_value "${meta}" "OWNER_STARTTIME")"
    if [[ -n "${owner_pid}" && "${force_release}" -ne 1 ]]; then
      expected_start="$(pid_starttime "${owner_pid}" || true)"
      if [[ "${pid}" != "${owner_pid}" || "${starttime}" != "${expected_start}" ]]; then
        log "Owner mismatch for gpu=${gpu_index}; skipping release"
        return 0
      fi
    fi
  fi

  rm -rf "${lease_path}"
  log "Released GPU ${gpu_index}"
}

status_leases() {
  parse_common_args "$@"
  ensure_nvidia_smi
  mkdir -p "${LOCK_DIR}"
  local -A busy=()
  while IFS= read -r idx; do
    [[ -n "${idx}" ]] && busy["${idx}"]=1
  done < <(busy_gpus | sort -u)

  while IFS= read -r idx; do
    local lease_path meta owner_pid owner_start job_id project_id state
    lease_path="$(lease_path_for_gpu "${idx}")"
    meta="${lease_path}/meta.env"
    owner_pid=""
    owner_start=""
    job_id=""
    project_id=""
    state="free"
    if [[ -d "${lease_path}" && -f "${meta}" ]]; then
      owner_pid="$(read_meta_value "${meta}" "OWNER_PID")"
      owner_start="$(read_meta_value "${meta}" "OWNER_STARTTIME")"
      job_id="$(read_meta_value "${meta}" "JOB_ID")"
      project_id="$(read_meta_value "${meta}" "PROJECT_ID")"
      if pid_alive_with_starttime "${owner_pid}" "${owner_start}"; then
        state="leased"
      else
        state="stale"
      fi
    elif [[ -d "${lease_path}" ]]; then
      state="stale"
    fi

    local busy_txt="no"
    [[ -n "${busy[${idx}]:-}" ]] && busy_txt="yes"
    echo "gpu=${idx} busy=${busy_txt} lease_state=${state} owner_pid=${owner_pid:-none} job_id=${job_id:-none} project_id=${project_id:-none}"
  done < <(gpu_indexes)
}

gc_stale() {
  parse_common_args "$@"
  ensure_nvidia_smi
  mkdir -p "${LOCK_DIR}"
  while IFS= read -r idx; do
    remove_stale_lock_if_needed "${idx}" || true
  done < <(gpu_indexes)
}

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

cmd="$1"
shift

case "${cmd}" in
  acquire)
    parse_common_args "$@"
    acquire_gpu
    ;;
  release)
    release_gpu "$@"
    ;;
  status)
    status_leases "$@"
    ;;
  gc)
    gc_stale "$@"
    ;;
  -h|--help)
    usage
    ;;
  *)
    err "Unknown subcommand: ${cmd}"
    usage
    exit 2
    ;;
esac
