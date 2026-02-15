---
name: wayward-stone-audiobook
description: Generate audiobooks from Wayward Stone chapters using Zephyr containers with GPU leasing, Spack provenance, and resumable chunk-based synthesis.
---

# Wayward Stone Audiobook

Generate long-form audiobooks with deterministic synthesis and GPU orchestration.

## Prerequisites

- Docker with NVIDIA runtime
- `AUDIOBOOK_USE_GPU=1` environment variable
- Zephyr container infra (see `audiobook/zephyr_container_infra_deep_dive.md` for details)

## Quick Start

### Single Chapter

```bash
AUDIOBOOK_USE_GPU=1 \
./audiobook/run_audiobook_zephyr.sh \
  inkforge/my-book/manuscript/chapter_001.md \
  outputs/ch01.wav
```

### Batch Generation

```bash
AUDIOBOOK_USE_GPU=1 ./audiobook/run_book_batch_zephyr.sh -- \
  --source-dir inkforge/my-book/manuscript \
  --out-dir outputs/my-book-audio
```

### Verify Provenance (Required Before Long Runs)

```bash
./audiobook/verify_zephyr_spack_provenance.sh
```

## GPU Leasing

For concurrent audiobook generation across multiple runs:

### Acquire GPU

```bash
GPU_INDEX=$(./audiobook/zephyr_gpu_lease.sh acquire --verbose)
echo "Acquired GPU $GPU_INDEX"
```

### Release GPU

```bash
./audiobook/zephyr_gpu_lease.sh release --gpu-index $GPU_INDEX
```

### Check Status

```bash
./audiobook/zephyr_gpu_lease.sh status --verbose
./audiobook/zephyr_gpu_lease.sh gc --verbose  # Clean stale leases
```

### Lease Options

- `--preferred-gpus 1,0` - Preferred GPU order
- `--timeout-seconds 21600` - Max wait (6hr default)
- `--poll-seconds 15` - Polling interval
- `--job-id <id>` - Logical job identifier

## Parallel Run Support

Generate audiobooks for multiple experiments simultaneously:

```bash
# Terminal 1 - Baseline run
AUDIOBOOK_USE_GPU=1 ./audiobook/run_book_batch_zephyr.sh -- \
  --source-dir inkforge/baseline/manuscript \
  --out-dir outputs/baseline-audio

# Terminal 2 - Experimental run (different GPU via lease)
GPU_INDEX=$(./audiobook/zephyr_gpu_lease.sh acquire)
AUDIOBOOK_USE_GPU=1 ./audiobook/run_book_batch_zephyr.sh -- \
  --source-dir inkforge/experimental/manuscript \
  --out-dir outputs/experimental-audio
```

## Environment Variables

- `AUDIOBOOK_USE_GPU=1` - Required for GPU mode
- `ZEPHYR_SNAPSHOT_BASE=sygaldry/zephyr:spack` - Base image
- `ZEPHYR_SNAPSHOT_DIGEST=sha256:...` - Pin exact digest
- `ZEPHYR_SHARED_HF_CACHE` - HuggingFace cache (default: `/mnt/data_infra/zephyr_container_infra/sygaldry/hf_cache`)
- `ZEPHYR_SHARED_UV_CACHE` - UV cache (default: `/mnt/data_infra/zephyr_container_infra/sygaldry/bazel_cache/uv_cache`)
- `AUDIOBOOK_SKIP_BUILD=1` - Reuse existing image
- `AUDIOBOOK_RUN_ID=<id>` - Explicit run naming
- `AUDIOBOOK_PREFERRED_GPUS=1,0` - GPU preference order

## Resumable Synthesis

Chunks are persisted immediately. If interrupted:

```bash
# Re-run same command - existing chunks are reused
AUDIOBOOK_USE_GPU=1 ./audiobook/run_audiobook_zephyr.sh chapter.md output.wav

# Force regeneration
AUDIOBOOK_USE_GPU=1 ./audiobook/run_audiobook_zephyr.sh chapter.md output.wav --force
```

## Package Policy

Install only through guard script:

```bash
bash /opt/audiobook/zephyr_uv_guard_install.sh <package>
```

Rules:
- Spack packages excluded from UV installs
- CUDA/NVIDIA wheels forbidden
- torch/jax must remain Spack-sourced

## Troubleshooting

- **Provenance failure**: Check image/tag or non-Spack Python
- **Forbidden package**: Verify UV constraints
- **Torchaudio errors**: Rebuild `.venv_audio`, match Spack torch version
