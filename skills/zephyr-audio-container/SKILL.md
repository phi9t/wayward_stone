---
name: zephyr-audio-container
description: Use the Zephyr launcher and Spack snapshot image to build/run Wayward Stone audiobook containers with GPU mounts, strict uv guardrails, and Torch/JAX provenance verification. Use when tasks mention Zephyr container infra, Spack snapshot base images, uv package policy, or validating torch/jax origins.
---

# Zephyr Audio Container

Use this skill for infrastructure tasks around audiobook containers in this repo.

## Preconditions

- Zephyr launcher exists at `audiobook/zephyr_launch_container.sh` (default) or via `ZEPHYR_LAUNCHER` override.
- Snapshot image exists (default `sygaldry/zephyr:spack`).
- Run from repo root.
-- Host-shared cache env vars (default to `/mnt/data_infra/zephyr_container_infra/sygaldry/` paths):
  - `ZEPHYR_SHARED_HF_CACHE` (default `.../hf_cache`)
  - `ZEPHYR_SHARED_UV_CACHE` (default `.../bazel_cache/uv_cache`)

## Standard Workflow

1) Build Zephyr-based audio image:

```bash
./audiobook/run_audiobook_zephyr.sh chapter_01_the_weight_of_the_third_day.md outputs/ch01.wav --dry-run
```

2) Verify Spack provenance for `torch` and `jax`:

```bash
./audiobook/verify_zephyr_spack_provenance.sh
```

3) Enforce uv policy before adding packages:

```bash
SYGALDRY_IMAGE=wayward-stone-audio-zephyr:gpu \
  ./audiobook/zephyr_launch_container.sh \
  --repo . \
  --entrypoint run-job -- \
  bash -lc "cd /workspace/$(basename \"$PWD\") && bash /opt/audiobook/zephyr_uv_guard_install.sh <package>"
```

4) Run kimi25 chapter synthesis with auto GPU lease:

```bash
AUDIOBOOK_USE_GPU=1 ./audiobook/run_kimi25_batch_zephyr.sh
```

The runner acquires a free GPU automatically using `audiobook/zephyr_gpu_lease.sh`.
If all GPUs are busy, it waits (polling) until one is free or timeout is hit.

## Policy Rules

- Zephyr container infra is GPU-only (`AUDIOBOOK_USE_GPU=1`).
- Never install with uv if package already exists in Spack.
- Never install CUDA-related packages with uv (`nvidia-*` forbidden; other CUDA stacks are blocked too).
- Always run model jobs through Zephyr launcher (`run-job` entrypoint).
- For concurrent jobs, use GPU leasing + run-scoped output roots.

## Useful Environment Variables

- `AUDIOBOOK_USE_GPU=1` (required; CPU mode is not supported).
- `ZEPHYR_SNAPSHOT_BASE=sygaldry/zephyr:spack`.
- `ZEPHYR_SNAPSHOT_DIGEST=sha256:...` to pin exact base.
- `AUDIOBOOK_SKIP_BUILD=1` to reuse existing image.
- `AUDIOBOOK_RUN_ID=<id>` to make output/project naming explicit.
- `AUDIOBOOK_PREFERRED_GPUS=1,0` preferred GPU order.
- `AUDIOBOOK_GPU_TIMEOUT_SECONDS=21600` max wait for free GPU lease.
- `AUDIOBOOK_GPU_POLL_SECONDS=15` polling interval for lease retries.
- `AUDIOBOOK_GPU_LOCK_DIR=outputs/.gpu_leases` lease lock root.
-- `ZEPHYR_SHARED_HF_CACHE=/host/path/hf_cache` (optional override; defaults to `/mnt/data_infra/zephyr_container_infra/sygaldry/hf_cache`).
-- `ZEPHYR_SHARED_UV_CACHE=/host/path/uv_cache` (optional override; defaults to `/mnt/data_infra/zephyr_container_infra/sygaldry/bazel_cache/uv_cache`).

## GPU Lease Operations

Inspect current lease state:

```bash
./audiobook/zephyr_gpu_lease.sh status --verbose
```

Garbage-collect stale leases (dead PID owner):

```bash
./audiobook/zephyr_gpu_lease.sh gc --verbose
```

## Concurrency Discipline

- Launching multiple audio jobs concurrently is supported.
- Each run should keep a unique `SYGALDRY_PROJECT_ID` (the wrapper sets one by default from run id).
- The wrapper writes outputs under run-specific roots (`outputs/kimi25/runs/<run_id>/...`) to avoid collisions.
