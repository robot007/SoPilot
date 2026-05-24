# Report 2.3 - SOUP Engine Test 1

**Date:** 2026-05-23  
**Implementation PRD:** [PRD2.3-StandaloneSOUPEngine-Codex.md](./PRD2.3-StandaloneSOUPEngine-Codex.md)  
**Package:** `sandbox/soup-engine`  
**Python used for verification:** Python 3.9.6  
**Result:** PASS

## 1. Summary

Implemented the standalone SOUP rule engine as a separate Python package:

```text
sandbox/soup-engine/
```

The package installs as `sopilot-rules` and exposes the PRD public API:

```python
from sopilot_rules import RuleEngine, Detection, Event, RunResult, SoupPackage, load_soup, validate_soup
```

The engine evaluates normalized detections and scene events against a `.soup.json` package. It returns deterministic `RunResult` JSON with:

- overall status
- step-level status
- evidence references
- decision trace
- privacy log

No YOLO, MLX, OpenCV, VLM, FastAPI, React, or SwiftUI dependency is used by the engine.

## 2. Implemented Artifacts

### Package and Docs

```text
sandbox/soup-engine/pyproject.toml
sandbox/soup-engine/setup.py
sandbox/soup-engine/README.md
sandbox/soup-engine/DEVELOPER.md
sandbox/soup-engine/CHANGELOG.md
```

`setup.py` was added as a compatibility bridge for the older pip version available in the local Python 3.9 environment. Modern builds can still use `pyproject.toml`.

### Source Modules

```text
sandbox/soup-engine/src/sopilot_rules/__init__.py
sandbox/soup-engine/src/sopilot_rules/schema.py
sandbox/soup-engine/src/sopilot_rules/loader.py
sandbox/soup-engine/src/sopilot_rules/engine.py
sandbox/soup-engine/src/sopilot_rules/geometry.py
sandbox/soup-engine/src/sopilot_rules/normalizer.py
sandbox/soup-engine/src/sopilot_rules/events.py
sandbox/soup-engine/src/sopilot_rules/evidence.py
sandbox/soup-engine/src/sopilot_rules/privacy.py
```

### Rule Evaluators

```text
sandbox/soup-engine/src/sopilot_rules/rules/exists_before.py
sandbox/soup-engine/src/sopilot_rules/rules/near_before.py
sandbox/soup-engine/src/sopilot_rules/rules/overlap.py
sandbox/soup-engine/src/sopilot_rules/rules/above.py
sandbox/soup-engine/src/sopilot_rules/rules/after_all_required.py
sandbox/soup-engine/src/sopilot_rules/rules/any_of.py
sandbox/soup-engine/src/sopilot_rules/rules/conditions.py
```

### CLI Tools

```text
sandbox/soup-engine/src/sopilot_rules/tools/validate_soup.py
sandbox/soup-engine/src/sopilot_rules/tools/rule_gen_cli.py
```

The rule-generation CLI is implemented as a creator-time scaffold. It prints the prompt when no `OPENROUTER_API_KEY` is present and validates generated rules before writing output.

## 3. BP Monitor Fixture Corpus

Implemented:

```text
sandbox/soup-engine/tests/fixtures/bp/bp_monitor.soup.json
sandbox/soup-engine/tests/fixtures/bp/all_pass.json
sandbox/soup-engine/tests/fixtures/bp/sleeve_not_rolled.json
sandbox/soup-engine/tests/fixtures/bp/missing_sleeve.json
sandbox/soup-engine/tests/fixtures/bp/cuff_not_on_upper_arm.json
sandbox/soup-engine/tests/fixtures/bp/measure_too_early.json
sandbox/soup-engine/tests/fixtures/bp/no_measure_event.json
sandbox/soup-engine/tests/fixtures/bp/low_confidence_cuff.json
sandbox/soup-engine/tests/fixtures/bp/multiple_good_frames.json
```

The BP package now uses exactly these tags:

```text
blood_pressure_monitor
cuff
upper_arm
sleeve
```

The BP package now uses exactly these states:

```text
S0: Start
S1: Roll sleeve
S2: Put Cuff On Upper Arm
S3: Measure
S4: Done
```

Fixture outcomes:

| Fixture | Expected Overall Status | Expected Failed Steps | Expected Uncertain Steps |
|---|---|---|---|
| `all_pass.json` | `passed` | none | none |
| `sleeve_not_rolled.json` | `failed` | `S1`, `S3`, `S4` | none |
| `missing_sleeve.json` | `passed` | none | none |
| `cuff_not_on_upper_arm.json` | `failed` | `S2`, `S3`, `S4` | none |
| `measure_too_early.json` | `failed` | `S3`, `S4` | none |
| `no_measure_event.json` | `needs_review` | none | `S0`, `S3`, `S4` |
| `low_confidence_cuff.json` | `needs_review` | none | `S2`, `S3`, `S4` |
| `multiple_good_frames.json` | `passed` | none | none |

Note: dependent `after_all_required` results become `failed` or `uncertain` when a prerequisite step failed or remained uncertain. This is intentional because the start-after-setup step cannot confidently pass if setup correctness is unresolved.

## 4. Test Coverage

Implemented 66 tests:

```text
sandbox/soup-engine/tests/unit/test_schema.py
sandbox/soup-engine/tests/unit/test_loader.py
sandbox/soup-engine/tests/unit/test_geometry.py
sandbox/soup-engine/tests/unit/test_normalizer.py
sandbox/soup-engine/tests/unit/test_events.py
sandbox/soup-engine/tests/unit/test_evidence.py
sandbox/soup-engine/tests/unit/test_privacy.py
sandbox/soup-engine/tests/unit/test_rules_exists_before.py
sandbox/soup-engine/tests/unit/test_rules_near_before.py
sandbox/soup-engine/tests/unit/test_rules_overlap.py
sandbox/soup-engine/tests/unit/test_rules_above.py
sandbox/soup-engine/tests/unit/test_rules_after_all_required.py
sandbox/soup-engine/tests/unit/test_engine.py
sandbox/soup-engine/tests/unit/test_tools.py
sandbox/soup-engine/tests/integration/test_bp_end_to_end.py
```

Coverage areas:

- Pydantic schema validation
- package loader
- invalid package rejection
- bbox geometry
- source-over-target overlap
- vertical relation ambiguity
- detection/event normalization
- event deduplication
- detector-derived start event helper
- privacy log construction
- evidence selection
- all six rule types
- `not_exists` child condition behavior
- `any_of` composite rule behavior
- end-to-end BP fixture evaluation
- deterministic JSON output
- validation CLI

## 5. Commands Run

### Import Check

```bash
PYTHONPATH=sandbox/soup-engine/src python3 -c "from sopilot_rules import RuleEngine, SoupPackage; print('import ok')"
```

Result:

```text
import ok
```

### Test Suite

```bash
PYTHONPATH=sandbox/soup-engine/src python3 -m unittest discover -s sandbox/soup-engine/tests -p 'test_*.py'
```

Result:

```text
Ran 66 tests in 0.008s

OK
```

### Package Validation CLI

```bash
PYTHONPATH=sandbox/soup-engine/src python3 -m sopilot_rules.tools.validate_soup \
  sandbox/soup-engine/tests/fixtures/bp/bp_monitor.soup.json
```

Result:

```text
OK: bp_monitor_sop_checker 0.1.0
```

### Editable Install Check

Created a temporary venv:

```bash
python3 -m venv --system-site-packages /private/tmp/sopilot-soup-engine-venv2
```

Installed package:

```bash
/private/tmp/sopilot-soup-engine-venv2/bin/python -m pip install -e sandbox/soup-engine
```

Result:

```text
Successfully installed sopilot-rules
```

### Installed Package Test Run

```bash
/private/tmp/sopilot-soup-engine-venv2/bin/python -m unittest discover \
  -s sandbox/soup-engine/tests -p 'test_*.py'
```

Result:

```text
Ran 66 tests in 0.006s

OK
```

### Installed Package Validation CLI

```bash
/private/tmp/sopilot-soup-engine-venv2/bin/python -m sopilot_rules.tools.validate_soup \
  sandbox/soup-engine/tests/fixtures/bp/bp_monitor.soup.json
```

Result:

```text
OK: bp_monitor_sop_checker 0.1.0
```

### Syntax Sweep

The default `compileall` run attempted to write bytecode under macOS' user cache and was blocked by sandbox permissions. It passed after redirecting bytecode output to `/private/tmp`:

```bash
PYTHONPYCACHEPREFIX=/private/tmp/sopilot-soup-pycache \
  /private/tmp/sopilot-soup-engine-venv2/bin/python -m compileall -q \
  sandbox/soup-engine/src sandbox/soup-engine/tests
```

Result:

```text
PASS
```

## 6. Local Tooling Notes

`pytest` is not installed in the system Python available in this environment:

```text
/Applications/Xcode.app/Contents/Developer/usr/bin/python3: No module named pytest
```

The test suite is written with `unittest`, so it runs without downloading pytest. These tests remain pytest-compatible because pytest can discover and execute unittest test cases.

The first editable install attempt failed because the local pip version required a `setup.py` compatibility path for editable installs. After adding `setup.py`, editable install passed.

## 7. Acceptance Criteria Result

| PRD 2.3 Acceptance Criterion | Result |
|---|---|
| `sandbox/soup-engine/` exists as a standalone package | PASS |
| `pip install -e sandbox/soup-engine` works | PASS |
| test suite passes | PASS |
| BP Monitor SOUP package validates | PASS |
| all eight BP fixtures pass expected outcomes | PASS |
| five MVP rule types implemented | PASS |
| result JSON includes step results, evidence refs, decision trace, and privacy log | PASS |
| public API exports available | PASS |
| LLM-generated rules cannot bypass schema validation in CLI scaffold | PASS |
| no engine dependency on YOLO, MLX, OpenCV, VLM, FastAPI, React, or SwiftUI | PASS |

## 8. Recommendation

The standalone SOUP engine is ready for app-side integration.

Recommended next integration point:

```text
YOLO / detector output -> Detection[]
runtime marker or event builder -> Event[]
RuleEngine.evaluate() -> RunResult JSON
UI renders RunResult
```

The app layer should not duplicate rule semantics. It should treat `sopilot_rules.RuleEngine` as the sole local SOP decision engine.
