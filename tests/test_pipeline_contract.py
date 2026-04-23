from __future__ import annotations

import inspect
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

import config  # noqa: E402
import main  # noqa: E402


EXPECTED_VIETNAMESE_IMAGES = {
    "gạo_bình_thường.png",
    "gạo_nhiễu_muối_tiêu.png",
    "gạo_nền_không_đều.png",
    "gạo_tương_phản_thấp.png",
}


def test_dataset_images_use_vietnamese_names_only() -> None:
    image_names = {path.name for path in config.DEFAULT_CONFIG.dataset_dir.iterdir() if path.is_file()}

    assert EXPECTED_VIETNAMESE_IMAGES.issubset(image_names)
    assert not any(name.startswith("rice_") for name in image_names)


def test_public_runner_accepts_only_image_name() -> None:
    signature = inspect.signature(main.run_one_image)

    assert list(signature.parameters) == ["image_name"]


def test_cli_configures_stdout_for_vietnamese_names(monkeypatch) -> None:
    class FakeStdout:
        def __init__(self) -> None:
            self.options = None

        def reconfigure(self, **options) -> None:
            self.options = options

    fake_stdout = FakeStdout()
    monkeypatch.setattr(main.sys, "stdout", fake_stdout)

    main.configure_stdout_for_unicode()

    assert fake_stdout.options == {"encoding": "utf-8", "errors": "replace"}


def test_source_pipeline_is_implemented() -> None:
    source_files = [
        PROJECT_ROOT / "src" / "preprocess.py",
        PROJECT_ROOT / "src" / "segment.py",
        PROJECT_ROOT / "src" / "watershed_count.py",
        PROJECT_ROOT / "src" / "utils.py",
        PROJECT_ROOT / "src" / "visualize.py",
    ]

    for source_file in source_files:
        assert "NotImplementedError" not in source_file.read_text(encoding="utf-8")
