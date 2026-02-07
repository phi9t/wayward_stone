# AGENTS.md — Wayward Stone

Repository guidelines for agentic coding assistants working on this Kingkiller Chronicle fan continuation.

## Project Overview

This is a prose project: a fan-continuation of Patrick Rothfuss's *The Kingkiller Chronicle* set on "Day Three" at the Waystone Inn. See `CLAUDE.md` for canon constraints and `writing_style.md` for voice/rhythm evaluation criteria.

## Build/Test Commands

This repository has no build system. Useful ad-hoc commands:

```bash
# Find references/motifs across chapters
rg "silence|wind|doors|names" -n chapter_*.md

# Quick word count for all chapters
wc -w chapter_*.md

# Check for frame narrative terms in told-past chapters (Ch. 3+)
rg -n "Chronicler|Bast|Kote|Waystone|Reshi|Newarre" chapter_00[3-9]*.md chapter_01*.md

# Validate chapter naming consistency
ls chapter_*.md | sort -V

# Check for audiobook generation
./audiobook/run_audiobook_zephyr.sh --help
```

## File Organization

- `chapter_XXX_<short_snake_case_title>.md` — Main manuscript chapters (three-digit numbers)
- `CLAUDE.md` — Canon bible and world-building reference
- `writing_style.md` — Prose style rubric (10 evaluation criteria)
- `audiobook/` — TTS generation scripts and Zephyr container infrastructure
- `outputs/` — Generated artifacts (audio, PDFs, etc.)

## Writing Conventions

### File Naming
- Pattern: `chapter_XXX_<short_snake_case_title>.md`
- Three-digit chapter numbers with leading zeros
- Example: `chapter_001_the_weight_of_the_third_day.md`

### Document Structure
- Start each chapter with `# Chapter X — Title`
- Use `---` for scene breaks (sparingly)
- Frame narrative (Ch. 1–2): third-person limited, observing Kote
- Told story (Ch. 3+): first-person Kvothe narrating

### Formatting
- Use Markdown italics for emphasis: `*word*`
- Keep paragraphs as primary pacing units
- Avoid excessive bold; let rhythm carry weight
- Use scene breaks only when time/location shifts significantly

## Style Guidelines

### Voice Requirements
- **Frame narrative**: Spare, melancholic, measured. External observation only.
- **Told past**: Vivid, energetic, occasionally grandiose. Kvothe's personality colors everything.
- If you can swap a frame paragraph with a told-past paragraph unnoticed, the voices aren't distinct enough.

### Dialogue Rules
- Each speaker must be identifiable without attribution tags
- **Kvothe (told)**: Articulate, showy, academic vocabulary, self-aware wit
- **Kote (frame)**: Measured, neutral, publican's professional voice
- **Bast**: Mercurial, "Reshi," affectionate and threatening simultaneously
- **Chronicler**: Precise, practical, careful neutrality
- **Elodin**: Scattered surface, profound undercurrent, performs private theater

### Prose Quality Checklist (from writing_style.md)

1. **Sentence Musicality** — Read aloud; if it stumbles, rewrite
2. **Metaphor Precision** — Vivid, unexpected, sensorily grounded; no clichés
3. **Dual Register** — Frame and told-past voices must be distinct
4. **Emotional Restraint** — Frame emotions through action, not stated internal monologue
5. **Dialogue as Character** — Identifiable without tags
6. **Sensory Grounding** — Abstract concepts anchored in physical detail
7. **Pacing Through Detail** — Expand important moments, compress transitions
8. **Thematic Motif Consistency** — Silence, wind, doors, names, music carry cumulative meaning
9. **Unreliable Narrator** — Kvothe's ego and blind spots shape the telling
10. **Ending Impact** — Each chapter closes on a resonant line

### Canon Compliance Requirements

Before committing new chapters, verify:

- **Sympathy**: Alar, bindings, slippage, energy conservation respected
- **Naming**: Hard-won, not casual; sleeping mind concept maintained
- **Magic costs**: Physical toll, exhaustion, unpredictability
- **The Fae**: Time dilation, iron vulnerability, moon connection
- **The Chandrian**: Seven signs, Haliax leads, Cinder is cruel
- **The Amyr**: "Ivare Enim Euge," secretive, information suppressed
- **Geography**: Four Corners locations consistent (University, Severen, Ademre, etc.)
- **Frame narrative**: Day Three structure, Kvothe tells to Chronicler

## Audiobook Generation

When generating TTS for chapters:

```bash
# Run provenance check before synthesis
./audiobook/verify_zephyr_spack_provenance.sh

# Single chapter
./audiobook/run_audiobook_zephyr.sh chapter_001.md outputs/ch001.wav

# Batch generation
./audiobook/run_book_batch_zephyr.sh -- \
  --source-dir manuscript/ \
  --out-dir outputs/book_audio/
```

**Constraints**:
- Use Spack snapshot base image (`sygaldry/zephyr:spack`)
- Install runtime deps only through `zephyr_uv_guard_install.sh`
- Do not allow `.venv_audio` to override Spack packages
- Do not allow `uv` to install `nvidia-*` or `cuda*` wheels
- If `torchaudio` issues occur, rebuild `.venv_audio` and verify version pin

**Voice target**: Warm, youthful, clear, conversational. Lyrical in reflection, brisk in action. Subtle character separation without caricature accents.

## Commits & Pull Requests

Prefer small, focused commits with imperative subjects:

- `Add Chapter 04 draft`
- `Tighten frame voice in Chapter 02`
- `Fix canon violation: correct Master name`

PRs should include:
- Short summary of changes
- Note any canon-sensitive changes (names/lineage/locations)
- Call out intentional divergences from writing_style.md
- Verify against CLAUDE.md for continuity

## Common Pitfalls to Avoid

- Over-explaining Naming mechanics (keep it ineffable)
- Making Bast too human or too alien (he oscillates)
- Giving Kote too much internal monologue (frame is observed externally)
- Modern idiom in dialogue (no contractions or contemporary slang)
- Breaking told-past voice with omniscience (Kvothe can only report what he experienced)
- Purple prose without narrative purpose (beauty must serve story)

## Review Checklist

Before submitting changes:

- [ ] Read key passages aloud (rhythm check)
- [ ] Verify dialogue identifiable without tags
- [ ] Check magic/world details are sensory, not expository
- [ ] Confirm continuity with CLAUDE.md (names, places, rules)
- [ ] Validate file naming follows convention
- [ ] Ensure frame/told-past register distinction is clear
