"""Evidence reference generation."""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from .schema import Detection, Event, EvidenceRef, StepResult


def build_evidence_refs(
    step_results: Iterable[StepResult],
    detections: Iterable[Detection],
    events: Iterable[Event],
) -> List[EvidenceRef]:
    detection_by_id: Dict[str, Detection] = {
        detection.id: detection for detection in detections if detection.id is not None
    }
    event_by_id: Dict[str, Event] = {event.id: event for event in events if event.id is not None}

    evidence = []
    for index, step in enumerate(step_results):
        detection_ids = [ref for ref in step.evidence_refs if ref in detection_by_id]
        event_ids = [ref for ref in step.evidence_refs if ref in event_by_id]

        selected_detection = _select_detection([detection_by_id[ref] for ref in detection_ids])
        selected_event = _select_event([event_by_id[ref] for ref in event_ids])

        timestamp = None
        if selected_detection is not None:
            timestamp = selected_detection.timestamp_sec
        elif selected_event is not None:
            timestamp = selected_event.timestamp_sec

        reason = step.message
        if step.decision_trace:
            reason = str(step.decision_trace[0].get("summary", step.message))

        evidence.append(
            EvidenceRef(
                id="ev_%04d" % index,
                step_id=step.step_id,
                rule_id=step.rule_id,
                frame_id=selected_detection.frame_id if selected_detection is not None else None,
                timestamp_sec=timestamp,
                detection_ids=detection_ids,
                event_ids=event_ids,
                reason=reason,
            )
        )
    return evidence


def _select_detection(detections: List[Detection]) -> Optional[Detection]:
    if not detections:
        return None
    return sorted(
        detections,
        key=lambda item: (-item.confidence, item.timestamp_sec, item.frame_id, item.id or ""),
    )[0]


def _select_event(events: List[Event]) -> Optional[Event]:
    if not events:
        return None
    return sorted(events, key=lambda item: (item.timestamp_sec, item.type, item.id or ""))[0]
