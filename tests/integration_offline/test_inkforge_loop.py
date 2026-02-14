from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest


def run_inkforge(repo_root: Path, args: list[str], env_overrides: dict[str, str]) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, **env_overrides}
    return subprocess.run(
        ["python", "scripts/inkforge_loop.py", *args],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.integration_offline
def test_inkforge_single_chapter_pass(repo_root: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "inkforge"
    proc = run_inkforge(
        repo_root,
        [
            "run",
            "--workspace-root",
            str(workspace),
            "--run-id",
            "pass1",
            "--target-chapter",
            "1",
        ],
        {"INKFORGE_AGENT_MODE": "mock", "INKFORGE_MOCK_CRITIC_PATTERN": "pass"},
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    run_root = workspace / "pass1"
    chapter_files = list((run_root / "manuscript").glob("chapter_001_*.md"))
    assert len(chapter_files) == 1
    run_state = json.loads((run_root / "state" / "run_state.json").read_text(encoding="utf-8"))
    assert run_state["phase"] == "DONE"


@pytest.mark.integration_offline
def test_inkforge_revision_then_pass(repo_root: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "inkforge"
    proc = run_inkforge(
        repo_root,
        [
            "run",
            "--workspace-root",
            str(workspace),
            "--run-id",
            "revpass",
            "--target-chapter",
            "1",
            "--max-revision-loops",
            "3",
        ],
        {"INKFORGE_AGENT_MODE": "mock", "INKFORGE_MOCK_CRITIC_PATTERN": "fail,pass"},
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    chapter_state = json.loads((workspace / "revpass" / "state" / "chapter_001_state.json").read_text(encoding="utf-8"))
    assert chapter_state["passed"] is True
    assert chapter_state["revision_count"] >= 1


@pytest.mark.integration_offline
def test_inkforge_restart_after_revision_cap(repo_root: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "inkforge"
    proc = run_inkforge(
        repo_root,
        [
            "run",
            "--workspace-root",
            str(workspace),
            "--run-id",
            "restart1",
            "--target-chapter",
            "1",
            "--max-revision-loops",
            "2",
        ],
        {"INKFORGE_AGENT_MODE": "mock", "INKFORGE_MOCK_CRITIC_PATTERN": "fail,fail,fail,pass"},
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    chapter_state = json.loads((workspace / "restart1" / "state" / "chapter_001_state.json").read_text(encoding="utf-8"))
    assert chapter_state["passed"] is True
    assert chapter_state["restart_count"] >= 1


@pytest.mark.integration_offline
def test_inkforge_resume_mid_chapter(repo_root: Path, tmp_path: Path) -> None:
    workspace = tmp_path / "inkforge"
    run_root = workspace / "resume1"
    (run_root / "manuscript").mkdir(parents=True, exist_ok=True)
    (run_root / "plans").mkdir(parents=True, exist_ok=True)
    (run_root / "state").mkdir(parents=True, exist_ok=True)
    (run_root / "artifacts" / "critic").mkdir(parents=True, exist_ok=True)
    (run_root / "logs").mkdir(parents=True, exist_ok=True)

    (run_root / "manuscript" / "chapter_001_resume.md").write_text("# Chapter 1 — Resume\n\nDraft", encoding="utf-8")
    (run_root / "plans" / "continuity_log.md").write_text("# Continuity Log\n\n", encoding="utf-8")

    (run_root / "state" / "run_state.json").write_text(
        json.dumps(
            {
                "run_id": "resume1",
                "target_chapter": 1,
                "current_chapter": 1,
                "phase": "CHECKPOINT",
                "total_failures": 0,
                "completed_chapters": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (run_root / "state" / "chapter_001_state.json").write_text(
        json.dumps(
            {
                "chapter_number": 1,
                "phase": "RECRITIQUE",
                "revision_count": 1,
                "restart_count": 0,
                "filename": "chapter_001_resume.md",
                "passed": False,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    proc = run_inkforge(
        repo_root,
        [
            "run",
            "--workspace-root",
            str(workspace),
            "--run-id",
            "resume1",
            "--target-chapter",
            "1",
            "--resume",
        ],
        {"INKFORGE_AGENT_MODE": "mock", "INKFORGE_MOCK_CRITIC_PATTERN": "pass"},
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    run_state = json.loads((run_root / "state" / "run_state.json").read_text(encoding="utf-8"))
    assert run_state["phase"] == "DONE"
    chapter_state = json.loads((run_root / "state" / "chapter_001_state.json").read_text(encoding="utf-8"))
    assert chapter_state["passed"] is True
