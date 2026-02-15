from __future__ import annotations

from pathlib import Path

import pytest

from inkforge_loop.state import (
    load_or_init_chapter_state,
    load_or_init_run_state,
    save_chapter_state,
    save_run_state,
)


@pytest.mark.unit
def test_run_state_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "state" / "run_state.json"
    state = load_or_init_run_state(path, run_id="r1", target_chapter=50)
    state.current_chapter = 7
    state.completed_chapters = [1, 2, 3]
    save_run_state(path, state)

    loaded = load_or_init_run_state(path, run_id="r1", target_chapter=50)
    assert loaded.current_chapter == 7
    assert loaded.completed_chapters == [1, 2, 3]


@pytest.mark.unit
def test_chapter_state_round_trip(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    chapter = load_or_init_chapter_state(state_dir, 4)
    chapter.phase = "REVISE"
    chapter.revision_count = 3
    chapter.filename = "chapter_004_test.md"
    save_chapter_state(state_dir, chapter)

    loaded = load_or_init_chapter_state(state_dir, 4)
    assert loaded.phase == "REVISE"
    assert loaded.revision_count == 3
    assert loaded.filename == "chapter_004_test.md"
