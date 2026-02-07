# Wayward Stone: Process Release

This repository contains the generation workflow for a long-form fiction + audiobook pipeline.

This release track is **process-first**:
- generation orchestration and runbooks,
- Zephyr container runtime integration,
- TTS synthesis wrappers and provenance checks,
- publication packaging scripts.

Narrative chapter content exists in the repo but is intentionally out-of-scope for this release guide.

## Quickstart

1. Run release preflight:

```bash
./scripts/release_preflight.sh
```

2. Run single-chapter synthesis in Zephyr:

```bash
AUDIOBOOK_USE_GPU=1 \
./audiobook/run_audiobook_zephyr.sh chapter_01_the_weight_of_the_third_day.md outputs/ch01.wav
```

3. Run batch synthesis:

```bash
AUDIOBOOK_USE_GPU=1 ./audiobook/run_book_batch_zephyr.sh -- \
  --source-dir /workspace/wayward_stone/manuscript \
  --out-dir /workspace/wayward_stone/outputs/book_audio
```

4. Verify Spack provenance:

```bash
./audiobook/verify_zephyr_spack_provenance.sh
```

5. Stage publish artifacts:

```bash
./scripts/publish_audiobooks.sh --dry-run
./scripts/publish_audiobooks.sh
```

6. Run autonomous chapter generation loop:

```bash
python scripts/inkforge_loop.py run \
  --workspace-root inkforge \
  --run-id run-001 \
  --target-chapter 50
```

7. Run continuous agent-supervised generation:

```bash
./scripts/supervise_inkforge_agent.sh \
  --run-id run-001 \
  --workspace-root inkforge \
  --target-chapter 3 \
  --supervisor-agent codex
```

## Core Process Docs

- `audiobook/README.md` - Zephyr audiobook workflow
- `audiobook/zephyr_container_infra_deep_dive.md` - runtime and package policy details
- `RELEASE.md` - release checklist and gating criteria
- `blog_zephyr_qwen3_tts_audiobook.md` - engineering deep-dive post

## Inkforge Loop

The orchestration loop writes chapters under a run-scoped root:

```text
inkforge/<run_id>/
  manuscript/
  plans/
  logs/
  state/
  artifacts/
```

Resume an existing run:

```bash
python scripts/inkforge_loop.py run \
  --workspace-root inkforge \
  --run-id run-001 \
  --target-chapter 50 \
  --resume
```

Run continuous supervision (Codex-first launcher, strict health checks):

```bash
./scripts/supervise_inkforge_agent.sh \
  --run-id run-001 \
  --workspace-root inkforge \
  --target-chapter 3 \
  --step 1 \
  --supervisor-agent codex \
  --stale-minutes 15 \
  --poll-seconds 30
```

## CLI Help

```bash
./audiobook/run_audiobook_zephyr.sh --help
./audiobook/run_book_batch_zephyr.sh --help
./scripts/publish_audiobooks.sh --help
./scripts/supervise_inkforge_agent.sh --help
```

## Testing

Install test dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Or run tests without persistent install:

```bash
uv run --with pytest --with numpy pytest
```

Run default suite (unit + offline integration):

```bash
pytest
```

Run runtime integration tests (Docker/NVIDIA/Zephyr required):

```bash
RUN_RUNTIME_INTEGRATION=1 pytest -m runtime
```
