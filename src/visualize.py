"""Visualization helpers for masks, labels, and contour overlays."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from utils import write_image
from watershed_count import CountResult


def save_visualizations(
    original: np.ndarray,
    mask: np.ndarray,
    result: CountResult,
    output_dir: Path,
) -> None:
    """Save mask, label image, contour overlay, and intermediate outputs."""

    stem = Path(result.image_name).stem

    write_image(output_dir / "masks" / f"{stem}_mask.png", mask.astype(np.uint8) * 255)
    write_image(output_dir / "labels" / f"{stem}_labels.png", labels_to_uint8(result.labels))
    write_image(output_dir / "contours" / f"{stem}_contours.png", contour_overlay(original, result.labels))


def save_preprocess_visualizations(
    image_name: str,
    steps: dict[str, np.ndarray],
    output_dir: Path,
) -> None:
    """Save preprocessing images for step-by-step inspection."""

    stem = Path(image_name).stem
    for step_name, image in steps.items():
        write_image(output_dir / "intermediate" / f"{stem}_{step_name}.png", image)


def save_segmentation_visualizations(
    image_name: str,
    steps: dict[str, np.ndarray],
    output_dir: Path,
) -> None:
    """Save threshold and cleaned masks for step-by-step inspection."""

    stem = Path(image_name).stem
    for step_name, mask in steps.items():
        write_image(output_dir / "masks" / f"{stem}_{step_name}.png", mask.astype(np.uint8) * 255)


def labels_to_uint8(labels: np.ndarray) -> np.ndarray:
    """Convert integer labels to a visible grayscale image."""

    if labels.max() == 0:
        return np.zeros(labels.shape, dtype=np.uint8)
    return ((labels.astype(np.float32) / labels.max()) * 255).astype(np.uint8)


def contour_overlay(original: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """Draw accepted grain contours on top of the original image."""

    overlay = original.copy()
    binary = (labels > 0).astype(np.uint8) * 255
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(overlay, contours, -1, (255, 0, 0), 2)
    return overlay
