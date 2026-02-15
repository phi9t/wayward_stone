# AGENTS.md — Wayward Stone

Contributor guidelines for agentic coding assistants.

## Project Overview

AI-assisted fiction writing pipeline with multi-agent orchestration, quality gates, and GPU-accelerated audiobook synthesis.

## Build/Test Commands

```bash
# Run all tests
pytest

# Run single test file
pytest tests/unit/test_inkforge_state_resume.py

# Run specific test
pytest tests/unit/test_inkforge_state_resume.py::test_run_state_round_trip -v

# Unit tests only
pytest -m unit

# Offline integration tests
pytest -m integration_offline

# Check motif usage
rg "silence|wind|doors|names" -n inkforge/*/manuscript/chapter_*.md
```

## Code Style Guidelines (Python)

### Imports
- Start with `from __future__ import annotations`
- Group: stdlib → third-party → local (blank lines between)
- Use absolute imports

### Type Hints
- Full annotations on all functions
- Prefer `list[int]` over `List[int]` (PEP 585)
- Use `Path` from `pathlib`
- Annotate return types (`-> None` for procedures)

### Naming
- `snake_case` for functions/variables/modules
- `PascalCase` for classes/dataclasses
- `SCREAMING_SNAKE_CASE` for module constants
- Private helpers: `_helper_function()`

### Error Handling
- Custom exceptions inherit from `RuntimeError`
- Specific exception types; avoid bare `except:`
- Include context in error messages
- Validate inputs early

### Code Organization
- Single responsibility functions
- Dataclasses for structured data
- Immutable defaults: `field(default_factory=list)`
- Atomic file operations (temp + rename)
- Avoid global state

### Testing
- Use `@pytest.mark.unit` or appropriate marker
- Descriptive names: `test_<scenario>_<expected>`
- Prefer `tmp_path` fixture
- Structure: Arrange → Act → Assert

## File Organization

- `inkforge/<run-id>/` - Run-specific workspaces
  - `manuscript/` - Chapter files
  - `plans/` - Outlines and continuity
  - `state/` - Resumable checkpoints
  - `artifacts/` - Reviews and revisions
- `skills/` - Agent capabilities
- `audiobook/` - TTS synthesis scripts
- `tests/` - Test suite

## Writing Conventions

### File Naming
- Pattern: `chapter_XXX_<snake_case_title>.md`
- Three-digit chapter numbers
- Example: `chapter_001_the_weight_of_the_third_day.md`

### Document Structure
- Start with `# Chapter X — Title`
- Frame narrative (Ch 1-2): third-person limited, observing Kote
- Told story (Ch 3+): first-person Kvothe narrating
- Use `---` for scene breaks (sparingly)
- Markdown italics for emphasis: `*word*`

### Hard Invariants
- **Ch001-002**: Frame + told story mix
- **Ch003+**: Told-past only; no frame cast on-page
- **Naming**: Experiential, never mechanistic rules
- **Chandrian/Amyr**: Hints and consequences only

## Canon Compliance

Before committing chapters, verify:

- **Sympathy**: Alar, bindings, slippage, energy conservation respected
- **Naming**: Hard-won, not casual; sleeping mind maintained
- **Magic costs**: Physical toll, exhaustion, unpredictability
- **The Fae**: Time dilation, iron vulnerability, moon connection
- **The Chandrian**: Seven signs, Haliax leads, Cinder is cruel
- **The Amyr**: "Ivare Enim Euge," secretive, information suppressed
- **Geography**: Four Corners locations consistent
- **Frame narrative**: Day Three structure maintained

## Common Pitfalls

- Over-explaining Naming mechanics (keep it ineffable)
- Making Bast too human or too alien (he oscillates)
- Giving Kote too much internal monologue (frame is observed)
- Modern idiom in dialogue (avoid contractions/contemporary slang)
- Breaking told-past voice with omniscience
- Purple prose without narrative purpose

## Commits

Prefer small, focused commits with imperative subjects:
- `Add Chapter 04 draft`
- `Fix canon violation: correct Master name`
- `Tighten frame voice in Chapter 02`

## Review Checklist

- [ ] Read key passages aloud (rhythm check)
- [ ] Verify dialogue identifiable without tags
- [ ] Check magic details are sensory, not expository
- [ ] Confirm continuity with CLAUDE.md
- [ ] Validate file naming follows convention
- [ ] Ensure frame/told-past register distinction
