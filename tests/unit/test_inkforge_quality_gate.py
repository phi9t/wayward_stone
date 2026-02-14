from __future__ import annotations

import pytest

from inkforge_loop.quality import evaluate_quality_gate


@pytest.mark.unit
def test_quality_gate_passes_on_strict_thresholds() -> None:
    result = evaluate_quality_gate(
        invariant_violations=[],
        overall_score=9.1,
        category_scores={"voice": 8.4, "canon": 9.2},
        overall_min=9.0,
        category_min=8.0,
    )
    assert result.passed
    assert result.reasons == []


@pytest.mark.unit
def test_quality_gate_fails_on_invariants_and_scores() -> None:
    result = evaluate_quality_gate(
        invariant_violations=["frame_leak"],
        overall_score=8.5,
        category_scores={"voice": 7.9},
        overall_min=9.0,
        category_min=8.0,
    )
    assert not result.passed
    assert "invariant_violations" in result.reasons
    assert "overall_score<9.0" in result.reasons
