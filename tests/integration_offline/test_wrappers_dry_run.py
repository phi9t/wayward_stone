from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


def run(repo_root: Path, args: list[str], extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        args,
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.integration_offline
def test_run_audiobook_help(repo_root: Path) -> None:
    proc = run(repo_root, ["./audiobook/run_audiobook_zephyr.sh", "--help"])
    assert proc.returncode == 0
    assert "Usage:" in proc.stdout


@pytest.mark.integration_offline
def test_run_audiobook_dry_run_has_no_build_side_effect(repo_root: Path) -> None:
    proc = run(
        repo_root,
        [
            "./audiobook/run_audiobook_zephyr.sh",
            "--dry-run",
            "README.md",
            "outputs/test_dry_run.wav",
        ],
        extra_env={"AUDIOBOOK_USE_GPU": "1", "AUDIOBOOK_SKIP_BUILD": "0"},
    )
    assert proc.returncode == 0, proc.stderr
    assert "DRY RUN: single chapter synthesis wrapper" in proc.stdout
    assert "Building Zephyr audio image" not in proc.stdout


@pytest.mark.integration_offline
def test_run_book_batch_dry_run_has_no_build_side_effect(repo_root: Path) -> None:
    proc = run(
        repo_root,
        ["./audiobook/run_book_batch_zephyr.sh", "--dry-run"],
        extra_env={"AUDIOBOOK_USE_GPU": "1", "AUDIOBOOK_SKIP_BUILD": "0"},
    )
    assert proc.returncode == 0, proc.stderr
    assert "DRY RUN: generic book batch synthesis wrapper" in proc.stdout
    assert "Building Zephyr audio image" not in proc.stdout


@pytest.mark.integration_offline
def test_run_book_batch_help_passthrough(repo_root: Path) -> None:
    proc = run(
        repo_root,
        ["./audiobook/run_book_batch_zephyr.sh", "--dry-run", "--", "--help"],
        extra_env={"AUDIOBOOK_USE_GPU": "1", "AUDIOBOOK_SKIP_BUILD": "0"},
    )
    assert proc.returncode == 0, proc.stderr
    assert "resolved_cmd=" in proc.stdout
    assert "--help" in proc.stdout


@pytest.mark.integration_offline
def test_publish_script_help_and_dry_run(repo_root: Path) -> None:
    help_proc = run(repo_root, ["./scripts/publish_audiobooks.sh", "--help"])
    assert help_proc.returncode == 0
    assert "Usage:" in help_proc.stdout

    dry_proc = run(repo_root, ["./scripts/publish_audiobooks.sh", "--dry-run"])
    assert dry_proc.returncode == 0
    assert "Dry-run complete" in dry_proc.stdout


@pytest.mark.integration_offline
def test_publish_script_rejects_unknown_argument(repo_root: Path) -> None:
    proc = run(repo_root, ["./scripts/publish_audiobooks.sh", "--bad-flag"])
    assert proc.returncode != 0
    assert "Unknown argument" in proc.stderr
