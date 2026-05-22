# SOUP Package Design

SOUP stands for **Standard Operating Understanding Package**.

A `.soup` package is an executable, portable definition of a physical workflow SOP. It tells SoPilot what to look for in a video, how to convert visual evidence into structured scene events, which local rules to evaluate, and how to produce an explainable result.

The key design rule is simple:

> A `.soup` file can use AI to observe a scene, but the final SOP decision must be made by the local rule engine.

---

## 1. Why `.soup` Exists

Traditional SOPs are written for humans. They are often PDFs, checklists, or training docs. That makes them easy to read but hard for software to execute.

A `.soup` package turns an SOP into a machine-readable workflow package:

- What steps should happen.
- What objects or actions must be visible.
- What order the steps should occur in.
- What timing or geometry constraints matter.
- Which local model detects which objects.
- When a step should pass, fail, or become uncertain.
- Whether optional cloud VLM help is allowed.
- What evidence should appear in the final report.

The goal is not to replace human expertise. The goal is to make physical workflow validation more repeatable, inspectable, and privacy-preserving.

---

## 2. Core Design Principles

## 2.1 Local-first by default

A `.soup` package should be runnable in **All Local** mode.

In All Local mode:

- Raw video stays local.
- SOP rules stay local.
- YOLO model stays local after installation.
- Local open VLM can generate scene events.
- Local rule engine makes the final decision.
- Reports and evidence are stored locally unless the user exports them.

## 2.2 Cloud VLM is advisory only

Cloud VLM must never be the source of final truth.

Allowed cloud role:

- Summarize an ambiguous cropped scene.
- Answer a single-step question.
- Help explain low-confidence local evidence.

Blocked cloud inputs:

- Raw video.
- Full SOP script.
- YOLO model.
- Full `.soup` package.
- Full private workflow logic.

The cloud VLM can produce an advisory summary, but the local rule engine performs the final evaluation.

## 2.3 Separate perception from rules

The `.soup` design separates three layers:

1. **Perception** — YOLO, tracker, local VLM, optional cloud VLM summary.
2. **Scene events** — normalized observations such as `cuff_on_upper_arm` or `connector_attached`.
3. **Rules** — deterministic local checks such as sequence, geometry, timing, and required steps.

This keeps SoPilot from becoming a fragile prompt-only system.

## 2.4 Explainability by default

Every result should point back to:

- The step being evaluated.
- The rule being applied.
- The evidence frame or clip.
- The model outputs used.
- The confidence score.
- Whether cloud assistance was used.
- Why the final result passed, failed, or remained uncertain.

## 2.5 Creator-friendly but auditable

Creators should be able to author packages through UI, but the final package should still be inspectable as structured JSON or YAML.

A package should be easy to review, version, diff, export, and share.

---

## 3. Recommended Package Shape

A `.soup` package can be represented as a single JSON/YAML file during the hackathon. In production, it may become a zipped bundle containing metadata, rules, prompts, sample tests, and model references.

Recommended sections:

```text
package
runtime
models
steps
tags
rules
prompts
outputs
tests
```

---

## 4. Package Metadata

```json
{
  "package": {
    "id": "bp_monitor_sop_checker",
    "name": "Blood Pressure Monitor SOP Checker",
    "version": "0.1.0",
    "category": "Healthcare Workflow",
    "creator": "Verified Creator",
    "description": "Checks whether a user sets up a blood pressure monitor workflow correctly.",
    "safety_note": "For workflow assistance only. Not medical diagnosis."
  }
}
```

Metadata should make the package understandable before installation.

Required fields:

- `id`
- `name`
- `version`
- `category`
- `description`
- `safety_note`

---

## 5. Runtime Policy

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
  }
}
```

Runtime policy exists so the app can explain exactly what is local, what is optional, and what is never sent to cloud.

---

## 6. Model Configuration

```json
{
  "models": {
    "detector": {
      "type": "yolo",
      "format": "pt",
      "runtime": "local",
      "uri": "https://r2.example.com/models/bp-yolo-v1.pt",
      "local_path": "models/bp-yolo-v1.pt"
    },
    "local_vlm": {
      "enabled": true,
      "provider": "ollama",
      "model": "qwen2.5-vl:3b",
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

The detector and local VLM generate evidence. The rule engine decides.

---

## 7. Tags

Tags define the objects or regions the package cares about.

```json
{
  "tags": [
    {
      "id": "blood_pressure_monitor",
      "name": "Blood pressure monitor",
      "used_by_yolo": true,
      "used_by_rules": true
    },
    {
      "id": "cuff",
      "name": "Arm cuff",
      "used_by_yolo": true,
      "used_by_rules": true
    },
    {
      "id": "upper_arm",
      "name": "Upper arm",
      "used_by_yolo": true,
      "used_by_rules": true
    },
    {
      "id": "elbow_bend",
      "name": "Elbow bend",
      "used_by_yolo": true,
      "used_by_rules": true
    },
    {
      "id": "grey_connector",
      "name": "Grey connector",
      "used_by_yolo": true,
      "used_by_rules": true
    }
  ]
}
```

Tags are shared by the labeling tool, YOLO model, rule engine, evidence review, and report UI.

---

## 8. Steps

Steps define the workflow checklist.

```json
{
  "steps": [
    {
      "id": "monitor_visible",
      "name": "Monitor is visible",
      "required": true,
      "order": 1
    },
    {
      "id": "connector_attached",
      "name": "Connector is attached",
      "required": true,
      "order": 2
    },
    {
      "id": "cuff_on_upper_arm",
      "name": "Cuff is on upper arm",
      "required": true,
      "order": 3
    },
    {
      "id": "cuff_above_elbow",
      "name": "Cuff is above elbow bend",
      "required": true,
      "order": 4,
      "ambiguity_allowed": true
    },
    {
      "id": "start_after_setup",
      "name": "Start is pressed after setup",
      "required": true,
      "order": 5
    }
  ]
}
```

Steps are the user-facing progress model. Rules implement how each step is validated.

---

## 9. Rules

Rules are local, deterministic checks over scene events, object detections, geometry, confidence, and time.

Example orientation rule:

```json
{
  "rules": [
    {
      "id": "cuff_above_elbow",
      "step_id": "cuff_above_elbow",
      "type": "orientation",
      "source_tag": "cuff",
      "target_tag": "elbow_bend",
      "direction": "above",
      "angle_tolerance_degrees": 60,
      "min_confidence": 0.5,
      "local_vlm_assistance": "optional",
      "cloud_fallback": "only_if_ambiguous",
      "failure_message": "The cuff may be too close to or below the elbow bend."
    }
  ]
}
```

Example sequence rule:

```json
{
  "id": "start_after_cuff_placement",
  "step_id": "start_after_setup",
  "type": "sequence",
  "required_before": [
    "monitor_visible",
    "connector_attached",
    "cuff_on_upper_arm",
    "cuff_above_elbow"
  ],
  "event": "start_button_pressed",
  "failure_message": "Start was pressed before setup was complete."
}
```

Recommended MVP rule types:

- `presence`
- `orientation`
- `overlap`
- `distance`
- `sequence`
- `required_step`
- `temporal_order`
- `confidence_gate`

---

## 10. Scene Events

The runtime converts model output into scene events.

```json
{
  "scene_event": {
    "id": "cuff_on_upper_arm",
    "timestamp": "00:23",
    "confidence": 0.82,
    "sources": [
      "yolo_tracker",
      "local_vlm"
    ],
    "evidence": {
      "frame_id": "frame_023",
      "tags": ["cuff", "upper_arm"]
    }
  }
}
```

Rules should operate on scene events rather than raw model outputs whenever possible.

---

## 11. Output and Report Policy

```json
{
  "outputs": {
    "result_format": "json",
    "include": [
      "step_results",
      "decision_trace",
      "privacy_log",
      "evidence_frames",
      "cloud_vlm_usage"
    ],
    "evidence_storage": "local_pointers",
    "export_options": [
      "summary_pdf",
      "json_report"
    ]
  }
}
```

The output should always include a decision trace.

---

## 12. Test Cases

A good package should include test videos or test metadata.

```json
{
  "tests": [
    {
      "id": "correct_01",
      "video": "tests/correct_01.mov",
      "expected_status": "passed"
    },
    {
      "id": "wrong_start_early",
      "video": "tests/wrong_start_early.mov",
      "expected_status": "failed",
      "expected_failed_steps": ["start_after_setup"]
    },
    {
      "id": "ambiguous_cuff_position",
      "video": "tests/ambiguous_cuff_position.mov",
      "expected_status": "needs_review",
      "expected_uncertain_steps": ["cuff_above_elbow"]
    }
  ]
}
```

Tests make packages more trustworthy and easier to publish.

---

## 13. MVP Validation Checklist

Before publishing a SOUP package:

- [ ] Package metadata is complete.
- [ ] Safety note is present.
- [ ] Runtime policy declares final local decision.
- [ ] All cloud allowed and blocked inputs are specified.
- [ ] Tags match YOLO labels.
- [ ] Steps are ordered and human-readable.
- [ ] Rules reference valid steps and tags.
- [ ] At least one positive test video passes.
- [ ] At least one negative test video fails correctly.
- [ ] Ambiguous cases produce `needs_review`, not false confidence.
- [ ] Report includes decision trace and privacy log.

---

## 14. One-line Design Summary

A `.soup` package is an installable SOP workflow definition that keeps rules and final decisions local while allowing AI models to contribute explainable visual evidence.
