# Copyright (c) 2026 webAI, Inc.
"""JSON CLI used by the macOS app to manage local VLM models."""

from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import json
import sys
from pathlib import Path
from typing import Any

from yolo26mlx.vlm.manager import (
    VLMModelManager,
    VLMModelManagerError,
)
from yolo26mlx.vlm.chat import VLMChatError, answer_question

_PROTOCOL_STDOUT = sys.stdout


def _write_json(payload: dict[str, Any]) -> None:
    _PROTOCOL_STDOUT.write(json.dumps(payload, separators=(",", ":")) + "\n")
    _PROTOCOL_STDOUT.flush()


def _manager(args: argparse.Namespace) -> VLMModelManager:
    app_support_dir = Path(args.app_support_dir).expanduser() if args.app_support_dir else None
    return VLMModelManager(app_support_dir=app_support_dir)


def _cmd_list(args: argparse.Namespace) -> int:
    _write_json(_manager(args).list_models())
    return 0


def _cmd_download(args: argparse.Namespace) -> int:
    _write_json(_manager(args).download_model(args.model_id))
    return 0


def _cmd_activate(args: argparse.Namespace) -> int:
    _write_json(_manager(args).activate_model(args.model_id))
    return 0


def _cmd_delete(args: argparse.Namespace) -> int:
    _write_json(_manager(args).delete_model(args.model_id))
    return 0


def _cmd_download_status(args: argparse.Namespace) -> int:
    _write_json(_manager(args).get_download_status(args.model_id))
    return 0


def _cmd_chat(args: argparse.Namespace) -> int:
    image_path = Path(args.image_file).expanduser() if args.image_file else None
    frame_paths = [Path(path).expanduser() for path in args.frame_file]
    system_prompt = _resolve_system_prompt(args.system_prompt, args.system_prompt_file)
    result = answer_question(
        _manager(args),
        model_id=args.model_id,
        image_path=image_path,
        prompt=args.prompt,
        system_prompt=system_prompt,
        frame_paths=frame_paths,
        max_new_tokens=args.max_new_tokens,
    )
    _write_json(result.to_dict())
    return 0


def _resolve_system_prompt(system_prompt: str | None, system_prompt_file: str | None) -> str | None:
    parts: list[str] = []
    if system_prompt_file:
        path = Path(system_prompt_file).expanduser()
        if not path.is_file():
            raise VLMChatError(f"System prompt file was not found: {path}")
        parts.append(path.read_text(encoding="utf-8"))
    if system_prompt:
        parts.append(system_prompt)

    combined = "\n\n".join(part.strip() for part in parts if part.strip()).strip()
    return combined or None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vlm-model-manager",
        description="Manage FaceBoxDemo local VLM model downloads.",
    )
    parser.add_argument(
        "--app-support-dir",
        default=None,
        help="Override Application Support directory. Intended for tests.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_cmd = subparsers.add_parser("list", help="List local VLM models.")
    list_cmd.set_defaults(func=_cmd_list)

    download_cmd = subparsers.add_parser("download", help="Download a fixed registry model.")
    download_cmd.add_argument("model_id")
    download_cmd.set_defaults(func=_cmd_download)

    activate_cmd = subparsers.add_parser("activate", help="Activate an installed model.")
    activate_cmd.add_argument("model_id")
    activate_cmd.set_defaults(func=_cmd_activate)

    delete_cmd = subparsers.add_parser("delete", help="Delete local model files.")
    delete_cmd.add_argument("model_id")
    delete_cmd.set_defaults(func=_cmd_delete)

    status_cmd = subparsers.add_parser("download-status", help="Read download status.")
    status_cmd.add_argument("model_id")
    status_cmd.set_defaults(func=_cmd_download_status)

    chat_cmd = subparsers.add_parser("chat", help="Ask the active local VLM about an image.")
    chat_cmd.add_argument("model_id")
    chat_cmd.add_argument("--image-file")
    chat_cmd.add_argument("--frame-file", action="append", default=[])
    chat_cmd.add_argument("--prompt", required=True)
    chat_cmd.add_argument("--system-prompt")
    chat_cmd.add_argument("--system-prompt-file")
    chat_cmd.add_argument("--max-new-tokens", type=int, default=128)
    chat_cmd.set_defaults(func=_cmd_chat)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        with redirect_stdout(sys.stderr):
            return args.func(args)
    except VLMModelManagerError as exc:
        _write_json({"ok": False, "error": str(exc), "error_type": type(exc).__name__})
        return 1
    except Exception as exc:
        _write_json({"ok": False, "error": str(exc), "error_type": type(exc).__name__})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
