# SoPilot
Version 1.0
5/24/2026
zhensong23931@gmail.com

SoPilot is a **local-first SOP video checker** for physical workflows.

It lets users install or create **SOUP packages** — Standard Operating Understanding Packages — that validate whether a recorded workflow follows a Standard Operating Procedure.

The core idea:

> Use computer vision and VLMs to understand what happened in a workflow video, but keep SOP rules and final decisions local.

For details on the `.soup` package format, see [SOUP.md](./SOUP.md).

---

## 1. Pitch

Physical SOPs are everywhere: healthcare device setup, field service, safety inspections, lab workflows, factory tasks, and training checklists. But most SOP validation still depends on manual review, self-reporting, or generic video recordings.

SoPilot turns SOPs into installable, executable AI packages.

A user can:

1. Install a SOUP package.
2. Record or upload a workflow video.
3. Run local computer vision and local rules.
4. Get an explainable pass / fail / needs-review report.
5. Ask follow-up questions grounded in the SOP and evidence.

A creator can:

1. Capture correct and incorrect workflow examples.
2. Label objects and steps.
3. Train or attach a YOLO detector.
4. Author local SOP rules with AI assistance.
5. Export or publish a reusable SOUP package.

SoPilot is intentionally not a cloud VLM wrapper.

The final decision is always made by the local rule engine. Cloud VLM can be used only in Guarded Hybrid mode, only for ambiguous cases, and only after redaction/minimization.

---

## 2. Core Product Promise

SoPilot gives teams a way to validate physical workflows with:

- **Local-first privacy** — raw video, SOP rules, and model weights stay local by default.
- **Explainable decisions** — every result points to steps, rules, evidence, and confidence.
- **Reusable SOP packages** — workflows can be distributed as `.soup` packages.
- **Creator tooling** — experts can build packages without hand-writing every line of code.
- **Optional guarded cloud help** — cloud VLM can summarize ambiguous visual evidence, but cannot make the final decision.

---

## 3. System Overview

```text
SOUP Package
  - SOP steps
  - object tags
  - local rules
  - model references
  - runtime policy
        │
        ▼
Video / Camera
        │
        ▼
Frame Sampler
        │
        ▼
YOLO / Tracker ───────▶ Local Open VLM
        │                       │
        │                       ▼
        │                Scene Events
        ▼
Local Rule Engine
        │
        ▼
Local Compliance Result
        │
        ▼
Optional Guarded Hybrid path only if ambiguous
        │
        ▼
Redacted/minimized context → Cloud VLM summary → Local final evaluation
```

---

## 4. Four Epics as Four Use Cases

## Epic 1 — SOUP Store and Package Installation

### Use case

A user wants to validate a specific workflow but does not want to build the SOP package from scratch.

They open the SOUP Store, search for a package, review what it checks, inspect the privacy policy, and install it.

### Example

A home user searches for **Blood Pressure Monitor SOP Checker**.

The package detail page explains that it checks:

- Monitor is visible.
- Grey connector is attached.
- Cuff is on upper arm.
- Cuff is above the elbow bend.
- Start button is pressed after setup.

The page also explains the decision pipeline:

1. Frame sampler.
2. YOLO / tracker.
3. Local open VLM for scene events.
4. Local rule engine.
5. Local compliance result.

The user chooses either:

- **All Local** — no cloud VLM.
- **Guarded Hybrid** — cloud VLM can be used only for ambiguous cases after redaction and confirmation.

### Why this matters

This makes SOP validation feel like installing an app. The user does not need to know how YOLO, VLMs, or rule engines work.

### MVP outcome

The user can install a SOUP package and start a SOP check in under one minute.

---

## Epic 2 — Consumer SOP Validation Runtime

### Use case

A user records or uploads a workflow video and wants to know whether the process was done correctly.

### Example

The user starts a Blood Pressure Monitor SOP check.

SoPilot shows the checklist before recording:

1. Monitor is visible.
2. Connector is attached.
3. Cuff is on upper arm.
4. Cuff is above elbow bend.
5. Start is pressed after setup.

The user records a video. SoPilot runs the local pipeline:

- Samples frames.
- Detects key objects with YOLO/tracker.
- Uses local VLM to describe ambiguous scene events.
- Evaluates local rules.
- Produces a result.

Example result:

```text
Compliance Score: 86%
Status: Needs Review

✓ Monitor visible
✓ Connector attached
✓ Cuff on upper arm
⚠ Cuff above elbow uncertain
✕ Start pressed too early

Decision path:
Frame sampler: local
YOLO / tracker: local
Local open VLM: used
Cloud VLM: not used
Final rule evaluation: local
```

The user can ask:

- “Can I repeat only failed step?”
- “Why did step 4 fail?”
- “Show evidence clip.”
- “Was cloud VLM used?”

### Why this matters

The product gives users a practical answer instead of a vague AI summary. It shows which step failed, why it failed, and what evidence supported the decision.

### MVP outcome

The user can record or upload a video, run validation, view results, and inspect evidence.

---

## Epic 3 — Guarded Hybrid Ambiguity Resolution

### Use case

The local system is unsure about a visual condition, and the user wants optional cloud help without exposing the full workflow.

### Example

The rule `cuff_above_elbow` is uncertain.

Local confidence is low because:

- The elbow bend is partially hidden.
- The cuff overlaps the upper arm.
- The angle relation is unclear.

If the package is running in Guarded Hybrid mode, SoPilot opens an ambiguity gate:

```text
Local system is unsure.
Cloud VLM can help summarize this ambiguous scene,
but the final decision will still be made locally.
```

Before sending anything to cloud, SoPilot shows:

- Cropped cuff/arm frame.
- Redacted face/background.
- Detection summary.
- Single-step question.

SoPilot blocks:

- Raw video.
- Full SOP script.
- YOLO model.
- Full package JSON.

After user approval, cloud VLM returns an advisory summary. Then the local rule engine performs the final decision.

### Why this matters

This preserves the local-first trust model while still giving the system a graceful fallback when local vision is uncertain.

### MVP outcome

The user can approve or skip cloud assistance. Reports clearly show whether cloud VLM was used and confirm that the final decision was local.

---

## Epic 4 — Creator Mode and SOUP Package Authoring

### Use case

A domain expert wants to create a reusable SOP validation package without building the whole AI stack manually.

### Example

A creator builds a Blood Pressure Monitor SOP package.

They go through the creator flow:

1. Create package metadata.
2. Add safety note.
3. Capture correct workflow videos.
4. Capture common mistake videos.
5. Upload part images.
6. Extract frames.
7. Label objects such as `cuff`, `upper_arm`, `elbow_bend`, `grey_connector`, and `button`.
8. Train or attach a YOLO model.
9. Test model precision and recall.
10. Author rules in AI Rule Studio.
11. Try rules on sample videos.
12. Debug failed rules.
13. Export or publish the `.soup` package.

A rule may look like:

```json
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
```

### Why this matters

The creator workflow turns expert SOP knowledge into reusable, installable packages. This is the foundation for a SOUP marketplace.

### MVP outcome

A creator can build a package shell, label data, train/test a detector, author rules, and export a `.soup` package.

---

## 5. Runtime Modes

## 5.1 All Local

In All Local mode:

- YOLO runs locally.
- Tracker runs locally.
- SOP rules stay local.
- Local open VLM runs locally.
- Final rule evaluation is local.
- Cloud VLM is disabled.

This is the default mode and the strongest privacy story.

## 5.2 Guarded Hybrid

In Guarded Hybrid mode:

- The full local pipeline runs first.
- Cloud VLM is triggered only for ambiguity, low confidence, or user-requested help.
- User must approve cloud use.
- Only minimized/redacted context is sent.
- Cloud VLM produces advisory summary only.
- Local rule engine still makes the final decision.

---

## 6. Repository Structure

Suggested structure:

```text
sopilot/
  README.md or READ.md
  SOUP.md
  packages/
    bp_monitor_sop_checker.soup.json
  app/
    mobile/
    desktop_runtime/
  runtime/
    frame_sampler/
    detector_yolo/
    tracker/
    local_vlm/
    rule_engine/
    report_generator/
  creator/
    labeling/
    training/
    rule_studio/
  docs/
    prd.md
    wireframes.md
    demo_script.md
```

---

## 7. VLM Fine Tuning Cost Estimation

## 7.1 Cost framing

For SoPilot, VLM fine-tuning should not be the first tool used for every workflow.

Recommended order:

1. Use YOLO/tracker for object detection and geometry.
2. Use local rules for final decisions.
3. Use local open VLM with prompts for scene-event generation and explanations.
4. Use optional cloud VLM only for ambiguous cases.
5. Fine-tune a VLM only when repeated prompt-based evaluation is not accurate enough.

For many private SOP workflows, the most cost-effective path is likely:

- Fine-tune or train lightweight object detectors per workflow.
- Keep SOP decision logic as local rules.
- Avoid VLM fine-tuning unless the workflow requires subtle visual reasoning.

## 7.2 Assumptions for 10 private SOP workflows

Example portfolio:

- 10 private SOP workflows.
- 5 steps per workflow on average.
- 8 object/action tags per workflow.
- 20 short videos per workflow.
- 300 labeled frames per workflow.
- 3,000 labeled frames total.
- One shared local VLM baseline.
- Optional LoRA fine-tuning on a small/medium VLM only if prompt-based local VLM quality is insufficient.

Hardware/pricing assumptions should be updated before production purchase. As of May 2026, public cloud GPU pricing varies by provider and GPU class. RunPod lists H100 and A100 options in per-second pricing, and Modal lists H100 at about `$0.001097/sec`, equivalent to about `$3.95/hour`; Modal lists A100 80GB at about `$0.000694/sec`, equivalent to about `$2.50/hour`. OpenAI’s public pricing page lists multimodal model pricing by token modality, including image input token pricing for several realtime multimodal models. See the references section below.

## 7.3 Example R&D budget for 10 workflows

This is a planning estimate, not a quote.

| Cost item | Assumption | Estimated cost |
|---|---:|---:|
| SOP expert time | 10 workflows × 4 hours × $100/hr | $4,000 |
| Video capture / collection | 10 workflows × 20 clips × light internal effort | $2,000 |
| Frame labeling | 3,000 frames × $0.60/frame average | $1,800 |
| Rule authoring and QA | 10 workflows × 8 hours × $100/hr | $8,000 |
| YOLO training experiments | 10 workflows × 4 GPU-hours × $2.50/hr | $100 |
| VLM prompt/eval experiments | 10 workflows × $50 API/local eval budget | $500 |
| Optional VLM LoRA fine-tuning | 3 shared experiments × 12 GPU-hours × $4/hr | $144 |
| Evaluation and regression tests | 10 workflows × 6 hours × $80/hr | $4,800 |
| Product integration overhead | mobile/runtime/report polish | $8,000 |
| **Estimated R&D total** |  | **$29,344** |

Practical takeaway: for a 10-workflow private deployment, labor and evaluation usually dominate raw GPU cost. Fine-tuning compute may be a small line item if the team uses small LoRA jobs, but dataset creation, labeling, rule design, and QA are the real cost drivers.

## 7.4 Example deployment cost for 10 workflows

Assume the customer uses local Mac runtime for normal operation.

| Cost item | Assumption | Estimated monthly cost |
|---|---:|---:|
| Local runtime hardware | Existing MacBook / Mac mini | $0 incremental |
| Package/model hosting | 10 YOLO models + metadata on object storage/CDN | $10–$50 |
| Cloud VLM fallback | 1,000 ambiguous checks/month × small cropped image + short text | $20–$200 |
| Remote GPU endpoint | Optional; only for heavier fallback or batch testing | $0–$500 |
| Logs/report storage | Metadata and local pointers; limited cloud sync | $10–$100 |
| Monitoring/admin overhead | lightweight ops | $100–$500 |
| **Estimated deployment total** | local-first default | **$140–$1,350/month** |

If the system uses cloud GPU inference heavily instead of local runtime, deployment cost can rise quickly. The local-first design is intended to keep recurring costs predictable.

## 7.5 Build vs. fine-tune decision

Fine-tune a VLM only if at least one is true:

- Prompted local VLM repeatedly misses domain-specific visual states.
- Ambiguous cases are common and expensive to review.
- The same visual reasoning pattern appears across many workflows.
- Object detection and geometry rules are not enough.
- The organization needs a private model with domain-specific vocabulary.

Do not fine-tune a VLM if:

- The task is mostly object presence and order checking.
- A YOLO detector plus local rules is sufficient.
- The workflow changes often.
- There is not enough labeled data.
- The team cannot maintain evaluation tests.

---

## 8. Example Hackathon Demo Flow

1. Open SoPilot.
2. Go to SOUP Store.
3. Select Blood Pressure Monitor SOP Checker.
4. Review the local-first decision pipeline.
5. Install package in All Local mode.
6. Record or upload a workflow video.
7. Watch local analysis progress.
8. See step-level result.
9. Open evidence review.
10. Ask: “Can I repeat step 4?”
11. Switch to Guarded Hybrid demo.
12. Show ambiguity gate.
13. Show redaction/minimization preview.
14. Show cloud advisory summary.
15. Show final local rule evaluation.
16. Open Creator Mode.
17. Show how a creator builds and publishes a SOUP package.

---

## 9. What Makes SoPilot Different

Most VLM demos ask a model, “Did this video follow the process?”

SoPilot does something more structured:

- Packages the SOP as a `.soup` file.
- Converts video into scene events.
- Evaluates deterministic local rules.
- Produces evidence-backed reports.
- Uses cloud only as optional advisory support.
- Supports creators who can build reusable workflow packages.

This gives SoPilot a stronger privacy story, lower recurring cost, and better auditability than a cloud-only VLM approach.

---

## 10. References for Cost Assumptions

Pricing changes frequently. Re-check before making budget decisions.

- Lambda GPU pricing: https://lambda.ai/pricing
- RunPod GPU pricing: https://www.runpod.io/pricing
- Modal GPU pricing: https://modal.com/pricing
- OpenAI API pricing: https://openai.com/api/pricing/

---

## 11. Project Status

Current status: hackathon product design and MVP planning.

Next recommended build steps:

1. Finalize the BP Monitor `.soup` example.
2. Build the local rule engine skeleton.
3. Add video frame sampler.
4. Add YOLO detector integration.
5. Add local VLM scene event generator.
6. Build result report and evidence review.
7. Prototype Creator Mode screens.
8. Add Guarded Hybrid ambiguity gate.
