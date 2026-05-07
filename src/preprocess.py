"""Preprocessing steps for rice grain images."""

from __future__ import annotations

import cv2
import numpy as np

from config import PipelineConfig


def _make_odd(value: int) -> int:
    return value if value % 2 == 1 else value + 1


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert RGB or grayscale image to grayscale."""

    if image.ndim == 2:
        return image.copy()
    return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)


def denoise_image(gray: np.ndarray, kernel_size: int) -> np.ndarray:
    """Reduce salt-and-pepper noise using median blur."""

    return cv2.medianBlur(gray, _make_odd(kernel_size))


def _normalize_to_uint8(image: np.ndarray) -> np.ndarray:
    image = np.real(image).astype(np.float32)
    image_min = float(np.min(image))
    image_max = float(np.max(image))
    if image_max <= image_min:
        return np.zeros(image.shape, dtype=np.uint8)
    normalized = (image - image_min) * (255.0 / (image_max - image_min))
    return np.clip(normalized, 0, 255).astype(np.uint8)


def correct_illumination_fourier(
    gray: np.ndarray,
    cutoff: int,
    low_gain: float,
    high_gain: float,
) -> np.ndarray:
    """Correct uneven illumination with Fourier homomorphic filtering."""

    cutoff = max(1, int(cutoff))
    low_gain = max(0.0, float(low_gain))
    high_gain = max(low_gain, float(high_gain))

    log_image = np.log1p(gray.astype(np.float32))
    spectrum = np.fft.fftshift(np.fft.fft2(log_image))

    rows, cols = gray.shape
    row_axis = np.arange(rows, dtype=np.float32) - rows / 2.0
    col_axis = np.arange(cols, dtype=np.float32) - cols / 2.0
    distance_squared = row_axis[:, None] ** 2 + col_axis[None, :] ** 2

    high_pass = 1.0 - np.exp(-distance_squared / (2.0 * float(cutoff) ** 2))
    homomorphic_filter = low_gain + (high_gain - low_gain) * high_pass

    filtered = spectrum * homomorphic_filter
    corrected_log = np.fft.ifft2(np.fft.ifftshift(filtered))
    corrected = np.expm1(np.real(corrected_log))
    return _normalize_to_uint8(corrected)


def suppress_stripes_fourier(
    gray: np.ndarray,
    min_frequency: int,
    max_frequency: int,
    top_k: int,
    radius: int,
    strength: float,
) -> np.ndarray:
    """Suppress vertical periodic background stripes using a 1D Fourier notch."""

    min_frequency = max(1, int(min_frequency))
    top_k = max(1, int(top_k))
    radius = max(0, int(radius))
    strength = max(0.0, float(strength))

    image = gray.astype(np.float32)
    profile = np.median(image, axis=0)
    profile_centered = profile - float(np.mean(profile))
    spectrum = np.fft.fft(profile_centered)

    width = profile.shape[0]
    max_frequency = min(max(min_frequency, int(max_frequency)), width // 2 - 1)
    usable_frequencies = np.arange(min_frequency, max_frequency + 1)
    if usable_frequencies.size == 0:
        return gray.copy()

    magnitude = np.abs(spectrum)
    strongest = usable_frequencies[
        np.argsort(magnitude[usable_frequencies])[-min(top_k, usable_frequencies.size) :]
    ]

    stripe_spectrum = np.zeros_like(spectrum)
    for frequency in strongest:
        for offset in range(-radius, radius + 1):
            positive = (int(frequency) + offset) % width
            negative = (-int(frequency) + offset) % width
            stripe_spectrum[positive] = spectrum[positive]
            stripe_spectrum[negative] = spectrum[negative]

    stripe_profile = np.real(np.fft.ifft(stripe_spectrum)) * strength
    corrected = image - stripe_profile[None, :]
    corrected += float(np.mean(image)) - float(np.mean(corrected))
    return np.clip(corrected, 0, 255).astype(np.uint8)


def correct_illumination(gray: np.ndarray, config: PipelineConfig) -> np.ndarray:
    """Correct uneven illumination with the final Fourier-based pipeline."""

    return illumination_steps(gray, config)["corrected"]


def illumination_steps(gray: np.ndarray, config: PipelineConfig) -> dict[str, np.ndarray]:
    """Return each Fourier illumination correction step."""

    fourier_corrected = correct_illumination_fourier(
        gray,
        config.fourier_cutoff,
        config.fourier_low_gain,
        config.fourier_high_gain,
    )
    stripe_suppressed = suppress_stripes_fourier(
        fourier_corrected,
        config.fourier_stripe_min_frequency,
        config.fourier_stripe_max_frequency,
        config.fourier_stripe_top_k,
        config.fourier_stripe_radius,
        config.fourier_stripe_strength,
    )
    return {
        "fourier_corrected": fourier_corrected,
        "stripe_suppressed": stripe_suppressed,
        "corrected": stripe_suppressed,
    }


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
    - correct uneven illumination with Fourier homomorphic and notch filtering
    - improve local contrast with CLAHE
    """

    return preprocess_steps(image, config)["enhanced"]


def preprocess_steps(image: np.ndarray, config: PipelineConfig) -> dict[str, np.ndarray]:
    """Return every preprocessing image that should be inspectable in output."""

    gray = to_grayscale(image)
    denoised = denoise_image(gray, config.median_kernel_size)
    illumination = illumination_steps(denoised, config)
    enhanced = enhance_contrast(illumination["corrected"], config)
    return {
        "gray": gray,
        "denoised": denoised,
        **illumination,
        "enhanced": enhanced,
    }
