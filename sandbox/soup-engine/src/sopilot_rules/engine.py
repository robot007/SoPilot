"""Deterministic SOUP rule engine."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Union

from .evidence import build_evidence_refs
from .normalizer import normalize_detections, normalize_events
from .privacy import build_privacy_log
from .rules import evaluate_rule
from .rules.base import EvaluationContext
from .schema import Detection, Event, RunResult, SoupPackage, StepResult


class RuleEngine:
    """Evaluate a SOUP package against detections and scene events."""

    def __init__(self, soup: Union[SoupPackage, Dict[str, Any]]):
        self.soup = soup if isinstance(soup, SoupPackage) else SoupPackage.model_validate(soup)
        self._step_order = {step.id: step.order for step in self.soup.steps}

    def evaluate(
        self,
        detections: Iterable[Union[Detection, Dict[str, Any]]],
        events: Iterable[Union[Event, Dict[str, Any]]],
        run_id: Optional[str] = None,
    ) -> RunResult:
        normalized_detections = normalize_detections(detections)
        normalized_events = normalize_events(events)

        prior_results: Dict[str, StepResult] = {}
        step_results: List[StepResult] = []

        for rule in self._evaluation_order():
            context = EvaluationContext(
                detections=normalized_detections,
                events=normalized_events,
                prior_results=dict(prior_results),
            )
            result = evaluate_rule(rule, context)
            prior_results[result.step_id] = result
            step_results.append(result)

        step_results = self._add_missing_required_steps(step_results)
        step_results = sorted(
            step_results,
            key=lambda item: (self._step_order.get(item.step_id, 9999), item.rule_id),
        )

        status = self._overall_status(step_results)
        sources = [detection.source for detection in normalized_detections]
        sources.extend(event.source for event in normalized_events)

        decision_trace = [
            {
                "step_id": step.step_id,
                "rule_id": step.rule_id,
                "status": step.status,
                "message": step.message,
            }
            for step in step_results
        ]

        return RunResult(
            run_id=run_id,
            status=status,
            steps=step_results,
            evidence=build_evidence_refs(step_results, normalized_detections, normalized_events),
            decision_trace=decision_trace,
            privacy_log=build_privacy_log(sources),
        )

    def _evaluation_order(self):
        return sorted(
            self.soup.rules,
            key=lambda rule: (
                1 if rule.type == "after_all_required" else 0,
                self._step_order.get(rule.step_id, 9999),
                rule.id,
            ),
        )

    def _add_missing_required_steps(self, step_results: List[StepResult]) -> List[StepResult]:
        by_step = {result.step_id: result for result in step_results}
        updated = list(step_results)
        for step in self.soup.steps:
            if step.required and step.id not in by_step:
                updated.append(
                    StepResult(
                        step_id=step.id,
                        rule_id="missing_rule",
                        status="skipped",
                        message="No rule produced a result for required step %s." % step.id,
                        decision_trace=[{"summary": "missing_required_step_rule"}],
                    )
                )
        return updated

    def _overall_status(self, step_results: List[StepResult]) -> str:
        by_step = {result.step_id: result for result in step_results}
        required_ids = [step.id for step in self.soup.steps if step.required]
        required_results = [by_step.get(step_id) for step_id in required_ids]

        if any(result is None or result.status == "failed" for result in required_results):
            return "failed"
        if any(result.status in ("uncertain", "skipped") for result in required_results):
            return "needs_review"
        return "passed"
