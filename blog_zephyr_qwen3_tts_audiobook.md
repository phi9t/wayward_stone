# Multi-Agent Fiction Generation: Architecture of an AI Writing Pipeline

## Abstract

A production pipeline generating ~40k words of long-form fiction using a state-machine-based multi-agent system with quality gates, resumable state, and GPU-orchestrated audio synthesis. The system treats creative generation as a deterministic workflow while preserving authorial intent through structured critique loops.

## System Architecture

### 1. The State Machine Model

The core abstraction is a deterministic state machine per chapter:

```
PLAN → WRITE → CRITIQUE → (REVISE → RECRITIQUE)* → PASS → DONE
```

This design enables three critical properties:

**Checkpoint/Resume**: State is persisted atomically at each transition. Interruptions are recoverable from the last completed state boundary.

**Deterministic Quality Gates**: Chapters cannot advance until explicit criteria are met, preventing "good enough" prose from contaminating downstream continuity.

**Clear Failure Modes**: After 20 revision loops without passing, the system restarts with a fresh draft rather than continuing to iterate on a broken foundation.

### 2. Multi-Agent Orchestration

Three specialized agents with distinct prompt strategies and output schemas:

| Agent | Tool | Role | Output Schema |
|-------|------|------|---------------|
| Writer | opencode | Initial draft | `{title, text, notes}` |
| Critic | Claude (sonnet) | Structured critique | `{violations[], score, fixes[]}` |
| Reviser | Codex (gpt-5) | Fix application | `{revised_text, changes[]}` |

**The Adapter Layer** (`adapters.py`) handles the messy reality of LLM outputs:
- Multi-format JSON extraction (fenced code blocks, inline JSON, trailing objects)
- Graceful degradation on malformed responses
- Deep text recovery from nested structures
- Retry logic with exponential backoff

This abstraction allows the core engine to assume structured data while the adapter manages vendor-specific response patterns.

### 3. Quality Gates

Pass/fail logic is deterministic and strict:

```python
passed = (
    not invariant_violations and
    overall_score >= 9.0 and
    all(category_scores >= 8.0)
)
```

**Invariants** include:
- Register lock (frame vs. told-past chapters)
- Canon discipline (explicit vs. implied facts)
- Continuity constraints (location, injuries, possessions)

The 9.0/8.0 thresholds are intentionally high—this is a gate, not a suggestion.

### 4. State Persistence

Resumable JSON state files with atomic writes:

```python
RunState: {
    run_id: str,
    target_chapter: int,
    current_chapter: int,
    completed_chapters: list[int],
    total_failures: int,
    phase: str  # enum of state machine phases
}

ChapterState: {
    chapter_number: int,
    phase: str,
    revision_count: int,
    restart_count: int,
    filename: str,
    passed: bool
}
```

Atomic writes (temp file + rename) prevent corruption on interruption. The state machine can resume from any checkpoint without data loss.

### 5. Parallel Experiment Support

Multiple run roots enable A/B testing of creative approaches:

```
inkforge/
├── baseline/           # Conservative approach
├── experimental/       # Aggressive style shifts
└── production/         # Current best
```

Each run maintains isolated:
- Manuscript state (`manuscript/`)
- Continuity logs (`plans/continuity_log.md`)
- Quality metrics (`artifacts/critic/`)
- Resumable checkpoints (`state/`)

This structure supports parallel exploration without cross-contamination.

### 6. Audio Synthesis Pipeline

GPU orchestration via file-based leasing:

**Lease Mechanics** (`zephyr_gpu_lease.sh`):
- Acquire: Poll for available GPU with timeout (default 6hr)
- Preferred ordering: `--preferred-gpus 1,0` for topology-aware selection
- Garbage collection: Clean stale leases from dead PIDs
- Concurrent jobs: Different `--run-id` namespaces

**Provenance** (`verify_zephyr_spack_provenance.sh`):
- Verify `torch` and `jax` resolve from Spack store
- Fail fast on unexpected package origins
- Ensure reproducible runtime environment

**Chunk-Based Synthesis**:
- Sentence-aware text segmentation
- Immediate per-chunk persistence
- Deterministic merge invariants
- Resumable from first missing chunk

## Key Engineering Decisions

### Why State Machines Over DAGs?

DAG-based orchestrators (Airflow, Prefect) optimize for task dependencies. State machines optimize for:
- Human-in-the-loop intervention
- Explicit quality decision points
- Clear resume semantics
- Simplicity of implementation

When the bottleneck is creative judgment rather than compute, explicit state transitions are preferable to implicit task graphs.

### Why Multi-Model?

Different models excel at different cognitive tasks:
- **Sonnet**: Nuanced critique with structured JSON output
- **GPT-5**: Surgical revision with context preservation
- **Opencode**: Long-form generation with skill integration

The marginal cost of model switching is negligible compared to the quality gains from task-specialized prompting.

### Why File-Based State?

- **Human inspectable**: JSON is readable and diffable
- **Git-friendly**: Version control of creative iterations
- **No database dependency**: Simpler deployment, easier debugging
- **Language-agnostic**: Any tool can read/write state

The tradeoff is scalability—this architecture targets individual authors, not thousand-user deployments.

### Why GPU Leasing?

File-based locks provide:
- Explicit resource ownership
- Timeout and cleanup semantics
- Visibility into contention
- Simple implementation (no external coordination service)

For multi-hour synthesis jobs, explicit lease management is preferable to implicit queue-based scheduling.

## Results

- **6 chapters** generated (~40k words)
- **Quality gate**: 9.0/10 threshold maintained across all passing chapters
- **Resumability**: Survived interruptions without data loss
- **Audio**: ~5 hours synthesized with chunk-level recovery
- **Parallel runs**: 3 concurrent experiments (baseline, experimental, production)

## Implementation

```bash
# Clone and run
python scripts/inkforge_loop.py run --run-id my-book --target-chapter 5

# Or with full GPU-accelerated audiobook pipeline:
AUDIOBOOK_USE_GPU=1 ./audiobook/run_book_batch_zephyr.sh -- \
  --source-dir inkforge/my-book/manuscript \
  --out-dir outputs/my-book-audio
```

github.com/anomalyco/wayward-stone

## Lessons

1. **Quality gates are load-bearing**: Treat them as invariant checks, not scoring suggestions.
2. **State machines simplify debugging**: When a chapter fails, the current state unambiguously identifies the problem phase.
3. **Parallel experiments multiply learning**: A/B testing creative approaches is as valuable as iteration within a single approach.
4. **File-based state is underrated**: For creative workflows, inspectable and versioned state beats database performance.
5. **Chunk-level persistence matters**: For multi-hour synthesis jobs, resume granularity determines operational feasibility.
