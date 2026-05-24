# SoPilot PRD 2.3 - Standalone SOUP Rule Engine

**Author:** Codex  
**Date:** 2026-05-23  
**Status:** Implementation PRD  
**Scope:** Standalone sandbox rule engine for SOUP package evaluation  
**Target:** 2-day hackathon MVP, BP Monitor SOP vertical slice  

## 1. Executive Summary

Build the SOUP rule engine as a standalone Python package before integrating it into any app shell.

The package will live at:

```text
sandbox/soup-engine/
```

It will be pip-installable as `sopilot-rules`, unit-tested with synthetic fixtures, and exposed through a small pure API:

```python
engine = RuleEngine(load_soup("bp_monitor.soup.json"))
result = engine.evaluate(detections=detections, events=events)
```

The engine is the core product artifact. It decides whether a physical SOP passed, failed, or needs review by evaluating deterministic local rules against normalized detections and scene events.

No YOLO, MLX, OpenCV, VLM, camera, FastAPI, React, or SwiftUI logic belongs inside this package. Those systems can produce input data for the engine, but the final SOP decision must be made by the standalone rule engine.

## 2. Source Context

This PRD synthesizes the rule-engine recommendations from:

- [PRD2.1-lit-kimi.md](./PRD2.1-lit-kimi.md)
- [PRD2.2-lit-claude.md](./PRD2.2-lit-claude.md)
- [PRD2.0-lit.md](./PRD2.0-lit.md)
- [SOUP.md](../SOUP.md)
- [README.md](../README.md)
- [testPRD1.4-YoloMlxMac.md](./sandbox-doc/testPRD1.4-YoloMlxMac.md)
- [testPRD1.5-VLM-Mac.md](./sandbox-doc/testPRD1.5-VLM-Mac.md)

Both PRD 2.1 and PRD 2.2 converge on the same architectural requirement: the SOUP rule engine must be developed and tested independently in `sandbox/` before any app integration.

They diverge on the app shell:

- PRD 2.1 recommends React + Vite served by FastAPI.
- PRD 2.2 recommends staying with the existing SwiftUI + Python sidecar path from `sandbox/macCamera/`.

This PRD deliberately avoids making the rule engine depend on that decision. The rule engine must work with either shell.

## 3. Product Problem

SoPilot needs a trustworthy local decision engine for physical SOP validation.

The perception stack can be probabilistic:

- YOLO detects objects.
- Trackers smooth detections.
- Local VLMs may explain ambiguous evidence.
- Optional cloud VLMs may summarize a redacted crop.

But the final SOP result must be deterministic, inspectable, local, and testable.

Without a standalone rule engine, rule logic risks leaking into UI view models, camera code, YOLO wrappers, or demo-specific scripts. That would make the product hard to test, hard to explain, and hard to reuse across future SOUP packages.

## 4. Goals

1. Create a reusable Python package named `sopilot-rules`.
2. Implement the BP Monitor MVP rule grammar.
3. Evaluate SOUP rules deterministically against detections and events.
4. Produce explainable results with step status, evidence references, decision trace, and privacy log.
5. Validate `.soup.json` packages before execution.
6. Provide a synthetic fixture corpus for BP Monitor.
7. Keep rule-engine tests fast enough to run constantly during development.
8. Provide an offline LLM-assisted rule-generation CLI with strict validation.
9. Define a frozen public API for app integration.

## 5. Non-Goals

This package will not:

1. Run YOLO inference.
2. Import `mlx`, `cv2`, `numpy`, or `yolo26mlx`.
3. Sample video frames.
4. Capture camera input.
5. Run local or cloud VLM inference.
6. Download or manage model files.
7. Render UI.
8. Package a `.dmg`.
9. Make medical or health judgments.
10. Decide anything from raw pixels directly.

The engine only evaluates structured inputs.

## 6. Primary User Stories

### 6.1 App Runtime

As the SoPilot runtime, I need to pass normalized detections and scene events into a local engine so that I can show the user a deterministic SOP result.

Acceptance:

- The runtime can call one stable API.
- The engine returns JSON suitable for UI display.
- The engine never reaches back into camera, YOLO, VLM, or filesystem state during evaluation.

### 6.2 SOUP Package Creator

As a package creator, I need to validate that my rules reference valid tags, valid steps, and supported rule types before publishing a package.

Acceptance:

- `validate_soup.py` catches malformed rules.
- Unknown tags and missing step references fail validation.
- Schema version compatibility is enforced.

### 6.3 Hackathon Demo

As a hackathon presenter, I need a reliable BP Monitor vertical slice that can show pass, fail, and uncertain outcomes without relying on live camera conditions.

Acceptance:

- Synthetic fixtures cover all expected outcomes.
- A prerecorded demo video can be converted into detections and evaluated.
- If YOLO is unreliable, the fixture corpus still proves the rule engine is real.

## 7. Architectural Principles

### 7.1 Pure Evaluation

`RuleEngine.evaluate()` must be pure:

- Inputs: `SoupPackage`, `Detection[]`, `Event[]`
- Output: `RunResult`
- No implicit I/O
- No wall-clock reads
- No random numbers
- No network calls

Same inputs must produce byte-identical JSON output.

### 7.2 Perception Is Not Policy

YOLO and VLM outputs are evidence. They are not the final decision.

The engine may consider:

- tag
- confidence
- bounding box geometry
- timestamp
- event ordering
- source provenance

The engine may not ask a model whether the SOP passed.

### 7.3 Rule Logic Belongs in One Place

Rule decisions must live under:

```text
sandbox/soup-engine/src/sopilot_rules/
```

The app layer should not contain fallback copies of rule semantics.

### 7.4 Schema First

Every rule type must have an explicit Pydantic schema. LLM-generated JSON, hand-authored JSON, and test fixtures must all pass the same validator.

### 7.5 Explainability Is Required

Every step result must explain:

- which rule produced the status
- which detections or events were used
- which threshold was applied
- which evidence frame or timestamp is relevant
- whether the step passed, failed, became uncertain, or was skipped

## 8. Package Layout

Implement the package with this structure:

```text
sandbox/soup-engine/
├── pyproject.toml
├── README.md
├── DEVELOPER.md
├── CHANGELOG.md
├── src/
│   └── sopilot_rules/
│       ├── __init__.py
│       ├── schema.py
│       ├── loader.py
│       ├── engine.py
│       ├── geometry.py
│       ├── normalizer.py
│       ├── events.py
│       ├── evidence.py
│       ├── privacy.py
│       └── rules/
│           ├── __init__.py
│           ├── base.py
│           ├── exists_before.py
│           ├── near_before.py
│           ├── overlap.py
│           ├── above.py
│           └── after_all_required.py
├── tools/
│   ├── validate_soup.py
│   └── rule_gen_cli.py
└── tests/
    ├── conftest.py
    ├── unit/
    │   ├── test_schema.py
    │   ├── test_loader.py
    │   ├── test_geometry.py
    │   ├── test_normalizer.py
    │   ├── test_events.py
    │   ├── test_evidence.py
    │   ├── test_privacy.py
    │   ├── test_rules_exists_before.py
    │   ├── test_rules_near_before.py
    │   ├── test_rules_overlap.py
    │   ├── test_rules_above.py
    │   └── test_rules_after_all_required.py
    ├── integration/
    │   └── test_bp_end_to_end.py
    └── fixtures/
        └── bp/
            ├── bp_monitor.soup.json
            ├── all_pass.json
            ├── sleeve_not_rolled.json
            ├── missing_sleeve.json
            ├── cuff_not_on_upper_arm.json
            ├── measure_too_early.json
            ├── no_measure_event.json
            ├── low_confidence_cuff.json
            └── multiple_good_frames.json
```

## 9. Runtime Dependencies

For `0.1.0`, runtime dependencies should be minimal:

```text
pydantic>=2
```

Development dependencies:

```text
pytest
pytest-cov
ruff
mypy
```

The engine must not require:

```text
mlx
yolo26mlx
opencv-python
numpy
requests
fastapi
```

`requests` or provider SDKs may be used by `tools/rule_gen_cli.py` only if they are optional extras, not core runtime dependencies.

## 10. Public API

The app layer may import only this public API:

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

Example:

```python
from sopilot_rules import RuleEngine, load_soup

soup = load_soup("bp_monitor.soup.json")
engine = RuleEngine(soup=soup)

result = engine.evaluate(
    detections=detections,
    events=events,
)

print(result.to_json())
```

API rules:

1. The constructor validates package shape.
2. `evaluate()` validates input shape.
3. `evaluate()` never mutates the package.
4. `RunResult.to_json()` produces stable key ordering.
5. App code must not import private rule modules directly.

## 11. Core Schemas

### 11.1 SoupPackage

Minimum fields:

```text
schema_version
package
runtime
tags[]
steps[]
rules[]
```

Required metadata:

```text
package.id
package.name
package.version
package.description
package.safety_note
```

Validation:

- `schema_version` must be supported.
- `package.id` must be stable and machine-readable.
- tags must be unique by `id`.
- steps must be unique by `id`.
- rule IDs must be unique.
- every rule `step_id` must reference a known step.
- every tag reference must reference a known tag.

### 11.2 Detection

```text
frame_id: str
timestamp_sec: float
tag: str
confidence: float
bbox: BBox
source: str
track_id: str | None
metadata: dict
```

`bbox` uses pixel coordinates:

```text
x1
y1
x2
y2
```

Validation:

- `0.0 <= confidence <= 1.0`
- `x2 > x1`
- `y2 > y1`
- `timestamp_sec >= 0`

### 11.3 Event

```text
id: str
type: str
timestamp_sec: float
confidence: float
source: str
evidence_refs: list[str]
metadata: dict
```

Initial BP Monitor event:

```text
measure_started
```

Events can come from:

- demo marker
- UI marker
- detector-derived event builder
- local VLM event builder in future versions

### 11.4 StepResult

```text
step_id: str
rule_id: str
status: passed | failed | uncertain | skipped
message: str
confidence: float | None
evidence_refs: list[str]
decision_trace: list[dict]
```

### 11.5 RunResult

```text
run_id: str | None
status: passed | failed | needs_review
steps: list[StepResult]
evidence: list[EvidenceRef]
decision_trace: list[dict]
privacy_log: PrivacyLog
```

Overall status rules:

- `failed` if any required step fails.
- `needs_review` if no required step fails and at least one required step is uncertain.
- `passed` if all required steps pass.
- `skipped` steps do not pass the SOP unless the step is optional.

### 11.6 PrivacyLog

```text
raw_video_leaves_device: false
sop_rules_leave_device: false
yolo_model_leaves_device: false
cloud_vlm_used: false
local_vlm_used: bool
final_decision_source: local_rule_engine
sources_used: list[str]
```

For this package, `cloud_vlm_used` must default to `false`.

## 12. Rule Grammar

The MVP supports six rule types.

### 12.1 exists_before

Purpose: require an object to appear before an event.

Example:

```json
{
  "id": "S0_monitor_visible_before_measure",
  "step_id": "S0",
  "type": "exists_before",
  "tag": "blood_pressure_monitor",
  "event": "measure_started",
  "min_confidence": 0.5,
  "failure_message": "The monitor was not visible before measurement started."
}
```

Pass:

- A detection with matching tag and confidence >= threshold exists before the event timestamp.

Fail:

- No matching detection exists before the event.

Uncertain:

- Only low-confidence matching detections exist.
- Event is missing and the rule cannot establish the temporal relation.

### 12.2 near_before

Purpose: require one object to be near another before an event.

Example:

```json
{
  "id": "sleeve_near_upper_arm_before_measure",
  "step_id": "S1",
  "type": "near_before",
  "source_tag": "sleeve",
  "target_tag": "upper_arm",
  "event": "measure_started",
  "max_distance_px": 120,
  "min_confidence": 0.5,
  "failure_message": "The sleeve was not close enough to the upper arm before measurement."
}
```

Distance is measured between bbox centers by default.

Pass:

- Source and target detections exist before the event and their center distance is <= threshold.

Fail:

- Both objects exist but are farther than threshold.

Uncertain:

- One object is low confidence or missing but related evidence exists.

### 12.3 overlap

Purpose: require two objects or regions to overlap.

Example:

```json
{
  "id": "S2_cuff_overlaps_upper_arm",
  "step_id": "S2",
  "type": "overlap",
  "source_tag": "cuff",
  "target_tag": "upper_arm",
  "min_overlap_ratio": 0.25,
  "min_confidence": 0.5,
  "failure_message": "The cuff did not appear to be on the upper arm."
}
```

Pass:

- Best matching source and target detections overlap above threshold.

Fail:

- Both objects exist with sufficient confidence and overlap is below threshold.

Uncertain:

- Required detections are borderline confidence or overlap is near threshold.

### 12.4 above

Purpose: require one object to be vertically above another.

Example:

```json
{
  "id": "object_above_reference",
  "step_id": "example_step",
  "type": "above",
  "source_tag": "source_object",
  "target_tag": "reference_object",
  "margin_px": 10,
  "ambiguity_margin_px": 20,
  "min_confidence": 0.5,
  "failure_message": "The source object was not clearly above the reference object."
}
```

Coordinate convention:

- Smaller `center_y` is visually higher in the image.

Pass:

- `source.center_y + margin_px < target.center_y`

Fail:

- Source is clearly below or too close to the target outside ambiguity range.

Uncertain:

- Vertical difference falls within `ambiguity_margin_px`.

### 12.5 after_all_required

Purpose: require an event to happen only after listed steps pass.

Example:

```json
{
  "id": "S3_measure_after_setup",
  "step_id": "S3",
  "type": "after_all_required",
  "event": "measure_started",
  "required_steps": [
    "S0",
    "S1",
    "S2"
  ],
  "failure_message": "Measurement started before setup was complete."
}
```

Pass:

- Event exists and all required steps passed before the event.

Fail:

- Event exists before one or more required steps passed.

Uncertain:

- One or more required steps is uncertain.

### 12.6 any_of

Purpose: pass a step when at least one child condition passes.

Example:

```json
{
  "id": "S1_sleeve_clear_or_on_upper_arm",
  "step_id": "S1",
  "type": "any_of",
  "conditions": [
    {"id": "S1_no_sleeve_detected", "type": "not_exists", "tag": "sleeve", "min_confidence": 0.5},
    {
      "id": "S1_sleeve_on_upper_arm",
      "type": "overlap",
      "source_tag": "sleeve",
      "target_tag": "upper_arm",
      "min_overlap_ratio": 0.25,
      "min_confidence": 0.5
    }
  ],
  "failure_message": "The sleeve was detected but did not appear to be clear of or on the upper arm."
}
```

Pass:

- Any child condition passes.

Fail:

- All child conditions fail.

Uncertain:

- No child condition passes and at least one child condition is uncertain.

Skipped:

- Event does not exist and this step cannot be evaluated.

## 13. Geometry Utilities

Implement in `geometry.py`:

```text
bbox_width
bbox_height
bbox_area
bbox_center
iou
overlap_ratio
center_distance_px
is_above
above_with_margin
```

Requirements:

- All functions are deterministic.
- All functions handle invalid bbox through schema validation before calculation.
- Boundary cases must be explicitly tested.

## 14. Scene Event Builder

Implement a minimal `events.py` even if the first demo passes events manually.

Responsibilities:

1. Normalize event shape.
2. Deduplicate repeated events.
3. Preserve timestamp ordering.
4. Convert configured detection patterns into events when needed.

For `0.1.0`, the only required event type is:

```text
measure_started
```

This can be supplied by a demo marker, UI marker, or later by detector-derived workflow logic.

## 15. Evidence Selection

Implement `evidence.py` to select evidence references for each step.

Initial strategy:

1. Prefer the frame that best satisfies the rule.
2. For failures, prefer the highest-confidence frame closest to the relevant event.
3. For uncertain results, prefer the frame with the strongest borderline evidence.
4. Preserve source detection IDs so UI overlays can be reconstructed.

Evidence references should include:

```text
frame_id
timestamp_sec
detection_ids
rule_id
step_id
reason
```

The engine does not write image files. It only returns references to frames or detections supplied by the caller.

## 16. BP Monitor MVP Package

The BP Monitor `.soup.json` must include these tags:

```text
blood_pressure_monitor
cuff
upper_arm
sleeve
```

Required states:

```text
S0: Start
S1: Roll sleeve
S2: Put Cuff On Upper Arm
S3: Measure
S4: Done
```

Required rule coverage:

```text
S0 Start: exists_before blood_pressure_monitor before measure_started
S1 Roll sleeve: any_of(no sleeve detected, sleeve overlaps upper_arm)
S2 Put Cuff On Upper Arm: overlap cuff with upper_arm
S3 Measure: after_all_required measure_started after S0, S1, S2
S4 Done: after_all_required measurement_done after S3
```

## 17. Fixture Corpus

Create synthetic fixture JSON files in:

```text
sandbox/soup-engine/tests/fixtures/bp/
```

### 17.1 all_pass.json

Expected:

```text
status: passed
failed_steps: []
uncertain_steps: []
```

### 17.2 sleeve_not_rolled.json

Expected:

```text
status: failed
failed_steps: [S1, S3, S4]
```

### 17.3 missing_sleeve.json

Expected:

```text
status: passed
uncertain_steps: []
```

### 17.4 cuff_not_on_upper_arm.json

Expected:

```text
status: failed
failed_steps: [S2, S3, S4]
```

### 17.5 measure_too_early.json

Expected:

```text
status: failed
failed_steps: [S3, S4]
```

### 17.6 no_measure_event.json

Expected:

```text
status: needs_review
uncertain_steps: [S0, S3, S4]
```

### 17.7 low_confidence_cuff.json

Expected:

```text
status: needs_review
uncertain_steps: [S2, S3, S4]
```

### 17.8 multiple_good_frames.json

Expected:

```text
status: passed
evidence: best frame selected deterministically
```

## 18. Test Plan

### 18.1 Unit Tests

Required tests:

```text
test_schema.py
test_loader.py
test_geometry.py
test_normalizer.py
test_events.py
test_evidence.py
test_privacy.py
test_rules_exists_before.py
test_rules_near_before.py
test_rules_overlap.py
test_rules_above.py
test_rules_after_all_required.py
```

### 18.2 Integration Tests

Required:

```text
test_bp_end_to_end.py
```

Each BP fixture must be loaded, evaluated, and compared against expected output.

### 18.3 Determinism Tests

Required:

- Same input evaluated twice produces identical `RunResult`.
- JSON serialization is stable.
- Evidence selection is stable when multiple candidate frames exist.

### 18.4 Validation Tests

Required invalid package cases:

- unknown rule type
- duplicate rule ID
- unknown tag reference
- unknown step reference
- missing required rule field
- unsupported future major schema version
- invalid confidence threshold
- invalid bbox coordinates

## 19. Integration Gate

The app may not import `sopilot_rules` until all of the following pass:

```bash
pip install -e sandbox/soup-engine
pytest sandbox/soup-engine
python -m sopilot_rules.tools.validate_soup \
  sandbox/soup-engine/tests/fixtures/bp/bp_monitor.soup.json
```

Gate criteria:

1. All tests pass.
2. Test suite completes in under 5 seconds.
3. `README.md` explains quick start.
4. `DEVELOPER.md` documents the public API and rule grammar.
5. `CHANGELOG.md` contains a `0.1.0` entry.
6. Runtime dependencies are limited to Pydantic unless explicitly justified.
7. No rule decision logic exists outside the package.

## 20. LLM-Assisted Rule Generation

Add offline CLI support in:

```text
sandbox/soup-engine/tools/rule_gen_cli.py
```

The CLI is for creator-time authoring, not runtime evaluation.

Example:

```bash
python -m sopilot_rules.tools.rule_gen_cli \
  --sop-text doc/sop-drafts/bp_monitor.txt \
  --tags blood_pressure_monitor,cuff,upper_arm,sleeve \
  --out sandbox/soup-engine/tests/fixtures/bp/bp_monitor.soup.json
```

The generated rules must pass:

1. JSON parse.
2. Pydantic schema validation.
3. Allowed-tag validation.
4. Unique rule ID validation.
5. Step reference validation.
6. Rule-type-specific validation.
7. Dry run against fixture corpus.
8. Human approval before overwrite unless `--yes` is passed.

The LLM is never the author of record. The human accepts the generated package after validation.

## 21. Rule Generation Prompt Contract

The rule-generation prompt should constrain the model:

```text
You are a SOUP rule author.
Output only valid JSON.
Use only these rule types:
- exists_before
- near_before
- overlap
- above
- after_all_required

Use only these tags:
{tag_list}

Every rule must include:
- id
- step_id
- type
- type-specific required fields

Do not invent tags.
Do not invent rule types.
Do not include markdown.
```

The CLI must reject non-JSON output.

## 22. Implementation Milestones

### Milestone 1 - Package Skeleton

Deliverables:

- `sandbox/soup-engine/pyproject.toml`
- importable `sopilot_rules`
- empty test suite running through pytest
- README quick start stub

Exit criteria:

```bash
pip install -e sandbox/soup-engine
pytest sandbox/soup-engine
```

### Milestone 2 - Schemas and Loader

Deliverables:

- `schema.py`
- `loader.py`
- package validation errors
- initial `bp_monitor.soup.json`

Exit criteria:

- valid BP package loads
- malformed package tests fail predictably

### Milestone 3 - Geometry

Deliverables:

- bbox helpers
- IoU
- overlap ratio
- center distance
- above/below logic

Exit criteria:

- all geometry edge cases pass

### Milestone 4 - Individual Rules

Deliverables:

- six rule implementations
- one test file per rule type

Exit criteria:

- pass, fail, uncertain, and missing-input cases covered

### Milestone 5 - Engine Orchestration

Deliverables:

- rule registry
- ordered step evaluation
- overall status aggregation
- deterministic result serialization

Exit criteria:

- end-to-end BP fixture tests run through `RuleEngine.evaluate()`

### Milestone 6 - Evidence and Privacy

Deliverables:

- evidence reference selection
- privacy log generation
- decision trace records

Exit criteria:

- result JSON is UI-ready and explains every step

### Milestone 7 - Fixture Corpus

Deliverables:

- all eight BP fixture files
- expected outcome assertions

Exit criteria:

- BP pass, fail, and uncertain cases are covered

### Milestone 8 - LLM Rule CLI

Deliverables:

- prompt scaffold
- provider abstraction
- validation pipeline
- diff-before-write behavior

Exit criteria:

- generated package cannot overwrite existing rules without validation and approval

### Milestone 9 - App Integration Contract

Deliverables:

- `DEVELOPER.md`
- `CHANGELOG.md`
- public API exports
- integration example

Exit criteria:

- app layer can use `RuleEngine` without importing private modules

## 23. Suggested 2-Day Execution Plan

### Day 1 Morning

1. Create package skeleton.
2. Implement schemas and loader.
3. Implement geometry helpers.
4. Add rule base class and registry.
5. Implement `exists_before`, `near_before`, and `overlap`.

Target output:

```text
pytest passes for schemas, loader, geometry, first three rule types
```

### Day 1 Afternoon

1. Implement `above`.
2. Implement `after_all_required`.
3. Add BP package fixture.
4. Add all eight BP scenario fixtures.
5. Implement engine orchestration.

Target output:

```text
BP fixture tests pass end-to-end
```

### Day 2 Morning

1. Add evidence selection.
2. Add privacy log.
3. Add deterministic JSON serialization tests.
4. Write README and DEVELOPER docs.
5. Add `validate_soup.py`.

Target output:

```text
Standalone package passes integration gate
```

### Day 2 Afternoon

1. Add LLM rule-generation CLI scaffold.
2. Integrate package into the chosen app shell.
3. Wire app input detections/events into `RuleEngine.evaluate()`.
4. Use fixture results as fallback demo data if YOLO output is unreliable.

Target output:

```text
App can display real engine output
```

## 24. App Integration Recommendation

The rule engine should be shell-agnostic.

For the current repo, the fastest integration path is likely:

```text
SwiftUI app shell from sandbox/macCamera/
Python sidecar process
sopilot_rules imported by the sidecar
YOLO output normalized into Detection[]
RuleEngine.evaluate() returns RunResult JSON
SwiftUI renders the result
```

If the app shell switches to React + FastAPI, the same package still applies:

```text
FastAPI endpoint receives video or detections
Backend normalizes detections/events
RuleEngine.evaluate() returns RunResult JSON
React renders the result
```

Do not bind the rule engine to either shell.

## 25. Risk Register

| Risk | Severity | Likelihood | Mitigation |
|---|---:|---:|---|
| Rule logic leaks into app code | High | Medium | Enforce integration gate and public API boundary |
| YOLO model misses BP tags | High | High | Use synthetic fixtures to prove engine; use prerecorded golden video for demo |
| LLM-generated rules are semantically wrong | Medium | High | Validate, dry-run fixtures, require human approval |
| Scene event builder creates wrong timestamps | High | Medium | Test event ordering, deduplication, and missing-event cases |
| Evidence selection is nondeterministic | Medium | Medium | Add tie-break rules and determinism tests |
| Schema drift breaks packages | Medium | Medium | Add `schema_version` and compatibility checks |
| VLM scope distracts from engine | Medium | High | Keep VLM out of engine and out of Day 1 scope |
| Package gains heavy dependencies | Medium | Medium | Runtime dependency gate in `pyproject.toml` review |

## 26. Open Questions

1. What exact schema version should `bp_monitor.soup.json` use for `0.1.0`?
2. Should ambiguous missing evidence produce `uncertain` or `failed` by default for each rule type?
3. Will the first app integration pass explicit `measure_started` and `measurement_done` events, or should the event builder infer them from workflow markers?
4. Should `near_before` use bbox center distance only, or allow edge-to-edge distance in schema?
5. Should `overlap` use IoU or source-over-target coverage as the default metric?

Recommended defaults for `0.1.0`:

- Missing required visual evidence: `uncertain`
- Clear contradictory visual evidence: `failed`
- `near_before`: center distance
- `overlap`: source-over-target coverage for placement rules, with IoU available as a utility
- `measure_started` and `measurement_done`: explicit events supplied by app or fixture

## 27. Final Acceptance Criteria

PRD 2.3 is implemented when:

1. `sandbox/soup-engine/` exists as a standalone package.
2. `pip install -e sandbox/soup-engine` works.
3. `pytest sandbox/soup-engine` passes.
4. BP Monitor SOUP package validates.
5. All eight BP fixtures pass expected outcomes.
6. The engine supports all five MVP rule types.
7. `RunResult` includes step results, evidence refs, decision trace, and privacy log.
8. The app can consume the engine through the public API only.
9. LLM-generated rules cannot bypass schema validation.
10. No rule engine code depends on YOLO, MLX, OpenCV, VLM, FastAPI, React, or SwiftUI.

## 28. One-Line Summary

Build `sopilot-rules` first as a pure, deterministic, fully tested sandbox package; only after it passes the fixture gate should SoPilot wire YOLO, camera, VLM, or UI around it.
