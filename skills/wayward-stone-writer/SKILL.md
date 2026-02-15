---
name: wayward-stone-writer
description: Draft Wayward Stone chapters in run-specific workspaces with canon discipline and Rothfuss-style scene craft.
---

# Wayward Stone Writer

Draft chapters with register discipline, continuity awareness, and Rothfuss-style prose craft.

## Workspace Model

Workspaces are organized under `inkforge/`:

```
inkforge/<run-id>/
├── manuscript/     # Chapter files
├── plans/         # Outlines and continuity
├── state/         # Resumable checkpoints
└── artifacts/     # Reviews and revisions
```

## Parallel Experiments

Create multiple runs to test different approaches:

```bash
# Baseline approach
python scripts/inkforge_loop.py run --run-id baseline --target-chapter 5

# Experimental approach
python scripts/inkforge_loop.py run --run-id experimental --target-chapter 5
```

Each run maintains isolated state, continuity, and quality metrics.

## Sources of Truth (Priority Order)

1. `AGENTS.md` - Repository rules
2. `writing_style.md` - Voice and rhythm rubric
3. `CLAUDE.md` - Project canon bible
4. Run-specific continuity:
   - `inkforge/<run-id>/plans/continuity_log.md`
   - `inkforge/<run-id>/plans/chapter_XXX-YYY.md`

## Hard Invariants

- **Chapters 001–002**: Frame narrative (3rd-person) + told story (1st-person)
- **Chapters 003+**: Told-past only (1st-person Kvothe). No Chronicler/Bast/Kote on-page.
- **Naming**: Experiential, never mechanistic
- **Chandrian/Amyr**: Hints and consequences only, never definitive explanations

## Workflow

1. **Context Pass**
   - Read previous chapter
   - Check continuity log for locks
   - Review plan doc (create if missing)

2. **Draft**
   - Scene-by-scene with clean turns
   - Keep exposition "under pressure" (dialogue/subtext/choices)

3. **Voice/Rhythm Pass**
   - Read aloud in your head
   - Cut flab, fix cadence

4. **Rothfuss Pass** (see below)

5. **Canon Pass**
   - Published canon: state plainly if explicit
   - Implied canon: keep implied ("it seemed…")
   - Project-invented: must be in CLAUDE.md

6. **Update Continuity**
   - Add chapter-keyed bullets to continuity log
   - Update next plan if spine changed

## Rothfuss-Style Scene Craft

### Core Principles

- **Never explain the point**: Cut interpretation lines ("I realized…", "This meant…")
- **Dialogue as evasion**: Question → deflection → pressure → accidental truth
- **Competence balance**: Kvothe gets corrected; others win quietly
- **Habit + interruption**: Establish physical habit, break it under pressure
- **End scenes early**: Exit on silence/leave/unanswered line

### Dialogue Rhythm

```
Character A asks (direct)
Character B deflects (evasive)
Character A presses (specific)
Character B gives partial truth (reluctant)
[Exit before resolution]
```

### Sensory Anchors

Replace abstract with concrete:
- ❌ "The room was tense"
- ✅ "No one touched their tea"

## Reference

Read `references/wayward_stone_writer.md` for templates, checklists, and chapter planning guidance.
