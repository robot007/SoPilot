"""Evaluator for local VLM answer rules."""

from __future__ import annotations

from sopilot_rules.schema import VLMAnswerRule

from .base import EvaluationContext, make_result, ref_id


def evaluate_vlm_answer(rule: VLMAnswerRule, context: EvaluationContext):
    event = _last_event(context, rule.event)
    if event is None:
        return make_result(
            rule,
            "uncertain",
            "VLM answer event %s was not observed." % rule.event,
            trace={
                "summary": "missing_vlm_answer_event",
                "event": rule.event,
                "question": rule.question,
            },
        )

    if event.confidence < rule.min_confidence:
        return make_result(
            rule,
            "uncertain",
            "VLM answer confidence was below threshold.",
            evidence_refs=[ref_id(event)],
            confidence=event.confidence,
            completed_at_sec=event.timestamp_sec,
            trace={
                "summary": "low_confidence_vlm_answer",
                "event": rule.event,
                "question": rule.question,
                "confidence": event.confidence,
                "threshold": rule.min_confidence,
            },
        )

    answer = _normalize_answer(event.metadata.get(rule.answer_metadata_key))
    if answer == rule.expected_answer:
        return make_result(
            rule,
            "passed",
            "VLM answered %s for: %s" % (answer, rule.question),
            evidence_refs=[ref_id(event)],
            confidence=event.confidence,
            completed_at_sec=event.timestamp_sec,
            trace={
                "summary": "vlm_answer_matched",
                "event": rule.event,
                "question": rule.question,
                "expected_answer": rule.expected_answer,
                "observed_answer": answer,
                "answer_metadata_key": rule.answer_metadata_key,
            },
        )

    if answer in ("", "unsure", "unknown", "uncertain"):
        return make_result(
            rule,
            "uncertain",
            rule.failure_message,
            evidence_refs=[ref_id(event)],
            confidence=event.confidence,
            completed_at_sec=event.timestamp_sec,
            trace={
                "summary": "uncertain_vlm_answer",
                "event": rule.event,
                "question": rule.question,
                "expected_answer": rule.expected_answer,
                "observed_answer": answer,
                "answer_metadata_key": rule.answer_metadata_key,
            },
        )

    return make_result(
        rule,
        "failed",
        rule.failure_message,
        evidence_refs=[ref_id(event)],
        confidence=event.confidence,
        completed_at_sec=event.timestamp_sec,
        trace={
            "summary": "vlm_answer_mismatched",
            "event": rule.event,
            "question": rule.question,
            "expected_answer": rule.expected_answer,
            "observed_answer": answer,
            "answer_metadata_key": rule.answer_metadata_key,
        },
    )


def _last_event(context: EvaluationContext, event_type: str):
    matches = [event for event in context.events if event.type == event_type]
    if not matches:
        return None
    return sorted(matches, key=lambda item: (item.timestamp_sec, item.type, item.id or ""))[-1]


def _normalize_answer(value) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()
