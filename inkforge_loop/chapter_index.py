from __future__ import annotations

import re
from pathlib import Path

CHAPTER_RE = re.compile(r"^chapter_(\d+)(?:_.*)?\.md$", re.IGNORECASE)


def discover_chapter_files(manuscript_dir: Path) -> list[tuple[int, Path]]:
    chapters: list[tuple[int, Path]] = []
    if not manuscript_dir.exists():
        return chapters
    for path in manuscript_dir.glob("chapter_*.md"):
        match = CHAPTER_RE.match(path.name)
        if match:
            chapters.append((int(match.group(1)), path))
    chapters.sort()
    return chapters


def highest_chapter_number(manuscript_dir: Path) -> int:
    chapters = discover_chapter_files(manuscript_dir)
    return chapters[-1][0] if chapters else 0


def next_chapter_number(manuscript_dir: Path) -> int:
    return highest_chapter_number(manuscript_dir) + 1


def slugify_title(title: str, fallback: str) -> str:
    lowered = title.strip().lower()
    if not lowered:
        lowered = fallback.lower()
    slug = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    return slug or fallback.lower()


def chapter_filename(chapter_num: int, title: str) -> str:
    slug = slugify_title(title, fallback=f"chapter_{chapter_num:03d}")
    return f"chapter_{chapter_num:03d}_{slug}.md"
