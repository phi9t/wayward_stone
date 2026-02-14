from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from audiobook.tts_utils import (
    chapter_manifest_lines,
    discover_chapters,
    normalize_tts_batch_output,
)


@pytest.mark.unit
def test_discover_chapters_sorts_numeric_ids(tmp_path: Path) -> None:
    (tmp_path / "chapter_010_ten.md").write_text("x", encoding="utf-8")
    (tmp_path / "chapter_002_two.md").write_text("x", encoding="utf-8")
    (tmp_path / "chapter_099.md").write_text("x", encoding="utf-8")
    (tmp_path / "chapter_bad.md").write_text("x", encoding="utf-8")

    chapters = discover_chapters(tmp_path)

    assert [num for num, _ in chapters] == [2, 10, 99]


@pytest.mark.unit
def test_chapter_manifest_lines_uses_zero_padded_ids(tmp_path: Path) -> None:
    chapters = [(3, tmp_path / "chapter_003_three.md"), (12, tmp_path / "chapter_012_twelve.md")]
    lines = chapter_manifest_lines(chapters)
    assert lines[0].startswith("003\t")
    assert lines[1].startswith("012\t")


@pytest.mark.unit
def test_normalize_tts_batch_output_handles_tuple_payload() -> None:
    payload = ([np.array([0.1, 0.2]), np.array([0.3])], 44100)
    audios, sr = normalize_tts_batch_output(payload)
    assert sr == 44100
    assert len(audios) == 2
    assert audios[0].shape == (2,)


@pytest.mark.unit
def test_normalize_tts_batch_output_handles_scalar_audio() -> None:
    audios, sr = normalize_tts_batch_output(np.array([0.5, 0.6]))
    assert sr == 24000
    assert len(audios) == 1
    assert audios[0].shape == (2,)
