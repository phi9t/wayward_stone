from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QualityResult:
    passed: bool
    reasons: list[str]


def evaluate_quality_gate(
    invariant_violations: list[str],
    overall_score: float,
    category_scores: dict[str, float],
    overall_min: float,
    category_min: float,
) -> QualityResult:
    reasons: list[str] = []
    if invariant_violations:
        reasons.append("invariant_violations")
    if overall_score < overall_min:
        reasons.append(f"overall_score<{overall_min}")
    low_categories = [k for k, v in category_scores.items() if v < category_min]
    if low_categories:
        reasons.append(f"low_categories:{','.join(sorted(low_categories))}")
    return QualityResult(passed=not reasons, reasons=reasons)
