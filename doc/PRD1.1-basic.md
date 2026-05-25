# SoPilot Mobile App PRD

## 1. Product Summary

**Product name:** SoPilot
**Core artifact:** SOUP Package
**SOUP meaning:** Standard Operating Understanding Package
**Primary platform:** Mobile app with local Mac runtime support
**Initial demo domain:** Blood Pressure Monitor SOP validation
**Product type:** Local-first SOP video checker, SOUP package marketplace, and creator workflow builder

SoPilot is a mobile-first product that lets users validate whether a real-world workflow video follows a Standard Operating Procedure. The system uses local computer vision, local rules, and optional VLM assistance to convert video into structured scene events, then evaluates those events against a SOUP package.

The product has two sides:

1. **Consumer Mode** — users install a SOUP package, record or upload a workflow video, and receive a step-by-step compliance result.
2. **Creator Mode** — creators build SOUP packages by uploading training videos, labeling objects, training/testing a YOLO model, writing local rules, and publishing the package to the SOUP Store.

The key product principle is:

> SoPilot is not a cloud VLM wrapper. SoPilot is a local SOP decision engine. Cloud VLM is only an optional advisory helper for ambiguous cases.

---

## 2. Background and Motivation

Many physical workflows are still checked manually. A user, trainer, supervisor, or technician may need to know whether a process was completed correctly, but the evidence is often buried in video or observed live without structured validation.

Examples include:

* Setting up a blood pressure monitor correctly.
* Inspecting HVAC equipment before activation.
* Following a lab protocol.
* Performing a factory safety checklist.
* Completing a field-service repair workflow.

Current approaches are limited:

* **Manual checklists** require self-reporting and are easy to skip.
* **Video review** is slow and subjective.
* **Cloud VLM-only workflows** can be hard to audit, expensive, latency-sensitive, and privacy-sensitive.
* **Hard-coded CV demos** are brittle and difficult for non-engineers to package or distribute.

SoPilot solves this by packaging workflow rules, object models, local runtime policy, and validation logic into a reusable **SOUP package**.

---

## 3. Product Vision

SoPilot should become the easiest way to create, distribute, and run local-first SOP validation packages for physical workflows.

Long-term, SoPilot can become a marketplace and runtime for executable SOPs:

* Creators build SOUP packages for specific workflows.
* Users install packages from a SOUP Store.
* The mobile app records or uploads video.
* Local models and rule engines validate the workflow.
* Users receive an explainable compliance report.
* Ambiguous cases can optionally ask a cloud VLM for advisory interpretation after redaction and minimization.

---

## 4. Goals

### 4.1 Product Goals

1. Let users install and run SOUP packages from a mobile app.
2. Validate workflow videos using local-first AI and local rules.
3. Make final SOP decisions locally, not in the cloud.
4. Provide explainable step-level results with evidence clips.
5. Let creators build SOUP packages through a guided mobile workflow.
6. Support optional Guarded Hybrid mode for ambiguous cases.
7. Demonstrate a complete hackathon flow using a Blood Pressure Monitor SOP package.

### 4.2 Demo Goals

The MVP demo should show:

1. A user installs a Blood Pressure Monitor SOUP package.
2. The user selects All Local mode.
3. The user records or uploads a BP monitor workflow video.
4. SoPilot samples frames, runs YOLO/tracker, creates scene events, and evaluates local rules.
5. The app returns a result with passed, failed, and uncertain steps.
6. The user can ask follow-up questions such as “Can I repeat step 4?”
7. Optional: switch to Guarded Hybrid mode and show the ambiguity gate, redaction preview, cloud summary, and local final evaluation.

---

## 5. Non-Goals

For MVP, SoPilot will not:

1. Provide medical diagnosis or clinical advice.
2. Guarantee regulatory compliance.
3. Replace a trained professional.
4. Upload raw video by default.
5. Let cloud VLM make the final decision.
6. Support every SOP domain at launch.
7. Provide a full web-based creator studio.
8. Handle multi-camera workflows.
9. Support real-time production-grade monitoring at high FPS.
10. Provide a full payment system for the SOUP Store in the hackathon version.

---

## 6. Target Users

### 6.1 Consumer User

A consumer user wants to check whether they performed a workflow correctly.

Example users:

* Home user learning how to use a blood pressure monitor.
* Caregiver helping someone perform a home health workflow.
* Technician following equipment setup steps.
* Trainee practicing a physical procedure.

Needs:

* Simple package installation.
* Easy camera recording or video upload.
* Clear pass/fail/needs-review result.
* Explanation of what went wrong.
* Guidance on whether they can repeat a step or need to restart.
* Confidence that private video and rules stay local.

### 6.2 Creator User

A creator builds SOUP packages for others to install and use.

Example creators:

* Medical device trainer.
* Equipment manufacturer.
* Field-service expert.
* Safety officer.
* SOP consultant.
* Internal operations team.

Needs:

* Create package metadata.
* Upload or capture correct and incorrect workflow videos.
* Label objects and actions.
* Train/test YOLO model.
* Author rules with AI help.
* Debug failed rules.
* Export or publish a SOUP package.

### 6.3 Reviewer / Supervisor

A reviewer inspects completed runs.

Needs:

* See run summary.
* Review evidence clips.
* Understand decision trace.
* Export report.
* Verify whether cloud VLM was used.
* See privacy log.

---

## 7. Core Product Principles

### 7.1 Local-First Decision Model

SoPilot must clearly communicate:

* SOP rules stay local.
* YOLO model stays local after installation.
* Raw video stays local by default.
* Rule engine makes the final decision locally.
* Local open VLM can help create scene events.
* Cloud VLM is optional.
* Cloud VLM is used only for ambiguity, low confidence, or user-requested clarification.
* Cloud VLM receives minimized/redacted context only.
* Cloud VLM summary returns to the local rule engine.

### 7.2 Cloud VLM Is Advisory Only

Cloud VLM must never be described as the final decision maker.

Allowed cloud role:

* Explain ambiguous frames.
* Summarize a cropped/redacted scene.
* Answer a single-step visual question.

Blocked cloud role:

* Making final pass/fail decision.
* Receiving full SOP script.
* Receiving raw video.
* Receiving full package JSON.
* Receiving YOLO model.

### 7.3 Explainability by Default

Every result should show:

* Which step passed, failed, or was uncertain.
* Which evidence supported the decision.
* Which local rule fired.
* Whether local VLM was used.
* Whether cloud VLM was used.
* Whether redaction/minimization occurred.

### 7.4 Creator-Friendly Packaging

A SOUP package should feel like an app-like workflow module:

* Name.
* Icon.
* Category.
* SOP rules.
* Object labels.
* Model metadata.
* Runtime policy.
* Safety note.
* Test videos / validation state.

### 7.5 Trust and Safety

For workflows with health, safety, or equipment risk, SoPilot must frame itself as workflow assistance, not expert replacement.

For the BP monitor demo:

> For workflow assistance only. Not medical diagnosis.

---

## 8. Operating Modes

### 8.1 All Local Mode

All core components run locally:

* Frame sampler.
* YOLO / tracker.
* Local open VLM.
* SOP rules.
* Rule engine.
* Final decision.
* Reports and evidence.

Cloud VLM is disabled.

This is the default MVP mode and the strongest privacy story.

### 8.2 Guarded Hybrid Mode

The system still runs locally first. Cloud VLM is only triggered when:

* Local confidence is low.
* Local VLM result is ambiguous.
* User explicitly asks for clarification.

Before cloud VLM use, SoPilot must:

* Ask for user confirmation.
* Redact/minimize visual context.
* Avoid raw video upload.
* Avoid full frame unless explicitly allowed.
* Avoid SOP script upload.
* Avoid YOLO model upload.
* Send only allowed inputs.

Allowed cloud inputs:

* Redacted crop.
* Detection summary.
* Single-step question.

Final decision remains local.

---

## 9. Key Concepts

### 9.1 SOUP Package

A SOUP package is an installable SOP validation package. It contains or references:

* Package metadata.
* SOP steps.
* Object tags.
* Rule definitions.
* Runtime policy.
* Model metadata.
* YOLO model URI or local model path.
* Local VLM configuration.
* Optional cloud VLM policy.
* Safety note.
* Test status.

### 9.2 Scene Event

A scene event is a structured observation extracted from video.

Examples:

* `monitor_visible`
* `connector_attached`
* `cuff_on_upper_arm`
* `cuff_above_elbow_uncertain`
* `start_button_pressed`

Scene events can come from:

* YOLO/tracker geometry.
* Local VLM summary.
* Optional cloud VLM advisory summary.

### 9.3 Local Rule Engine

The local rule engine evaluates scene events against package rules.

Examples:

* Monitor must be visible before setup begins.
* Connector must attach cuff to monitor before start.
* Cuff must be on upper arm.
* Cuff must be above elbow bend.
* Start button must be pressed after cuff placement.

### 9.4 Decision Trace

The decision trace explains where each result came from:

* Frame sampler: local.
* YOLO / tracker: local.
* Local open VLM: used or not used.
* Cloud VLM: used or not used.
* Rule engine: local.
* Final evaluation: local.

---

## 10. Information Architecture

Bottom navigation:

1. **Home** — installed packages, runtime status, recent runs.
2. **Store** — discover and install SOUP packages.
3. **Create** — creator projects and SOUP package builder.
4. **Runs** — completed analysis runs and reports.
5. **Me** — settings, privacy mode, local models, storage.

---

## 11. Primary User Flows

### 11.1 Consumer Flow: Install and Run SOP Check

1. User opens SoPilot.
2. User goes to SOUP Store.
3. User searches for Blood Pressure Monitor SOP.
4. User opens package detail.
5. User reviews workflow, decision pipeline, safety note, and privacy mode.
6. User installs the package.
7. User chooses All Local or Guarded Hybrid.
8. User starts a SOP check.
9. User records new workflow video or uploads an existing video.
10. SoPilot runs local validation.
11. User views result summary.
12. User reviews evidence or asks SoPilot a question.
13. User exports report, reruns, or repeats a failed step.

### 11.2 Guarded Hybrid Flow

1. Local pipeline detects ambiguous step.
2. App shows Ambiguity Gate.
3. User sees why local confidence is low.
4. User sees what would be sent to cloud.
5. User reviews redaction/minimization preview.
6. User approves one-time cloud VLM request.
7. Cloud VLM returns advisory summary.
8. Local rule engine performs final evaluation.
9. Result shows cloud was used once and final decision was local.

### 11.3 Creator Flow: Build SOUP Package

1. Creator starts new SOUP package.
2. Creator enters package metadata.
3. Creator captures correct and wrong workflow videos.
4. Creator uploads part images.
5. App extracts frames.
6. Creator labels object tags and bounding boxes.
7. Creator trains YOLO model.
8. Creator tests model performance.
9. Creator authors rules using AI Rule Studio.
10. Creator tries rules on test videos.
11. Creator debugs failed rules.
12. Creator exports `.soup` JSON or publishes to Store.

---

## 12. Functional Requirements

## 12.1 Launch / Role Selection

### Purpose

Introduce SoPilot and let user choose between consuming or creating SOUP packages.

### Requirements

* Show product name and subtitle.
* Explain SOP and SOUP in plain language.
* Show local-first decision principles.
* Provide two primary actions:

  * Use a SOUP Package.
  * Create a SOUP Package.

### Acceptance Criteria

* User can choose Consumer Mode.
* User can choose Creator Mode.
* Screen clearly says rules, YOLO model, and final decision stay local.
* Screen explains cloud VLM is only for ambiguity.

---

## 12.2 Home Dashboard

### Purpose

Show installed packages, recent runs, and quick entry points.

### Requirements

* Show installed SOUP packages.
* For each package, show:

  * Name.
  * Runtime mode.
  * Pipeline summary.
  * Final decision policy.
  * Start Check CTA.
* Show recent runs.
* For each recent run, show:

  * Package name.
  * Score.
  * Status.
  * Cloud VLM usage.
  * View Report CTA.
* Provide Install SOUP and Create SOUP CTAs.

### Acceptance Criteria

* User can start a check from an installed package.
* User can open a previous report.
* User can navigate to Store.
* User can navigate to Create.

---

## 12.3 SOUP Store Home

### Purpose

Let users discover SOUP packages.

### Requirements

* Search bar.
* Category chips.
* Featured packages.
* Package cards with:

  * Name.
  * Short description.
  * Runtime modes.
  * Final decision policy.
  * View CTA.

### Categories for MVP

* Healthcare.
* HVAC.
* Factory.
* Safety.
* Field Service.
* Lab.

### Acceptance Criteria

* User can search packages.
* User can open package detail.
* Package cards communicate whether cloud is optional or not.

---

## 12.4 Package Detail Page

### Purpose

Explain what the package checks before installation.

### Requirements

For the BP Monitor SOP package, show:

* Package icon or demo video.
* Package name.
* Creator name.
* Step checklist:

  * Monitor visible.
  * Cuff on upper arm.
  * Grey connector attached.
  * Start after cuff placement.
* Decision pipeline:

  * Frame sampler.
  * YOLO / tracker.
  * Local open VLM to scene events.
  * Local rule engine.
  * Local compliance result.
* Optional cloud path.
* Redaction/minimization rules.
* Package info:

  * Version.
  * Model format.
  * Model host.
  * Runtime modes.
* Safety note.
* CTAs:

  * Install SOUP.
  * Try Sample Video.
  * View Rules.

### Acceptance Criteria

* User understands what the package validates.
* User understands final decision is local.
* User understands cloud VLM is optional and advisory.
* User can install package.

---

## 12.5 Install and Configure Privacy Mode

### Purpose

Let user choose runtime mode during installation.

### Requirements

* Show install progress.
* Show model binary name and host.
* Show runtime mode selection:

  * All Local.
  * Guarded Hybrid.
* Show cloud fallback policy options:

  * Ask before cloud VLM use.
  * Send minimized summary only.
  * Redact faces/hands if needed.
  * Keep SOP script local.
  * Keep YOLO model local.
* Install CTA.

### Acceptance Criteria

* User can choose All Local.
* User can choose Guarded Hybrid.
* User can require confirmation before cloud use.
* Package cannot enable cloud fallback without showing privacy explanation.

---

## 12.6 Start SOP Check

### Purpose

Start a validation session from an installed package.

### Requirements

* Show selected package.
* Show runtime mode.
* Show local decision stack:

  * SOP script/rules.
  * YOLO model.
  * Tracker.
  * Local open VLM.
  * Rule engine.
* Show input choices:

  * Record new workflow video.
  * Upload existing video.
* Show checklist preview.
* Start Camera CTA.

### Acceptance Criteria

* User can record new video.
* User can upload existing video.
* User sees checklist before starting.
* User sees local runtime components before starting.

---

## 12.7 Live Camera Overlay

### Purpose

Let user record a workflow with real-time status overlay.

### Requirements

* Show live camera view.
* Overlay YOLO boxes for detected objects.
* Show SOP checklist progress.
* Show runtime status:

  * Frame sampler.
  * YOLO / tracker.
  * Local open VLM.
  * Rule engine.
* Controls:

  * Pause.
  * Finish & Analyze.

### Acceptance Criteria

* App can display detection boxes over camera view.
* App shows checklist progress while recording.
* User can finish recording and begin analysis.

---

## 12.8 Offline Validation Progress

### Purpose

Show local analysis progress after recording or upload.

### Requirements

* Show pipeline stages:

  * Frame sampler.
  * YOLO / tracker.
  * Local open VLM.
  * Rule engine.
  * Local decision.
* Show progress per stage.
* Show scene events as they are detected.
* Show privacy status:

  * Raw video stayed local.
  * SOP rules stayed local.
  * YOLO model stayed local.
  * Final decision will be local.

### Acceptance Criteria

* User can see that local analysis is running.
* User can see scene events appearing.
* User can verify privacy guarantees.

---

## 12.9 Ambiguity Gate

### Purpose

Control optional cloud VLM use in Guarded Hybrid mode.

### Trigger

Only appears when:

* Runtime mode is Guarded Hybrid.
* Local confidence is below threshold.
* A step is ambiguous.
* User asks for clarification requiring cloud help.

### Requirements

* Show ambiguous step.
* Show local confidence score.
* Explain why local system is unsure.
* State current mode.
* Explain cloud VLM role.
* Show privacy guarantees.
* Show context to send:

  * Cropped cuff/arm frame.
  * Detection summary.
  * Step question.
  * Full frame disabled by default.
  * Full video disabled.
* CTAs:

  * Use Cloud VLM Once.
  * Skip and Mark Needs Review.

### Acceptance Criteria

* Cloud VLM cannot be used without explicit user action.
* User sees what data would be sent.
* User can skip cloud use.
* If skipped, result becomes Needs Review or Uncertain.

---

## 12.10 Redaction / Minimization Preview

### Purpose

Show the user exactly what will be sent to cloud.

### Requirements

* Show cropped/redacted image preview.
* Show text summary to send.
* Explicitly say no SOP script included.
* CTAs:

  * Send Minimized Context.
  * Cancel.

### Acceptance Criteria

* User can review visual and text payload before cloud call.
* User can cancel.
* Raw video is not sent.
* Full SOP package is not sent.

---

## 12.11 Cloud VLM Summary Returned

### Purpose

Show advisory cloud result and return to local evaluation.

### Requirements

* Show summary received from cloud VLM.
* Clearly state it is not final decision.
* Explain next step: local rule engine will evaluate.
* CTA: Run Local Final Evaluation.

### Acceptance Criteria

* Cloud result is labeled advisory.
* User understands final decision remains local.
* Local rule engine is invoked after cloud summary.

---

## 12.12 Result Summary with Chat

### Purpose

Show final compliance result and allow user to ask follow-up questions.

### Requirements

* Show package name.
* Show compliance score.
* Show status:

  * Passed.
  * Needs Review.
  * Failed.
* Show decision path:

  * Frame sampler.
  * YOLO / tracker.
  * Local open VLM.
  * Cloud VLM.
  * Final rule evaluation.
* Show step results:

  * Passed steps.
  * Failed steps.
  * Uncertain steps.
* Provide Ask SoPilot input.
* Suggested questions:

  * Can I repeat only failed step?
  * Why did step 4 fail?
  * Show evidence clip.
  * Was cloud VLM used?
* CTAs:

  * Review Evidence.
  * Export Report.
  * Run Again.

### Acceptance Criteria

* User can understand result without reading raw logs.
* User can ask questions grounded in local rules and run evidence.
* Result clearly indicates whether cloud was used.

---

## 12.13 Evidence Review

### Purpose

Let user inspect why a step passed, failed, or was uncertain.

### Requirements

* Show selected step.
* Show status.
* Show evidence clip or frame.
* Show YOLO boxes and timeline marker.
* Show local rule explanation.
* Show scene events.
* Show local VLM summary.
* Show cloud VLM status.
* Provide question input.
* Recovery actions:

  * Recheck step.
  * Mark as false positive.
  * Restart from previous step.
  * Update rule suggestion.

### Acceptance Criteria

* User can see visual evidence for a decision.
* User can distinguish local vs cloud sources.
* User can take a recovery action.

---

## 12.14 Creator Dashboard

### Purpose

Manage creator projects.

### Requirements

* Show creator projects.
* Each project card shows:

  * Name.
  * Status.
  * Model state.
  * Runtime policy.
  * Cloud fallback status.
  * Continue CTA.
* New SOUP Package CTA.

### Acceptance Criteria

* Creator can resume existing project.
* Creator can start new project.

---

## 12.15 New Creator Project

### Purpose

Create package metadata and define policy.

### Requirements

* Upload package icon.
* Enter package name.
* Select category.
* Describe what package checks.
* Show fixed decision policy:

  * SOP rules stay local.
  * Final rule evaluation is local.
  * Optional cloud VLM only for low-confidence ambiguity.
* Enter target users.
* Enter safety note.
* Create Project CTA.

### Acceptance Criteria

* Creator can create project shell.
* Package cannot be created without name, category, description, and safety note.
* Local-final decision policy is visible.

---

## 12.16 Capture Training Data

### Purpose

Collect videos and images for model training and rules.

### Requirements

* Record correct workflow video.
* Record wrong workflow video.
* Upload part images from multiple angles.
* Show uploaded videos.
* Extract Frames CTA.

### Acceptance Criteria

* Creator can upload or record correct and incorrect examples.
* Creator can upload object part images.
* Creator can continue to frame extraction.

---

## 12.17 Extract Frames

### Purpose

Sample frames from training videos.

### Requirements

* Show selected videos.
* Frame sampler settings:

  * Every N seconds.
  * Add high-motion frames.
  * Add action-transition frames.
* Show estimated frames.
* Show frame preview grid.
* CTAs:

  * Start Extraction.
  * Continue to Tagging.

### Acceptance Criteria

* Creator can configure sampling interval.
* System can extract frames.
* Creator can continue to tagging.

---

## 12.18 Label Tags

### Purpose

Label objects and bounding boxes for YOLO training and rules.

### Requirements

* Show current frame index.
* Show current tag dropdown.
* Show frame image.
* Support drawing bounding boxes.
* Support deleting boxes.
* Show tag list.
* Manage tags:

  * Add.
  * Edit.
  * Delete.
* Show tag details:

  * Name.
  * Description.
  * Used by YOLO.
  * Used by rules.
* Auto-label similar frames CTA.
* Prev / Save / Next navigation.

### Acceptance Criteria

* Creator can create and manage tags.
* Creator can draw bounding boxes.
* Labels are saved to dataset.
* Creator can move through frames efficiently.

---

## 12.19 Train YOLO Model

### Purpose

Train object detector from labeled frames.

### Requirements

* Show dataset summary:

  * Videos.
  * Frames.
  * Labels.
  * Tags.
* Select model size.
* Select output format `.pt`.
* Select runtime target.
* Start Training CTA.
* Show progress:

  * Epoch.
  * Loss.
  * mAP.
  * Progress bar.
* View Sample Detections CTA.

### Acceptance Criteria

* Creator can start training.
* Creator can monitor training metrics.
* Trained model is available for testing.

---

## 12.20 Test YOLO Model

### Purpose

Validate model performance before packaging.

### Requirements

* Select test set.
* Show metrics:

  * Recall rate.
  * False detection rate.
  * Precision.
  * mAP.
* Show tag-level performance.
* Review queues:

  * Missed detections.
  * False boxes.
  * Low confidence.
  * Wrong tag.
* Show runtime impact note.
* CTAs:

  * Open Review Queue.
  * Add More Labels.
  * Accept Model.

### Acceptance Criteria

* Creator can identify weak tags.
* Creator can accept model or improve labels.
* Weak detection tags can be marked as ambiguity-prone.

---

## 12.21 Rule Authoring Chat

### Purpose

Let creator define SOP rules using natural language and AI assistance.

### Requirements

* Show rule source policy:

  * Stored locally in `.soup`.
  * Used by local rule engine.
  * Not sent to cloud VLM.
* Show video frame context.
* Provide chat interface.
* Convert creator text into generated local rules.
* Show generated rule list.
* CTAs:

  * Open Rule Studio.
  * Try Run.

### Acceptance Criteria

* Creator can describe a rule in plain language.
* System generates structured rule candidates.
* Creator can inspect and edit generated rules.

---

## 12.22 AI Rule Studio

### Purpose

Edit, parameterize, and test structured rules.

### Requirements

* Show frame context strip.
* Show selected frame with bounding boxes.
* Show generated rule text.
* Provide Chat and Parameters tabs.
* In Chat tab:

  * Explain how rule is checked locally.
  * Let creator request changes.
* In Parameters tab:

  * Rule type.
  * Source tag.
  * Target tag.
  * Direction.
  * Angle tolerance.
  * Min confidence.
  * Local VLM assistance.
  * Cloud fallback policy.
* Show live rule preview.
* CTAs:

  * Generate Rule.
  * Save Rule.
  * Try on Video.

### Acceptance Criteria

* Creator can edit rule parameters.
* Creator can preview rule on selected frame.
* Creator can save rule to package.

---

## 12.23 Try Run Rules

### Purpose

Test full package rules on sample videos.

### Requirements

* Select test video.
* Show runtime path.
* Run Test CTA.
* Show results by step.
* Show expected vs actual.
* Show cloud VLM usage.
* CTAs:

  * Accept.
  * Edit Failed Rule.

### Acceptance Criteria

* Creator can run package against known videos.
* Creator can verify expected outcome.
* Failed rule can be debugged.

---

## 12.24 Failed Rule Debug

### Purpose

Help creator improve a failing rule.

### Requirements

* Show failed item.
* Show evidence frame.
* Show detected geometry or confidence.
* Show local reason.
* Show local VLM summary.
* Show cloud fallback status.
* Provide AI suggestion.
* Provide chat edit.
* CTAs:

  * Update Rule.
  * Try Again.

### Acceptance Criteria

* Creator understands why rule failed.
* Creator can update threshold or add more labels.
* Creator can rerun test.

---

## 12.25 Package and Publish SOUP

### Purpose

Export or publish the completed SOUP package.

### Requirements

* Show package summary:

  * Name.
  * Version.
  * Model.
  * Model host.
  * Rule count.
  * Test video count.
* Show decision policy.
* Show validation checklist:

  * Schema valid.
  * Model link works.
  * Sample tests passed.
  * Safety note included.
* CTAs:

  * Export `.soup` JSON.
  * Publish to Store.

### Acceptance Criteria

* Creator cannot publish invalid package.
* Creator can export package for local testing.
* Published package includes runtime policy and safety note.

---

## 12.26 Runs List

### Purpose

Show previous validation runs.

### Requirements

* Group runs by date.
* Run card fields:

  * Package name.
  * Score.
  * Status.
  * Decision location.
  * Cloud VLM usage.
  * Open CTA.

### Acceptance Criteria

* User can find previous runs.
* User can open report detail.

---

## 12.27 Report Detail

### Purpose

Provide complete analysis report.

### Requirements

* Package name.
* Run ID.
* Mode.
* Overall score and status.
* Decision trace.
* Failed steps.
* Uncertain steps.
* Evidence clips.
* Privacy log.
* CTAs:

  * Export PDF.
  * Share Summary.
  * Delete Run.

### Acceptance Criteria

* User can understand what happened in the run.
* User can export/share summary.
* User can delete run.
* Privacy trace is visible.

---

## 12.28 Settings / Privacy

### Purpose

Configure runtime defaults and privacy policy.

### Requirements

* Default runtime mode:

  * All Local.
  * Guarded Hybrid.
* Local open VLM selector.
* Remote cloud VLM selector.
* Cloud fallback triggers:

  * Low confidence.
  * Ambiguous local VLM summary.
  * User asks for clarification.
  * Always use cloud VLM disabled or discouraged.
* Redaction/minimization settings:

  * Do not upload raw video.
  * Do not upload SOP scripts.
  * Do not upload YOLO model.
  * Send detection summary only.
  * Redact faces/background.
  * Require confirmation first.
* Final decision policy:

  * Always local rule evaluation.
  * Cloud VLM summary is advisory.
* Storage controls.

### Acceptance Criteria

* User can set default runtime mode.
* User can configure local VLM.
* User can configure cloud VLM provider if enabled.
* User can clear cache.
* User cannot configure cloud as final decision maker.

---

## 13. MVP Screens

The hackathon MVP should prioritize these screens:

1. Launch / Role Selection.
2. Home Dashboard.
3. SOUP Store Home.
4. Package Detail.
5. Install and Configure Privacy Mode.
6. Start SOP Check.
7. Live Camera Overlay.
8. Offline Validation Progress.
9. Ambiguity Gate.
10. Redaction Preview.
11. Result Summary with Chat.
12. Evidence Review.
13. Creator Dashboard.
14. New Creator Project.
15. Capture Training Data.
16. Label Tags.
17. AI Rule Studio.
18. Package and Publish.
19. Runs List.
20. Report Detail.
21. Settings / Privacy.

For a shorter demo, prioritize:

1. Install BP Monitor SOUP package.
2. Run SOP validation.
3. Show result and evidence.
4. Show Guarded Hybrid ambiguity gate.
5. Show Creator Mode package flow at high level.

---

## 14. MVP Demo Package: Blood Pressure Monitor SOP

### 14.1 Package Name

Blood Pressure Monitor SOP Checker

### 14.2 Category

Healthcare Workflow

### 14.3 Target Users

* Home users.
* Caregivers.
* Nurses.
* Trainers.
* Device onboarding teams.

### 14.4 Safety Note

For workflow assistance only. Not medical diagnosis.

### 14.5 Steps

1. Monitor is visible.
2. Grey connector is attached.
3. Cuff is on upper arm.
4. Cuff is above elbow bend.
5. Start button is pressed after setup.

### 14.6 Required Tags

* `blood_pressure_monitor`
* `cuff`
* `upper_arm`
* `elbow_bend`
* `grey_connector`
* `button`
* `screen`

### 14.7 Example Rules

1. `monitor_visible_before_start`

   * Monitor must be visible before start button press.

2. `connector_attached_before_start`

   * Grey connector must be near/attached to monitor and cuff before start.

3. `cuff_on_upper_arm`

   * Cuff bounding box should overlap upper arm region.

4. `cuff_above_elbow`

   * Cuff should be above elbow bend with configurable angle tolerance.

5. `start_after_cuff_placement`

   * Start button press should occur only after cuff placement passes or is sufficiently confident.

### 14.8 Example Result States

* Passed.
* Needs Review.
* Failed.
* Uncertain.

### 14.9 Example Failed/Uncertain Cases

* Start pressed too early.
* Cuff too close to elbow.
* Connector missing.
* Elbow hidden and cuff placement ambiguous.

---

## 15. Data and Runtime Architecture

## 15.1 Local Runtime Pipeline

```text
SOP Script / Rules
Local on Mac or local device
        │
        ▼
Video / Camera
        │
        ▼
Frame Sampler
        │
        ▼
YOLO / Tracker
        │
        ├──────────────▶ Local Open VLM
        │                       │
        │                       ▼
        │                Scene Events
        │
        ▼
Rule Engine
        │
        ▼
Local Decision
        │
        ▼
Compliance Result
        │
        ▼
Low confidence / ambiguous?
        │
   ┌────┴────┐
   │         │
  No        Yes
   │         │
   ▼         ▼
Done     Redaction / Minimization
Local        │
             ▼
     Optional Cloud VLM Summary
             │
             ▼
     Local Final Rule Evaluation
```

## 15.2 Components

### Frame Sampler

* Samples video frames at configured interval.
* Adds high-motion or transition frames in creator workflows.
* Produces frame IDs and timestamps.

### YOLO / Tracker

* Detects package-specific objects.
* Tracks object positions across frames.
* Produces bounding boxes and confidence scores.

### Local Open VLM

* Generates scene events and ambiguity explanations.
* Used for visual context that is hard to encode as pure geometry.
* Runs locally where possible.

### Rule Engine

* Evaluates structured scene events against SOUP rules.
* Produces pass/fail/uncertain results.
* Always performs final decision.

### Optional Cloud VLM

* Used only in Guarded Hybrid mode.
* Receives minimized/redacted context.
* Produces advisory summary.
* Does not receive raw video, full SOP script, YOLO model, or full package JSON.

---

## 16. SOUP Package Schema Requirements

The `.soup` package should support the decision flow.

```json
{
  "runtime": {
    "decision_policy": {
      "final_decision": "local_rule_engine",
      "cloud_vlm_role": "advisory_summary_only",
      "cloud_vlm_allowed": true,
      "cloud_vlm_trigger": [
        "low_confidence",
        "ambiguous_scene_event",
        "user_requested_help"
      ]
    },
    "privacy_modes": {
      "all_local": {
        "enabled": true,
        "raw_video_leaves_device": false,
        "sop_rules_leave_device": false,
        "yolo_model_leaves_device": false,
        "local_vlm_enabled": true,
        "cloud_vlm_enabled": false
      },
      "guarded_hybrid": {
        "enabled": true,
        "raw_video_leaves_device": false,
        "sop_rules_leave_device": false,
        "yolo_model_leaves_device": false,
        "local_vlm_enabled": true,
        "cloud_vlm_enabled": true,
        "redaction_required": true,
        "minimization_required": true,
        "require_user_confirmation": true
      }
    }
  },
  "models": {
    "detector": {
      "type": "yolo",
      "format": "pt",
      "runtime": "mlx",
      "uri": "https://r2.example.com/models/bp-yolo-v1.pt"
    },
    "local_vlm": {
      "enabled": true,
      "provider": "ollama",
      "model": "llava:latest",
      "role": [
        "scene_event_generation",
        "ambiguity_explanation"
      ]
    },
    "cloud_vlm": {
      "enabled": true,
      "provider": "openai",
      "model": "gpt-4o-mini",
      "role": [
        "optional_ambiguous_scene_summary"
      ],
      "allowed_inputs": [
        "redacted_crop",
        "detection_summary",
        "single_step_question"
      ],
      "blocked_inputs": [
        "raw_video",
        "full_sop_script",
        "yolo_model",
        "full_package_json"
      ]
    }
  }
}
```

Additional package fields needed:

```json
{
  "package": {
    "id": "bp_monitor_sop_checker",
    "name": "Blood Pressure Monitor SOP Checker",
    "version": "0.1.0",
    "category": "Healthcare Workflow",
    "creator": "Verified Creator",
    "safety_note": "For workflow assistance only. Not medical diagnosis."
  },
  "steps": [
    {
      "id": "monitor_visible",
      "name": "Monitor is visible",
      "required": true
    },
    {
      "id": "connector_attached",
      "name": "Connector is attached",
      "required": true
    },
    {
      "id": "cuff_on_upper_arm",
      "name": "Cuff is on upper arm",
      "required": true
    },
    {
      "id": "cuff_above_elbow",
      "name": "Cuff is above elbow bend",
      "required": true,
      "ambiguity_allowed": true
    },
    {
      "id": "start_after_setup",
      "name": "Start is pressed after setup",
      "required": true
    }
  ],
  "tags": [
    "blood_pressure_monitor",
    "cuff",
    "upper_arm",
    "elbow_bend",
    "grey_connector",
    "button",
    "screen"
  ],
  "rules": [
    {
      "id": "cuff_above_elbow",
      "type": "orientation",
      "source_tag": "cuff",
      "target_tag": "elbow_bend",
      "direction": "above",
      "angle_tolerance_degrees": 60,
      "min_confidence": 0.5,
      "local_vlm_assistance": "optional",
      "cloud_fallback": "only_if_ambiguous"
    }
  ]
}
```

---

## 17. Result Data Model

### 17.1 Run Result

```json
{
  "run_id": "2026-05-21-001",
  "package_id": "bp_monitor_sop_checker",
  "package_version": "0.1.0",
  "mode": "all_local",
  "overall_score": 86,
  "status": "needs_review",
  "decision_trace": {
    "frame_sampler": "local",
    "yolo_tracker": "local",
    "local_vlm": "used",
    "cloud_vlm": "not_used",
    "rule_engine": "local",
    "final_evaluation": "local"
  },
  "privacy_log": {
    "raw_video_stayed_local": true,
    "sop_script_stayed_local": true,
    "yolo_model_stayed_local": true,
    "final_decision_local": true
  }
}
```

### 17.2 Step Result

```json
{
  "step_id": "cuff_above_elbow",
  "name": "Cuff above elbow",
  "status": "uncertain",
  "confidence": 0.42,
  "reason": "Elbow bend is partially hidden and cuff relation is uncertain.",
  "evidence": {
    "timestamp": "00:23",
    "frame_id": "frame_023",
    "objects": [
      "cuff",
      "upper_arm",
      "elbow_bend"
    ],
    "local_vlm_summary": "The cuff appears near the upper arm but elbow visibility is weak.",
    "cloud_vlm_used": false
  }
}
```

### 17.3 Cloud Advisory Event

```json
{
  "event_type": "cloud_vlm_advisory_summary",
  "trigger": "ambiguous_scene_event",
  "user_confirmed": true,
  "inputs_sent": [
    "redacted_crop",
    "detection_summary",
    "single_step_question"
  ],
  "blocked_inputs": [
    "raw_video",
    "full_sop_script",
    "yolo_model",
    "full_package_json"
  ],
  "summary": "The cuff appears to be around the upper arm, but the lower edge may be too close to the elbow bend.",
  "final_decision_source": "local_rule_engine"
}
```

---

## 18. UX Copy Requirements

### 18.1 Required Local-First Copy

Use consistently across screens:

* “Final decision: Local.”
* “Cloud VLM is advisory only.”
* “Raw video stays local.”
* “SOP rules stay local.”
* “YOLO model stays local.”
* “Cloud is used only for ambiguous cases.”
* “Minimized/redacted context only.”

### 18.2 BP Monitor Safety Copy

Use consistently:

> For workflow assistance only. Not medical diagnosis.

### 18.3 Ambiguity Gate Copy

Required wording:

> Local system is unsure. Cloud VLM can help summarize this ambiguous scene, but the final decision will still be made locally.

### 18.4 Result Copy

Required wording:

> This is the final local rule evaluation.

If cloud was used:

> Cloud VLM was used once as an advisory summary after redaction/minimization. Final decision was made locally.

---

## 19. Permissions and Privacy Requirements

### 19.1 Permissions

Mobile app may request:

* Camera.
* Microphone only if needed for videos.
* Photos/videos library.
* Local network access for Mac runtime connection.
* Files access for importing packages or videos.

### 19.2 Privacy Requirements

* Raw video must not leave device/Mac by default.
* User must approve any cloud VLM request.
* Cloud VLM request must show preview of payload.
* SOP script cannot be included in cloud request.
* YOLO model cannot be uploaded to cloud VLM.
* Cloud logs should be marked in report.
* User can delete local run data.
* User can clear package/model cache.

---

## 20. Analytics and Instrumentation

Track product usage without storing sensitive raw video.

Suggested events:

* `app_launched`
* `role_selected`
* `package_viewed`
* `package_installed`
* `runtime_mode_selected`
* `sop_check_started`
* `video_recorded`
* `video_uploaded`
* `analysis_started`
* `analysis_completed`
* `step_passed`
* `step_failed`
* `step_uncertain`
* `ambiguity_gate_shown`
* `cloud_vlm_approved`
* `cloud_vlm_skipped`
* `report_exported`
* `creator_project_created`
* `frames_extracted`
* `labels_created`
* `model_training_started`
* `model_training_completed`
* `rule_created`
* `package_exported`
* `package_published`

Do not track:

* Raw frames.
* Raw videos.
* Full SOP scripts.
* Full cloud prompts containing sensitive content.

---

## 21. Success Metrics

### 21.1 Consumer MVP Metrics

* Package install completion rate.
* SOP check start rate.
* SOP check completion rate.
* Average time to result.
* Percentage of runs with understandable result.
* Evidence review open rate.
* Report export rate.
* Cloud VLM usage rate in Guarded Hybrid mode.
* Cloud VLM skip rate.

### 21.2 Creator MVP Metrics

* Creator project creation rate.
* Training data upload completion rate.
* Frame extraction completion rate.
* Labeling completion rate.
* Model training completion rate.
* Rule creation count.
* Test run pass rate.
* Package export rate.
* Package publish rate.

### 21.3 Quality Metrics

* Step detection precision.
* Step detection recall.
* Rule false positive rate.
* Rule false negative rate.
* Ambiguity rate.
* Percentage of failed cases with evidence.
* Percentage of reports with complete decision trace.

---

## 22. YOLO26 MLX Integration Plan

### 22.1 Purpose

SoPilot should use **YOLO26 MLX** as the preferred local detector runtime for Apple Silicon. The goal is to make object detection, tracking, and optional segmentation run natively on Mac without a PyTorch runtime dependency.

The uploaded YOLO26 MLX README describes the project as a pure MLX implementation for Apple Silicon with no PyTorch dependency at runtime, using Apple's MLX framework for native Metal GPU acceleration. It also supports detection, training, tracking, and segmentation workflows. This aligns directly with SoPilot's local-first decision model.

### 22.2 Why YOLO26 MLX Fits SoPilot

YOLO26 MLX is a strong match for SoPilot because:

1. **Local-first runtime**
   SoPilot needs SOP package execution to work locally on Mac. YOLO26 MLX runs in MLX on Apple Silicon and avoids PyTorch at runtime.

2. **Apple Silicon optimization**
   SoPilot's target local runtime is MacBook M-series hardware. YOLO26 MLX is designed for M1/M2/M3/M4 chips.

3. **Fast object detection**
   For SOP validation, object detection should be the fast, deterministic perception layer before VLM reasoning. YOLO26 MLX provides high FPS on Apple Silicon, especially for smaller models.

4. **Tracking support**
   SOP validation often needs object continuity across frames: cuff stays on arm, connector remains attached, tool remains in use, button press follows setup. YOLO26 MLX includes tracking support through ByteTrack and BoT-SORT.

5. **Segmentation path**
   Some SOPs may need more precise geometry than bounding boxes. YOLO26 MLX's segmentation support gives SoPilot a future path for masks, overlap, distance, and region-based rules.

6. **Creator Mode training path**
   Creator Mode includes object labeling, model training, testing, and packaging. YOLO26 MLX provides a training pipeline and custom dataset support, which maps to the Creator Mode flow.

### 22.3 Integration Scope

#### MVP Scope

For the hackathon MVP, integrate YOLO26 MLX for:

* Local object detection.
* Frame-by-frame inference on sampled video frames.
* Basic tracking for object continuity.
* Detection output normalization into SoPilot scene events.
* Model packaging inside or referenced by a `.soup` package.

#### Post-MVP Scope

After MVP, extend YOLO26 MLX integration for:

* Instance segmentation.
* Custom local fine-tuning from Creator Mode.
* Automated benchmark reporting.
* Model quality gates before publishing packages.
* Multi-model fallback between `n`, `s`, and `m` model sizes.
* On-device model conversion and validation.

### 22.4 Recommended Model Strategy

SoPilot should support several model sizes but choose defaults based on device and workflow complexity.

| Runtime target                 | Recommended model              | Use case                                       | Rationale                                           |
| ------------------------------ | ------------------------------ | ---------------------------------------------- | --------------------------------------------------- |
| MacBook Air / 16GB memory      | `yolo26n`                      | MVP, fast detection, simple SOP objects        | Highest FPS and best demo reliability               |
| MacBook Pro / 16GB+ memory     | `yolo26s`                      | Better accuracy for moderate object complexity | Good balance of accuracy and latency                |
| MacBook Pro / M4 Pro or better | `yolo26m`                      | Higher accuracy workflows                      | Better detection quality when latency budget allows |
| Advanced / offline analysis    | `yolo26l` or `yolo26x`         | Batch validation, not live UX                  | Better quality but slower                           |
| Geometry-sensitive workflows   | `yolo26n-seg` or `yolo26s-seg` | Mask overlap, region checks                    | Enables segmentation-based rules                    |

For the BP Monitor SOP demo, the default should be:

```text
yolo26n for live detection and fast iteration
yolo26s for higher-quality offline validation if needed
```

### 22.5 Runtime Architecture

YOLO26 MLX should sit between the frame sampler and the scene-event extractor.

```text
Video / Camera
        │
        ▼
Frame Sampler
        │
        ▼
YOLO26 MLX Detector / Tracker
        │
        ├── bounding boxes
        ├── class labels
        ├── confidence scores
        ├── optional track IDs
        └── optional masks
        │
        ▼
Scene Event Extractor
        │
        ├── monitor_visible
        ├── connector_attached
        ├── cuff_on_upper_arm
        ├── cuff_above_elbow_candidate
        └── start_button_pressed
        │
        ▼
Local Rule Engine
```

YOLO26 MLX should not make SOP compliance decisions directly. It only provides perception evidence. The local SoPilot rule engine remains the final decision maker.

### 22.6 Package Installation Flow

When a user installs a SOUP package:

1. Download package metadata.
2. Download or locate YOLO model artifact.
3. If package ships `.pt` weights, convert to MLX `.npz` format.
4. Verify model checksum.
5. Run a tiny smoke-test inference on sample frame.
6. Register model in local runtime cache.
7. Bind model labels to `.soup` tags.
8. Mark package as ready.

Example install state:

```json
{
  "detector_runtime": "yolo26_mlx",
  "source_weight_format": "pt",
  "runtime_weight_format": "npz",
  "model_size": "yolo26n",
  "task": "detect",
  "converted": true,
  "verified": true,
  "local_path": "models/bp-monitor-yolo26n.npz"
}
```

### 22.7 Model Conversion Plan

YOLO26 MLX uses converted MLX weights for runtime inference. SoPilot should support a conversion pipeline:

```text
Package model artifact
  .pt source weights
        │
        ▼
YOLO26 MLX converter
        │
        ▼
.npz runtime weights
        │
        ▼
Local model cache
        │
        ▼
SoPilot detector runtime
```

Implementation requirements:

* Provide `ModelConverter` service in the Mac runtime.
* Convert `.pt` to `.npz` during install or creator export.
* Store converted models in a package-specific cache folder.
* Verify converted model by running sample inference.
* Store conversion metadata in package install manifest.
* Avoid conversion during live recording.

### 22.8 Inference API Wrapper

SoPilot should wrap YOLO26 MLX behind a stable detector interface so the rest of the app is not coupled to YOLO internals.

```python
class DetectorRuntime:
    def load(self, model_path: str, labels: list[str]) -> None:
        pass

    def predict_frame(self, frame, conf: float = 0.25, imgsz: int = 640) -> list[Detection]:
        pass

    def track_video(self, video_path: str, conf: float = 0.25, tracker: str = "bytetrack") -> list[FrameDetections]:
        pass
```

Normalized detection object:

```json
{
  "frame_id": "frame_023",
  "timestamp_ms": 23000,
  "tag": "cuff",
  "confidence": 0.91,
  "bbox_xyxy": [120, 240, 360, 410],
  "track_id": 7,
  "source": "yolo26_mlx"
}
```

If segmentation is enabled:

```json
{
  "frame_id": "frame_023",
  "tag": "cuff",
  "confidence": 0.88,
  "bbox_xyxy": [120, 240, 360, 410],
  "mask_ref": "frame_023_cuff_7.mask",
  "source": "yolo26_mlx_seg"
}
```

### 22.9 Scene Event Mapping

YOLO labels must map to SOUP tags and then to rule-ready scene events.

Example:

```json
{
  "label_map": {
    "blood_pressure_monitor": "monitor",
    "grey_connector": "connector",
    "upper_arm": "upper_arm",
    "elbow_bend": "elbow_bend",
    "cuff": "cuff",
    "button": "start_button"
  }
}
```

Scene event examples:

```json
{
  "event": "cuff_on_upper_arm_candidate",
  "evidence": {
    "cuff_bbox": [120, 240, 360, 410],
    "upper_arm_bbox": [100, 220, 380, 460],
    "overlap_ratio": 0.73,
    "confidence": 0.84
  }
}
```

```json
{
  "event": "cuff_above_elbow_candidate",
  "evidence": {
    "cuff_center_y": 310,
    "elbow_center_y": 455,
    "relation": "above",
    "confidence": 0.78
  }
}
```

### 22.10 Tracking Integration

Tracking should be used when a rule depends on continuity across frames.

Examples:

* Cuff remains on the same arm for at least N seconds.
* Connector remains attached before start button press.
* Button press occurs after required setup steps.
* Tool/object remains in the required zone.

Tracking requirements:

* Use `track_id` when available.
* Persist object identity across sampled frames.
* Mark object identity as uncertain if tracker confidence drops.
* Fall back to frame-level detection if tracking is unavailable.
* Expose tracker choice in package/runtime config: `bytetrack` or `botsort`.

Example config:

```json
{
  "models": {
    "detector": {
      "runtime": "yolo26_mlx",
      "task": "detect",
      "model": "yolo26n",
      "weights": "models/bp-monitor-yolo26n.npz",
      "tracker": {
        "enabled": true,
        "type": "bytetrack",
        "persist": true,
        "vid_stride": 1
      }
    }
  }
}
```

### 22.11 Segmentation Integration

Segmentation should be optional for v0.1 and recommended only when bounding boxes are not precise enough.

Good segmentation use cases:

* Cuff overlap with upper arm.
* Hand/tool contact with object.
* Object inside/outside a region.
* Fine-grained distance from elbow bend.
* Part occlusion detection.

Segmentation package config:

```json
{
  "models": {
    "detector": {
      "runtime": "yolo26_mlx",
      "task": "segment",
      "model": "yolo26n-seg",
      "weights": "models/bp-monitor-yolo26n-seg.npz"
    }
  },
  "rules": [
    {
      "id": "cuff_overlaps_upper_arm",
      "type": "mask_overlap",
      "source_tag": "cuff",
      "target_tag": "upper_arm",
      "min_iou": 0.35,
      "min_confidence": 0.65
    }
  ]
}
```

### 22.12 Creator Mode Integration

Creator Mode should use YOLO26 MLX in four places:

1. **Training data preparation**

   * Extract frames from correct and wrong videos.
   * Save labels in YOLO-compatible format.
   * Support detection labels first; segmentation polygons later.

2. **Training**

   * Train or fine-tune YOLO26 model from labeled data.
   * Start with `yolo26n` for fast iteration.
   * Allow `yolo26s` for better quality.

3. **Model testing**

   * Run validation frames through YOLO26 MLX.
   * Show precision, recall, false detection rate, mAP, and tag-level metrics.
   * Mark weak tags as ambiguity-prone.

4. **Package export**

   * Export `.soup` package metadata.
   * Export or reference `.pt` source weights.
   * Export `.npz` MLX runtime weights when available.
   * Include label map, runtime config, benchmark summary, and model checksum.

Creator Mode model acceptance gates:

```text
Required before publish:
- schema valid
- labels complete
- model loads locally
- sample inference passes
- package rules reference valid tags
- no missing required model artifact

Recommended before publish:
- per-tag recall >= 80% for critical tags
- false detection rate <= 10% for critical tags
- model benchmark available
- at least one correct and one wrong test video pass expected outcomes
```

### 22.13 Runtime Config Additions to `.soup`

Add these fields to support YOLO26 MLX.

```json
{
  "models": {
    "detector": {
      "provider": "yolo26_mlx",
      "task": "detect",
      "model_size": "n",
      "source_format": "pt",
      "runtime_format": "npz",
      "source_uri": "https://r2.example.com/models/bp-monitor-yolo26n.pt",
      "runtime_path": "models/bp-monitor-yolo26n.npz",
      "checksum": "sha256:...",
      "imgsz": 640,
      "conf_threshold": 0.25,
      "labels": [
        "blood_pressure_monitor",
        "cuff",
        "upper_arm",
        "elbow_bend",
        "grey_connector",
        "button",
        "screen"
      ],
      "label_map": {
        "blood_pressure_monitor": "monitor",
        "grey_connector": "connector",
        "button": "start_button"
      },
      "tracking": {
        "enabled": true,
        "tracker": "bytetrack",
        "persist": true,
        "vid_stride": 1
      },
      "conversion": {
        "required": true,
        "converter": "yolo26mlx.converters",
        "verify_after_conversion": true
      }
    }
  }
}
```

### 22.14 Benchmark and QA Requirements

Each package should store a small local benchmark summary after install or creator export.

Benchmark fields:

```json
{
  "benchmark": {
    "device": "Apple M4 Pro",
    "model": "yolo26n",
    "task": "detect",
    "imgsz": 640,
    "mean_latency_ms": 12.5,
    "fps": 80.0,
    "peak_memory_mb": 900,
    "sample_size": 100
  }
}
```

QA checks:

* Model file exists.
* Model checksum matches.
* Model loads in MLX.
* Sample inference returns expected output shape.
* Labels align with package tags.
* Critical tags have enough validation examples.
* Tracking can run on at least one sample video if enabled.
* Segmentation masks are present if segmentation rules are used.

### 22.15 UI Changes Required

#### Package Detail

Add model runtime details:

```text
Detector Runtime
YOLO26 MLX · Apple Silicon optimized
Model: yolo26n
Task: Detection + tracking
Runtime weights: .npz
Final decision: Local rule engine
```

#### Install Screen

Add conversion progress:

```text
Model setup
Downloading yolo26n .pt weights...
Converting to MLX .npz...
Verifying sample inference...
Registered local detector runtime.
```

#### Offline Analysis Progress

Replace generic YOLO copy with YOLO26 MLX:

```text
2. YOLO26 MLX / Tracker
██████████████░░░░ 76%
Detected: cuff, upper_arm, grey_connector, monitor
Tracking: active
```

#### Creator Train Screen

Update runtime target:

```text
Model
[ YOLO26 small / yolo26n ▼ ]

Runtime target
[ Apple Silicon / MLX ▼ ]

Output
[ .pt source + .npz runtime weights ]
```

#### Model Test Screen

Add device benchmark:

```text
Local benchmark
Device: Apple M4 Pro
Runtime: YOLO26 MLX
FPS: 105
Peak memory: 820 MB
```

### 22.16 Implementation Milestones

#### Milestone 1: Runtime Adapter

* Add `Yolo26MlxDetector` adapter.
* Load `.npz` model.
* Run `predict()` on image/frame.
* Normalize boxes into SoPilot `Detection` objects.

#### Milestone 2: Package Install Conversion

* Download `.pt` artifact.
* Convert to `.npz`.
* Verify checksum and sample inference.
* Save install manifest.

#### Milestone 3: Video Analysis

* Connect frame sampler to YOLO26 MLX adapter.
* Run sampled frame detection.
* Emit scene events.
* Feed rule engine.

#### Milestone 4: Tracking

* Add `model.track()` path.
* Persist track IDs.
* Use track continuity in rules.

#### Milestone 5: Creator Mode

* Export YOLO-format labels.
* Fine-tune model.
* Show training/testing metrics.
* Package `.pt` + `.npz` artifacts.

#### Milestone 6: Segmentation

* Add `task="segment"` support.
* Normalize masks.
* Add mask-overlap rule type.

### 22.17 Risks and Mitigations

| Risk                                         | Impact                          | Mitigation                                                          |
| -------------------------------------------- | ------------------------------- | ------------------------------------------------------------------- |
| AGPL license constraints                     | May affect commercial packaging | Review license before bundling or distributing modified runtime     |
| Model conversion latency during install      | Slow first-run setup            | Convert during package install, never during live run               |
| Creator training too heavy on lower-end Macs | Poor UX                         | Start with prebuilt models or remote/offline training option        |
| Critical tags have low recall                | False failures or unsafe passes | Add model acceptance gates and uncertainty fallback                 |
| Segmentation adds complexity                 | Slower MVP                      | Keep segmentation post-MVP unless required by rule geometry         |
| Tracking ID switches                         | Incorrect temporal rules        | Treat low-confidence tracks as uncertain and use local VLM fallback |

### 22.18 Acceptance Criteria

YOLO26 MLX integration is MVP-ready when:

1. A SOUP package can declare `provider: yolo26_mlx`.
2. The Mac runtime can load a converted `.npz` model.
3. The app can run detection on sampled video frames.
4. Detections are mapped to SOUP tags.
5. Scene events are generated from detections.
6. The local rule engine can evaluate rules using YOLO26 MLX evidence.
7. The result report shows `YOLO26 MLX: local` in the decision trace.
8. Package install can verify model availability and show setup status.
9. Creator Mode can display model testing metrics.
10. The system can fall back to uncertain status instead of making unsupported decisions.

---

## 23. Technical Assumptions

1. YOLO model is package-specific and can be downloaded from a model host such as Cloudflare R2.
2. `.pt` is the MVP detector format.
3. Local open VLM can run through local runtime such as Ollama or similar local inference stack.
4. Mobile app can either run lightweight local tasks or connect to a local Mac runtime for heavier analysis.
5. The Mac/local runtime is preferred for heavier model execution.
6. Creator training may be local or remote in future, but MVP can simulate or simplify training if needed.
7. Final rule engine runs locally.
8. Cloud VLM provider is configurable but optional.

---

## 23. Risks and Mitigations

### 23.1 Risk: Object detection accuracy is not good enough

Mitigation:

* Use clear MVP objects.
* Provide part images from multiple angles.
* Add more labels.
* Show uncertainty instead of false confidence.
* Use local VLM for ambiguity explanation.

### 23.2 Risk: Users misunderstand cloud VLM role

Mitigation:

* Repeat “final decision local” across screens.
* Show decision trace in every report.
* Use explicit Ambiguity Gate.
* Show payload preview before cloud call.

### 23.3 Risk: BP monitor use appears like medical advice

Mitigation:

* Add safety note everywhere.
* Focus on workflow setup, not health interpretation.
* Do not interpret readings.
* Do not make clinical recommendations.

### 23.4 Risk: Creator flow is too large for hackathon

Mitigation:

* Build high-fidelity clickable prototype for Creator Mode.
* Implement only core consumer runtime path.
* Simulate training if needed.
* Use prebuilt model and sample rules.

### 23.5 Risk: Mobile device cannot run all models locally

Mitigation:

* Use Mac local runtime for heavy models.
* Mobile app acts as camera/control surface.
* Clearly show connected local runtime status.

---

## 24. MVP Implementation Phases

### Phase 1: Consumer Demo Core

* Package detail screen.
* Install/configure mode screen.
* Start SOP check.
* Video upload/record.
* Local analysis progress.
* Result summary.
* Evidence review.

### Phase 2: Guarded Hybrid Demo

* Ambiguity detection.
* Ambiguity Gate.
* Redaction preview.
* Cloud advisory summary.
* Local final evaluation trace.

### Phase 3: Creator Prototype

* Creator dashboard.
* New package flow.
* Training data capture.
* Frame extraction.
* Labeling UI.
* Rule Studio UI.
* Package/export screen.

### Phase 4: Store and Reporting Polish

* SOUP Store list.
* Search/categories.
* Runs list.
* Report export mock.
* Settings/privacy screen.

---

## 25. Hackathon Demo Script

1. Open SoPilot.
2. Show launch screen explaining local-first SOP video checking.
3. Open SOUP Store.
4. Select Blood Pressure Monitor SOP Checker.
5. Show package detail and decision pipeline.
6. Install package in All Local mode.
7. Start SOP check.
8. Record or upload BP monitor workflow video.
9. Show local analysis progress:

   * Frame sampler.
   * YOLO / tracker.
   * Local open VLM.
   * Local rule engine.
10. Show result:

* Score 86%.
* Needs Review.
* Cuff above elbow uncertain.
* Start pressed too early.

11. Ask SoPilot: “Can I repeat step 4?”
12. Show evidence review.
13. Switch to Guarded Hybrid demo.
14. Show ambiguity gate for cuff above elbow.
15. Show redaction/minimization preview.
16. Show cloud VLM advisory summary.
17. Show local final rule evaluation.
18. Open Creator Mode.
19. Show how a creator builds a SOUP package.
20. End with pitch:

> SoPilot turns any physical SOP into an installable, local-first AI package. The VLM helps interpret ambiguity, but the rules and final decision stay local.

---

## 26. Open Questions

1. Should the first MVP assume mobile-only runtime, Mac-connected runtime, or both?
2. Should Creator Mode training be real for the hackathon or simulated with prebuilt model artifacts?
3. Should SOUP packages be stored as JSON, YAML, or both?
4. Should `.soup` be a single file or a zipped package containing rules, metadata, prompts, and model references?
5. Should cloud VLM be disabled by default for all health-related packages?
6. Should all cloud VLM usage require explicit confirmation every time, or can users create a trusted policy?
7. Should evidence clips store actual video snippets or only local pointers to timestamps?
8. Should users be able to share reports without sharing evidence clips?
9. Should creators be verified before publishing healthcare-related packages?
10. What is the minimum acceptable detector quality before a package can be published?

---

## 27. Final MVP Definition

The MVP is successful if a user can:

1. Install a Blood Pressure Monitor SOUP package.
2. Choose All Local mode.
3. Record or upload a workflow video.
4. See local analysis progress.
5. Receive a step-level result.
6. Review visual evidence for failed or uncertain steps.
7. Ask a follow-up question grounded in local rules.
8. Optionally approve a redacted cloud VLM advisory summary for ambiguity.
9. See that final decision remains local.
10. Export or view a report with a privacy/decision trace.

The creator-side MVP is successful if a creator can:

1. Create a SOUP package shell.
2. Upload or capture training videos.
3. Extract frames.
4. Label object tags.
5. View model training/testing screens.
6. Author a rule in AI Rule Studio.
7. Test the rule on sample video.
8. Export or publish the package.
