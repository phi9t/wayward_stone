# Release Procedure (Process-Only)

## Scope Boundary

Release preparation in this document covers generation process assets only:
- Zephyr launch and runtime behavior,
- TTS synthesis wrappers,
- provenance and policy checks,
- publishing/staging scripts,
- operational documentation.

Narrative chapter prose review is excluded.

## Prerequisites

- Docker daemon accessible
- NVIDIA runtime available for Docker
- `rsync`, `bash`, `rg`, `sed`
- Shared cache roots (or defaults):
  - `ZEPHYR_SHARED_HF_CACHE`
  - `ZEPHYR_SHARED_UV_CACHE`

## Preflight Gate

Run:

```bash
./scripts/release_preflight.sh
```

Expected:
- required commands found,
- release docs present,
- wrappers are executable,
- `--help` works for public scripts,
- `--dry-run` works without build/lease side effects.

## Test Gate

1. Default test suite:

```bash
pytest
```

2. Optional runtime integration:

```bash
RUN_RUNTIME_INTEGRATION=1 pytest -m runtime
```

## Runtime Validation

1. Verify provenance:

```bash
./audiobook/verify_zephyr_spack_provenance.sh
```

2. Validate wrapper command resolution without execution:

```bash
./audiobook/run_book_batch_zephyr.sh --dry-run
```

3. Validate publish staging plan:

```bash
./scripts/publish_audiobooks.sh --dry-run
```

4. Validate inkforge loop CLI:

```bash
python scripts/inkforge_loop.py run --help
```

## Publish Staging

When artifacts are ready:

```bash
./scripts/publish_audiobooks.sh
```

Optional custom roots:

```bash
./scripts/publish_audiobooks.sh \
  --pdf-root output/pdf \
  --published-root outputs/published
```

## Release Notes Template

- Summary of process changes
- CLI/interface changes
- Infra/runtime policy changes
- Known limitations
- Operator prerequisites

## Tag Checklist

- [ ] `scripts/release_preflight.sh` passes
- [ ] Provenance check passes
- [ ] Script `--help`/`--dry-run` behavior verified
- [ ] Blog post reviewed for process-first framing
- [ ] Changelog updated
- [ ] Tag + release notes drafted
