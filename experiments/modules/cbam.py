"""
Convolutional Block Attention Module (CBAM) implementation for Ultralytics YOLO26.

Reference:
    Woo, S., Park, J., Lee, J. Y., & Kweon, I. S. (2018).
    CBAM: Convolutional Block Attention Module. ECCV 2018.
"""

from __future__ import annotations

import inspect
import logging
from typing import Optional

import torch
import torch.nn as nn

logger = logging.getLogger("experiments.cbam")


class ChannelAttention(nn.Module):
    """
    Channel Attention Module (CAM).
    Applies shared MLP across avg-pooled and max-pooled feature maps.
    """

    def __init__(self, channels: int, ratio: int = 16):
        super().__init__()
        self.channels = channels
        self.ratio = ratio
        reduced_channels = max(channels // ratio, 8)
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)

        self.mlp = nn.Sequential(
            nn.Conv2d(channels, reduced_channels, kernel_size=1, bias=False),
            nn.ReLU(inplace=True),
            nn.Conv2d(reduced_channels, channels, kernel_size=1, bias=False),
        )
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        avg_out = self.mlp(self.avg_pool(x))
        max_out = self.mlp(self.max_pool(x))
        attention = self.sigmoid(avg_out + max_out)
        return x * attention


class SpatialAttention(nn.Module):
    """
    Spatial Attention Module (SAM).
    Applies 7x7 (or 3x3) convolution over concatenated channel-wise avg and max pooling.
    """

    def __init__(self, kernel_size: int = 7):
        super().__init__()
        if kernel_size not in (3, 7):
            raise ValueError(f"kernel_size must be 3 or 7, got {kernel_size}")
        padding = 3 if kernel_size == 7 else 1
        self.conv = nn.Conv2d(2, 1, kernel_size=kernel_size, padding=padding, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        avg_out = torch.mean(x, dim=1, keepdim=True)
        max_out, _ = torch.max(x, dim=1, keepdim=True)
        combined = torch.cat([avg_out, max_out], dim=1)
        attention = self.sigmoid(self.conv(combined))
        return x * attention


class CBAM(nn.Module):
    """
    Convolutional Block Attention Module (CBAM).
    Combines Channel Attention and Spatial Attention sequentially.

    Args:
        c1: Number of input channels. If None, automatically inferred from Ultralytics
            parse_model context or on the first forward pass.
        kernel_size: Spatial attention kernel size (default: 7).
        ratio: Channel attention reduction ratio (default: 16).
    """

    def __init__(
        self,
        c1: Optional[int] = None,
        kernel_size: int = 7,
        ratio: int = 16,
    ):
        super().__init__()
        # If c1 not supplied directly in YAML args, inspect parse_model stack frame
        if c1 is None or c1 <= 0:
            c1 = self._infer_channels_from_caller()

        self.c1 = c1
        self.kernel_size = kernel_size
        self.ratio = ratio

        if self.c1 is not None and self.c1 > 0:
            self.ca = ChannelAttention(self.c1, ratio=self.ratio)
        else:
            self.ca = None

        self.sa = SpatialAttention(kernel_size=self.kernel_size)

    @staticmethod
    def _infer_channels_from_caller() -> Optional[int]:
        """
        Inspect call stack to retrieve incoming channel count `ch[f]`
        when instantiated by Ultralytics parse_model.
        """
        frame = inspect.currentframe()
        try:
            curr = frame.f_back if frame else None
            while curr:
                f_locals = curr.f_locals
                if "ch" in f_locals and "f" in f_locals:
                    ch_list = f_locals["ch"]
                    f_idx = f_locals["f"]
                    if isinstance(f_idx, int) and -len(ch_list) <= f_idx < len(ch_list):
                        return int(ch_list[f_idx])
                curr = curr.f_back
        finally:
            del frame
        return None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Dynamic fallback initialization in case c1 was not determinable during parse
        if self.ca is None:
            self.c1 = x.shape[1]
            self.ca = ChannelAttention(self.c1, ratio=self.ratio).to(
                device=x.device, dtype=x.dtype
            )

        out = self.ca(x)
        out = self.sa(out)
        return out


def register_cbam() -> None:
    """
    Dynamically registers CBAM into Ultralytics YOLO modules and tasks registry.
    This enables Ultralytics to parse CBAM layers in YAML architectures without
    needing manual edits to the installed ultralytics package.
    """
    try:
        import ultralytics.nn.modules as modules
        import ultralytics.nn.modules.block as block
        import ultralytics.nn.tasks as tasks

        # Register in tasks and modules globals
        tasks.CBAM = CBAM
        setattr(tasks, "CBAM", CBAM)
        setattr(modules, "CBAM", CBAM)
        setattr(block, "CBAM", CBAM)

        # Add to modules.__all__ if available
        if hasattr(modules, "__all__") and "CBAM" not in modules.__all__:
            if isinstance(modules.__all__, tuple):
                modules.__all__ = modules.__all__ + ("CBAM",)
            elif isinstance(modules.__all__, list):
                modules.__all__.append("CBAM")

        logger.info("Successfully registered CBAM module into Ultralytics registry.")
    except ImportError as exc:
        logger.warning(
            f"Ultralytics is not installed in the current environment ({exc}). "
            "CBAM will be registered when Ultralytics is imported."
        )
