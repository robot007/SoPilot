from __future__ import annotations

import unittest

from sopilot_rules.events import build_measure_started_events, dedupe_events, first_event
from sopilot_rules.schema import Detection, Event


class EventTests(unittest.TestCase):
    def test_dedupe_events_removes_duplicate_id(self):
        events = [
            Event(id="evt", type="measure_started", timestamp_sec=2),
            Event(id="evt", type="measure_started", timestamp_sec=3),
        ]
        self.assertEqual(len(dedupe_events(events)), 1)

    def test_first_event_returns_earliest_matching_event(self):
        events = [
            Event(id="late", type="measure_started", timestamp_sec=5),
            Event(id="early", type="measure_started", timestamp_sec=1),
        ]
        self.assertEqual(first_event(events, "measure_started").id, "early")

    def test_build_measure_started_events_from_monitor_detection(self):
        detections = [
            Detection(
                id="monitor",
                frame_id="frame",
                timestamp_sec=3,
                tag="blood_pressure_monitor",
                confidence=0.8,
                bbox={"x1": 0, "y1": 0, "x2": 10, "y2": 10},
            )
        ]
        events = build_measure_started_events(detections)
        self.assertEqual(events[0].type, "measure_started")
        self.assertEqual(events[0].timestamp_sec, 3)


if __name__ == "__main__":
    unittest.main()
