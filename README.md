# Wayward Stone: AI-Assisted Fiction Writing

Collaborative fiction writing with automated critique loops that enforce continuity and style.

> **⚠️ Research Prototype Notice**
>
> This is a research prototype for generating *one specific book* (Wayward Stone).
> It is **not a framework** and not intended for general-purpose use without
> modification. Think of it as a hackable foundation—a minimalist starting point
> showing how to build creative writing pipelines with agent orchestration.
> Fork it, strip it, adapt it to your own project.

## Quick Start

```bash
# Write 5 chapters
python scripts/inkforge_loop.py run --run-id my-book --target-chapter 5

# Chapters appear in: inkforge/my-book/manuscript/

# Generate audiobook (requires GPU)
AUDIOBOOK_USE_GPU=1 ./audiobook/run_audiobook_zephyr.sh \
  inkforge/my-book/manuscript/chapter_001.md outputs/ch01.wav
```

## How It Works

State machine per chapter: **Plan → Write → Critique → Revise → Pass**

- **Continuity tracking**: Automatic in `plans/continuity_log.md`
- **Quality gate**: Score ≥9.0 overall, ≥8.0 per category
- **Resumable**: Stop anytime, restart with `--resume`

## Parallel Experiments

Run multiple versions simultaneously:

```bash
python scripts/inkforge_loop.py run --run-id baseline --target-chapter 5
python scripts/inkforge_loop.py run --run-id experimental --target-chapter 5
```

## Prerequisites

- Python 3.9+, opencode agent
- Docker + NVIDIA GPU (audiobooks only)

## File Structure

```
inkforge/<run-id>/
├── manuscript/     # Chapters (chapter_XXX_title.md)
├── plans/         # Outlines, continuity
├── state/         # Checkpoints
└── artifacts/     # Reviews and revisions
```

## Documentation

- `CLAUDE.md` - Canon bible (world-building rules)
- `writing_style.md` - Voice and style rubric
- `AGENTS.md` - Contributor guidelines
- `skills/` - Agent capabilities (writer, critic, pipeline, audiobook)

## Testing

```bash
pytest                    # Unit and offline integration tests
pytest -m unit           # Unit tests only
pytest -m integration_offline  # Offline integration tests
```

## Skills

Available agent skills:

- `wayward-stone-writer` - Draft chapters with canon discipline
- `wayward-stone-critic` - Structured critique with quality gates
- `wayward-stone-pipeline` - Autonomous write-critique-revise loops
- `wayward-stone-audiobook` - GPU-orchestrated audio synthesis
- `wayward-stone-book-pdf` - Book-quality PDF generation
