from __future__ import annotations

import unittest

from sopilot_rules.rules.base import EvaluationContext
from sopilot_rules.rules.vlm_answer import evaluate_vlm_answer
from sopilot_rules.schema import Event, VLMAnswerRule


class VLMAnswerRuleTests(unittest.TestCase):
    def rule(self):
        return VLMAnswerRule(
            id="vlm_upper_arm",
            step_id="S1",
            type="vlm_answer",
            event="vlm_cuff_on_upper_arm_answer",
            question="Has the person put any object on upper arm?",
            expected_answer="yes",
            failure_message="The cuff was not confirmed on the upper arm.",
        )

    def event(self, answer="yes", confidence=1.0):
        return Event(
            id="evt_vlm_answer",
            type="vlm_cuff_on_upper_arm_answer",
            timestamp_sec=10,
            confidence=confidence,
            source="fastvlm_0_5b",
            metadata={"answer_normalized": answer},
        )

    def test_passes_when_vlm_answer_matches_expected(self):
        result = evaluate_vlm_answer(
            self.rule(),
            EvaluationContext(detections=[], events=[self.event("yes")], prior_results={}),
        )
        self.assertEqual(result.status, "passed")

    def test_fails_when_vlm_answer_rejects_expected(self):
        result = evaluate_vlm_answer(
            self.rule(),
            EvaluationContext(detections=[], events=[self.event("no")], prior_results={}),
        )
        self.assertEqual(result.status, "failed")

    def test_uncertain_when_vlm_answer_is_unsure(self):
        result = evaluate_vlm_answer(
            self.rule(),
            EvaluationContext(detections=[], events=[self.event("unsure")], prior_results={}),
        )
        self.assertEqual(result.status, "uncertain")

    def test_uncertain_when_vlm_event_is_missing(self):
        result = evaluate_vlm_answer(
            self.rule(),
            EvaluationContext(detections=[], events=[], prior_results={}),
        )
        self.assertEqual(result.status, "uncertain")

    def test_uncertain_when_vlm_event_is_low_confidence(self):
        result = evaluate_vlm_answer(
            self.rule(),
            EvaluationContext(detections=[], events=[self.event("yes", confidence=0.2)], prior_results={}),
        )
        self.assertEqual(result.status, "uncertain")


if __name__ == "__main__":
    unittest.main()
