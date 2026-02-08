---
name: wayward-stone-writer
description: Draft/revise Wayward Stone chapters with strict register rules, canon discipline (CLAUDE.md), and continuity management across novel-gen run roots.
---

# Wayward Stone Writer

Use this skill when the user asks to draft, rewrite, revise, or plan chapters in this repository.

## Run-root model (novel-gen)

- Treat each manuscript subspace as its own novel-gen run root.
- Known run roots in this repo: `gpt53/`, `kimi25/`, `kimi25_blend/`.
- Any new directory that contains chapter files is also a valid run root.
- Never merge continuities across run roots unless the user explicitly requests a sync/port.

## Target selection (`RUN_ROOT`)

1. If the user names a run root/path, use it.
2. Else prefer known run roots that contain chapters.
3. Else discover any directory with chapter files and select the most recently active one.
4. If still ambiguous, ask the user.

## Sources of truth (in order)

1. Repo rules: `AGENTS.md`
2. Voice rubric: `writing_style.md`
3. Project canon: `CLAUDE.md`
4. `RUN_ROOT` continuity + plans (discover in this order):
   - continuity log (for example, `plans/continuity_log.md`)
   - story bible (for example, `story_bible.md`)
   - act map and nearest chapter-plan docs in the same `RUN_ROOT`

## Hard invariants

- Chapters 001–002 only: Waystone frame (3rd-limited) plus told story (1st-person).
- Chapters 003+: told-past only (1st-person). No present-day interludes or frame cast on-page.
- Headings + filenames must follow the active run root's established chapter convention.

## Workflow (default)

1. Read the previous chapter (and the relevant plan doc).
2. Skim `RUN_ROOT` continuity artifacts for locks you must not contradict.
3. Draft for scene turns first; revise for rhythm/voice second; canon pass last.
4. After landing the chapter, update continuity artifacts only inside `RUN_ROOT`.

## Reference

Read `references/wayward_stone_writer.md` for templates, checklists, and the “Rothfuss-style rewrite pass” guidance.
