# SoPilot PRD 2.0 — Architectural Review

**Reviewer:** Kimi (Senior Architect)  
**Date:** 2026-05-22  
**Context:** 2-day hackathon, BP Monitor SOP, YOLO26 MLX, OpenRouter LLM budget  
**Reviewing:** `doc/PRD2.0-lit.md` against `README.md`, `SOUP.md`, `yolo26-README.md`, sandbox work  
**Precedent:** `doc/Note1.1-kimi.md` (3-day scope, now compressed to 2 days)

---

## 1. Executive Summary

PRD 2.0 is a **well-scoped, credible hackathon document** with one critical flaw: it still assumes too much can be built in 2 days. The core insight of PRD 2.0 — "Real Monitoring, Mocked Creation" — is exactly right. The document should be treated as a **product vision**, not an execution checklist. For 2 days, we must cut to a **single vertical slice**: upload a video → YOLO detects → SOUP rules evaluate → result with evidence.

**Key decisions from this review:**

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Frontend | **React + Vite** (not SwiftUI, not Tauri) | FastAPI serves static files; no CORS; rapid screen building with shadcn/ui; user doesn't need to learn SwiftUI |
| Camera | **File upload primary**, live camera bonus | OpenCV file processing is deterministic; live camera adds risk for 2-day timeline |
| SOUP Engine | **Standalone Python package**, sandbox-tested first | Must be unit-testable before any UI integration |
| Rule Generation | **LLM-assisted authoring** via OpenRouter (GPT-4o/Claude) | Generates rule JSON from natural language SOP descriptions |
| YOLO Model | **Pre-train before hackathon** using Roboflow | 7 tags, ~50 images minimum, convert to `.npz` before Day 1 |

---

## 2. Frontend Stack Recommendation

### 2.1 The Decision: React + Vite, Served by FastAPI

You said you prefer Python/FastAPI and don't know frontend. For a 2-day hackathon, here is the ranked choice:

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **React + Vite** | Huge component ecosystem (shadcn/ui); FastAPI can serve `dist/` as static files; no CORS; one process | Must learn JSX + hooks basics | **✅ RECOMMENDED** |
| SwiftUI + HTTP to Python | Reuses `FaceBoxDemo` camera work; native menus | 26 screens in SwiftUI in 2 days is extremely high risk; bridging to Python adds complexity | ⚠️ Too slow for 2 days |
| Tauri + React | Native .app feel; Rust + React | Rust learning curve; Tauri build complexity; overkill for 2 days | ❌ Reject |
| Streamlit/Gradio | No frontend learning; pure Python | Cannot achieve PRD 2.0 UI fidelity; hard to package as .dmg | ❌ Reject |

**Why React wins for you:**
- **shadcn/ui** gives you pre-built, beautiful components (button, card, dialog, progress, table) that look like Apple's design language without writing CSS
- **FastAPI static file serving**: `app.mount("/", StaticFiles(directory="ui/dist", html=True))` — your entire frontend is just files served by Python
- **No separate frontend server**: One Python process starts, opens browser to `http://localhost:8000`, serves the React app AND the API
- **Camera via OpenCV**: Instead of SwiftUI camera, use `cv2.VideoCapture(0)` in Python, stream frames to React via WebSocket (`python-socketio` or FastAPI WebSocket)

### 2.2 Architecture Diagram

```text
┌─────────────────────────────────────────────────────────────┐
│  SoPilot.app (packaged with PyInstaller/py2app)             │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Python FastAPI Process                              │   │
│  │  ├── GET /health                                     │   │
│  │  ├── POST /validate/upload          (video → YOLO)   │   │
│  │  ├── GET /validate/{run_id}/status                   │   │
│  │  ├── GET /validate/{run_id}/result  (SOUP engine)    │   │
│  │  ├── GET /api/vlm/models                             │   │
│  │  ├── WS /camera/stream              (OpenCV → React) │   │
│  │  └── StaticFiles("/", "ui/dist")    (React app)      │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  React + Vite Frontend                               │   │
│  │  ├── Launch Screen                                   │   │
│  │  ├── Upload / Camera Selector                        │   │
│  │  ├── Live Overlay (WebSocket frames)                 │   │
│  │  ├── Result Screen                                   │   │
│  │  ├── Evidence Review                                 │   │
│  │  └── Settings (VLM Manager)                          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Packaging for .dmg (Hackathon Grade)

For the 2-day demo, use **PyInstaller** to bundle the Python environment + React `dist/` into a single executable:

```bash
# Build React
npm run build   # outputs ui/dist/

# Package Python + dist/
pyinstaller --onefile --add-data "ui/dist:ui/dist" start.py

# start.py:
#   1. Starts FastAPI (serves static files from ui/dist/)
#   2. Opens browser to http://localhost:8000
#   3. Blocks until user quits
```

Wrap the resulting executable in a minimal `.app` bundle (Automator or Platypus) for drag-to-Applications behavior. This is **not production-grade** but works for a hackathon demo.

> **Note:** The existing `FaceBoxDemo.app` SwiftUI work is **not wasted**. It becomes your "camera tech demo" — a separate mini-app that proves native macOS camera access works. Show it to judges as evidence of camera capability, but use the React/FastAPI path for the main SOP demo.

---

## 3. SOUP Rule Engine — Standalone Package Design

### 3.1 Core Principle: Test in Sandbox Before Integration

The SOUP rule engine must be developed as a **standalone, reusable Python package** in `sandbox/soup-engine/` and achieve **100% unit test coverage** before it ever touches FastAPI or React.

**Why standalone?**
- Deterministic rule evaluation is the **core product differentiator** — it cannot be buggy
- Unit tests must run in milliseconds, not requiring the full app stack
- Reusability: the same engine can be used by CLI scripts, Jupyter notebooks, or future mobile apps
- Debugging: when a rule gives unexpected results, you want to isolate it in a test, not trace through WebSocket → React → FastAPI → engine

**Package structure:**

```text
sandbox/soup-engine/
├── README.md                    # Developer documentation
├── CHANGELOG.md                 # Release notes
├── pyproject.toml               # Standalone package: pip install -e .
├── soup_engine/
│   ├── __init__.py
│   ├── schema.py                # Pydantic models: Rule, Detection, Event, Result
│   ├── geometry.py              # bbox math: IoU, distance, above/below, center
│   ├── rules/
│   │   ├── __init__.py
│   │   ├── base.py              # AbstractRule interface
│   │   ├── exists_before.py     # exists_before rule type
│   │   ├── near_before.py       # near_before rule type
│   │   ├── overlap.py           # overlap rule type
│   │   ├── above.py             # above rule type
│   │   └── after_all_required.py # after_all_required rule type
│   ├── engine.py                # SOUPRuleEngine: loads rules, evaluates run
│   ├── evidence.py              # EvidenceFrame selector (best confidence frame)
│   └── loader.py                # Load .soup.json → Python objects
└── tests/
    ├── conftest.py              # Shared fixtures
    ├── test_geometry.py         # All geometry primitives (15 tests)
    ├── test_rules/              # One test file per rule type
    │   ├── test_exists_before.py
    │   ├── test_near_before.py
    │   ├── test_overlap.py
    │   ├── test_above.py
    │   └── test_after_all_required.py
    ├── test_engine.py           # Full pipeline tests (fixture-based)
    └── fixtures/                # JSON test inputs
        ├── bp_all_pass.json
        ├── bp_missing_connector.json
        ├── bp_cuff_too_low.json
        ├── bp_elbow_hidden.json
        └── bp_start_too_early.json
```

### 3.2 Developer Documentation (README.md)

The `sandbox/soup-engine/README.md` should contain:

1. **Quick Start**: `pip install -e .` + run a fixture test in 30 seconds
2. **Rule Type Reference**: Each rule type with JSON schema, parameters, and example
3. **Adding a New Rule**: Implement `AbstractRule`, add to `rules/__init__.py`, add tests
4. **Fixture Format**: How to write a `.json` fixture for a new SOP
5. **Running Tests**: `pytest tests/ -v`
6. **Release Notes**: Version history (start at `0.1.0-hackathon`)

### 3.3 Unit Test Strategy (Mirroring YOLO26 MLX Approach)

YOLO26 MLX was validated before integration via `sandbox/test-yolo-inference.py` (4 phases: basic, compatibility, benchmark, COCO). The SOUP engine should follow the same pattern:

**Phase A — Geometry Primitives (Day 1, Hour 1)**
```python
def test_iou_fully_overlapping():
    a = BBox(0, 0, 100, 100)
    b = BBox(0, 0, 100, 100)
    assert iou(a, b) == 1.0

def test_above_with_margin():
    cuff = BBox(100, 50, 150, 100)   # center_y = 75
    elbow = BBox(100, 120, 150, 170) # center_y = 145
    assert is_above(cuff, elbow, margin_px=20) is True

def test_above_uncertain_boundary():
    # cuff center_y is only 15px above elbow center_y
    # ambiguity_margin_px = 30 → uncertain
    assert is_above(cuff, elbow, margin_px=20, ambiguity_margin_px=30) == "uncertain"
```

**Phase B — Individual Rule Types (Day 1, Hour 2–3)**
Each rule type gets 5–10 tests covering pass, fail, uncertain, and edge cases:

| Test | Rule | Input | Expected |
|------|------|-------|----------|
| `test_exists_before_pass` | exists_before | monitor detected at t=2, start at t=10 | passed |
| `test_exists_before_fail` | exists_before | no monitor before start | failed |
| `test_exists_before_uncertain` | exists_before | monitor confidence = 0.3 (< 0.5 threshold) | uncertain |
| `test_near_before_pass` | near_before | connector 80px from monitor (< 120px max) | passed |
| `test_overlap_pass` | overlap | cuff IoU with arm = 0.35 (> 0.25 min) | passed |
| `test_above_pass` | above | cuff center 50px above elbow | passed |
| `test_above_uncertain` | above | cuff center 10px above elbow (within 30px ambiguity) | uncertain |

**Phase C — Full Engine Pipeline (Day 1, Hour 4)**
Use JSON fixtures that simulate complete detection sequences:

```python
def test_bp_all_pass():
    soup = load_soup("tests/fixtures/bp_all_pass.json")
    engine = SOUPRuleEngine(soup)
    detections = load_detections("tests/fixtures/bp_all_pass_detections.json")
    result = engine.evaluate(detections)
    assert result.overall_status == "passed"
    assert all(s.status == "passed" for s in result.steps)
```

**Phase D — Performance / Determinism (Day 1, Hour 5)**
```python
def test_engine_is_deterministic():
    # Same input → same output, always
    result1 = engine.evaluate(detections)
    result2 = engine.evaluate(detections)
    assert result1 == result2  # or JSON-serialized equality
```

### 3.4 Integration Gate

The SOUP engine **may not be integrated** into FastAPI until:

- [ ] All 15 geometry tests pass
- [ ] All 25+ rule tests pass (5 rule types × 5 tests each)
- [ ] All 5 BP fixture tests pass
- [ ] `pytest` runs in under 5 seconds total
- [ ] A second person (or Claude/Codex) can read the README and run tests successfully

This gate is non-negotiable. The rule engine is the product's core. A buggy engine destroys credibility.

---

## 4. LLM Rule Generation Strategy

### 4.1 Approach: LLM-Assisted Authoring, Not Fully Automated

You have OpenRouter budget. Use it to **accelerate rule authoring**, not to eliminate human judgment.

**The workflow:**

```text
1. Human describes SOP in natural language:
   "The blood pressure monitor must be visible before the start button is pressed.
    The grey connector should be attached to the monitor. The cuff must be on the
    upper arm and above the elbow bend. Finally, start should only be pressed
    after all setup steps are complete."

2. Human provides tag list:
   [blood_pressure_monitor, cuff, upper_arm, elbow_bend, grey_connector, button, screen]

3. LLM (GPT-4o via OpenRouter) generates draft rule JSON

4. Human reviews and adjusts thresholds (confidence, distance_px, margin_px)

5. Human runs fixture tests; LLM helps debug failures
```

### 4.2 Prompt Template

Save this as `sandbox/soup-engine/prompts/generate_rules.txt`:

```
You are a SOUP rule engine architect. Convert a natural language SOP into
a JSON array of SOUP rules.

Available rule types:
- exists_before: object must be detected before an event
- near_before: object A must be near object B before an event
- overlap: object A must overlap object B (IoU > threshold)
- above: object A must be above object B (center_y with margin)
- after_all_required: event must occur after all listed steps pass

Available object tags: {{tags}}

SOP description:
{{sop_description}}

Constraints:
- min_confidence default: 0.5
- max_distance_px for near_before: 120
- min_overlap_ratio for overlap: 0.25
- margin_px for above: 20
- ambiguity_margin_px for above: 30 (produces "uncertain" if within this range)

Output ONLY a JSON array. No markdown fences. No explanation.
Each rule must have: id, type, step_id, and type-specific fields.
```

### 4.3 OpenRouter Integration Script

```python
# sandbox/soup-engine/scripts/generate_rules.py
import json, os, requests

API_KEY = os.environ["OPENROUTER_API_KEY"]
MODEL = "openai/gpt-4o"  # or "anthropic/claude-3.5-sonnet"

def generate_rules(sop_description: str, tags: list[str]) -> list[dict]:
    prompt = load_prompt("generate_rules.txt").replace("{{tags}}", json.dumps(tags)).replace("{{sop_description}}", sop_description)
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }
    )
    return json.loads(resp.json()["choices"][0]["message"]["content"])
```

### 4.4 Validation Pipeline

LLM-generated rules must pass through a validation layer before use:

```python
def validate_rules(rules: list[dict], allowed_tags: list[str]) -> tuple[bool, list[str]]:
    errors = []
    required_fields = {"id", "type", "step_id"}
    for r in rules:
        if not required_fields.issubset(r.keys()):
            errors.append(f"Rule {r.get('id', '?')} missing required fields")
        if r.get("tag") and r["tag"] not in allowed_tags:
            errors.append(f"Rule {r['id']} uses unknown tag: {r['tag']}")
        # ... more validation
    return len(errors) == 0, errors
```

**Cost estimate:** One rule generation call ≈ $0.02–$0.05. Iterative debugging (10 calls) ≈ $0.50. Negligible.

---

## 5. Complete Risk Register

| # | Risk | Probability | Impact | Mitigation |
|---|------|------------|--------|------------|
| R1 | **2 days is insufficient for PRD 2.0 scope** | High | Critical | Cut to single vertical slice: upload video → detect → rules → result. Mock everything else. |
| R2 | **BP Monitor YOLO model not trained before hackathon** | Medium | Critical | Pre-train on Roboflow **before** Day 1. Minimum 50 images, 7 tags. Convert to `.npz`. Have backup COCO-trained `yolo26n.npz` that detects generic objects as fallback. |
| R3 | **React learning curve slows frontend** | Medium | High | Use shadcn/ui copy-paste components. Skip animations. Focus on 4 screens max: Upload, Progress, Result, Evidence. |
| R4 | **SOUP rule engine has edge-case bugs** | Medium | Critical | Sandbox testing gate (§3.4). No integration until 100% unit test pass. Use fixture-driven testing. |
| R5 | **LLM-generated rules are semantically wrong** | Medium | High | Human review step. Validation layer. Start with hand-written rules, use LLM only for iteration. |
| R6 | **OpenRouter API down or slow during demo** | Low | Medium | Cache generated rules to JSON files. Demo uses pre-generated rules, not live LLM calls. |
| R7 | **PyInstaller packaging fails or app won't launch** | Medium | High | Test packaging on Day 1 afternoon, not Day 2 evening. Have `python start.py` fallback (Terminal launch). |
| R8 | **AGPL license concern from judges** | Low | Medium | Include AGPL attribution in About dialog. State "open-source core" as a strength, not a liability. |
| R9 | **Demo video fails (YOLO misses tags)** | Medium | Critical | Pre-record 3 "golden" demo videos where YOLO works reliably. Test them end-to-end before hackathon. |
| R10 | **Camera permission denied during live demo** | Medium | Medium | Use file upload as primary demo path. Camera is a bonus feature shown separately. |
| R11 | **YOLO26 MLX version conflict (mlx 0.31.x hang)** | Low | High | `pyproject.toml` already caps `mlx<0.31`. Pin exact version in requirements. |
| R12 | **VLM download too large/slow for demo** | Medium | Medium | Skip live VLM download in demo. Show "installed" state with pre-downloaded stub or mock. |
| R13 | **FastAPI + React static files CORS/port issues** | Low | Medium | FastAPI serves static files from same origin (`/`). No CORS. Use fixed port (8000) with retry logic. |
| R14 | **Team member cannot run React dev server** | Low | Low | Document exact Node version. Use `npx` to avoid global install. Provide `npm install` script. |

---

## 6. Revised 2-Day Execution Plan

### Day 1 — Core Pipeline (Backend + Rule Engine)

**Goal:** A working Python script that takes a video file and outputs a SOUP result JSON.

| Time | Task | Output |
|------|------|--------|
| 0:00–0:30 | Set up `sandbox/soup-engine/` package structure, `pyproject.toml`, pytest | `pytest` runs, 0 tests (passes) |
| 0:30–1:30 | Implement `geometry.py` (IoU, distance, above/below, center) + unit tests | 15 geometry tests pass |
| 1:30–3:00 | Implement 5 rule types + individual tests | 25 rule tests pass |
| 3:00–4:00 | Write 5 BP fixture JSONs + full engine pipeline tests | 5 fixture tests pass |
| 4:00–5:00 | Build `FrameSampler` (OpenCV → frames at 2 FPS) | Video → frame sequence works |
| 5:00–6:00 | Build `YOLOWrapper` (load `.npz`, run inference on frames) | Frame → detections JSON works |
| 6:00–7:00 | Integrate: sampler → YOLO → engine → result JSON | End-to-end Python script works |
| 7:00–8:00 | Start FastAPI skeleton, add `/health`, `/validate/upload` | API returns 200 |

**End of Day 1 gate:** Run `python -m soup_engine.tests` → all pass. Run `python demo_pipeline.py test_video.mp4` → produces `result.json` with step statuses.

### Day 2 — UI + Packaging + Demo

**Goal:** A React UI that calls the Day 1 backend, shows result, and can be packaged.

| Time | Task | Output |
|------|------|--------|
| 0:00–1:00 | Scaffold React + Vite + shadcn/ui, add API client | `npm run dev` shows blank app |
| 1:00–2:30 | Build Upload screen + Progress screen | User can upload video, see progress stages |
| 2:30–4:00 | Build Result screen + Evidence Review screen | Shows step pass/fail/uncertain + evidence frame |
| 4:00–5:00 | Build Settings screen (VLM manager UI, mock data) | Shows FastVLM/SmolVLM with install/activate/delete |
| 5:00–6:00 | PyInstaller packaging test | `SoPilot.app` launches, opens browser, works |
| 6:00–7:00 | Create .dmg with Applications shortcut | `SoPilot.dmg` ready |
| 7:00–8:00 | Rehearse demo script 5 times | Smooth 1-minute demo |

**End of Day 2 gate:** Double-click `SoPilot.dmg` → drag to Applications → double-click app → upload video → see result with evidence.

---

## 7. Pre-Hackathon Checklist (Must Complete Before Day 1)

These items cannot be done during the 2-day hackathon:

- [ ] **Train BP Monitor YOLO model** on Roboflow (7 tags, 50+ images)
- [ ] **Convert model** to `.npz` using `yolo-mlx converters convert`
- [ ] **Record 3 demo videos:** correct workflow, wrong workflow, ambiguous workflow
- [ ] **Verify YOLO detects all 7 tags** reliably on demo videos
- [ ] **Pre-generate SOUP rules** (hand-written or LLM-assisted) for BP Monitor
- [ ] **Write fixture JSONs** for all 5 test scenarios (all_pass, missing_connector, cuff_low, elbow_hidden, start_early)
- [ ] **Test PyInstaller** on your Mac to confirm packaging works
- [ ] **Install Node.js + npm** and verify `npx create-vite@latest` works

---

## 8. What PRD 2.0 Should Explicitly Cut for 2 Days

PRD 2.0 §3.1 lists 12 "In Scope" items. For 2 days, cut these:

| PRD Item | Cut? | Reason |
|----------|------|--------|
| Live camera preview (§3.1 #3) | **Cut to bonus** | File upload is deterministic; live camera adds risk |
| VLM model download (§3.1 #9) | **Mock only** | Show UI with fake "installed" state; no real download |
| VLM question box (§3.1 #10) | **Mock only** | Show text box + canned response; no real inference |
| Creator mock pages (§3.1 #11) | **Reduce to 2 screens** | Dashboard + Package Export animation only |
| E2E tests (§3.1 #12) | **Cut** | Unit tests on engine + manual demo rehearsal suffice |
| E2E test plan (§17) | **Cut** | All 64 E2E scenarios cannot be automated in 2 days |
| VLM model manager tests (§16.7) | **Cut to 3 tests** | Registry, path safety, activate/deactivate only |
| Camera E2E (§17.2) | **Cut** | Manual test only |
| YOLO Model E2E (§17.3) | **Cut to 2 tests** | Install + activate only |
| VLM Model E2E (§17.5) | **Cut** | All mocked |
| Creator Mock E2E (§17.6) | **Cut** | Visual only |
| Regression E2E (§17.7) | **Cut** | Out of scope |

**What stays:**
- Upload video → frame sampling → YOLO detection → SOUP rule evaluation → result JSON → React UI display
- 4 React screens: Upload, Progress, Result, Evidence
- SOUP rule engine with 5 rule types, fully unit tested
- Settings screen with VLM manager (mocked)
- Creator dashboard + export animation (mocked)

---

## 9. Open Questions Resolved

| PRD 2.0 Open Question (§20) | Resolution |
|-----------------------------|------------|
| SmolVLM HF repo | Use `apple/FastVLM-0.5B` as primary (per `testPRD1.5-VLM-Mac.md`); skip Moondream for 2-day scope |
| Moondream 2 runtime | Skip for hackathon; mock only |
| YOLO `.npz` bundled or manual | **Manual select** — app asks user to pick `.npz` file on first launch; simpler than bundling |
| Live camera or sample video default | **Sample video default** — pre-loaded `demo_correct.mp4`; live camera as bonus |
| DMG signed or ad-hoc | **Ad-hoc** — Gatekeeper bypass via right-click → Open; notarize is post-hackathon |
| Minimum Mac hardware | **Apple Silicon only** — MLX requirement; no Intel fallback |

---

## 10. One-Line Summary

> **Build a standalone, fully unit-tested SOUP rule engine in `sandbox/soup-engine/` (Python, pytest, fixtures) before touching any UI. Pre-train the BP Monitor YOLO model on Roboflow and convert to `.npz` before Day 1. Use React + Vite for the frontend, FastAPI to serve it, and PyInstaller for hackathon-grade `.dmg` packaging. Mock the VLM and Creator flows. Demo with pre-recorded videos, not live camera.**
