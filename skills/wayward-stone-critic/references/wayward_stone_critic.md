# Wayward Stone Critic (Reference)

This reference merges strict invariants, macro pacing checks, and scene-craft diagnostics while avoiding brittle "facts" that should instead be verified against `CLAUDE.md`.

Runs live under `inkforge/<run-id>/`. Any new directory with chapter files under `inkforge/` is also valid.

## 1) Review workflow (4 passes)

1. **Register + structure**
   - Identify chapter number.
   - Enforce register lock (frame vs told-past).
2. **Story pass**
   - What changed by the end? (1 sentence.)
   - Where are the scene turns? Are they earned?
3. **Voice + craft pass**
   - Musicality, metaphor precision, dialogue identity, motif layering.
   - Subtext/evasion, habit+interruption characterization, scenes ending early.
4. **Canon + continuity pass**
   - Contradictions vs published canon (explicit).
   - Contradictions vs `CLAUDE.md`.
   - Contradictions vs target run-root continuity locks.
   - “Hardened inference” flags.

## 2) Hard invariants

- Ch001–002: frame + told.
- Ch003+: told-past only; frame cast must not appear on-page.
- Naming should stay experiential; avoid new mechanics/rules.
- Chandrian/Amyr: avoid definitive explanations; keep menace and mystery intact.

Register check (Ch003+):
```bash
rg -n "Chronicler|Bast|Kote|Waystone|Reshi|Newarre" \
  inkforge/<run-id>/manuscript/chapter_00[3-9]*.md \
  inkforge/<run-id>/manuscript/chapter_01*.md
```

## 3) What to flag (high signal)

### A) Canon discipline
- Sympathy that “just works” without energy/cost/failure modes.
- Naming treated like a learnable spell list or a clean technique.
- Fae treated as ordinary; iron/time strangeness ignored when relevant.
- Definitive lore dumps about Chandrian/Amyr (especially new “closed systems”).
- Any specific “facts” that aren’t anchored in published canon or `CLAUDE.md`.

### B) Continuity
- A fact changes without on-page explanation (location, injuries, possessions, relationships).
- A promise/constraint is introduced and then forgotten for multiple chapters.
- A thread repeats without transformation (same refusal beat, same label beat).

### C) Voice + rhythm
- Modern idiom/slang that breaks setting.
- Exposition that explains the point of the scene.
- Metaphors that are pretty but non-specific (no sensory anchor).
- Dialogue where everyone says what they mean.

## 4) Rothfuss-style craft diagnostics (quick)

- **Never explain the point of the scene:** cut interpretation lines.
- **Dialogue as evasion game:** question → deflection → pressure → accidental truth.
- **Competence balance:** Kvothe gets corrected; others “win” quietly.
- **Humor under stress:** jokes as defense, not comfort.
- **Habit + interruption:** establish a repeating physical habit, then break it under pressure.
- **Scenes end early:** exit on silence/leave/unanswered line, not on resolution.

## 5) Pacing & Momentum (required section)

### Micro pacing
- Are important beats slowed down with detail?
- Are transitions compressed?
- Do we linger on the *right* sensory anchors (not generic atmosphere)?

### Macro momentum
Use these detectors:
- **Label treadmill:** consecutive chapters where the “turn” is just a new label/notice.
- **Constraint treadmill:** repeated refusal/defiance beats without forcing a tradeoff.

Repair toolkit:
- Compress multiple label/notice beats into one scene/chapter.
- Convert refusal into a forced tradeoff with cost.
- Add an engine shift every ~4–5 chapters (music/lecture/friendship rupture/research break-in).
- Vary endings so they land on different emotional chords.

## 6) Output format (copy/paste template)

```markdown
## Chapter X — Title

### Verdict
**APPROVED / REVISION REQUIRED / REJECTED**

### Top Issues (Fix First)
- [Issue] (why it matters) -> [concrete fix]

### Voice & Rhythm
- [musicality/register/dialogue identity/motifs]

### Pacing & Momentum
- Macro turn: [1 sentence: what changed by the end]
- Repetition risks: [treadmills]
- Compress/expand: [what to cut vs slow down]
- Next-chapter pacing target: [1–2 directives]

### Canon & Continuity
- [explicit contradiction vs canon]
- [contradiction vs `CLAUDE.md`]
- [continuity lock breaks]
- [inference stated as fact]

### Stakes & Plausibility
- [motivation/consequence/cost/timing]

### Line-Level Notes
- Quote short fragments only; point to paragraph/beat.
```

## 7) Optional scoring (if user wants numbers)

If scoring is requested, score against `writing_style.md` criteria with 0–10 per item, and explicitly justify criterion #7 with **both micro and macro** pacing notes.
