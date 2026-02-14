from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


def run_cli(repo_root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "audiobook.render_book_zephyr", *args],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.unit
def test_render_book_dry_run_lists_sorted_chapters(repo_root: Path, tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "chapter_010_ten.md").write_text("ten", encoding="utf-8")
    (src / "chapter_002_two.md").write_text("two", encoding="utf-8")

    out_dir = tmp_path / "out"
    proc = run_cli(
        repo_root,
        ["--source-dir", str(src), "--out-dir", str(out_dir), "--dry-run"],
    )

    assert proc.returncode == 0, proc.stderr
    assert "DRY RUN: generic book batch synthesis" in proc.stdout
    assert "chapter_count=2" in proc.stdout
    assert proc.stdout.index("chapter=002") < proc.stdout.index("chapter=010")


@pytest.mark.unit
def test_render_book_dry_run_respects_no_merge(repo_root: Path, tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "chapter_001_one.md").write_text("one", encoding="utf-8")

    proc = run_cli(
        repo_root,
        ["--source-dir", str(src), "--out-dir", str(tmp_path / "out"), "--dry-run", "--no-merge"],
    )

    assert proc.returncode == 0, proc.stderr
    assert "merge_enabled=False" in proc.stdout


@pytest.mark.unit
def test_render_book_fails_when_no_chapters_match(repo_root: Path, tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()

    proc = run_cli(
        repo_root,
        ["--source-dir", str(src), "--out-dir", str(tmp_path / "out"), "--dry-run"],
    )

    assert proc.returncode != 0
    assert "No chapters matched pattern" in proc.stderr
