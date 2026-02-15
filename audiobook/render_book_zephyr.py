#!/usr/bin/env python3
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from .qwen3_tts_audiobook import (
        INSTRUCT_DEFAULT,
        MODEL_DEFAULT,
        chunk_text,
        markdown_to_text,
        merge_wavs,
        positive_int,
    )
    from .tts_utils import chapter_manifest_lines, discover_chapters, normalize_tts_batch_output
except ImportError:
    from qwen3_tts_audiobook import (
        INSTRUCT_DEFAULT,
        MODEL_DEFAULT,
        chunk_text,
        markdown_to_text,
        merge_wavs,
        positive_int,
    )
    from tts_utils import chapter_manifest_lines, discover_chapters, normalize_tts_batch_output


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Batch render chapters with Qwen3-TTS")
    parser.add_argument("--source-dir", required=True, help="Directory containing chapter markdown files")
    parser.add_argument("--chapter-glob", default="chapter_*.md", help="Glob for chapter discovery")
    parser.add_argument("--out-dir", required=True, help="Output root directory")
    parser.add_argument("--chapters-subdir", default="chapters", help="Relative chapter output subdirectory")
    parser.add_argument("--chunks-root", default=None, help="Chunk root path (default: <out-dir>/chunks)")
    parser.add_argument(
        "--merge-output",
        default=None,
        help="Merged full-book wav path (default: <out-dir>/audiobook_all_chapters.wav)",
    )
    parser.add_argument("--no-merge", action="store_true", help="Skip merged full-book output")
    parser.add_argument("--manifest", default=None, help="Manifest path (default: <out-dir>/manifest.json)")

    parser.add_argument("--model", default=MODEL_DEFAULT, help="Qwen TTS model id")
    parser.add_argument("--device-map", default="cuda", help="Model device map (e.g. cpu, cuda)")
    parser.add_argument("--speaker", default="Ryan", help="Speaker name")
    parser.add_argument("--language", default="English", help="Language name")
    parser.add_argument("--instruct", default=INSTRUCT_DEFAULT, help="Speaking style instruction")

    parser.add_argument("--max-chars", type=positive_int, default=420, help="Max characters per chunk")
    parser.add_argument("--batch-size", type=positive_int, default=4, help="Chunks per generate call")
    parser.add_argument("--force", action="store_true", help="Regenerate existing chunk WAVs")
    parser.add_argument("--dry-run", action="store_true", help="Print resolved run plan without synthesis")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()

    source_dir = Path(args.source_dir)
    out_dir = Path(args.out_dir)
    chapters_dir = out_dir / args.chapters_subdir
    chunks_root = Path(args.chunks_root) if args.chunks_root else out_dir / "chunks"
    merge_output = Path(args.merge_output) if args.merge_output else out_dir / "audiobook_all_chapters.wav"
    manifest_path = Path(args.manifest) if args.manifest else out_dir / "manifest.json"

    if not source_dir.exists() or not source_dir.is_dir():
        raise NotADirectoryError(f"Source directory not found: {source_dir}")

    chapters = discover_chapters(source_dir, glob_pattern=args.chapter_glob)
    if not chapters:
        raise RuntimeError(f"No chapters matched pattern '{args.chapter_glob}' in {source_dir}")

    if args.dry_run:
        print("DRY RUN: generic book batch synthesis")
        print(f"source_dir={source_dir}")
        print(f"chapter_glob={args.chapter_glob}")
        print(f"out_dir={out_dir}")
        print(f"chapters_dir={chapters_dir}")
        print(f"chunks_root={chunks_root}")
        print(f"merge_enabled={not args.no_merge}")
        print(f"merge_output={merge_output}")
        print(f"manifest={manifest_path}")
        print(f"model={args.model}")
        print(f"device_map={args.device_map}")
        print(f"speaker={args.speaker}")
        print(f"language={args.language}")
        print(f"max_chars={args.max_chars}")
        print(f"batch_size={args.batch_size}")
        print(f"force={args.force}")
        print(f"chapter_count={len(chapters)}")
        for line in chapter_manifest_lines(chapters):
            print(f"chapter={line}")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    chapters_dir.mkdir(parents=True, exist_ok=True)
    chunks_root.mkdir(parents=True, exist_ok=True)

    chapter_manifest_path = out_dir / "chapter_manifest.txt"
    chapter_manifest_path.write_text("\n".join(chapter_manifest_lines(chapters)) + "\n", encoding="utf-8")

    import soundfile as sf
    from qwen_tts import Qwen3TTSModel

    print(f"Loading model once for {len(chapters)} chapters...")
    model = Qwen3TTSModel.from_pretrained(args.model, device_map=args.device_map)

    all_start = time.time()
    rendered_chapters = []
    chapter_wavs: list[Path] = []

    for chapter_num, chapter_path in chapters:
        chapter_tag = f"ch{chapter_num:03d}"
        chapter_wav = chapters_dir / f"{chapter_tag}.wav"

        text = markdown_to_text(chapter_path.read_text(encoding="utf-8"))
        chunks = chunk_text(text, max_chars=args.max_chars)
        if not chunks:
            print(f"[{chapter_tag}] empty after preprocessing, skipping")
            continue

        chapter_chunks = chunks_root / chapter_tag
        chapter_chunks.mkdir(parents=True, exist_ok=True)

        pending = []
        for idx, chunk in enumerate(chunks, start=1):
            chunk_path = chapter_chunks / f"chunk_{idx:05d}.wav"
            if args.force or not chunk_path.exists():
                pending.append((idx, chunk, chunk_path))

        print(f"[{chapter_tag}] chunks={len(chunks)} pending={len(pending)} -> {chapter_wav.name}")
        chapter_start = time.time()

        batch_start = 0
        max_batch_size = max(1, args.batch_size)
        while batch_start < len(pending):
            batch_size = min(max_batch_size, len(pending) - batch_start)
            batch = pending[batch_start : batch_start + batch_size]
            batch_texts = [item[1] for item in batch]

            try:
                wav = model.generate_custom_voice(
                    text=batch_texts,
                    speaker=args.speaker,
                    language=args.language,
                    instruct=args.instruct,
                )
            except RuntimeError as exc:
                if "out of memory" in str(exc).lower() and batch_size > 1:
                    next_size = max(1, batch_size // 2)
                    max_batch_size = next_size
                    try:
                        import torch

                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()
                    except Exception:
                        pass
                    print(
                        f"  [{chapter_tag}] CUDA OOM at batch_size={batch_size}; retrying with batch_size={next_size}"
                    )
                    continue
                raise

            audios, sample_rate = normalize_tts_batch_output(wav)
            if len(audios) != len(batch):
                raise RuntimeError(
                    f"[{chapter_tag}] batch output size mismatch: got {len(audios)} expected {len(batch)}"
                )

            for (_, _, chunk_path), audio in zip(batch, audios, strict=False):
                sf.write(chunk_path, audio, samplerate=sample_rate)

            batch_start += len(batch)
            done = batch_start
            if done == len(pending) or done % 10 == 0:
                elapsed = time.time() - chapter_start
                print(f"  [{chapter_tag}] rendered {done}/{len(pending)} pending chunks elapsed={elapsed / 60:.1f}m")

        ordered = [chapter_chunks / f"chunk_{i:05d}.wav" for i in range(1, len(chunks) + 1)]
        missing = [path for path in ordered if not path.exists()]
        if missing:
            raise RuntimeError(f"[{chapter_tag}] missing {len(missing)} chunk wav files")

        merge_wavs(ordered, chapter_wav)
        chapter_wavs.append(chapter_wav)

        chapter_elapsed = time.time() - chapter_start
        print(f"[{chapter_tag}] merged -> {chapter_wav} ({chapter_elapsed / 60:.1f}m)")
        rendered_chapters.append(
            {
                "chapter": chapter_num,
                "chapter_path": str(chapter_path),
                "chapter_wav": str(chapter_wav),
                "chunk_count": len(chunks),
                "pending_count": len(pending),
                "elapsed_minutes": round(chapter_elapsed / 60.0, 2),
            }
        )

    if not chapter_wavs:
        raise RuntimeError("No chapter wavs generated")

    master_output = None
    if not args.no_merge:
        merge_output.parent.mkdir(parents=True, exist_ok=True)
        merge_wavs(chapter_wavs, merge_output)
        master_output = merge_output
        print(f"Master audiobook: {merge_output}")

    elapsed_minutes = round((time.time() - all_start) / 60.0, 2)
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_dir": str(source_dir),
        "chapter_glob": args.chapter_glob,
        "out_dir": str(out_dir),
        "chapters_subdir": args.chapters_subdir,
        "chunks_root": str(chunks_root),
        "merge_enabled": not args.no_merge,
        "merge_output": str(master_output) if master_output else None,
        "manifest_version": 1,
        "model": args.model,
        "device_map": args.device_map,
        "speaker": args.speaker,
        "language": args.language,
        "max_chars": args.max_chars,
        "batch_size": args.batch_size,
        "force": args.force,
        "chapter_count": len(chapters),
        "rendered_count": len(rendered_chapters),
        "rendered_chapters": rendered_chapters,
        "elapsed_minutes": elapsed_minutes,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Manifest: {manifest_path}")
    print(f"Total elapsed: {elapsed_minutes:.1f}m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
