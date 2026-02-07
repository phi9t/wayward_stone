# Changelog

All notable process and infrastructure changes are documented in this file.

## [0.2.0-inkforge-loop] - 2026-02-14

### Added
- `inkforge_loop` orchestration package with checkpointed autonomous chapter pipeline.
- `scripts/inkforge_loop.py` CLI to run/resume generation until a target chapter.
- Structured run-root layout under `inkforge/<run_id>/` with manuscript/plans/logs/state/artifacts.
- Unit + offline integration tests for loop state machine, quality gates, and resume behavior.
- Opt-in runtime smoke tests for agent CLI availability and loop command surface.

### Changed
- `README.md` and `RELEASE.md` now document autonomous loop invocation and validation.

### Scope Notes
- Loop role mapping defaults: OpenCode writer, Claude critic, Codex reviser.
- Narrative content quality remains governed by existing writer/critic/pipeline skill constraints.

## [0.1.1-process-polish] - 2026-02-14

### Added
- `pytest` test suite with unit, offline integration, and opt-in runtime integration coverage.
- Shared Python helper module `audiobook/tts_utils.py` for chapter discovery and TTS output normalization.

### Changed
- `audiobook/run_audiobook_zephyr.sh` now supports `--help` and `--dry-run`.
- `audiobook/run_book_batch_zephyr.sh` keeps side-effect-free dry-run behavior for generic directory runs.
- `audiobook/render_book_zephyr.py` imports heavy runtime deps lazily and uses shared helpers.
- `scripts/release_preflight.sh` now validates single-chapter wrapper help and dry-run paths.

### Scope Notes
- Changes are focused on technical process code (`audiobook/` and `scripts/`) and testing.
- Narrative chapter prose remains out-of-scope.
