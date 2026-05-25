# sopilot-rules

Standalone deterministic SOUP rule engine for SoPilot.

The engine evaluates a `.soup.json` package against normalized detections and scene events. It does not run YOLO, read video, call a VLM, or render UI. Those systems provide structured inputs; this package makes the local final SOP decision.

## Quick Start

```bash
cd sandbox/soup-engine
python3 -m pip install -e .
python3 -m unittest discover -s tests -p "test_*.py"
python3 -m sopilot_rules.tools.validate_soup tests/fixtures/bp/bp_monitor.soup.json
```

## Public API

```python
from sopilot_rules import RuleEngine, load_soup

soup = load_soup("tests/fixtures/bp/bp_monitor.soup.json")
engine = RuleEngine(soup)
result = engine.evaluate(detections=detections, events=events)

print(result.to_json())
```

## Rule Types

Version `0.1.0` supports:

- `exists_before`
- `near_before`
- `overlap`
- `above`
- `after_all_required`
- `any_of`

`any_of` supports child conditions including `not_exists` and `overlap`.

See `DEVELOPER.md` for the schema contract and rule semantics.
