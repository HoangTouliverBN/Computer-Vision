"""Configuration defaults for the rice grain counting pipeline."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelineConfig:
    """Parameters shared by preprocessing, segmentation, and counting."""

    # Đường dẫn dữ liệu đầu vào.
    dataset_dir: Path = Path("Dataset")

    # Nơi lưu mask, label, contour và bảng kết quả sau khi chạy pipeline.
    output_dir: Path = Path("output")

    # Nơi lưu log local theo dõi mỗi lần thay đổi tham số và chạy batch.
    log_dir: Path = Path("logs")

    # Tiền xử lý: median blur để giảm nhiễu muối tiêu trước khi threshold.
    median_kernel_size: int = 3

    # Tiền xử lý: Gaussian blur kernel dùng để ước lượng nền/ánh sáng không đều.
    background_kernel_size: int = 71

    # Tiền xử lý: giới hạn khuếch đại tương phản cục bộ trong CLAHE.
    clahe_clip_limit: float = 1.5

    # Tiền xử lý: kích thước lưới CLAHE, ảnh hưởng mức tăng tương phản theo vùng.
    clahe_tile_grid_size: tuple[int, int] = (8, 8)

    # Hậu xử lý mask: kernel morphology để mở/đóng vùng hạt sau threshold.
    morphology_kernel_size: int = 3

    # Hậu xử lý mask: số lần giãn nhẹ để bù phần biên hạt bị threshold lấy thiếu.
    mask_dilation_iterations: int = 0

    # Threshold: kích thước vùng cục bộ khi Otsu fallback sang adaptive threshold.
    adaptive_block_size: int = 51

    # Threshold: hằng số C của adaptive threshold, điều chỉnh lượng foreground giữ lại.
    adaptive_c: int = -5

    # Lọc nhiễu/lọc vùng: diện tích nhỏ nhất để một vùng được xem là hạt hợp lệ.
    min_grain_area: int = 100

    # Lọc vùng: diện tích lớn nhất để loại các mảng nền hoặc cụm quá lớn.
    max_grain_area: int = 8000

    # Lọc vùng: tỷ lệ dài/ngắn nhỏ nhất, ưu tiên hình dạng thon dài của hạt gạo.
    min_aspect_ratio: float = 1.2

    # Lọc vùng: tỷ lệ dài/ngắn lớn nhất, loại vùng quá dài hoặc nhiễu dạng vệt.
    max_aspect_ratio: float = 10.0

    # Lọc vùng: độ đặc tối thiểu, loại vùng rỗng/méo nhưng vẫn giữ hạt bị dính nhẹ.
    min_solidity: float = 0.50

    # Lọc vùng: độ thuôn dài tối thiểu, giúp loại nhiễu không giống hình hạt gạo.
    min_eccentricity: float = 0.70

    # Watershed: khoảng cách tối thiểu giữa marker, kiểm soát tách hạt dính nhau.
    min_peak_distance: int = 13

    # Watershed: chỉ tách component có diện tích lớn hơn median area theo hệ số này.
    watershed_split_area_factor: float = 1.30


DEFAULT_CONFIG = PipelineConfig()
