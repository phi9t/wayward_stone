#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import re
import time
import wave
from collections.abc import Iterable
from pathlib import Path

try:
    from .tts_utils import normalize_tts_output
except ImportError:
    from tts_utils import normalize_tts_output

MODEL_DEFAULT = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
INSTRUCT_DEFAULT = "Read naturally, steady pace, clear pronunciation."


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def split_sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    return [p.strip() for p in parts if p.strip()]


def chunk_text(text: str, max_chars: int) -> list[str]:
    sentences = split_sentences(text)
    if not sentences:
        return []

    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        # If one sentence is too long, hard-split it.
        if len(sentence) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            for i in range(0, len(sentence), max_chars):
                chunks.append(sentence[i : i + max_chars])
            continue

        candidate = sentence if not current else f"{current} {sentence}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)

    return chunks


def markdown_to_text(raw: str) -> str:
    text = raw
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^\)]*\)", " ", text)
    text = re.sub(r"\[[^\]]*\]\([^\)]*\)", " ", text)
    text = re.sub(r"^\s{0,3}#{1,6}\s+", "", text, flags=re.M)
    text = re.sub(r"^\s*>\s?", "", text, flags=re.M)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.M)
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.M)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def merge_wavs(wav_paths: Iterable[Path], output_path: Path) -> None:
    wav_paths = list(wav_paths)
    if not wav_paths:
        raise ValueError("No wav files to merge")

    with wave.open(str(wav_paths[0]), "rb") as first:
        params = first.getparams()

    with wave.open(str(output_path), "wb") as out:
        out.setparams(params)
        for path in wav_paths:
            with wave.open(str(path), "rb") as src:
                src_params = src.getparams()
                if (
                    src_params.nchannels != params.nchannels
                    or src_params.sampwidth != params.sampwidth
                    or src_params.framerate != params.framerate
                ):
                    raise ValueError(f"Incompatible wav format: {path}")
                out.writeframes(src.readframes(src.getnframes()))


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate audiobook audio with Qwen3-TTS")
    p.add_argument("--input", required=True, help="Input text/markdown file")
    p.add_argument("--output", required=True, help="Output merged WAV path")
    p.add_argument(
        "--chunks-dir",
        default=None,
        help="Directory for per-chunk WAV files (default: audio_chunks/<input-stem>_<hash>)",
    )
    p.add_argument("--model", default=MODEL_DEFAULT, help="Qwen TTS model id")
    p.add_argument("--speaker", default="Ryan", help="Speaker name")
    p.add_argument("--language", default="English", help="Language name")
    p.add_argument("--instruct", default=INSTRUCT_DEFAULT, help="Speaking style instruction")
    p.add_argument("--max-chars", type=positive_int, default=420, help="Max characters per chunk")
    p.add_argument("--device-map", default="cpu", help="Model device map (e.g. cpu, cuda)")
    p.add_argument("--force", action="store_true", help="Regenerate existing chunk WAVs")
    p.add_argument("--dry-run", action="store_true", help="Only print chunk plan, do not synthesize")
    return p


def default_chunks_dir(input_path: Path) -> Path:
    abs_path = str(input_path.resolve())
    suffix = hashlib.sha1(abs_path.encode("utf-8")).hexdigest()[:10]
    return Path("audio_chunks") / f"{input_path.stem}_{suffix}"


def main() -> int:
    args = build_arg_parser().parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    chunks_dir = Path(args.chunks_dir) if args.chunks_dir else default_chunks_dir(input_path)

    raw_text = input_path.read_text(encoding="utf-8")
    text = markdown_to_text(raw_text)
    chunks = chunk_text(text, args.max_chars)

    if not chunks:
        raise ValueError("Input text produced zero chunks after preprocessing")

    print(f"Input: {input_path}")
    print(f"Chunks: {len(chunks)} (max_chars={args.max_chars})")
    print(f"Chunks dir: {chunks_dir}")
    print(f"Output: {output_path}")

    if args.dry_run:
        for i, chunk in enumerate(chunks[:10], start=1):
            preview = chunk[:120] + ("..." if len(chunk) > 120 else "")
            print(f"[{i:04d}] {preview}")
        if len(chunks) > 10:
            print(f"... {len(chunks) - 10} more chunks")
        return 0

    chunks_dir.mkdir(parents=True, exist_ok=True)

    import soundfile as sf
    from qwen_tts import Qwen3TTSModel

    print(f"Loading model: {args.model}")
    engine = Qwen3TTSModel.from_pretrained(
        pretrained_model_name_or_path=args.model,
        device_map=args.device_map,
    )

    t0 = time.time()
    rendered = 0

    for idx, chunk in enumerate(chunks, start=1):
        chunk_path = chunks_dir / f"chunk_{idx:05d}.wav"
        if chunk_path.exists() and not args.force:
            print(f"[{idx}/{len(chunks)}] skip existing {chunk_path.name}")
            continue

        wav = engine.generate_custom_voice(
            text=chunk,
            speaker=args.speaker,
            language=args.language,
            instruct=args.instruct,
        )

        wav_array, sample_rate = normalize_tts_output(wav)
        sf.write(chunk_path, wav_array, samplerate=sample_rate)
        rendered += 1

        elapsed = time.time() - t0
        rate = idx / elapsed if elapsed > 0 else 0.0
        eta = (len(chunks) - idx) / rate if rate > 0 else float("inf")
        eta_txt = f"{eta / 60:.1f}m" if eta != float("inf") else "unknown"
        print(f"[{idx}/{len(chunks)}] wrote {chunk_path.name} | elapsed={elapsed / 60:.1f}m eta={eta_txt}")

    chunk_paths = [chunks_dir / f"chunk_{i:05d}.wav" for i in range(1, len(chunks) + 1)]
    missing = [p for p in chunk_paths if not p.exists()]
    if missing:
        raise RuntimeError(f"Missing chunk WAV files: {len(missing)}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    merge_wavs(chunk_paths, output_path)

    total = time.time() - t0
    print(f"Rendered {rendered} chunks in {total / 60:.1f}m")
    print(f"Audiobook written: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
