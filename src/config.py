"""Configuration defaults for the rice grain counting pipeline."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelineConfig:
    """Parameters shared by preprocessing, segmentation, and counting."""

    dataset_dir: Path = Path("Dataset")
    output_dir: Path = Path("output")
    median_kernel_size: int = 3
    background_kernel_size: int = 51
    clahe_clip_limit: float = 2.0
    clahe_tile_grid_size: tuple[int, int] = (8, 8)
    morphology_kernel_size: int = 3
    min_grain_area: int = 40
    max_grain_area: int = 5000
    min_aspect_ratio: float = 1.5
    max_aspect_ratio: float = 8.0


DEFAULT_CONFIG = PipelineConfig()

