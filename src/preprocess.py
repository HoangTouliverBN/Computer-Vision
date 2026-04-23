"""Preprocessing steps for rice grain images."""

from __future__ import annotations

import cv2
import numpy as np

from config import PipelineConfig


def _make_odd(value: int) -> int:
    return value if value % 2 == 1 else value + 1


def _bounded_odd(value: int, upper_bound: int) -> int:
    value = min(_make_odd(value), upper_bound)
    return value if value % 2 == 1 else value - 1


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert RGB or grayscale image to grayscale."""

    if image.ndim == 2:
        return image.copy()
    return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)


def denoise_image(gray: np.ndarray, kernel_size: int) -> np.ndarray:
    """Reduce salt-and-pepper noise using median blur."""

    return cv2.medianBlur(gray, _make_odd(kernel_size))


def correct_illumination(gray: np.ndarray, kernel_size: int) -> np.ndarray:
    """Normalize the image with a blurred background estimate."""

    max_kernel = max(3, min(gray.shape) - 1)
    kernel_size = _bounded_odd(kernel_size, max_kernel)
    background = cv2.GaussianBlur(gray, (kernel_size, kernel_size), 0)
    corrected = gray.astype(np.float32) / (background.astype(np.float32) + 1.0)
    corrected *= np.mean(background)
    return np.clip(corrected, 0, 255).astype(np.uint8)


def enhance_contrast(gray: np.ndarray, config: PipelineConfig) -> np.ndarray:
    """Improve local contrast using CLAHE."""

    clahe = cv2.createCLAHE(
        clipLimit=config.clahe_clip_limit,
        tileGridSize=config.clahe_tile_grid_size,
    )
    return clahe.apply(gray)


def preprocess_image(image: np.ndarray, config: PipelineConfig) -> np.ndarray:
    """Return an enhanced grayscale image ready for segmentation.

    Steps:
    - convert to grayscale
    - reduce salt-and-pepper noise
    - correct uneven illumination
    - improve local contrast with CLAHE
    """

    gray = to_grayscale(image)
    denoised = denoise_image(gray, config.median_kernel_size)
    corrected = correct_illumination(denoised, config.background_kernel_size)
    return enhance_contrast(corrected, config)
