"""Evaluator for after_all_required rules."""

from __future__ import annotations

from sopilot_rules.schema import AfterAllRequiredRule

from .base import EvaluationContext, first_event, make_result, ref_id


def evaluate_after_all_required(rule: AfterAllRequiredRule, context: EvaluationContext):
    event = first_event(context.events, rule.event)
    if event is None:
        return make_result(
            rule,
            "uncertain",
            "Event %s was not observed." % rule.event,
            trace={"summary": "missing_event", "event": rule.event},
        )

    failed = []
    uncertain = []
    late = []
    refs = [ref_id(event)]

    for step_id in rule.required_steps:
        step = context.prior_results.get(step_id)
        if step is None:
            uncertain.append(step_id)
            continue
        refs.extend(step.evidence_refs)
        if step.status == "failed":
            failed.append(step_id)
        elif step.status != "passed":
            uncertain.append(step_id)
        elif step.completed_at_sec is not None and step.completed_at_sec > event.timestamp_sec:
            late.append(step_id)

    if failed or late:
        return make_result(
            rule,
            "failed",
            rule.failure_message,
            evidence_refs=_dedupe(refs),
            completed_at_sec=event.timestamp_sec,
            trace={
                "summary": "required_steps_failed_or_late",
                "failed_steps": failed,
                "late_steps": late,
                "event": rule.event,
            },
        )

    if uncertain:
        return make_result(
            rule,
            "uncertain",
            "Required setup steps were uncertain before %s." % rule.event,
            evidence_refs=_dedupe(refs),
            completed_at_sec=event.timestamp_sec,
            trace={
                "summary": "required_steps_uncertain",
                "uncertain_steps": uncertain,
                "event": rule.event,
            },
        )

    return make_result(
        rule,
        "passed",
        "%s occurred after all required steps." % rule.event,
        evidence_refs=_dedupe(refs),
        completed_at_sec=event.timestamp_sec,
        trace={"summary": "event_after_all_required_steps", "event": rule.event},
    )


def _dedupe(values):
    result = []
    seen = set()
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
