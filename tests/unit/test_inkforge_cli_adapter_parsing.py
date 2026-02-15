from __future__ import annotations

import json
from pathlib import Path

import pytest

from inkforge_loop.adapters import AgentInvocationError, CliAgentAdapter


@pytest.mark.unit
def test_critic_parses_claude_json_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    critique = {
        "invariant_violations": [],
        "overall_score": 9.3,
        "category_scores": {"pacing": 9.0, "canon": 9.6, "voice": 9.2},
        "must_fix": [],
        "nice_to_fix": ["trim one paragraph"],
    }
    envelope = {"type": "result", "result": json.dumps(critique)}

    monkeypatch.setattr(
        "inkforge_loop.adapters._run_command",
        lambda *_args, **_kwargs: json.dumps(envelope),
    )
    adapter = CliAgentAdapter(run_root=Path("."), writer_agent="writer", critic_model="sonnet", reviser_model="gpt-5")
    result = adapter.critic("critique this")

    assert result.overall_score == pytest.approx(9.3)
    assert result.category_scores["canon"] == pytest.approx(9.6)
    assert result.nice_to_fix == ["trim one paragraph"]


@pytest.mark.unit
def test_critic_raises_when_schema_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    bad_envelope = {"type": "result", "result": '{"foo":1}'}

    monkeypatch.setattr(
        "inkforge_loop.adapters._run_command",
        lambda *_args, **_kwargs: json.dumps(bad_envelope),
    )
    adapter = CliAgentAdapter(run_root=Path("."), writer_agent="writer", critic_model="sonnet", reviser_model="gpt-5")

    with pytest.raises(AgentInvocationError, match="missing required schema fields"):
        adapter.critic("critique this")


@pytest.mark.unit
def test_critic_parses_structured_output_field(monkeypatch: pytest.MonkeyPatch) -> None:
    envelope = {
        "type": "result",
        "structured_output": {
            "invariant_violations": [],
            "overall_score": 9.0,
            "category_scores": {"pacing": 8.8, "canon": 9.2, "voice": 9.0},
            "must_fix": ["tighten one scene"],
            "nice_to_fix": [],
        },
    }
    monkeypatch.setattr(
        "inkforge_loop.adapters._run_command",
        lambda *_args, **_kwargs: json.dumps(envelope),
    )
    adapter = CliAgentAdapter(run_root=Path("."), writer_agent="writer", critic_model="sonnet", reviser_model="gpt-5")
    result = adapter.critic("critique this")

    assert result.overall_score == pytest.approx(9.0)
    assert result.must_fix == ["tighten one scene"]


@pytest.mark.unit
def test_writer_extracts_payload_from_opencode_event_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    nested = {"chapter_title": "The Test Chapter", "draft_text": "# Chapter 1 — The Test Chapter\n\nBody text.\n"}
    stream = "\n".join(
        [
            json.dumps({"type": "response.created", "id": "abc"}),
            json.dumps({"type": "response.output_text.delta", "delta": "ignored"}),
            json.dumps({"type": "response.completed", "part": {"text": json.dumps(nested)}}),
        ]
    )

    monkeypatch.setattr("inkforge_loop.adapters._run_command", lambda *_args, **_kwargs: stream)
    adapter = CliAgentAdapter(run_root=Path("."), writer_agent="writer", critic_model="sonnet", reviser_model="gpt-5")
    result = adapter.writer("write")

    assert result.chapter_title == "The Test Chapter"
    assert "Body text." in result.draft_text


@pytest.mark.unit
def test_writer_retries_default_mode_after_event_telemetry(monkeypatch: pytest.MonkeyPatch) -> None:
    telemetry = "\n".join(
        [
            json.dumps({"type": "step_start", "timestamp": 1}),
            json.dumps({"type": "step_finish", "timestamp": 2}),
        ]
    )
    second = json.dumps({"chapter_title": "Retry Chapter", "draft_text": "# Chapter 1 — Retry Chapter\n\nProse."})
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **_kwargs: object) -> str:
        calls.append(cmd)
        return telemetry if len(calls) == 1 else second

    monkeypatch.setattr("inkforge_loop.adapters._run_command", fake_run)
    adapter = CliAgentAdapter(run_root=Path("."), writer_agent="build", critic_model="sonnet", reviser_model="gpt-5")
    result = adapter.writer("write")

    assert len(calls) == 2
    assert "--format" in calls[0]
    assert "--format" not in calls[1]
    assert result.chapter_title == "Retry Chapter"
    assert "Prose." in result.draft_text


@pytest.mark.unit
def test_writer_raises_when_both_modes_return_telemetry(monkeypatch: pytest.MonkeyPatch) -> None:
    telemetry = "\n".join(
        [
            json.dumps({"type": "step_start", "timestamp": 1}),
            json.dumps({"type": "step_finish", "timestamp": 2}),
        ]
    )

    monkeypatch.setattr("inkforge_loop.adapters._run_command", lambda *_args, **_kwargs: telemetry)
    adapter = CliAgentAdapter(run_root=Path("."), writer_agent="build", critic_model="sonnet", reviser_model="gpt-5")

    with pytest.raises(AgentInvocationError, match="event telemetry"):
        adapter.writer("write")


@pytest.mark.unit
def test_writer_rejects_non_draft_text(monkeypatch: pytest.MonkeyPatch) -> None:
    outputs = [
        json.dumps({"type": "step_finish", "timestamp": 1}),
        "I need more information before I can draft this chapter.",
    ]
    calls = {"n": 0}

    def fake_run(*_args: object, **_kwargs: object) -> str:
        idx = calls["n"]
        calls["n"] += 1
        return outputs[idx]

    monkeypatch.setattr("inkforge_loop.adapters._run_command", fake_run)
    adapter = CliAgentAdapter(run_root=Path("."), writer_agent="build", critic_model="sonnet", reviser_model="gpt-5")

    with pytest.raises(AgentInvocationError, match="resemble a chapter draft"):
        adapter.writer("write")


@pytest.mark.unit
def test_writer_accepts_plain_markdown_chapter(monkeypatch: pytest.MonkeyPatch) -> None:
    chapter = "# Chapter 2 — A Plain Draft\n\nThis is a direct markdown draft response.\n"
    monkeypatch.setattr("inkforge_loop.adapters._run_command", lambda *_args, **_kwargs: chapter)
    adapter = CliAgentAdapter(run_root=Path("."), writer_agent="build", critic_model="sonnet", reviser_model="gpt-5")

    result = adapter.writer("write")
    assert result.chapter_title == "A Plain Draft"
    assert "direct markdown draft" in result.draft_text
