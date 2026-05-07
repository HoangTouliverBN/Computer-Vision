"""Watershed-based separation and counting for rice grains."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import ndimage as ndi
from skimage import measure
from skimage.feature import peak_local_max
from skimage.segmentation import watershed

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

    labels = watershed_separation(mask, config)
    filtered_labels, rejected_regions = filter_grain_regions(labels, config)
    return CountResult(
        image_name=image_name,
        count=int(filtered_labels.max()),
        rejected_regions=rejected_regions,
        labels=filtered_labels,
    )


def watershed_separation(mask: np.ndarray, config: PipelineConfig) -> np.ndarray:
    """Separate touching grain regions with a distance-transform watershed."""

    component_labels = measure.label(mask.astype(bool)).astype(np.int32) # type: ignore
    component_regions = measure.regionprops(component_labels)
    candidate_areas = [
        region.area
        for region in component_regions
        if region.area >= config.min_grain_area
    ]
    median_area = float(np.median(candidate_areas)) if candidate_areas else float(config.min_grain_area)
    split_area = median_area * config.watershed_split_area_factor

    separated = np.zeros(mask.shape, dtype=np.int32)
    next_id = 1

    for region in component_regions:
        component_mask = component_labels == region.label
        if region.area >= split_area:
            local_labels = _watershed_component(component_mask, config)
            for local_id in range(1, int(local_labels.max()) + 1):
                separated[local_labels == local_id] = next_id
                next_id += 1
        else:
            separated[component_mask] = next_id
            next_id += 1

    return separated


def _watershed_component(component_mask: np.ndarray, config: PipelineConfig) -> np.ndarray:
    """Apply watershed only inside one large connected component."""

    distance = ndi.distance_transform_edt(component_mask)
    coords = peak_local_max(
        distance,
        min_distance=config.min_peak_distance,
        labels=component_mask,
    )

    markers = np.zeros(component_mask.shape, dtype=np.int32)
    for marker_id, (row, col) in enumerate(coords, start=1):
        markers[row, col] = marker_id

    if markers.max() == 0:
        return component_mask.astype(np.int32)

    return watershed(-distance, markers, mask=component_mask.astype(bool)) # type: ignore


def filter_grain_regions(
    labels: np.ndarray,
    config: PipelineConfig,
) -> tuple[np.ndarray, int]:
    """Keep regions whose size and shape match rice grains."""

    filtered = np.zeros(labels.shape, dtype=np.int32)
    next_id = 1
    rejected_regions = 0

    for region in measure.regionprops(labels):
        aspect_ratio = region_axis_ratio(region)

        accepted = (
            config.min_grain_area <= region.area <= config.max_grain_area
            and config.min_aspect_ratio <= aspect_ratio <= config.max_aspect_ratio
            and region.solidity >= config.min_solidity
            and region.eccentricity >= config.min_eccentricity
        )

        if accepted:
            filtered[labels == region.label] = next_id
            next_id += 1
        else:
            rejected_regions += 1

    return filtered, rejected_regions


def region_axis_ratio(region: Any) -> float:
    """Return elongated-shape ratio from fitted ellipse axes."""

    major_axis_length = getattr(region, "axis_major_length", None)
    minor_axis_length = getattr(region, "axis_minor_length", None)
    if major_axis_length is None or minor_axis_length is None:
        major_axis_length = region.major_axis_length
        minor_axis_length = region.minor_axis_length
    if minor_axis_length > 0:
        return float(major_axis_length / minor_axis_length)

    min_row, min_col, max_row, max_col = region.bbox
    height = max_row - min_row
    width = max_col - min_col
    short_side = max(1, min(height, width))
    long_side = max(height, width)
    return float(long_side / short_side)
