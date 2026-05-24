from __future__ import annotations

import unittest

from sopilot_rules.rules.base import EvaluationContext
from sopilot_rules.rules.near_before import evaluate_near_before
from sopilot_rules.schema import Detection, Event, NearBeforeRule


def det(tag, x1, y1, x2, y2, confidence=0.9, timestamp=1.0, frame="frame"):
    return Detection(
        id="%s_%s" % (tag, x1),
        frame_id=frame,
        timestamp_sec=timestamp,
        tag=tag,
        confidence=confidence,
        bbox={"x1": x1, "y1": y1, "x2": x2, "y2": y2},
    )


class NearBeforeRuleTests(unittest.TestCase):
    def rule(self):
        return NearBeforeRule(
            id="near",
            step_id="S1",
            type="near_before",
            source_tag="sleeve",
            target_tag="blood_pressure_monitor",
            event="measure_started",
            max_distance_px=50,
        )

    def test_passes_when_pair_is_near_before_event(self):
        result = evaluate_near_before(
            self.rule(),
            EvaluationContext(
                detections=[
                    det("blood_pressure_monitor", 0, 0, 20, 20),
                    det("sleeve", 20, 0, 40, 20),
                ],
                events=[Event(id="measure", type="measure_started", timestamp_sec=2)],
                prior_results={},
            ),
        )
        self.assertEqual(result.status, "passed")

    def test_fails_when_pair_is_far(self):
        result = evaluate_near_before(
            self.rule(),
            EvaluationContext(
                detections=[
                    det("blood_pressure_monitor", 0, 0, 20, 20),
                    det("sleeve", 200, 0, 220, 20),
                ],
                events=[Event(id="measure", type="measure_started", timestamp_sec=2)],
                prior_results={},
            ),
        )
        self.assertEqual(result.status, "failed")

    def test_uncertain_when_low_confidence_pair(self):
        result = evaluate_near_before(
            self.rule(),
            EvaluationContext(
                detections=[
                    det("blood_pressure_monitor", 0, 0, 20, 20),
                    det("sleeve", 20, 0, 40, 20, confidence=0.2),
                ],
                events=[Event(id="measure", type="measure_started", timestamp_sec=2)],
                prior_results={},
            ),
        )
        self.assertEqual(result.status, "uncertain")

    def test_uncertain_when_event_missing(self):
        result = evaluate_near_before(
            self.rule(),
            EvaluationContext(
                detections=[
                    det("blood_pressure_monitor", 0, 0, 20, 20),
                    det("sleeve", 20, 0, 40, 20),
                ],
                events=[],
                prior_results={},
            ),
        )
        self.assertEqual(result.status, "uncertain")


if __name__ == "__main__":
    unittest.main()
