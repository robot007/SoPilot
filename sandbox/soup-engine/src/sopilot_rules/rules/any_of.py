"""Evaluator for any_of composite rules."""

from __future__ import annotations

from typing import Iterable, List

from sopilot_rules.schema import AnyOfRule

from .base import EvaluationContext, make_result
from .conditions import ConditionResult, evaluate_condition


def evaluate_any_of(rule: AnyOfRule, context: EvaluationContext):
    child_results = [evaluate_condition(condition, context) for condition in rule.conditions]
    passed = [result for result in child_results if result.status == "passed"]
    uncertain = [result for result in child_results if result.status == "uncertain"]

    if passed:
        selected = _select_passing_condition(passed)
        return make_result(
            rule,
            "passed",
            "At least one condition passed for %s." % rule.step_id,
            evidence_refs=selected.evidence_refs,
            confidence=selected.confidence,
            completed_at_sec=selected.completed_at_sec,
            trace=_trace(rule, child_results, selected.condition_id),
        )

    if uncertain:
        return make_result(
            rule,
            "uncertain",
            "No condition passed, and at least one condition was uncertain.",
            evidence_refs=_dedupe_refs(result.evidence_refs for result in child_results),
            confidence=_min_confidence(child_results),
            trace=_trace(rule, child_results),
        )

    return make_result(
        rule,
        "failed",
        rule.failure_message,
        evidence_refs=_dedupe_refs(result.evidence_refs for result in child_results),
        confidence=_min_confidence(child_results),
        trace=_trace(rule, child_results),
    )


def _select_passing_condition(results: List[ConditionResult]) -> ConditionResult:
    return sorted(
        results,
        key=lambda item: (
            item.completed_at_sec is None,
            item.completed_at_sec if item.completed_at_sec is not None else 0.0,
            item.condition_id,
        ),
    )[0]


def _trace(rule: AnyOfRule, results: List[ConditionResult], selected_id=None):
    return {
        "summary": "any_of_evaluated",
        "rule_id": rule.id,
        "selected_condition_id": selected_id,
        "conditions": [
            {
                "condition_id": result.condition_id,
                "status": result.status,
                "message": result.message,
                "trace": result.trace,
            }
            for result in results
        ],
    }


def _dedupe_refs(groups: Iterable[List[str]]) -> List[str]:
    refs = []
    seen = set()
    for group in groups:
        for ref in group:
            if ref and ref not in seen:
                seen.add(ref)
                refs.append(ref)
    return refs


def _min_confidence(results: List[ConditionResult]):
    values = [result.confidence for result in results if result.confidence is not None]
    return min(values) if values else None
