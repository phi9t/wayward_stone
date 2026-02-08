# Building a Process-First Audiobook Pipeline with qwen3-tts

## Executive Summary

This project shipped an end-to-end generation system that produced:
- many chapter artifacts,
- roughly 40k words of source markdown,
- roughly 5 hours of merged audiobook output.

The important result is not the prose itself. The result is the **process**: a deterministic, resumable, and operator-friendly pipeline that couples writing workflows with long-form TTS synthesis.

## System Boundaries

The implementation is split into two pipelines with a strict contract between them.

1. Creative pipeline
- planning context and constraints,
- chapter drafting,
- human review for consistency,
- iterative state updates.

2. Audio pipeline
- markdown normalization,
- deterministic segmentation,
- per-segment synthesis,
- chapter merge,
- full-book merge.

Handoff rule: only stable, review-approved text enters synthesis.

## Why Contracts Matter

Long-running generation systems fail when they depend on implicit state. This stack uses explicit contracts:
- deterministic file naming,
- stable chapter/segment ordering,
- resumable checkpoints,
- invariant checks before merge.

That design enables restart safety without redoing completed work.

## Runtime Design

The runtime is built around Zephyr container execution:
- launcher: `audiobook/zephyr_launch_container.sh`,
- wrappers: `run_audiobook_zephyr.sh`, `run_book_batch_zephyr.sh`,
- shared host caches for HuggingFace and uv,
- Spack-based runtime provenance checks.

Containerization is used for repeatability, not convenience. It pins toolchain behavior and reduces host drift.

## Package Governance

Package installation inside runs is policy-constrained through:
- `audiobook/zephyr_uv_guard_install.sh`,
- constraints generated from the active Spack environment,
- explicit exclusion of CUDA/NVIDIA wheel families,
- validation that core runtime packages remain Spack-sourced.

Provenance is verified with:

```bash
./audiobook/verify_zephyr_spack_provenance.sh
```

This check fails fast if `torch`/`jax` resolve outside the expected Spack tree.

## Segmentation and Synthesis Mechanics

The TTS path is sentence-aware and bounded:
- text is normalized,
- sentence units are packed up to target thresholds,
- overlong units are controlled-split,
- each segment gets a stable index,
- each successful segment is persisted immediately.

Immediate segment persistence is the core reliability primitive. A multi-hour run becomes recoverable from the first missing artifact instead of restarting from zero.

## Merge Invariants

Chapter and full-book merges are gated by simple invariants:
- complete index coverage,
- deterministic order,
- compatible waveform contracts,
- idempotent output for identical inputs.

This removes ambiguity from post-processing and makes failures diagnosable.

## Operational Controls

Batch wrappers now expose explicit operator surfaces:
- `--help` for interface discovery,
- `--dry-run` for command resolution without side effects.

Example:

```bash
./audiobook/run_book_batch_zephyr.sh --dry-run
```

Publishing is also script-driven:

```bash
./scripts/publish_audiobooks.sh --dry-run
./scripts/publish_audiobooks.sh
```

## Release Discipline

The release path uses a single preflight gate:

```bash
./scripts/release_preflight.sh
```

It validates:
- required tools,
- process docs,
- executable wrappers,
- public script help output,
- dry-run behavior for wrapper and publish scripts.

## Lessons for Agentic Systems

1. Keep generation and operations separate.
A model can produce content; shipping requires contracts, policy, and repeatability.

2. Optimize for restartability before throughput.
Resumable checkpoints are more valuable than raw speed on long jobs.

3. Make interfaces explicit.
`--help` and `--dry-run` are not cosmetic; they reduce operator mistakes.

4. Enforce provenance in code, not in docs.
If runtime source-of-truth matters, fail the run when invariants break.

## Reproduction Appendix

Minimal process commands:

```bash
# Release gate
./scripts/release_preflight.sh

# Single run
AUDIOBOOK_USE_GPU=1 \
./audiobook/run_audiobook_zephyr.sh chapter_01_the_weight_of_the_third_day.md outputs/ch01.wav

# Batch run
AUDIOBOOK_USE_GPU=1 ./audiobook/run_book_batch_zephyr.sh -- \
  --source-dir /workspace/wayward_stone/manuscript \
  --out-dir /workspace/wayward_stone/outputs/book_audio

# Publish staging
./scripts/publish_audiobooks.sh --dry-run
```

The main takeaway: treat long-form multimodel generation as a production system. Contracts, provenance, and operator ergonomics are what make it shippable.
