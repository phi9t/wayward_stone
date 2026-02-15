from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class WriterResult:
    chapter_title: str
    draft_text: str
    notes: str = ""


@dataclass
class CriticResult:
    invariant_violations: list[str]
    overall_score: float
    category_scores: dict[str, float]
    must_fix: list[str]
    nice_to_fix: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "invariant_violations": self.invariant_violations,
            "overall_score": self.overall_score,
            "category_scores": self.category_scores,
            "must_fix": self.must_fix,
            "nice_to_fix": self.nice_to_fix,
        }


@dataclass
class ReviserResult:
    revised_text: str
    changes_summary: str
    applied_fixes: list[str]


class AgentInvocationError(RuntimeError):
    pass


def _run_command(cmd: list[str], cwd: Path, env: dict[str, str] | None = None, timeout: int = 600) -> str:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            env={**os.environ, **(env or {})},
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise AgentInvocationError(f"Command timed out after {timeout}s: {' '.join(cmd)}") from exc
    if proc.returncode != 0:
        raise AgentInvocationError(
            f"Command failed ({proc.returncode}): {' '.join(cmd)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc.stdout.strip()


def _try_parse_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None
    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass

    for line in reversed([ln for ln in text.splitlines() if ln.strip()]):
        try:
            payload = json.loads(line)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            continue

    matches = re.findall(r"\{[\s\S]*\}", text)
    for chunk in reversed(matches):
        try:
            payload = json.loads(chunk)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            continue

    fence = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    for chunk in reversed(fence):
        try:
            payload = json.loads(chunk)
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError:
            continue

    return None


def _deep_find_text(node: Any) -> str:
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        for item in reversed(node):
            out = _deep_find_text(item)
            if out:
                return out
    if isinstance(node, dict):
        for key in ("draft_text", "revised_text", "text", "content", "message", "output"):
            if key in node:
                out = _deep_find_text(node[key])
                if out:
                    return out
        for value in reversed(list(node.values())):
            out = _deep_find_text(value)
            if out:
                return out
    return ""


_CRITIC_REQUIRED_KEYS = {
    "invariant_violations",
    "overall_score",
    "category_scores",
    "must_fix",
    "nice_to_fix",
}


def _collect_json_objects(text: str) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(payload: dict[str, Any]) -> None:
        key = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        if key not in seen:
            seen.add(key)
            objects.append(payload)

    primary = _try_parse_json(text)
    if primary is not None:
        add(primary)

    for line in [ln for ln in text.splitlines() if ln.strip()]:
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            add(payload)

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            add(value)
            for inner in value.values():
                walk(inner)
            return
        if isinstance(value, list):
            for item in value:
                walk(item)
            return
        if isinstance(value, str):
            nested = _try_parse_json(value)
            if nested is not None:
                add(nested)
                for inner in nested.values():
                    walk(inner)

    idx = 0
    while idx < len(objects):
        node = objects[idx]
        idx += 1
        for value in node.values():
            walk(value)
    return objects


def _is_critic_payload(payload: dict[str, Any]) -> bool:
    return _CRITIC_REQUIRED_KEYS.issubset(set(payload.keys()))


def _extract_critic_payload(raw: str) -> dict[str, Any]:
    candidates = _collect_json_objects(raw)
    for payload in reversed(candidates):
        if _is_critic_payload(payload):
            return payload
    raise AgentInvocationError("Critic output missing required schema fields")


def _extract_writer_payload(raw: str) -> dict[str, Any]:
    candidates = _collect_json_objects(raw)
    for payload in reversed(candidates):
        if "draft_text" in payload or "chapter_title" in payload or "title" in payload:
            return payload

    for payload in reversed(candidates):
        text = _deep_find_text(payload)
        if not text:
            continue
        nested = _try_parse_json(text)
        if nested is not None and ("draft_text" in nested or "chapter_title" in nested or "title" in nested):
            return nested
    return {}


def _infer_title_from_text(draft_text: str) -> str:
    heading = draft_text.splitlines()[0] if draft_text.splitlines() else ""
    match = re.match(r"^#\s*Chapter\s+\d+\s+[—-]\s*(.+)$", heading.strip())
    if match:
        return match.group(1).strip()
    return "Untitled"


def _looks_like_json_event_stream(text: str) -> bool:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return False
    parsed = 0
    for line in lines:
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            return False
        if not isinstance(payload, dict) or "type" not in payload:
            return False
        parsed += 1
    return parsed > 0


def _looks_like_chapter_draft(text: str) -> bool:
    head = text.lstrip().splitlines()[0] if text.lstrip().splitlines() else ""
    if re.match(r"^#\s*Chapter\s+\d+\s+[—-]\s+.+", head):
        return True
    return bool(re.match(r"^Chapter\s+\d+\b", head))


class MockAgentAdapter:
    def __init__(self, run_root: Path) -> None:
        self.run_root = run_root
        self.mock_state_path = run_root / "state" / "mock_state.json"

    def _load_mock_state(self) -> dict[str, Any]:
        if self.mock_state_path.exists():
            return json.loads(self.mock_state_path.read_text(encoding="utf-8"))
        return {"critic_calls": 0}

    def _save_mock_state(self, state: dict[str, Any]) -> None:
        self.mock_state_path.parent.mkdir(parents=True, exist_ok=True)
        self.mock_state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def writer(self, chapter_num: int, restart: bool) -> WriterResult:
        title = f"Inkforge Chapter {chapter_num:03d}"
        body = (
            f"# Chapter {chapter_num} — {title}\n\n"
            f"This is a mock draft for chapter {chapter_num:03d}.\n"
            f"Restart mode: {'yes' if restart else 'no'}.\n"
        )
        return WriterResult(chapter_title=title, draft_text=body, notes="mock_writer")

    def critic(self, chapter_text: str) -> CriticResult:
        state = self._load_mock_state()
        calls = int(state.get("critic_calls", 0))
        state["critic_calls"] = calls + 1
        self._save_mock_state(state)

        pattern = os.environ.get("INKFORGE_MOCK_CRITIC_PATTERN", "pass").split(",")
        pattern = [p.strip().lower() for p in pattern if p.strip()]
        token = pattern[calls] if calls < len(pattern) else pattern[-1]

        if token == "pass":
            return CriticResult(
                invariant_violations=[],
                overall_score=9.2,
                category_scores={"pacing": 9.0, "canon": 9.5, "voice": 9.1},
                must_fix=[],
                nice_to_fix=["minor line polish"],
            )

        if token == "invariant":
            return CriticResult(
                invariant_violations=["register_violation"],
                overall_score=8.9,
                category_scores={"pacing": 8.8, "canon": 9.0, "voice": 8.7},
                must_fix=["remove frame narrative leakage"],
                nice_to_fix=[],
            )

        return CriticResult(
            invariant_violations=[],
            overall_score=8.0,
            category_scores={"pacing": 7.0, "canon": 8.4, "voice": 7.8},
            must_fix=["tighten pacing", "improve voice distinction"],
            nice_to_fix=[],
        )

    def reviser(self, chapter_text: str, critique: CriticResult, revision_count: int) -> ReviserResult:
        revised = chapter_text + f"\n\n[Mock revision pass {revision_count}]\n"
        return ReviserResult(
            revised_text=revised,
            changes_summary=f"Applied mock revision pass {revision_count}",
            applied_fixes=critique.must_fix or ["general cleanup"],
        )


class CliAgentAdapter:
    def __init__(self, run_root: Path, writer_agent: str, critic_model: str, reviser_model: str) -> None:
        self.run_root = run_root
        self.writer_agent = writer_agent
        self.critic_model = critic_model
        self.reviser_model = reviser_model

    def writer(self, prompt: str) -> WriterResult:
        cmd_base = ["opencode", "run", "--agent", self.writer_agent]
        attempts = [(["--format", "json"], "json"), ([], "default")]
        last_error = "Writer produced empty draft_text"

        for extra_args, label in attempts:
            out = _run_command([*cmd_base, *extra_args, prompt], cwd=self.run_root)
            payload = _extract_writer_payload(out)
            title = str(payload.get("chapter_title") or payload.get("title") or "")
            draft_text = str(payload.get("draft_text") or "")

            if draft_text:
                maybe_nested = _try_parse_json(draft_text)
                if maybe_nested is not None:
                    draft_text = str(maybe_nested.get("draft_text") or _deep_find_text(maybe_nested) or "")
                    title = str(maybe_nested.get("chapter_title") or maybe_nested.get("title") or title)

            if not draft_text.strip():
                if payload:
                    fallback = _deep_find_text(payload)
                    maybe_nested = _try_parse_json(fallback) if fallback else None
                    if maybe_nested is not None:
                        draft_text = str(maybe_nested.get("draft_text") or _deep_find_text(maybe_nested) or "")
                        title = str(maybe_nested.get("chapter_title") or maybe_nested.get("title") or title)
                    else:
                        draft_text = fallback
                else:
                    draft_text = out

            if not draft_text.strip():
                last_error = f"Writer produced empty draft_text ({label} mode)"
                continue
            if _looks_like_json_event_stream(draft_text):
                last_error = f"Writer produced event telemetry instead of prose ({label} mode)"
                continue
            if not _looks_like_chapter_draft(draft_text):
                last_error = f"Writer output did not resemble a chapter draft ({label} mode)"
                continue

            notes = str(payload.get("notes") or "")
            if not title:
                title = _infer_title_from_text(draft_text)
            return WriterResult(chapter_title=title, draft_text=draft_text, notes=notes)

        raise AgentInvocationError(last_error)

    def critic(self, prompt: str) -> CriticResult:
        schema = {
            "type": "object",
            "properties": {
                "invariant_violations": {"type": "array", "items": {"type": "string"}},
                "overall_score": {"type": "number"},
                "category_scores": {"type": "object", "additionalProperties": {"type": "number"}},
                "must_fix": {"type": "array", "items": {"type": "string"}},
                "nice_to_fix": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "invariant_violations",
                "overall_score",
                "category_scores",
                "must_fix",
                "nice_to_fix",
            ],
        }
        out = _run_command(
            [
                "claude",
                "-p",
                "--output-format",
                "json",
                "--model",
                self.critic_model,
                "--json-schema",
                json.dumps(schema, separators=(",", ":")),
                "--permission-mode",
                "default",
                prompt,
            ],
            cwd=self.run_root,
        )
        payload = _extract_critic_payload(out)
        return CriticResult(
            invariant_violations=[str(x) for x in list(payload["invariant_violations"])],
            overall_score=float(payload["overall_score"]),
            category_scores={k: float(v) for k, v in dict(payload["category_scores"]).items()},
            must_fix=[str(x) for x in list(payload["must_fix"])],
            nice_to_fix=[str(x) for x in list(payload["nice_to_fix"])],
        )

    def reviser(self, prompt: str, output_path: Path) -> ReviserResult:
        _run_command(
            [
                "codex",
                "exec",
                "--json",
                "--model",
                self.reviser_model,
                "-o",
                str(output_path),
                "-C",
                str(self.run_root),
                prompt,
            ],
            cwd=self.run_root,
        )
        raw = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
        payload = _try_parse_json(raw)
        if payload:
            revised_text = str(payload.get("revised_text") or _deep_find_text(payload))
            return ReviserResult(
                revised_text=revised_text,
                changes_summary=str(payload.get("changes_summary") or "revised"),
                applied_fixes=list(payload.get("applied_fixes") or []),
            )
        return ReviserResult(revised_text=raw, changes_summary="revised", applied_fixes=[])


class AgentFacade:
    def __init__(self, run_root: Path, writer_agent: str, critic_model: str, reviser_model: str) -> None:
        mode = os.environ.get("INKFORGE_AGENT_MODE", "live").lower()
        self.mock = mode == "mock"
        self.mock_adapter = MockAgentAdapter(run_root) if self.mock else None
        self.live_adapter = None if self.mock else CliAgentAdapter(run_root, writer_agent, critic_model, reviser_model)

    def writer(self, chapter_num: int, prompt: str, restart: bool) -> WriterResult:
        if self.mock:
            assert self.mock_adapter
            return self.mock_adapter.writer(chapter_num=chapter_num, restart=restart)
        assert self.live_adapter
        return self.live_adapter.writer(prompt)

    def critic(self, chapter_text: str, prompt: str) -> CriticResult:
        if self.mock:
            assert self.mock_adapter
            return self.mock_adapter.critic(chapter_text=chapter_text)
        assert self.live_adapter
        return self.live_adapter.critic(prompt)

    def reviser(
        self, chapter_text: str, critique: CriticResult, prompt: str, output_path: Path, revision_count: int
    ) -> ReviserResult:
        if self.mock:
            assert self.mock_adapter
            return self.mock_adapter.reviser(
                chapter_text=chapter_text, critique=critique, revision_count=revision_count
            )
        assert self.live_adapter
        return self.live_adapter.reviser(prompt=prompt, output_path=output_path)
