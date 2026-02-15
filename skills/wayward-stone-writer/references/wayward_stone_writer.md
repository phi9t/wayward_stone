# Wayward Stone Writer (Reference)

Drafting guide for run-specific workspaces with Rothfuss-style craft.

## 1) Identify Your Run

Runs live under `inkforge/<run-id>/`:

```bash
# List existing runs
ls -la inkforge/

# Current active runs:
# - inkforge/run-target-030/    (production, 6 chapters)
# - inkforge/baseline/          (experiment)
# - inkforge/experimental/      (experiment)
```

Each run maintains:
- Independent manuscript state
- Isolated continuity constraints
- Separate quality metrics

## 2) Parallel Experiments

Test different creative approaches simultaneously:

```bash
# Conservative approach
python scripts/inkforge_loop.py run --run-id conservative --target-chapter 5

# Experimental approach
python scripts/inkforge_loop.py run --run-id experimental --target-chapter 5

# Compare results:
# - inkforge/conservative/manuscript/chapter_001.md
# - inkforge/experimental/manuscript/chapter_001.md
```

## 3) Non-Negotiables

- **Ch001–002**: Frame + told story mix
- **Ch003+**: Told-past only; no frame cast on-page
- **Naming**: Experiential, never mechanistic rules
- **Chandrian/Amyr**: Mystery preserved; hints only

Register check (Ch003+):
```bash
rg -n "Chronicler|Bast|Kote|Waystone|Reshi|Newarre" \
  inkforge/<run-id>/chapter_00[3-9]*.md
```

## 4) Drafting Loop

### Context Pass
1. Read immediately prior chapter
2. Read plan doc: `inkforge/<run-id>/plans/chapter_NNN-NNN.md`
3. Check continuity locks in `plans/continuity_log.md`

### Plan Template

```markdown
**Chapter XXX — Title**

**Goal**: One sentence (what changes by the end).

**Scenes**:
- Scene A: [location] (conflict turn + sensory anchor)
- Scene B: [location] (conflict turn + sensory anchor)
- Scene C: [location] (conflict turn + sensory anchor)

**Motifs**: (pick 1–2 from silence, wind, doors, names, music)

**Continuity Locks**:
- [existing constraint to preserve]
- [new constraint this chapter introduces]

**End Hook**: (tightened constraint or forced tradeoff, not cliffhanger)
```

### Draft Scene-by-Scene

Aim for clean turns:
- Each scene changes something
- Exposition emerges under pressure
- No scene exists for information delivery alone

## 5) Rothfuss-Style Pass

### Cut Interpretation

❌ "I realized she was afraid."
✅ "Her hand found the edge of the table and did not let go."

### Dialogue as Evasion Game

Structure every significant exchange:
1. **Question** (direct, puts pressure)
2. **Deflection** (evasive, maintains guard)
3. **Pressure** (specific, narrows field)
4. **Accidental Truth** (reluctant, partial revelation)
5. **Exit** (before full resolution)

### Competence Balance

Kvothe should be wrong or corrected:
- ❌ "Kvothe explained the mechanism perfectly"
- ✅ "'That's not how sympathy works,' Kilvin said. 'The binding would slip.'"

### Habit + Interruption

1. Establish physical habit in calm scene (tapping, adjusting, smoothing)
2. Break it under pressure (hand stills, forgets habit)
3. Restore only when tension releases (or don't restore)

### End Scenes Early

Exit on:
- Silence that stretches
- Physical exit (door, walk away)
- Unanswered final line
- Realization dawning (not stated)

Never on:
- Summary of what happened
- Emotional interpretation
- "And then they decided..."

## 6) Canon Pass

| Source Type | Treatment |
|-------------|-----------|
| Published canon (explicit) | State plainly |
| Published canon (implied) | Keep implied ("it seemed...") |
| CLAUDE.md canon | May expand if supported |
| Project-invented | Must have on-page precedent |

## 7) Continuity Updates

After landing chapter:

1. **Add to continuity_log.md**:
   ```markdown
   - Chapter XXX: [key fact established] [constraint introduced]
   ```

2. **Update next plan** if spine shifted

3. **Check motifs**:
   ```bash
   rg "silence|wind|doors|names|music" \
     -n inkforge/<run-id>/manuscript/chapter_*.md
   ```

## 8) Useful Commands

```bash
# Check word count
wc -w inkforge/<run-id>/manuscript/chapter_*.md

# Validate chapter naming
ls inkforge/<run-id>/manuscript/chapter_*.md | sort -V

# Find motif usage
rg "silence|wind|doors|names|music" \
  -n inkforge/<run-id>/manuscript/chapter_*.md

# Check register violations (Ch003+)
rg -n "Chronicler|Bast|Kote|Waystone|Reshi|Newarre" \
  inkforge/<run-id>/chapter_00[3-9]*.md

# Next chapter number
ls inkforge/<run-id>/manuscript/chapter_*.md | sort -V | tail -n 1
```
