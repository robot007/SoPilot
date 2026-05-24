"""Rule evaluator registry."""

from __future__ import annotations

from sopilot_rules.schema import (
    AboveRule,
    AfterAllRequiredRule,
    AnyOfRule,
    ExistsBeforeRule,
    NearBeforeRule,
    OverlapRule,
    Rule,
)

from .above import evaluate_above
from .after_all_required import evaluate_after_all_required
from .any_of import evaluate_any_of
from .base import EvaluationContext
from .exists_before import evaluate_exists_before
from .near_before import evaluate_near_before
from .overlap import evaluate_overlap


def evaluate_rule(rule: Rule, context: EvaluationContext):
    if isinstance(rule, ExistsBeforeRule):
        return evaluate_exists_before(rule, context)
    if isinstance(rule, NearBeforeRule):
        return evaluate_near_before(rule, context)
    if isinstance(rule, OverlapRule):
        return evaluate_overlap(rule, context)
    if isinstance(rule, AboveRule):
        return evaluate_above(rule, context)
    if isinstance(rule, AfterAllRequiredRule):
        return evaluate_after_all_required(rule, context)
    if isinstance(rule, AnyOfRule):
        return evaluate_any_of(rule, context)
    raise ValueError("unsupported rule type %s" % getattr(rule, "type", "<unknown>"))
