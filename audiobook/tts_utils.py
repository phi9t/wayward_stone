from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

import numpy as np


def normalize_tts_output(wav_output, default_sample_rate: int = 24000):
    """Normalize qwen-tts output variants into (1D float32 audio, sample_rate)."""
    if isinstance(wav_output, tuple) and len(wav_output) == 2:
        audio, sample_rate = wav_output
        if isinstance(audio, list):
            if len(audio) == 0:
                return np.zeros((0,), dtype=np.float32), int(sample_rate)
            if len(audio) == 1:
                return np.asarray(audio[0], dtype=np.float32).ravel(), int(sample_rate)
            merged = np.concatenate([np.asarray(x, dtype=np.float32).ravel() for x in audio])
            return merged, int(sample_rate)
        return np.asarray(audio, dtype=np.float32).ravel(), int(sample_rate)
    if isinstance(wav_output, list):
        if len(wav_output) == 0:
            return np.zeros((0,), dtype=np.float32), int(default_sample_rate)
        if len(wav_output) == 1:
            return np.asarray(wav_output[0], dtype=np.float32).ravel(), int(default_sample_rate)
        merged = np.concatenate([np.asarray(x, dtype=np.float32).ravel() for x in wav_output])
        return merged, int(default_sample_rate)
    return np.asarray(wav_output, dtype=np.float32).ravel(), int(default_sample_rate)


def normalize_tts_batch_output(wav_output, default_sample_rate: int = 24000):
    """Normalize qwen-tts batch output into (list[1D float32 audio], sample_rate)."""
    if isinstance(wav_output, tuple) and len(wav_output) == 2:
        audio, sample_rate = wav_output
        if isinstance(audio, list):
            normalized = [np.asarray(item, dtype=np.float32).ravel() for item in audio]
            return normalized, int(sample_rate)
        return [np.asarray(audio, dtype=np.float32).ravel()], int(sample_rate)
    if isinstance(wav_output, list):
        return [np.asarray(item, dtype=np.float32).ravel() for item in wav_output], int(default_sample_rate)
    return [np.asarray(wav_output, dtype=np.float32).ravel()], int(default_sample_rate)


# NOTE: Chapter discovery logic parallels inkforge_loop/chapter_index.py:discover_chapter_files
def discover_chapters(src_dir: Path, glob_pattern: str = "chapter_*.md") -> list[tuple[int, Path]]:
    """Return sorted chapter files by numeric prefix."""
    chapter_name_re = re.compile(r"^chapter_(\d+)(?:_.*)?\.md$", re.IGNORECASE)
    chapters: list[tuple[int, Path]] = []
    for path in src_dir.glob(glob_pattern):
        match = chapter_name_re.match(path.name)
        if match:
            chapters.append((int(match.group(1)), path))
    chapters.sort()
    return chapters


def chapter_manifest_lines(chapters: Iterable[tuple[int, Path]]) -> list[str]:
    return [f"{num:03d}\t{path.as_posix()}" for num, path in chapters]
