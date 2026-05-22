Design a polished responsive app UI for “SoPilot,” a local-first AI app that checks SOP workflow videos.

Product summary:
SoPilot helps users run and create SOUP packages. SOP means Standard Operating Procedure. SOUP means Standard Operating Understanding Package. A SOUP package contains a YOLO model link, SOP rules, tags, rule-engine logic, optional VLM settings, and privacy policies. Users can install a SOUP package, record or upload a workflow video, see YOLO bounding boxes, view SOP checklist overlays, and get local compliance results.

Design style:
Use Apple-inspired design: clean, minimal, elegant, trustworthy, high contrast, soft rounded cards, subtle glass/blur surfaces, SF-like typography, generous spacing, quiet gradients, refined icons, and professional healthcare/industrial workflow aesthetics. Avoid cartoon style. The UI should feel like a premium Apple productivity + AI assistant app.

Responsive targets:
Generate responsive layouts for:
1. iPhone portrait
2. iPad tablet layout
3. MacBook desktop layout

For iPhone:
Use bottom tab navigation: Home, Store, Create, Runs, Me.
Use single-column cards and full-screen flows.

For iPad:
Use split layout with a left sidebar and large content panel.
Use two-column cards where appropriate.

For MacBook:
Use desktop sidebar navigation, large dashboard panels, wider data tables, video preview panel, and right-side inspector/chat panel.

Core design concept:
SoPilot is not a cloud VLM wrapper. It is a local SOP decision engine.

Decision flow:
SOP Script / Rules stay local on Mac.
Video or camera input goes to Frame Sampler.
Frame Sampler feeds YOLO / Tracker.
YOLO / Tracker feeds the local Rule Engine.
YOLO / Tracker can also feed a Local Open VLM to create Scene Events.
The Rule Engine produces a Local Decision and Compliance Result.
If confidence is high, the workflow is done locally.
If confidence is low or ambiguous, the app performs Redaction / Minimization.
Only then can an Optional Cloud VLM Summary be used.
The final decision always returns to Local Final Rule Evaluation.

Privacy language to show in UI:
- SOP rules stay local
- YOLO model stays local
- Raw video stays local
- Final decision is local
- Cloud VLM is optional
- Cloud VLM is used only for ambiguous cases
- Cloud VLM receives minimized/redacted context only
- Cloud VLM summary is advisory, not the final decision

Runtime modes:
1. All Local
   YOLO, Tracker, SOP rules, local open VLM, and final rule evaluation stay local.
2. Guarded Hybrid
   Runs locally first. If the result is ambiguous, SoPilot minimizes/redacts context, optionally asks a cloud VLM for a summary, then returns to local rule evaluation.

Main user roles:
1. Consumer
   Installs SOUP packages and runs SOP validation.
2. Creator
   Creates SOUP packages by collecting training videos, labeling tags, training YOLO, authoring rules, testing rules, and publishing the package.

Key screens to design:

Screen 1: Launch / Role Selection
Title: SoPilot
Subtitle: Local SOP Video Checker
Show definition:
SOP = Standard Operating Procedure
SOUP = Standard Operating Understanding Package
Primary buttons:
- Use a SOUP Package
- Create a SOUP Package
Show local-first privacy bullets.

Screen 2: Home Dashboard
Show installed SOUP packages:
- Blood Pressure Monitor SOP
- HVAC Compressor Setup
Each card shows runtime mode, local decision status, and Start Check button.
Show recent runs with status, score, and whether cloud VLM was used.

Screen 3: SOUP Store
Search bar.
Categories: Healthcare, HVAC, Factory, Safety, Field Service, Lab.
Featured package cards with icon, description, mode, model size, install count.
Package example: Blood Pressure Monitor SOP Checker.

Screen 4: Package Detail
Show icon, demo preview, description, checklist preview, version, model type, model host, supported modes.
Show Decision Pipeline:
1. Frame Sampler
2. YOLO / Tracker
3. Local Open VLM → Scene Events
4. Local Rule Engine
5. Local Compliance Result
Show Optional Cloud Path with redaction/minimization.
Buttons:
- Install SOUP
- Try Sample Video
- View Rules

Screen 5: Install and Configure Privacy Mode
Show two large selectable cards:
- All Local
- Guarded Hybrid
Add checkboxes:
- Ask before cloud VLM use
- Send minimized summary only
- Redact faces/background
- Keep SOP script local
- Keep YOLO model local
Button: Install

Screen 6: Start SOP Check
Package: Blood Pressure Monitor SOP
Runtime mode: All Local
Input cards:
- Record new workflow video
- Upload existing video
Checklist preview:
1. Monitor is visible
2. Connector is attached
3. Cuff is on upper arm
4. Cuff is above elbow bend
5. Start is pressed after setup
Button: Start Camera

Screen 7: Live Camera Validation Overlay
Show live video area with YOLO bounding boxes:
- cuff
- upper_arm
- grey_connector
- monitor
Overlay a floating SOP checklist:
✓ Monitor visible
✓ Connector attached
⏳ Cuff on upper arm
○ Cuff above elbow
○ Press start button
Show runtime status:
Frame Sampler active
YOLO / Tracker active
Local Open VLM standby
Rule Engine checking
Buttons:
Pause
Finish & Analyze

Screen 8: Offline Validation Progress
Show step-by-step progress:
1. Frame Sampler
2. YOLO / Tracker
3. Local Open VLM
4. Rule Engine
5. Local Decision
Show animated progress bars and current detections.
Show privacy status:
Raw video stayed local
SOP rules stayed local
YOLO model stayed local
Final decision will be local

Screen 9: Ambiguity Gate
Only shown in Guarded Hybrid mode.
Title: Ambiguous Step Detected
Example:
Step 4: Cuff above elbow bend
Local confidence: 0.42
Explain why local system is unsure.
Show cloud request policy:
Raw video will not be uploaded
SOP script will not be uploaded
YOLO model will not be uploaded
Only minimized/redacted context will be sent
Buttons:
- Use Cloud VLM Once
- Skip and Mark Needs Review

Screen 10: Redaction / Minimization Preview
Show cropped/redacted preview:
Face blurred
Background masked
Only cuff + arm region shown
Show text summary to send:
Detected objects: cuff, upper_arm, elbow_bend.
Question: Is cuff above elbow?
No SOP script included.
Buttons:
- Send Minimized Context
- Cancel

Screen 11: Cloud VLM Summary Returned
Show cloud VLM summary as advisory.
Important text:
This is not the final decision.
SoPilot will return this summary to the local rule engine for final evaluation.
Button:
Run Local Final Evaluation

Screen 12: SOP Result with Chat
Show compliance score, status, and decision path:
Frame Sampler: local
YOLO / Tracker: local
Local Open VLM: used
Cloud VLM: not used or used once
Final Rule Evaluation: local
Show step results:
✓ Monitor visible
✓ Connector attached
✓ Cuff on upper arm
⚠ Cuff above elbow uncertain
✕ Start pressed too early
Add chat text field:
“Ask SoPilot…”
Suggested chips:
- Can I repeat only failed step?
- Why did step 4 fail?
- Show evidence clip
- Was cloud VLM used?
Buttons:
Review Evidence
Export Report
Run Again

Screen 13: Evidence Review with Chat
Show selected step:
Step 4: Cuff above elbow
Status: Uncertain
Show evidence clip/frame with YOLO boxes.
Show local rule explanation.
Show local open VLM scene events.
Show cloud VLM usage status.
Add chat:
“Can I repeat this step only?”
Recovery action buttons:
- Recheck Step 4
- Mark as False Positive
- Restart from Step 3
- Update Rule Suggestion

Screen 14: Creator Dashboard
Cards for creator projects:
- BP Monitor SOP
- HVAC Setup SOP
Show status: labeling, training, testing rules, packaged, published.
Button: New SOUP Package

Screen 15: New SOUP Package
Fields:
Package icon upload
Package name
Category
What should this package check?
Target users
Safety note
Decision policy:
SOP rules stay local
Final rule evaluation is local
Cloud VLM optional only for ambiguity
Button: Create Project

Screen 16: Capture Training Data
Step 1: Record workflow videos
- Record Correct Video
- Record Wrong Video
Step 2: Upload part images from different angles
Example parts:
- blood_pressure_monitor
- cuff
- grey_connector
Uploaded videos list.
Button: Extract Frames

Screen 17: Extract Frames
Frame sampler settings:
Every 1.0 seconds
Add high-motion frames
Add action-transition frames
Preview extracted frames.
Button: Continue to Tagging

Screen 18: Label Tags
Replace “classes” with “tags.”
Show frame image with bounding box.
Current tag dropdown.
Tags:
monitor, cuff, upper_arm, elbow, connector, button
Manage tags:
Add, Edit, Delete
Tools:
Draw Box
Delete Box
Auto Label Similar Frames
Buttons:
Prev, Save, Next

Screen 19: Train YOLO Model
Dataset summary:
Videos, frames, labels, tags.
Model selection:
YOLO small
Output format:
.pt
Runtime target:
Mac local runtime / MLX
Training progress:
Epoch, loss, mAP, progress bar.
Button: View Sample Detections

Screen 20: Test YOLO Model
Show metrics:
Recall Rate
False Detection Rate
Precision
mAP
Show tag-level performance table:
cuff, connector, elbow_bend
Review problem images:
Missed Detections
False Boxes
Low Confidence
Wrong Tag
Runtime impact note:
Low recall tags may trigger Local VLM or Guarded Hybrid ambiguity checks.
Buttons:
Open Review Queue
Add More Labels
Accept Model

Screen 21: AI Rule Studio
Use a Lovable-style AI design interface.
Top: horizontal frame strip from video.
Middle: selected frame with YOLO boxes.
Bottom: card area with two tabs:
- Chat
- Parameters
Chat card:
User types natural language SOP rule.
AI generates a local rule.
Example:
“Cuff should be above elbow bend and overlap the upper arm before the start button is pressed.”
Parameter card:
type: orientation
source tag: cuff
target tag: elbow_bend
direction: above
angle tolerance: 60°
min confidence: 0.50
local VLM assistance: optional
cloud fallback: only if ambiguous
Buttons:
Generate Rule
Try on Video
Save Rule

Screen 22: Try Run Rules
Select test videos:
correct_01.mov
wrong_start_early.mov
wrong_cuff_low.mov
Show runtime path:
Frame Sampler
YOLO / Tracker
Local Open VLM
Local Rule Engine
Cloud VLM only if ambiguous
Show result checklist.
Show expected vs actual.
Show Cloud VLM used: Yes/No
Buttons:
Accept
Edit Failed Rule

Screen 23: Package SOUP
Package summary:
Name
Version
Model
Model host: Cloudflare R2
Rules
Test videos
Decision policy:
SOP rules local
YOLO / Tracker local
Local Open VLM supported
Final rule evaluation local
Cloud VLM fallback optional
Cloud only after redaction
Validation:
Schema valid
Model link works
Sample tests passed
Safety note included
Buttons:
Export .soup JSON
Publish to Store

Screen 24: Runs / Reports
List analysis runs.
Each row/card:
Package name
Score
Status
Decision: local
Cloud VLM: not used / used once
Open button.

Screen 25: Report Detail
Show run summary, decision trace, failed steps, uncertain steps, evidence clips, privacy log.
Buttons:
Export PDF
Share Summary
Delete Run

Screen 26: Settings / Privacy
Default runtime mode:
All Local / Guarded Hybrid
Local Open VLM:
LLaVA via Ollama
Remote Cloud VLM:
GPT-4o-mini or similar
Cloud fallback trigger:
Low confidence
Ambiguous local VLM summary
User asks for clarification
Redaction/minimization options:
Do not upload raw video
Do not upload SOP scripts
Do not upload YOLO model
Send detection summary only
Redact faces/background
Require confirmation first
Final decision policy:
Always local rule evaluation
Cloud VLM summary is advisory

Animation and micro-interaction requirements:
Add subtle motion to guide the next action:
- Pulsing glow around primary CTA buttons
- Animated checkmarks when SOP steps pass
- Step items slide from gray to green when completed
- Yellow shimmer for uncertain steps
- Red shake or alert pulse for failed steps
- YOLO boxes fade in with a soft scan-line animation
- Frame Sampler shows flowing frame thumbnails
- Rule Engine shows a local decision pipeline animation
- Guarded Hybrid ambiguity gate gently expands when confidence is low
- Redaction preview animates blur/mask over the image
- Cloud VLM summary card slides in as advisory, then returns to local rule evaluation
- Creator flow progress uses a horizontal stepper with active step glow
- AI Rule Studio chat card should animate AI-generated rule cards appearing
- Parameter sliders should update live rule preview

Visual hierarchy:
Use blue/indigo for primary actions, green for passed steps, amber for uncertain/needs review, red for failed, gray for not started. Keep the overall palette Apple-like and restrained, not overly colorful.

Important UX copy:
Use “All Local” and “Guarded Hybrid” consistently.
Use “Final decision stays local.”
Use “Cloud VLM summary is advisory.”
Use “SOUP package” consistently.
Use “tags” instead of “classes” in creator labeling UI.

Generate the UI as a complete responsive app design with iPhone, iPad, and MacBook variants.

# Bring your key settings
# Google Stitch Prompt — SoPilot Mobile App UI

## Goal

Design a polished, responsive mobile app UI for **SoPilot**, a local-first AI app that checks SOP workflow videos.

SoPilot helps users run and create **SOUP packages**.

- **SOP** = Standard Operating Procedure
- **SOUP** = Standard Operating Understanding Package

A SOUP package contains:
- YOLO model link
- SOP rules
- tags
- rule-engine logic
- optional VLM settings
- privacy policies
- package metadata
- model/package asset links

Users can install a SOUP package, record or upload a workflow video, see YOLO bounding boxes, view SOP checklist overlays, get local compliance results, and ask a chat assistant what to do next.

The UI should be generated for:
1. iPhone portrait
2. iPad responsive layout
3. MacBook responsive layout

---

## Design Style

Use an **Apple-inspired design style**:

- clean
- minimal
- elegant
- trustworthy
- high contrast where needed
- soft rounded cards
- subtle glass/blur surfaces
- SF-like typography
- generous spacing
- quiet gradients
- refined icons
- premium productivity app feel
- professional healthcare + industrial workflow aesthetic

Avoid:
- cartoon style
- cluttered dashboards
- overly colorful UI
- heavy cyberpunk visuals
- generic SaaS templates

The app should feel like a premium Apple productivity + AI assistant app for industrial, healthcare, HVAC, and field-service SOP validation.

---

## Responsive Layout Rules

### iPhone

Use:
- bottom tab navigation
- single-column cards
- full-screen step-by-step flows
- large primary buttons
- readable checklists
- camera/video-first runtime screen

Bottom tabs:

```text
Home | Store | Create | Runs | Me
```

### iPad

Use:
- split layout
- left sidebar
- large content panel
- optional right inspector panel for chat/rule parameters
- two-column card layout where appropriate

### MacBook

Use:
- desktop sidebar navigation
- large dashboard panels
- wider data tables
- video preview panel
- right-side inspector/chat panel
- package/rule editor optimized for wide screen

---

## Core Product Concept

SoPilot is **not a cloud VLM wrapper**.

It is a **local SOP decision engine**.

Cloud VLM is only an optional assistant for ambiguous cases.

The final decision always happens locally.

---

## Decision Pipeline

Represent this clearly in the UI:

```text
SOP Script / Rules
Local on Mac
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

---

## Privacy Language

Use these phrases consistently in the UI:

- SOP rules stay local
- YOLO model stays local
- Raw video stays local
- Final decision is local
- Cloud VLM is optional
- Cloud VLM is used only for ambiguous cases
- Cloud VLM receives minimized/redacted context only
- Cloud VLM summary is advisory, not the final decision
- Final rule evaluation always happens locally

---

## Runtime Modes

### All Local

YOLO, Tracker, SOP rules, local open VLM, and final rule evaluation stay local.

### Guarded Hybrid

SoPilot runs locally first. If a step is ambiguous or low-confidence, the app minimizes/redacts context, optionally asks a cloud VLM for a summary, then returns to local rule evaluation.

The cloud VLM summary is advisory only.

---

## Main User Roles

### Consumer

Installs SOUP packages and runs SOP validation.

### Creator

Creates SOUP packages by:
- collecting training videos
- uploading part images
- extracting frames
- labeling tags
- training YOLO
- authoring rules
- testing rules
- exporting/publishing the package

---

# Screens to Generate

## Screen 1 — Launch / Role Selection

Title:

```text
SoPilot
```

Subtitle:

```text
Local SOP Video Checker
```

Show definitions:

```text
SOP = Standard Operating Procedure
SOUP = Standard Operating Understanding Package
```

Primary buttons:
- Use a SOUP Package
- Create a SOUP Package

Show local-first privacy bullets:
- Rules stay local
- YOLO model stays local
- Final decision stays local
- Cloud VLM only for ambiguity

---

## Screen 2 — Home Dashboard

Show installed SOUP packages:

### Package Card 1

```text
Blood Pressure Monitor SOP
Mode: All Local
Runtime: YOLO + Local Rules
Final decision: Local
Button: Start Check
```

### Package Card 2

```text
HVAC Compressor Setup
Mode: Guarded Hybrid
Cloud used only if ambiguous
Final decision: Local
Button: Start Check
```

Show recent runs:

```text
BP Monitor Check
86% · Needs Review
Cloud VLM: Not used
Button: View Report
```

Show quick actions:

```text
Install SOUP
Create SOUP
```

---

## Screen 3 — SOUP Store

Search bar:

```text
Search SOP packages
```

Categories:
- Healthcare
- HVAC
- Factory
- Safety
- Field Service
- Lab

Featured package cards:
- package icon
- title
- short description
- runtime mode
- model size
- install count
- View button

Example card:

```text
Blood Pressure Monitor SOP Checker
Checks cuff, connector, screen
Local / Guarded Hybrid
Final decision always local
View
```

---

## Screen 4 — Package Detail

Package:

```text
Blood Pressure Monitor SOP Checker
```

Show:
- icon
- demo video preview
- description
- checklist preview
- version
- model type
- model host
- supported modes

Checklist preview:

```text
✓ monitor visible
✓ cuff on upper arm
✓ grey connector attached
✓ start after cuff placement
```

Decision Pipeline section:

```text
1. Frame Sampler
2. YOLO / Tracker
3. Local Open VLM → Scene Events
4. Local Rule Engine
5. Local Compliance Result
```

Optional Cloud Path section:

```text
Used only if local result is low-confidence or ambiguous.
Before cloud:
✓ Redaction
✓ Minimization
✓ No SOP script upload
✓ No YOLO model upload
```

Safety note:

```text
For workflow assistance only. Not medical diagnosis.
```

Buttons:
- Install SOUP
- Try Sample Video
- View Rules

---

## Screen 5 — Install and Configure Privacy Mode

Title:

```text
Install SOUP Package
```

Show model binary:

```text
bp-monitor-yolo-v1.pt
Host: Cloudflare R2
```

Two large selectable cards:

### All Local

```text
YOLO, tracker, SOP rules, local open VLM, and final rule evaluation stay local.
```

### Guarded Hybrid

```text
Runs locally first. Cloud VLM is used only for ambiguous cases after redaction. Final rule decision remains local.
```

Checkboxes:
- Ask before cloud VLM use
- Send minimized summary only
- Redact faces/background
- Keep SOP script local
- Keep YOLO model local

Button:

```text
Install
```

---

## Screen 6 — Start SOP Check

Package:

```text
Blood Pressure Monitor SOP
```

Runtime mode:

```text
All Local
```

Local Decision Stack:
- SOP script / rules
- YOLO model
- Tracker
- Local Open VLM
- Rule engine

Input cards:
- Record new workflow video
- Upload existing video

Checklist preview:
1. Monitor is visible
2. Connector is attached
3. Cuff is on upper arm
4. Cuff is above elbow bend
5. Start is pressed after setup

Button:

```text
Start Camera
```

---

## Screen 7 — Live Camera Validation Overlay

Show a camera/video area with YOLO bounding boxes:
- cuff
- upper_arm
- grey_connector
- monitor

Overlay a floating SOP checklist:
- ✓ Monitor visible
- ✓ Connector attached
- ⏳ Cuff on upper arm
- ○ Cuff above elbow
- ○ Press start button

Show runtime status:
- Frame Sampler: active
- YOLO / Tracker: active
- Local Open VLM: standby
- Rule Engine: checking

Buttons:
- Pause
- Finish & Analyze

---

## Screen 8 — Offline Validation Progress

Show step-by-step progress:

1. Frame Sampler
2. YOLO / Tracker
3. Local Open VLM
4. Rule Engine
5. Local Decision

Use animated progress bars.

Show current detections:
- monitor
- cuff
- upper_arm
- grey_connector

Show privacy status:
- Raw video stayed local
- SOP rules stayed local
- YOLO model stayed local
- Final decision will be local

---

## Screen 9 — Ambiguity Gate

Only shown in Guarded Hybrid mode.

Title:

```text
Ambiguous Step Detected
```

Example:

```text
Step 4: Cuff above elbow bend
Local confidence: 0.42
```

Explain:

```text
Local system is unsure because:
- elbow bend is partially hidden
- cuff box overlaps arm, but angle relation is uncertain
```

Show cloud request policy:
- Raw video will not be uploaded
- SOP script will not be uploaded
- YOLO model will not be uploaded
- Only minimized/redacted context will be sent

Context to send:
- Cropped cuff/arm frame
- Detection summary
- Step question
- Full frame disabled
- Full video disabled

Buttons:
- Use Cloud VLM Once
- Skip and Mark Needs Review

---

## Screen 10 — Redaction / Minimization Preview

Show cropped/redacted preview:
- face blurred
- background masked
- only cuff + arm region shown

Show text summary to send:

```text
Detected objects: cuff, upper_arm, elbow_bend.
Question: Is cuff above elbow?
No SOP script included.
```

Buttons:
- Send Minimized Context
- Cancel

---

## Screen 11 — Cloud VLM Summary Returned

Show cloud VLM summary as advisory.

Example:

```text
The cuff appears to be around the upper arm, but the lower edge may be too close to the elbow bend.
```

Important text:

```text
This is not the final decision.
SoPilot will return this summary to the local rule engine for final evaluation.
```

Button:
- Run Local Final Evaluation

---

## Screen 12 — SOP Result with Chat

Show compliance score:

```text
86%
Needs Review
```

Show decision path:
- Frame Sampler: local
- YOLO / Tracker: local
- Local Open VLM: used
- Cloud VLM: not used / used once
- Final Rule Evaluation: local

Show step results:
- ✓ Monitor visible
- ✓ Connector attached
- ✓ Cuff on upper arm
- ⚠ Cuff above elbow uncertain
- ✕ Start pressed too early

Add chat input field:

```text
Ask SoPilot…
```

Suggested chips:
- Can I repeat only failed step?
- Why did step 4 fail?
- Show evidence clip
- Was cloud VLM used?

Buttons:
- Review Evidence
- Export Report
- Run Again

---

## Screen 13 — Evidence Review with Chat

Show selected step:

```text
Step 4: Cuff above elbow
Status: Uncertain
```

Show evidence clip/frame with YOLO boxes.

Show:
- local rule explanation
- local open VLM scene events
- cloud VLM usage status

Chat example:

```text
Can I repeat this step only?
```

Recovery action buttons:
- Recheck Step 4
- Mark as False Positive
- Restart from Step 3
- Update Rule Suggestion

---

## Screen 14 — Creator Dashboard

Cards for creator projects:

```text
BP Monitor SOP
Status: rule testing
Model: trained
Runtime: local-first
Cloud fallback: optional
Continue
```

```text
HVAC Setup SOP
Status: labeling frames
Model: not trained
Continue
```

Button:

```text
New SOUP Package
```

---

## Screen 15 — New SOUP Package

Fields:
- Package icon upload
- Package name
- Category
- What should this package check?
- Target users
- Safety note

Decision policy display:
- SOP rules stay local
- Final rule evaluation is local
- Cloud VLM optional only for ambiguity

Button:

```text
Create Project
```

---

## Screen 16 — Capture Training Data

Step 1: Record workflow videos:
- Record Correct Video
- Record Wrong Video

Step 2: Upload part images from different angles.

Example parts:
- blood_pressure_monitor
- cuff
- grey_connector

Uploaded videos list:
- correct_01.mov
- wrong_start_early.mov

Button:
- Extract Frames

---

## Screen 17 — Extract Frames

Frame Sampler settings:
- Every 1.0 seconds
- Add high-motion frames
- Add action-transition frames

Preview extracted frames.

Buttons:
- Start Extraction
- Continue to Tagging

---

## Screen 18 — Label Tags

Use **Tags**, not “classes.”

Show:
- frame image with bounding box
- current tag dropdown
- tag chips

Tags:
- monitor
- cuff
- upper_arm
- elbow
- connector
- button

Manage tags:
- Add
- Edit
- Delete

Tools:
- Draw Box
- Delete Box
- Auto Label Similar Frames

Buttons:
- Prev
- Save
- Next

---

## Screen 19 — Train YOLO Model

Dataset summary:
- Videos
- Frames
- Labels
- Tags

Model selection:
- YOLO small

Output format:
- .pt

Runtime target:
- Mac local runtime / MLX

Training progress:
- Epoch
- Loss
- mAP
- Progress bar

Button:
- View Sample Detections

---

## Screen 20 — Test YOLO Model

Show metrics:
- Recall Rate
- False Detection Rate
- Precision
- mAP

Show tag-level performance table:
- cuff
- connector
- elbow_bend

Review problem images:
- Missed Detections
- False Boxes
- Low Confidence
- Wrong Tag

Runtime impact note:

```text
Low recall tags may trigger Local VLM or Guarded Hybrid ambiguity checks later.
```

Buttons:
- Open Review Queue
- Add More Labels
- Accept Model

---

## Screen 21 — AI Rule Studio

Use a Lovable-style AI design interface.

Top:
- horizontal frame strip from video

Middle:
- selected frame with YOLO boxes

Bottom:
- card area with two tabs:
  - Chat
  - Parameters

Chat card:
User types natural language SOP rule.
AI generates a local rule.

Example generated rule:

```text
Cuff should be above elbow bend and overlap the upper arm before the start button is pressed.
```

Parameter card:
- type: orientation
- source tag: cuff
- target tag: elbow_bend
- direction: above
- angle tolerance: 60°
- min confidence: 0.50
- local VLM assistance: optional
- cloud fallback: only if ambiguous

Buttons:
- Generate Rule
- Try on Video
- Save Rule

---

## Screen 22 — Try Run Rules

Select test videos:
- correct_01.mov
- wrong_start_early.mov
- wrong_cuff_low.mov

Show runtime path:
- Frame Sampler
- YOLO / Tracker
- Local Open VLM
- Local Rule Engine
- Cloud VLM only if ambiguous

Show result checklist.

Show:
- Expected: Pass / Fail
- Actual: Pass / Fail
- Cloud VLM used: Yes / No

Buttons:
- Accept
- Edit Failed Rule

---

## Screen 23 — Package SOUP

Package summary:
- Name
- Version
- Model
- Model host: Cloudflare R2
- Rules
- Test videos

Decision policy:
- SOP rules local
- YOLO / Tracker local
- Local Open VLM supported
- Final rule evaluation local
- Cloud VLM fallback optional
- Cloud only after redaction

Validation:
- Schema valid
- Model link works
- Sample tests passed
- Safety note included

Buttons:
- Export .soup JSON
- Publish to Store

---

## Screen 24 — Runs / Reports

List analysis runs.

Each row/card:
- Package name
- Score
- Status
- Decision: local
- Cloud VLM: not used / used once
- Open button

---

## Screen 25 — Report Detail

Show:
- run summary
- decision trace
- failed steps
- uncertain steps
- evidence clips
- privacy log

Privacy log:
- raw video stayed local
- SOP script stayed local
- YOLO model stayed local
- final decision local

Buttons:
- Export PDF
- Share Summary
- Delete Run

---

## Screen 26 — Settings / Privacy

Default runtime mode:
- All Local
- Guarded Hybrid

Local Open VLM:
- LLaVA via Ollama
- Status: installed
- Role: scene events + explanation

Remote Cloud VLM:
- Gemini
- GPT-4o-mini
- Used only in Guarded Hybrid mode

Cloud fallback trigger:
- Low confidence
- Ambiguous local VLM summary
- User asks for clarification
- Always use cloud VLM disabled by default

Redaction/minimization options:
- Do not upload raw video
- Do not upload SOP scripts
- Do not upload YOLO model
- Send detection summary only
- Redact faces/background
- Require confirmation first

Final decision policy:
- Always local rule evaluation
- Cloud VLM summary is advisory

---

## Screen 27 — Settings / API Keys

Create a separate API Keys section.

Allow users to paste:
1. Gemini API Key
2. Cloudflare API Key
3. Cloudflare Account ID
4. Cloudflare R2 Bucket Name
5. Cloudflare Public Model Base URL

Important UI copy:

```text
API keys are optional.
They are only used for Guarded Hybrid Mode or cloud-hosted package/model workflows.
If you do not provide keys, you can still use all local YOLO features, local SOP validation, local rule engine, offline video analysis, and local reports.
```

Gemini API Key section:

```text
Used only when Guarded Hybrid needs optional cloud VLM help for ambiguous steps after redaction/minimization.
The final decision still happens locally.
```

Cloudflare API Key section:

```text
Used only if creators want to upload or manage SOUP package assets such as YOLO model binaries, icons, demo videos, preview images, or sample reports in their Cloudflare bucket.
Not needed to run local YOLO.
```

Design requirements:
- Mask API keys by default
- Add Test Key buttons
- Add Delete Saved Keys button
- Add “Why is this needed?” expandable info cards
- Add local-first privacy assurance
- Store key status visually as configured / not configured / invalid

Empty state copy:

```text
No API keys configured.

You can still use SoPilot in All Local Mode:
✓ YOLO detection
✓ Tracker
✓ SOUP Rule Engine
✓ Local SOP validation
✓ Offline video analysis
✓ Local reports
```

---

# Animation and Micro-Interaction Requirements

Add subtle motion to guide the next action.

Use:

- pulsing glow around primary CTA buttons
- animated checkmarks when SOP steps pass
- step items slide from gray to green when completed
- yellow shimmer for uncertain steps
- red shake or alert pulse for failed steps
- YOLO boxes fade in with a soft scan-line animation
- frame sampler shows flowing frame thumbnails
- rule engine shows a local decision pipeline animation
- Guarded Hybrid ambiguity gate gently expands when confidence is low
- redaction preview animates blur/mask over the image
- cloud VLM summary card slides in as advisory, then returns to local rule evaluation
- creator flow progress uses a horizontal stepper with active step glow
- AI Rule Studio chat card animates AI-generated rule cards appearing
- parameter sliders update live rule preview
- API key field gently confirms “configured” after successful test
- privacy badges animate when each protection is active

---

# Visual Semantics

Use colors carefully:

- Blue / indigo: primary actions
- Green: passed steps
- Amber: uncertain / needs review
- Red: failed
- Gray: not started
- Purple accent: AI assistance
- Teal accent: local privacy / secure processing

Keep palette Apple-like and restrained.

---

# Important UX Copy

Use these exact terms consistently:

- All Local
- Guarded Hybrid
- Final decision stays local
- Cloud VLM summary is advisory
- SOUP package
- Tags, not classes
- Local Open VLM
- YOLO / Tracker
- Rule Engine
- Redaction / Minimization
- Standard Operating Understanding Package

---

# Output Requirement

Generate a complete responsive app design with:

1. iPhone portrait screens
2. iPad responsive screens
3. MacBook responsive screens

Make the UI feel like a professional Apple-style productivity app for AI-powered SOP workflow validation.
