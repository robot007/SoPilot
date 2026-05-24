"""Pydantic schemas for SOUP rule evaluation."""

from __future__ import annotations

import json
from typing import Annotated, Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


StepStatus = Literal["passed", "failed", "uncertain", "skipped"]
RunStatus = Literal["passed", "failed", "needs_review"]


class StrictModel(BaseModel):
    """Base model with strict-ish defaults for package contracts."""

    model_config = ConfigDict(extra="forbid")


class BBox(StrictModel):
    x1: float
    y1: float
    x2: float
    y2: float

    @model_validator(mode="after")
    def validate_coordinates(self) -> "BBox":
        if self.x2 <= self.x1:
            raise ValueError("bbox.x2 must be greater than bbox.x1")
        if self.y2 <= self.y1:
            raise ValueError("bbox.y2 must be greater than bbox.y1")
        return self


class Detection(StrictModel):
    id: Optional[str] = None
    frame_id: str
    timestamp_sec: float
    tag: str
    confidence: float
    bbox: BBox
    source: str = "yolo"
    track_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp_sec")
    @classmethod
    def timestamp_must_be_non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("timestamp_sec must be non-negative")
        return value

    @field_validator("confidence")
    @classmethod
    def confidence_must_be_probability(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("confidence must be between 0 and 1")
        return value


class Event(StrictModel):
    id: Optional[str] = None
    type: str
    timestamp_sec: float
    confidence: float = 1.0
    source: str = "runtime"
    evidence_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp_sec")
    @classmethod
    def timestamp_must_be_non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("timestamp_sec must be non-negative")
        return value

    @field_validator("confidence")
    @classmethod
    def confidence_must_be_probability(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("confidence must be between 0 and 1")
        return value


class Tag(StrictModel):
    id: str
    name: str
    used_by_yolo: bool = True
    used_by_rules: bool = True


class Step(StrictModel):
    id: str
    name: str
    required: bool = True
    order: int
    ambiguity_allowed: bool = False


class PackageMetadata(StrictModel):
    id: str
    name: str
    version: str
    description: str
    safety_note: str
    category: Optional[str] = None
    creator: Optional[str] = None


class RuleBase(StrictModel):
    id: str
    step_id: str
    type: str
    min_confidence: float = 0.5
    failure_message: str = "Rule failed."

    @field_validator("min_confidence")
    @classmethod
    def min_confidence_must_be_probability(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("min_confidence must be between 0 and 1")
        return value


class ConditionBase(StrictModel):
    id: str
    type: str
    min_confidence: float = 0.5

    @field_validator("min_confidence")
    @classmethod
    def min_confidence_must_be_probability(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("min_confidence must be between 0 and 1")
        return value


class NotExistsCondition(ConditionBase):
    type: Literal["not_exists"]
    tag: str


class OverlapCondition(ConditionBase):
    type: Literal["overlap"]
    source_tag: str
    target_tag: str
    min_overlap_ratio: float
    ambiguity_margin_ratio: float = 0.05

    @field_validator("min_overlap_ratio", "ambiguity_margin_ratio")
    @classmethod
    def ratio_must_be_probability(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("overlap ratios must be between 0 and 1")
        return value


Condition = Annotated[
    Union[NotExistsCondition, OverlapCondition],
    Field(discriminator="type"),
]


class ExistsBeforeRule(RuleBase):
    type: Literal["exists_before"]
    tag: str
    event: str


class NearBeforeRule(RuleBase):
    type: Literal["near_before"]
    source_tag: str
    target_tag: str
    event: str
    max_distance_px: float

    @field_validator("max_distance_px")
    @classmethod
    def max_distance_must_be_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("max_distance_px must be positive")
        return value


class OverlapRule(RuleBase):
    type: Literal["overlap"]
    source_tag: str
    target_tag: str
    min_overlap_ratio: float
    ambiguity_margin_ratio: float = 0.05

    @field_validator("min_overlap_ratio", "ambiguity_margin_ratio")
    @classmethod
    def ratio_must_be_probability(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("overlap ratios must be between 0 and 1")
        return value


class AboveRule(RuleBase):
    type: Literal["above"]
    source_tag: str
    target_tag: str
    margin_px: float
    ambiguity_margin_px: float = 30.0

    @field_validator("ambiguity_margin_px")
    @classmethod
    def ambiguity_margin_must_be_non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("ambiguity_margin_px must be non-negative")
        return value


class AfterAllRequiredRule(RuleBase):
    type: Literal["after_all_required"]
    event: str
    required_steps: List[str]

    @model_validator(mode="after")
    def required_steps_must_not_be_empty(self) -> "AfterAllRequiredRule":
        if not self.required_steps:
            raise ValueError("required_steps must not be empty")
        return self


class AnyOfRule(RuleBase):
    type: Literal["any_of"]
    conditions: List[Condition]

    @model_validator(mode="after")
    def conditions_must_not_be_empty_or_duplicate(self) -> "AnyOfRule":
        if not self.conditions:
            raise ValueError("conditions must not be empty")
        _ensure_unique([condition.id for condition in self.conditions], "condition")
        return self


Rule = Annotated[
    Union[ExistsBeforeRule, NearBeforeRule, OverlapRule, AboveRule, AfterAllRequiredRule, AnyOfRule],
    Field(discriminator="type"),
]


class SoupPackage(StrictModel):
    schema_version: str = "0.1.0"
    package: PackageMetadata
    runtime: Dict[str, Any] = Field(default_factory=dict)
    tags: List[Tag]
    steps: List[Step]
    rules: List[Rule]

    @model_validator(mode="after")
    def validate_references(self) -> "SoupPackage":
        tag_ids = [tag.id for tag in self.tags]
        step_ids = [step.id for step in self.steps]
        rule_ids = [rule.id for rule in self.rules]

        _ensure_unique(tag_ids, "tag")
        _ensure_unique(step_ids, "step")
        _ensure_unique(rule_ids, "rule")

        if not self.schema_version.startswith("0."):
            raise ValueError("unsupported SOUP schema major version")

        known_tags = set(tag_ids)
        known_steps = set(step_ids)

        for rule in self.rules:
            if rule.step_id not in known_steps:
                raise ValueError("rule %s references unknown step %s" % (rule.id, rule.step_id))

            for tag_ref in _rule_tag_refs(rule):
                if tag_ref not in known_tags:
                    raise ValueError("rule %s references unknown tag %s" % (rule.id, tag_ref))

            if isinstance(rule, AfterAllRequiredRule):
                for step_ref in rule.required_steps:
                    if step_ref not in known_steps:
                        raise ValueError(
                            "rule %s references unknown required step %s" % (rule.id, step_ref)
                        )

        return self


class StepResult(StrictModel):
    step_id: str
    rule_id: str
    status: StepStatus
    message: str
    confidence: Optional[float] = None
    evidence_refs: List[str] = Field(default_factory=list)
    decision_trace: List[Dict[str, Any]] = Field(default_factory=list)
    completed_at_sec: Optional[float] = None


class EvidenceRef(StrictModel):
    id: str
    step_id: str
    rule_id: str
    frame_id: Optional[str] = None
    timestamp_sec: Optional[float] = None
    detection_ids: List[str] = Field(default_factory=list)
    event_ids: List[str] = Field(default_factory=list)
    reason: str


class PrivacyLog(StrictModel):
    raw_video_leaves_device: bool = False
    sop_rules_leave_device: bool = False
    yolo_model_leaves_device: bool = False
    cloud_vlm_used: bool = False
    local_vlm_used: bool = False
    final_decision_source: str = "local_rule_engine"
    sources_used: List[str] = Field(default_factory=list)


class RunResult(StrictModel):
    run_id: Optional[str] = None
    status: RunStatus
    steps: List[StepResult]
    evidence: List[EvidenceRef] = Field(default_factory=list)
    decision_trace: List[Dict[str, Any]] = Field(default_factory=list)
    privacy_log: PrivacyLog = Field(default_factory=PrivacyLog)

    def to_json(self) -> str:
        return json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))


def validate_soup(data: Union[SoupPackage, Dict[str, Any]]) -> List[str]:
    """Return validation errors for a package-shaped object."""

    try:
        if isinstance(data, SoupPackage):
            SoupPackage.model_validate(data.model_dump(mode="json"))
        else:
            SoupPackage.model_validate(data)
    except Exception as exc:  # Pydantic exposes nested validation detail via str().
        return [str(exc)]
    return []


def _ensure_unique(values: List[str], label: str) -> None:
    seen = set()
    for value in values:
        if value in seen:
            raise ValueError("duplicate %s id %s" % (label, value))
        seen.add(value)


def _rule_tag_refs(rule: Rule) -> List[str]:
    if isinstance(rule, ExistsBeforeRule):
        return [rule.tag]
    if isinstance(rule, (NearBeforeRule, OverlapRule, AboveRule)):
        return [rule.source_tag, rule.target_tag]
    if isinstance(rule, AnyOfRule):
        refs = []
        for condition in rule.conditions:
            refs.extend(_condition_tag_refs(condition))
        return refs
    return []


def _condition_tag_refs(condition: Condition) -> List[str]:
    if isinstance(condition, NotExistsCondition):
        return [condition.tag]
    if isinstance(condition, OverlapCondition):
        return [condition.source_tag, condition.target_tag]
    return []
