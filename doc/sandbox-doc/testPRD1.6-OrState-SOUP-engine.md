# Plan: Add OR Condition for S1 Roll Sleeve

## Summary
Update S1 so it passes when either condition is true:

```text
S1 passes if:
1. no sleeve is detected
OR
2. sleeve overlaps / is on upper_arm
```

Do not add `sleeve_rollup`. Keep the current four tags:

```text
blood_pressure_monitor
cuff
upper_arm
sleeve
```

## Key Changes
- Add a new composite rule type to the SOUP engine:
  ```json
  {
    "type": "any_of",
    "conditions": [...]
  }
  ```
- Add two condition types under `any_of`:
  ```json
  {"type": "not_exists", "tag": "sleeve", "min_confidence": 0.5}
  ```
  and:
  ```json
  {
    "type": "overlap",
    "source_tag": "sleeve",
    "target_tag": "upper_arm",
    "min_overlap_ratio": 0.25
  }
  ```

- Change S1 in `bp_monitor.soup.json` from the current `above` rule to:
  ```json
  {
    "id": "S1_sleeve_clear_or_on_upper_arm",
    "step_id": "S1",
    "type": "any_of",
    "conditions": [
      {
        "id": "S1_no_sleeve_detected",
        "type": "not_exists",
        "tag": "sleeve",
        "min_confidence": 0.5
      },
      {
        "id": "S1_sleeve_on_upper_arm",
        "type": "overlap",
        "source_tag": "sleeve",
        "target_tag": "upper_arm",
        "min_overlap_ratio": 0.25,
        "min_confidence": 0.5
      }
    ],
    "failure_message": "The sleeve was detected but did not appear to be clear of or on the upper arm."
  }
  ```

## Engine Behavior
- `any_of` returns `passed` if any child condition passes.
- `any_of` returns `failed` if all child conditions fail.
- `any_of` returns `uncertain` if no child passes and at least one child is uncertain.
- `not_exists` returns:
  - `passed` when no `sleeve` detection meets `min_confidence`
  - `failed` when a `sleeve` detection meets `min_confidence`
  - `uncertain` when only low-confidence sleeve evidence exists
- S1 completion time should be the earliest passing condition evidence timestamp when available; for `not_exists`, use `None` because absence has no frame timestamp.

## Fixture Updates
- `all_pass.json`: make S1 pass through `sleeve` overlapping `upper_arm`.
- Add or revise a fixture where no `sleeve` detection exists and S1 passes.
- `sleeve_not_rolled.json`: sleeve is detected but does not overlap `upper_arm`, so S1 fails.
- `missing_sleeve.json`: update expected outcome from `needs_review` to `passed`, because no sleeve detected is now valid.
- Keep S2, S3, and S4 behavior unchanged.

## Test Plan
- Add schema tests for valid and invalid `any_of` rules.
- Add unit tests for `not_exists`:
  - no sleeve detected -> passed
  - sleeve detected above threshold -> failed
  - only low-confidence sleeve -> uncertain
- Add unit tests for `any_of`:
  - one child passes -> passed
  - all children fail -> failed
  - no pass and one uncertain -> uncertain
- Update BP integration tests for the new S1 outcomes.
- Run:
  ```bash
  PYTHONPATH=sandbox/soup-engine/src python3 -m sopilot_rules.tools.validate_soup sandbox/soup-engine/tests/fixtures/bp/bp_monitor.soup.json
  PYTHONPATH=sandbox/soup-engine/src python3 -m unittest discover -s sandbox/soup-engine/tests -p 'test_*.py'
  ```

## Assumptions
- “No sleeve detected” is a valid pass condition for S1.
- “Sleeve on upper_arm” means bbox overlap between `sleeve` and `upper_arm`.
- The tag list remains exactly the four existing tags.
- This change should be implemented generically as reusable `any_of` / `not_exists` rule support, not as a BP-only hardcoded special case.
