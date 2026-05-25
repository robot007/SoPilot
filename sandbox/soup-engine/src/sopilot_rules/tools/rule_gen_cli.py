"""LLM-assisted rule generation CLI scaffold.

This tool is intentionally creator-time only. It validates generated JSON before
writing anything, and can also run as a prompt generator when no provider key is
available.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List

from pydantic import TypeAdapter

from sopilot_rules.schema import Rule


PROMPT_TEMPLATE = """You are a SOUP rule author.
Output only valid JSON with a top-level "rules" array.
Use only these rule types:
- exists_before
- near_before
- overlap
- above
- after_all_required
- any_of
- vlm_answer

Inside any_of conditions, use only:
- not_exists
- overlap

Use only these tags:
{tags}

Every rule must include id, step_id, type, and type-specific required fields.
Every any_of rule must include a non-empty conditions array.
Every vlm_answer rule must include event, question, and expected_answer.
Do not invent tags.
Do not invent rule types.
Do not include markdown.

SOP:
{sop_text}
"""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate SOUP rules from SOP text")
    parser.add_argument("--sop-text", required=True, help="Path to plain-language SOP text")
    parser.add_argument("--tags", required=True, help="Comma-separated allowed tags")
    parser.add_argument("--out", help="Output package or rules JSON path")
    parser.add_argument("--print-prompt", action="store_true", help="Print prompt and exit")
    parser.add_argument("--yes", action="store_true", help="Overwrite output without confirmation")
    args = parser.parse_args(argv)

    sop_text = Path(args.sop_text).read_text(encoding="utf-8")
    tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
    prompt = PROMPT_TEMPLATE.format(tags=json.dumps(tags), sop_text=sop_text)

    if args.print_prompt or "OPENROUTER_API_KEY" not in os.environ:
        print(prompt)
        return 0

    try:
        generated = _call_openrouter(prompt)
        _validate_generated_rules(generated, tags)
    except Exception as exc:
        print("rule generation failed: %s" % exc, file=sys.stderr)
        return 1

    if not args.out:
        print(json.dumps(generated, indent=2, sort_keys=True))
        return 0

    out_path = Path(args.out)
    if out_path.exists() and not args.yes:
        response = input("Overwrite %s? [y/N] " % out_path)
        if response.strip().lower() != "y":
            print("aborted")
            return 1
    out_path.write_text(json.dumps(generated, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def _validate_generated_rules(generated, allowed_tags: List[str]) -> None:
    if not isinstance(generated, dict) or "rules" not in generated:
        raise ValueError("generated output must be an object with a rules array")
    adapter = TypeAdapter(List[Rule])
    rules = adapter.validate_python(generated["rules"])
    allowed = set(allowed_tags)
    ids = set()
    for rule in rules:
        if rule.id in ids:
            raise ValueError("duplicate rule id %s" % rule.id)
        ids.add(rule.id)
        for tag in _tag_refs(rule):
            if tag not in allowed:
                raise ValueError("unknown tag %s" % tag)


def _tag_refs(rule):
    refs = []
    for field_name in ("tag", "source_tag", "target_tag"):
        value = getattr(rule, field_name, None)
        if value:
            refs.append(value)
    for condition in getattr(rule, "conditions", []):
        refs.extend(_tag_refs(condition))
    return refs


def _call_openrouter(prompt: str):
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("requests is required for live OpenRouter calls") from exc

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": "Bearer %s" % os.environ["OPENROUTER_API_KEY"]},
        json={
            "model": os.environ.get("SOPILOT_RULE_GEN_MODEL", "openai/gpt-4o"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        },
        timeout=60,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return json.loads(content)


if __name__ == "__main__":
    raise SystemExit(main())
