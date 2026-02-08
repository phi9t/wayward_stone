---
name: zephyr-qwen3-tts-runs
description: Run qwen3-tts audiobook jobs in Wayward Stone through Zephyr container infra, including single-chapter synthesis, kimi25 batch synthesis, resumable chunk handling, and dry-run diagnostics.
---

# Zephyr Qwen3-TTS Runs

Use this skill for actual qwen3-tts synthesis runs in this repo.

Zephyr container infra is GPU-only. Use `AUDIOBOOK_USE_GPU=1`.
Set shared cache env vars before runs (defaults exist under `/mnt/data_infra/zephyr_container_infra/sygaldry/`):
- `ZEPHYR_SHARED_HF_CACHE`
- `ZEPHYR_SHARED_UV_CACHE`

## Single Chapter

```bash
./audiobook/run_audiobook_zephyr.sh chapter_01_the_weight_of_the_third_day.md outputs/ch01.wav
```

Optional:

```bash
AUDIOBOOK_USE_GPU=1 \
./audiobook/run_audiobook_zephyr.sh chapter_02_what_the_door_conceals.md outputs/ch02.wav \
  --speaker Ryan --language English --max-chars 380
```

## Batch Kimi25

```bash
AUDIOBOOK_USE_GPU=1 ./audiobook/run_kimi25_batch_zephyr.sh
```

## Dry-Run Planning

```bash
./audiobook/run_audiobook_zephyr.sh chapter_03_the_name_beneath_the_name.md outputs/ch03.wav --dry-run
```

## Run Discipline

- Keep input/output files inside this repo (wrappers mount repo at `/workspace/<repo_name>`).
- Let wrappers choose chunk dirs by default for resumable runs.
- If package changes are needed, use `/opt/audiobook/zephyr_uv_guard_install.sh`; do not bypass it.
- Verify provenance with `./audiobook/verify_zephyr_spack_provenance.sh` before long runs.
