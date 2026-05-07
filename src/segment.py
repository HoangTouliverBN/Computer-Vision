"""Segmentation steps for separating rice grains from the background."""

from __future__ import annotations

import cv2
import numpy as np
from scipy import ndimage as ndi
from skimage import morphology

from config import PipelineConfig


def _make_odd(value: int) -> int:
    return value if value % 2 == 1 else value + 1


def adaptive_threshold(gray: np.ndarray, config: PipelineConfig) -> np.ndarray:
    """Create a mask with adaptive Gaussian thresholding."""

    block_size = _make_odd(config.adaptive_block_size)
    return cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        block_size,
        config.adaptive_c,
    ).astype(bool)


def threshold_grains(preprocessed: np.ndarray, config: PipelineConfig) -> np.ndarray:
    """Create an initial grain mask using Otsu with automatic fallback."""

    _, otsu_mask = cv2.threshold(
        preprocessed,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )
    mask = otsu_mask.astype(bool)
    foreground_ratio = float(mask.mean())

    if (
        foreground_ratio < config.otsu_min_foreground_ratio
        or foreground_ratio > config.otsu_max_foreground_ratio
    ):
        return adaptive_threshold(preprocessed, config)

    return mask


def clean_mask(mask: np.ndarray, config: PipelineConfig) -> np.ndarray:
    """Remove small noise and repair candidate grain regions."""

    kernel_size = _make_odd(config.morphology_kernel_size)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))

    no_small = morphology.remove_small_objects(
        mask.astype(bool),
        max_size=max(0, config.min_grain_area - 1),
    )
    opened = cv2.morphologyEx(
        no_small.astype(np.uint8) * 255,
        cv2.MORPH_OPEN,
        kernel,
    ) > 0
    closed = cv2.morphologyEx(
        opened.astype(np.uint8) * 255,
        cv2.MORPH_CLOSE,
        kernel,
    ) > 0
    filled = ndi.binary_fill_holes(closed)
    if config.mask_dilation_iterations > 0:
        filled = cv2.dilate(
            filled.astype(np.uint8) * 255, # type: ignore
            kernel,
            iterations=config.mask_dilation_iterations,
        ) > 0

    return morphology.remove_small_objects(
        filled.astype(bool), # pyright: ignore[reportOptionalMemberAccess]
        max_size=max(0, config.min_grain_area - 1),
    )


def segment_grains(preprocessed: np.ndarray, config: PipelineConfig) -> np.ndarray:
    """Return a binary mask of candidate rice grain regions."""

    raw_mask = threshold_grains(preprocessed, config)
    return clean_mask(raw_mask, config)
