"""Reusable child-condition evaluators for composite rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sopilot_rules.geometry import overlap_ratio
from sopilot_rules.schema import Condition, NotExistsCondition, OverlapCondition

from .base import (
    EvaluationContext,
    best_detection,
    detections_for_tag,
    low_confidence_detections,
    ref_id,
    same_frame_pairs,
)


@dataclass(frozen=True)
class ConditionResult:
    condition_id: str
    status: str
    message: str
    evidence_refs: List[str] = field(default_factory=list)
    confidence: Optional[float] = None
    completed_at_sec: Optional[float] = None
    trace: Dict[str, Any] = field(default_factory=dict)


def evaluate_condition(condition: Condition, context: EvaluationContext) -> ConditionResult:
    if isinstance(condition, NotExistsCondition):
        return evaluate_not_exists_condition(condition, context)
    if isinstance(condition, OverlapCondition):
        return evaluate_overlap_condition(condition, context)
    raise ValueError("unsupported condition type %s" % getattr(condition, "type", "<unknown>"))


def evaluate_not_exists_condition(
    condition: NotExistsCondition,
    context: EvaluationContext,
) -> ConditionResult:
    high = detections_for_tag(context.detections, condition.tag, condition.min_confidence)
    if high:
        best = best_detection(high)
        return ConditionResult(
            condition_id=condition.id,
            status="failed",
            message="Detected %s above confidence threshold." % condition.tag,
            evidence_refs=[ref_id(best)],
            confidence=best.confidence,
            completed_at_sec=best.timestamp_sec,
            trace={
                "summary": "tag_exists",
                "tag": condition.tag,
                "confidence": best.confidence,
                "threshold": condition.min_confidence,
            },
        )

    low = low_confidence_detections(context.detections, condition.tag, condition.min_confidence)
    if low:
        best = best_detection(low)
        return ConditionResult(
            condition_id=condition.id,
            status="uncertain",
            message="Only low-confidence %s evidence was observed." % condition.tag,
            evidence_refs=[ref_id(best)],
            confidence=best.confidence,
            completed_at_sec=best.timestamp_sec,
            trace={
                "summary": "only_low_confidence_tag_exists",
                "tag": condition.tag,
                "confidence": best.confidence,
                "threshold": condition.min_confidence,
            },
        )

    return ConditionResult(
        condition_id=condition.id,
        status="passed",
        message="No %s detection met the confidence threshold." % condition.tag,
        trace={
            "summary": "tag_not_detected",
            "tag": condition.tag,
            "threshold": condition.min_confidence,
        },
    )


def evaluate_overlap_condition(
    condition: OverlapCondition,
    context: EvaluationContext,
) -> ConditionResult:
    sources = detections_for_tag(context.detections, condition.source_tag, condition.min_confidence)
    targets = detections_for_tag(context.detections, condition.target_tag, condition.min_confidence)
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
        if ratio >= condition.min_overlap_ratio:
            status = "passed"
            message = "%s overlapped %s." % (condition.source_tag, condition.target_tag)
        elif ratio >= condition.min_overlap_ratio - condition.ambiguity_margin_ratio:
            status = "uncertain"
            message = "Overlap between %s and %s was borderline." % (
                condition.source_tag,
                condition.target_tag,
            )
        else:
            status = "failed"
            message = "%s did not overlap %s enough." % (
                condition.source_tag,
                condition.target_tag,
            )

        return ConditionResult(
            condition_id=condition.id,
            status=status,
            message=message,
            evidence_refs=[ref_id(source), ref_id(target)],
            confidence=min(source.confidence, target.confidence),
            completed_at_sec=max(source.timestamp_sec, target.timestamp_sec),
            trace={
                "summary": "condition_overlap_checked",
                "overlap_ratio": ratio,
                "min_overlap_ratio": condition.min_overlap_ratio,
                "source_tag": condition.source_tag,
                "target_tag": condition.target_tag,
            },
        )

    low_source = low_confidence_detections(
        context.detections, condition.source_tag, condition.min_confidence
    )
    low_target = low_confidence_detections(
        context.detections, condition.target_tag, condition.min_confidence
    )
    if low_source or low_target or not sources or not targets:
        source = best_detection(low_source or sources)
        target = best_detection(low_target or targets)
        refs = [ref_id(item) for item in (source, target) if item is not None]
        confidence_values = [item.confidence for item in (source, target) if item is not None]
        confidence = min(confidence_values) if confidence_values else None
        return ConditionResult(
            condition_id=condition.id,
            status="uncertain",
            message="Overlap condition evidence was missing or low confidence.",
            evidence_refs=refs,
            confidence=confidence,
            trace={
                "summary": "condition_missing_or_low_confidence_overlap_evidence",
                "source_tag": condition.source_tag,
                "target_tag": condition.target_tag,
            },
        )

    return ConditionResult(
        condition_id=condition.id,
        status="failed",
        message="%s did not overlap %s enough." % (condition.source_tag, condition.target_tag),
        trace={"summary": "condition_no_overlap_pair_found"},
    )
