"""Command-line entry point for the rice grain counting pipeline."""

from __future__ import annotations

import argparse
import sys

from config import DEFAULT_CONFIG, PipelineConfig
from preprocess import preprocess_image
from segment import segment_grains
from utils import ensure_output_dirs, list_image_files, read_image, save_results_csv
from visualize import save_visualizations
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


def run_one_image(image_name: str) -> CountResult:
    """Run the fixed pipeline for one image name from the dataset directory."""

    config = PipelineConfig(
        dataset_dir=DEFAULT_CONFIG.dataset_dir,
        output_dir=DEFAULT_CONFIG.output_dir,
    )
    ensure_output_dirs(config.output_dir)

    image_path = config.dataset_dir / image_name
    image = read_image(image_path)
    preprocessed = preprocess_image(image, config)
    mask = segment_grains(preprocessed, config)
    result = separate_and_count(image_path.name, mask, config)
    save_visualizations(image, mask, result, config.output_dir)
    save_results_csv([result], config.output_dir / "results.csv")
    return result


def run_all_images() -> list[CountResult]:
    """Run the fixed pipeline for every image using the same configuration."""

    results = []
    for image_path in list_image_files(DEFAULT_CONFIG.dataset_dir):
        results.append(run_one_image(image_path.name))
    save_results_csv(results, DEFAULT_CONFIG.output_dir / "results.csv")
    return results


def main() -> None:
    """Run the full pipeline for one image name."""

    configure_stdout_for_unicode()
    args = parse_args()
    result = run_one_image(args.image_name)
    print(f"{result.image_name}: {result.count}")


if __name__ == "__main__":
    main()
