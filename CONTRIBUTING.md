# Contributing to Wayward Stone

Thanks for your interest in contributing! This document covers the basics.

## Getting Started

```bash
# Clone the repo
git clone https://github.com/phi9t/wayward_stone.git
cd wayward_stone

# Install in editable mode with dev dependencies
pip install -e '.[dev]'

# Install pre-commit hooks
pre-commit install
```

## Development Workflow

1. Create a feature branch from `main`.
2. Make your changes.
3. Run `make preflight` to lint, typecheck, and test.
4. Open a pull request against `main`.

## Code Style

- Python: enforced by [Ruff](https://docs.astral.sh/ruff/) (config in `pyproject.toml`).
- Shell: checked by [ShellCheck](https://www.shellcheck.net/).
- Line length limit is **120** characters.
- See `AGENTS.md` for AI-agent-specific coding conventions.

## Testing

```bash
make test          # all non-runtime tests
make test-unit     # unit tests only
make test-offline  # unit + integration-offline tests
```

Runtime tests (Docker/GPU) are opt-in and excluded from CI. Run them locally with:

```bash
pytest -m runtime
```

## Pull Request Guidelines

- Keep PRs focused — one logical change per PR.
- Include tests for new functionality.
- Ensure `make preflight` passes before requesting review.
- Write a clear PR description explaining *why*, not just *what*.

## Reporting Issues

Open an issue on GitHub. Include reproduction steps, expected vs. actual behavior, and relevant logs.
