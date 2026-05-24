"""Input normalization helpers."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Union

from .schema import Detection, Event


def normalize_detections(records: Iterable[Union[Detection, Dict[str, Any]]]) -> List[Detection]:
    detections = []
    for index, record in enumerate(records):
        detection = record if isinstance(record, Detection) else Detection.model_validate(record)
        if detection.id is None:
            detection = detection.model_copy(update={"id": "det_%04d" % index})
        detections.append(detection)
    return sorted(detections, key=lambda item: (item.timestamp_sec, item.frame_id, item.tag, item.id or ""))


def normalize_events(records: Iterable[Union[Event, Dict[str, Any]]]) -> List[Event]:
    events = []
    for index, record in enumerate(records):
        event = record if isinstance(record, Event) else Event.model_validate(record)
        if event.id is None:
            event = event.model_copy(update={"id": "evt_%04d" % index})
        events.append(event)
    return sorted(events, key=lambda item: (item.timestamp_sec, item.type, item.id or ""))
