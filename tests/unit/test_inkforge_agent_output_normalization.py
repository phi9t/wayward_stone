from __future__ import annotations

import pytest

from inkforge_loop.adapters import _deep_find_text, _try_parse_json


@pytest.mark.unit
def test_try_parse_json_reads_json_line() -> None:
    text = "not json\n{\"chapter_title\":\"X\",\"draft_text\":\"hello\"}\n"
    payload = _try_parse_json(text)
    assert payload is not None
    assert payload["chapter_title"] == "X"


@pytest.mark.unit
def test_deep_find_text_finds_nested_message() -> None:
    payload = {"events": [{"foo": 1}, {"content": {"text": "chapter body"}}]}
    assert _deep_find_text(payload) == "chapter body"
