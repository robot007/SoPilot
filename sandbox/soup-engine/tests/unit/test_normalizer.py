from __future__ import annotations

import unittest

from sopilot_rules.normalizer import normalize_detections, normalize_events


class NormalizerTests(unittest.TestCase):
    def test_detection_ids_are_assigned_and_sorted(self):
        detections = normalize_detections(
            [
                {
                    "frame_id": "b",
                    "timestamp_sec": 2,
                    "tag": "cuff",
                    "confidence": 0.9,
                    "bbox": {"x1": 0, "y1": 0, "x2": 10, "y2": 10},
                },
                {
                    "frame_id": "a",
                    "timestamp_sec": 1,
                    "tag": "cuff",
                    "confidence": 0.9,
                    "bbox": {"x1": 0, "y1": 0, "x2": 10, "y2": 10},
                },
            ]
        )
        self.assertEqual([item.frame_id for item in detections], ["a", "b"])
        self.assertEqual({item.id for item in detections}, {"det_0000", "det_0001"})

    def test_event_ids_are_assigned_and_sorted(self):
        events = normalize_events(
            [
                {"type": "measure_started", "timestamp_sec": 5},
                {"type": "measure_started", "timestamp_sec": 1},
            ]
        )
        self.assertEqual([item.timestamp_sec for item in events], [1, 5])
        self.assertEqual({item.id for item in events}, {"evt_0000", "evt_0001"})


if __name__ == "__main__":
    unittest.main()
