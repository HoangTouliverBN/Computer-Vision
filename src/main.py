"""Command-line entry point for the rice grain counting pipeline."""

from __future__ import annotations

import argparse
import sys

from config import DEFAULT_CONFIG, PipelineConfig
from parameter_log import write_parameter_log
from preprocess import preprocess_steps
from segment import segmentation_steps
from utils import ensure_output_dirs, list_image_files, read_image, save_results_csv
from visualize import (
    save_preprocess_visualizations,
    save_segmentation_visualizations,
    save_visualizations,
)
from watershed_count import CountResult, separate_and_count


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Count rice grains in one image using the fixed pipeline.",
    )
    parser.add_argument("image_name", help="Image file name inside the Dataset directory.")
    return parser.parse_args()


def configure_stdout_for_unicode() -> None:
    """Make CLI output safe for Vietnamese file names on Windows consoles."""

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _process_one_image(image_name: str, config: PipelineConfig) -> CountResult:
    """Run the fixed pipeline for one image with an explicit config object."""

    ensure_output_dirs(config.output_dir)

    image_path = config.dataset_dir / image_name
    image = read_image(image_path)
    preprocessing = preprocess_steps(image, config)
    preprocessed = preprocessing["enhanced"]
    segmentation = segmentation_steps(preprocessed, config)
    mask = segmentation["mask"]
    result = separate_and_count(image_path.name, mask, config)
    save_preprocess_visualizations(image_path.name, preprocessing, config.output_dir)
    save_segmentation_visualizations(image_path.name, segmentation, config.output_dir)
    save_visualizations(image, mask, result, config.output_dir)
    return result


def run_one_image(image_name: str) -> CountResult:
    """Run the fixed pipeline for one image name from the dataset directory."""

    result = _process_one_image(image_name, DEFAULT_CONFIG)
    save_results_csv([result], DEFAULT_CONFIG.output_dir / "results.csv")
    return result


def run_all_images(config: PipelineConfig | None = None) -> list[CountResult]:
    """Run the fixed pipeline for every image using the same configuration."""

    active_config = config or DEFAULT_CONFIG
    ensure_output_dirs(active_config.output_dir)

    results = []
    for image_path in list_image_files(active_config.dataset_dir):
        results.append(_process_one_image(image_path.name, active_config))
    save_results_csv(results, active_config.output_dir / "results.csv")
    write_parameter_log(active_config, results)
    return results


def main() -> None:
    """Run the full pipeline for one image name."""

    configure_stdout_for_unicode()
    args = parse_args()
    result = run_one_image(args.image_name)
    print(f"{result.image_name}: {result.count}")


if __name__ == "__main__":
    main()
