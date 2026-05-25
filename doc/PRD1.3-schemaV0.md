Below is a **Neon/PostgreSQL data schema** to support the mobile wireframes and the 4 Epics:

```text
E1: Creator trains YOLO
E2: Creator authors rules and exports .soup
E3: Consumer installs .soup from store
E4: Consumer records/runs SOP validation and chats about results
```

Design principle:

> Keep the exported `.soup` package as JSONB for flexibility, but store key fields in normalized tables so the UI is easy to query.

---

# 1. High-Level Schema Map

```text
users
 └── creator_projects
      ├── project_assets
      ├── workflow_videos
      ├── video_frames
      ├── tags
      ├── annotations
      ├── training_jobs
      ├── model_artifacts
      ├── model_eval_runs
      ├── model_eval_items
      ├── rule_authoring_sessions
      ├── soup_packages
      └── soup_versions

soup_packages
 ├── soup_versions
 ├── package_assets
 ├── package_installs
 └── package_reviews

package_installs
 ├── consumer_configs
 ├── validation_runs
 │    ├── run_detections
 │    ├── run_events
 │    ├── run_step_results
 │    ├── evidence_items
 │    ├── run_reports
 │    └── chat_threads
 │         └── chat_messages
```

---

# 2. Core User Tables

## `users`

Stores app users: creators and consumers.

```sql
create table users (
  id uuid primary key default gen_random_uuid(),
  email text unique,
  display_name text,
  avatar_url text,
  role text default 'consumer'
    check (role in ('consumer', 'creator', 'admin')),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
```

---

# 3. Creator Project Tables

## `creator_projects`

Supports screen **#5.2 New SOUP Package**.

```sql
create table creator_projects (
  id uuid primary key default gen_random_uuid(),
  creator_id uuid references users(id) on delete cascade,

  name text not null,
  slug text,
  category text,
  description text,
  target_users text,
  safety_note text,

  icon_asset_id uuid,
  status text default 'draft'
    check (status in (
      'draft',
      'collecting_data',
      'labeling',
      'training',
      'model_testing',
      'rule_authoring',
      'testing_rules',
      'packaged',
      'published'
    )),

  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
```

---

## `project_assets`

Stores icons, part images, screenshots, demo videos, sample reports.

Supports:

```text
#5.2 upload icon
#5.3 upload part images
#3.2 package detail preview images/videos
```

```sql
create table project_assets (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references creator_projects(id) on delete cascade,
  uploaded_by uuid references users(id),

  asset_type text not null
    check (asset_type in (
      'icon',
      'part_image',
      'workflow_video',
      'frame_image',
      'demo_video',
      'cover_image',
      'evidence_clip',
      'sample_report',
      'other'
    )),

  tag_id uuid,
  uri text not null,
  storage_provider text default 'cloudflare_r2',
  file_name text,
  mime_type text,
  file_size_bytes bigint,

  metadata jsonb default '{}'::jsonb,

  created_at timestamptz default now()
);
```

---

# 4. Training Data Tables — E1

## `workflow_videos`

Supports **#5.3 Capture Training Videos**.

```sql
create table workflow_videos (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references creator_projects(id) on delete cascade,

  video_type text not null
    check (video_type in ('correct', 'wrong', 'test', 'demo', 'consumer_run')),
  title text,
  uri text not null,
  duration_sec numeric,
  fps numeric,
  width int,
  height int,

  notes text,
  metadata jsonb default '{}'::jsonb,

  created_at timestamptz default now()
);
```

---

## `video_frames`

Supports **#5.4 Extract Frames** and **#6.2 AI Rule Studio frame strip**.

```sql
create table video_frames (
  id uuid primary key default gen_random_uuid(),
  video_id uuid references workflow_videos(id) on delete cascade,
  project_id uuid references creator_projects(id) on delete cascade,

  frame_index int not null,
  timestamp_sec numeric not null,
  image_uri text not null,

  extraction_method text default 'interval'
    check (extraction_method in ('interval', 'motion', 'manual', 'keyframe')),
  metadata jsonb default '{}'::jsonb,

  created_at timestamptz default now(),

  unique(video_id, frame_index)
);
```

---

## `tags`

Replaces “classes” with creator-friendly **tags**.

Supports **#5.5 Label Tags**.

```sql
create table tags (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references creator_projects(id) on delete cascade,

  name text not null,
  label text,
  description text,
  color text,
  yolo_class text not null,

  is_required boolean default false,
  is_editable boolean default true,

  created_at timestamptz default now(),
  updated_at timestamptz default now(),

  unique(project_id, name)
);
```

Example tags:

```text
monitor
cuff
upper_arm
elbow_bend
grey_connector
black_power_cord
start_button
display_screen
```

---

## `annotations`

Stores bounding boxes drawn on extracted frames.

Supports **#5.5 mobile labeling UI**.

```sql
create table annotations (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references creator_projects(id) on delete cascade,
  frame_id uuid references video_frames(id) on delete cascade,
  tag_id uuid references tags(id) on delete cascade,

  bbox_format text default 'xyxy_normalized',
  x_min numeric not null,
  y_min numeric not null,
  x_max numeric not null,
  y_max numeric not null,

  source text default 'manual'
    check (source in ('manual', 'auto_label', 'corrected_auto_label', 'model_prediction')),
  confidence numeric,

  created_by uuid references users(id),
  metadata jsonb default '{}'::jsonb,

  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
```

---

# 5. YOLO Training Tables — E1

## `training_jobs`

Supports **#5.6 Train YOLO Model**.

```sql
create table training_jobs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references creator_projects(id) on delete cascade,
  creator_id uuid references users(id),

  status text default 'queued'
    check (status in (
      'queued',
      'running',
      'completed',
      'failed',
      'cancelled'
    )),

  model_base text,
  output_format text default 'pt'
    check (output_format in ('pt', 'onnx', 'mlx', 'coreml')),
  training_target text default 'fast_local_prototype',

  epochs int,
  image_size int,
  validation_split numeric,

  started_at timestamptz,
  completed_at timestamptz,

  metrics jsonb default '{}'::jsonb,
  logs_uri text,
  error_message text,

  created_at timestamptz default now()
);
```

---

## `model_artifacts`

Stores trained model references, including Cloudflare R2 URLs.

Supports:

```text
E1 trained .pt output
E2 .soup links to model binary
E3 consumer downloads model
```

```sql
create table model_artifacts (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references creator_projects(id) on delete cascade,
  training_job_id uuid references training_jobs(id) on delete set null,

  name text not null,
  version text default '0.1.0',

  model_type text default 'yolo',
  model_format text default 'pt'
    check (model_format in ('pt', 'onnx', 'mlx', 'coreml')),
  runtime text default 'mlx'
    check (runtime in ('mlx', 'pytorch', 'onnxruntime', 'coreml', 'other')),

  uri text not null,
  storage_provider text default 'cloudflare_r2',
  file_size_bytes bigint,

  classes jsonb default '[]'::jsonb,
  metrics jsonb default '{}'::jsonb,

  is_active boolean default true,

  created_at timestamptz default now()
);
```

---

# 6. Model Testing Tables — E1

## `model_eval_runs`

Supports **#5.7 Model Test on Images / Frames**.

```sql
create table model_eval_runs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references creator_projects(id) on delete cascade,
  model_artifact_id uuid references model_artifacts(id) on delete cascade,

  name text,
  dataset_type text default 'validation_frames'
    check (dataset_type in ('training_frames', 'validation_frames', 'test_frames', 'custom')),

  recall_rate numeric,
  false_detection_rate numeric,
  precision_rate numeric,
  map_score numeric,

  tag_metrics jsonb default '{}'::jsonb,

  status text default 'completed'
    check (status in ('running', 'completed', 'failed')),

  created_at timestamptz default now()
);
```

---

## `model_eval_items`

Stores wrong labels, missed detections, false boxes, low-confidence frames.

Supports **Problem Image Review Queue**.

```sql
create table model_eval_items (
  id uuid primary key default gen_random_uuid(),
  eval_run_id uuid references model_eval_runs(id) on delete cascade,
  frame_id uuid references video_frames(id) on delete cascade,
  tag_id uuid references tags(id) on delete set null,

  issue_type text
    check (issue_type in (
      'missed_detection',
      'false_detection',
      'wrong_tag',
      'low_confidence',
      'bad_bbox'
    )),

  expected_bbox jsonb,
  predicted_bbox jsonb,
  confidence numeric,

  review_status text default 'open'
    check (review_status in ('open', 'fixed', 'ignored', 'added_to_training')),

  reviewer_note text,

  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
```

---

# 7. Rule Authoring Tables — E2

## `rule_authoring_sessions`

Supports **#6.1 Rule Authoring Chat** and **#6.2 AI Rule Studio**.

```sql
create table rule_authoring_sessions (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references creator_projects(id) on delete cascade,
  creator_id uuid references users(id),

  title text,
  selected_video_id uuid references workflow_videos(id),
  selected_frame_ids uuid[],

  status text default 'active'
    check (status in ('active', 'saved', 'archived')),

  generated_conditions jsonb default '[]'::jsonb,
  generated_actions jsonb default '[]'::jsonb,
  generated_steps jsonb default '[]'::jsonb,

  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
```

---

## `rule_conditions`

Stores normalized geometry rules.

Supports:

```text
inside
outside
overlap
orientation
position
transform_position
bridge_relation
```

```sql
create table rule_conditions (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references creator_projects(id) on delete cascade,

  condition_key text not null,
  condition_type text not null
    check (condition_type in (
      'inside',
      'outside',
      'overlap',
      'orientation',
      'position',
      'transform_position',
      'bridge_relation',
      'vlm_confirmation',
      'fusion'
    )),

  label text,
  description text,

  source jsonb not null default '{}'::jsonb,
  target jsonb default '{}'::jsonb,
  reference jsonb default '{}'::jsonb,
  params jsonb default '{}'::jsonb,

  is_active boolean default true,

  created_at timestamptz default now(),
  updated_at timestamptz default now(),

  unique(project_id, condition_key)
);
```

Example `params`:

```json
{
  "direction": "above",
  "angle_tolerance_deg": 60,
  "min_confidence": 0.5,
  "min_duration_sec": 2.0
}
```

---

## `rule_actions`

Stores SOP actions inferred from geometry or optional VLM.

```sql
create table rule_actions (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references creator_projects(id) on delete cascade,

  action_key text not null,
  label text not null,
  description text,

  trigger_type text default 'geometry_event'
    check (trigger_type in (
      'geometry_event',
      'vlm_confirmation',
      'hybrid',
      'manual'
    )),

  primary_condition_id uuid references rule_conditions(id),
  fallback_config jsonb default '{}'::jsonb,

  min_duration_sec numeric default 1.0,
  confidence_threshold numeric default 0.5,

  is_active boolean default true,

  created_at timestamptz default now(),
  updated_at timestamptz default now(),

  unique(project_id, action_key)
);
```

---

## `rule_steps`

Stores checklist steps shown in runtime overlay.

Supports:

```text
#4.2 live checklist overlay
#4.4 step results
#4.5 evidence review
```

```sql
create table rule_steps (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references creator_projects(id) on delete cascade,

  step_key text not null,
  step_order int not null,

  label text not null,
  description text,

  required_action_ids uuid[] default '{}',
  optional_action_ids uuid[] default '{}',

  success_ui text default 'green_check',
  failure_ui text default 'red_cross',

  recovery_policy jsonb default '{}'::jsonb,

  is_active boolean default true,

  created_at timestamptz default now(),
  updated_at timestamptz default now(),

  unique(project_id, step_key)
);
```

Example `recovery_policy`:

```json
{
  "allow_partial_retry": true,
  "restart_required_after_failure": false,
  "retry_instruction": "Repeat this step while keeping the cuff visible."
}
```

---

## `event_order_rules`

Supports simple event order before full FSM.

```sql
create table event_order_rules (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references creator_projects(id) on delete cascade,

  before_action_id uuid references rule_actions(id),
  after_action_id uuid references rule_actions(id),

  strict boolean default false,
  severity text default 'warning'
    check (severity in ('info', 'warning', 'fail')),

  message text,

  created_at timestamptz default now()
);
```

---

# 8. SOUP Package Tables — E2 + E3

## `soup_packages`

Represents the public/store-level package.

Supports **#3.1 Store Home** and **#3.2 Package Detail Page**.

```sql
create table soup_packages (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references creator_projects(id) on delete set null,
  creator_id uuid references users(id) on delete set null,

  name text not null,
  slug text unique,
  category text,
  short_description text,
  long_description text,
  icon_url text,

  status text default 'draft'
    check (status in ('draft', 'private', 'published', 'unlisted', 'archived')),

  latest_version_id uuid,
  install_count int default 0,
  rating_avg numeric,
  rating_count int default 0,

  safety_note text,

  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
```

---

## `soup_versions`

The most important table.

Stores exported `.soup` JSON and model links.

```sql
create table soup_versions (
  id uuid primary key default gen_random_uuid(),
  package_id uuid references soup_packages(id) on delete cascade,
  project_id uuid references creator_projects(id) on delete set null,

  version text not null,
  soup_schema_version text default '0.1',

  model_artifact_id uuid references model_artifacts(id) on delete set null,
  model_uri text,
  model_format text default 'pt',

  soup_json jsonb not null,
  soup_json_uri text,

  supported_modes text[] default array['local'],
  default_mode text default 'local',

  requires_vlm boolean default false,
  optional_vlm boolean default true,

  is_active boolean default true,

  created_at timestamptz default now(),

  unique(package_id, version)
);
```

Recommended `.soup_json` shape:

```json
{
  "soup_version": "0.1",
  "package": {},
  "runtime": {},
  "models": {},
  "tags": {},
  "actions": {},
  "conditions": [],
  "steps": [],
  "event_order": {},
  "fsm": {
    "enabled": false,
    "placeholder": true,
    "states": [],
    "transitions": []
  }
}
```

---

## `package_assets`

Store-facing preview images, demo videos, sample reports.

```sql
create table package_assets (
  id uuid primary key default gen_random_uuid(),
  package_id uuid references soup_packages(id) on delete cascade,
  version_id uuid references soup_versions(id) on delete cascade,

  asset_type text not null
    check (asset_type in (
      'icon',
      'cover_image',
      'preview_image',
      'demo_video',
      'sample_report',
      'sample_video',
      'documentation'
    )),

  uri text not null,
  title text,
  description text,
  display_order int default 0,

  created_at timestamptz default now()
);
```

---

# 9. Consumer Installation Tables — E3

## `package_installs`

Supports **#3.3 Install and Configure Privacy Mode**.

```sql
create table package_installs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  package_id uuid references soup_packages(id) on delete cascade,
  version_id uuid references soup_versions(id) on delete cascade,

  install_status text default 'installed'
    check (install_status in ('installed', 'uninstalled', 'failed')),
  installed_at timestamptz default now(),
  uninstalled_at timestamptz,

  local_model_path text,
  local_soup_path text,

  unique(user_id, package_id)
);
```

---

## `consumer_configs`

Stores local vs hybrid mode and VLM settings per installed package.

```sql
create table consumer_configs (
  id uuid primary key default gen_random_uuid(),
  install_id uuid references package_installs(id) on delete cascade,
  user_id uuid references users(id) on delete cascade,

  privacy_mode text default 'local'
    check (privacy_mode in ('local', 'hybrid')),

  local_vlm_enabled boolean default false,
  local_vlm_provider text,
  local_vlm_model text,

  remote_vlm_enabled boolean default false,
  remote_vlm_provider text,
  remote_vlm_model text,

  raw_video_leaves_device boolean default false,
  frames_leave_device boolean default false,
  detection_summary_can_leave_device boolean default false,
  sop_rules_leave_device boolean default false,
  yolo_model_leaves_device boolean default false,
  redact_faces boolean default true,

  config_json jsonb default '{}'::jsonb,

  created_at timestamptz default now(),
  updated_at timestamptz default now(),

  unique(install_id)
);
```

---

# 10. Runtime Validation Tables — E4

## `validation_runs`

Supports:

```text
#4.1 Start SOP Check
#4.3 Offline Analysis Progress
#4.4 Result Summary
```

```sql
create table validation_runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,
  install_id uuid references package_installs(id) on delete set null,
  package_id uuid references soup_packages(id) on delete set null,
  version_id uuid references soup_versions(id) on delete set null,

  input_video_uri text,
  input_mode text
    check (input_mode in ('recorded_camera', 'uploaded_video', 'sample_video')),

  run_mode text default 'offline_video'
    check (run_mode in ('realtime_preview', 'offline_video', 'both')),

  privacy_mode text default 'local'
    check (privacy_mode in ('local', 'hybrid')),

  status text default 'queued'
    check (status in (
      'queued',
      'recording',
      'analyzing',
      'completed',
      'failed',
      'cancelled'
    )),

  compliance_score numeric,
  result_status text
    check (result_status in ('passed', 'needs_review', 'failed')),

  started_at timestamptz default now(),
  completed_at timestamptz,

  summary jsonb default '{}'::jsonb,
  error_message text
);
```

---

## `run_detections`

Stores YOLO detection boxes per frame.

```sql
create table run_detections (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references validation_runs(id) on delete cascade,

  frame_index int not null,
  timestamp_sec numeric not null,

  tag_name text not null,
  confidence numeric,

  bbox_format text default 'xyxy_normalized',
  x_min numeric not null,
  y_min numeric not null,
  x_max numeric not null,
  y_max numeric not null,

  track_id text,

  metadata jsonb default '{}'::jsonb,

  created_at timestamptz default now()
);
```

Indexes recommended:

```sql
create index idx_run_detections_run_time
on run_detections(run_id, timestamp_sec);

create index idx_run_detections_tag
on run_detections(run_id, tag_name);
```

---

## `run_events`

Stores inferred actions/events.

Example:

```text
connect_cuff completed at 12.4 sec
place_cuff uncertain at 18.2 sec
press_start failed order check
```

```sql
create table run_events (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references validation_runs(id) on delete cascade,

  action_key text not null,
  event_status text default 'detected'
    check (event_status in ('detected', 'completed', 'uncertain', 'failed')),

  start_sec numeric,
  end_sec numeric,
  confidence numeric,

  trigger_type text
    check (trigger_type in ('geometry_event', 'vlm_confirmation', 'hybrid', 'manual')),

  condition_results jsonb default '[]'::jsonb,
  evidence_detection_ids uuid[] default '{}',

  created_at timestamptz default now()
);
```

---

## `run_step_results`

Supports checklist overlay and final result.

```sql
create table run_step_results (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references validation_runs(id) on delete cascade,

  step_key text not null,
  step_order int not null,
  label text not null,

  status text default 'not_started'
    check (status in (
      'not_started',
      'in_progress',
      'passed',
      'warning',
      'uncertain',
      'failed',
      'manual_pass'
    )),

  confidence numeric,

  started_sec numeric,
  completed_sec numeric,

  failure_reason text,
  explanation text,

  recovery_policy jsonb default '{}'::jsonb,
  evidence_item_ids uuid[] default '{}',

  created_at timestamptz default now(),
  updated_at timestamptz default now(),

  unique(run_id, step_key)
);
```

---

## `evidence_items`

Supports **#4.5 Evidence Review**.

```sql
create table evidence_items (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references validation_runs(id) on delete cascade,
  step_result_id uuid references run_step_results(id) on delete cascade,

  evidence_type text
    check (evidence_type in ('frame', 'clip', 'detection_group', 'vlm_summary')),
  uri text,
  frame_index int,
  start_sec numeric,
  end_sec numeric,

  title text,
  description text,
  related_detections jsonb default '[]'::jsonb,
  rule_snapshot jsonb default '{}'::jsonb,

  review_status text default 'unreviewed'
    check (review_status in (
      'unreviewed',
      'confirmed',
      'false_positive',
      'needs_better_rule',
      'needs_more_data'
    )),

  reviewer_note text,

  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
```

---

## `run_reports`

Supports **#7.2 Report Detail** and PDF export.

```sql
create table run_reports (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references validation_runs(id) on delete cascade,

  report_type text default 'summary'
    check (report_type in ('summary', 'full_pdf', 'json_export')),
  report_uri text,
  report_json jsonb default '{}'::jsonb,

  created_at timestamptz default now()
);
```

---

# 11. Chat Tables — Consumer + Creator

You need chat in:

```text
#4.4 Result Summary
#4.5 Evidence Review
#6.1 Rule Authoring Chat
#6.2 AI Rule Studio
```

## `chat_threads`

```sql
create table chat_threads (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references users(id) on delete cascade,

  thread_type text not null
    check (thread_type in (
      'rule_authoring',
      'result_help',
      'evidence_help',
      'package_support'
    )),

  project_id uuid references creator_projects(id) on delete cascade,
  run_id uuid references validation_runs(id) on delete cascade,
  step_result_id uuid references run_step_results(id) on delete cascade,
  evidence_item_id uuid references evidence_items(id) on delete cascade,

  title text,
  context jsonb default '{}'::jsonb,

  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
```

---

## `chat_messages`

```sql
create table chat_messages (
  id uuid primary key default gen_random_uuid(),
  thread_id uuid references chat_threads(id) on delete cascade,

  role text not null
    check (role in ('user', 'assistant', 'system', 'tool')),
  content text not null,

  structured_output jsonb default '{}'::jsonb,

  created_at timestamptz default now()
);
```

Example consumer question:

```text
Can I just repeat step 4, or do I need to start over?
```

The assistant answer can be generated from:

```text
run_step_results.recovery_policy
event_order_rules
soup_versions.soup_json
evidence_items.rule_snapshot
```

---

# 12. Store and Reviews — E3

## `package_reviews`

Optional for MVP, useful for App Store-like portal.

```sql
create table package_reviews (
  id uuid primary key default gen_random_uuid(),
  package_id uuid references soup_packages(id) on delete cascade,
  user_id uuid references users(id) on delete cascade,

  rating int check (rating between 1 and 5),
  review_text text,

  created_at timestamptz default now(),
  updated_at timestamptz default now(),

  unique(package_id, user_id)
);
```

---

# 13. Recommended MVP Tables Only

For hackathon, you do **not** need everything. I would implement this subset first:

```text
users
creator_projects
project_assets
workflow_videos
video_frames
tags
annotations
training_jobs
model_artifacts
model_eval_runs
model_eval_items
rule_conditions
rule_actions
rule_steps
event_order_rules
soup_packages
soup_versions
package_installs
consumer_configs
validation_runs
run_detections
run_events
run_step_results
evidence_items
chat_threads
chat_messages
```

Optional later:

```text
package_reviews
run_reports
package_assets
rule_authoring_sessions
```

---

# 14. Most Important Schema Decisions

## A. `.soup` should be versioned

Do not overwrite `.soup` packages. Always create a new `soup_versions` row.

```text
Blood Pressure Monitor SOP v0.1.0
Blood Pressure Monitor SOP v0.1.1
Blood Pressure Monitor SOP v0.2.0
```

This helps consumers know which package version produced each validation result.

---

## B. Keep `soup_json` as source of truth

Even though we normalize rules into tables, the actual export should live here:

```sql
soup_versions.soup_json
```

That is the portable package.

---

## C. Store model binary as URL, not inside Neon

The model should be in Cloudflare R2:

```text
model_artifacts.uri
soup_versions.model_uri
```

Neon stores metadata only.

---

## D. Tags should be user-facing; YOLO classes should be internal

Use:

```text
tag = creator-facing label
yolo_class = model-facing class name
```

Example:

```json
{
  "tag": "Grey connector",
  "yolo_class": "grey_connector"
}
```

---

## E. Runtime outputs should be linked to rules

Every failed step should be traceable:

```text
step_result
→ evidence_item
→ run_detections
→ original rule snapshot
```

This makes the chat feature useful and explainable.

---

# 15. Minimal `.soup` JSON Example Stored in `soup_versions.soup_json`

```json
{
  "soup_version": "0.1",
  "package": {
    "id": "bp-monitor-basic",
    "name": "Blood Pressure Monitor SOP Checker",
    "version": "0.1.0",
    "category": "healthcare_workflow",
    "safety_note": "For workflow assistance only. Not medical diagnosis."
  },
  "models": {
    "detector": {
      "type": "yolo",
      "format": "pt",
      "runtime": "mlx",
      "uri": "https://r2.example.com/models/bp-yolo-v1.pt",
      "bbox_format": "xyxy_normalized"
    },
    "vlm": {
      "enabled": false,
      "optional": true,
      "mode": "none"
    }
  },
  "tags": {
    "monitor": {
      "label": "Blood pressure monitor",
      "yolo_class": "blood_pressure_monitor"
    },
    "cuff": {
      "label": "Arm cuff",
      "yolo_class": "cuff"
    },
    "elbow_bend": {
      "label": "Elbow bend",
      "yolo_class": "elbow_bend"
    }
  },
  "conditions": [
    {
      "id": "cond_cuff_above_elbow",
      "type": "orientation",
      "source": {
        "tags": ["cuff"]
      },
      "target": {
        "tags": ["elbow_bend"]
      },
      "params": {
        "direction": "above",
        "angle_tolerance_deg": 60,
        "min_confidence": 0.5
      }
    }
  ],
  "actions": {
    "place_cuff": {
      "label": "Place cuff above elbow",
      "trigger": {
        "type": "geometry_event",
        "condition_id": "cond_cuff_above_elbow",
        "min_duration_sec": 2.0
      }
    }
  },
  "steps": [
    {
      "id": "step_place_cuff",
      "order": 1,
      "label": "Place cuff above elbow bend",
      "required_actions": ["place_cuff"],
      "recovery_policy": {
        "allow_partial_retry": true,
        "retry_instruction": "Reposition the cuff above the elbow and recheck this step."
      }
    }
  ],
  "event_order": {
    "enabled": true,
    "strict": false,
    "rules": []
  },
  "fsm": {
    "enabled": false,
    "placeholder": true,
    "states": [],
    "transitions": []
  }
}
```

---

This schema is enough to support the wireframes and gives you a clean path from **hackathon MVP** to **SOUP Store marketplace**.
