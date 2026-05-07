# Computer Vision - Đếm Hạt Gạo

Project này dùng một pipeline xử lý ảnh duy nhất để đếm hạt gạo trong toàn bộ ảnh đầu vào. Pipeline không chọn tham số theo từng ảnh, không nhận input phụ ngoài tên ảnh, và chỉ dùng các quyết định tự động dựa trên đặc trưng ảnh trung gian.

## 1. Mục Tiêu

Đầu vào là ảnh trong thư mục `Dataset/`. Đầu ra gồm:

- Số hạt gạo đếm được.
- Mask phân đoạn hạt.
- Label màu sau watershed và lọc vùng.
- Ảnh contour overlay để kiểm tra trực quan.
- Bảng kết quả `output/results.csv`.

Các trường hợp ảnh cần xử lý:

- `gạo_bình_thường.png`: nền tương đối đều, hạt sáng và biên rõ.
- `gạo_nhiễu_muối_tiêu.png`: có điểm nhiễu trắng/đen dễ bị đếm nhầm.
- `gạo_nền_không_đều.png`: nền có sọc sáng tối, dễ sinh foreground giả.
- `gạo_tương_phản_thấp.png`: hạt và nền gần nhau về cường độ, biên yếu.

## 2. Pipeline Đã Chốt

Pipeline cuối cùng:

```text
Đọc ảnh
-> Chuyển grayscale
-> Lọc median
-> Fourier homomorphic filtering
-> Fourier notch trên profile cột
-> CLAHE
-> Otsu threshold, fallback adaptive nếu foreground ratio bất thường
-> Remove small objects, morphology opening/closing, fill holes
-> Distance transform
-> Watershed có điều kiện cho component lớn
-> Lọc vùng theo diện tích, tỷ lệ trục ellipse, solidity, eccentricity
-> Đếm hạt và lưu kết quả
```

Giải thích từng bước:

1. `to_grayscale`: đưa ảnh RGB hoặc grayscale về một kênh cường độ.
2. `denoise_image`: dùng median blur để giảm nhiễu muối tiêu nhưng vẫn giữ biên hạt tốt hơn lọc trung bình.
3. `correct_illumination_fourier`: dùng homomorphic filtering trong miền tần số để giảm biến thiên sáng tối chậm của nền.
4. `suppress_stripes_fourier`: lấy median profile theo cột, tìm các đỉnh tần số mạnh gây sọc nền, rồi trừ thành phần sọc đã ước lượng khỏi ảnh.
5. `correct_illumination`: gói cố định hai bước Fourier ở trên. Đây là bước hiệu chỉnh nền duy nhất trong code hiện tại.
6. `enhance_contrast`: dùng CLAHE để tăng tương phản cục bộ, hỗ trợ ảnh tương phản thấp.
7. `threshold_grains`: dùng Otsu trước; nếu tỷ lệ foreground quá thấp hoặc quá cao thì tự fallback sang adaptive threshold.
8. `clean_mask`: xóa vùng nhỏ, opening/closing, fill holes và tùy chọn giãn mask nhẹ.
9. `watershed_separation`: chỉ tách watershed với component lớn hơn ngưỡng diện tích tương đối, giúp giảm nguy cơ tách đôi một hạt đơn.
10. `filter_grain_regions`: giữ vùng có hình dạng giống hạt gạo dựa trên diện tích, tỷ lệ trục ellipse, solidity và eccentricity.
11. `separate_and_count`: trả về số hạt, số vùng bị loại và label cuối cùng.

## 3. Vì Sao Chọn Pipeline Này

Pipeline này xử lý trực tiếp bốn vấn đề chính:

- Nhiễu muối tiêu: xử lý bằng median blur, morphology và lọc diện tích.
- Nền không đều: xử lý bằng Fourier homomorphic và Fourier notch.
- Tương phản thấp: xử lý bằng CLAHE và fallback threshold tự động.
- Hạt dính nhau: xử lý bằng distance transform và watershed có điều kiện.

Phần lọc vùng hiện dùng tỷ lệ trục ellipse (`axis_major_length / axis_minor_length`) thay cho tỷ lệ bounding box. Cách này phù hợp hơn với hạt gạo nằm chéo vì bounding box của hạt chéo có thể gần vuông dù bản thân hạt vẫn thuôn dài.

## 4. Tham Số Chính

Các tham số nằm trong `src/config.py`:

- `median_kernel_size`: mức lọc nhiễu muối tiêu.
- `fourier_cutoff`: bán kính tách nền tần số thấp trong homomorphic filtering.
- `fourier_low_gain`: mức giữ lại thành phần chiếu sáng nền.
- `fourier_high_gain`: mức nhấn chi tiết và biên hạt.
- `fourier_stripe_min_frequency`, `fourier_stripe_max_frequency`: dải tần số được xem là sọc nền.
- `fourier_stripe_top_k`: số đỉnh phổ mạnh nhất bị triệt.
- `fourier_stripe_radius`: độ rộng vùng triệt quanh mỗi đỉnh phổ.
- `fourier_stripe_strength`: cường độ trừ thành phần sọc nền.
- `clahe_clip_limit`, `clahe_tile_grid_size`: mức tăng tương phản cục bộ.
- `adaptive_block_size`, `adaptive_c`: tham số cho adaptive threshold khi Otsu fallback.
- `otsu_min_foreground_ratio`, `otsu_max_foreground_ratio`: ngưỡng quyết định Otsu có bất thường hay không.
- `min_grain_area`, `max_grain_area`: giới hạn diện tích vùng hợp lệ.
- `min_aspect_ratio`, `max_aspect_ratio`: giới hạn tỷ lệ trục ellipse.
- `min_solidity`, `min_eccentricity`: lọc vùng méo, rỗng hoặc không thuôn dài.
- `min_peak_distance`: khoảng cách marker watershed.
- `watershed_split_area_factor`: quyết định component nào đủ lớn để tách watershed.

## 5. Thư Viện Sử Dụng

Cài đặt:

```powershell
pip install -r requirements.txt
```

Thư viện chính:

- `opencv-python`: đọc/ghi ảnh, chuyển màu, threshold, morphology, CLAHE và contour.
- `numpy`: xử lý ma trận ảnh và biến đổi Fourier.
- `scipy`: `distance_transform_edt` và `binary_fill_holes`.
- `scikit-image`: connected components, `regionprops`, `peak_local_max`, watershed.
- `matplotlib`: hiển thị ảnh và histogram trong notebook.
- `pandas`: hiển thị bảng thống kê trong notebook.
- `ipykernel`: chạy notebook trong Jupyter hoặc VS Code.
- `pytest`: kiểm tra local trong quá trình phát triển; thư mục `tests/` không đưa vào Git.

## 6. Chạy Project

Chạy một ảnh:

```powershell
python src/main.py gạo_bình_thường.png
```

Chạy toàn bộ dataset từ Python hoặc notebook:

```python
from main import run_all_images
from config import DEFAULT_CONFIG

run_all_images(DEFAULT_CONFIG)
```

Notebook:

```text
notebooks/rice_counting_pipeline.ipynb
```

Notebook dùng trực tiếp code trong `src/`. Sau khi sửa `src/config.py` hoặc code trong `src/`, cần chạy lại cell setup đầu tiên để reload module mới.

## 7. Output Và Log

Output chính:

```text
output/
|-- masks/
|-- contours/
|-- labels/
|-- intermediate/
`-- results.csv
```

Log local:

```text
logs/
|-- parameter_runs.md
|-- parameter_runs.csv
`-- latest_run.json
```

`logs/` chỉ dùng để theo dõi thử nghiệm ở local và đã được ignore. Mỗi lần chạy batch, log ghi lại tham số thay đổi, ảnh hưởng dự kiến của tham số và kết quả từng ảnh.

## 8. Kết Quả Hiện Tại

| Ảnh | Số hạt đếm được | Vùng bị loại |
| --- | ---: | ---: |
| `gạo_bình_thường.png` | 101 | 2 |
| `gạo_nhiễu_muối_tiêu.png` | 100 | 2 |
| `gạo_nền_không_đều.png` | 107 | 3 |
| `gạo_tương_phản_thấp.png` | 96 | 0 |

Ảnh bình thường đạt 101 hạt, khớp mốc đếm tay hiện tại. Ảnh nền không đều vẫn là ca cần kiểm tra trực quan kỹ nhất bằng label màu và contour overlay.

## 9. Cấu Trúc Project

```text
Computer-Vision/
|-- Dataset/
|   |-- gạo_bình_thường.png
|   |-- gạo_nhiễu_muối_tiêu.png
|   |-- gạo_nền_không_đều.png
|   `-- gạo_tương_phản_thấp.png
|
|-- src/
|   |-- main.py
|   |-- config.py
|   |-- parameter_log.py
|   |-- preprocess.py
|   |-- segment.py
|   |-- watershed_count.py
|   |-- visualize.py
|   `-- utils.py
|
|-- notebooks/
|   `-- rice_counting_pipeline.ipynb
|
|-- output/
|-- logs/        # local-only
|-- tests/       # local-only
|-- report/
|   `-- rice_counting_report.md
|
|-- requirements.txt
`-- README.md
```

Vai trò file:

- `src/main.py`: entry point chạy một ảnh hoặc toàn bộ dataset.
- `src/config.py`: tham số chung cho pipeline cuối.
- `src/preprocess.py`: grayscale, median, Fourier homomorphic, Fourier notch, CLAHE.
- `src/segment.py`: threshold tự động, morphology, fill holes.
- `src/watershed_count.py`: watershed có điều kiện, lọc vùng và đếm hạt.
- `src/visualize.py`: lưu mask, label và contour overlay.
- `src/utils.py`: đọc/ghi ảnh, tạo output, lưu CSV.
- `src/parameter_log.py`: ghi log local khi chạy batch.
- `report/rice_counting_report.md`: báo cáo tóm tắt phương pháp và kết quả.
