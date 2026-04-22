"""Watershed-based separation and counting for rice grains."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from config import PipelineConfig


@dataclass(frozen=True)
class CountResult:
    """Counting result for one image."""

    image_name: str
    count: int
    rejected_regions: int
    labels: np.ndarray


def separate_and_count(
    image_name: str,
    mask: np.ndarray,
    config: PipelineConfig,
) -> CountResult:
    """Split touching grains, filter invalid regions, and return a count."""

    raise NotImplementedError("Watershed counting will be implemented in the next step.")

