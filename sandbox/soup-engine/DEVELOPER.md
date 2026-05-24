# sopilot-rules Developer Guide

## Contract

`sopilot-rules` is intentionally small and pure. The runtime may import:

```python
from sopilot_rules import (
    RuleEngine,
    Detection,
    Event,
    RunResult,
    SoupPackage,
    load_soup,
    validate_soup,
)
```

All rule decisions must stay inside `src/sopilot_rules/`. App code should pass detections and events in, then render `RunResult`.

## Evaluation Rules

- No implicit filesystem access during `RuleEngine.evaluate()`.
- No network access.
- No wall-clock reads.
- Same inputs produce identical JSON.
- Missing or ambiguous visual evidence should prefer `uncertain` over false confidence.
- Clear contradictory evidence should produce `failed`.

## Adding a Rule Type

1. Add a Pydantic rule schema in `schema.py`.
2. Add a rule evaluator in `rules/`.
3. Register the evaluator in `rules/__init__.py`.
4. Add unit tests for pass, fail, uncertain, missing input, and determinism.
5. Add package validation checks if the rule references tags, steps, or events.

## Fixture Format

Fixture files under `tests/fixtures/bp/` contain:

```json
{
  "name": "all_pass",
  "detections": [],
  "events": [],
  "expected": {
    "status": "passed",
    "failed_steps": [],
    "uncertain_steps": []
  }
}
```

The fixture corpus is synthetic. Real videos are integration inputs outside this package.
