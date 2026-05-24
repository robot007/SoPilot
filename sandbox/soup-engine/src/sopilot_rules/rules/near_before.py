"""Evaluator for near_before rules."""

from __future__ import annotations

from sopilot_rules.geometry import center_distance_px
from sopilot_rules.schema import NearBeforeRule

from .base import (
    EvaluationContext,
    best_detection,
    detections_for_tag,
    first_event,
    low_confidence_detections,
    make_result,
    ref_id,
    same_frame_pairs,
)


def evaluate_near_before(rule: NearBeforeRule, context: EvaluationContext):
    event = first_event(context.events, rule.event)
    if event is None:
        return make_result(
            rule,
            "uncertain",
            "Event %s was not observed." % rule.event,
            trace={"summary": "missing_event", "event": rule.event},
        )

    sources = detections_for_tag(
        context.detections, rule.source_tag, rule.min_confidence, event.timestamp_sec
    )
    targets = detections_for_tag(
        context.detections, rule.target_tag, rule.min_confidence, event.timestamp_sec
    )
    pairs = same_frame_pairs(sources, targets)

    if pairs:
        scored = sorted(
            [(center_distance_px(source.bbox, target.bbox), source, target) for source, target in pairs],
            key=lambda item: (
                item[0],
                -min(item[1].confidence, item[2].confidence),
                item[1].timestamp_sec,
                item[1].id or "",
                item[2].id or "",
            ),
        )
        distance, source, target = scored[0]
        status = "passed" if distance <= rule.max_distance_px else "failed"
        message = (
            "%s was near %s before %s." % (rule.source_tag, rule.target_tag, rule.event)
            if status == "passed"
            else rule.failure_message
        )
        return make_result(
            rule,
            status,
            message,
            evidence_refs=[ref_id(source), ref_id(target), ref_id(event)],
            confidence=min(source.confidence, target.confidence),
            completed_at_sec=max(source.timestamp_sec, target.timestamp_sec),
            trace={
                "summary": "distance_checked",
                "distance_px": distance,
                "max_distance_px": rule.max_distance_px,
                "source_tag": rule.source_tag,
                "target_tag": rule.target_tag,
            },
        )

    low_source = low_confidence_detections(
        context.detections, rule.source_tag, rule.min_confidence, event.timestamp_sec
    )
    low_target = low_confidence_detections(
        context.detections, rule.target_tag, rule.min_confidence, event.timestamp_sec
    )
    if low_source or low_target:
        source = best_detection(low_source or sources)
        target = best_detection(low_target or targets)
        refs = [ref_id(item) for item in (source, target, event) if item is not None]
        confidence_values = [item.confidence for item in (source, target) if item is not None]
        confidence = min(confidence_values) if confidence_values else None
        return make_result(
            rule,
            "uncertain",
            "Only low-confidence proximity evidence was observed.",
            evidence_refs=refs,
            confidence=confidence,
            trace={
                "summary": "low_confidence_proximity",
                "source_tag": rule.source_tag,
                "target_tag": rule.target_tag,
            },
        )

    refs = [ref_id(event)]
    if sources:
        refs.append(ref_id(best_detection(sources)))
    if targets:
        refs.append(ref_id(best_detection(targets)))
    return make_result(
        rule,
        "failed",
        rule.failure_message,
        evidence_refs=refs,
        trace={
            "summary": "no_same_frame_pair_before_event",
            "source_count": len(sources),
            "target_count": len(targets),
        },
    )
