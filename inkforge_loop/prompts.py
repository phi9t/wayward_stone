from __future__ import annotations


def writer_prompt(chapter_num: int, continuity_excerpt: str, planning_excerpt: str, restart: bool) -> str:
    restart_note = "This is a full restart draft after repeated revision failures." if restart else ""
    return (
        f"You are the writer agent for Wayward Stone. Draft chapter {chapter_num:03d}.\n"
        "Use repository constraints from AGENTS.md, CLAUDE.md, writing_style.md, "
        "and the writer/pipeline skills.\n"
        "Continuity context:\n"
        f"{continuity_excerpt}\n"
        "Planning context:\n"
        f"{planning_excerpt}\n"
        f"{restart_note}\n"
        "If any detail is missing, invent a plausible continuation and proceed without asking follow-up questions. "
        "Do not call tools. Do not emit step/event telemetry. "
        "Draft must begin with '# Chapter X — Title'. "
        "Return strict JSON with keys: chapter_title, draft_text, notes."
    )


def critic_prompt(chapter_text: str, chapter_num: int) -> str:
    return (
        f"Critique chapter {chapter_num:03d} for canon/continuity/voice using repo rules and critic skill.\n"
        "Return strict JSON keys: invariant_violations (array), overall_score (number), "
        "category_scores (object), must_fix (array), nice_to_fix (array).\n"
        "Chapter text follows:\n"
        f"{chapter_text}"
    )


def reviser_prompt(chapter_text: str, critique_json: str, chapter_num: int) -> str:
    return (
        f"Revise chapter {chapter_num:03d} using the critique findings.\n"
        "Fix invariants/canon/continuity first, then pacing/voice.\n"
        "Return strict JSON with keys: revised_text, changes_summary, applied_fixes.\n"
        "Critique JSON:\n"
        f"{critique_json}\n"
        "Current chapter text:\n"
        f"{chapter_text}"
    )
