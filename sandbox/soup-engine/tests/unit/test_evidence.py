from __future__ import annotations

import unittest

from sopilot_rules.evidence import build_evidence_refs
from sopilot_rules.schema import Detection, Event, StepResult


class EvidenceTests(unittest.TestCase):
    def test_build_evidence_refs_prefers_highest_confidence_detection(self):
        detections = [
            Detection(
                id="low",
                frame_id="frame_1",
                timestamp_sec=1,
                tag="cuff",
                confidence=0.6,
                bbox={"x1": 0, "y1": 0, "x2": 10, "y2": 10},
            ),
            Detection(
                id="high",
                frame_id="frame_2",
                timestamp_sec=2,
                tag="cuff",
                confidence=0.9,
                bbox={"x1": 0, "y1": 0, "x2": 10, "y2": 10},
            ),
        ]
        step = StepResult(
            step_id="S2",
            rule_id="rule",
            status="passed",
            message="ok",
            evidence_refs=["low", "high"],
        )
        evidence = build_evidence_refs([step], detections, [])
        self.assertEqual(evidence[0].frame_id, "frame_2")

    def test_build_evidence_refs_can_use_event_only(self):
        event = Event(id="evt", type="measure_started", timestamp_sec=5)
        step = StepResult(
            step_id="S3",
            rule_id="rule",
            status="uncertain",
            message="missing",
            evidence_refs=["evt"],
        )
        evidence = build_evidence_refs([step], [], [event])
        self.assertEqual(evidence[0].timestamp_sec, 5)
        self.assertEqual(evidence[0].event_ids, ["evt"])


if __name__ == "__main__":
    unittest.main()
