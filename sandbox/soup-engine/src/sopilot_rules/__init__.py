"""Public API for the standalone SOUP rule engine."""

from .engine import RuleEngine
from .loader import load_soup
from .schema import (
    BBox,
    Detection,
    Event,
    EvidenceRef,
    RunResult,
    SoupPackage,
    StepResult,
    validate_soup,
)

__all__ = [
    "BBox",
    "Detection",
    "Event",
    "EvidenceRef",
    "RuleEngine",
    "RunResult",
    "SoupPackage",
    "StepResult",
    "load_soup",
    "validate_soup",
]
