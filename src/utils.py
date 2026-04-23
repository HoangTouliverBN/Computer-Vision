"""Utility functions for file IO and result export."""

from __future__ import annotations

import csv
from pathlib import Path

import cv2
import numpy as np

from watershed_count import CountResult


def list_image_files(dataset_dir: Path) -> list[Path]:
    """Return supported image files from the dataset directory."""

    extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
    return sorted(path for path in dataset_dir.iterdir() if path.suffix.lower() in extensions)


def read_image(path: Path) -> np.ndarray:
    """Read one image from disk, including paths with Vietnamese characters."""

    encoded = np.fromfile(str(path), dtype=np.uint8)
    image_bgr = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise ValueError(f"Cannot read image: {path}")
    return cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)


def write_image(path: Path, image: np.ndarray) -> None:
    """Write an image to disk, including paths with Vietnamese characters."""

    path.parent.mkdir(parents=True, exist_ok=True)
    image_to_write = image
    if image.ndim == 3:
        image_to_write = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    extension = path.suffix or ".png"
    ok, encoded = cv2.imencode(extension, image_to_write)
    if not ok:
        raise ValueError(f"Cannot encode image: {path}")
    encoded.tofile(path)


def ensure_output_dirs(output_dir: Path) -> None:
    """Create the expected output directory tree."""

    for child in ("masks", "contours", "labels", "intermediate"):
        (output_dir / child).mkdir(parents=True, exist_ok=True)


def save_results_csv(results: list[CountResult], output_path: Path) -> None:
    """Save one summary CSV containing image names and grain counts."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["image_name", "count", "rejected_regions"],
        )
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "image_name": result.image_name,
                    "count": result.count,
                    "rejected_regions": result.rejected_regions,
                }
            )
