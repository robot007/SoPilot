"""Evaluator for overlap rules."""

from __future__ import annotations

from sopilot_rules.geometry import overlap_ratio
from sopilot_rules.schema import OverlapRule

from .base import (
    EvaluationContext,
    best_detection,
    detections_for_tag,
    low_confidence_detections,
    make_result,
    ref_id,
    same_frame_pairs,
)


def evaluate_overlap(rule: OverlapRule, context: EvaluationContext):
    sources = detections_for_tag(context.detections, rule.source_tag, rule.min_confidence)
    targets = detections_for_tag(context.detections, rule.target_tag, rule.min_confidence)
    pairs = same_frame_pairs(sources, targets)

    if pairs:
        scored = sorted(
            [
                (overlap_ratio(source.bbox, target.bbox), source, target)
                for source, target in pairs
            ],
            key=lambda item: (
                -item[0],
                -min(item[1].confidence, item[2].confidence),
                item[1].timestamp_sec,
                item[1].id or "",
                item[2].id or "",
            ),
        )
        ratio, source, target = scored[0]
        if ratio >= rule.min_overlap_ratio:
            status = "passed"
            message = "%s overlapped %s." % (rule.source_tag, rule.target_tag)
        elif ratio >= rule.min_overlap_ratio - rule.ambiguity_margin_ratio:
            status = "uncertain"
            message = "Overlap between %s and %s was borderline." % (
                rule.source_tag,
                rule.target_tag,
            )
        else:
            status = "failed"
            message = rule.failure_message

        return make_result(
            rule,
            status,
            message,
            evidence_refs=[ref_id(source), ref_id(target)],
            confidence=min(source.confidence, target.confidence),
            completed_at_sec=max(source.timestamp_sec, target.timestamp_sec),
            trace={
                "summary": "overlap_checked",
                "overlap_ratio": ratio,
                "min_overlap_ratio": rule.min_overlap_ratio,
                "source_tag": rule.source_tag,
                "target_tag": rule.target_tag,
            },
        )

    low_source = low_confidence_detections(context.detections, rule.source_tag, rule.min_confidence)
    low_target = low_confidence_detections(context.detections, rule.target_tag, rule.min_confidence)
    if low_source or low_target or not sources or not targets:
        source = best_detection(low_source or sources)
        target = best_detection(low_target or targets)
        refs = [ref_id(item) for item in (source, target) if item is not None]
        confidence_values = [item.confidence for item in (source, target) if item is not None]
        confidence = min(confidence_values) if confidence_values else None
        return make_result(
            rule,
            "uncertain",
            "Overlap evidence was missing or low confidence.",
            evidence_refs=refs,
            confidence=confidence,
            trace={
                "summary": "missing_or_low_confidence_overlap_evidence",
                "source_tag": rule.source_tag,
                "target_tag": rule.target_tag,
            },
        )

    return make_result(
        rule,
        "failed",
        rule.failure_message,
        trace={"summary": "no_overlap_pair_found"},
    )
