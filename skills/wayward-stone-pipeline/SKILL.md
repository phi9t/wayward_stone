---
name: wayward-stone-pipeline
description: Run autonomous write → critique → revise loops for Wayward Stone chapters with quality gates and resumable state.
---

# Wayward Stone Pipeline

End-to-end chapter generation with automated quality enforcement.

## Usage

```bash
# Basic run
python scripts/inkforge_loop.py run --run-id my-book --target-chapter 5

# With resume (after interruption)
python scripts/inkforge_loop.py run --run-id my-book --target-chapter 5 --resume

# Custom quality thresholds
python scripts/inkforge_loop.py run \
  --run-id my-book \
  --target-chapter 10 \
  --quality-overall-min 9.0 \
  --quality-category-min 8.0
```

## Workspace Structure

```
inkforge/<run-id>/
├── manuscript/          # Chapter files (chapter_XXX_title.md)
├── plans/              # Outlines and continuity_log.md
├── state/              # run_state.json, chapter_XXX_state.json
├── logs/               # events.jsonl
└── artifacts/          # critic/, revision/
    ├── critic/chapter_XXX_review.json
    └── revision/chapter_XXX_rev_NN.json
```

## Parallel Experiments

Run multiple experiments simultaneously:

```bash
# Terminal 1
python scripts/inkforge_loop.py run --run-id baseline --target-chapter 5

# Terminal 2
python scripts/inkforge_loop.py run --run-id experimental --target-chapter 5

# Compare: inkforge/baseline/manuscript/ vs inkforge/experimental/manuscript/
```

Each run maintains independent state and continuity.

## State Machine

```
PLAN → WRITE → CRITIQUE → (REVISE → RECRITIQUE)* → PASS → DONE
```

- **PLAN**: Create outline if missing
- **WRITE**: Initial draft via writer agent
- **CRITIQUE**: Structured review via critic agent
- **REVISE**: Fix application via reviser agent
- **PASS**: Chapter meets quality gate

## Pass Criteria

A chapter passes only when:

- **No invariant violations** (register/canon/continuity)
- **Overall score ≥ 9.0** (default)
- **All category scores ≥ 8.0** (default)

Categories evaluated against `writing_style.md` criteria.

## Revision Cap

If a chapter fails after 20 revise+re-critique loops:
- Full restart with fresh draft
- Continuity constraints preserved
- Failure count tracked in run state

## Resumability

State is persisted atomically (JSON files). Resume any time:

```bash
# Continue from last checkpoint
python scripts/inkforge_loop.py run --run-id my-book --target-chapter 5 --resume
```

State includes:
- Current chapter and phase
- Completed chapters list
- Revision/restart counts per chapter
- Total failure count

## CLI Options

```
--workspace-root inkforge    # Root for all runs
--run-id <id>                # Run identifier
--target-chapter <n>         # Stop at chapter N
--max-revision-loops 20      # Restart after N revisions
--max-total-failures 200     # Abort run after N failures
--quality-overall-min 9.0    # Pass threshold
--quality-category-min 8.0   # Per-category threshold
--writer-agent writer        # OpenCode agent id
--critic-model sonnet        # Claude model alias
--reviser-model gpt-5        # Codex model
--resume                     # Continue existing run
```

## Reference

Read `references/wayward_stone_pipeline.md` for detailed procedures and failure handling.
