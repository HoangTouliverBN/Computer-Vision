"""Preprocessing steps for rice grain images."""

from __future__ import annotations

import numpy as np

from config import PipelineConfig


def preprocess_image(image: np.ndarray, config: PipelineConfig) -> np.ndarray:
    """Return an enhanced grayscale image ready for segmentation.

    Planned steps:
    - convert to grayscale
    - reduce salt-and-pepper noise
    - correct uneven illumination
    - improve local contrast with CLAHE
    """

    raise NotImplementedError("Preprocessing will be implemented in the next step.")

