# Copyright (c) 2026 webAI, Inc.
"""Local VLM image-question answering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from yolo26mlx.vlm.manager import ModelNotInstalledError, VLMModelManager

IMAGE_TOKEN_INDEX = -200
VIDEO_CONTEXT_PREFIX = (
    "This is a time-ordered contact sheet from recent video, oldest to newest. "
    "Use all frames to answer temporal questions.\n"
)


class VLMChatError(RuntimeError):
    """Raised when local VLM chat cannot produce an answer."""


@dataclass(frozen=True)
class VLMChatResult:
    model_id: str
    answer: str

    def to_dict(self) -> dict[str, Any]:
        return {"model_id": self.model_id, "answer": self.answer}


def answer_question(
    manager: VLMModelManager,
    model_id: str,
    image_path: Path | None,
    prompt: str,
    frame_paths: Sequence[Path] | None = None,
    max_new_tokens: int = 128,
) -> VLMChatResult:
    """Answer a question about one image or sampled recent-video frames."""
    model = manager.get_model(model_id)
    if not manager.is_installed(model_id):
        raise ModelNotInstalledError(f"Model is not installed: {model_id}")
    if model.id != "fastvlm_0_5b":
        raise VLMChatError(f"Chat is currently supported for FastVLM 0.5B, not {model.display_name}.")

    question = prompt.strip()
    if not question:
        raise VLMChatError("Question is empty.")

    frame_paths = list(frame_paths or [])
    if frame_paths:
        validated_paths = validate_frame_paths(frame_paths)
        model_prompt = VIDEO_CONTEXT_PREFIX + question
    elif image_path is not None:
        validated_paths = validate_frame_paths([image_path])
        model_prompt = question
    else:
        raise VLMChatError("No image or video frames were provided.")

    try:
        import torch
        from PIL import Image
        from PIL import ImageDraw
        from PIL import ImageOps
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except Exception as exc:  # pragma: no cover - depends on optional local runtime
        raise VLMChatError(
            "Local VLM chat dependencies are missing. Install the 'vlm' extra dependencies."
        ) from exc

    local_path = manager.model_path(model_id)
    device = _best_torch_device(torch)
    dtype = torch.float16 if device in {"cuda", "mps"} else torch.float32

    try:
        tokenizer = AutoTokenizer.from_pretrained(
            str(local_path),
            trust_remote_code=True,
            local_files_only=True,
        )
        vlm = AutoModelForCausalLM.from_pretrained(
            str(local_path),
            torch_dtype=dtype,
            trust_remote_code=True,
            local_files_only=True,
        )
        vlm.to(device)
        vlm.eval()

        visual_context = build_visual_context_image(
            validated_paths,
            image_type=Image,
            image_draw_type=ImageDraw,
            image_ops_type=ImageOps,
        )
        input_ids, attention_mask = _build_input_tensors(tokenizer, model_prompt, torch, device)
        pixel_values = _build_image_tensor(vlm, visual_context, device, dtype)

        with torch.no_grad():
            output = vlm.generate(
                inputs=input_ids,
                attention_mask=attention_mask,
                images=pixel_values,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                bos_token_id=_first_token_id(tokenizer.bos_token_id, vlm.config.bos_token_id),
                pad_token_id=_first_token_id(tokenizer.pad_token_id, tokenizer.eos_token_id),
            )
    except Exception as exc:
        raise VLMChatError(f"Local VLM inference failed: {exc}") from exc

    decoded = tokenizer.decode(output[0], skip_special_tokens=True)
    answer = _clean_answer(decoded, model_prompt)
    if not answer:
        raise VLMChatError("Local VLM returned an empty answer.")
    return VLMChatResult(model_id=model_id, answer=answer)


def validate_frame_paths(frame_paths: Sequence[Path]) -> list[Path]:
    if not frame_paths:
        raise VLMChatError("No image or video frames were provided.")

    validated_paths: list[Path] = []
    for frame_path in frame_paths:
        path = Path(frame_path).expanduser()
        if not path.is_file():
            raise VLMChatError(f"Frame file was not found: {path}")
        validated_paths.append(path)
    return validated_paths


def build_visual_context_image(
    frame_paths: Sequence[Path],
    image_type: Any,
    image_draw_type: Any,
    image_ops_type: Any,
    cell_size: tuple[int, int] = (384, 288),
    label_height: int = 34,
) -> Any:
    """Build one labeled image from one or more time-ordered frames."""
    validated_paths = validate_frame_paths(frame_paths)
    if len(validated_paths) == 1:
        with image_type.open(validated_paths[0]) as image:
            return image.convert("RGB").copy()

    columns = min(3, len(validated_paths))
    rows = (len(validated_paths) + columns - 1) // columns
    cell_width, image_height = cell_size
    cell_height = image_height + label_height
    sheet = image_type.new("RGB", (columns * cell_width, rows * cell_height), "white")
    draw = image_draw_type.Draw(sheet)

    for index, frame_path in enumerate(validated_paths):
        column = index % columns
        row = index // columns
        x = column * cell_width
        y = row * cell_height
        with image_type.open(frame_path) as frame:
            image = image_ops_type.contain(frame.convert("RGB"), cell_size)

        image_x = x + (cell_width - image.width) // 2
        image_y = y + label_height + (image_height - image.height) // 2
        sheet.paste(image, (image_x, image_y))

        label = f"Frame {index + 1}"
        if index == 0:
            label += " (oldest)"
        elif index == len(validated_paths) - 1:
            label += " (newest)"
        draw.text((x + 10, y + 9), label, fill=(0, 0, 0))

    return sheet


def _best_torch_device(torch_module: Any) -> str:
    if torch_module.cuda.is_available():
        return "cuda"
    if torch_module.backends.mps.is_available():
        return "mps"
    return "cpu"


def _build_input_tensors(tokenizer: Any, question: str, torch_module: Any, device: str) -> tuple[Any, Any]:
    rendered = tokenizer.apply_chat_template(
        [{"role": "user", "content": f"<image>\n{question}"}],
        add_generation_prompt=True,
        tokenize=False,
    )
    if "<image>" not in rendered:
        raise VLMChatError("Model chat template did not include the image placeholder.")

    prefix, suffix = rendered.split("<image>", 1)
    prefix_ids = tokenizer(prefix, return_tensors="pt", add_special_tokens=False).input_ids
    suffix_ids = tokenizer(suffix, return_tensors="pt", add_special_tokens=False).input_ids
    image_token = torch_module.tensor([[IMAGE_TOKEN_INDEX]], dtype=prefix_ids.dtype)
    input_ids = torch_module.cat([prefix_ids, image_token, suffix_ids], dim=1).to(device)
    attention_mask = torch_module.ones_like(input_ids, device=device)
    return input_ids, attention_mask


def _build_image_tensor(vlm: Any, image: Any, device: str, dtype: Any) -> Any:
    pixel_values = vlm.get_vision_tower().image_processor(
        images=image,
        return_tensors="pt",
    )["pixel_values"]
    return pixel_values.to(device=device, dtype=dtype)


def _first_token_id(*token_ids: int | None) -> int | None:
    for token_id in token_ids:
        if token_id is not None:
            return token_id
    return None


def _clean_answer(decoded: str, question: str) -> str:
    answer = decoded.strip()
    if question in answer:
        answer = answer.split(question, 1)[-1].strip()
    for prefix in ["assistant\n", "assistant:", "Assistant:", "ASSISTANT:"]:
        if answer.startswith(prefix):
            answer = answer[len(prefix) :].strip()
    return answer
