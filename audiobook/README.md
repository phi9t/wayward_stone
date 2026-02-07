# Qwen3-TTS Audiobook on Zephyr (Hermetic Repo Launcher)

Primary workflow uses repo-local Zephyr launcher behavior plus snapshot-based audiobook images.

## 1) Required environment

Shared cache defaults (can be overridden):

```bash
# optional override
export ZEPHYR_SHARED_HF_CACHE=/path/on/host/hf_cache
export ZEPHYR_SHARED_UV_CACHE=/path/on/host/uv_cache
```

Defaults point at the original Zephyr infra caches under `/mnt/data_infra/zephyr_container_infra/sygaldry/`.
Notes:
- Zephyr infra is GPU-only.
- Launcher defaults to `audiobook/zephyr_launch_container.sh`.
- Runtime state is repo-local under `outputs/zephyr_infra/<project_id>/`.
- Spack runtime is baked into snapshot/image lineage; no host Spack mount.

## 2) Snapshot/image policy

- Base snapshot default: `sygaldry/zephyr:spack`
- Optional digest pin:

```bash
export ZEPHYR_SNAPSHOT_BASE=sygaldry/zephyr:spack
export ZEPHYR_SNAPSHOT_DIGEST=sha256:...
```

Wrappers build a small audiobook image layer on top of snapshot (`Dockerfile.zephyr-gpu`).

## 3) Single chapter synthesis

```bash
AUDIOBOOK_USE_GPU=1 \
./audiobook/run_audiobook_zephyr.sh chapter_001_example.md outputs/ch001.wav
```

Optional tuning:

```bash
AUDIOBOOK_USE_GPU=1 \
./audiobook/run_audiobook_zephyr.sh chapter_002_example.md outputs/ch002.wav \
  --speaker Ryan --language English --max-chars 380
```

## 4) Generic batch synthesis

Render a directory of chapters to per-chapter WAV files plus merged full-book WAV:

```bash
AUDIOBOOK_USE_GPU=1 \
./audiobook/run_book_batch_zephyr.sh -- \
  --source-dir /workspace/wayward_stone/manuscript \
  --out-dir /workspace/wayward_stone/outputs/book_audio
```

Dry-run and CLI help:

```bash
./audiobook/run_book_batch_zephyr.sh --help
AUDIOBOOK_USE_GPU=1 ./audiobook/run_book_batch_zephyr.sh --dry-run
AUDIOBOOK_USE_GPU=1 ./audiobook/run_book_batch_zephyr.sh -- --help
```

## 5) Resume behavior

- Chunks are stored under `<out-dir>/chunks` by default.
- Existing chunks are reused automatically.
- Use `--force` to regenerate chunks.
- Use `--no-merge` to skip full-book merge output.

## 6) Release preflight

```bash
./scripts/release_preflight.sh
```

## 7) uv package policy in container

Use only:

```bash
bash /opt/audiobook/zephyr_uv_guard_install.sh <pkg> [pkg...]
```

Policy summary:
- Spack-provided packages are excluded from uv installs.
- CUDA/NVIDIA wheel families are excluded.
- `torch` and `jax` must remain Spack-sourced.
- If missing from Spack, `torchaudio` is pinned to Spack torch version.

## 8) Verify provenance

```bash
./audiobook/verify_zephyr_spack_provenance.sh
```

Check fails if `sys.base_prefix`, `torch`, or `jax` resolve outside `/opt/spack_store/`.
