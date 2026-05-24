from __future__ import annotations

import unittest

from sopilot_rules.rules.base import EvaluationContext
from sopilot_rules.rules.exists_before import evaluate_exists_before
from sopilot_rules.schema import Detection, Event, ExistsBeforeRule


def det(tag, confidence=0.9, timestamp=1.0):
    return Detection(
        id="%s_%s" % (tag, timestamp),
        frame_id="frame_%s" % timestamp,
        timestamp_sec=timestamp,
        tag=tag,
        confidence=confidence,
        bbox={"x1": 0, "y1": 0, "x2": 10, "y2": 10},
    )


class ExistsBeforeRuleTests(unittest.TestCase):
    def rule(self):
        return ExistsBeforeRule(
            id="exists",
            step_id="monitor_visible",
            type="exists_before",
            tag="blood_pressure_monitor",
            event="measure_started",
        )

    def test_passes_when_detection_exists_before_event(self):
        result = evaluate_exists_before(
            self.rule(),
            EvaluationContext(
                detections=[det("blood_pressure_monitor", timestamp=1)],
                events=[Event(id="measure", type="measure_started", timestamp_sec=2)],
                prior_results={},
            ),
        )
        self.assertEqual(result.status, "passed")

    def test_fails_when_detection_missing_before_event(self):
        result = evaluate_exists_before(
            self.rule(),
            EvaluationContext(
                detections=[det("blood_pressure_monitor", timestamp=3)],
                events=[Event(id="measure", type="measure_started", timestamp_sec=2)],
                prior_results={},
            ),
        )
        self.assertEqual(result.status, "failed")

    def test_uncertain_when_only_low_confidence_detection_exists(self):
        result = evaluate_exists_before(
            self.rule(),
            EvaluationContext(
                detections=[det("blood_pressure_monitor", confidence=0.2, timestamp=1)],
                events=[Event(id="measure", type="measure_started", timestamp_sec=2)],
                prior_results={},
            ),
        )
        self.assertEqual(result.status, "uncertain")

    def test_uncertain_when_event_missing(self):
        result = evaluate_exists_before(
            self.rule(),
            EvaluationContext(
                detections=[det("blood_pressure_monitor", timestamp=1)],
                events=[],
                prior_results={},
            ),
        )
        self.assertEqual(result.status, "uncertain")


if __name__ == "__main__":
    unittest.main()
