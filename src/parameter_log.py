"""Local experiment logging for shared pipeline parameter changes."""

from __future__ import annotations

import csv
import json
from dataclasses import fields
from datetime import datetime
from pathlib import Path
from typing import Any

from config import PipelineConfig
from watershed_count import CountResult


TRACKED_PARAMETERS = [
    "median_kernel_size",
    "background_kernel_size",
    "clahe_clip_limit",
    "clahe_tile_grid_size",
    "morphology_kernel_size",
    "adaptive_block_size",
    "adaptive_c",
    "min_grain_area",
    "max_grain_area",
    "min_aspect_ratio",
    "max_aspect_ratio",
    "min_solidity",
    "min_peak_distance",
]


def write_parameter_log(
    config: PipelineConfig,
    results: list[CountResult],
    timestamp: datetime | None = None,
) -> None:
    """Append one local log entry for a full batch run."""

    run_time = timestamp or datetime.now()
    log_dir = config.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    current_config = serialize_config(config)
    previous_run = read_latest_run(log_dir / "latest_run.json")
    previous_config = previous_run.get("config", {})
    previous_results = previous_run.get("results", {})
    changes = compare_configs(previous_config, current_config)

    append_markdown_log(
        log_dir / "parameter_runs.md",
        run_time,
        changes,
        results,
        previous_results,
    )
    append_csv_log(
        log_dir / "parameter_runs.csv",
        run_time,
        changes,
        results,
        previous_results,
    )
    write_latest_run(log_dir / "latest_run.json", current_config, results)


def serialize_config(config: PipelineConfig) -> dict[str, Any]:
    """Convert tracked pipeline parameters into JSON-safe values."""

    output: dict[str, Any] = {}
    field_names = {field.name for field in fields(config)}
    for name in TRACKED_PARAMETERS:
        if name not in field_names:
            continue
        value = getattr(config, name)
        if isinstance(value, tuple):
            output[name] = list(value)
        elif isinstance(value, Path):
            output[name] = str(value)
        else:
            output[name] = value
    return output


def read_latest_run(path: Path) -> dict[str, Any]:
    """Read the previous local run summary if it exists."""

    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def compare_configs(
    previous_config: dict[str, Any],
    current_config: dict[str, Any],
) -> list[dict[str, str]]:
    """Return changed parameters and their expected effect."""

    changes = []
    for name in TRACKED_PARAMETERS:
        old_value = previous_config.get(name)
        new_value = current_config.get(name)
        if old_value == new_value:
            continue
        if old_value is None:
            changes.append(
                {
                    "name": name,
                    "old": "",
                    "new": format_value(new_value),
                    "effect": "Lần chạy đầu tiên, dùng làm mốc so sánh cho các lần thay đổi tham số sau.",
                }
            )
            continue
        changes.append(
            {
                "name": name,
                "old": format_value(old_value),
                "new": format_value(new_value),
                "effect": parameter_effect(name, old_value, new_value),
            }
        )
    return changes


def parameter_effect(name: str, old_value: Any, new_value: Any) -> str:
    """Explain how one parameter change can affect the count result."""

    if name == "min_peak_distance":
        if new_value < old_value:
            return (
                "giảm khoảng cách marker làm watershed dễ tách các hạt dính nhau hơn, "
                "có thể tăng số hạt đếm được nhưng cũng tăng nguy cơ tách một hạt thành nhiều phần."
            )
        return (
            "tăng khoảng cách marker làm watershed tạo ít marker hơn, giảm nguy cơ đếm dư "
            "nhưng có thể làm các hạt dính nhau bị gộp và đếm thiếu."
        )

    if name == "min_grain_area":
        if new_value > old_value:
            return "Tăng diện tích tối thiểu giúp loại nhiễu nhỏ tốt hơn nhưng có thể làm mất hạt nhỏ hoặc hạt ở biên."
        return "Giảm diện tích tối thiểu giúp giữ lại hạt nhỏ nhưng có thể làm tăng số vùng nhiễu được đếm nhầm."

    if name == "max_grain_area":
        if new_value > old_value:
            return "Tăng diện tích tối đa cho phép giữ vùng hạt lớn hoặc cụm hạt, nhưng có thể nhận nhầm mảng nền lớn."
        return "Giảm diện tích tối đa giúp loại vùng nền lớn nhưng có thể loại nhầm cụm hạt dính nhau."

    if name == "min_solidity":
        if new_value > old_value:
            return "Tăng solidity tối thiểu giúp loại vùng méo hoặc rỗng, giảm đếm nhầm nền nhưng có thể loại hạt bị dính hoặc mất biên."
        return "Giảm solidity tối thiểu giúp giữ lại vùng hạt méo hoặc dính nhau nhưng có thể tăng đếm nhầm vùng nền."

    if name == "adaptive_c":
        if new_value > old_value:
            return "Tăng adaptive_c làm ngưỡng cục bộ thấp hơn trong OpenCV, thường giữ nhiều foreground hơn và có thể tăng số vùng được đếm."
        return "Giảm adaptive_c làm ngưỡng cục bộ cao hơn trong OpenCV, thường giảm foreground và có thể làm mất hạt yếu."

    if name == "adaptive_block_size":
        if new_value > old_value:
            return "Tăng block size làm adaptive threshold ổn định hơn trên vùng rộng nhưng có thể kém nhạy với thay đổi cục bộ."
        return "Giảm block size làm threshold nhạy hơn với vùng cục bộ nhưng dễ bắt nhiễu hoặc nền không đều."

    if name == "background_kernel_size":
        if new_value > old_value:
            return "Tăng kernel hiệu chỉnh nền giúp xử lý biến thiên ánh sáng lớn hơn nhưng có thể làm mất chi tiết cục bộ."
        return "Giảm kernel hiệu chỉnh nền giúp phản ứng với thay đổi cục bộ nhanh hơn nhưng có thể kém ổn định với nền thay đổi chậm."

    if name == "morphology_kernel_size":
        if new_value > old_value:
            return "Tăng kernel morphology làm sạch và nối vùng mạnh hơn nhưng có thể làm biến dạng hoặc gộp hạt nhỏ."
        return "Giảm kernel morphology giữ chi tiết tốt hơn nhưng có thể để lại nhiều nhiễu nhỏ."

    if name == "median_kernel_size":
        if new_value > old_value:
            return "Tăng median kernel lọc nhiễu muối tiêu mạnh hơn nhưng có thể làm mờ biên hạt."
        return "Giảm median kernel giữ biên tốt hơn nhưng giảm khả năng khử nhiễu muối tiêu."

    if name == "clahe_clip_limit":
        if new_value > old_value:
            return "Tăng CLAHE clip limit làm tương phản cục bộ mạnh hơn nhưng có thể khuếch đại nhiễu."
        return "Giảm CLAHE clip limit làm tăng tương phản nhẹ hơn, giảm nhiễu nhưng có thể làm hạt tương phản thấp khó tách."

    if name == "min_aspect_ratio":
        if new_value > old_value:
            return "Tăng aspect ratio tối thiểu ưu tiên vùng thon dài giống hạt gạo hơn nhưng có thể loại hạt ngắn hoặc bị cắt."
        return "Giảm aspect ratio tối thiểu chấp nhận nhiều hình dạng hơn nhưng có thể tăng đếm nhầm vùng không giống hạt."

    if name == "max_aspect_ratio":
        if new_value > old_value:
            return "Tăng aspect ratio tối đa cho phép giữ vùng rất dài nhưng có thể chấp nhận nhiễu dạng vệt."
        return "Giảm aspect ratio tối đa loại vùng quá dài nhưng có thể loại nhầm hạt nằm nghiêng hoặc cụm hạt."

    return "Thay đổi tham số này có thể ảnh hưởng đến cân bằng giữa giữ hạt thật và loại nhiễu."


def append_markdown_log(
    path: Path,
    timestamp: datetime,
    changes: list[dict[str, str]],
    results: list[CountResult],
    previous_results: dict[str, int],
) -> None:
    """Append a human-readable Markdown log entry."""

    lines = []
    if not path.exists():
        lines.append("# Nhật ký thay đổi tham số\n\n")

    lines.append(f"## {timestamp:%Y-%m-%d %H:%M:%S}\n\n")
    lines.append("### Tham số thay đổi\n\n")
    if changes:
        for change in changes:
            if change["old"]:
                lines.append(f"- {change['name']}: {change['old']} -> {change['new']}\n")
            else:
                lines.append(f"- {change['name']}: {change['new']}\n")
            lines.append(f"  - Ảnh hưởng: {change['effect']}\n")
    else:
        lines.append("- Không thay đổi tham số so với lần chạy trước.\n")

    lines.append("\n### Kết quả\n\n")
    lines.append("| Ảnh | Count | Delta | Vùng bị loại |\n")
    lines.append("| --- | ---: | ---: | ---: |\n")
    for result in results:
        delta = count_delta(result, previous_results)
        lines.append(
            f"| {result.image_name} | {result.count} | {format_delta(delta)} | {result.rejected_regions} |\n"
        )
    lines.append("\n")

    with path.open("a", encoding="utf-8") as markdown_file:
        markdown_file.writelines(lines)


def append_csv_log(
    path: Path,
    timestamp: datetime,
    changes: list[dict[str, str]],
    results: list[CountResult],
    previous_results: dict[str, int],
) -> None:
    """Append machine-readable rows for each image in one run."""

    fieldnames = [
        "timestamp",
        "image_name",
        "count",
        "rejected_regions",
        "delta_count",
        "changed_parameters",
    ]
    write_header = not path.exists()
    changed_parameters = ",".join(change["name"] for change in changes) or "none"

    with path.open("a", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "timestamp": f"{timestamp:%Y-%m-%d %H:%M:%S}",
                    "image_name": result.image_name,
                    "count": result.count,
                    "rejected_regions": result.rejected_regions,
                    "delta_count": format_delta(count_delta(result, previous_results)),
                    "changed_parameters": changed_parameters,
                }
            )


def write_latest_run(
    path: Path,
    config: dict[str, Any],
    results: list[CountResult],
) -> None:
    """Save the latest run as the next comparison baseline."""

    latest_run = {
        "config": config,
        "results": {result.image_name: result.count for result in results},
    }
    path.write_text(
        json.dumps(latest_run, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def count_delta(result: CountResult, previous_results: dict[str, int]) -> int | None:
    """Return the count delta for one image if a previous result exists."""

    previous_count = previous_results.get(result.image_name)
    if previous_count is None:
        return None
    return result.count - int(previous_count)


def format_delta(delta: int | None) -> str:
    """Format count delta for Markdown and CSV logs."""

    if delta is None:
        return ""
    if delta > 0:
        return f"+{delta}"
    return str(delta)


def format_value(value: Any) -> str:
    """Format parameter values in a compact, readable form."""

    if isinstance(value, list):
        return str(tuple(value))
    return str(value)
