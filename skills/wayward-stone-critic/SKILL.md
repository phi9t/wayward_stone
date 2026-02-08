---
name: wayward-stone-critic
description: Critique Wayward Stone chapters for canon discipline, continuity, and Rothfuss-like voice/rhythm across novel-gen run roots; includes a required Pacing & Momentum (micro+macro) section.
---

# Wayward Stone Critic

Use this skill when the user asks for critique/review of one or more chapters in this repository.

## Run-root model (novel-gen)

- Known run roots: `gpt53/`, `kimi25/`, `kimi25_blend/`.
- Any new directory with chapter files is a valid run root.
- Do not critique one run root using another run root's continuity assumptions.

## Target selection (`RUN_ROOT`)

1. If user specifies a run root/path, use it.
2. Else prefer known run roots with chapter files.
3. Else auto-detect the most recently active run root.
4. If ambiguous, ask the user.

## Sources of truth (in order)

1. Published canon: NotW + WMF (treat non-explicit claims as inference)
2. Project canon: `CLAUDE.md`
3. `RUN_ROOT` continuity artifacts (continuity log, story bible, plan docs)
4. Voice rubric: `writing_style.md`
5. Repo rules: `AGENTS.md` + target `*/AGENTS.md`

## Critical invariants

- Chapters 001–002 only: Waystone frame (3rd-limited) plus told story (1st-person).
- Chapters 003+: told-past only; no present-day interludes or frame cast on-page.
- Do not harden inferences into facts (if not explicit, phrase as inference).

## Output requirements

- Prioritize fix-first issues (invariants/canon/continuity before style).
- Include a dedicated **Pacing & Momentum** section covering:
  - Micro pacing (inside scenes)
  - Macro momentum (chapter-to-chapter novelty / escalation shape)

## Reference

Read `references/wayward_stone_critic.md` for the full checklist, scoring guidance, and repair toolkit.
