# SoPilot macOS App PRD 2.0

## 1. Product Summary

**Product name:** SoPilot macOS
**Artifact:** SOUP Package — Standard Operating Understanding Package
**Primary platform:** macOS desktop app distributed as a `.dmg`
**Hackathon target:** 2-day build, 1-minute demo video, code submission
**Initial demo domain:** Blood Pressure Monitor SOP monitoring
**Core technical requirement:** Must use YOLO MLX for local object detection

SoPilot macOS is a local-first SOP monitoring app that validates whether a real-world workflow follows a structured procedure. The app runs on a Mac, uses a configurable USB or built-in/web camera, runs YOLO MLX locally with a user-installed `.npz` model, converts detections into scene events, and evaluates those events with a deterministic SOUP rule engine.

The app includes optional local VLM support for user questions and ambiguity explanation. Users can download and manage small local VLMs such as SmolVLM and Moondream 2. VLM output is advisory only; the SOUP rule engine always makes the final SOP decision.

For the hackathon version, creator-side features such as dataset labeling, YOLO training, and package publishing are shown as animated static mockup pages. The real implemented path is SOP monitoring: camera or sample video input, YOLO MLX detection, SOUP rule evaluation, evidence display, and local result generation.

## 2. Positioning

SoPilot is not a cloud VLM wrapper. SoPilot is a local SOP decision engine.

The core pitch:

> SoPilot turns a physical SOP into an installable local AI package. YOLO MLX detects workflow objects, the SOUP rule engine checks procedural correctness, and optional local VLMs help explain ambiguity. Final decisions stay local.

## 3. Hackathon Scope

### 3.1 In Scope

The hackathon app must support:

1. macOS app distributed as `.dmg`.
2. Double-click launch with no Terminal commands for end users.
3. Configurable camera source: built-in camera, USB camera, or compatible web camera.
4. Local YOLO MLX inference using installed `.npz` model files.
5. Local SOUP rule engine for real SOP monitoring.
6. Live or playback overlay showing detected objects.
7. Step-by-step SOP result with pass, fail, or uncertain state.
8. Evidence view with frame, timestamp, bounding boxes, and rule explanation.
9. Local VLM model manager with two downloadable options: SmolVLM and Moondream 2.
10. VLM question box for advisory local Q&A, if model is installed.
11. Static animated mockup pages for data labeling, YOLO model training, and creator workflow.
12. Unit tests and E2E tests for rule engine, model manager, camera selection, inference contract, and SOP result flow.

### 3.2 Out of Scope

The hackathon app will not support:

1. iPhone app runtime.
2. Real in-app YOLO training.
3. Real in-app manual labeling editor.
4. Full marketplace.
5. Payment system.
6. User accounts.
7. Cloud VLM as final decision maker.
8. Medical diagnosis or health interpretation.
9. Production-grade multi-camera synchronization.
10. Regulatory compliance certification.

## 4. Target Users

### 4.1 Hackathon Judges

Judges need to quickly understand the product without local setup complexity.

Needs:

* Open a `.dmg`.
* Drag app to Applications or run directly.
* Launch by double-click.
* See a working local AI demo.
* Understand that YOLO MLX and rule evaluation are real.
* Understand that creator/training screens are mocked for scope control.

### 4.2 SOP Consumer User

A user wants to check whether a workflow was performed correctly.

Needs:

* Select camera.
* Run or upload a SOP workflow video.
* See object detection overlays.
* Receive step-level result.
* Understand why a step passed, failed, or is uncertain.
* Ask optional local VLM questions.
* Keep raw video, YOLO model, rules, and result local.

### 4.3 SOP Creator User — Demo Mock Only

A creator wants to package a new SOP.

Needs shown in animated mockup:

* Capture or upload training videos.
* Extract frames.
* Label objects.
* Train YOLO model.
* Test model quality.
* Author SOUP rules.
* Export package.

For PRD 2.0, this flow is a visual mock, not a real implemented feature.

## 5. Product Principles

### 5.1 Local-First Runtime

The app must clearly communicate:

* Camera input stays local.
* Raw video stays local.
* YOLO `.npz` model stays local.
* SOUP rules stay local.
* Rule engine makes the final decision locally.
* Optional VLMs run locally if installed.
* No cloud VLM is required for the main demo path.

### 5.2 Real Monitoring, Mocked Creation

The monitoring path must be real.

Real:

* Camera selection.
* Video frame capture or sample video playback.
* YOLO MLX detection.
* Bounding box overlay.
* Detection-to-event conversion.
* SOUP rule engine.
* Evidence and result generation.

Mocked:

* Training data capture flow.
* Data labeling UI.
* YOLO training progress.
* Model testing metrics.
* Creator publishing flow.

### 5.3 VLM Advisory Only

Local VLMs can answer user questions and explain ambiguous visual evidence. They do not make final pass/fail decisions.

Allowed VLM roles:

* Explain an evidence frame.
* Answer a user question about the current frame.
* Help describe why a rule may be uncertain.
* Summarize visible scene context.

Blocked VLM roles:

* Final SOP pass/fail decision.
* Override SOUP rule result.
* Modify rule thresholds automatically.
* Provide medical advice.

### 5.4 Explainability by Default

Every result should show:

* Step status.
* Rule that fired.
* Evidence frame or timestamp.
* Relevant detected objects.
* Detection confidence.
* Whether VLM was used.
* Whether final decision came from local rule engine.

## 6. App Distribution and Installation

### 6.1 Distribution Format

The app should be distributed as:

```text
SoPilot.dmg
  SoPilot.app
  Applications shortcut
```

### 6.2 Install Experience

Target user flow:

1. User downloads `SoPilot.dmg`.
2. User opens DMG.
3. User drags `SoPilot.app` to Applications.
4. User double-clicks `SoPilot.app`.
5. App launches without requiring Terminal.
6. App shows local runtime status.
7. App guides the user to run the BP Monitor demo.

### 6.3 First Launch Checks

On first launch, app checks:

* macOS compatibility.
* Camera permission.
* Local model directory availability.
* Installed YOLO `.npz` models.
* Installed VLM models.
* SOUP package availability.
* Runtime backend health.

### 6.4 Packaging Recommendation

Recommended stack:

```text
macOS app shell:
  Tauri or Electron

Frontend:
  React + TypeScript

Backend sidecar:
  Python
  YOLO MLX
  SOUP rule engine
  VLM model manager

Distribution:
  .app + .dmg
```

SwiftUI is acceptable for a native-only prototype, but the recommended implementation is a desktop web shell with a bundled local Python backend because YOLO MLX and model-management code are easier to implement in Python.

## 7. Runtime Architecture

### 7.1 High-Level Architecture

```text
SoPilot macOS App
  ├── UI Shell
  │   ├── Camera selector
  │   ├── Live overlay screen
  │   ├── SOP checklist
  │   ├── VLM model manager
  │   ├── VLM question panel
  │   ├── Result summary
  │   ├── Evidence review
  │   └── Creator mock pages
  │
  ├── Local Backend Sidecar
  │   ├── Camera/video input adapter
  │   ├── Frame sampler
  │   ├── YOLO MLX runner
  │   ├── Detection normalizer
  │   ├── Scene event builder
  │   ├── SOUP rule engine
  │   ├── Evidence generator
  │   ├── VLM model manager
  │   └── Optional VLM inference adapter
  │
  └── Local Storage
      ├── YOLO models
      ├── VLM models
      ├── SOUP packages
      ├── run results
      ├── evidence frames
      └── app config
```

### 7.2 Local Storage Layout

```text
~/Library/Application Support/SoPilot/
  config.json
  models/
    yolo/
      bp_monitor_yolo26.npz
    vlm/
      smolvlm/
      moondream2/
  soup/
    bp_monitor.soup.json
  runs/
    run_001/
      result.json
      detections.json
      evidence/
        frame_023.jpg
        frame_023_overlay.jpg
  logs/
    app.log
```

No downloaded models should be stored inside `SoPilot.app`.

## 8. Camera Input

### 8.1 Requirements

The app must support:

* Built-in Mac camera.
* USB camera.
* Compatible web camera.
* Camera selection from settings or run screen.
* Camera permission request.
* Camera unavailable state.
* Sample video fallback.

### 8.2 Camera Selection UI

Screen: `Runtime Settings` or `Start SOP Check`

Fields:

* Camera source dropdown.
* Resolution dropdown, optional.
* FPS selector, optional.
* Preview window.
* Test Camera button.
* Use Sample Video button.

Example:

```text
Camera Source
[ FaceTime HD Camera ▾ ]

Other sources:
- USB Camera
- OBS Virtual Camera
- Sample BP Monitor Video
```

### 8.3 Camera Error States

The app should handle:

* Camera permission denied.
* No camera found.
* Selected camera disconnected.
* Camera busy in another app.
* Backend cannot open camera.
* FPS too low.

User-facing copy:

```text
Camera access is required to monitor the SOP workflow.
You can enable camera access in macOS Settings > Privacy & Security > Camera.
```

## 9. YOLO MLX Model Management

### 9.1 Requirement

The app must allow users to install a YOLO `.npz` model from local drive.

The initial demo model is expected to detect Blood Pressure Monitor SOP objects.

### 9.2 Required Tags for Demo

The demo SOUP package expects the following object tags:

```text
blood_pressure_monitor
cuff
upper_arm
elbow_bend
grey_connector
button
screen
```

### 9.3 Install YOLO Model Flow

User flow:

1. Open Settings > Local Models.
2. Click Install YOLO Model.
3. Select `.npz` file from local drive.
4. App validates file extension.
5. App copies file to local model directory.
6. App stores model metadata.
7. App shows model as installed.
8. User can activate model for the BP Monitor SOUP package.

### 9.4 YOLO Model Metadata

```json
{
  "id": "bp_monitor_yolo26",
  "name": "BP Monitor YOLO26",
  "format": "npz",
  "runtime": "mlx",
  "local_path": "~/Library/Application Support/SoPilot/models/yolo/bp_monitor_yolo26.npz",
  "installed_at": "2026-05-22T10:00:00Z",
  "tags": [
    "blood_pressure_monitor",
    "cuff",
    "upper_arm",
    "elbow_bend",
    "grey_connector",
    "button",
    "screen"
  ]
}
```

### 9.5 YOLO Model Validation

Minimum validation:

* File exists.
* File extension is `.npz`.
* File size is greater than minimum threshold.
* App can load model with YOLO MLX runner.
* Optional smoke inference succeeds on sample image.

If validation fails, the app should show:

```text
This YOLO model could not be loaded by the local MLX runtime.
Please select a valid `.npz` model file.
```

## 10. VLM Model Manager

### 10.1 Requirement

The app must support downloading, activating, and deleting local VLM models.

Supported models for PRD 2.0:

1. SmolVLM.
2. Moondream 2.

### 10.2 VLM UX

Screen: `Settings > Local VLM` or `Runtime Panel`

Fields:

```text
Local VLM
Models are stored locally on this Mac.
No cloud VLM is used by this setting.
Downloaded models can be removed anytime.

Model:
[ SmolVLM ▾ ]

Status:
Not installed / Downloading / Installed / Active / Failed

Buttons:
[Download] [Use] [Delete]
```

### 10.3 Model Registry

```json
{
  "models": [
    {
      "id": "smolvlm",
      "display_name": "SmolVLM",
      "provider": "huggingface",
      "description": "Small local VLM for image and video question answering.",
      "recommended": true
    },
    {
      "id": "moondream2",
      "display_name": "Moondream 2",
      "provider": "huggingface",
      "description": "Compact local VLM for image question answering.",
      "recommended": false
    }
  ]
}
```

The exact model repository IDs should be stored in a registry file and may be updated after implementation testing.

### 10.4 VLM States

```text
not_installed
downloading
installed
active
download_failed
delete_failed
```

### 10.5 Download Flow

1. User selects VLM from dropdown.
2. User clicks Download.
3. App checks disk space.
4. App creates local model folder.
5. App downloads model files from Hugging Face or configured source.
6. App shows progress or indeterminate loading.
7. App verifies model files exist.
8. App marks model as installed.
9. User can activate model.

### 10.6 Delete Flow

1. User selects installed model.
2. User clicks Delete.
3. App asks for confirmation.
4. If model is active, app warns that Local VLM will be turned off.
5. App deletes only the model folder inside SoPilot model directory.
6. App clears active model if needed.
7. App updates UI.

### 10.7 VLM Question Panel

The result and evidence screens should include an optional local VLM question box.

Example UI:

```text
Ask Local VLM
Model: SmolVLM · Active
[ Why is this step uncertain?                 ]
[Ask]
```

VLM answer should include a visible advisory label:

```text
Local VLM advisory answer. Final SOP decision is still made by the SOUP rule engine.
```

### 10.8 VLM Failure Behavior

If VLM is not installed:

```text
Local VLM is not installed. You can still run SOP monitoring with YOLO MLX and the SOUP rule engine.
```

If VLM fails:

```text
Local VLM failed to respond. The SOP result is unchanged because final evaluation is handled by the local rule engine.
```

## 11. SOUP Rule Engine

### 11.1 Requirement

The SOUP rule engine is the real core implementation for PRD 2.0.

It must:

* Load package rules from local SOUP JSON.
* Consume normalized detections and scene events.
* Evaluate rules deterministically.
* Produce step-level results.
* Produce final result.
* Produce evidence trace.
* Remain independent from YOLO MLX implementation.

### 11.2 Minimal Rule Types

The hackathon rule engine should support five rule types:

```text
exists_before
near_before
overlap
above
after_all_required
```

### 11.3 Example BP Monitor Rules

```json
[
  {
    "id": "monitor_visible_before_start",
    "type": "exists_before",
    "tag": "blood_pressure_monitor",
    "before_event": "start_button_pressed",
    "min_confidence": 0.5
  },
  {
    "id": "connector_attached_before_start",
    "type": "near_before",
    "source_tag": "grey_connector",
    "target_tag": "blood_pressure_monitor",
    "before_event": "start_button_pressed",
    "max_distance_px": 120,
    "min_confidence": 0.5
  },
  {
    "id": "cuff_on_upper_arm",
    "type": "overlap",
    "source_tag": "cuff",
    "target_tag": "upper_arm",
    "min_overlap_ratio": 0.25,
    "min_confidence": 0.5
  },
  {
    "id": "cuff_above_elbow",
    "type": "above",
    "source_tag": "cuff",
    "target_tag": "elbow_bend",
    "margin_px": 20,
    "ambiguity_margin_px": 30,
    "min_confidence": 0.5
  },
  {
    "id": "start_after_setup",
    "type": "after_all_required",
    "event": "start_button_pressed",
    "required_steps": [
      "monitor_visible_before_start",
      "connector_attached_before_start",
      "cuff_on_upper_arm",
      "cuff_above_elbow"
    ]
  }
]
```

### 11.4 Rule Status

Each rule returns:

```text
passed
failed
uncertain
skipped
```

Status logic:

```text
passed:
  predicate is true and confidence is above threshold

failed:
  predicate is false and confidence is above threshold

uncertain:
  required object is missing
  confidence is below threshold
  geometry is near threshold
  previous required step is uncertain

skipped:
  dependent event or prerequisite is unavailable
```

### 11.5 Overall Result

```text
failed:
  any required step failed

needs_review:
  no required step failed, but at least one required step is uncertain

passed:
  all required steps passed
```

### 11.6 Rule Engine Input

```json
{
  "detections": [
    {
      "frame_id": "frame_023",
      "timestamp": 7.6,
      "tag": "cuff",
      "bbox": [120, 180, 280, 260],
      "confidence": 0.88,
      "source": "yolo_mlx"
    }
  ],
  "events": [
    {
      "type": "start_button_pressed",
      "timestamp": 19.2,
      "source": "demo_marker"
    }
  ]
}
```

### 11.7 Rule Engine Output

```json
{
  "run_id": "run_001",
  "package_id": "bp_monitor_sop_checker",
  "status": "needs_review",
  "final_decision_source": "local_rule_engine",
  "steps": [
    {
      "step_id": "cuff_above_elbow",
      "status": "uncertain",
      "confidence": 0.42,
      "reason": "Elbow bend confidence is below threshold.",
      "evidence": {
        "frame_id": "frame_023",
        "timestamp": 7.6,
        "objects": ["cuff", "elbow_bend"],
        "source": "yolo_mlx"
      }
    }
  ],
  "privacy_log": {
    "raw_video_stayed_local": true,
    "sop_rules_stayed_local": true,
    "yolo_model_stayed_local": true,
    "vlm_used": false,
    "final_decision_local": true
  }
}
```

## 12. SOP Monitoring Flow

### 12.1 Main User Flow

1. User launches SoPilot.
2. App shows local runtime status.
3. User selects BP Monitor SOP Checker.
4. User selects camera or sample video.
5. User confirms YOLO `.npz` model is installed.
6. User starts monitoring.
7. App samples frames.
8. App runs YOLO MLX locally.
9. App draws bounding boxes on live or playback view.
10. App converts detections into scene events.
11. SOUP rule engine evaluates SOP rules.
12. App shows step-level result.
13. User opens evidence review.
14. User optionally asks local VLM a question.
15. App shows final local decision trace.

### 12.2 Live Overlay Screen

Required elements:

* Camera/video preview.
* Bounding boxes.
* Object labels.
* Confidence score.
* SOP checklist.
* Runtime status.
* Stop / Finish Analysis button.

Example checklist:

```text
✓ Monitor visible
✓ Grey connector attached
✓ Cuff on upper arm
? Cuff above elbow
✕ Start pressed after setup
```

### 12.3 Analysis Progress Screen

Stages:

```text
Frame sampler
YOLO MLX detector
Scene event builder
SOUP rule engine
Evidence generator
Local decision
```

### 12.4 Result Summary Screen

Required fields:

* Package name.
* Run ID.
* Overall status.
* Step results.
* Final decision source.
* VLM usage status.
* Privacy log.
* Review Evidence CTA.
* Ask Local VLM CTA.

### 12.5 Evidence Review Screen

Required fields:

* Selected step.
* Status.
* Evidence frame.
* Bounding boxes.
* Timestamp.
* Rule explanation.
* Detection confidence.
* VLM advisory answer, if used.
* Final decision note.

## 13. Creator Mock Pages

Creator pages are static, animated mockups. They should look polished but should not implement real training.

### 13.1 Mock Flow

1. Creator Dashboard.
2. New SOUP Package.
3. Capture Training Data.
4. Extract Frames.
5. Label Objects.
6. Train YOLO Model.
7. Test Model.
8. Rule Studio.
9. Package and Export.

### 13.2 Animation Requirements

Mock pages should include lightweight animations:

* Progress bars.
* Frame extraction shimmer.
* Bounding box drawing animation.
* Training loss/mAP chart animation.
* Rule generation typing animation.
* Package export success animation.

### 13.3 Mock Disclosure

Because these pages are not real in PRD 2.0, include subtle demo labeling where appropriate:

```text
Creator workflow prototype — training is simulated in this hackathon build.
```

Do not hide the fact that training is mocked in the code submission.

## 14. API Requirements

### 14.1 Backend Health

```text
GET /api/health
```

Response:

```json
{
  "status": "ok",
  "runtime": "local_mac",
  "yolo_mlx_available": true,
  "active_yolo_model": "bp_monitor_yolo26",
  "active_vlm_model": "smolvlm"
}
```

### 14.2 Camera APIs

```text
GET /api/cameras
POST /api/cameras/select
GET /api/cameras/preview
```

### 14.3 YOLO Model APIs

```text
GET /api/yolo/models
POST /api/yolo/models/install
POST /api/yolo/models/{model_id}/activate
DELETE /api/yolo/models/{model_id}
POST /api/yolo/models/{model_id}/validate
```

### 14.4 VLM Model APIs

```text
GET /api/vlm/models
POST /api/vlm/models/{model_id}/download
GET /api/vlm/models/{model_id}/download-status
POST /api/vlm/models/{model_id}/activate
DELETE /api/vlm/models/{model_id}
POST /api/vlm/ask
```

### 14.5 SOP Run APIs

```text
POST /api/runs/start
GET /api/runs/{run_id}/status
GET /api/runs/{run_id}/result
GET /api/runs/{run_id}/evidence/{frame_id}
POST /api/runs/{run_id}/ask-vlm
```

## 15. Non-Functional Requirements

### 15.1 Performance

Hackathon target:

* App launch: under 5 seconds after first install, excluding model downloads.
* Camera preview start: under 5 seconds after permission granted.
* Sample video analysis: under 60 seconds.
* Rule engine evaluation: under 1 second for saved detections.
* VLM answer: best effort, no hard guarantee.

### 15.2 Reliability

The app must still function if:

* VLM is not installed.
* VLM download fails.
* Camera permission is denied.
* USB camera disconnects.
* YOLO model is missing.
* YOLO model validation fails.

In all cases, the app should show a clear error and avoid crashing.

### 15.3 Privacy

* No raw video upload.
* No cloud VLM by default.
* No SOP rules uploaded.
* No YOLO model uploaded.
* VLM models are downloaded only after user action.
* User can delete downloaded VLM models.
* User can delete local run results.

### 15.4 Security

* Model deletion must only operate inside SoPilot model directory.
* Arbitrary delete paths are forbidden.
* Downloaded model metadata should be validated.
* App should avoid executing untrusted scripts from downloaded models.
* YOLO `.npz` model installation should copy files to controlled app storage.

## 16. Detailed Unit Test Plan

### 16.1 Rule Geometry Tests

| Test ID    | Test Name                | Input                                   | Expected                                  |
| ---------- | ------------------------ | --------------------------------------- | ----------------------------------------- |
| UT-GEO-001 | above_true_image_coords  | cuff center y above elbow center y      | passed                                    |
| UT-GEO-002 | above_false_image_coords | cuff center y below elbow center y      | failed                                    |
| UT-GEO-003 | above_uncertain_margin   | cuff near elbow within ambiguity margin | uncertain                                 |
| UT-GEO-004 | overlap_true             | cuff overlaps upper_arm above threshold | passed                                    |
| UT-GEO-005 | overlap_false            | cuff outside upper_arm                  | failed                                    |
| UT-GEO-006 | overlap_boundary         | overlap exactly at threshold            | passed or deterministic expected boundary |
| UT-GEO-007 | near_true                | connector close to monitor              | passed                                    |
| UT-GEO-008 | near_false               | connector far from monitor              | failed                                    |
| UT-GEO-009 | bbox_center              | bbox center calculation                 | correct x/y                               |
| UT-GEO-010 | distance_px              | two bbox centers                        | correct distance                          |

### 16.2 Detection Normalizer Tests

| Test ID    | Test Name             | Expected                                                     |
| ---------- | --------------------- | ------------------------------------------------------------ |
| UT-DET-001 | parse_yolo_mlx_output | MLX output converts to normalized detection JSON             |
| UT-DET-002 | reject_unknown_tag    | unknown tag handled or marked unsupported                    |
| UT-DET-003 | low_confidence_filter | detections below threshold filtered or marked low confidence |
| UT-DET-004 | frame_id_assigned     | every detection has frame ID                                 |
| UT-DET-005 | timestamp_assigned    | every detection has timestamp                                |
| UT-DET-006 | source_recorded       | detection source is `yolo_mlx`                               |
| UT-DET-007 | bbox_shape_validation | invalid bbox rejected                                        |
| UT-DET-008 | best_frame_selection  | highest-confidence evidence frame selected                   |

### 16.3 Scene Event Builder Tests

| Test ID    | Test Name                    | Expected                                                |
| ---------- | ---------------------------- | ------------------------------------------------------- |
| UT-EVT-001 | monitor_visible_event        | monitor detection creates monitor visible event         |
| UT-EVT-002 | connector_near_monitor_event | connector near monitor creates candidate attached event |
| UT-EVT-003 | cuff_upper_arm_event         | overlap creates cuff_on_upper_arm candidate             |
| UT-EVT-004 | cuff_above_elbow_event       | geometry creates cuff_above_elbow candidate             |
| UT-EVT-005 | missing_required_object      | missing object creates uncertain event                  |
| UT-EVT-006 | event_ordering               | events sorted by timestamp                              |
| UT-EVT-007 | duplicate_events_collapsed   | repeated detections collapse into best event            |

### 16.4 Rule Engine Tests

| Test ID     | Test Name                    | Expected                               |
| ----------- | ---------------------------- | -------------------------------------- |
| UT-RULE-001 | exists_before_pass           | monitor exists before start event      |
| UT-RULE-002 | exists_before_fail           | monitor appears only after start       |
| UT-RULE-003 | exists_before_uncertain      | monitor confidence below threshold     |
| UT-RULE-004 | near_before_pass             | connector near monitor before start    |
| UT-RULE-005 | near_before_fail             | connector far from monitor             |
| UT-RULE-006 | overlap_pass                 | cuff overlaps upper arm                |
| UT-RULE-007 | overlap_fail                 | cuff does not overlap upper arm        |
| UT-RULE-008 | above_pass                   | cuff above elbow                       |
| UT-RULE-009 | above_fail                   | cuff below elbow                       |
| UT-RULE-010 | above_uncertain              | cuff too close to elbow boundary       |
| UT-RULE-011 | after_all_required_pass      | start after all required steps passed  |
| UT-RULE-012 | after_all_required_fail      | start before required step             |
| UT-RULE-013 | after_all_required_uncertain | dependency uncertain                   |
| UT-RULE-014 | final_passed                 | all required steps passed              |
| UT-RULE-015 | final_failed                 | one required step failed               |
| UT-RULE-016 | final_needs_review           | no failures but at least one uncertain |

### 16.5 BP SOP Fixture Tests

| Test ID   | Fixture                   | Expected                               |
| --------- | ------------------------- | -------------------------------------- |
| UT-BP-001 | all_pass.json             | overall passed                         |
| UT-BP-002 | missing_connector.json    | connector step failed or uncertain     |
| UT-BP-003 | cuff_too_low.json         | cuff_above_elbow failed                |
| UT-BP-004 | elbow_hidden.json         | cuff_above_elbow uncertain             |
| UT-BP-005 | start_too_early.json      | start_after_setup failed               |
| UT-BP-006 | no_start_event.json       | start_after_setup skipped or uncertain |
| UT-BP-007 | low_confidence_cuff.json  | cuff steps uncertain                   |
| UT-BP-008 | multiple_good_frames.json | best evidence frame selected           |

### 16.6 YOLO Model Manager Tests

| Test ID     | Test Name                   | Expected                                |
| ----------- | --------------------------- | --------------------------------------- |
| UT-YOLO-001 | install_npz_success         | valid `.npz` copied to model directory  |
| UT-YOLO-002 | reject_non_npz              | non-`.npz` file rejected                |
| UT-YOLO-003 | activate_installed_model    | config updated                          |
| UT-YOLO-004 | activate_missing_model      | error returned                          |
| UT-YOLO-005 | delete_installed_model      | model removed safely                    |
| UT-YOLO-006 | delete_active_model         | active model cleared                    |
| UT-YOLO-007 | unsafe_delete_path_rejected | arbitrary paths cannot be deleted       |
| UT-YOLO-008 | validate_load_failure       | invalid `.npz` returns validation error |

### 16.7 VLM Model Manager Tests

| Test ID    | Test Name                  | Expected                              |
| ---------- | -------------------------- | ------------------------------------- |
| UT-VLM-001 | registry_has_two_models    | SmolVLM and Moondream 2 returned      |
| UT-VLM-002 | unknown_model_rejected     | invalid model ID rejected             |
| UT-VLM-003 | download_status_initial    | not installed before download         |
| UT-VLM-004 | download_success_mock      | status becomes installed              |
| UT-VLM-005 | download_failure_mock      | status becomes download_failed        |
| UT-VLM-006 | activate_installed_model   | active model saved to config          |
| UT-VLM-007 | activate_missing_model     | error returned                        |
| UT-VLM-008 | delete_model               | local folder removed                  |
| UT-VLM-009 | delete_active_model        | active model cleared                  |
| UT-VLM-010 | unsafe_delete_rejected     | deletion outside model root forbidden |
| UT-VLM-011 | corrupted_config_recovered | app uses safe defaults                |

### 16.8 Camera Tests

| Test ID    | Test Name                | Expected                     |
| ---------- | ------------------------ | ---------------------------- |
| UT-CAM-001 | list_cameras             | available cameras returned   |
| UT-CAM-002 | select_valid_camera      | selected camera saved        |
| UT-CAM-003 | select_missing_camera    | error returned               |
| UT-CAM-004 | camera_permission_denied | user-friendly error          |
| UT-CAM-005 | camera_disconnected      | runtime error handled        |
| UT-CAM-006 | sample_video_fallback    | sample video can be selected |

### 16.9 Privacy and Provenance Tests

| Test ID     | Test Name            | Expected                              |
| ----------- | -------------------- | ------------------------------------- |
| UT-PRIV-001 | final_decision_local | result source is local_rule_engine    |
| UT-PRIV-002 | yolo_source_recorded | detections show `yolo_mlx` source     |
| UT-PRIV-003 | vlm_advisory_only    | VLM answer cannot change final status |
| UT-PRIV-004 | privacy_log_present  | result includes privacy log           |
| UT-PRIV-005 | no_cloud_default     | default config has cloud disabled     |

## 17. E2E Test Plan

### 17.1 App Launch and Install E2E

| Test ID | Scenario                               | Expected                                      |
| ------- | -------------------------------------- | --------------------------------------------- |
| E2E-001 | Open DMG and launch app                | App launches successfully                     |
| E2E-002 | First launch without camera permission | Permission prompt or clear instruction shown  |
| E2E-003 | First launch with no YOLO model        | App asks user to install `.npz`               |
| E2E-004 | First launch with no VLM               | App still allows SOP monitoring               |
| E2E-005 | Backend health check                   | Local runtime shows ready or actionable error |

### 17.2 Camera E2E

| Test ID | Scenario                       | Expected                              |
| ------- | ------------------------------ | ------------------------------------- |
| E2E-010 | Select built-in camera         | Preview appears                       |
| E2E-011 | Select USB camera              | Preview appears if connected          |
| E2E-012 | Disconnect selected USB camera | App shows recoverable error           |
| E2E-013 | Use sample video               | Video playback starts                 |
| E2E-014 | Deny camera permission         | App explains how to enable permission |

### 17.3 YOLO Model E2E

| Test ID | Scenario                   | Expected                                                    |
| ------- | -------------------------- | ----------------------------------------------------------- |
| E2E-020 | Install valid `.npz` model | Model appears as installed                                  |
| E2E-021 | Install invalid file       | App rejects with error                                      |
| E2E-022 | Activate installed model   | Active model shown in runtime status                        |
| E2E-023 | Run sample inference       | Detections appear in overlay                                |
| E2E-024 | Delete model               | Model removed and runtime disabled until new model selected |

### 17.4 SOP Monitoring E2E

| Test ID | Scenario                     | Expected                                   |
| ------- | ---------------------------- | ------------------------------------------ |
| E2E-030 | Run all-pass sample video    | Overall status passed                      |
| E2E-031 | Run missing connector sample | Connector step failed or uncertain         |
| E2E-032 | Run cuff-too-low sample      | Cuff above elbow failed                    |
| E2E-033 | Run elbow-hidden sample      | Needs Review                               |
| E2E-034 | Run start-too-early sample   | Start after setup failed                   |
| E2E-035 | Open evidence review         | Evidence frame and boxes shown             |
| E2E-036 | Review decision trace        | Final decision source is local rule engine |

### 17.5 VLM Model E2E

| Test ID | Scenario                       | Expected                                         |
| ------- | ------------------------------ | ------------------------------------------------ |
| E2E-040 | Open Local VLM settings        | SmolVLM and Moondream 2 shown                    |
| E2E-041 | Download SmolVLM               | Status changes to installed                      |
| E2E-042 | Activate SmolVLM               | Model becomes active                             |
| E2E-043 | Ask question on evidence frame | Local advisory answer shown                      |
| E2E-044 | Delete active VLM              | Active model cleared                             |
| E2E-045 | Ask question with no VLM       | App says VLM not installed, SOP result unchanged |
| E2E-046 | Simulate download failure      | Retry-friendly error shown                       |

### 17.6 Creator Mock E2E

| Test ID | Scenario                     | Expected                       |
| ------- | ---------------------------- | ------------------------------ |
| E2E-050 | Open Creator Mode            | Mock dashboard appears         |
| E2E-051 | Navigate to labeling mock    | Animated boxes appear          |
| E2E-052 | Navigate to training mock    | Animated progress shown        |
| E2E-053 | Navigate to rule studio mock | Rule authoring animation shown |
| E2E-054 | Export mock package          | Success state shown            |

### 17.7 Regression E2E

| Test ID | Scenario                         | Expected                                  |
| ------- | -------------------------------- | ----------------------------------------- |
| E2E-060 | VLM unavailable during SOP run   | SOP monitoring still works                |
| E2E-061 | YOLO unavailable during SOP run  | App blocks run with clear error           |
| E2E-062 | Rule engine error                | App shows failed analysis state, no crash |
| E2E-063 | Delete run data                  | Local result files removed                |
| E2E-064 | Restart app after config changes | Settings persist                          |

## 18. Demo Script

### 18.1 One-Minute Demo

```text
0–8s
Open SoPilot from macOS app. Show local runtime ready.

8–15s
Select BP Monitor SOP Checker. Show All Local mode.

15–25s
Select camera or sample video. Start monitoring.

25–38s
Show YOLO MLX overlay detecting monitor, cuff, connector, arm, elbow.

38–48s
Show SOUP rule engine result:
- Monitor visible: passed
- Connector attached: passed
- Cuff on upper arm: passed
- Cuff above elbow: uncertain/failed
- Start after setup: failed or passed

48–55s
Open evidence review. Show bounding boxes and rule explanation.

55–60s
Show Local VLM dropdown and Creator mock training page.
End with: final decision local.
```

## 19. Acceptance Criteria

The PRD 2.0 MVP is successful if:

1. User can install and launch macOS app from `.dmg`.
2. User can select built-in, USB, or sample video input.
3. User can install and activate YOLO `.npz` model locally.
4. App can run YOLO MLX inference locally.
5. App can draw detection overlays.
6. App can evaluate BP Monitor SOP with SOUP rule engine.
7. App can show step-level pass/fail/uncertain result.
8. App can show evidence frame and decision trace.
9. User can download, activate, and delete SmolVLM or Moondream 2.
10. User can ask a local VLM question if a model is installed.
11. VLM answer is advisory only.
12. Creator labeling/training pages exist as animated mockups.
13. Unit tests cover rule engine, geometry, model management, and safety logic.
14. E2E tests cover install, camera, model install, monitoring, VLM management, and creator mock flow.

## 20. Open Questions

No blocking questions for implementation, but these should be resolved during build:

1. Which exact SmolVLM Hugging Face repository and runtime format should be used for the first downloadable model?
2. Which exact Moondream 2 runtime path should be used: direct Python inference, MLX conversion, or another local adapter?
3. Should the first YOLO `.npz` model be bundled with the demo build or selected manually from local drive?
4. Should the app use live camera by default or sample video by default for the hackathon demo?
5. Should DMG be signed and notarized for external judges, or is ad-hoc signing acceptable for internal demo submission?
6. What is the minimum supported Mac hardware: Apple Silicon only, or Intel fallback with disabled MLX?

## 21. Recommended Build Priority

### Day 1 Morning

* Package shell app.
* Backend health check.
* Camera or sample video preview.
* YOLO `.npz` model installer.
* Rule engine unit tests.

### Day 1 Afternoon

* YOLO MLX runner.
* Detection overlay.
* Scene event builder.
* BP SOP rule evaluation.
* Result JSON.

### Day 2 Morning

* Result screen.
* Evidence review.
* VLM model manager UI.
* Download/activate/delete flow.
* Creator mock pages.

### Day 2 Afternoon

* E2E tests.
* DMG packaging.
* Demo script.
* README.
* 1-minute video recording.

## 22. Final Definition

SoPilot macOS PRD 2.0 is a scoped hackathon version that prioritizes a credible local runtime over full product breadth.

The real implementation is:

```text
Mac app
+ camera/sample video
+ YOLO MLX .npz inference
+ SOUP rule engine
+ local evidence/result trace
+ optional local VLM model manager
```

The mocked implementation is:

```text
Creator workflow
+ labeling screens
+ training screens
+ model testing screens
+ package export animation
```

This version is optimized for a 2-day build and a 1-minute demo while preserving the long-term product thesis: local AI packages for real-world SOP monitoring.
