Below is an English summary of the SoPilot Neon/PostgreSQL database schema. The schema supports four core product epics: creator-side YOLO workflow training, creator-side rule authoring and `.soup` packaging, consumer-side package installation, and consumer-side SOP video validation. 

## Database Schema Summary

The SoPilot database is designed around a hybrid storage model:

**Neon/PostgreSQL** stores structured application data, JSONB rules, package metadata, validation results, chat history, reports, and decision traces.

**Cloudflare R2** stores large binary files such as videos, extracted frames, YOLO model files, evidence clips, images, and PDF reports.

The `.soup` package itself is stored as JSONB in PostgreSQL through the `soup_versions.soup_json` field, while it can also be exported as a `.soup.json` file.

API keys should not be stored in plaintext. The schema stores only encrypted references such as `gemini_key_ref` and `cloudflare_key_ref`.

---

## 1. Core User and Settings Tables

### `users`

Stores basic user identity and role information.

Main fields include:

* `id`
* `email`
* `display_name`
* `avatar_url`
* `role`: `consumer`, `creator`, or `admin`
* timestamps

This table is the root entity for both creators and consumers.

### `api_key_settings`

Stores user-level runtime and integration settings.

It supports:

* Gemini API configuration
* Cloudflare / R2 configuration
* default runtime mode
* key status tracking

The schema intentionally avoids storing raw API keys. Instead, it stores key references.

---

## 2. Creator Project Tables

### `creator_projects`

Represents a creator’s SOP workflow project.

It stores:

* project name
* slug
* category
* description
* target users
* safety notes
* project status

The project lifecycle includes states such as:

* `draft`
* `collecting_data`
* `labeling`
* `training`
* `model_testing`
* `rule_authoring`
* `packaged`
* `published`

This table connects Epic E1 and Epic E2.

### `project_assets`

Stores metadata and URLs for project-related assets in R2.

Examples include:

* icons
* workflow videos
* frame images
* demo videos
* evidence clips
* cover images

---

## 3. Training Data Tables

These tables support Epic E1: Creator trains a YOLO model.

### `workflow_videos`

Stores uploaded or recorded workflow videos.

Video types include:

* `correct`
* `wrong`
* `test`
* `demo`
* `consumer_run`

It also records metadata such as duration, FPS, width, and height.

### `video_frames`

Stores extracted frames from workflow videos.

Each frame includes:

* `frame_index`
* `timestamp_sec`
* `image_uri`
* extraction method

Extraction methods include interval sampling, motion-based sampling, transition detection, manual selection, and keyframe extraction.

### `tags`

Defines object labels used for YOLO training.

Each tag maps to a YOLO class.

For example:

* tag name: `cuff`
* label: `Arm cuff`
* YOLO class: `cuff`

### `annotations`

Stores bounding box annotations on video frames.

Each annotation includes:

* frame reference
* tag reference
* bounding box coordinates
* annotation source
* confidence
* creator metadata

This table is central to preparing YOLO training data.

---

## 4. YOLO Training and Evaluation Tables

### `training_jobs`

Tracks YOLO model training jobs.

It records:

* job status
* base model
* output format
* runtime target
* epochs
* image size
* validation split
* metrics
* logs
* errors

Supported output formats include:

* `pt`
* `onnx`
* `mlx`
* `coreml`

### `model_artifacts`

Stores trained model metadata.

The actual model binary is stored in R2, while PostgreSQL stores:

* model name
* version
* model format
* runtime
* URI
* file size
* class list
* metrics

### `model_eval_runs`

Stores model evaluation results.

Metrics include:

* recall rate
* false detection rate
* precision rate
* mAP score
* per-tag metrics

### `model_eval_items`

Stores review items for model errors.

Issue types include:

* missed detection
* false detection
* wrong tag
* low confidence
* bad bounding box

This table supports human review and iterative model improvement.

---

## 5. Rule Engine Authoring Tables

These tables support Epic E2: Creator authors rules and packages `.soup`.

### `soup_conditions`

Stores geometric, VLM, or fusion-based conditions.

Condition types include:

* `inside`
* `outside`
* `overlap`
* `orientation`
* `position`
* `transform_position`
* `bridge_relation`
* `vlm_confirmation`
* `fusion`

Conditions are stored with JSONB fields such as:

* `source`
* `target`
* `reference`
* `params`

### `soup_actions`

Defines semantic actions triggered by conditions.

For example, a condition like “cuff is above elbow bend” may trigger an action like “place cuff correctly.”

Each action includes:

* action key
* label
* trigger type
* primary condition
* fallback configuration
* duration threshold
* confidence threshold

### `soup_steps`

Represents checklist steps in an SOP workflow.

Each step includes:

* step key
* step order
* label
* required actions
* optional actions
* success UI state
* failure UI state
* recovery policy

This table maps low-level detection and rule logic into user-facing SOP steps.

### `event_order_rules`

Stores ordering constraints between actions.

For MVP, this supports simple event-order validation. A future finite-state machine can be added later.

---

## 6. SOUP Package and Store Tables

These tables support Epic E2 and Epic E3.

### `soup_packages`

Represents a package visible in the SOUP Store.

It stores:

* package name
* slug
* category
* short and long descriptions
* icon
* status
* latest version
* install count
* rating information
* safety note

Package statuses include:

* `draft`
* `private`
* `published`
* `unlisted`
* `archived`

### `soup_versions`

This is one of the most important tables.

It stores versioned `.soup` package definitions, including:

* package version
* schema version
* model reference
* model URI
* model format
* `soup_json`
* supported runtime modes
* default mode
* VLM requirements
* decision policy
* privacy policy

Published `.soup` versions should be immutable. Instead of overwriting an existing version, the system should create a new version.

### `package_assets`

Stores Store-facing media assets.

Examples include:

* cover images
* preview images
* demo videos
* sample reports
* documentation

---

## 7. Consumer Installation Tables

These tables support Epic E3: Consumer installs and configures a SOUP package.

### `package_installs`

Tracks which packages a user has installed.

It stores:

* user
* package
* version
* install status
* install timestamp
* local model path
* local `.soup` path

### `consumer_runtime_configs`

Stores runtime configuration for each installed package.

It controls whether the package runs in:

* `all_local`
* `guarded_hybrid`

It also tracks privacy-related settings, such as:

* whether raw video can leave the device
* whether frames can leave the device
* whether detection summaries can leave the device
* whether SOP rules can leave the device
* whether the YOLO model can leave the device
* face redaction
* background redaction

This table is important for SoPilot’s privacy story.

---

## 8. Runtime Validation Tables

These tables support Epic E4: Consumer runs SOP video validation.

### `validation_runs`

Represents one SOP validation run.

It stores:

* user
* installed package
* package version
* input video
* input mode
* run mode
* runtime mode
* current status
* compliance score
* final result status
* whether cloud VLM was used
* whether local VLM was used
* summary
* decision trace

Validation status can move through stages such as:

* recording
* sampling frames
* detecting
* local VLM
* rule engine
* ambiguity gate
* cloud VLM
* final local evaluation
* completed

### `run_detections`

Stores YOLO or tracker output for a validation run.

Each detection includes:

* frame index
* timestamp
* tag name
* confidence
* bounding box
* track ID

### `run_scene_events`

Stores scene events generated by local VLM, cloud VLM, rule engine, or manual review.

It records:

* event source
* event key
* label
* description
* start and end time
* confidence
* related detections
* whether redaction was applied
* whether context was minimized

### `run_rule_results`

Stores the result of each condition evaluation.

Each rule result includes:

* condition key
* condition type
* status
* confidence
* evaluated timestamp
* input snapshot
* result details

Statuses include:

* `passed`
* `failed`
* `uncertain`
* `not_applicable`

### `run_step_results`

Stores checklist-level validation results.

Each step result includes:

* step key
* step order
* label
* status
* confidence
* timing
* failure reason
* explanation
* recovery policy
* evidence references

Statuses include:

* `not_started`
* `in_progress`
* `passed`
* `warning`
* `uncertain`
* `failed`
* `manual_pass`

### `evidence_items`

Stores evidence for review.

Evidence types include:

* frame
* clip
* detection group
* VLM summary
* redaction preview

This table supports evidence review, debugging, and model/rule improvement.

### `run_reports`

Stores report exports.

Supported report types include:

* summary
* full PDF
* JSON export

The PDF or exported file is stored externally, while PostgreSQL stores the URI and report JSON metadata.

---

## 9. Chat Tables

These tables support both creator-side and consumer-side AI assistance.

### `chat_threads`

Represents a chat thread linked to a project, validation run, step result, or evidence item.

Thread types include:

* rule authoring
* result help
* evidence help
* package support

### `chat_messages`

Stores messages inside each chat thread.

Message roles include:

* user
* assistant
* system
* tool

The schema also supports structured assistant outputs through a JSONB field.

---

## 10. Optional Store Table

### `package_reviews`

Stores user reviews for packages.

It includes:

* package ID
* user ID
* rating
* review text
* timestamps

This table can be delayed until after the MVP.

---

## 11. Important Indexes

The schema defines indexes for common access patterns, including:

* projects by creator
* videos by project
* frames by video
* annotations by frame or tag
* training jobs by project
* model artifacts by project
* packages by status
* package versions by package
* installs by user
* validation runs by user
* detections by run and timestamp
* detections by tag
* step results by run and order
* chat messages by thread

It also defines GIN indexes for JSONB queries on:

* `soup_versions.soup_json`
* `validation_runs.decision_trace`

---

## 12. MVP Schema Recommendation

For a hackathon MVP, the essential tables are:

* `users`
* `api_key_settings`
* `creator_projects`
* `project_assets`
* `workflow_videos`
* `video_frames`
* `tags`
* `annotations`
* `training_jobs`
* `model_artifacts`
* `model_eval_runs`
* `model_eval_items`
* `soup_conditions`
* `soup_actions`
* `soup_steps`
* `event_order_rules`
* `soup_packages`
* `soup_versions`
* `package_assets`
* `package_installs`
* `consumer_runtime_configs`
* `validation_runs`
* `run_detections`
* `run_scene_events`
* `run_rule_results`
* `run_step_results`
* `evidence_items`
* `chat_threads`
* `chat_messages`

The following can be postponed:

* `package_reviews`
* `run_reports`

---

## 13. High-Level Entity Relationship Summary

The schema can be understood as four connected layers:

### Creator Layer

A creator creates a `creator_project`, uploads `workflow_videos`, extracts `video_frames`, defines `tags`, and creates `annotations`.

### Model Layer

The system creates `training_jobs`, produces `model_artifacts`, and evaluates models through `model_eval_runs` and `model_eval_items`.

### Package Layer

The creator defines rules using `soup_conditions`, `soup_actions`, `soup_steps`, and `event_order_rules`. These are packaged into `soup_packages` and versioned through `soup_versions`.

### Runtime Layer

A consumer installs a package through `package_installs`, configures runtime behavior through `consumer_runtime_configs`, and runs validation through `validation_runs`. Each run produces detections, scene events, rule results, step results, evidence items, reports, and chat history.

---

## 14. Design Principles

The schema follows several important principles:

1. **Separate metadata from large files**
   PostgreSQL stores metadata and references. Cloudflare R2 stores videos, images, models, clips, and reports.

2. **Keep `.soup` versions immutable**
   Published versions should never be overwritten. New changes should create new package versions.

3. **Make privacy auditable**
   Runtime configs and decision traces record whether local VLM, cloud VLM, redaction, or minimization was used.

4. **Support both all-local and guarded-hybrid modes**
   The schema explicitly models privacy boundaries for raw video, frames, detection summaries, SOP rules, and YOLO model files.

5. **Preserve explainability**
   Validation runs store detections, scene events, rule results, step results, evidence, and decision traces so the UI can explain why a workflow passed, failed, or needs review.

6. **Support iterative improvement**
   Model evaluation items and evidence review can feed back into better annotations, better training data, and better rules.
