# Note 1.3 — Codex Architect Review for SoPilot

**Reviewer:** Codex, senior architect lens  
**Date:** 2026-05-22  
**Inputs reviewed:** `README.md`, `doc/PRD1.1-basic.md`, `doc/PRD1.2-schema.md`, `doc/PRD1.3-schemaV0.md`, `doc/mobileAppDesign.md`, `SOUP.md`, `yolo26-README.md`, and the local `yolo26mlx` source/package metadata.  
**Scope:** Architecture opinion, feasibility review, schema/design critique, YOLO26 MLX integration guidance, and TODO list for an iPhone PWA-oriented SoPilot product.

---

## 1. Executive Opinion

SoPilot has a strong core product idea: package physical SOPs into portable `.soup` definitions, use computer vision to extract evidence, and keep the final compliance decision inside a local deterministic rule engine. That is the right differentiation. It is much stronger than a generic "upload video to VLM and ask if it passed" product.

The most important architectural issue is this:

> **An iPhone PWA cannot directly run YOLO26 MLX.**

YOLO26 MLX is a Python + MLX + Metal runtime for Apple Silicon macOS. It is excellent for a Mac local runtime, but it is not an in-browser iPhone runtime. The project must therefore choose one of these product shapes:

1. **Recommended for current requirement:** iPhone PWA as the capture/UI client, paired with a local Mac YOLO26 MLX runtime on the same network. The PWA records or uploads video; the Mac performs frame sampling, YOLO26 MLX inference, tracking, rule evaluation, evidence generation, and optional guarded cloud calls.
2. **Recommended if strict on-device iPhone local processing is mandatory:** native iOS app with CoreML model artifacts, not a PWA and not MLX.
3. **Possible but weak fit:** browser-only PWA using ONNX/WebGPU/WASM, not MLX. This sacrifices the explicit YOLO26 MLX requirement and increases browser compatibility risk.
4. **Not recommended for the product promise:** cloud Apple-Silicon MLX service. It could use MLX technically, but it breaks the local-first consumer privacy story unless it is clearly branded as cloud processing.

My recommendation is to define SoPilot v0.1 as:

> **iPhone PWA + local Mac Runtime Companion.**

The iPhone PWA gives the user-friendly mobile capture and review experience. The Mac runtime gives you YOLO26 MLX, local file access, local SQLite, optional local VLM, and a credible "final decision is local" story. This is the only path that preserves the user's iPhone PWA direction while honestly using YOLO26 MLX.

---

## 2. Top P0 Decisions

These decisions should be made before building more UI or schema.

### 2.1 Define the runtime boundary

Current docs say "iPhone PWA" and also "YOLO / Tracker local" and "Local Open VLM". Those cannot all happen inside the iPhone browser.

Define the boundary as:

```text
iPhone PWA
  - login/install UI
  - package browsing
  - camera capture/upload
  - run progress display
  - result/evidence/chat UI
  - consent gate for guarded hybrid

Local Mac Runtime Companion
  - package download and integrity verification
  - YOLO26 MLX model loading
  - frame sampling
  - detection/tracking
  - optional local VLM
  - deterministic rule engine
  - local SQLite run database
  - evidence clips/frames
  - redaction/minimization before cloud
  - final local rule evaluation

Cloud Control Plane
  - SOUP store metadata
  - creator project metadata
  - package/model hosting in R2
  - optional guarded cloud VLM proxy
  - optional sync, never required for local run execution
```

This model lets the product truthfully say:

- The iPhone controls the workflow.
- The user's raw video is processed by their own local Mac runtime.
- YOLO26 MLX is used where it can actually run.
- Final rule evaluation is still local.

### 2.2 Rename "All Local" more precisely in PWA context

If processing happens on a paired Mac, "All Local" means local to the user's trusted local machine or local network, not local inside the iPhone browser.

Recommended copy:

- **All Local:** Video is processed by your paired local Mac runtime. YOLO, rules, evidence, and final decision stay off the cloud.
- **Guarded Hybrid:** Local Mac runtime processes first. Only if a step is ambiguous, SoPilot can send a redacted/minimized crop to a cloud VLM after confirmation. The final decision remains local.

Avoid implying that an iPhone PWA itself runs MLX.

### 2.3 Split the product into three planes

The docs currently mix consumer runtime, creator workflow, store, model hosting, local-first privacy, and cloud VLM under one schema. Split the architecture mentally and in docs:

```text
1. Creator Plane
   Cloud-friendly. Uses Neon/R2. Stores training videos, frames, labels, model artifacts, package versions.

2. Store / Control Plane
   Cloud metadata. Packages, versions, reviews, install counts, creator profiles, model artifact manifests.

3. Consumer Runtime Plane
   Local-first. Runs on Mac companion for v0.1. Stores validation runs, detections, evidence, reports, privacy logs locally.
```

Without this split, the local-first promise will keep contradicting the cloud database schema.

---

## 3. Review of Input Documents

### 3.1 `README.md`

Strengths:

- The product promise is clear: local-first SOP video checking, final decision made by local rules, optional guarded cloud assistance.
- The four epics are understandable and map to real product flows.
- The decision pipeline is directionally correct: frame sampler, YOLO/tracker, local VLM scene events, rule engine, compliance result, optional cloud fallback.
- The "not a cloud VLM wrapper" positioning is valuable and should remain central.

Issues:

- It does not resolve the runtime platform question. It describes a local stack, but the current user requirement is iPhone PWA plus YOLO26 MLX. The README should explicitly state that YOLO26 MLX runs in the Mac runtime companion, not inside the iPhone PWA.
- The suggested repository structure does not match the actual repo. The repo currently looks like a YOLO26 MLX package with SoPilot docs layered on top. The README should separate "current repository state" from "target SoPilot product structure".
- The cost section is useful but too early for the immediate architecture. The highest-risk cost is not GPU training; it is engineering time to build reliable capture, pairing, local runtime, rule engine, and evidence trace.
- "Raw video stays local" needs scope. It can be true for consumer validation runs, but creator training videos are explicitly R2-hosted in the schema.

Suggested change:

Add a "Runtime Architecture" section before the epics:

```text
For v0.1, SoPilot uses an iPhone PWA for capture and review, paired with a local Mac Runtime Companion for YOLO26 MLX inference and local rule evaluation. A future native iOS app may run CoreML artifacts directly on-device.
```

### 3.2 `doc/PRD1.1-basic.md`

This file is empty.

That is a documentation problem because the filename implies it is the foundational PRD. Either:

- delete it,
- rename it to `PRD1.1-placeholder.md`, or
- fill it with the actual product requirements summary.

Recommended content for `PRD1.1-basic.md`:

- Product thesis.
- Target user roles.
- P0 workflows.
- Runtime target for v0.1.
- Non-goals.
- Success metrics.
- Privacy claims.
- Definitions of SOP, SOUP, All Local, Guarded Hybrid, Local Mac Runtime Companion.

### 3.3 `doc/PRD1.2-schema.md`

Strengths:

- Correctly separates PostgreSQL metadata from R2 binary storage.
- Correctly treats `.soup` JSON as a portable artifact.
- Captures the main lifecycle: creator project, training data, YOLO jobs, model artifacts, rules, packages, installs, runs, evidence, chat.
- Mentions encrypted API key references instead of raw key storage.

Issues:

- It is a summary document, but it overlaps heavily with `PRD1.3-schemaV0.md`.
- It uses table names that drift from PRD1.3:
  - `soup_conditions` vs `rule_conditions`
  - `soup_actions` vs `rule_actions`
  - `soup_steps` vs `rule_steps`
  - `consumer_runtime_configs` vs `consumer_configs`
  - `run_scene_events` vs `run_events`
  - `run_rule_results` exists here but is missing from PRD1.3
- The MVP table list is too large for a first build.
- It still assumes the database is the center of all product behavior. For consumer local-first runtime, local storage is the center.

Suggested change:

Keep PRD1.2 as the conceptual schema overview, but update it to match PRD1.3 names exactly. Add a section called "Cloud schema vs local runtime schema".

### 3.4 `doc/PRD1.3-schemaV0.md`

This is the best schema document and should become the canonical schema starting point after edits.

Strengths:

- Contains concrete SQL.
- Uses creator-friendly `tags` with internal `yolo_class`, which is the right split.
- Versioned `soup_versions` is correct.
- `soup_json` as source of truth is correct.
- `evidence_items.rule_snapshot` is good because it preserves explainability when rules change later.
- `model_eval_items` is a good future loop for model improvement.

Major issues:

1. **It does not model the PWA + Mac runtime architecture.**
   The schema assumes cloud tables but does not specify what lives locally on the Mac runtime or in the PWA.

2. **Model artifact format values need correction.**
   Current values include `pt`, `onnx`, `mlx`, `coreml`. For YOLO26 MLX, the real runtime formats are more specific:
   - `pt_source`
   - `mlx_npz`
   - `mlx_safetensors`
   - `onnx`
   - `coreml_mlpackage`

3. **`soup_versions.model_uri` and `model_format` are too scalar.**
   A `.soup` package needs a runtime artifact manifest. The iPhone PWA + Mac runtime plan needs at least:
   - Mac MLX artifact (`.npz` or `.safetensors`)
   - optional iOS CoreML artifact (`.mlpackage`) for future native app
   - optional ONNX artifact for browser/cloud fallback experiments
   - sha256 and size for each artifact

4. **`decision_trace` is missing from PRD1.3 `validation_runs`.**
   README and PRD1.2 both emphasize traceability. PRD1.3 must add it.

5. **`run_rule_results` is missing.**
   Storing condition results inside `run_events.condition_results` is acceptable for a demo, but not for strong auditability. A failed step should be traceable to specific rule conditions.

6. **Array columns are not portable.**
   `text[]`, `uuid[]`, and PostgreSQL-specific defaults are fine for Neon, but the local runtime should use SQLite. Use JSON arrays if the same schema is expected to run locally.

7. **API key handling is unresolved.**
   The UI asks for API keys, PRD1.2 mentions encrypted refs, PRD1.3 omits the table. For PWA, do not store sensitive keys in localStorage. Prefer a backend proxy for cloud VLM and R2 management. If a native app exists later, use Keychain.

Recommended schema direction:

- PRD1.3 remains the cloud/control-plane schema.
- Add a separate `doc/PRD1.4-local-runtime-schema.md` for Mac runtime SQLite.
- Add `models_manifest jsonb` to `soup_versions`.
- Add `decision_trace jsonb default '[]'::jsonb` to `validation_runs`.
- Re-add `run_rule_results`, or explicitly document why rule results are embedded in `run_events`.

### 3.5 `doc/mobileAppDesign.md`

Strengths:

- Strong and consistent visual direction.
- Good privacy language.
- Correctly emphasizes that final decision is local.
- Captures the consumer journey from install to run to evidence review.
- Captures creator aspirations: training data, labeling, model training, rule studio, packaging.

Issues:

- It is a design-generation prompt, not an implementation-ready product spec.
- It asks for 27 screens across iPhone, iPad, and MacBook. That is too broad for v0.1.
- It describes local YOLO, local VLM, and local rule engine without saying where those run in an iPhone PWA architecture.
- On-phone creator labeling is not a good MVP path. Drawing boxes on an iPhone is possible but inefficient and expensive to polish.
- API key storage in a PWA is risky and needs a backend/key-management decision before implementation.
- The design leans heavily on explanatory text. For a production tool, the runtime screen should be operational and evidence-led, not a privacy brochure on every screen.

Recommended v0.1 screen set:

1. Launch / Pair Runtime
2. Home / Installed Packages
3. SOUP Store
4. Package Detail
5. Install / Runtime Mode
6. Start SOP Check
7. Upload/Record Progress
8. Analysis Progress
9. Ambiguity Gate
10. Result Summary
11. Evidence Review
12. Settings / Runtime Pairing / Privacy

Creator screens should be Mac-first or deferred:

- Creator Dashboard
- Rule Studio
- Package Export

Everything else can be a shell or future milestone.

### 3.6 `SOUP.md`

This is one of the strongest documents in the repo. It correctly frames `.soup` as the product contract.

Strengths:

- Clear separation of perception, scene events, and rules.
- Correct local-final-decision principle.
- Good MVP validation checklist.
- Good test case concept.
- Good blocked inputs for cloud VLM.

Required improvements:

- Convert the conceptual package shape into a real JSON Schema file.
- Add runtime capability requirements.
- Add model artifact manifest with multiple platform artifacts.
- Add package signature and artifact hash requirements.
- Add a redaction policy section that is machine-readable, not just copy.
- Add rule grammar versioning.
- Add package migration/version compatibility policy.

Recommended `.soup` top-level shape:

```json
{
  "schema_version": "0.1.0",
  "package": {},
  "capabilities": {},
  "runtime_policy": {},
  "privacy_policy": {},
  "models": {
    "detector": {
      "kind": "yolo26",
      "artifacts": []
    }
  },
  "tags": [],
  "steps": [],
  "rules": [],
  "event_order": [],
  "redaction": {},
  "outputs": {},
  "tests": []
}
```

### 3.7 `yolo26-README.md` and local YOLO26 MLX package

The YOLO26 MLX project is real and useful for SoPilot, but only in the right runtime.

Observed from docs/source:

- Requires macOS with Apple Silicon.
- Requires Python 3.10+.
- Requires `mlx>=0.30.3,<0.31`.
- Provides pure MLX inference and training.
- Supports detection, tracking, and segmentation.
- Supports `.npz` and `.safetensors` loading in code.
- Can load `.pt` by converting/loading through its converter path, but `.pt` should not be treated as the preferred runtime package artifact.
- License is AGPL-3.0-only.

Architectural implications:

- Use YOLO26 MLX in the Mac Runtime Companion.
- Prefer `yolo26n` or `yolo26s` for the first SOP package.
- Do not require tracking for the BP monitor v0.1 unless object identity across time is truly needed.
- Treat `.pt` as source/training artifact, not consumer runtime artifact.
- Add `sha256`, `size_bytes`, `class_names`, `input_size`, `task`, and `format` to model artifact metadata.
- Review AGPL obligations before commercial distribution. This matters especially if SoPilot wraps or exposes YOLO26 MLX over a network API.

---

## 4. Recommended v0.1 Architecture

### 4.1 System architecture

```text
                           Cloud Control Plane
                  ┌─────────────────────────────────┐
                  │ Neon: package/store metadata     │
                  │ R2: model/package assets         │
                  │ Optional cloud VLM proxy         │
                  └───────────────▲─────────────────┘
                                  │ package metadata/assets
                                  │ optional guarded cloud call
                                  │
┌─────────────────────┐    paired │     ┌──────────────────────────────┐
│ iPhone PWA           │◀──────────┼────▶│ Local Mac Runtime Companion   │
│ - capture/upload     │ HTTPS/WSS │     │ - YOLO26 MLX                  │
│ - progress UI        │          │     │ - frame sampler               │
│ - consent gates      │          │     │ - local rules                 │
│ - results/evidence   │          │     │ - local SQLite                │
│ - package browsing   │          │     │ - evidence files              │
└─────────────────────┘          │     │ - redaction before cloud       │
                                 │     └──────────────────────────────┘
                                 │
                         final decision remains here
                         in local rule engine
```

### 4.2 Mac Runtime Companion responsibilities

The Mac runtime should be treated as a local service, not just a script.

P0 API surface:

```text
GET  /health
  returns runtime version, YOLO availability, model formats, local VLM availability

POST /pair
  establishes trusted PWA session

GET  /packages
  lists installed local SOUP packages

POST /packages/install
  downloads .soup and model artifact, verifies sha256, stores locally

POST /runs
  creates validation run

POST /runs/{id}/video
  uploads recorded video or chunks from PWA

GET  /runs/{id}/events
  server-sent events or WebSocket for progress

GET  /runs/{id}/result
  final compliance result and decision trace

GET  /runs/{id}/evidence/{evidence_id}
  returns local evidence frame/clip to paired PWA

POST /runs/{id}/ambiguity/{step_id}/approve-cloud
  user-approved guarded hybrid call
```

P0 runtime modules:

```text
runtime/
  package_store.py       # local .soup install, artifact verification
  sampler.py             # frame extraction
  detector_yolo_mlx.py   # wrapper over yolo26mlx.YOLO
  rule_engine.py         # deterministic rule evaluation
  decision_trace.py      # audit trace builder
  evidence_store.py      # local frames/clips/redaction previews
  redaction.py           # ROI crop first, face/background later
  api.py                 # local HTTPS/WSS API
  db.py                  # SQLite
```

### 4.3 iPhone PWA responsibilities

The PWA should not pretend to be the inference runtime.

P0 PWA modules:

```text
pwa/
  pairing/
    runtime discovery or manual URL
    QR pairing/token entry
  package/
    store list
    package detail
    install mode selection
  capture/
    camera recording
    upload progress
  run/
    live status
    ambiguity gate
    result summary
    evidence review
  settings/
    paired runtime status
    privacy mode
    cloud fallback consent defaults
```

Important PWA constraints to validate in a spike:

- camera capture quality and file size on iPhone
- upload reliability for long videos
- local network connection from iPhone to Mac
- HTTPS certificate or pairing flow
- background behavior if the user locks the phone
- storage quota if videos are temporarily stored before upload
- recovery if upload is interrupted

### 4.4 Cloud control plane responsibilities

Keep cloud out of the compliance decision.

P0 cloud:

- package metadata
- package version metadata
- model artifact hosting
- signed manifest
- optional cloud VLM proxy for guarded hybrid

Defer:

- full creator collaboration
- marketplace reviews
- remote training orchestration
- analytics beyond basic install counts

---

## 5. Data and Schema Recommendations

### 5.1 Separate cloud schema from local runtime schema

Cloud schema is for:

- users
- creator projects
- training assets
- model artifacts
- package versions
- store metadata
- optional cloud-side logs

Local runtime schema is for:

- installed packages
- runtime configs
- validation runs
- detections
- events
- rule results
- step results
- evidence items
- privacy logs
- local chat context

The current PRD combines these too tightly.

### 5.2 Minimal local runtime schema

For the Mac Runtime Companion, start with:

```sql
installed_packages
package_versions
runtime_configs
validation_runs
run_frames
run_detections
run_events
run_rule_results
run_step_results
evidence_items
privacy_log_entries
chat_threads
chat_messages
```

Use local SQLite. Store UUIDs as text. Store JSON as text with JSON validation in the service layer.

### 5.3 Minimal cloud/control schema

For v0.1 cloud:

```sql
users
creator_projects
project_assets
workflow_videos
video_frames
tags
annotations
model_artifacts
soup_packages
soup_versions
package_assets
```

Defer:

- `training_jobs`
- `model_eval_runs`
- `model_eval_items`
- normalized rule tables
- `package_reviews`
- cloud `validation_runs`
- cloud chat history

For v0.1, model training can be manual/CLI and model metrics can live inside `model_artifacts.metrics`.

### 5.4 `soup_versions` should use a manifest

Replace scalar model fields with:

```sql
alter table soup_versions
  add column models_manifest jsonb not null default '{}'::jsonb,
  add column package_manifest jsonb not null default '{}'::jsonb,
  add column signature jsonb,
  add column published_at timestamptz,
  add column published_by uuid;
```

The manifest should include:

```json
{
  "detector": {
    "kind": "yolo26",
    "task": "detect",
    "input_size": 640,
    "class_names": ["monitor", "cuff", "upper_arm", "elbow_bend", "grey_connector"],
    "artifacts": [
      {
        "platform": "mac_mlx",
        "format": "mlx_npz",
        "uri": "r2://models/bp-monitor/yolo26n-v0.1.0.npz",
        "sha256": "required",
        "size_bytes": 12345678
      },
      {
        "platform": "ios_coreml",
        "format": "coreml_mlpackage",
        "uri": "r2://models/bp-monitor/yolo26n-v0.1.0.mlpackage",
        "sha256": "required",
        "size_bytes": 12345678,
        "optional": true
      }
    ]
  }
}
```

### 5.5 Add `decision_trace`

Every validation run should include an append-only trace:

```json
[
  {
    "time": "2026-05-22T12:00:00Z",
    "stage": "frame_sampler",
    "status": "completed",
    "details": { "sampled_frames": 84 }
  },
  {
    "stage": "detector",
    "runtime": "mac_mlx",
    "model_artifact_sha256": "...",
    "status": "completed"
  },
  {
    "stage": "rule_engine",
    "final_decision_authority": true,
    "status": "needs_review"
  }
]
```

This is not optional. It is the evidence behind the product promise.

### 5.6 Add `privacy_log_entries`

Do not bury privacy claims in a generic summary JSON. Store them explicitly.

Suggested fields:

```text
id
run_id
event_type
occurred_at
local_runtime_id
data_category
left_device boolean
destination
redaction_applied boolean
minimization_applied boolean
user_confirmed boolean
payload_hash
details_json
```

Example rows:

- raw_video, left_device=false
- yolo_model, left_device=false
- sop_rules, left_device=false
- redacted_crop, left_device=true, destination=cloud_vlm, user_confirmed=true

### 5.7 Rule results should be first-class

For auditability, add:

```text
run_rule_results
  id
  run_id
  step_key
  rule_id
  condition_type
  status
  confidence
  start_sec
  end_sec
  input_detection_ids
  rule_snapshot_json
  result_json
```

Then `run_step_results` can summarize one or more `run_rule_results`.

### 5.8 Avoid arrays for portable schema

For anything shared between Postgres and SQLite, prefer JSON arrays over SQL arrays:

- `supported_modes`
- `required_action_ids`
- `optional_action_ids`
- `evidence_detection_ids`
- `evidence_item_ids`

SQL arrays are fine for Neon-only tables, but painful in local SQLite and TypeScript clients.

---

## 6. Rule Engine Recommendations

### 6.1 Keep the v0.1 rule grammar small

For the BP monitor demo, implement only:

- `presence_duration`
- `inside`
- `overlap`
- `orientation_above`
- `temporal_order`
- `confidence_gate`

Do not implement every type listed in PRD1.3 yet. Every rule type creates evaluator code, UI controls, tests, evidence rendering, and ambiguity behavior.

### 6.2 Rules should operate on normalized scene facts

Detection boxes are noisy. The runtime should convert detections to facts:

```json
{
  "fact": "cuff_visible",
  "start_sec": 3.2,
  "end_sec": 19.4,
  "confidence": 0.88,
  "sources": ["yolo26_mlx"],
  "evidence": ["frame_0012", "frame_0015"]
}
```

Then rules evaluate facts and geometry snapshots.

### 6.3 Define coordinate conventions

The schema must explicitly state:

- normalized coordinates are `[0, 1]`
- origin is top-left
- x increases right
- y increases downward
- "above" means smaller y-center than target by threshold
- bbox format is `xyxy_normalized`
- frame orientation must be normalized before inference

This prevents many subtle bugs on iPhone videos, especially portrait videos with rotation metadata.

### 6.4 Define confidence precedence

Recommended precedence:

1. YOLO detections below `min_detection_confidence` are ignored.
2. Frame-level conditions evaluate over surviving detections.
3. A condition is true only if geometry is true and involved detections meet condition confidence thresholds.
4. An action fires only if a condition holds for `min_duration_sec`.
5. A step passes only if required actions fire and ordering constraints hold.
6. If evidence is insufficient, status is `uncertain`, not `failed`.
7. Guarded Hybrid can ask for advisory help only from `uncertain`, never to override a deterministic `failed` unless the rule declares that fallback is allowed.

### 6.5 Make ambiguity explicit

Ambiguity is not just low confidence. It can come from:

- missing key tag
- conflicting detections
- insufficient frames
- occlusion
- temporal order conflict
- local VLM disagreement
- redaction would remove needed context

Add an `ambiguity_reason` enum in rule results and step results.

---

## 7. YOLO26 MLX Integration Plan

### 7.1 Use MLX as a local Mac service

Do not import YOLO26 MLX into the PWA. Wrap it behind the Mac runtime API.

Detector wrapper responsibilities:

- load `.soup`
- select `mac_mlx` artifact
- verify hash
- load model with `YOLO(path)`
- normalize image orientation
- run `predict` or `track`
- map YOLO class ids to SOUP tags
- normalize boxes
- persist detections
- expose progress events

### 7.2 Artifact policy

Use:

- `.pt` only as source/training artifact
- `.npz` as preferred Mac MLX runtime artifact
- `.safetensors` as accepted MLX checkpoint/runtime artifact if supported in the runtime wrapper
- `.mlpackage` for future native iOS
- `.onnx` only for experimental non-MLX runtimes

Do not publish a `.soup` package whose only runtime model is `.pt`.

### 7.3 Model size policy

For v0.1:

- start with `yolo26n`
- use `imgsz=640`
- avoid segmentation unless bounding boxes fail the workflow
- avoid tracking unless temporal identity is needed

For BP monitor, plain detection plus simple temporal smoothing is likely enough.

### 7.4 Training path

Do not build full training orchestration in v0.1.

Recommended:

1. collect sample videos manually
2. extract frames with a script
3. label in a proven external tool or simple desktop UI
4. export YOLO dataset
5. train via `yolo-mlx` CLI/API
6. convert/publish `.npz`
7. hand-author `.soup`
8. run test videos

Only after the runtime works should you build in-app training jobs.

### 7.5 License risk

The local package metadata says `AGPL-3.0-only`. This matters.

TODO:

- Confirm whether SoPilot will be open source under AGPL-compatible terms.
- If not, talk to the upstream maintainer about commercial licensing.
- If exposing YOLO26 MLX through a local network service, review AGPL network-use obligations with counsel.

This is not a reason to avoid YOLO26 MLX for a hackathon, but it is a P0 business/legal issue before distribution.

---

## 8. PWA-Specific Product Risks

### 8.1 Pairing and trust

An iPhone PWA talking to a Mac runtime needs a pairing story.

Recommended hackathon pairing:

1. Mac runtime starts and shows a QR code.
2. iPhone scans QR code.
3. QR includes local HTTPS URL and one-time pairing token.
4. PWA stores a session token.
5. Mac runtime restricts API access to paired sessions.

Do not leave a local runtime open on the network without auth.

### 8.2 HTTPS and local network friction

Camera, service workers, and secure APIs all push you toward HTTPS. A local Mac service with HTTPS can be annoying due to certificates.

For the demo, decide early:

- use a tunnel only for demo convenience, knowing it weakens local-first, or
- install/trust a local certificate, or
- serve the PWA from the Mac runtime itself over a local HTTPS origin.

The cleanest v0.1 path is:

> Mac runtime serves the PWA and API from the same local origin.

Then the iPhone visits the Mac runtime URL.

### 8.3 Video upload reliability

iPhone videos can be large. Avoid a single giant upload if possible.

Recommended:

- set max demo video length
- compress/transcode client-side only if practical
- support chunked upload
- show upload progress
- resume or restart failed uploads cleanly
- cap storage usage on the Mac runtime

### 8.4 Offline behavior

Define offline precisely:

- PWA offline without Mac runtime: can view cached package metadata and past synced results only.
- PWA with Mac runtime but no internet: can run installed packages in All Local mode.
- PWA with internet but no Mac runtime: can browse store, but cannot run YOLO26 MLX.

This distinction should be visible in Settings.

---

## 9. Privacy and Security Review

### 9.1 Privacy claims need exact scope

Use these scoped claims:

- Consumer validation raw video stays on the paired local runtime unless the user explicitly exports it.
- SOP rules are evaluated by the local runtime.
- YOLO model runs on the local runtime after install.
- Final compliance decision is made by the local rule engine.
- Cloud VLM is optional and advisory.
- Cloud VLM receives only the specific minimized/redacted payload shown to the user.

Avoid these broad claims:

- "Everything stays local" because package browsing, model download, creator training, and optional sync are cloud-based.
- "YOLO model stays local" before first install.
- "Face/background redacted" before the redaction pipeline exists.

### 9.2 Redaction/minimization must be auditable

For v0.1, do the simplest honest version:

- crop around relevant detections
- include only tag names, confidence, and one question
- do not send full SOP
- do not send raw video
- do not send full frame unless explicitly allowed

Face blur and background masking can be P1/P2.

Record:

- exact image/crop sent
- payload hash
- prompt/question sent
- user approval timestamp
- cloud response
- local final rule result after advisory summary

### 9.3 Package supply chain

`.soup` packages can cause harm if they reference malicious or swapped model artifacts.

Add:

- package signature
- artifact sha256
- creator identity
- version immutability
- revocation list
- runtime capability checks
- blocked arbitrary script execution

A `.soup` should be declarative. It should not contain arbitrary executable code.

### 9.4 API keys

Screen 27 says users can paste Gemini and Cloudflare keys. In a PWA, this is risky.

Recommendation:

- Cloud VLM calls should go through a SoPilot backend proxy with user consent and rate limits.
- Cloudflare creator asset management should happen in creator web app backend, not directly from consumer PWA.
- If BYO keys are required for hackathon, store them only in browser storage as a temporary demo feature and label that as non-production.
- For native iOS/macOS later, use Keychain.

---

## 10. UX/Product Recommendations

### 10.1 Add a "Runtime Pairing" first-run screen

The current design starts with role selection. For iPhone PWA + Mac runtime, a user cannot run checks until paired.

Suggested first-run flow:

1. Welcome to SoPilot
2. Choose "Use a SOUP Package"
3. Pair Local Runtime
4. Scan QR from Mac
5. Runtime health check
6. Continue to Home

Runtime health should show:

- YOLO26 MLX available
- MLX model cache path
- local storage available
- local VLM available/not installed
- cloud fallback enabled/disabled

### 10.2 Keep the runtime screen operational

Avoid over-explaining privacy on every screen. During a run, users need:

- current stage
- elapsed time
- progress
- detected objects
- failed/uncertain steps
- whether a decision is waiting for consent

Privacy claims should be summarized in a compact "Decision Path" and detailed in Report.

### 10.3 Creator flow should be Mac-first

Creator tasks need screen space and precise input:

- labeling
- rule authoring
- debugging detections
- inspecting frames
- reviewing model failures

An iPhone PWA can review packages and maybe capture training videos, but the serious creator workflow should be Mac/tablet first.

### 10.4 Reduce v0.1 screens

The current 27-screen design is aspirational.

Build 12 polished screens first:

1. Pair Runtime
2. Home
3. Store
4. Package Detail
5. Install Mode
6. Start Check
7. Upload/Record
8. Analysis Progress
9. Ambiguity Gate
10. Redaction Preview
11. Result
12. Evidence Review

Settings can be a simple panel for v0.1.

---

## 11. Recommended MVP Scope

### 11.1 MVP package

Use one package:

```text
Blood Pressure Monitor SOP Checker
```

Tags:

```text
monitor
cuff
upper_arm
elbow_bend
grey_connector
start_button
```

Steps:

```text
1. Monitor visible
2. Connector attached
3. Cuff on upper arm
4. Cuff above elbow bend
5. Start pressed after setup
```

Rules:

```text
presence_duration(monitor)
presence_duration(grey_connector)
inside_or_overlap(cuff, upper_arm)
orientation_above(cuff, elbow_bend)
temporal_order(cuff_on_upper_arm and connector_attached before start_button_pressed)
```

### 11.2 MVP demo flow

1. Start Mac Runtime Companion.
2. iPhone opens PWA served by Mac runtime.
3. Pair runtime.
4. Browse/install BP Monitor `.soup`.
5. Select All Local mode.
6. Record/upload short video from iPhone.
7. Mac runtime samples frames and runs YOLO26 MLX.
8. PWA shows progress via WebSocket/SSE.
9. Rule engine returns one uncertain or failed step.
10. User opens evidence review.
11. In Guarded Hybrid demo, user approves one redacted crop.
12. Cloud advisory summary returns.
13. Local rule engine produces final result.
14. Result screen shows decision trace and privacy log.

### 11.3 What to defer

Defer:

- full SOUP marketplace
- reviews/ratings
- in-app model training jobs
- on-phone bounding-box labeling
- segmentation
- local open VLM if setup is unstable
- native iOS CoreML
- PDF exports
- advanced chat memory
- multi-workflow support

---

## 12. TODO List

### P0 — Architecture blockers

- [ ] Write `doc/architecture-runtime.md` defining iPhone PWA, Mac Runtime Companion, and cloud control plane.
- [ ] State explicitly that YOLO26 MLX runs on Mac, not inside iPhone PWA.
- [ ] Add a runtime capability matrix: PWA, Mac MLX, native iOS CoreML future, cloud fallback.
- [ ] Decide whether the Mac runtime serves the PWA itself. I recommend yes for v0.1.
- [ ] Define local pairing: QR code, token, local HTTPS/WSS, paired-session auth.
- [ ] Define the exact meaning of All Local in PWA + Mac context.
- [ ] Split privacy claims into consumer runtime claims vs creator cloud workflow claims.
- [ ] Review AGPL obligations for YOLO26 MLX before public distribution.

### P0 — SOUP package contract

- [ ] Create `doc/soup-schema-0.1.json`.
- [ ] Add JSON Schema validation for every `.soup` package.
- [ ] Add `models.detector.artifacts[]` with platform, format, URI, sha256, and size.
- [ ] Add `capabilities.required_runtime` to `.soup`.
- [ ] Add rule grammar version to `.soup`.
- [ ] Add package signature field.
- [ ] Add redaction/minimization policy field.
- [ ] Add test cases to the BP Monitor package.
- [ ] Create `packages/bp-monitor-basic.soup.json`.

### P0 — Schema cleanup

- [ ] Pick PRD1.3 table names and update PRD1.2 to match.
- [ ] Fill or delete empty `doc/PRD1.1-basic.md`.
- [ ] Add `models_manifest` to `soup_versions`.
- [ ] Add `decision_trace` to `validation_runs`.
- [ ] Add `privacy_log_entries`.
- [ ] Re-add `run_rule_results`, or explicitly document denormalized rule results.
- [ ] Change model formats from generic `mlx` to `mlx_npz` / `mlx_safetensors`.
- [ ] Stop treating `.pt` as the default consumer runtime model format.
- [ ] Write `doc/local-runtime-schema.md` for SQLite.
- [ ] Reduce v0.1 cloud schema to package/store/creator essentials.

### P1 — Mac Runtime Companion

- [ ] Build local runtime service skeleton.
- [ ] Add `/health` endpoint.
- [ ] Add QR pairing/token flow.
- [ ] Add local SQLite migrations.
- [ ] Add package install with sha256 verification.
- [ ] Add YOLO26 MLX detector wrapper.
- [ ] Add frame sampler.
- [ ] Normalize iPhone video orientation before detection.
- [ ] Persist `run_detections`.
- [ ] Implement minimal rule engine.
- [ ] Emit `run_rule_results`, `run_step_results`, and `decision_trace`.
- [ ] Add local evidence frame storage.
- [ ] Add WebSocket/SSE progress stream.

### P1 — iPhone PWA

- [ ] Build Pair Runtime screen.
- [ ] Build Home with runtime health badge.
- [ ] Build Package Detail.
- [ ] Build Install Mode selection.
- [ ] Build Record/Upload flow.
- [ ] Add upload progress and failure recovery.
- [ ] Build Analysis Progress.
- [ ] Build Result Summary with decision path.
- [ ] Build Evidence Review.
- [ ] Build Ambiguity Gate.
- [ ] Build Redaction Preview using real local crop from runtime.

### P1 — BP Monitor demo

- [ ] Freeze BP Monitor tags.
- [ ] Collect short correct/wrong/ambiguous videos.
- [ ] Extract representative frames.
- [ ] Label frames.
- [ ] Train or fine-tune `yolo26n`.
- [ ] Export preferred Mac MLX artifact as `.npz`.
- [ ] Create BP Monitor `.soup`.
- [ ] Create three test videos: pass, fail start too early, uncertain cuff position.
- [ ] Validate all three through runtime.
- [ ] Tune thresholds to prefer `uncertain` over false confidence.

### P1 — Guarded Hybrid

- [ ] Implement ambiguity reason codes.
- [ ] Implement ROI crop around relevant detections.
- [ ] Show exact outgoing crop and text payload.
- [ ] Require explicit user approval.
- [ ] Store payload hash and approval timestamp.
- [ ] Stub cloud VLM response first.
- [ ] Feed advisory response back to local rule engine.
- [ ] Show final local evaluation after advisory summary.

### P2 — Post-MVP

- [ ] Add real cloud VLM proxy.
- [ ] Add face detection/background masking redaction.
- [ ] Add local open VLM on Mac if it materially improves ambiguity handling.
- [ ] Add native iOS/CoreML runtime if strict phone-local execution becomes a requirement.
- [ ] Add normalized rule authoring tables after Rule Studio is real.
- [ ] Add training job orchestration.
- [ ] Add package reviews and marketplace trust features.
- [ ] Add PDF reports.
- [ ] Add package update/revocation flow.
- [ ] Add second workflow to test rule grammar generality.

---

## 13. Final Recommendation

The project should keep the SoPilot product thesis but sharpen the runtime architecture immediately.

Do not try to make an iPhone PWA run YOLO26 MLX. It will waste time and create misleading product claims. Instead, make the iPhone PWA the mobile capture and review surface, and make the Mac Runtime Companion the local AI/rule engine. This uses YOLO26 MLX honestly, preserves the local-first claim in a defensible way, and gives the team a demo path that can actually work.

The next document I would write is `doc/architecture-runtime.md`. The next code I would write is the Mac runtime `/health` endpoint plus a tiny YOLO26 MLX detector wrapper that can process one uploaded frame and return normalized detections. Everything else should build around that proof.

