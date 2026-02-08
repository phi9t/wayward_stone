# Wayward Stone Pipeline (Reference)

This is the strict, repeatable “keep writing the book” loop.

Known run roots: `gpt53/`, `kimi25/`, `kimi25_blend/`.
Also accept any new directory with chapter files as a run root.

## Inputs to read every chapter (`RUN_ROOT`)

- Repo rules: `AGENTS.md`
- Voice rubric: `writing_style.md`
- Project canon: `CLAUDE.md`
- Continuity locks in `RUN_ROOT` (continuity log or story bible)
- Planning spine in `RUN_ROOT` (act map + nearest chapter-plan docs)

Do not mix continuity artifacts across run roots unless explicitly requested.

## Find the next chapter to write (`RUN_ROOT`)

1. Determine the highest existing chapter file:
   - `ls <RUN_ROOT>/chapter_*.md | sort -V | tail -n 1`
2. Use the nearest plan doc to choose the next chapter number/title:
   - `ls <RUN_ROOT>/plans/chapter_*.md <RUN_ROOT>/plan_chapters_*.md 2>/dev/null | sort -V | tail -n 1`

## Per-chapter pipeline (strict)

For each chapter:

1. **Plan**
   - Produce a plan using the writer template (Goal, scenes, motifs, continuity locks, end hook).
2. **Draft**
   - Write the full chapter draft.
3. **Critique**
   - Use `wayward-stone-critic` output format.
   - If scoring is enabled, score against `writing_style.md` and justify #7 with micro+macro pacing.
4. **Revise**
   - Apply fix-first issues first (invariants/canon/continuity), then voice/rhythm, then line-level polish.
5. **Re-critique**
   - Repeat critique and re-score (if enabled).
6. **Loop**
   - Repeat steps 4–5 until pass criteria are met.

## Revision cap handling (20 loops)

- If 20 loops fail, do a full restart:
  - re-plan from scratch
  - write a fresh draft that uses a new scene engine (not a re-skin of the same beats)
  - resume critique/revise loop

## Required updates after a passing chapter (`RUN_ROOT`)

- Append continuity locks to `RUN_ROOT` continuity artifact (chapter-keyed bullets).
- Update the relevant run-root plan doc if the draft changes the near-term spine.
- If the repo uses a chapter list in `CLAUDE.md` for “Existing chapters”, update it.

## Sanity checks (recommended)

- Motif search for accidental repetition:
  - `rg "silence|wind|doors|names" -n <RUN_ROOT>/chapter_*.md`
- Register enforcement (Ch003+):
  - `rg -n "Chronicler|Bast|Kote|Waystone|Reshi|Newarre" <RUN_ROOT>/chapter_00[3-9]*.md <RUN_ROOT>/chapter_01*.md`
