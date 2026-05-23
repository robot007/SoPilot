# PRD 2.2 — Architect Review of PRD 2.0 (Claude)

**Reviewer:** Claude (senior software architect lens)
**Date:** 2026-05-22
**Inputs reviewed:** [PRD2.0-lit.md](./PRD2.0-lit.md), [README.md](../README.md), [SOUP.md](../SOUP.md), [yolo26-README.md](../yolo26-README.md), [Note1.2-claude.md](./Note1.2-claude.md), [sandbox-doc/testPRD1.4-YoloMlxMac.md](./sandbox-doc/testPRD1.4-YoloMlxMac.md)
**Scope:** Hackathon 2-day MVP feasibility; opinionated; sandbox-first.

**User direction baked into this review:**
1. Build & unit-test the SOUP rule engine **standalone in `sandbox/` first**, integrate only after green tests.
2. The SOUP rule engine is its own **reusable Python package** (pip-installable) with its own dev docs, release notes, and test suite.
3. Use a mature LLM (Claude/ChatGPT) to **generate** the rules — both offline (primary) and in-app (secondary).
4. Apply the same pattern proven in [FaceBoxDemo](../sandbox/macCamera/): every complex module gets a standalone sandbox proof before it touches the app.

---

## TL;DR

PRD 2.0 is a sensible reduction of v1.x — drop the iPhone target, drop the cloud-VLM-as-decider mode, ship a Mac app with real YOLO MLX inference and a deterministic rule engine. The scope is achievable in 2 days **only if** you do the four things below:

1. **Extract the SOUP rule engine into its own package today.** Put it in `sandbox/soup-engine/` as a self-contained `pip install -e .` project. Don't put a single line of rule logic inside the macOS app target. The app imports `sopilot_rules`, nothing more. This is the most important architectural call in the whole project.
2. **Decide the macOS shell now.** PRD 2.0 hedges between Tauri/Electron+Python sidecar and SwiftUI. You already shipped [FaceBoxDemo](../sandbox/macCamera/) as a Swift app that calls a Python `YoloMLXWorker`. **Stay on that path.** Adding Tauri now is a half-day of yak-shaving you do not have.
3. **The LLM-rule-generation path is not in PRD 2.0 at all** — add it. Rules in §11.3 are hand-written JSON; for the demo to scale past BP Monitor you need a Claude/ChatGPT prompt that emits validated rule JSON from a plain-language SOP description. Build this as a CLI in `sandbox/soup-engine/tools/` first.
4. **Cut the VLM model manager from Day 1 scope.** PRD 2.0 §10 spends a third of the doc on SmolVLM/Moondream2 download flows. For the 1-minute demo, a `vlm_used: false` line in the privacy log is enough. Ship VLM as a stub button on Day 2 only if Day 1 lands clean.

The rest of this doc is the long version with concrete artifacts.

---

## 1. What PRD 2.0 got right (don't change)

- **Mocked creator / real consumer split.** §5.2 is the right scope discipline.
- **Five rule types in §11.2.** `exists_before`, `near_before`, `overlap`, `above`, `after_all_required` is a defensible MVP rule grammar — concrete enough to implement, broad enough to express the BP Monitor SOP.
- **Three-status output** (`passed`/`failed`/`uncertain`/`skipped`) + overall `needs_review`. Matches the SOUP.md design and avoids the false-confidence trap.
- **Privacy log as a first-class output field** (§11.7). This is the demo-defining UX moment.
- **Tags vocabulary frozen in §9.2.** Seven tags, all needed for the five rules. No bloat.
- **YOLO `.npz` model installer rather than bundled model.** §9.3 keeps the `.app` small and dodges the AGPL/redistribution question for YOLO weights.

---

## 2. Critical gaps in PRD 2.0

### 2.1 The rule engine is described, not architected

§11 says "the rule engine is the real core implementation" but never says **where it lives in the repo**, **what its public API looks like**, or **how it gets tested independently of the app**. For a 2-day hackathon that's how you end up with rule logic tangled into SwiftUI view models on Day 2 night.

**Fix:** Adopt §3 of this doc — standalone Python package, sandbox-first, unit tests gate integration.

### 2.2 No story for generating rules at scale

PRD 2.0 §11.3 shows five hand-authored rules for one SOP. The product thesis in [README.md §1](../README.md) is a *marketplace* of SOPs. Hand-authoring does not scale, and the doc has no answer.

**Fix:** Adopt §4 of this doc — LLM-driven rule generation, validated against a JSON schema, gated by a human-readable diff before commit.

### 2.3 Shell-tech decision is left open in §6.4

"Tauri or Electron... SwiftUI is acceptable for a native-only prototype" — for a hackathon, "acceptable" means "do it." Tauri+Python sidecar is real engineering with codesigning headaches. You already proved SwiftUI + Python subprocess works in FaceBoxDemo. **Lock SwiftUI.**

### 2.4 VLM model manager is over-scoped for Day 1

§10 spends ~120 lines on SmolVLM/Moondream2 download/activate/delete flows with disk-space checks, registry files, and a question panel. Realistically:

- SmolVLM-MLX has a working path via mlx-vlm but is still finicky on M-series; Moondream2 has no official MLX port (open question §20.2 admits this).
- The 1-minute demo (§18.1) only needs the *appearance* of a VLM dropdown in the last 5 seconds.

**Fix:** Day 1 = no VLM code at all. Day 2 afternoon = optional. If you only get a "Local VLM — coming soon" disabled dropdown, the demo still hits §19 acceptance criteria 9–11 by showing the UI surface.

### 2.5 "Scene event builder" is hand-waved

§7.1 and §11.6 mention scene events but never define the conversion from `Detection[]` → `Event[]`. This is the most subtle piece of the pipeline and the most likely place for silent bugs. It needs its own sandbox module and test fixtures.

### 2.6 No fixture corpus → no E2E tests can be written

PRD 2.0 §16.5 lists eight BP fixture tests (`all_pass.json`, `cuff_too_low.json`, etc.) but never says who creates them or what format they're in. Without these, §17.4 E2E tests cannot exist. Treat the fixture corpus as a Day-1 deliverable, generated synthetically (hand-edited JSON), not from real video.

### 2.7 Open question §20.3 (bundle YOLO model?) blocks the demo

If the YOLO `.npz` is not bundled, every judge's first action is "install model" — and your one-minute demo loses 20 seconds. **Bundle the BP Monitor YOLO model** in `~/Library/Application Support/SoPilot/models/yolo/` via first-launch copy from the `.app/Contents/Resources/`. The "install YOLO model" flow stays as a real feature but isn't on the demo path.

---

## 3. Sandbox-first plan for the SOUP rule engine

This is the answer to user ask #1. Mirror the pattern that worked for [FaceBoxDemo](../sandbox/macCamera/): build, test, prove in `sandbox/`; only then integrate.

### 3.1 Folder layout

```text
sandbox/soup-engine/                  # standalone Python package
├── pyproject.toml                    # name="sopilot-rules", version=0.1.0
├── README.md                         # quick start, install, 5-line example
├── CHANGELOG.md                      # release notes from 0.1.0 onward
├── DEVELOPER.md                      # public API contract, rule grammar
├── LICENSE                           # MIT (engine is reusable across apps)
├── src/sopilot_rules/
│   ├── __init__.py                   # public exports: evaluate, RuleEngine, schemas
│   ├── schema.py                     # pydantic models: Rule, Detection, Event, StepResult, RunResult
│   ├── engine.py                     # RuleEngine.evaluate(detections, events, rules) -> RunResult
│   ├── geometry.py                   # bbox_center, distance_px, overlap_ratio, above_with_margin
│   ├── rules/
│   │   ├── __init__.py               # rule type registry
│   │   ├── exists_before.py
│   │   ├── near_before.py
│   │   ├── overlap.py
│   │   ├── above.py
│   │   └── after_all_required.py
│   ├── normalizer.py                 # raw YOLO MLX output -> Detection[]
│   ├── events.py                     # Detection[] -> Event[] (scene event builder)
│   └── evidence.py                   # best-frame selection, evidence trace
├── tools/
│   ├── rule_gen_cli.py               # LLM-driven rule generator (see §4)
│   └── validate_soup.py              # validates a .soup.json against schema
├── tests/
│   ├── conftest.py                   # shared fixtures
│   ├── unit/
│   │   ├── test_geometry.py          # UT-GEO-001..010
│   │   ├── test_normalizer.py        # UT-DET-001..008
│   │   ├── test_events.py            # UT-EVT-001..007
│   │   ├── test_rules_exists_before.py
│   │   ├── test_rules_near_before.py
│   │   ├── test_rules_overlap.py
│   │   ├── test_rules_above.py
│   │   ├── test_rules_after_all.py   # UT-RULE-001..016
│   │   └── test_privacy.py           # UT-PRIV-001..005
│   ├── fixtures/
│   │   ├── bp/
│   │   │   ├── all_pass.json
│   │   │   ├── missing_connector.json
│   │   │   ├── cuff_too_low.json
│   │   │   ├── elbow_hidden.json
│   │   │   ├── start_too_early.json
│   │   │   ├── no_start_event.json
│   │   │   ├── low_confidence_cuff.json
│   │   │   └── multiple_good_frames.json
│   │   └── bp_monitor.soup.json      # the rules under test
│   └── integration/
│       └── test_bp_end_to_end.py     # UT-BP-001..008
└── .github/workflows/ci.yml          # pytest on PR (optional for hackathon)
```

### 3.2 Public API (frozen for v0.1.0)

The app should never import anything outside this surface:

```python
from sopilot_rules import (
    RuleEngine,        # main entry point
    Detection,         # input dataclass
    Event,             # input dataclass
    RunResult,         # output dataclass
    SoupPackage,       # loaded .soup.json
    load_soup,         # path -> SoupPackage
    validate_soup,     # SoupPackage -> list[ValidationError]
)

engine = RuleEngine(soup=load_soup("bp_monitor.soup.json"))
result: RunResult = engine.evaluate(
    detections=[Detection(...), ...],
    events=[Event(type="start_button_pressed", timestamp=19.2, source="demo_marker")],
)
result.status            # "passed" | "needs_review" | "failed"
result.steps             # list[StepResult]
result.privacy_log       # dict
result.to_json()         # PRD 2.0 §11.7 exact shape
```

Three rules for this API:
- **Pure functions, no I/O.** The engine does not read files, hit the network, or touch the clock. The caller passes everything in.
- **Deterministic.** Same inputs → byte-identical output JSON. Required for the regression fixtures to work.
- **No YOLO dependency.** The engine never imports `mlx`, `yolo26mlx`, `cv2`, or `numpy>=2`. Detections come in as plain dataclasses. This is what makes it reusable by future apps.

### 3.3 Unit test matrix (gates integration)

Map every test ID from PRD 2.0 §16 into the test files above. Total: **62 unit tests + 8 fixture tests = 70 tests** before any integration with the macOS app.

| PRD 2.0 §16 | Test file | Count |
|---|---|---:|
| 16.1 Geometry | `test_geometry.py` | 10 |
| 16.2 Normalizer | `test_normalizer.py` | 8 |
| 16.3 Scene events | `test_events.py` | 7 |
| 16.4 Rule engine | `test_rules_*.py` | 16 |
| 16.5 BP fixtures | `test_bp_end_to_end.py` | 8 |
| 16.9 Privacy/provenance | `test_privacy.py` | 5 |
| **Subtotal (in scope for sandbox)** |  | **54** |
| 16.6 YOLO model manager | *not in this package* (app concern) | — |
| 16.7 VLM model manager | *not in this package* (app concern) | — |
| 16.8 Camera | *not in this package* (app concern) | — |

### 3.4 Integration gate

The macOS app may not import `sopilot_rules` until:

- [ ] All 54 unit tests pass on a clean checkout (`pytest sandbox/soup-engine/`).
- [ ] `pip install -e sandbox/soup-engine` succeeds in a fresh venv with only `pydantic` as a runtime dep.
- [ ] `python -m sopilot_rules.tools.validate_soup tests/fixtures/bp/bp_monitor.soup.json` exits 0.
- [ ] `DEVELOPER.md` lists the frozen public API and rule grammar.
- [ ] `CHANGELOG.md` has a `0.1.0` entry with the contract documented.

This gate is non-negotiable. If you skip it, you will be debugging rule logic in a Swift `@MainActor` view model at 3 AM on Day 2.

### 3.5 Suggested doc artifacts (companion to this PRD)

Create alongside the package:

- `doc/sandbox-doc/testPRD1.6-SoupEngine.md` — sandbox build doc, same style as `testPRD1.4-YoloMlxMac.md`.
- `sandbox/soup-engine/DEVELOPER.md` — API contract, rule grammar reference, fixture authoring guide.
- `sandbox/soup-engine/CHANGELOG.md` — `0.1.0 — initial release with 5 rule types and BP fixture corpus`.

---

## 4. LLM-driven rule generation

This is the answer to user ask #2. PRD 2.0 omits this entirely; for the product thesis to hold, rule authoring must be assisted by a mature LLM.

### 4.1 Two-track design

**Primary: offline CLI in `sandbox/soup-engine/tools/rule_gen_cli.py`** — runs at creator time, not user time. Calls Claude or ChatGPT API, emits `.soup.json`, validates it, prints a human-readable diff. Output is committed to source control. No runtime cloud dependency in the consumer path.

**Secondary: in-app Creator Mode hook (Day 2+ stretch)** — same prompt, same validator, called from the (currently mocked) Rule Studio screen. Requires user-supplied API key. Out of Day-1 scope; keep the design space open by reusing the CLI's `RuleGenerator` class.

### 4.2 CLI usage

```bash
# Generate rules from a plain-text SOP description
python -m sopilot_rules.tools.rule_gen_cli \
  --sop-text doc/sop-drafts/bp_monitor.txt \
  --tags blood_pressure_monitor,cuff,upper_arm,elbow_bend,grey_connector,button,screen \
  --model claude-opus-4-7 \
  --out packages/bp_monitor.soup.json

# Validate any .soup.json
python -m sopilot_rules.tools.validate_soup packages/bp_monitor.soup.json

# Diff against existing
python -m sopilot_rules.tools.rule_gen_cli \
  --sop-text doc/sop-drafts/bp_monitor.txt \
  --diff packages/bp_monitor.soup.json
```

### 4.3 Prompt scaffold (sketch)

```text
SYSTEM:
You are a SOP rule author. Output ONLY valid JSON matching the SOUP rule schema.
You may use exactly these rule types: exists_before, near_before, overlap, above, after_all_required.
You may reference only these tags: {tag_list}.
Every rule must have an id, type, and the required fields for its type (see schema).

USER:
SOP description:
{sop_text}

Existing rules (for diff context, may be empty):
{existing_rules_json}

Output a JSON object with a "rules" array. No prose, no markdown fences.
```

### 4.4 Validation pipeline (non-negotiable)

LLM output is **never** trusted directly. Every generated `.soup.json` runs through:

1. **JSON parse** — reject if invalid JSON.
2. **Pydantic schema validation** — reject if any rule has wrong shape/missing fields.
3. **Tag-closure check** — reject if any rule references a tag not in `tags[]`.
4. **Rule-ID uniqueness** — reject duplicates.
5. **Reference check** — `after_all_required.required_steps` must all exist.
6. **Dry-run on fixture corpus** — generated rules are run against the BP fixtures; any change in pass/fail outcome triggers a diff that the human must approve.

Only after all six checks pass is the file written. The CLI exits non-zero on any failure with a specific error message — easy to feed back into the LLM in a retry loop.

### 4.5 Human-in-the-loop gate

The CLI always prints a unified diff vs. the previous `.soup.json` and waits for `y/N` confirmation before overwriting (unless `--yes` is passed for CI). This is the "creator's signature" on the rules — the LLM is an assistant, not the author of record.

---

## 5. Risk register

This is the answer to user ask #3. Severity × Likelihood, with concrete mitigations.

| # | Risk | Sev | Lik | Mitigation |
|---|---|---|---|---|
| R1 | **YOLO MLX `.npz` model for BP Monitor doesn't exist** — PRD 2.0 §9.2 lists seven custom tags; no trained model is mentioned. Training a real BP detector in 2 days is infeasible. | High | High | **Use a YOLO26 COCO model + tag remapping for the demo.** Map COCO `cell phone`→`blood_pressure_monitor`, `person`→`upper_arm`, etc. Document the cheat in the demo script. Or hand-label ~50 frames + LoRA-style quick fine-tune; budget 4 GPU-hours. The honest path is to fake the model and be transparent about it. |
| R2 | **MLX + Python subprocess from SwiftUI is brittle** — JSON over stdio, MLX cold-start latency, Python venv discovery. | High | Med | Already partially solved in `sandbox/macCamera/Sources/FaceBoxDemo/YoloMLXWorker.swift`. Reuse that pattern. Add a `/api/health` check on app launch (PRD 2.0 §14.1). Keep the Python process alive for the session, not per-frame. |
| R3 | **Rule engine grows tendrils into the app** — without the §3 standalone package, rule logic ends up in Swift view models. | High | High | Hard gate in §3.4. CI fails if `sopilot_rules` has any non-pydantic runtime dep. Code review rejects any rule logic outside `sandbox/soup-engine/src/`. |
| R4 | **LLM-generated rules silently regress on existing fixtures** — Claude proposes a "better" rule that breaks BP-001. | Med | High | §4.4 step 6 — every generation runs the fixture corpus and surfaces any outcome change as a diff. No silent overwrites. |
| R5 | **VLM scope creep eats Day 2** — SmolVLM/Moondream2 download flows have unknowns (§20.1, §20.2). | Med | High | §2.4 — defer VLM code entirely. Disabled dropdown is enough for the demo. |
| R6 | **DMG codesigning blocks distribution** — judges' Macs reject unsigned `.app` from internet download. | Med | Med | Open question §20.5. Ad-hoc sign for internal demo (matches FaceBoxDemo today). If shipping externally, get a Developer ID cert before Day 2 morning — notarization takes ~15 min once you have the cert. |
| R7 | **Camera permission UX kills the cold-start demo** — first launch denies camera, judge sees blank screen. | Med | Med | Pre-launch the app once on the demo machine to grant permission. Implement §8.3 denied-state copy as a non-blocking fallback. |
| R8 | **Scene event builder produces wrong events** — silent semantic bug that makes rules fire on wrong frames. | High | Med | §2.5 — give it its own module + tests (`test_events.py`, 7 tests). Fixtures cover ordering, deduplication, missing-object cases. |
| R9 | **Privacy log is wrong** — claim "vlm_used: false" while a VLM call was made, or vice versa. Trust-breaking. | High | Low | Single source of truth: privacy log fields are set by the engine, not the caller. Tests UT-PRIV-001..005 verify the log against actual call traces. |
| R10 | **`.soup.json` schema drift** — engine v0.2.0 silently breaks v0.1.0 packages. | Med | Med | Schema version field in every `.soup.json`. Engine refuses to load packages with a major version newer than itself. Document in `DEVELOPER.md`. |
| R11 | **Bundle copy of YOLO model fails on first launch** — sandbox permissions block writing to `~/Library/Application Support/SoPilot/`. | Low | Med | Create the directory with `FileManager` in app init, not the Python sidecar. Test on a clean user account before demo. |
| R12 | **Two-day burn-down stalls on the macOS shell choice** — half a day lost evaluating Tauri vs SwiftUI. | High | Med | §2.3 — decision is already made by your FaceBoxDemo investment. Lock SwiftUI in the PRD revision. |
| R13 | **Demo runs against a video file but README claims live camera** — credibility hit during Q&A. | Low | Med | Be explicit in the demo script that live camera + sample video are both supported and the recording uses sample video for reproducibility. PRD 2.0 already allows this (§8.1). |
| R14 | **AGPL of yolo26-mlx infects the app** — distributing the `.app` bundling AGPL code may force open-sourcing SoPilot itself. | Med | Low | Keep `yolo26mlx` in a separate Python process (already the case). The Swift app does not statically link AGPL code. Document the separation. Consult counsel before any commercial release; not a hackathon blocker. |
| R15 | **LLM rule-gen API key handling** — accidentally committed key, or quota exhaustion mid-demo. | Med | Low | CLI reads key from `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` env vars only. `.gitignore` covers `.env`. Generate rules ahead of demo, not live. |

---

## 6. Recommended revisions to PRD 2.0 (concrete edits)

The following sections of PRD 2.0 should be amended:

1. **§3.1 (In Scope) — add:** "SOUP rule engine is delivered as a standalone Python package `sopilot-rules`, developed and tested in `sandbox/soup-engine/` before app integration."
2. **§3.1 — add:** "Offline CLI for LLM-assisted rule generation (`tools/rule_gen_cli.py`), with schema validation and human-review gate."
3. **§3.2 (Out of Scope) — add:** "In-app LLM rule generation (Creator Mode). Offline CLI only for hackathon."
4. **§6.4 (Packaging Recommendation) — replace:** "SwiftUI app shell + Python subprocess sidecar for YOLO MLX and the SOUP rule engine. Pattern already proven in [FaceBoxDemo](../sandbox/macCamera/). Tauri/Electron deferred to post-hackathon."
5. **§7.1 — add module:** "LLM Rule Generator (creator-time only, not in runtime app)."
6. **§9 — add §9.6:** "For the hackathon demo, a pre-bundled BP Monitor `.npz` is copied from `SoPilot.app/Contents/Resources/` to the local model directory on first launch. The user-driven Install YOLO Model flow remains a real feature but is not on the demo path." This resolves open question §20.3.
7. **§10 — defer to Day 2 stretch:** add "If Day 1 lands clean. Otherwise, show a disabled 'Local VLM — coming soon' dropdown to satisfy acceptance criteria §19.9–11 without code."
8. **§11 — add §11.0:** "The rule engine is the `sopilot-rules` Python package (v0.1.0), developed in [sandbox/soup-engine/](../sandbox/soup-engine/). The macOS app depends on it as a pip-installable module. See [DEVELOPER.md](../sandbox/soup-engine/DEVELOPER.md) for the public API contract."
9. **§16.5 — add note:** "Fixture corpus is hand-authored JSON in `sandbox/soup-engine/tests/fixtures/bp/`. No real video required for unit tests; integration tests use sample video at the app layer."
10. **§20 (Open Questions) — resolve §20.3** as in §6 of this doc; resolve §20.4 as **sample video by default** (more reliable for a recorded demo); resolve §20.6 as **Apple Silicon only** (MLX prerequisite, no point pretending otherwise).
11. **§21 (Build Priority) — restructure Day 1 Morning:**
    - Stand up `sandbox/soup-engine/` package skeleton + pydantic schemas.
    - Implement 5 rule types + geometry helpers.
    - Author BP fixture corpus (8 JSON files).
    - Run unit tests green (54 tests).
    - **Only then** start app shell work in the afternoon.

---

## 7. Concrete TODO (Day 1 morning, in order)

1. `mkdir -p sandbox/soup-engine/{src/sopilot_rules,tests,tools}` — bootstrap the package.
2. Write `pyproject.toml` with `pydantic>=2` as the only runtime dep.
3. Write `src/sopilot_rules/schema.py` — Detection, Event, Rule (5 subtypes), StepResult, RunResult, SoupPackage.
4. Write `geometry.py` — bbox_center, distance_px, overlap_ratio, above_with_margin. Write `test_geometry.py` first (10 tests, TDD).
5. Implement the 5 rule types one at a time, each with its own test file.
6. Author `tests/fixtures/bp/bp_monitor.soup.json` and the 8 fixture detection-stream JSONs.
7. Implement `engine.py` to glue rules + fixtures.
8. Run `pytest` — gate is green before lunch.
9. Write `DEVELOPER.md` (API contract) and `CHANGELOG.md` (v0.1.0 release note).
10. Sketch `tools/rule_gen_cli.py` with the prompt scaffold from §4.3 — implementation can land Day 2.
11. **Now** start on the macOS app: add `pip install -e sandbox/soup-engine` to the Swift app's Python sidecar setup, import `sopilot_rules`, wire it to the YOLO MLX worker.

---

## 8. Questions left for the team

These were not resolvable from the documents alone and should be answered before Day 1:

1. **YOLO model strategy for BP Monitor** — is there a real labeled dataset, or do we cheat with COCO + tag remapping for the demo? (R1 is the highest risk in the register.)
2. **Demo video source** — is there an existing BP Monitor video to use as the canonical sample, or do we record one on a phone?
3. **LLM rule-gen API budget** — Claude vs ChatGPT, who provides the key, what's the spend ceiling for Day 1 experiments?
4. **Distribution audience for the DMG** — internal-only submission, or public download? Drives R6 codesigning decision.
5. **Is there an existing creator (you?) who can write the BP SOP plain-text description that the LLM converts into rules?** This is the input to §4.2.

---

## 9. One-line summary

PRD 2.0 is shippable in 2 days **if** the rule engine becomes a standalone Python package in `sandbox/soup-engine/` on Day 1 morning, the VLM manager is deferred to a disabled dropdown, the macOS shell stays SwiftUI, and the LLM rule generator lands as an offline CLI with strict validation — everything else in PRD 2.0 is fine as written.
