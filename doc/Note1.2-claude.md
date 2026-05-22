# Note 1.2 — Architect Review of SoPilot Plan & Schema

**Reviewer:** Claude (senior architect lens)
**Date:** 2026-05-21
**Inputs reviewed:** [README.md](../README.md), [PRD1.1-basic.md](./PRD1.1-basic.md), [PRD1.2-schema.md](./PRD1.2-schema.md), [PRD1.3-schemaV0.md](./PRD1.3-schemaV0.md), [mobileAppDesign.md](./mobileAppDesign.md), [yolo26-README.md](../yolo26-README.md)
**Scope:** Hackathon MVP feasibility, opinionated.
**User decisions baked in (from intake):**
1. **Drop "iPhone PWA" framing.** Target = native iOS + macOS, with `yolo26-mlx` on Mac and CoreML on iOS.
2. **Creator-side is cloud (Neon + R2). Consumer-side is local.** Privacy claims only attach to the consumer runtime path.
3. Hackathon MVP feasibility lens.
4. Direct, opinionated.

---

## TL;DR

The product vision is strong and differentiated — "local SOP decision engine, cloud VLM only as advisory" is a defensible position with a clear privacy story and a real creator marketplace. The schema work in PRD1.3 is competent and basically right in shape.

But three things will sink the hackathon if not fixed in week one:

1. **The runtime story is incoherent.** "iPhone PWA" + "YOLO26 MLX" + "LLaVA via Ollama" cannot coexist on one device. MLX needs Python + Metal + macOS; Ollama needs a server; PWA needs WebKit. You committed to dropping PWA — good. Now you need an explicit **two-target capability matrix** (Mac MLX vs iOS CoreML) before any UI screen is built, because they have different model formats, different VLM stories, and different rule-engine constraints.
2. **The schema is overengineered for an MVP and underspecified for the moments that matter** (`.soup` format, model-binary multi-platform manifest, on-device DB, redaction pipeline). 28 tables in the "MVP" list is a red flag. Cut to ~10 tables for the demo path, ship the rest as v0.2.
3. **The "local-first" claim has cracks.** Models hosted in R2 are *not* local until downloaded. Raw video is local *during runtime*, but creator-side it sits in R2. "Cloud VLM gets redacted/minimized context" is currently a checkbox, not a pipeline. Tighten the marketing copy to match what you can actually demo, or build the redaction pipeline.

The rest of this note is the long version, with a concrete TODO list at the end.

---

## 1. Strengths worth preserving

Before the critique, these are the parts of the plan that I would not change:

- **Separation of `.soup` (declarative SOP package) from runtime.** This is the single most important architectural decision and it's correct. It enables a store, versioning, third-party authoring, and audit trails.
- **Rule engine as final decision-maker.** Putting an LLM behind a deterministic rule engine is what makes this product defensible vs. a thin VLM wrapper. Do not weaken this.
- **Two-mode runtime (All Local / Guarded Hybrid).** The labels are good, the user-facing copy is consistent across docs. Keep this terminology locked.
- **Tags ≠ YOLO classes split.** Creator-facing label vs. internal class is the right abstraction. Most ML tools conflate these and pay for it later.
- **JSONB `soup_json` as source of truth + normalized tables as a view layer.** PRD1.3 §14.B nails this. Keep it.
- **Choosing `yolo26-mlx`.** For Mac-side inference this is the correct bet: pure MLX, no PyTorch at runtime, mature segmentation + tracking, and an MIT-friendly conversion path. Smaller models (yolo26n/s) hit real-time on M-series. The `coreml` output format in the conversion pipeline is the bridge to iOS.

---

## 2. The runtime architecture is the elephant in the room

### 2.1 What `yolo26-mlx` actually requires

From [yolo26-README.md](../yolo26-README.md):

- macOS with Apple Silicon (M1+)
- Python 3.10+
- MLX 0.30.3+
- Models are `.npz` (MLX) or `.safetensors` (training checkpoints)

This is a **macOS desktop runtime**. It is not portable to iPhone, iPad, or a browser. The MLX framework has no iOS distribution path — Apple's on-device ML story for iOS is CoreML.

### 2.2 The two-target reality

You need two runtimes that share one `.soup` format:

| Capability | macOS (yolo26-mlx) | iOS (CoreML) |
|---|---|---|
| YOLO detection | ✅ MLX `.npz`, 60–170 FPS | ✅ `.mlpackage`, A17/M-series Neural Engine |
| Tracker (ByteTrack/BoT-SORT) | ✅ in yolo26-mlx | ⚠️ port the matching/Kalman code to Swift |
| Local open VLM | ✅ Ollama (LLaVA, Qwen2-VL) | ❌ no Ollama on iOS — use a small CoreML VLM (e.g., MobileVLM, Apple's converted models) or skip |
| Rule engine | ✅ Python | ⚠️ port to Swift, or run as a WASM module |
| Cloud VLM (Gemini/GPT) | ✅ HTTPS | ✅ HTTPS |
| Video I/O | ✅ AVFoundation via PyObjC or `opencv` | ✅ AVFoundation native |
| `.soup` parsing | ✅ Python | ⚠️ Swift parser needed |

**Two things follow from this table:**

1. The `.soup` package must carry **multiple model artifacts** keyed by runtime — not a single `model_uri`. See §3.3.
2. The rule engine must be implemented twice (Python on Mac, Swift on iOS) OR be a portable layer (WASM, or a tiny interpreter for the small grammar you actually need). Pick one and document it.

### 2.3 Recommendation: collapse the demo to one platform first

Don't try to ship Mac and iOS for the hackathon. Pick one. My recommendation:

**Pick macOS for the demo.** Reasons:
- `yolo26-mlx` already works there. You'd be re-implementing nothing critical for the demo.
- Local VLM (LLaVA via Ollama) is only viable on Mac. If you skip Mac, you lose the local-open-VLM story for the demo.
- Mac has cameras, video file I/O, and enough screen real estate for the creator flow.
- The design doc already specifies a MacBook variant. Reuse the wireframes.
- iOS becomes a **stretch goal**: a "consumer-only viewer" that connects to a paired Mac, or a pure offline consumer running CoreML-converted models with no local VLM and a stricter rule subset.

This single decision halves the surface area of week 1.

---

## 3. `.soup` package format — the most underspecified asset in the repo

The package is the product. Everything else (store, runtime, creator tool) exists to produce or consume it. Yet:

- There is no JSON Schema file checked into the repo.
- `soup_schema_version` exists in `soup_versions` but no version policy is defined.
- The example in PRD1.3 §15 has `models.detector.format: "pt"` — but the consumer downloads it and runs MLX. The `.pt` → `.npz` conversion has to happen *somewhere*. Where?
- iOS consumers need `.mlpackage`, not `.npz`. The schema has no way to express this.

### 3.1 Pin a schema, in a file, today

Create `doc/soup-schema-0.1.json` (JSON Schema draft 2020-12). Treat it as the contract between creator, store, and runtime. Every code path that reads or writes `.soup` must validate against it.

### 3.2 Multi-platform model manifest

Replace the single-model fields in `soup_versions` with a manifest:

```json
"models": {
  "detector": {
    "kind": "yolo26",
    "artifacts": [
      { "platform": "mac_mlx",   "format": "npz",        "uri": "r2://…/yolo26n.npz",        "sha256": "…", "size_bytes": 12345678 },
      { "platform": "ios_coreml","format": "mlpackage",  "uri": "r2://…/yolo26n.mlpackage",  "sha256": "…", "size_bytes": 12345678 },
      { "platform": "any_onnx",  "format": "onnx",       "uri": "r2://…/yolo26n.onnx",       "sha256": "…", "size_bytes": 12345678 }
    ],
    "classes": ["cuff","monitor","elbow_bend",...]
  },
  "vlm": {
    "required": false,
    "advisory_only": true,
    "providers": [
      { "platform": "mac_local", "kind": "llava-7b-q4", "via": "ollama" },
      { "platform": "cloud",     "kind": "gemini-2.5",  "modes": ["guarded_hybrid"] }
    ]
  }
}
```

Reflect this in `soup_versions`:

- Drop scalar `model_uri`, `model_format`.
- Add JSONB `models_manifest`.
- Keep `model_artifact_id` as a back-reference to the creator's primary artifact, but understand it's no longer load-bearing at runtime.

The runtime picks the artifact whose `platform` matches its capability.

### 3.3 sha256 + size are non-negotiable

Without integrity hashes, you can't make any local-trust claim. A creator publishes once; a consumer downloads from R2; the device must verify before executing. Add `sha256` and `size_bytes` to every artifact in the manifest.

### 3.4 Immutability is stated but not enforced

PRD1.2 says published `.soup` versions are immutable. The schema does not enforce it (no `published_at` lock, no row-level immutability check). Add either a DB-level rule or a service-layer guard, and document which.

---

## 4. Schema review (PRD1.2 + PRD1.3)

### 4.1 Naming drift between PRD1.2 and PRD1.3 — pick one and unify

| PRD1.2 calls it | PRD1.3 calls it |
|---|---|
| `soup_conditions` | `rule_conditions` |
| `soup_actions` | `rule_actions` |
| `soup_steps` | `rule_steps` |
| `consumer_runtime_configs` | `consumer_configs` |
| `run_scene_events` | `run_events` |
| `run_rule_results` | (missing — implicit in `run_events.condition_results`) |

**Recommendation:** keep the PRD1.3 names (`rule_*`, `consumer_configs`, `run_events`) because they're more concise and PRD1.3 has the actual SQL. Update PRD1.2 to match. Drift between two documents in the same repo is a sign nobody is reading both — fix the drift before adding more documents.

Also: PRD1.3 drops `run_rule_results`. That's a real loss — without it you can't answer "which specific condition failed for this step?" cleanly. Either re-add it, or commit to the denormalized `run_events.condition_results` JSONB pattern and add a GIN index. Don't leave it ambiguous.

### 4.2 The "MVP" subset is too big

PRD1.2 §12 lists ~28 tables. PRD1.3 §13 lists ~25. For a hackathon demo, both are too many. The minimum viable demo schema:

```
users
creator_projects
workflow_videos
video_frames           -- if you do any labeling
tags
annotations            -- if you do any labeling
model_artifacts        -- one row per trained model
soup_packages
soup_versions          -- soup_json is source of truth, no normalized rule tables yet
package_installs
validation_runs
run_detections
run_step_results
evidence_items
```

That's 14 tables. Notice what I cut:

- `training_jobs`, `model_eval_runs`, `model_eval_items` — for the hackathon, train models manually via `yolo-mlx` CLI. Record results in `model_artifacts.metrics` (JSONB). You do not need a job orchestrator.
- `rule_conditions`, `rule_actions`, `rule_steps`, `event_order_rules` — `soup_versions.soup_json` is your source of truth per §14.B. Normalize these in v0.2 when you have a real authoring UI to drive it.
- `consumer_configs` — fold into `package_installs.config_json` until you actually need to query on it.
- `rule_authoring_sessions` — defer entirely. The AI Rule Studio screen can use ephemeral browser state for the demo.
- `package_reviews`, `run_reports` — already deferred in PRD1.3 §13.
- `project_assets`, `package_assets` — replace with `r2_uri` columns on the relevant rows. You can always extract them later.

This gives you a schema that fits on one page and that you can hold in your head during a demo crisis at 11 PM.

### 4.3 Cloud vs on-device — the schema is silent on this

The biggest unanswered question in PRD1.3: **does the consumer device write to Neon, or to a local DB?**

Given the user decision (consumer-side local), the answer must be: **local SQLite mirror, optional cloud sync.**

Concretely:

- `validation_runs`, `run_detections`, `run_step_results`, `evidence_items` should be written to a local SQLite database on the consumer device. Neon is only relevant if the user opts in to sync.
- `package_installs` exists locally; a copy can be synced to Neon for analytics (install count, version distribution) but the *authoritative* row is on-device.
- This implies you need a schema that compiles to **both Postgres and SQLite**. Things to remove or rework:
  - `uuid` PKs are fine (SQLite stores as TEXT).
  - `jsonb` → SQLite `json` (no GIN; emulate with computed columns + indexes where needed).
  - `text[]` arrays in `supported_modes`, `required_action_ids` → JSON arrays.
  - `check (… in (…))` enums → fine in both, but keep the lists short.
  - `gen_random_uuid()` → app-side UUID generation.
  - GIN indexes → drop, or replace with shadow columns.

Write a short "Postgres ↔ SQLite parity" note in `doc/` before you start the consumer app.

### 4.4 Specific table-level critique

#### `users`
Fine. For MVP, you may not need this at all on the consumer device — installing a package locally doesn't require an account. Defer auth.

#### `api_key_settings` (PRD1.2 §1) — missing from PRD1.3
PRD1.2 says "API keys should not be stored in plaintext" and uses `gemini_key_ref`, `cloudflare_key_ref`. PRD1.3 doesn't include this table at all. Decide:
- If keys are user-supplied (Screen 27), keep them in the OS keychain (macOS Keychain, iOS Keychain) — **not in Neon, not in SQLite**. Schema only needs `is_configured` booleans.
- If keys are server-side (you operate Gemini/Cloudflare on behalf of users), they shouldn't be in user-scoped rows at all.

Screen 27 implies user-supplied. Drop the table; use Keychain.

#### `creator_projects`
Status enum has 8 states. That's too many to maintain consistency on. Collapse to 4: `draft`, `training`, `authoring`, `published`. The fine-grained states (`collecting_data`, `labeling`, `model_testing`, `rule_authoring`, `testing_rules`, `packaged`) are UI hints, not schema state. Compute them from the existence of related rows.

#### `workflow_videos`
`video_type` enum has `'consumer_run'` — that doesn't belong here. Consumer videos go to `validation_runs.input_video_uri` (local path). `workflow_videos` is creator-side training data. Drop `'consumer_run'`.

#### `annotations`
`bbox_format: 'xyxy_normalized'` — good, but enforce it. If you ever store unnormalized boxes the bug will be silent. Add a CHECK `(x_min between 0 and 1 and x_max between 0 and 1 and …)` for normalized boxes.

#### `model_artifacts`
- `model_format: 'pt' | 'onnx' | 'mlx' | 'coreml'` — fine, but `'mlx'` is ambiguous. The MLX export is `.npz`. Call it `'mlx_npz'`. Also add `'safetensors'` because that's what `yolo26-mlx` training produces (`best.safetensors`).
- `runtime: 'mlx' | 'pytorch' | 'onnxruntime' | 'coreml' | 'other'` — drop `'pytorch'` (you said local-first, no PyTorch at runtime).
- `classes jsonb default '[]'` — should be a non-empty array on a successful artifact. Add a service-layer check or a CHECK constraint.

#### `soup_versions`
- See §3 above on the manifest restructuring.
- `supported_modes: text[] default array['local']` — fine, but the values should be exactly `'all_local'` and `'guarded_hybrid'` to match the consumer UI copy.
- Missing `published_at` and `published_by` for the audit trail required by your immutability claim.

#### `package_installs`
- `local_model_path text, local_soup_path text` — these are filesystem paths and shouldn't be in Neon at all (they leak user device paths and become invalid across devices). Move to local SQLite only.
- Unique `(user_id, package_id)` — what about reinstall after uninstall? Either soft-delete with `uninstalled_at` (what you have) and drop the unique constraint, or hard-delete on uninstall. Pick one.

#### `consumer_configs`
- Lots of boolean toggles that all default to safe values. Good.
- Missing: `cloud_vlm_confidence_threshold numeric` — what's the threshold for triggering ambiguity gate? This needs to be configurable per install.
- Missing: `cloud_vlm_provider` choice when multiple are configured.

#### `validation_runs`
- `input_video_uri text` — call out explicitly that this is a **local file URI** for consumer runs (`file:///…`). If it ever points to R2, your privacy claim breaks.
- `summary jsonb default '{}'` is vague. Define a schema for it (it's the data the result screen renders).
- `decision_trace` mentioned in PRD1.2 §8 is missing in PRD1.3 SQL. Add it: `decision_trace jsonb default '[]'`. This is the audit log that proves the local-final-decision claim.

#### `run_detections`
- For a 30-second BP monitor video at 5 FPS sampling × 5 average detections per frame = 750 rows. Fine. For a 5-minute HVAC walkthrough at 10 FPS × 20 detections = 60,000 rows. Plan for this in indexing and in UI pagination.
- Drop the per-row `bbox_format` column — it should be a per-run or per-package invariant, not per-row. Saves ~30 bytes per row at scale.

#### `evidence_items`
- `evidence_type` enum is missing `'redaction_preview'` from PRD1.2 §8. Add it.
- `rule_snapshot jsonb` — capturing the rule at evaluation time is correct (rules can be edited later). Good design.

#### `chat_threads`
- Four nullable FKs (`project_id`, `run_id`, `step_result_id`, `evidence_item_id`) — this is a polymorphic association in disguise. Acceptable for MVP but document it. Add a CHECK: exactly one of the four is non-null.

### 4.5 Indexes

PRD1.2 §11 is fine. Two additions:

- `run_detections (run_id, frame_index)` — your inner loop will be "give me all detections for this frame."
- `validation_runs (user_id, started_at desc)` — the home screen lists recent runs.

---

## 5. Rule engine — the smallest grammar that demos well

PRD1.3 lists 9 `condition_type` values. For the BP monitor demo, you need 3:

- `inside` — `cuff inside upper_arm bbox`
- `orientation` — `cuff above elbow_bend` (with angle tolerance)
- `presence_duration` — `monitor visible for ≥ N seconds`

For event order (start button pressed after cuff placed):

- `temporal_order` — `event A before event B`

That's the entire grammar for v0.1. Defer `overlap`, `outside`, `position`, `transform_position`, `bridge_relation`, `vlm_confirmation`, `fusion` until you have a second workflow that genuinely needs one of them.

**Why this matters:** every condition type is a separate piece of code, a separate test fixture, a separate UI in the Rule Studio, and a separate place for the cloud-vlm fallback to misbehave. Four condition types is a weekend of work. Nine is a month.

### 5.1 Coordinate convention — pin it now

"above" in image space means smaller y (origin top-left). State this explicitly in the schema doc with a coordinate diagram. Hand-wavy "orientation" rules will fail in confusing ways otherwise.

### 5.2 Confidence vs. duration vs. min_confidence

`rule_actions.confidence_threshold`, `rule_actions.min_duration_sec`, `rule_conditions.params.min_confidence` are three different knobs that all affect whether a step passes. Document the precedence. My recommendation:

1. Each frame is detected (YOLO confidence ≥ `min_detection_confidence`, package-level).
2. Each condition is evaluated per frame; condition holds if predicate is true AND involved detections meet `params.min_confidence`.
3. Each action fires when its primary condition holds for ≥ `min_duration_sec` continuously AND mean condition-confidence ≥ `confidence_threshold`.
4. Each step passes when its required actions fire in valid temporal order.

Write this out. Once. In one place.

---

## 6. Privacy story — match copy to reality

The product promise is good. The exact wording occasionally drifts in directions you cannot deliver. Tighten:

| Current copy | Issue | Suggested copy |
|---|---|---|
| "YOLO model stays local" | The model lives in R2 until first install. | "Your YOLO model runs locally after install" |
| "Raw video stays local" | True for consumer runs; false for creator training videos. | Same copy, but **only show on the consumer runtime**. Remove from creator screens. |
| "Cloud VLM receives minimized/redacted context only" | This requires a redaction pipeline that doesn't exist yet. | Until built: "If you enable cloud VLM, only a cropped detection summary is sent." Then build the face-blur/bg-mask pipeline before adding "redacted." |
| "Final decision is local" | This is the strongest claim and is genuinely true. | Keep as-is. Use it everywhere. |

Add a single source-of-truth `doc/privacy-claims.md` that the UI copy is sourced from. Right now the same claims are paraphrased 8+ ways across the design doc.

### 6.1 The redaction pipeline is a real piece of code, not a checkbox

Screen 10 ("Redaction / Minimization Preview") implies a face detector and a background masker. For the hackathon: ship Screen 10 with a hard-coded crop ("the only image we ever send is a 256×256 crop around the YOLO-detected ROI, with no face detection"). That is honest and easy. If you ship a screen that says "face blurred" and the face isn't blurred, you have a credibility problem.

---

## 7. Creator workflow — what's realistic in a hackathon

The 13-step creator flow in Epic 4 is a 6-month product, not a hackathon demo. The smallest creator flow that produces a working `.soup`:

1. CLI / Mac-only "import existing dataset" — point at a folder of labeled YOLO data, no in-app labeling.
2. Run `yolo-mlx converters convert` + a tiny training driver — output `.npz` and convert to `.mlpackage`.
3. Hand-write `soup.json` from a template, validate against schema.
4. "Try on video" runs the existing rule engine.
5. Click "Export" — bundles `.npz`, `.mlpackage`, `soup.json` into a `.soup` (a zip or just a folder).

That's the demoable creator path. Screens 14–23 are aspirational; build the UI shells, gate the buttons, and tell the audience "the in-app version is post-MVP." Nobody will fault you for this if the consumer flow is polished.

### 7.1 Drop on-phone labeling

Screen 18 — labeling bounding boxes on a phone — is a UX disaster even when done well. Specify that labeling happens on Mac (or in a web tool like CVAT/Roboflow you don't have to build). The mobile screen can exist as "Review samples on the go" but not "draw boxes here."

---

## 8. Cloud VLM — what's actually needed for the demo

For the hackathon you do **not** need cloud VLM to function. You need the **UI flow** to demonstrate the policy: ambiguity gate → user consent → minimized payload preview → result → "final decision still local."

Stub it. The cloud call can be a 2-second `setTimeout` returning a canned advisory string. Spend zero time on Gemini integration in week 1. The story sells the architecture, not a working API call.

When you do wire it up (post-hackathon): pick **one** provider (Gemini 2.5 Flash is the natural fit for cheap multimodal), implement actual redaction, and put it behind a server-side proxy so API keys are never on consumer devices.

---

## 9. Design doc (mobileAppDesign.md) — observations

This is a Stitch/AI generation prompt, not a wireframe doc. That's fine for getting started, but:

- **27 screens for a hackathon is too many.** Pick the 8 screens that survive demo day:
  1. Launch / role select
  2. Home (installed packages)
  3. Package detail
  4. Start SOP check
  5. Recording / analysis progress
  6. Result with chat
  7. Evidence review
  8. Settings (mode + privacy)

  Everything else is shells with "Coming soon."
- The doc switches between "Mac local runtime / MLX" (Screen 19) and "iPhone PWA" (top of file). With the PWA framing dropped, do a global find-replace.
- "Bottom tabs: Home | Store | Create | Runs | Me" — for an iOS consumer-only app, drop **Create**. Creator lives on Mac.
- Color palette and motion direction is good and consistent. Keep this as-is; it's not the bottleneck.

### 9.1 The "AI Rule Studio" screen (Screen 21) is the one to invest in

If you have time for one polished creator screen, it's this one. Natural-language → typed rule parameters with live preview on a frame is the demoable creator moment. Everything else (labeling, training) can be CLI.

---

## 10. Open questions you still need to answer

1. **Who runs the cloud?** Neon costs money, R2 costs money, Cloudflare Workers cost money. Is this self-funded for the hackathon? If so, set hard quotas (R2 ≤ 5GB, no premium model hosting). If a sponsor, document the constraints in the README.
2. **What happens when a published `.soup` references a model that's deleted from R2?** Define a "model orphan" recovery story.
3. **How does the consumer device update an installed package?** Auto-update? User-prompted? Pinned versions? This isn't addressed.
4. **What's the LOC budget for the rule engine?** Mine: 500 LOC of Python for v0.1. If you exceed 1500, you're building the wrong abstraction.
5. **What's the licensing situation?** YOLO26-MLX is AGPL-3.0. If SoPilot wraps it as a library, your app is also AGPL. Acceptable for hackathon; matters at distribution.

---

## 11. Concrete TODO list

### P0 — blockers (do before any UI code)

- [ ] **Write `doc/architecture-runtime.md`**: the two-target capability matrix (Mac MLX, iOS CoreML), what each can and cannot do, which is the hackathon target. Lock it.
- [ ] **Write `doc/soup-schema-0.1.json`**: JSON Schema for the `.soup` package. Validate the example in PRD1.3 §15 against it as a unit test.
- [ ] **Restructure `soup_versions`** with the multi-platform `models_manifest` (§3.2). Migrate PRD1.3 SQL.
- [ ] **Resolve naming drift** between PRD1.2 and PRD1.3. Pick PRD1.3 names; rewrite PRD1.2 §1–§10 to match.
- [ ] **Cut the MVP table list to ~14** (§4.2). Update PRD1.3 §13 and PRD1.2 §12.
- [ ] **Decide and document**: Neon (cloud) ↔ SQLite (consumer device) parity rules. Add `doc/db-parity.md`.

### P1 — MVP demo path (week 1)

- [ ] Pick BP Monitor as the sole demo workflow. Freeze its tags and rules.
- [ ] Pin the rule grammar to 4 condition types: `inside`, `orientation`, `presence_duration`, `temporal_order`. Delete the rest from PRD1.3 enums.
- [ ] Write the rule precedence doc (§5.2).
- [ ] Train yolo26n on BP monitor labels — manual via `yolo-mlx` CLI, no `training_jobs` table.
- [ ] Convert to `.mlpackage` for the iOS stretch path.
- [ ] Hand-author `bp_monitor.soup` against the v0.1 schema. Check it into `packages/`.
- [ ] Build the Mac runtime: load `.soup`, sample frames, run YOLO via MLX, evaluate rules, emit `validation_runs` + `run_detections` + `run_step_results` rows in local SQLite.
- [ ] Build 8 screens (§9) in Mac variant. Stub cloud VLM with a 2-second canned response.
- [ ] Wire `decision_trace` JSONB and surface it on the Result screen — this is the demo's "wow."

### P1.5 — privacy claim cleanup (parallel)

- [ ] Add `doc/privacy-claims.md` as single source of truth. Update README, design doc, and UI copy to source from it.
- [ ] Remove the "face blurred / background masked" promise from Screen 10 until the redaction pipeline exists. Replace with "fixed-crop ROI only."
- [ ] Move API key storage to OS Keychain. Remove `api_key_settings` table from schema.

### P2 — post-hackathon (next 4 weeks)

- [ ] iOS consumer app: Swift port of rule engine, CoreML inference, no local VLM, no cloud VLM (or via server-side proxy).
- [ ] Actual cloud VLM integration with Gemini 2.5 Flash, server-side, with real redaction.
- [ ] Schema v0.2: re-add `rule_conditions/actions/steps` normalized tables once Rule Studio is real.
- [ ] Training job orchestration if creator usage shows demand.
- [ ] One additional workflow (HVAC compressor setup is listed) to stress-test the rule grammar's expressiveness.

### P3 — later

- [ ] Marketplace concerns: ratings, reviews, signed packages, revocation.
- [ ] `run_reports` (PDF export).
- [ ] Multi-tenant cloud + auth.
- [ ] Model-orphan recovery.
- [ ] Auto-update for installed packages.

---

## 12. Things I'd push back on if you disagreed with me

These are the recommendations I'd argue hardest for:

1. **Drop iOS from the hackathon.** Mac-only demo. iOS is a 3-week stretch, not a 1-week sprint.
2. **Cut the schema to ~14 tables.** Every additional table is a place the demo breaks.
3. **`soup_json` is the source of truth — don't normalize rules into tables yet.** PRD1.3 §14.B is correct; honor it.
4. **Stub cloud VLM, don't integrate.** The demo story is the architecture, not the API call.
5. **Pin the rule grammar to 4 types.** Every additional condition_type is a Pandora's box of edge cases.

If you want to override any of these, fine — but each one trades demo polish for ambition, and the hackathon rewards polish.

---

## 13. What I'd build day 1

If I were writing code tomorrow:

```
src/
  soup/
    schema.py         # JSON Schema validator, version negotiation
    loader.py         # .soup → in-memory package
    bp_monitor.soup   # hand-authored demo package
  runtime/
    sampler.py        # AVFoundation/cv2 frame sampler
    detector_mlx.py   # thin wrapper over yolo26mlx.YOLO
    rules/
      inside.py
      orientation.py
      presence_duration.py
      temporal_order.py
    engine.py         # condition evaluator + step state machine
    trace.py          # decision_trace builder
  db/
    sqlite.py         # local DB; one file
    migrations/0001_init.sql
  app/
    main_mac.py       # PyObjC or rumps for the menu-bar shell; or Electron
    ui/...
```

No Neon. No R2. No cloud. The cloud comes back once the local loop works end-to-end on the BP monitor demo. That's the hackathon.

---

## Appendix A — Verbatim issues found in PRD1.3

For the next editing pass:

- Line ~313 (`training_jobs`): `output_format` includes `'mlx'`. Should be `'mlx_npz'` or `'npz'` to match `yolo26-mlx` artifacts.
- Line ~356 (`model_artifacts`): `runtime` includes `'pytorch'` — remove (no PyTorch at runtime per spec).
- Line ~709 (`soup_versions`): `model_format default 'pt'` — `.pt` is the input to conversion, not a runtime artifact. Default to `'mlx_npz'` or, better, drop the scalar entirely (see §3.2).
- Line ~872 (`validation_runs`): no `decision_trace` column. PRD1.2 §8 says it should be there. Add it.
- Line ~960 (`run_events`): missing `run_rule_results` equivalent. Either re-add per-condition results table or document the JSONB pattern explicitly.

---

## Appendix B — `yolo26-mlx` integration notes

Concrete details for the runtime team:

- **Install:** `pip install -e .` + `pip install -e ".[convert]"` for the `.pt → .npz` step.
- **API:** `from yolo26mlx import YOLO; model = YOLO("path.npz"); results = model.predict(...)`. Match this signature in your detector wrapper so swapping models is trivial.
- **Output format:** `results[0].boxes` is `(N, 6)` `[x1, y1, x2, y2, conf, cls]`. Normalize once in the wrapper, store normalized in `run_detections`.
- **Image sizes:** default 640. The BP monitor demo will be fine at 640. Don't bump to 1280 without a measured reason.
- **Performance reality check:** on M4 Pro, yolo26n gets 170 FPS, yolo26s 105 FPS. On an M1 MacBook Air expect roughly half. That's still real-time. On M3 iPhone via CoreML: roughly 30 FPS for n-size. Plan UI animations accordingly.
- **License:** AGPL-3.0. If you ship a binary that statically links yolo26-mlx, the app is AGPL. For a hackathon this is fine. For commercial distribution, talk to webAI (the upstream maintainer) about a commercial license, or run yolo26-mlx as a separate process and IPC into it.
- **CoreML export path:** `yolo-mlx converters convert model.pt -o model.mlpackage --format coreml` (verify the exact flag in the CLI; if not supported directly, go `.pt → .onnx → .mlpackage` via `coremltools`).
- **Tracker:** ByteTrack is in the package. For BP monitor demo you don't need a tracker (objects are stationary). Defer.

---

*End of review. Happy to drill into any section, or to write the `soup-schema-0.1.json` and `bp_monitor.soup` next.*
