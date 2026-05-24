from __future__ import annotations

import unittest

from sopilot_rules.rules.after_all_required import evaluate_after_all_required
from sopilot_rules.rules.base import EvaluationContext
from sopilot_rules.schema import AfterAllRequiredRule, Event, StepResult


class AfterAllRequiredRuleTests(unittest.TestCase):
    def rule(self):
        return AfterAllRequiredRule(
            id="after",
            step_id="S3",
            type="after_all_required",
            event="measure_started",
            required_steps=["S1", "S2"],
        )

    def step(self, step_id, status="passed", completed_at=1):
        return StepResult(
            step_id=step_id,
            rule_id="rule_%s" % step_id,
            status=status,
            message="ok",
            completed_at_sec=completed_at,
        )

    def test_passes_when_all_required_steps_pass_before_event(self):
        result = evaluate_after_all_required(
            self.rule(),
            EvaluationContext(
                detections=[],
                events=[Event(id="measure", type="measure_started", timestamp_sec=5)],
                prior_results={
                    "S1": self.step("S1", completed_at=1),
                    "S2": self.step("S2", completed_at=2),
                },
            ),
        )
        self.assertEqual(result.status, "passed")

    def test_fails_when_required_step_failed(self):
        result = evaluate_after_all_required(
            self.rule(),
            EvaluationContext(
                detections=[],
                events=[Event(id="measure", type="measure_started", timestamp_sec=5)],
                prior_results={"S1": self.step("S1", "failed"), "S2": self.step("S2")},
            ),
        )
        self.assertEqual(result.status, "failed")

    def test_fails_when_required_step_completed_after_event(self):
        result = evaluate_after_all_required(
            self.rule(),
            EvaluationContext(
                detections=[],
                events=[Event(id="measure", type="measure_started", timestamp_sec=5)],
                prior_results={"S1": self.step("S1", completed_at=7), "S2": self.step("S2")},
            ),
        )
        self.assertEqual(result.status, "failed")

    def test_uncertain_when_required_step_uncertain(self):
        result = evaluate_after_all_required(
            self.rule(),
            EvaluationContext(
                detections=[],
                events=[Event(id="measure", type="measure_started", timestamp_sec=5)],
                prior_results={"S1": self.step("S1", "uncertain"), "S2": self.step("S2")},
            ),
        )
        self.assertEqual(result.status, "uncertain")

    def test_uncertain_when_event_missing(self):
        result = evaluate_after_all_required(
            self.rule(),
            EvaluationContext(
                detections=[],
                events=[],
                prior_results={"S1": self.step("S1"), "S2": self.step("S2")},
            ),
        )
        self.assertEqual(result.status, "uncertain")


if __name__ == "__main__":
    unittest.main()
