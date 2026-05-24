"""Shared rule evaluation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from sopilot_rules.schema import Detection, Event, Rule, StepResult


@dataclass(frozen=True)
class EvaluationContext:
    detections: List[Detection]
    events: List[Event]
    prior_results: Dict[str, StepResult]


def make_result(
    rule: Rule,
    status: str,
    message: str,
    evidence_refs: Optional[List[str]] = None,
    confidence: Optional[float] = None,
    trace: Optional[Dict[str, Any]] = None,
    completed_at_sec: Optional[float] = None,
) -> StepResult:
    return StepResult(
        step_id=rule.step_id,
        rule_id=rule.id,
        status=status,
        message=message,
        confidence=confidence,
        evidence_refs=evidence_refs or [],
        decision_trace=[trace or {"summary": message, "status": status}],
        completed_at_sec=completed_at_sec,
    )


def first_event(events: Sequence[Event], event_type: str) -> Optional[Event]:
    for event in sorted(events, key=lambda item: (item.timestamp_sec, item.type, item.id or "")):
        if event.type == event_type:
            return event
    return None


def detections_for_tag(
    detections: Iterable[Detection],
    tag: str,
    min_confidence: Optional[float] = None,
    before_sec: Optional[float] = None,
) -> List[Detection]:
    matches = []
    for detection in detections:
        if detection.tag != tag:
            continue
        if before_sec is not None and detection.timestamp_sec > before_sec:
            continue
        if min_confidence is not None and detection.confidence < min_confidence:
            continue
        matches.append(detection)
    return sort_detections(matches)


def low_confidence_detections(
    detections: Iterable[Detection],
    tag: str,
    min_confidence: float,
    before_sec: Optional[float] = None,
) -> List[Detection]:
    matches = []
    for detection in detections:
        if detection.tag != tag:
            continue
        if before_sec is not None and detection.timestamp_sec > before_sec:
            continue
        if detection.confidence < min_confidence:
            matches.append(detection)
    return sort_detections(matches)


def best_detection(detections: Iterable[Detection]) -> Optional[Detection]:
    sorted_detections = sort_detections(detections)
    return sorted_detections[0] if sorted_detections else None


def sort_detections(detections: Iterable[Detection]) -> List[Detection]:
    return sorted(
        detections,
        key=lambda item: (-item.confidence, item.timestamp_sec, item.frame_id, item.tag, item.id or ""),
    )


def same_frame_pairs(
    sources: Iterable[Detection],
    targets: Iterable[Detection],
) -> List[Tuple[Detection, Detection]]:
    pairs = []
    target_by_frame: Dict[str, List[Detection]] = {}
    for target in targets:
        target_by_frame.setdefault(target.frame_id, []).append(target)
    for source in sources:
        for target in target_by_frame.get(source.frame_id, []):
            pairs.append((source, target))
    return pairs


def ref_id(item: object) -> str:
    value = getattr(item, "id", None)
    return value or ""
