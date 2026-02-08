# Wayward Stone Writer (Reference)

This reference generalizes prior manuscript-specific workflows into one run-root workflow, while staying anchored to this repo's sources of truth.

## 1) Identify the target run root (`RUN_ROOT`)

Choose exactly one:

- Known novel-gen run roots: `gpt53/`, `kimi25/`, `kimi25_blend/`.
- Also accept any new directory that contains chapter files.
- Use exactly one `RUN_ROOT` per writing task.

Guardrail: do not import invented canon or unresolved threads from one run root into another unless explicitly requested.

## 2) Non-negotiables (register lock)

- **Ch001–002:** frame + told story.
- **Ch003+:** told-past only; do not put Chronicler/Bast/Kote/Waystone on-page.
- **Keep Naming ineffable:** describe sensation/aftermath, not mechanics or “rules”.
- **Keep Chandrian/Amyr unresolved:** hints and consequences are fine; definitive explanations are not.

## 3) Drafting loop (repeatable)

1. **Context pass**
   - Read the immediately prior chapter.
   - Read the plan doc for the chapter you’re writing (or draft a plan first).
   - Check continuity locks inside `RUN_ROOT` (prefer continuity log, then story bible, then chapter-plan docs).
2. **Plan (1 paragraph + bullets)**
   - One-sentence **Goal**: what changes by the end.
   - 2–4 scenes, each with:
     - location + time feel
     - the conflict turn
     - one sensory anchor
   - Choose 1–2 motifs to deepen (don’t decorate).
   - Write an **End Hook** as a tightened constraint/tradeoff, not a random cliff.
3. **Draft**
   - Write scene by scene, aiming for clean turns.
   - Keep exposition “under pressure” (in dialogue/subtext/choices).
4. **Revision passes**
   - **Voice/rhythm pass** (read aloud in your head): cut flab, fix cadence.
   - **Rothfuss pass**: remove interpretation; add subtext; end scenes earlier.
   - **Canon discipline pass**:
     - If it’s explicit in published canon, state it plainly.
     - If it’s only implied, keep it implied (“it seemed…”, “I suspected…”).
     - If it’s project-invented, ensure it is already supported by `CLAUDE.md` + on-page continuity.
5. **Continuity updates (after landing)**
   - Add/adjust continuity locks (chapter-keyed bullets).
   - Update/append the next plan doc in `RUN_ROOT` if your draft changes the near-term spine.

## 4) Useful checks/commands

Motifs:
- `rg "silence|wind|doors|names" -n <RUN_ROOT>/chapter_*.md`

Register enforcement (Ch003+):
- `rg -n "Chronicler|Bast|Kote|Waystone|Reshi|Newarre" <RUN_ROOT>/chapter_00[3-9]*.md <RUN_ROOT>/chapter_01*.md`

Next chapter number:
- `ls <RUN_ROOT>/chapter_*.md | sort -V | tail -n 1`

## 5) Chapter planning template (Ch003+)

```markdown
**Chapter XXX — Title**

**Goal:** One sentence (what changes by the end).

**Scene A:** [place] (conflict turn + sensory anchor)
**Scene B:** [place] (conflict turn + sensory anchor)
**Scene C:** [place] (conflict turn + sensory anchor)

**Motifs:** (pick 1–2)

**Continuity Locks:**
- [existing lock you must preserve]

**End Hook:** (a tightened constraint or forced tradeoff)
```

## 6) Rothfuss-style rewrite pass (quick checklist)

Use `skills/wayward-stone-rothfuss-style` for deeper guidance. In short:

- Cut lines that interpret emotion (“I realized…”, “This meant…”).
- Dialogue rhythm: **question → deflection → pressure → small accidental truth**.
- Give other characters real competence: Kvothe gets corrected.
- End scenes early: on silence, exit, or an unanswered line.
