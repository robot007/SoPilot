"""Scene event helpers."""

from __future__ import annotations

from typing import Iterable, List, Optional

from .normalizer import normalize_events
from .schema import Detection, Event


def dedupe_events(events: Iterable[Event]) -> List[Event]:
    """Return stable, timestamp-sorted events with duplicate IDs removed."""

    normalized = normalize_events(events)
    seen = set()
    deduped = []
    for event in normalized:
        key = event.id or "%s:%s" % (event.type, event.timestamp_sec)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(event)
    return deduped


def first_event(events: Iterable[Event], event_type: str) -> Optional[Event]:
    for event in dedupe_events(events):
        if event.type == event_type:
            return event
    return None


def build_measure_started_events(
    detections: Iterable[Detection],
    trigger_tag: str = "blood_pressure_monitor",
    min_confidence: float = 0.5,
) -> List[Event]:
    """Minimal detector-derived measure event builder for future app integration.

    The current BP fixtures pass explicit events. This helper exists so the
    event-builder contract is testable without introducing YOLO or VLM deps.
    """

    best_trigger = None
    for detection in detections:
        if detection.tag == trigger_tag and detection.confidence >= min_confidence:
            if best_trigger is None or detection.timestamp_sec < best_trigger.timestamp_sec:
                best_trigger = detection

    if best_trigger is None:
        return []

    return [
        Event(
            id="evt_measure_started",
            type="measure_started",
            timestamp_sec=best_trigger.timestamp_sec,
            confidence=best_trigger.confidence,
            source="detector_event_builder",
            evidence_refs=[best_trigger.id or ""],
            metadata={"trigger_tag": trigger_tag},
        )
    ]
