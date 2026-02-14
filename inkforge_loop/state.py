from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class RunState:
    run_id: str
    target_chapter: int
    current_chapter: int = 0
    phase: str = "INIT_RUN"
    total_failures: int = 0
    completed_chapters: list[int] = field(default_factory=list)


@dataclass
class ChapterState:
    chapter_number: int
    phase: str = "PLAN_CHAPTER"
    revision_count: int = 0
    restart_count: int = 0
    filename: str = ""
    passed: bool = False


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def load_or_init_run_state(path: Path, run_id: str, target_chapter: int) -> RunState:
    if path.exists():
        raw = _read_json(path)
        return RunState(**raw)
    state = RunState(run_id=run_id, target_chapter=target_chapter)
    save_run_state(path, state)
    return state


def save_run_state(path: Path, state: RunState) -> None:
    _write_json(path, asdict(state))


def chapter_state_path(state_dir: Path, chapter_num: int) -> Path:
    return state_dir / f"chapter_{chapter_num:03d}_state.json"


def load_or_init_chapter_state(state_dir: Path, chapter_num: int) -> ChapterState:
    path = chapter_state_path(state_dir, chapter_num)
    if path.exists():
        return ChapterState(**_read_json(path))
    state = ChapterState(chapter_number=chapter_num)
    save_chapter_state(state_dir, state)
    return state


def save_chapter_state(state_dir: Path, state: ChapterState) -> None:
    path = chapter_state_path(state_dir, state.chapter_number)
    _write_json(path, asdict(state))
