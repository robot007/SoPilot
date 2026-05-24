# SOUP Engine 
## Motivation: why Hybrid VLM architeure

@TODO: Improve the writing to emphasis high $ and hour costs on VLM fine tuning. Not affordable by small businesses. 
like a low cost VLM fine-tuning with privacy protection for small businesses


@TODO: this is the cost estimation by ChatGPT
Rough cost estimation

| Scope                 | Senior AI Engineer Hours | Senior AI Cost at $95/hr | Domain Expert Hours, 2× AI Hours | Domain Expert Cost at $64/hr | Total Development Labor Cost |
| --------------------- | -----------------------: | -----------------------: | -------------------------------: | ---------------------------: | ---------------------------: |
| **10 SOP workflows**  |            **180–320 h** |        **$17.1k–$30.4k** |                    **360–640 h** |            **$23.0k–$41.0k** |            **$40.1k–$71.4k** |
| **100 SOP workflows** |          **700–1,400 h** |       **$66.5k–$133.0k** |                **1,400–2,800 h** |           **$89.6k–$179.2k** |          **$156.1k–$312.2k** |


| Scope                 | Fine-Tuning Approach                                                  | Development Labor Cost | Training GPU Hours |                                     Training GPU Cost | Local Deployment GPU                                                      |  Energy / Month | Maintenance Engineer Hours / Month |                          Maintenance Cost / Month |
| --------------------- | --------------------------------------------------------------------- | ---------------------: | -----------------: | ----------------------------------------------------: | ------------------------------------------------------------------------- | --------------: | ---------------------------------: | ------------------------------------------------: |
| **10 SOP workflows**  | LoRA/QLoRA on 3B–7B VLM; small domain dataset; manual evaluation      |      **$40.1k–$71.4k** |    **20–80 GPU-h** |       **$7–$27 on RTX 4090** or **$138–$550 on H100** | **1× RTX 4090** prototype, or **1× RTX 6000 Ada** for safer 7B deployment | **~$14–$19/mo** |                      **8–16 h/mo** |   **$760–$1,520/mo** if senior AI/MLOps at $95/hr |
| **100 SOP workflows** | LoRA/QLoRA + dataset pipeline, regression tests, active-learning loop |    **$156.1k–$312.2k** |  **200–800 GPU-h** | **$68–$272 on RTX 4090** or **$1.38k–$5.50k on H100** | **1–2× RTX 6000 Ada** depending on concurrency                            | **~$14–$38/mo** |                     **24–60 h/mo** | **$2,280–$5,700/mo** if senior AI/MLOps at $95/hr |


The main change is that domain expert labor becomes a major cost driver. For this kind of SOP/VLM system, that is realistic: the model training itself may be cheap, but defining workflows, labeling objects, validating edge cases, and judging whether the system feedback is correct usually takes more human time than running the fine-tune.


10 SOP workflows:
  good for prototype / demo / pilot
  likely total dev labor: ~$40k–$71k

100 SOP workflows:
  real productization effort
  likely total dev labor: ~$156k–$312k

@TODO this is the Cost Estimation by Claude 
A note on the question: the third scale ("SOP workflows") looks like a typo — I'm interpreting it as 10, 100, and 1,000 SOPs. Flag me if you meant a different number. Everything below assumes parameter-efficient fine-tuning (QLoRA/LoRA on a 7B–11B VLM like Qwen2.5-VL, Llama-3.2-Vision, or LLaVA-NeXT), since full fine-tuning of even a 7B VLM is essentially uneconomical — full fine-tuning of a 7B model needs 100–120 GB of VRAM (~$50K of H100s), while QLoRA does the same on a $1,500 RTX 4090. Introl
Rate inputs I'm anchoring to (all cited): AI/ML engineer fully-loaded at ~$85/hr (Glassdoor May 2026 average for an AI/ML engineer is $177,652/yr or $85/hr); electricity at $0.12/kWh with PUE 1.4 (Spheron's 2026 model uses $0.12/kWh, 1.8× server overhead, and 1.4 PUE, yielding ~$0.21/hr per H100 GPU in electricity); GPU prices from current 2026 listings (RTX 4090 ~$1,600, H100 ~$30,000, A100 80GB $7,000–$15,000 new); training-time benchmarks from Spheron's 2026 fine-tuning guide (7B QLoRA on A100 = 2–4 hrs, 70B QLoRA on H100 = 8–12 hrs, full 70B fine-tune on 8×H100 = 24–48 hrs) and Runpod's QLoRA-on-RTX-4090 benchmark of 3–4 hrs for a 13B model; dataset sizing from Label Your Data (2026): 5,000–50,000 labeled image-text pairs for production-quality VLM fine-tuning, costing $100–$5,000 in compute with LoRA and Nanonets' VLM fine-tuning guide targeting 10,000–100,000 total training samples. Glassdoor + 7
Cost component10 SOPs (pilot)100 SOPs (mid)1,000 SOPs (large)DEVELOPMENT — one-timeImage-text pairs needed3,000–8,00025,000–50,000100,000–200,000Annotation labor (hrs)¹60–150500–1,0002,000–4,000ML engineer hrs (data pipeline, training, eval, iteration)²250–450800–1,5002,500–5,000Training GPU type1× RTX 40901–2× A100 80GB4–8× H100 (cluster)Training GPU-hours (across ~5–15 runs)³20–50120–300600–1,800Engineer payroll @ $85/hr$21K–$38K$68K–$128K$213K–$425KAnnotation cost ($25–30/hr in-house, or $0.50–2/image outsourced)$1.5K–$8K$13K–$50K$50K–$200KTraining compute (cloud spot equivalent: 4090 $0.55/hr, A100 $1.07/hr, H100 $2.49/hr⁴)$15–$50$130–$750$1,500–$9,000Dev subtotal$23K–$46K$82K–$179K$265K–$634KLOCAL DEPLOYMENT — one-time hardwareInference GPU(s) + server1× RTX 4090 workstation ~$3K–$5K1× A100 80GB or 2× L40S server ~$15K–$30K4–8× H100 cluster ~$150K–$400KDEPLOYMENT — annual recurringGPU power draw (TDP × 24/7)450 W~1,400 W (2 GPUs)~5.6 kW (8× 700W)Electricity kWh/yr (PUE 1.4)~5,500~17,200~68,700Energy cost @ $0.12/kWh~$660/yr~$2,100/yr~$8,200/yrMaintenance / MLOps engineer hrs/yr⁵60–120200–400800–1,500Maintenance payroll @ $85/hr$5K–$10K$17K–$34K$68K–$128KAnnual deployment subtotal~$6K–$11K~$19K–$36K~$76K–$136K
Notes on the ranges:
¹ Annotation throughput of ~50 images/hour for moderate-complexity image-text pairs is consistent with the dataset-size guidance in the sources above; teams cut this dramatically with auto-labeling (e.g., NVIDIA's Project Hafnia compressed 750,000 hours of manual labeling to 10,000 hours using embedding-based curation + AI-driven annotation). Milestone Systems
² The engineer-hour figures combine data engineering, training-script setup, evaluation harness, and iteration. These are my project-scoping estimates extrapolated from the workflow described in the Spheron 2026 guide ("collect 500–10,000 high-quality examples", configure hyperparameters, monitor loss, evaluate, merge adapters, deploy) — not a direct citation, since published per-project labor data for VLM fine-tuning is scarce. Spheron
³ Training GPU-hour basis: the most directly comparable published benchmark is Park et al. (PMC 2025), which fine-tuned five open-source VLMs (Llama-3.2-Vision, Qwen2-VL, Qwen2.5-VL, LLaVA-1.6, Gemma-3) on 1,000 annotated frames using QLoRA + Unsloth on a single RTX 4090. Scaling roughly with dataset size and number of tuning runs gives the ranges above. nih
⁴ Cloud GPU pricing per Spheron's April 2026 multi-provider survey: H100 from $1.03/hr, A100 80GB $1.07/hr on-demand and $0.60/hr spot, RTX 4090 from $0.31–0.55/hr. If you train on owned hardware, substitute amortized capex + electricity instead. Spheron
⁵ Maintenance hours scale with the number of GPUs, not directly with SOPs; Spheron's 2026 economics model assigns one infrastructure engineer (~$200K/yr) across roughly 8–128 GPUs depending on team maturity. Spheron
Two structural caveats worth naming: first, the development subtotal is dominated by labor, not compute — the much-discussed "GPU bill" for LoRA fine-tuning is typically <5% of project cost at every scale here. Second, at 1,000 SOPs you cross the threshold where local deployment economics start to compete with cloud inference; the break-even quoted by gpucost.org puts H100 break-even around 10,000 hours of usage versus $3/hr rental, which a single inference workload reaches in 14 months of 24/7 uptime.

## Root cause for the cost

@TODO VLM does not recognize domain specific objects, such as medical device, HVAC parts, auto parts, technicians' tools etc.

Examples are 
'doc/img/VLM-identify-pen.pgn'
Fig 1. VLM can identify common objects like this pen

'doc/img/VLM-identify-cuff-failed.png'
Fig 2. VLM cannot identify the cuff of a blood pressure measurement device. On the text window, VLM referred the cuff as 'a black object' and VLM cannot learn this cuff online. It needs fine-tuning and high price tag to recognize this new object.

## Potential saving: Hybrid approach with a Rule Engine

@TODO the key idea is to shift fine tuning on new objects to Yolo. Yolo models are 10MB to 100MB level, comparing to commond VLM models in the range of 1GB to 144GB level. 

We can easily train and run Yolo models on a laptop, so that cost is minimal. 


@TODO put this table to appendix
| Model family               |        Common parameter sizes |          Approx disk size, FP16 |             Approx disk size, Q4 |                                                                                                                                                    Practical local memory |
| -------------------------- | ----------------------------: | ------------------------------: | -------------------------------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
| **SmolVLM**                |              256M, 500M, 2.2B |         ~0.5 GB, ~1 GB, ~4.4 GB |      ~0.13 GB, ~0.25 GB, ~1.1 GB |                                                                               256M can run under ~1 GB GPU RAM for one image; 2.2B around several GB. ([Hugging Face][1]) |
| **FastVLM**                |                0.5B, 1.5B, 7B |            ~1 GB, ~3 GB, ~14 GB |      ~0.25 GB, ~0.75 GB, ~3.5 GB | 0.5B/1.5B suitable for Mac mini-class demos; 7B better for Mac with larger unified memory or PC GPU. Apple lists FastVLM 0.5B, 1.5B, and 7B variants. ([Hugging Face][2]) |
| **Qwen2.5-VL**             |                   3B, 7B, 72B |          ~6 GB, ~14 GB, ~144 GB |         ~1.5 GB, ~3.5 GB, ~36 GB |                                            3B/7B are realistic local candidates; 72B is server-grade. vLLM notes that context length strongly affects memory. ([vLLM][3]) |
| **Phi-3.5 Vision**         |                          4.2B |                         ~8.4 GB |                          ~2.1 GB |                                                                                   Usually needs around 8–14 GB practical runtime memory depending on backend and context. |
| **LLaVA 1.5 / LLaVA-NeXT** |            7B, 13B, 34B, 110B | ~14 GB, ~26 GB, ~68 GB, ~220 GB | ~3.5 GB, ~6.5 GB, ~17 GB, ~55 GB |                                                                                              7B is local-workstation friendly; 13B+ needs more memory; 34B+ server-grade. |
| **MiniCPM-V**              |                           ~8B |                          ~16 GB |                            ~4 GB |                                                                                                           Good 7B/8B-class local VLM, but needs a stronger local machine. |
| **InternVL**               |     1B, 2B, 8B, 14B, 38B, 78B |                ~2 GB to ~156 GB |                ~0.5 GB to ~39 GB |                                                                                                                       Small variants are local; 38B/78B are server-grade. |
| **Molmo**                  | 1B active / 7B total, 7B, 72B |  ~14 GB for 7B, ~144 GB for 72B |   ~3.5 GB for 7B, ~36 GB for 72B |                                                                                                                             7B is local workstation; 72B is server-grade. |

[1]: https://huggingface.co/HuggingFaceTB/SmolVLM-256M-Instruct?utm_source=chatgpt.com "HuggingFaceTB/SmolVLM-256M-Instruct"
[2]: https://huggingface.co/apple/FastVLM-0.5B?utm_source=chatgpt.com "apple/FastVLM-0.5B"
[3]: https://docs.vllm.ai/projects/recipes/en/latest/Qwen/Qwen2.5-VL.html?utm_source=chatgpt.com "Qwen2.5-VL Usage Guide - vLLM Recipes"



@TODO list saving estimation with Hybrid Approach from ChatGPT and Claude
@TODO from ChatGPT

Table 1: Adjusted Development / Onboarding Cost
Mode	Scope	Domain Expert Hours	Domain Expert Cost at $64/hr	Senior AI Engineer Hours	Senior AI Engineer Cost
Full Local	10 SOP workflows	160–320 h	$10.2k–$20.5k	0 h	$0
Full Local	100 SOP workflows	1,200–2,400 h	$76.8k–$153.6k	0 h	$0
Hybrid Cloud VLM	10 SOP workflows	120–240 h	$7.7k–$15.4k	0 h	$0
Hybrid Cloud VLM	100 SOP workflows	800–1,600 h	$51.2k–$102.4k	0 h	$0
Why Full Local has slightly higher Domain Expert time: smaller local VLMs may need more explicit object tags, more YOLO labeling, more SOUP rules, and more manual evaluation because the VLM is weaker than a cloud model. Hybrid Cloud VLM should need fewer compensating rules because the cloud VLM can usually understand human action and scene context better.

| Mode                 |                 Scope | Main Approach                                                           | Onboarding Labor Cost |                            Training GPU / Fine-tuning Cost | Local Hardware                                   |       Token Cost |  Energy / Month | Maintenance Hours / Month | Maintenance Cost / Month |
| -------------------- | --------------------: | ----------------------------------------------------------------------- | --------------------: | ---------------------------------------------------------: | ------------------------------------------------ | ---------------: | --------------: | ------------------------: | -----------------------: |
| **Full Local**       |  **10 SOP workflows** | YOLO + SOUP RuleEngine + local FastVLM/small VLM                        |     **$10.2k–$20.5k** |          **$0 VLM fine-tune**; optional YOLO training only | **2–3× Mac mini-level nodes** ≈ **$1.2k–$4.2k**  |           **$0** |  **~$8–$12/mo** |             **6–12 h/mo** |         **$384–$768/mo** |
| **Full Local**       | **100 SOP workflows** | More YOLO labels/rules; local VLM used for general action understanding |    **$76.8k–$153.6k** | **$0 VLM fine-tune**; optional YOLO retraining cycles only | **4–8× Mac mini-level nodes** ≈ **$2.4k–$11.2k** |           **$0** | **~$16–$40/mo** |            **16–40 h/mo** |     **$1,024–$2,560/mo** |
| **Hybrid Cloud VLM** |  **10 SOP workflows** | Local YOLO + SOUP RuleEngine; cloud VLM for action/scene reasoning      |      **$7.7k–$15.4k** |          **$0 VLM fine-tune**; optional YOLO training only | **1× Mac mini/PC** ≈ **$600–$1.4k**              |   **~$5–$50/mo** |   **~$2–$5/mo** |              **4–8 h/mo** |         **$256–$512/mo** |
| **Hybrid Cloud VLM** | **100 SOP workflows** | Local YOLO grounding + cloud VLM reasoning + SOUP validation            |    **$51.2k–$102.4k** | **$0 VLM fine-tune**; optional YOLO retraining cycles only | **1–2× Mac mini/PC** ≈ **$600–$2.8k**            | **~$50–$500/mo** |  **~$2–$10/mo** |            **10–24 h/mo** |       **$640–$1,536/mo** |


@TODO estimation from Claude


## SOUP Engine Data Workflow

The hybrid design in shown in 

@TODO: add this image
`doc/img/SOUP-dataflow-glass3.png`

@TODO: improve this description

**Training time.** The system starts by collecting domain-specific training videos and extracting representative frames. Users label important objects with task-specific tags, such as `cuff`, `sleeve`, `upper_arm`, `BP monitor`, or factory components like connectors, cables, and tools. These labels are used to train a YOLO model that specializes in recognizing objects that a general VLM may not understand reliably. The workflow is iterative: label images, train YOLO, test detection quality, review errors, add more labeled examples, and retrain. Over time, the YOLO model becomes a domain-specific visual detector that can ground objects precisely with bounding boxes and class names.

**Runtime phase.** The trained YOLO model is deployed inside the macOS app. During live video, the app samples frames and sends them through YOLO to detect domain objects and produce bounding boxes, labels, and confidence scores. These annotations are overlaid on the video and also passed to the VLM as structured context. The VLM can understand human actions and general scene meaning, but it may describe specialized objects vaguely, such as calling a cuff or factory component “a black object.” The SOUP rule engine merges both sources: YOLO provides object identity and location, while the VLM provides action understanding. The engine then compares this combined evidence against the `.soup` SOP definition and outputs step-by-step feedback.

## SOUP Engine Architecture 

@TODO Show this architecture image and explain
'doc/img/SOUP-engine-archtecture-GPT1.png' 

Below is a concise layer-by-layer architecture description based on your diagram text.

Consumer Layer
The Consumer Layer contains all user-facing or integration-facing entry points. FaceBoxDemo provides a Swift-based application interface, while CLI tools support Python-based command-line workflows. External apps and integration tests can also call the system through Python imports. This layer should stay lightweight and should not contain core rule logic. Its role is to collect inputs, trigger evaluations, and display results.

Public API Layer
The Public API Layer exposes the stable interface of the sopilot_rules package. Users import RuleEngine, load_soup, validate_soup, and schema types such as Detection, Event, and RunResult. This layer hides internal implementation details and gives downstream apps a clean contract. It is mainly implemented through __init__.py and schema.py.

Engine / Orchestration Layer
The Engine Layer is centered on RuleEngine. It receives detections and events, normalizes them, evaluates rules in the configured order, fills missing required steps, computes the final status, and produces a RunResult. It also builds evidence references and privacy logs. This is the main orchestration layer that turns raw observations into structured SOP evaluation results.

Rule Evaluator Layer
The Rule Evaluator Layer dispatches each rule to a typed evaluator through a registry. Rule types include exists_before, near_before, overlap, above, after_all_required, and any_of. Each evaluator receives an EvaluationContext containing detections, events, prior results, and configuration. This makes the rule system extensible: new rule types can be added without changing the main engine.

Schema / Contract Layer
The Schema Layer defines the core data contracts used across the system. Important models include SoupPackage, Detection, Event, RunResult, StepResult, EvidenceRef, PrivacyLog, and BBox. These models provide type safety, validation, and consistent data structure for all layers. A strict schema layer is especially important because detections, VLM outputs, and UI events may come from different sources.

Support Services Layer
The Support Services Layer provides reusable utilities used by the engine and rule evaluators. The normalizer validates and sorts detections/events. The evidence module builds references from rule results. The privacy module classifies local versus cloud VLM usage. The geometry module handles bounding-box operations such as IoU, center point, area, and relative position checks like above.

Input / I/O Layer
The Input / I/O Layer handles external data entering the system. It loads .soup.json SOP definitions, receives detection streams from YOLO or VLM outputs, and accepts event streams from UI, sensors, or device APIs. The loader converts raw JSON into validated SoupPackage objects. This layer separates raw file/data ingestion from the rule engine’s internal logic.

## SOUP Engine Details: Object Relationships
@TODO we often need to 

## SOUP Package Design



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



## SOUP Engine Architecture 
Below is a concise layer-by-layer architecture description based on your diagram text. 

**Consumer Layer**
The Consumer Layer contains all user-facing or integration-facing entry points. `FaceBoxDemo` provides a Swift-based application interface, while CLI tools support Python-based command-line workflows. External apps and integration tests can also call the system through Python imports. This layer should stay lightweight and should not contain core rule logic. Its role is to collect inputs, trigger evaluations, and display results.

**Public API Layer**
The Public API Layer exposes the stable interface of the `sopilot_rules` package. Users import `RuleEngine`, `load_soup`, `validate_soup`, and schema types such as `Detection`, `Event`, and `RunResult`. This layer hides internal implementation details and gives downstream apps a clean contract. It is mainly implemented through `__init__.py` and `schema.py`.

**Engine / Orchestration Layer**
The Engine Layer is centered on `RuleEngine`. It receives detections and events, normalizes them, evaluates rules in the configured order, fills missing required steps, computes the final status, and produces a `RunResult`. It also builds evidence references and privacy logs. This is the main orchestration layer that turns raw observations into structured SOP evaluation results.

**Rule Evaluator Layer**
The Rule Evaluator Layer dispatches each rule to a typed evaluator through a registry. Rule types include `exists_before`, `near_before`, `overlap`, `above`, `after_all_required`, and `any_of`. Each evaluator receives an `EvaluationContext` containing detections, events, prior results, and configuration. This makes the rule system extensible: new rule types can be added without changing the main engine.

**Schema / Contract Layer**
The Schema Layer defines the core data contracts used across the system. Important models include `SoupPackage`, `Detection`, `Event`, `RunResult`, `StepResult`, `EvidenceRef`, `PrivacyLog`, and `BBox`. These models provide type safety, validation, and consistent data structure for all layers. A strict schema layer is especially important because detections, VLM outputs, and UI events may come from different sources.

**Support Services Layer**
The Support Services Layer provides reusable utilities used by the engine and rule evaluators. The normalizer validates and sorts detections/events. The evidence module builds references from rule results. The privacy module classifies local versus cloud VLM usage. The geometry module handles bounding-box operations such as IoU, center point, area, and relative position checks like `above`.

**Input / I/O Layer**
The Input / I/O Layer handles external data entering the system. It loads `.soup.json` SOP definitions, receives detection streams from YOLO or VLM outputs, and accepts event streams from UI, sensors, or device APIs. The loader converts raw JSON into validated `SoupPackage` objects. This layer separates raw file/data ingestion from the rule engine’s internal logic.

