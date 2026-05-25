from __future__ import annotations

import unittest

from sopilot_rules.rules.base import EvaluationContext
from sopilot_rules.rules.conditions import evaluate_not_exists_condition
from sopilot_rules.schema import Detection, NotExistsCondition


def det(tag, confidence=0.9, timestamp=1.0):
    return Detection(
        id="%s_%s" % (tag, timestamp),
        frame_id="frame_%s" % timestamp,
        timestamp_sec=timestamp,
        tag=tag,
        confidence=confidence,
        bbox={"x1": 0, "y1": 0, "x2": 10, "y2": 10},
    )


class NotExistsConditionTests(unittest.TestCase):
    def condition(self):
        return NotExistsCondition(
            id="no_sleeve",
            type="not_exists",
            tag="sleeve",
            min_confidence=0.5,
        )

    def test_passes_when_tag_is_not_detected(self):
        result = evaluate_not_exists_condition(
            self.condition(),
            EvaluationContext(detections=[det("upper_arm")], events=[], prior_results={}),
        )
        self.assertEqual(result.status, "passed")
        self.assertIsNone(result.completed_at_sec)

    def test_fails_when_tag_is_detected_above_threshold(self):
        result = evaluate_not_exists_condition(
            self.condition(),
            EvaluationContext(detections=[det("sleeve", confidence=0.9)], events=[], prior_results={}),
        )
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.evidence_refs, ["sleeve_1.0"])

    def test_uncertain_when_only_low_confidence_tag_is_detected(self):
        result = evaluate_not_exists_condition(
            self.condition(),
            EvaluationContext(detections=[det("sleeve", confidence=0.3)], events=[], prior_results={}),
        )
        self.assertEqual(result.status, "uncertain")


if __name__ == "__main__":
    unittest.main()
