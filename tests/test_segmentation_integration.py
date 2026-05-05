# Copyright (c) 2026 webAI, Inc.
"""Integration tests for segmentation pipeline.

Tests model building from YAML, inference with random weights, CLI parsing,
and training loop with COCO128-seg.

Run:
    python -m pytest tests/test_segmentation_integration.py -v
"""

from pathlib import Path

import numpy as np
import pytest

mx = pytest.importorskip("mlx.core", reason="MLX requires Apple Silicon")

from yolo26mlx.nn.modules.head import Segment26
from yolo26mlx.nn.tasks import build_model

PACKAGE_DIR = Path(__file__).resolve().parent.parent / "src" / "yolo26mlx"
SEG_YAML = PACKAGE_DIR / "cfg" / "models" / "26" / "yolo26-seg.yaml"


# ---------------------------------------------------------------------------
# Model building from YAML
# ---------------------------------------------------------------------------


class TestModelBuild:
    """Verify segmentation model builds from YAML config."""

    def test_build_nano_seg(self):
        """Build yolo26n-seg from YAML with scale=n."""
        model = build_model(str(SEG_YAML), ch=3, nc=80, verbose=False, scale="n")
        mx.eval(model.parameters())
        assert model is not None

        head = model.model.layers[-1]
        assert isinstance(head, Segment26), f"Last layer is {type(head)}, expected Segment26"
        assert head.nm == 32
        # nano scale: width=0.25, npr=int(256*0.25)=64
        assert head.npr == 64

    def test_build_large_seg(self):
        """Build yolo26l-seg from YAML with scale=l."""
        model = build_model(str(SEG_YAML), ch=3, nc=80, verbose=False, scale="l")
        mx.eval(model.parameters())

        head = model.model.layers[-1]
        assert isinstance(head, Segment26)
        assert head.nm == 32
        assert head.npr == 256

    def test_build_all_scales(self):
        """All five scales should build without error."""
        for scale in ["n", "s", "m", "l", "x"]:
            model = build_model(str(SEG_YAML), ch=3, nc=80, verbose=False, scale=scale)
            mx.eval(model.parameters())
            head = model.model.layers[-1]
            assert isinstance(head, Segment26), f"scale={scale}: last layer not Segment26"


# ---------------------------------------------------------------------------
# Forward pass with random weights
# ---------------------------------------------------------------------------


class TestModelForward:
    """Verify forward pass produces expected output format."""

    @pytest.fixture()
    def model(self):
        m = build_model(str(SEG_YAML), ch=3, nc=80, verbose=False, scale="n")
        mx.eval(m.parameters())
        return m

    def test_inference_output_format(self, model):
        """Inference should return (det_mc, protos) tuple."""
        model.eval()
        img = mx.random.normal((1, 640, 640, 3))
        out = model(img)
        assert isinstance(out, tuple), f"Expected tuple, got {type(out)}"
        det_mc, protos = out
        mx.eval(det_mc, protos)

        assert det_mc.ndim == 3
        assert det_mc.shape[0] == 1
        assert det_mc.shape[1] == 300  # max_det
        assert det_mc.shape[2] == 6 + 32  # det + mask coeffs

        assert protos.ndim == 4
        assert protos.shape[0] == 1
        assert protos.shape[-1] == 32  # nm

    def test_training_output_format(self, model):
        """Training should return (dict_with_keys, proto_raw)."""
        model.train()
        img = mx.random.normal((1, 640, 640, 3))
        out = model(img)
        assert isinstance(out, tuple)
        preds, proto_raw = out
        assert isinstance(preds, dict)
        assert "one2many" in preds
        assert "one2one" in preds
        assert "mask_coeff" in preds
        assert "proto" in preds

    def test_batch_size_2(self, model):
        """Forward pass should work with batch size > 1."""
        model.eval()
        img = mx.random.normal((2, 640, 640, 3))
        out = model(img)
        det_mc, protos = out
        mx.eval(det_mc, protos)
        assert det_mc.shape[0] == 2
        assert protos.shape[0] == 2


# ---------------------------------------------------------------------------
# YOLO API
# ---------------------------------------------------------------------------


class TestYOLOAPI:
    """Verify high-level YOLO class with segmentation."""

    def test_build_from_yaml(self):
        """YOLO should build a segmentation model from YAML."""
        from yolo26mlx.engine.model import YOLO

        model = YOLO(str(SEG_YAML), task="segment", verbose=False)
        assert model.task == "segment"
        assert model.model is not None

    def test_auto_detect_task(self):
        """Task should be auto-detected from -seg in filename."""
        from yolo26mlx.engine.model import YOLO

        model = YOLO(str(SEG_YAML), verbose=False)
        assert model.task == "segment"

    def test_predict_with_random_weights(self, tmp_path):
        """predict() should return Results with masks when using seg model."""
        from yolo26mlx.engine.model import YOLO

        model = YOLO(str(SEG_YAML), task="segment", verbose=False)

        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        from PIL import Image

        img_path = tmp_path / "test_img.jpg"
        Image.fromarray(img).save(str(img_path))

        results = model.predict(str(img_path), conf=0.001)
        assert results is not None
        assert len(results) > 0
        r = results[0]
        assert r.boxes is not None
        # With random weights, masks may or may not be populated
        # depending on whether any detection exceeds the threshold


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


class TestCLI:
    """Verify CLI parses segmentation-related flags."""

    def test_predict_with_task_segment(self):
        """--task segment should be parsed correctly."""
        from yolo26mlx.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(
            [
                "predict",
                "--model",
                "models/yolo26n-seg.npz",
                "--source",
                "images/test.jpg",
                "--task",
                "segment",
            ]
        )
        assert args.task == "segment"
        assert args.model == "models/yolo26n-seg.npz"

    def test_train_with_task_segment(self):
        """train subcommand should accept --task segment."""
        from yolo26mlx.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(
            [
                "train",
                "--model",
                "models/yolo26n-seg.npz",
                "--data",
                "coco128-seg",
                "--task",
                "segment",
                "--epochs",
                "2",
            ]
        )
        assert args.task == "segment"
        assert args.data == "coco128-seg"


# ---------------------------------------------------------------------------
# Dataset config
# ---------------------------------------------------------------------------


class TestDatasetConfig:
    """Verify segmentation dataset configs exist and are valid."""

    def test_coco128_seg_yaml_exists(self):
        """coco128-seg.yaml should exist in package cfg/datasets."""
        cfg_path = PACKAGE_DIR / "cfg" / "datasets" / "coco128-seg.yaml"
        assert cfg_path.exists(), f"Missing: {cfg_path}"

    def test_coco128_seg_yaml_content(self):
        """Config should have correct nc and download URL."""
        import yaml

        cfg_path = PACKAGE_DIR / "cfg" / "datasets" / "coco128-seg.yaml"
        with open(cfg_path) as f:
            cfg = yaml.safe_load(f)
        assert cfg["nc"] == 80
        assert "coco128-seg" in cfg.get("download", "")
        assert "names" in cfg
        assert len(cfg["names"]) == 80

    def test_seg_model_yaml_exists(self):
        """yolo26-seg.yaml should exist."""
        assert SEG_YAML.exists(), f"Missing: {SEG_YAML}"

    def test_seg_model_yaml_content(self):
        """Seg model YAML should have Segment26 in head."""
        import yaml

        with open(SEG_YAML) as f:
            cfg = yaml.safe_load(f)
        assert cfg["nc"] == 80

        head_layers = cfg.get("head", [])
        seg_layers = [layer for layer in head_layers if "Segment26" in str(layer)]
        assert len(seg_layers) > 0, "No Segment26 layer found in head"


# ---------------------------------------------------------------------------
# Weight converter patterns
# ---------------------------------------------------------------------------


class TestConverterPatterns:
    """Verify converter recognizes segmentation-specific weight names."""

    def test_proto_upsample_weight(self):
        from yolo26mlx.converters.convert import is_conv_transpose_weight

        assert is_conv_transpose_weight("model.23.proto.upsample.weight", (64, 64, 2, 2))

    def test_cv4_conv_weight(self):
        from yolo26mlx.converters.convert import is_conv_weight

        assert is_conv_weight("model.23.cv4.0.0.conv.weight", (32, 64, 3, 3))
        assert is_conv_weight("model.23.one2one_cv4.0.0.conv.weight", (32, 64, 3, 3))

    def test_semseg_bare_conv(self):
        from yolo26mlx.converters.convert import is_conv_weight

        assert is_conv_weight("model.23.proto.semseg.2.weight", (80, 128, 1, 1))

    def test_feat_refine_conv(self):
        from yolo26mlx.converters.convert import is_conv_weight

        assert is_conv_weight("model.23.proto.feat_refine.0.conv.weight", (64, 128, 1, 1))

    def test_feat_fuse_conv(self):
        from yolo26mlx.converters.convert import is_conv_weight

        assert is_conv_weight("model.23.proto.feat_fuse.conv.weight", (128, 64, 3, 3))
