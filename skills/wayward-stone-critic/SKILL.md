---
name: wayward-stone-critic
description: Critique Wayward Stone chapters for canon discipline, continuity, and Rothfuss-like voice/rhythm across run-specific workspaces; includes required Pacing & Momentum analysis.
---

# Wayward Stone Critic

Structured critique for chapters with Pacing & Momentum requirements.

## Target Selection

Critique chapters within a specific run:

```bash
# Critic reviews are stored in:
# inkforge/<run-id>/artifacts/critic/chapter_XXX_review.json
```

Each run maintains independent continuity constraints. Do not cross-reference between runs unless explicitly requested.

## Sources of Truth (Priority Order)

1. Published canon (NotW + WMF) - treat non-explicit claims as inference
2. `CLAUDE.md` - project canon bible
3. Run-specific continuity:
   - `inkforge/<run-id>/plans/continuity_log.md`
   - `inkforge/<run-id>/plans/chapter_XXX-YYY.md`
4. `writing_style.md` - voice and rhythm rubric
5. `AGENTS.md` - repository rules

## Critical Invariants

- **Chapters 001–002**: Frame (3rd-person) + told story (1st-person)
- **Chapters 003+**: Told-past only; no frame cast on-page
- Do not harden inferences into facts

Register check (Ch003+):
```bash
rg -n "Chronicler|Bast|Kote|Waystone|Reshi|Newarre" \
  inkforge/<run-id>/manuscript/chapter_00[3-9]*.md
```

## Review Workflow (4 Passes)

1. **Register + Structure**
   - Identify chapter number
   - Enforce register lock

2. **Story Pass**
   - What changed by the end? (1 sentence)
   - Where are the scene turns? Are they earned?

3. **Voice + Craft Pass**
   - Musicality, metaphor precision, dialogue identity
   - Subtext/evasion, habit+interruption, early scene exits

4. **Canon + Continuity Pass**
   - Contradictions vs published canon (explicit)
   - Contradictions vs `CLAUDE.md`
   - Contradictions vs run-specific continuity locks

## Output Requirements

Prioritize fix-first issues (invariants/canon/continuity before style).

**Required Section: Pacing & Momentum**

Cover both:
- **Micro pacing**: Inside scenes (detail vs compression)
- **Macro momentum**: Chapter-to-chapter novelty and escalation

## Reference

Read `references/wayward_stone_critic.md` for full checklist, scoring guidance, and repair toolkit.
