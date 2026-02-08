---
name: wayward-stone-pipeline
description: Run an autonomous write → critic → revise loop for Wayward Stone chapters within a selected novel-gen run root until pass criteria are met; then advance to the next chapter.
---

# Wayward Stone Pipeline

Use this skill when the user wants an end-to-end loop that continues a manuscript: draft a chapter, critique it, revise, re-critique, and repeat until it passes; then move on.

## Run-root model (novel-gen)

- Known run roots: `gpt53/`, `kimi25/`, `kimi25_blend/`.
- Any new directory with chapter files is a valid run root.
- Run the entire pipeline in one `RUN_ROOT` at a time.

## Target selection (`RUN_ROOT`)

1. If user specifies a run root/path, use it.
2. Else prefer known run roots that contain chapters.
3. Else auto-detect the most recently active run root.
4. If ambiguous, ask the user.

## Pass criteria

A chapter “passes” only if:

- No invariant violations (register/canon/continuity).
- Critic score target is met (when scoring is requested):
  - Overall >= 9.0 / 10, and
  - No category < 8.0 / 10.

## Revision cap

- If the chapter still fails after 20 revise+re-critique loops, restart with a fresh draft.

## Reference

Read `references/wayward_stone_pipeline.md` for the exact per-chapter procedure and required post-pass updates.
