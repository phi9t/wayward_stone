from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .adapters import AgentFacade, CriticResult
from .chapter_index import chapter_filename, discover_chapter_files, highest_chapter_number, next_chapter_number
from .config import LoopConfig
from .logging_utils import append_event
from .prompts import critic_prompt, reviser_prompt, writer_prompt
from .quality import evaluate_quality_gate
from .state import (
    ChapterState,
    RunState,
    chapter_state_path,
    load_or_init_chapter_state,
    load_or_init_run_state,
    save_chapter_state,
    save_run_state,
)


def _ensure_layout(cfg: LoopConfig) -> None:
    cfg.manuscript_dir.mkdir(parents=True, exist_ok=True)
    cfg.plans_dir.mkdir(parents=True, exist_ok=True)
    cfg.logs_dir.mkdir(parents=True, exist_ok=True)
    cfg.state_dir.mkdir(parents=True, exist_ok=True)
    (cfg.artifacts_dir / "critic").mkdir(parents=True, exist_ok=True)
    (cfg.artifacts_dir / "revision").mkdir(parents=True, exist_ok=True)

    continuity_path = cfg.plans_dir / "continuity_log.md"
    if not continuity_path.exists():
        continuity_path.write_text("# Continuity Log\n\n", encoding="utf-8")


def _chapter_file_for_number(manuscript_dir: Path, chapter_num: int) -> Path | None:
    for num, path in discover_chapter_files(manuscript_dir):
        if num == chapter_num:
            return path
    return None


def _write_plan(cfg: LoopConfig, chapter_num: int) -> Path:
    plan_path = cfg.plans_dir / f"chapter_{chapter_num:03d}-{chapter_num + 1:03d}.md"
    if not plan_path.exists():
        plan_path.write_text(
            "\n".join(
                [
                    f"# Chapter {chapter_num:03d} Plan",
                    "",
                    "## Goal",
                    "Advance core arc while preserving continuity constraints.",
                    "",
                    "## Scenes",
                    "1. Open with immediate tension.",
                    "2. Escalate conflict with concrete stakes.",
                    "3. End on a resonant hook.",
                    "",
                    "## Motifs",
                    "Silence, wind, doors, names, music.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
    return plan_path


def _critic_artifact_path(cfg: LoopConfig, chapter_num: int) -> Path:
    return cfg.artifacts_dir / "critic" / f"chapter_{chapter_num:03d}_review.json"


def _revision_artifact_path(cfg: LoopConfig, chapter_num: int, revision_count: int) -> Path:
    return cfg.artifacts_dir / "revision" / f"chapter_{chapter_num:03d}_rev_{revision_count:02d}.json"


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _read_excerpt(path: Path, max_chars: int = 3000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[truncated]..."


def _append_continuity(cfg: LoopConfig, chapter_num: int, chapter_path: Path, critique: CriticResult) -> None:
    continuity_path = cfg.plans_dir / "continuity_log.md"
    stamp = datetime.now(timezone.utc).isoformat()
    entry = (
        f"- {stamp} | chapter {chapter_num:03d} | {chapter_path.name} | "
        f"overall={critique.overall_score:.2f} | must_fix={len(critique.must_fix)}\n"
    )
    with continuity_path.open("a", encoding="utf-8") as f:
        f.write(entry)


def _chapter_summary(cfg: LoopConfig, run_state: RunState) -> None:
    summary_path = cfg.state_dir / "summary.json"
    payload = {
        "run_id": run_state.run_id,
        "target_chapter": run_state.target_chapter,
        "completed_chapters": run_state.completed_chapters,
        "total_failures": run_state.total_failures,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _chapter_filename(chapter_state: ChapterState, chapter_num: int, title: str) -> str:
    if chapter_state.filename:
        return chapter_state.filename
    return chapter_filename(chapter_num, title=title)


def run_loop(cfg: LoopConfig, resume: bool = False) -> int:
    _ensure_layout(cfg)
    events_path = cfg.logs_dir / "events.jsonl"

    run_state = load_or_init_run_state(cfg.run_state_path, run_id=cfg.run_id, target_chapter=cfg.target_chapter)
    if not resume and run_state.completed_chapters:
        append_event(events_path, "resume_hint", message="Run has existing completed chapters; use --resume to continue")

    agents = AgentFacade(
        run_root=cfg.run_root,
        writer_agent=cfg.writer_agent,
        critic_model=cfg.critic_model,
        reviser_model=cfg.reviser_model,
    )

    append_event(events_path, "run_start", run_id=cfg.run_id, target=cfg.target_chapter, resume=resume)

    def has_pending_chapter() -> bool:
        if run_state.current_chapter <= 0:
            return False
        path = chapter_state_path(cfg.state_dir, run_state.current_chapter)
        if not path.exists():
            return False
        payload = json.loads(path.read_text(encoding="utf-8"))
        return not bool(payload.get("passed", False))

    while highest_chapter_number(cfg.manuscript_dir) < cfg.target_chapter or has_pending_chapter():
        chapter_num = run_state.current_chapter if has_pending_chapter() else next_chapter_number(cfg.manuscript_dir)
        run_state.current_chapter = chapter_num
        save_run_state(cfg.run_state_path, run_state)

        chapter_state = load_or_init_chapter_state(cfg.state_dir, chapter_num)
        append_event(events_path, "chapter_start", chapter=chapter_num, phase=chapter_state.phase)

        while not chapter_state.passed:
            if chapter_state.phase == "PLAN_CHAPTER":
                plan_path = _write_plan(cfg, chapter_num)
                append_event(events_path, "plan_written", chapter=chapter_num, plan=str(plan_path))
                chapter_state.phase = "WRITE_DRAFT"
                save_chapter_state(cfg.state_dir, chapter_state)
                continue

            if chapter_state.phase == "WRITE_DRAFT":
                plan_path = cfg.plans_dir / f"chapter_{chapter_num:03d}-{chapter_num + 1:03d}.md"
                prompt = writer_prompt(
                    chapter_num=chapter_num,
                    continuity_excerpt=_read_excerpt(cfg.plans_dir / "continuity_log.md"),
                    planning_excerpt=_read_excerpt(plan_path),
                    restart=chapter_state.restart_count > 0,
                )
                writer = agents.writer(chapter_num=chapter_num, prompt=prompt, restart=chapter_state.restart_count > 0)
                filename = _chapter_filename(chapter_state, chapter_num, writer.chapter_title)
                chapter_path = cfg.manuscript_dir / filename
                _write_text_atomic(chapter_path, writer.draft_text)
                chapter_state.filename = filename
                chapter_state.phase = "CRITIQUE_DRAFT"
                save_chapter_state(cfg.state_dir, chapter_state)
                append_event(events_path, "draft_written", chapter=chapter_num, file=filename)
                continue

            chapter_path = cfg.manuscript_dir / chapter_state.filename if chapter_state.filename else _chapter_file_for_number(cfg.manuscript_dir, chapter_num)
            if chapter_path is None or not chapter_path.exists():
                chapter_state.phase = "WRITE_DRAFT"
                save_chapter_state(cfg.state_dir, chapter_state)
                append_event(events_path, "draft_missing", chapter=chapter_num)
                continue

            if chapter_state.phase in {"CRITIQUE_DRAFT", "RECRITIQUE"}:
                chapter_text = chapter_path.read_text(encoding="utf-8")
                critique = agents.critic(chapter_text=chapter_text, prompt=critic_prompt(chapter_text=chapter_text, chapter_num=chapter_num))

                critique_path = _critic_artifact_path(cfg, chapter_num)
                critique_path.write_text(json.dumps(critique.as_dict(), indent=2), encoding="utf-8")

                gate = evaluate_quality_gate(
                    invariant_violations=critique.invariant_violations,
                    overall_score=critique.overall_score,
                    category_scores=critique.category_scores,
                    overall_min=cfg.quality_overall_min,
                    category_min=cfg.quality_category_min,
                )

                append_event(
                    events_path,
                    "critique_complete",
                    chapter=chapter_num,
                    passed=gate.passed,
                    reasons=gate.reasons,
                    overall=critique.overall_score,
                )

                if gate.passed:
                    chapter_state.phase = "PASS_CHAPTER"
                else:
                    if chapter_state.revision_count >= cfg.max_revision_loops:
                        chapter_state.phase = "WRITE_DRAFT"
                        chapter_state.restart_count += 1
                        chapter_state.revision_count = 0
                        run_state.total_failures += 1
                        if run_state.total_failures > cfg.max_total_failures:
                            raise RuntimeError(
                                f"Exceeded max_total_failures ({cfg.max_total_failures}) without reaching quality gate"
                            )
                        save_run_state(cfg.run_state_path, run_state)
                        append_event(events_path, "chapter_restart", chapter=chapter_num, restart_count=chapter_state.restart_count)
                    else:
                        chapter_state.phase = "REVISE"
                save_chapter_state(cfg.state_dir, chapter_state)
                continue

            if chapter_state.phase == "REVISE":
                chapter_text = chapter_path.read_text(encoding="utf-8")
                critique_payload = _critic_artifact_path(cfg, chapter_num).read_text(encoding="utf-8")
                revision_count = chapter_state.revision_count + 1
                revision_output = _revision_artifact_path(cfg, chapter_num, revision_count)
                revised = agents.reviser(
                    chapter_text=chapter_text,
                    critique=CriticResult(**json.loads(critique_payload)),
                    prompt=reviser_prompt(chapter_text=chapter_text, critique_json=critique_payload, chapter_num=chapter_num),
                    output_path=revision_output,
                    revision_count=revision_count,
                )
                _write_text_atomic(chapter_path, revised.revised_text)
                revision_output.write_text(
                    json.dumps(
                        {
                            "changes_summary": revised.changes_summary,
                            "applied_fixes": revised.applied_fixes,
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                chapter_state.revision_count = revision_count
                chapter_state.phase = "RECRITIQUE"
                save_chapter_state(cfg.state_dir, chapter_state)
                append_event(events_path, "revision_applied", chapter=chapter_num, revision_count=revision_count)
                continue

            if chapter_state.phase == "PASS_CHAPTER":
                critique_payload = json.loads(_critic_artifact_path(cfg, chapter_num).read_text(encoding="utf-8"))
                critique = CriticResult(**critique_payload)
                chapter_state.passed = True
                chapter_state.phase = "DONE"
                save_chapter_state(cfg.state_dir, chapter_state)

                if chapter_num not in run_state.completed_chapters:
                    run_state.completed_chapters.append(chapter_num)
                    run_state.completed_chapters.sort()
                run_state.phase = "CHECK_TARGET"
                save_run_state(cfg.run_state_path, run_state)

                _append_continuity(cfg, chapter_num, chapter_path, critique)
                _chapter_summary(cfg, run_state)
                append_event(events_path, "chapter_passed", chapter=chapter_num, file=chapter_path.name)
                break

            raise RuntimeError(f"Unknown chapter phase: {chapter_state.phase}")

        run_state.current_chapter = 0
        save_run_state(cfg.run_state_path, run_state)

    run_state.phase = "DONE"
    save_run_state(cfg.run_state_path, run_state)
    _chapter_summary(cfg, run_state)
    append_event(events_path, "run_complete", completed=run_state.completed_chapters)
    return 0
