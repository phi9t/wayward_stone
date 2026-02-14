from __future__ import annotations

import sys
import wave
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return ROOT


@pytest.fixture
def make_wav(tmp_path):
    def _make(
        name: str,
        *,
        nchannels: int = 1,
        sampwidth: int = 2,
        framerate: int = 8000,
        frames: int = 200,
    ) -> Path:
        path = tmp_path / name
        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(nchannels)
            wav.setsampwidth(sampwidth)
            wav.setframerate(framerate)
            wav.writeframes(b"\x00" * frames * nchannels * sampwidth)
        return path

    return _make
