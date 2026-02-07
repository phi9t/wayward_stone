# Zephyr Container Infra Deep Dive (Audiobook)

This note documents the generic audiobook runtime path on Zephyr.

## 1) Runtime model

- Host runs wrapper scripts under `audiobook/`.
- Wrapper builds a thin image (`Dockerfile.zephyr-gpu`) on top of Zephyr snapshot base.
- Workload runs inside container via `zephyr_launch_container.sh`.
- Synthesis runs with Spack-backed torch/jax and guarded uv installs.

## 2) Entrypoints

- Single chapter: `audiobook/run_audiobook_zephyr.sh`
- Directory batch: `audiobook/run_book_batch_zephyr.sh`
- Container launcher: `audiobook/zephyr_launch_container.sh`
- uv guard: `audiobook/zephyr_uv_guard_install.sh`
- Provenance check: `audiobook/verify_zephyr_spack_provenance.sh`

## 3) Generic batch command

```bash
AUDIOBOOK_USE_GPU=1 ./audiobook/run_book_batch_zephyr.sh -- \
  --source-dir /workspace/wayward_stone/manuscript \
  --out-dir /workspace/wayward_stone/outputs/book_audio
```

Default outputs:
- `<out-dir>/chapters/chXXX.wav`
- `<out-dir>/chunks/chXXX/chunk_XXXXX.wav`
- `<out-dir>/audiobook_all_chapters.wav`
- `<out-dir>/manifest.json`

## 4) Package policy

Only install runtime Python packages via:

```bash
bash /opt/audiobook/zephyr_uv_guard_install.sh <pkg> [pkg...]
```

Guard behavior:
- Blocks uv-installed CUDA/NVIDIA wheel families.
- Leaves Spack torch/jax untouched.
- Falls back to a compatible `torchaudio` only when missing from Spack.

## 5) Provenance validation

```bash
./audiobook/verify_zephyr_spack_provenance.sh
```

This must report that torch and jax resolve from the Spack prefix.
