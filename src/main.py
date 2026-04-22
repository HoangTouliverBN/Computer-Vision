"""Command-line entry point for the rice grain counting pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from config import DEFAULT_CONFIG, PipelineConfig
from preprocess import preprocess_image
from segment import segment_grains
from utils import ensure_output_dirs, list_image_files, read_image, save_results_csv
from visualize import save_visualizations
from watershed_count import separate_and_count


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description="Count rice grains in images.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_CONFIG.dataset_dir)
    parser.add_argument("--output", type=Path, default=DEFAULT_CONFIG.output_dir)
    return parser.parse_args()


def main() -> None:
    """Run the full pipeline for every image in the dataset directory."""

    args = parse_args()
    config = PipelineConfig(dataset_dir=args.dataset, output_dir=args.output)
    ensure_output_dirs(config.output_dir)

    results = []
    for image_path in list_image_files(config.dataset_dir):
        image = read_image(image_path)
        preprocessed = preprocess_image(image, config)
        mask = segment_grains(preprocessed, config)
        result = separate_and_count(image_path.name, mask, config)
        save_visualizations(image, mask, result, config.output_dir)
        results.append(result)

    save_results_csv(results, config.output_dir / "results.csv")


if __name__ == "__main__":
    main()

