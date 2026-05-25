"""Evaluator for above rules."""

from __future__ import annotations

from sopilot_rules.geometry import above_with_margin, vertical_delta_px
from sopilot_rules.schema import AboveRule

from .base import (
    EvaluationContext,
    best_detection,
    detections_for_tag,
    low_confidence_detections,
    make_result,
    ref_id,
    same_frame_pairs,
)


def evaluate_above(rule: AboveRule, context: EvaluationContext):
    sources = detections_for_tag(context.detections, rule.source_tag, rule.min_confidence)
    targets = detections_for_tag(context.detections, rule.target_tag, rule.min_confidence)
    pairs = same_frame_pairs(sources, targets)

    if pairs:
        scored = []
        rank = {"passed": 0, "uncertain": 1, "failed": 2}
        for source, target in pairs:
            status = above_with_margin(
                source.bbox,
                target.bbox,
                margin_px=rule.margin_px,
                ambiguity_margin_px=rule.ambiguity_margin_px,
            )
            delta = vertical_delta_px(source.bbox, target.bbox)
            scored.append((rank[status], -delta, status, delta, source, target))
        scored.sort(
            key=lambda item: (
                item[0],
                item[1],
                item[4].timestamp_sec,
                item[4].id or "",
                item[5].id or "",
            )
        )
        _, _, status, delta, source, target = scored[0]

        if status == "passed":
            message = "%s was above %s." % (rule.source_tag, rule.target_tag)
        elif status == "uncertain":
            message = "Vertical relation between %s and %s was borderline." % (
                rule.source_tag,
                rule.target_tag,
            )
        else:
            message = rule.failure_message

        return make_result(
            rule,
            status,
            message,
            evidence_refs=[ref_id(source), ref_id(target)],
            confidence=min(source.confidence, target.confidence),
            completed_at_sec=max(source.timestamp_sec, target.timestamp_sec),
            trace={
                "summary": "vertical_relation_checked",
                "delta_px": delta,
                "margin_px": rule.margin_px,
                "ambiguity_margin_px": rule.ambiguity_margin_px,
                "source_tag": rule.source_tag,
                "target_tag": rule.target_tag,
            },
        )

    low_source = low_confidence_detections(context.detections, rule.source_tag, rule.min_confidence)
    low_target = low_confidence_detections(context.detections, rule.target_tag, rule.min_confidence)
    source = best_detection(low_source or sources)
    target = best_detection(low_target or targets)
    refs = [ref_id(item) for item in (source, target) if item is not None]
    confidence_values = [item.confidence for item in (source, target) if item is not None]
    confidence = min(confidence_values) if confidence_values else None
    return make_result(
        rule,
        "uncertain",
        "Vertical relation evidence was missing or low confidence.",
        evidence_refs=refs,
        confidence=confidence,
        trace={
            "summary": "missing_or_low_confidence_vertical_evidence",
            "source_tag": rule.source_tag,
            "target_tag": rule.target_tag,
        },
    )
