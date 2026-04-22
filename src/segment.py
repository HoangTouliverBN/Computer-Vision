"""Segmentation steps for separating rice grains from the background."""

from __future__ import annotations

import numpy as np

from config import PipelineConfig


def segment_grains(preprocessed: np.ndarray, config: PipelineConfig) -> np.ndarray:
    """Return a binary mask of candidate rice grain regions."""

    raise NotImplementedError("Segmentation will be implemented in the next step.")

