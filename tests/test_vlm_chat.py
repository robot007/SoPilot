# Copyright (c) 2026 webAI, Inc.
"""Tests for local VLM chat frame handling."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageOps

from yolo26mlx.vlm.chat import (
    VLMChatError,
    VIDEO_CONTEXT_PREFIX,
    build_visual_context_image,
    validate_frame_paths,
)
from yolo26mlx.vlm.cli import build_parser


def _write_frame(path: Path, color: tuple[int, int, int]) -> None:
    Image.new("RGB", (80, 60), color).save(path)


def test_validate_frame_paths_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(VLMChatError, match="Frame file was not found"):
        validate_frame_paths([tmp_path / "missing.jpg"])


def test_build_visual_context_image_returns_single_image_unchanged(tmp_path: Path) -> None:
    frame = tmp_path / "frame.jpg"
    _write_frame(frame, (255, 0, 0))

    image = build_visual_context_image(
        [frame],
        image_type=Image,
        image_draw_type=ImageDraw,
        image_ops_type=ImageOps,
    )

    assert image.size == (80, 60)


def test_build_visual_context_image_creates_time_ordered_contact_sheet(tmp_path: Path) -> None:
    frames = []
    for index, color in enumerate([(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]):
        frame = tmp_path / f"frame-{index}.jpg"
        _write_frame(frame, color)
        frames.append(frame)

    image = build_visual_context_image(
        frames,
        image_type=Image,
        image_draw_type=ImageDraw,
        image_ops_type=ImageOps,
    )

    assert image.size == (1152, 644)
    assert image.getbbox() is not None


def test_chat_parser_accepts_repeated_frame_files() -> None:
    args = build_parser().parse_args(
        [
            "chat",
            "fastvlm_0_5b",
            "--frame-file",
            "a.jpg",
            "--frame-file",
            "b.jpg",
            "--prompt",
            "What changed?",
        ]
    )

    assert args.image_file is None
    assert args.frame_file == ["a.jpg", "b.jpg"]
    assert args.prompt == "What changed?"


def test_video_context_prompt_is_explicit() -> None:
    assert "time-ordered contact sheet" in VIDEO_CONTEXT_PREFIX
    assert "oldest to newest" in VIDEO_CONTEXT_PREFIX
