from __future__ import annotations

from pathlib import Path

import pytest

from inkforge_loop.chapter_index import (
    chapter_filename,
    discover_chapter_files,
    highest_chapter_number,
    next_chapter_number,
)


@pytest.mark.unit
def test_discover_and_next_chapter(tmp_path: Path) -> None:
    (tmp_path / "chapter_002_second.md").write_text("x", encoding="utf-8")
    (tmp_path / "chapter_010_tenth.md").write_text("x", encoding="utf-8")
    (tmp_path / "chapter_bad.md").write_text("x", encoding="utf-8")

    found = discover_chapter_files(tmp_path)
    assert [n for n, _ in found] == [2, 10]
    assert highest_chapter_number(tmp_path) == 10
    assert next_chapter_number(tmp_path) == 11


@pytest.mark.unit
def test_chapter_filename_slugifies() -> None:
    name = chapter_filename(3, "A Door, A Name!")
    assert name == "chapter_003_a_door_a_name.md"
