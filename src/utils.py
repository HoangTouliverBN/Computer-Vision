"""Utility functions for file IO and result export."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from watershed_count import CountResult


def list_image_files(dataset_dir: Path) -> list[Path]:
    """Return supported image files from the dataset directory."""

    extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
    return sorted(path for path in dataset_dir.iterdir() if path.suffix.lower() in extensions)


def read_image(path: Path) -> np.ndarray:
    """Read one image from disk."""

    raise NotImplementedError("Image loading will be implemented in the next step.")


def ensure_output_dirs(output_dir: Path) -> None:
    """Create the expected output directory tree."""

    for child in ("masks", "contours", "labels", "intermediate"):
        (output_dir / child).mkdir(parents=True, exist_ok=True)


def save_results_csv(results: list[CountResult], output_path: Path) -> None:
    """Save one summary CSV containing image names and grain counts."""

    raise NotImplementedError("CSV export will be implemented in the next step.")

