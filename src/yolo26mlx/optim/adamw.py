# Copyright (c) 2026 webAI, Inc.
# Ultralytics 🚀 AGPL-3.0 License - https://ultralytics.com/license
"""
AdamW Optimizer for MLX — matches Ultralytics' ``optimizer='auto'`` short-run choice.

When PyTorch Ultralytics resolves ``optimizer='auto'`` with
``iterations <= 10000`` (the typical fine-tuning regime), it builds **AdamW**
with ``lr_fit = round(0.002 * 5 / (4 + nc), 6)`` and momentum=0.9 →
``betas=(0.9, 0.999)``, with weight_decay applied only to "regular weight"
params and zero on biases / norm layers (see
``ultralytics/engine/trainer.py:build_optimizer``).

This wrapper exposes the same ``step(model, grads)`` /
``learning_rate`` / ``momentum`` / ``state`` / ``set_lr_scale`` surface as
``MuSGD`` so that ``Trainer`` can swap the two without changing the warmup,
LR schedule, gradient clipping, or EMA paths.
"""

import re

import mlx.core as mx
from mlx.utils import tree_flatten, tree_unflatten


class AdamW:
    """AdamW optimizer with Ultralytics-style per-group weight decay.

    Mirrors PyTorch ``torch.optim.AdamW`` semantics with two weight-decay
    groups (``decay`` for weights, ``0.0`` for biases / BN / running buffers),
    so the per-step magnitude on pretrained weights matches what
    ``ultralytics.YOLO.train(optimizer='auto', ...)`` produces on short
    fine-tuning runs.

    Args:
        model: MLX nn.Module whose parameters to optimize.
        lr: Base learning rate (typically ``0.002 * 5 / (4 + nc)``).
        betas: AdamW betas (default ``(0.9, 0.999)``).
        eps: Numerical stability term (default ``1e-8``).
        weight_decay: Decay coefficient applied only to "weight" param group
            (matches PyTorch's per-group ``decay``).
        bias_correction: Whether to apply bias correction (default ``True``,
            matching ``torch.optim.AdamW``).
    """

    def __init__(
        self,
        model,
        lr: float = 0.000119,
        betas: tuple[float, float] = (0.9, 0.999),
        eps: float = 1e-8,
        weight_decay: float = 0.0005,
        bias_correction: bool = True,
    ):
        """Initialize the AdamW optimizer."""
        self.learning_rate = lr
        # Stored on the instance so the ``momentum`` property below maps reads
        # and writes onto ``beta1`` for warmup-path API parity with MuSGD.
        self.beta1, self.beta2 = betas
        self.eps = eps
        self.weight_decay = weight_decay
        self.bias_correction = bias_correction

        # Param group categorization (matches Ultralytics build_optimizer).
        self._weight_paths: set[str] = set()  # AdamW + weight decay
        self._bias_paths: set[str] = set()  # AdamW, no decay
        self._bn_paths: set[str] = set()  # AdamW, no decay
        self._categorize_params(model)

        # Per-parameter LR scale (default 1.0). PyTorch applies lr*3 to a
        # fine-tuning regex-matched group; we replicate via per-path scales.
        self._lr_scale: dict[str, float] = {}

        # State: m (1st moment) and v (2nd moment) per parameter path.
        self._state: dict[str, dict[str, mx.array]] = {}
        self._step_count = 0

    @property
    def momentum(self) -> float:
        """Expose AdamW's first beta as ``momentum`` for warmup-path parity with MuSGD."""
        return self.beta1

    @momentum.setter
    def momentum(self, value: float) -> None:
        self.beta1 = float(value)

    def _categorize_params(self, model) -> None:
        """Group parameters into weight/bias/bn buckets.

        Matches PyTorch ``build_optimizer`` priority order:
          1. ``"bias"`` in name → bias (no decay)
          2. norm layer / running stats → bn (no decay)
          3. else → weight (with decay) — covers both ``ndim>=2`` and
             scalar/vector weight params (AdamW does not branch by ndim).

        Args:
            model: MLX nn.Module whose parameters will be categorized.
        """
        for path, _param in tree_flatten(model.parameters()):
            if "bias" in path:
                self._bias_paths.add(path)
            elif any(k in path for k in ["bn", "norm", "running_mean", "running_var"]):
                self._bn_paths.add(path)
            else:
                self._weight_paths.add(path)

    def _get_state(self, path: str, param: mx.array) -> dict[str, mx.array]:
        """Lazily allocate first/second moment buffers for ``path``."""
        if path not in self._state:
            self._state[path] = {
                "m": mx.zeros_like(param),
                "v": mx.zeros_like(param),
            }
        return self._state[path]

    @property
    def state(self) -> list[mx.array]:
        """Flat list of all moment buffers, for ``mx.eval`` synchronization."""
        arrays: list[mx.array] = []
        for s in self._state.values():
            for v in s.values():
                arrays.append(v)
        return arrays

    def set_lr_scale(self, model, pattern, scale: float) -> None:
        """Apply per-parameter LR scaling for paths matching ``pattern``.

        Mirrors ``MuSGD.set_lr_scale`` and PyTorch's fine-tuning ``lr*3``
        boost on the ``cv3`` / ``proto.semseg`` / ``flow_model`` head paths
        (see ``ultralytics/engine/trainer.py:build_optimizer``).

        Args:
            model: MLX model (used to enumerate parameter paths).
            pattern: Compiled regex or string pattern.
            scale: Multiplier applied to the base LR for matched params.
        """
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        for path, _ in tree_flatten(model.parameters()):
            if pattern.search(path):
                self._lr_scale[path] = scale

    def step(self, model, grads) -> None:
        """Perform one AdamW optimization step.

        Update rule (per parameter, with per-group decay):
            m = beta1*m + (1-beta1)*grad
            v = beta2*v + (1-beta2)*grad**2
            m_hat = m / (1 - beta1**t)   # if bias_correction
            v_hat = v / (1 - beta2**t)
            param -= lr * (m_hat / (sqrt(v_hat) + eps) + decay * param)

        Args:
            model: MLX model to update.
            grads: Gradient tree (same structure as ``model.parameters()``).
        """
        self._step_count += 1
        t = self._step_count
        bc1 = 1.0 - (self.beta1**t) if self.bias_correction else 1.0
        bc2 = 1.0 - (self.beta2**t) if self.bias_correction else 1.0

        flat_params = dict(tree_flatten(model.parameters()))
        flat_grads = dict(tree_flatten(grads))

        updated: dict[str, mx.array] = {}
        for path, param in flat_params.items():
            grad = flat_grads.get(path)
            if grad is None:
                updated[path] = param
                continue

            state = self._get_state(path, param)
            plr = self.learning_rate * self._lr_scale.get(path, 1.0)

            # Moment updates.
            state["m"] = self.beta1 * state["m"] + (1.0 - self.beta1) * grad
            state["v"] = self.beta2 * state["v"] + (1.0 - self.beta2) * (grad * grad)

            m_hat = state["m"] / bc1
            v_hat = state["v"] / bc2

            adam_update = m_hat / (mx.sqrt(v_hat) + self.eps)

            # Decoupled weight decay — applied only to "weight" group.
            if path in self._weight_paths and self.weight_decay > 0.0:
                param = param - plr * (adam_update + self.weight_decay * param)
            else:
                param = param - plr * adam_update

            updated[path] = param

        model.update(tree_unflatten(list(updated.items())))

    @staticmethod
    def auto_lr(nc: int = 80) -> float:
        """Compute the Ultralytics auto LR for AdamW: ``round(0.002 * 5 / (4 + nc), 6)``.

        Mirrors ``ultralytics/engine/trainer.py:build_optimizer`` for the
        ``optimizer='auto'`` + ``iterations <= 10000`` branch.

        Args:
            nc: Number of classes in the dataset.

        Returns:
            Base learning rate (e.g. ``0.000119`` for ``nc=80``).
        """
        return round(0.002 * 5 / (4 + nc), 6)
