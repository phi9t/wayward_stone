from __future__ import annotations

import argparse
import wave

import numpy as np
import pytest

from audiobook.qwen3_tts_audiobook import (
    chunk_text,
    markdown_to_text,
    merge_wavs,
    positive_int,
    split_sentences,
)
from audiobook.tts_utils import normalize_tts_output


@pytest.mark.unit
def test_positive_int_accepts_positive_values() -> None:
    assert positive_int("7") == 7


@pytest.mark.unit
def test_positive_int_rejects_non_positive_values() -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        positive_int("0")


@pytest.mark.unit
def test_split_sentences_handles_whitespace() -> None:
    text = "  Hello world.  How are you?  Fine!  "
    assert split_sentences(text) == ["Hello world.", "How are you?", "Fine!"]


@pytest.mark.unit
def test_chunk_text_hard_splits_long_sentence() -> None:
    chunks = chunk_text("A" * 11 + ".", max_chars=5)
    assert chunks == ["AAAAA", "AAAAA", "A."]


@pytest.mark.unit
def test_markdown_to_text_strips_structural_markup() -> None:
    raw = """
# Header
- item one
- item two
`inline`

```python
print('x')
```

[link](https://example.com)
"""
    out = markdown_to_text(raw)
    assert "Header" in out
    assert "item one" in out
    assert "inline" in out
    assert "print" not in out


@pytest.mark.unit
def test_normalize_tts_output_handles_tuple_list_shape() -> None:
    payload = ([np.array([0.1, 0.2]), np.array([0.3])], 22050)
    audio, sr = normalize_tts_output(payload)
    assert sr == 22050
    assert audio.shape == (3,)


@pytest.mark.unit
def test_merge_wavs_merges_in_order(make_wav) -> None:
    first = make_wav("a.wav", frames=100)
    second = make_wav("b.wav", frames=60)
    out = first.parent / "out.wav"

    merge_wavs([first, second], out)

    with wave.open(str(out), "rb") as merged:
        assert merged.getnframes() == 160


@pytest.mark.unit
def test_merge_wavs_rejects_mismatched_format(make_wav) -> None:
    first = make_wav("a.wav", framerate=8000)
    second = make_wav("b.wav", framerate=16000)
    out = first.parent / "out.wav"

    with pytest.raises(ValueError, match="Incompatible wav format"):
        merge_wavs([first, second], out)
