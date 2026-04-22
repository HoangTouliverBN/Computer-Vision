"""Visualization helpers for masks, labels, and contour overlays."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from watershed_count import CountResult


def save_visualizations(
    original: np.ndarray,
    mask: np.ndarray,
    result: CountResult,
    output_dir: Path,
) -> None:
    """Save mask, label image, contour overlay, and intermediate outputs."""

    raise NotImplementedError("Visualization will be implemented in the next step.")

