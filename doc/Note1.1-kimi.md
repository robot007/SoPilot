# SoPilot Architectural Review — Note 1.1

**Reviewer:** Kimi (Senior Architect)  
**Date:** 2026-05-21  
**Context:** 3-day hackathon, single use case (Blood Pressure Monitor SOP), <5 YOLO tags, MLX is non-negotiable, iPhone PWA dropped due to MLX macOS dependency.

---

## 1. Executive Summary

SoPilot has a **strong product vision** and a **well-documented design language**, but there is a significant gap between the design ambition (26 screens, 4 epics, 30+ DB tables) and what is achievable in 72 hours. The decision to anchor on **YOLO26 MLX** (macOS-only, Apple Silicon) is correct for the "local-first" narrative, but it forces the consumer runtime to be a **macOS desktop application**, not an iPhone PWA.

**Verdict:** The project is architecturally sound at the conceptual level, but the implementation plan needs aggressive scope reduction and a clear technology stack decision for the consumer app. The schema is over-engineered for a hackathon; the UI designs are excellent but must be narrowed to a vertical slice.

**Hackathon Goal:** Deliver one complete blood-pressure-monitor workflow that a creator can (appear to) build and a consumer can (actually) run end-to-end locally on a Mac, with all 4 epics represented in the UI even if some backend paths are mocked or pre-staged.

---

## 2. Critical Architecture Decisions

### 2.1 Consumer App Platform: macOS Desktop, Not iPhone PWA

**Issue:** YOLO26 MLX requires macOS + Apple Silicon (M1/M2/M3/M4). It cannot run on iPhone iOS. `mobileAppDesign.md` still targets iPhone as the primary form factor.

**Decision:** The consumer-facing "App" must run on macOS. The iPhone screens should be reframed as **"future mobile companion" mockups** or dropped. The MacBook layouts in `mobileAppDesign.md` become the primary demo surface.

**Recommended Stack for Consumer App:**

| Layer | Recommendation | Rationale |
|-------|---------------|-----------|
| **ML Runtime** | Python 3.11+ + YOLO26 MLX (`src/yolo26mlx/`) | Non-negotiable; pure MLX, Metal GPU |
| **Backend API** | FastAPI (local server, `localhost:8000`) | Python-native, fast to build, easy YOLO integration |
| **Frontend UI** | React 18 + TypeScript (Vite) | Rapid development of 26 screens; matches design doc fidelity |
| **Packaging** | `start_sopilot.sh` script or Tauri wrapper | Opens browser + starts FastAPI; good enough for hackathon |
| **Alternative** | Streamlit/Gradio | Faster but cannot achieve the Apple-inspired UI in the design doc. **Not recommended.** |

> **Why not SwiftUI?** Building 26 screens in SwiftUI in 3 days while also integrating Python MLX via PythonKit is extremely high risk. A local web stack lets the team leverage the excellent screen designs in `mobileAppDesign.md` with CSS/React, while keeping the MLX runtime in its native Python environment.

### 2.2 Creator vs. Consumer Boundary

**Clarified Model:**
- **Creator:** Uses a cloud-connected web portal (or the same Mac app in "Creator Mode") to publish packages, videos, and models to cloud storage (R2/Supabase Storage) and metadata to PostgreSQL.
- **Consumer:** Runs the Mac app locally. Downloads SOUP packages (JSON + model weights) from the cloud store once, then runs entirely offline. Optional: syncs validation run summaries to cloud DB.

**Implication:** The consumer app must work **offline-first** after package installation. This is actually a strength for the hackathon demo — you can demo the consumer flow on a Mac with Wi-Fi disabled after package download.

### 2.3 Database Strategy: Two-Tier for Hackathon

**Issue:** `PRD1.2-schema.md` and `PRD1.3-schemaV0.md` define ~30 tables. This is a production schema, not a hackathon schema.

**Recommendation:** Split into two tiers:

- **Cloud Tier (Creator + Store):** Use **Supabase** (PostgreSQL + Auth + Storage + Edge Functions) instead of raw Neon + R2. It gives you Auth, Row-Level Security, and Storage APIs in one platform, saving ~1 day of integration work. If the team insists on Neon + R2, that is acceptable but slower.
- **Local Tier (Consumer Runtime):** Use **SQLite** (via SQLAlchemy or even JSON files) for validation runs, detections, and evidence. Do not force the consumer app to write to cloud PostgreSQL in real time during inference — it adds latency and ruins the "local-first" story.

**Hackathon Schema (Maximum 10 Tables):**

```text
users                  -- Supabase Auth (handled for free)
soup_packages          -- 1 row: BP Monitor
soup_versions          -- 1 row: v0.1.0
tags                   -- ~5 rows: monitor, cuff, connector, button, arm
annotations            -- Minimal training labels (pre-loaded)
model_artifacts        -- 1 row: bp-yolo26n.npz
creator_projects       -- 1 row: BP Monitor Project
workflow_videos        -- 3-5 demo videos
rule_conditions        -- ~5 rules (geometry)
rule_steps             -- ~5 steps
validation_runs        -- Consumer run history
run_detections         -- YOLO output per frame
run_step_results       -- Rule evaluation results
evidence_items         -- Frames/clips for evidence review
```

Tables to **omit entirely** for hackathon MVP:
- `training_jobs` (pre-train the model before the hackathon)
- `model_eval_runs`, `model_eval_items` (mock the metrics UI)
- `event_order_rules` (sequence logic can be hardcoded for 1 use case)
- `rule_authoring_sessions` (simplify to direct rule editing)
- `package_reviews`, `run_reports` (post-MVP)
- `chat_threads`, `chat_messages` (if time permits, mock the chat UI with hardcoded responses)

### 2.4 YOLO Model Strategy: Pre-Stage Training

**Issue:** The Creator Epic (E1) includes data collection, frame extraction, labeling, and YOLO training. A full training pipeline cannot be built AND executed in 3 days.

**Recommendation:**
1. **Before hackathon:** Collect 30–50 images/videos of the blood pressure monitor workflow. Label bounding boxes for 5 tags. Fine-tune `yolo26n` using the MLX training pipeline (`model.train()`).
2. **During hackathon:** The "Train YOLO Model" screen in the creator flow should be a **replay/wizard** that shows the pre-staged dataset, simulates a training progress bar, and produces the pre-trained `.npz` file. This is a demo necessity, not engineering dishonesty — you are showing the *workflow*, and you can disclose that training was pre-run for time.
3. **Consumer runtime:** Load `bp-monitor-yolo26n.npz` directly via `YOLO("...")` and run `model.predict()` / `model.track()` on uploaded/recorded videos.

**Model Output Format:** Use `.npz` (MLX native), not `.pt`. The converter script (`yolo-mlx converters convert`) can be run before the hackathon.

### 2.5 Rule Engine: Keep It Deterministic and Simple

**Observation:** The rule types in `SOUP.md` and `PRD1.3-schemaV0.md` (`inside`, `outside`, `overlap`, `orientation`, `position`, `transform_position`, `bridge_relation`, `vlm_confirmation`, `fusion`) are well-designed but too many for a hackathon.

**Recommendation:** Implement exactly **3 rule types** for the BP monitor demo:

1. **`presence`** — Is the tag detected in the frame with confidence > threshold?
2. **`overlap`** — Do two bounding boxes overlap (IoU > threshold)?
3. **`orientation`** — Is box A above/below/left/right of box B (with angle tolerance)?

These three cover all 5 BP monitor steps:
- Monitor visible → `presence(monitor)`
- Connector attached → `overlap(connector, monitor)` or `presence(connector)`
- Cuff on upper arm → `overlap(cuff, arm)`
- Cuff above elbow → `orientation(cuff, elbow, direction="above")`
- Start pressed after setup → temporal ordering (hardcoded logic, not a generic rule type)

The Rule Engine should be a pure Python module that takes:
- `soup_json` (the loaded SOUP package)
- `run_detections` (list of frame-by-frame YOLO outputs)
- Returns `run_step_results` + `evidence_items`

### 2.6 Local VLM vs. Cloud VLM for Hackathon

**Issue:** The design documents heavily feature a "Local Open VLM" (e.g., LLaVA via Ollama) that generates scene events. Running a local VLM alongside YOLO26 MLX on a Mac is feasible but adds significant complexity (another model download, memory pressure, API surface).

**Recommendation:**
- **Skip true Local VLM integration for the hackathon MVP.**
- Replace "Local Open VLM → Scene Events" with **rule-derived scene events**. The Rule Engine can generate synthetic scene events (e.g., `cuff_on_upper_arm` detected at frame 47) directly from YOLO + geometry.
- For the **Guarded Hybrid / Ambiguity Gate** demo, use a **cloud VLM** (OpenAI GPT-4o-mini or Google Gemini Flash) with a redacted crop. This is easier to integrate (single HTTP call) and makes the privacy/redaction story more tangible in the demo.
- The UI should still show "Local Open VLM: standby / used" in the decision pipeline animation, but the backend can short-circuit it.

> **Demo Narrative:** "In the MVP, scene events are generated directly from local YOLO detections. The architecture has a hook for local VLM when subtle visual reasoning is needed. For this demo, the ambiguity gate uses a minimized cloud advisory."

### 2.7 Video Input and Frame Sampling

**Issue:** The Frame Sampler is mentioned but not architecturally specified. For a Mac app, video input can come from:
- File upload (existing `.mov`/`.mp4`)
- Webcam (live camera feed)
- iPhone Continuity Camera (if we want to show phone-as-camera)

**Recommendation:**
- Support **file upload** as the primary input for the hackathon. It is deterministic and avoids real-time streaming complexity.
- Support **webcam** as a secondary "live preview" feature using OpenCV (`cv2.VideoCapture(0)`) with a 5-second recording buffer.
- Frame sampling: simple interval-based extraction (e.g., 2 FPS) using OpenCV or ffmpeg-python. Store frames in a local temp directory.

---

## 3. Document-by-Document Review

### 3.1 `README.md` — Product Vision ✅

**Strengths:**
- Excellent pitch and differentiation (not a cloud VLM wrapper).
- Clear runtime modes (All Local / Guarded Hybrid).
- Good cost estimation and build-vs-fine-tune guidance.
- Hackathon demo flow (Section 8) is well-structured and should be the demo script.

**Gaps:**
- **Repository structure (Section 6)** is outdated and generic. It suggests `app/mobile/` and `app/desktop_runtime/`, but the actual repo already contains `yolo26mlx/` as a Python package. Needs to be rewritten to match the real stack.
- **Next recommended build steps (Section 11)** are reasonable but do not reflect the 3-day constraint. Needs a hackathon-specific roadmap.

### 3.2 `PRD1.1-basic.md` — MISSING ❌

File is empty. Either delete it or merge its content into `README.md` / `SOUP.md`. For a hackathon, do not maintain empty placeholder files — they create confusion.

### 3.3 `PRD1.2-schema.md` + `PRD1.3-schemaV0.md` — Schema Design ⚠️

**Strengths:**
- Comprehensive, production-ready schema.
- Good separation of metadata (PostgreSQL) and binaries (R2).
- Strong privacy auditing fields (`raw_video_leaves_device`, `decision_trace`, etc.).
- Normalized rule tables (`rule_conditions`, `rule_actions`, `rule_steps`) are well-designed.

**Issues:**
- **Over-engineered for 3 days.** 30 tables with JSONB GIN indexes, foreign key cascades, and full eval pipelines cannot be implemented, tested, and demoed in 72 hours.
- **Table naming inconsistency:** `PRD1.2` uses `soup_conditions`, `soup_actions`, `soup_steps` while `PRD1.3` uses `rule_conditions`, `rule_actions`, `rule_steps`. Pick one. I recommend `rule_*` because it is clearer.
- **`consumer_configs` vs. `consumer_runtime_configs`:** `PRD1.2` uses `consumer_runtime_configs` but `PRD1.3` uses `consumer_configs`. Align them.
- **No local/offline schema:** The schema assumes constant cloud connectivity. The consumer runtime should be able to function with a local SQLite copy of `soup_versions`, `rule_conditions`, etc.
- **`video_frames` table:** Storing every extracted frame as a DB row with a URI is fine for cloud, but local frame extraction should just use a temp folder with sequential filenames.

### 3.4 `mobileAppDesign.md` — UI/UX Specification ✅⚠️

**Strengths:**
- Extremely detailed screen descriptions (26 screens).
- Apple-inspired design language is appropriate and premium-feeling.
- Privacy copy is consistent and well-branded.
- Animation and micro-interaction requirements are specific.

**Issues:**
- **iPhone-first assumption is now invalid.** Screens 7 (Live Camera Overlay) and 8 (Offline Progress) assume a portrait mobile form factor. These need MacBook-desktop adaptations.
- **MacBook layouts are under-specified.** The doc says "desktop sidebar navigation, large dashboard panels, wider data tables, video preview panel, and right-side inspector/chat panel" but does not provide the same level of detail as the iPhone screens.
- **Creator Mode Screen 21 (AI Rule Studio)** references "Lovable-style AI design interface." This is ambiguous. Specify whether it is a chat-to-rule interface, a visual node editor, or a form builder. For a hackathon, a **chat-to-rule form** is fastest.

### 3.5 `yolo26-README.md` / YOLO26 MLX — ML Runtime ✅

**Strengths:**
- Pure MLX, no PyTorch runtime dependency. Perfect for local-first story.
- Supports detection, tracking, segmentation, training.
- COCO validation accuracy is within 0.5% of official — credible.
- Tracking (ByteTrack/BoT-SORT) and Segmentation are bonus features.

**Concerns:**
- **AGPL-3.0 License.** This is a copyleft license. If SoPilot is distributed, it may need to be open-sourced under AGPL as well. Verify license compatibility before public release.
- **Python-only API.** There is no HTTP API or C library. Integration requires embedding Python or running a Python process. This reinforces the FastAPI-local-server recommendation.
- **Model weights:** The `download_yolo26_models.sh` downloads `.pt` files (PyTorch format) that must be converted to `.npz` via `yolo-mlx converters convert`. This conversion step must be pre-run before the hackathon demo.

### 3.6 `SOUP.md` — Package Format ✅

**Strengths:**
- Clean JSON structure.
- Good separation of `package`, `runtime`, `models`, `tags`, `steps`, `rules`.
- Runtime policy explicitly declares local decision authority.
- MVP validation checklist is practical.

**Recommendations:**
- **Lock `soup_version` to `"0.1.0-hackathon"`** to avoid versioning complexity.
- **Simplify `models.detector.format`:** Use `"npz"` or `"mlx"`, not `"pt"`, for the consumer runtime.
- **Add a `hackathon_demo` flag** to the package JSON so the UI can show "Hackathon Preview" badges where data is mocked.
- **Remove `fsm` (finite state machine)** from the hackathon `.soup` — it is a placeholder and adds conceptual weight without value.

---

## 4. Technical Recommendations

### 4.1 Recommended Project Structure

```text
sopilot/
├── README.md
├── SOUP.md
├── start.py                      # Single command: starts FastAPI + opens browser
├── pyproject.toml                # Python deps: fastapi, uvicorn, yolo26mlx, opencv-python, supabase-py
│
├── runtime/                      # LOCAL CONSUMER RUNTIME (Python)
│   ├── __init__.py
│   ├── main.py                   # FastAPI app
│   ├── sampler.py                # Frame extraction (OpenCV)
│   ├── detector.py               # YOLO26 MLX wrapper
│   ├── tracker.py                # Optional: ByteTrack wrapper
│   ├── rule_engine.py            # Deterministic rule evaluator
│   ├── reporter.py               # Compliance score + evidence generator
│   ├── redactor.py               # Crop + blur for ambiguity gate
│   └── local_db.py               # SQLite models (SQLAlchemy or plain SQLite)
│
├── soup_packages/                # Local SOUP storage
│   └── bp_monitor_v010.soup.json
│   └── bp_monitor_yolo26n.npz    # Pre-trained model weights
│
├── ui/                           # CONSUMER + CREATOR UI (React/Vite)
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── screens/              # One folder per screen from mobileAppDesign.md
│   │   │   ├── LaunchScreen.tsx
│   │   │   ├── HomeDashboard.tsx
│   │   │   ├── SoupStore.tsx
│   │   │   ├── PackageDetail.tsx
│   │   │   ├── InstallConfig.tsx
│   │   │   ├── StartCheck.tsx
│   │   │   ├── LiveOverlay.tsx
│   │   │   ├── OfflineProgress.tsx
│   │   │   ├── AmbiguityGate.tsx
│   │   │   ├── ResultChat.tsx
│   │   │   ├── EvidenceReview.tsx
│   │   │   ├── CreatorDashboard.tsx
│   │   │   ├── NewPackage.tsx
│   │   │   ├── CaptureData.tsx
│   │   │   ├── LabelTags.tsx
│   │   │   ├── TrainModel.tsx      # Simulated/wizard
│   │   │   ├── TestModel.tsx       # Pre-staged metrics
│   │   │   ├── RuleStudio.tsx
│   │   │   ├── TryRunRules.tsx
│   │   │   ├── PackageExport.tsx
│   │   │   ├── RunsReports.tsx
│   │   │   ├── Settings.tsx
│   │   │   └── ReportDetail.tsx
│   │   ├── components/           # Reusable: ChecklistItem, YoloOverlay, PrivacyBadge
│   │   ├── hooks/                # useValidation, useSoupPackage, useDetections
│   │   └── api/                  # Axios client calling localhost:8000
│   └── public/
│       └── demo_videos/          # Pre-loaded sample videos for instant demo
│
├── creator_backend/              # CLOUD CREATOR API (optional for hackathon)
│   └── supabase/                 # Migrations, edge functions, storage policies
│
└── doc/
    ├── PRD1.1-basic.md           # DELETE or merge
    ├── PRD1.2-schema.md          # Keep as production reference
    ├── PRD1.3-schemaV0.md        # Keep as production reference
    ├── mobileAppDesign.md        # Keep; adapt Mac screens
    └── Note1.1-kimi.md           # This file
```

### 4.2 API Surface (FastAPI)

Minimal endpoints for hackathon:

```text
GET  /health                      → MLX available? GPU active?
GET  /packages                    → List installed local SOUP packages
GET  /packages/{id}               → Load soup_json
POST /validate/upload            → Upload video, start validation run
POST /validate/webcam/start      → Start webcam capture (optional)
POST /validate/webcam/stop       → Stop and process buffer
GET  /validate/{run_id}/status   → Poll progress: sampling → detecting → rules → done
GET  /validate/{run_id}/result   → Full result: steps, evidence, decision trace
POST /validate/{run_id}/ambiguity → Trigger cloud VLM on redacted crop (Guarded Hybrid demo)
GET  /evidence/{item_id}         → Serve frame/clip image
```

### 4.3 Data Flow (Consumer Runtime)

```text
User uploads video
      │
      ▼
FrameSampler (OpenCV, 2 FPS)
      │
      ▼
YOLO26 MLX (local .npz model)
      │
      ▼
RunDetections → SQLite (local)
      │
      ▼
RuleEngine (deterministic, local)
      │
      ▼
RunStepResults + EvidenceItems
      │
      ▼
If ambiguous & Guarded Hybrid:
   Redactor → crop + blur → Cloud VLM (HTTP)
   → Advisory summary → RuleEngine (final local eval)
      │
      ▼
Result UI + Chat UI (React calling local FastAPI)
```

### 4.4 Creator Flow Simplification for Hackathon

The Creator Epic does not need a real-time training pipeline during the demo. Instead:

1. **New SOUP Package** → Form fills `soup_packages` + `soup_versions` locally.
2. **Capture Training Data** → Upload 3 pre-recorded demo videos. Show thumbnails.
3. **Extract Frames** → Run OpenCV extraction locally, show frame grid.
4. **Label Tags** → Load pre-staged annotations (COCO JSON). Show bounding boxes. Allow minor adjustments.
5. **Train YOLO Model** → **Wizard / Simulation.** Show dataset summary, model config, then play a progress bar that "trains" for 30 seconds while loading the pre-trained `.npz` into the model directory.
6. **Test YOLO Model** → Run inference on a validation frame. Show pre-computed metrics (recall, precision) from a JSON file.
7. **AI Rule Studio** → Chat interface where the user types "Cuff should be above elbow." The backend maps this to a `rule_conditions` row with `type="orientation"`. Show parameter sliders.
8. **Try Run Rules** → Run the local RuleEngine on a test video. Show pass/fail.
9. **Package SOUP** → Serialize `soup_json` + copy model to `soup_packages/`. Optionally POST metadata to Supabase.

> **Key Point:** The creator flow is a **UI-heavy, compute-light wizard**. All heavy lifting (training, metrics) is pre-staged. This is the only way to show all 4 epics in 3 days.

---

## 5. Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| YOLO26 MLX installation fails on demo Mac | Medium | Critical | Pre-install on demo machine; bring a second Mac; have a Docker fallback |
| Custom YOLO model performs poorly on demo video | Medium | High | Pre-record a "golden" demo video that works reliably; have 2 backup videos |
| React + FastAPI integration takes too long | Medium | High | Start with a monorepo and a single `start.py` script; avoid CORS issues by serving React from FastAPI static files |
| Guarded Hybrid cloud VLM call fails / is slow | Low | Medium | Mock the cloud VLM response for the demo; show the redaction UI but return a canned advisory |
| Rule Engine logic is buggy for edge cases | Medium | Medium | Hardcode the BP monitor rules; do not attempt generic rule parser |
| 26 screens cannot all be built in 3 days | High | High | Group screens into reusable layouts; use a component library (shadcn/ui or MUI); skip animations on Day 1–2 |
| AGPL license concern blocks distribution | Low | Medium | Add LICENSE note acknowledging YOLO26 MLX AGPL origin; plan to open-source SoPilot under AGPL or replace MLX post-hackathon |

---

## 6. 3-Day Hackathon Execution Plan

### Day 1 — Foundation & Detection Pipeline

**Goal:** A Mac app that can upload a video and see YOLO bounding boxes.

- [ ] **P0** Finalize stack: FastAPI + React, confirm Python 3.11+ and MLX install on demo Mac.
- [ ] **P0** Set up monorepo: `runtime/` (FastAPI) and `ui/` (React/Vite).
- [ ] **P0** Integrate YOLO26 MLX: Load `yolo26n.npz`, run `model.predict()` on a test image, return JSON bounding boxes.
- [ ] **P0** Build FrameSampler: OpenCV video → extract frames at 2 FPS → save to temp dir.
- [ ] **P0** Build `POST /validate/upload` endpoint: accepts video, runs sampler + detector, stores detections in SQLite.
- [ ] **P1** Build React screens: Launch, Home, Start Check, Offline Progress (skeleton only).
- [ ] **P1** Pre-stage BP monitor demo video and verify YOLO detects all 5 tags.

### Day 2 — Rules, Results & Creator Flow

**Goal:** End-to-end consumer validation + Creator Mode UI skeleton.

- [ ] **P0** Build RuleEngine with 3 rule types (`presence`, `overlap`, `orientation`).
- [ ] **P0** Hardcode BP monitor `soup_json` with 5 steps and 5 rules.
- [ ] **P0** Build `GET /validate/{run_id}/result` endpoint: returns step results + evidence items.
- [ ] **P0** Build React screens: Result with Chat, Evidence Review, Ambiguity Gate (UI only), Settings.
- [ ] **P1** Build Creator screens: Creator Dashboard, New Package, Capture Data, Label Tags (pre-loaded annotations), Train Model (wizard), Test Model (pre-staged metrics).
- [ ] **P1** Build React components: ChecklistItem, YoloOverlay, PrivacyBadge, ProgressPipeline.
- [ ] **P2** Add basic animations: step completion (green slide), YOLO box fade-in.

### Day 3 — Integration, Polish & Demo Script

**Goal:** All 4 epics demoable. One smooth end-to-end flow.

- [ ] **P0** Build SOUP Store screen (1 featured package: BP Monitor) + Install Config screen.
- [ ] **P0** Build Rule Studio screen: chat-to-rule interface that edits the hardcoded `soup_json`.
- [ ] **P0** Build Package Export screen: exports `.soup.json` to disk.
- [ ] **P0** Integrate Ambiguity Gate with a mocked cloud VLM response (redaction UI + canned advisory).
- [ ] **P0** Write and rehearse hackathon demo script (follow `README.md` Section 8 flow).
- [ ] **P1** Add decision trace logging to every screen.
- [ ] **P1** Add privacy language badges consistently.
- [ ] **P2** Add SQLite → cloud sync for `validation_runs` (optional).
- [ ] **P2** Add Runs / Reports history screen.

---

## 7. Prioritized TODO List

### P0 — Must Have (Demo Breaks Without This)

1. [ ] **Delete or populate `doc/PRD1.1-basic.md`.** Empty files are technical debt.
2. [ ] **Decide consumer app stack.** I recommend FastAPI + React local server. Document in `README.md`.
3. [ ] **Pre-train BP monitor YOLO model** (`yolo26n`, 5 tags) before hackathon starts. Convert to `.npz`.
4. [ ] **Pre-record 3 demo videos:** 1 correct, 1 wrong (start early), 1 ambiguous (cuff low).
5. [ ] **Implement FrameSampler + YOLO detector wrapper** in Python FastAPI.
6. [ ] **Implement RuleEngine** with 3 rule types (`presence`, `overlap`, `orientation`).
7. [ ] **Build hardcoded `bp_monitor_v010.soup.json`** with 5 steps, 5 rules, model reference.
8. [ ] **Build React screens:** Launch, Home, Start Check, Offline Progress, Result, Evidence Review.
9. [ ] **Build `POST /validate/upload` + `GET /validate/{id}/result` APIs.**
10. [ ] **Rehearse demo flow end-to-end** at least 5 times before judging.

### P1 — Should Have (Demo Is Compelling)

11. [ ] **Build Creator Mode screens** (dashboard, new package, capture, label, train wizard, test, rule studio, export).
12. [ ] **Build SOUP Store + Install Config screens.** Even if there is only 1 package.
13. [ ] **Build Ambiguity Gate UI** with redaction preview. Mock cloud VLM response.
14. [ ] **Add decision trace visualization** to Result screen.
15. [ ] **Add privacy badges** ("Raw video stayed local", etc.) to all runtime screens.
16. [ ] **Set up Supabase project** for creator metadata and package store (if time permits).
17. [ ] **Add YOLO bounding box overlay** on video frames in Evidence Review.
18. [ ] **Implement local SQLite schema** for `validation_runs`, `run_detections`, `run_step_results`, `evidence_items`.

### P2 — Nice to Have (Demo Wins Awards)

19. [ ] **Add live webcam support** (`cv2.VideoCapture`) for a "real-time" demo segment.
20. [ ] **Add tracking** (ByteTrack) to maintain object IDs across frames.
21. [ ] **Add chat UI** with hardcoded helpful responses based on `recovery_policy`.
22. [ ] **Add PDF report export** (or JSON download as placeholder).
23. [ ] **Add iPhone Continuity Camera** support so the Mac app can use the iPhone camera wirelessly.
24. [ ] **Add true local VLM** (e.g., Qwen2.5-VL via Ollama) as a post-MVP architecture hook.
25. [ ] **Add segmentation masks** instead of bounding boxes for cuff/arm overlap (visual wow factor).

---

## 8. Open Questions for Team

1. **Consumer App Technology:** Do you accept the recommendation of FastAPI + React running locally? Or do you want to explore Tauri, Electron, or pure Swift?
2. **Cloud Backend:** Can we use Supabase for the hackathon to save setup time, or is Neon + R2 a firm requirement?
3. **Demo Video Availability:** Do you already have blood pressure monitor video footage, or do we need to acquire one before Day 1?
4. **Team Composition:** How many engineers, and what are their strengths (frontend, Python, ML, design)? This affects whether we can parallelize React + FastAPI effectively.
5. **Judging Criteria:** Is the hackathon judged on working code, UI polish, or business pitch? This determines whether Day 3 should prioritize bug fixes or demo rehearsal.

---

## 9. One-Line Architectural Summary

> **Build a local macOS web app (FastAPI + React) that runs YOLO26 MLX inference and a deterministic rule engine offline, wraps it in a polished Apple-style UI for 26 screens, pre-stages the YOLO training and metrics for the creator flow, and mocks the cloud VLM ambiguity gate so all 4 epics are demoable in 3 days.**
