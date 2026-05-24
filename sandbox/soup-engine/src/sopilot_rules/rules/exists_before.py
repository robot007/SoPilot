"""Evaluator for exists_before rules."""

from __future__ import annotations

from sopilot_rules.schema import ExistsBeforeRule

from .base import (
    EvaluationContext,
    best_detection,
    detections_for_tag,
    first_event,
    low_confidence_detections,
    make_result,
    ref_id,
)


def evaluate_exists_before(rule: ExistsBeforeRule, context: EvaluationContext):
    event = first_event(context.events, rule.event)
    if event is None:
        candidate = best_detection(detections_for_tag(context.detections, rule.tag))
        refs = [ref_id(candidate)] if candidate is not None else []
        return make_result(
            rule,
            "uncertain",
            "Event %s was not observed." % rule.event,
            evidence_refs=refs,
            trace={"summary": "missing_event", "event": rule.event},
        )

    high = detections_for_tag(
        context.detections,
        rule.tag,
        min_confidence=rule.min_confidence,
        before_sec=event.timestamp_sec,
    )
    if high:
        best = best_detection(high)
        return make_result(
            rule,
            "passed",
            "Detected %s before %s." % (rule.tag, rule.event),
            evidence_refs=[ref_id(best), ref_id(event)],
            confidence=best.confidence,
            completed_at_sec=best.timestamp_sec,
            trace={
                "summary": "tag_detected_before_event",
                "tag": rule.tag,
                "event": rule.event,
                "confidence": best.confidence,
            },
        )

    low = low_confidence_detections(
        context.detections,
        rule.tag,
        min_confidence=rule.min_confidence,
        before_sec=event.timestamp_sec,
    )
    if low:
        best = best_detection(low)
        return make_result(
            rule,
            "uncertain",
            "Only low-confidence %s evidence was observed before %s." % (rule.tag, rule.event),
            evidence_refs=[ref_id(best), ref_id(event)],
            confidence=best.confidence,
            completed_at_sec=best.timestamp_sec,
            trace={
                "summary": "low_confidence_tag_before_event",
                "tag": rule.tag,
                "event": rule.event,
                "confidence": best.confidence,
                "threshold": rule.min_confidence,
            },
        )

    return make_result(
        rule,
        "failed",
        rule.failure_message,
        evidence_refs=[ref_id(event)],
        trace={"summary": "tag_missing_before_event", "tag": rule.tag, "event": rule.event},
    )
