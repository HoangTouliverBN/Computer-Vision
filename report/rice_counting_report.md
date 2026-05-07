# Báo Cáo Bài Toán Đếm Hạt Gạo

## 1. Giới Thiệu

Bài toán là đếm số hạt gạo trong ảnh bằng một pipeline xử lý ảnh duy nhất. Pipeline dùng chung một bộ tham số cho toàn bộ dataset, không chỉnh tay theo từng ảnh và khi chạy script chỉ nhận tên ảnh làm đầu vào.

Dataset gồm bốn nhóm ảnh:

- Ảnh bình thường.
- Ảnh nhiễu muối tiêu.
- Ảnh nền không đều.
- Ảnh tương phản thấp.

Các khó khăn chính là nhiễu nhỏ, hạt dính nhau, nền sáng tối không đều, biên yếu và nguy cơ mất hạt sau khi lọc vùng.

## 2. Pipeline Cuối Cùng

Pipeline đã chốt:

```text
Đọc ảnh
-> Chuyển grayscale
-> Lọc median
-> Fourier homomorphic filtering
-> Fourier notch trên profile cột
-> CLAHE
-> Otsu threshold, fallback adaptive nếu foreground ratio bất thường
-> Morphology và fill holes
-> Distance transform
-> Watershed có điều kiện
-> Lọc vùng theo hình dạng
-> Đếm hạt
```

Pipeline này là pipeline duy nhất trong implementation hiện tại. Code không còn nhánh chọn phương pháp hiệu chỉnh nền khác; bước hiệu chỉnh nền được cố định bằng Fourier.

## 3. Phân Tích Các Bước Xử Lý

### Grayscale

Ảnh RGB được chuyển về ảnh xám để toàn bộ pipeline xử lý trên cường độ sáng. Nếu ảnh đầu vào đã là grayscale thì giữ nguyên bản sao của ảnh.

### Median Blur

Median blur giảm nhiễu muối tiêu bằng cách thay mỗi pixel bằng giá trị trung vị trong vùng lân cận. Bước này ít làm mờ biên hơn so với lọc trung bình, nên phù hợp với hạt gạo có biên mảnh.

Tham số ảnh hưởng:

- `median_kernel_size` tăng thì lọc nhiễu mạnh hơn nhưng có thể làm mất chi tiết biên.
- `median_kernel_size` giảm thì giữ biên tốt hơn nhưng có thể còn điểm nhiễu.

### Fourier Homomorphic Filtering

Ảnh được đưa sang miền log rồi biến đổi Fourier. Thành phần tần số thấp thường biểu diễn ánh sáng nền thay đổi chậm, còn chi tiết hạt nằm ở tần số cao hơn. Bộ lọc homomorphic làm giảm nền chậm và giữ chi tiết hạt trước khi đưa ảnh về miền không gian.

Tham số ảnh hưởng:

- `fourier_cutoff`: điều khiển vùng tần số thấp bị giảm.
- `fourier_low_gain`: mức giữ lại ánh sáng nền.
- `fourier_high_gain`: mức nhấn chi tiết và biên hạt.

### Fourier Notch Trên Profile Cột

Ảnh nền không đều có sọc theo phương cột. Homomorphic filtering xử lý tốt biến thiên nền chậm nhưng chưa triệt hết sọc có tính chu kỳ. Vì vậy pipeline lấy median intensity theo từng cột, biến đổi Fourier một chiều, tìm các đỉnh phổ mạnh trong dải tần đã cấu hình, rồi trừ thành phần sọc ước lượng khỏi ảnh.

Tham số ảnh hưởng:

- `fourier_stripe_min_frequency`, `fourier_stripe_max_frequency`: xác định dải tần được xem là sọc nền.
- `fourier_stripe_top_k`: số đỉnh phổ bị triệt.
- `fourier_stripe_radius`: độ rộng vùng triệt quanh mỗi đỉnh.
- `fourier_stripe_strength`: cường độ trừ thành phần sọc.

### CLAHE

CLAHE tăng tương phản cục bộ sau khi nền đã được hiệu chỉnh. Bước này giúp ảnh tương phản thấp tách hạt rõ hơn, nhưng nếu tăng quá mạnh có thể làm nhiễu hoặc sọc còn sót rõ hơn.

Tham số ảnh hưởng:

- `clahe_clip_limit`: mức khuếch đại tương phản cục bộ.
- `clahe_tile_grid_size`: kích thước vùng cục bộ dùng cho CLAHE.

### Threshold Tự Động

Pipeline dùng Otsu threshold trước. Sau đó tính `foreground_ratio`, tức tỷ lệ pixel được xem là foreground trong mask. Nếu tỷ lệ này quá thấp hoặc quá cao so với ngưỡng cấu hình, pipeline tự động chuyển sang adaptive threshold.

Đây vẫn là một pipeline duy nhất vì quyết định fallback dựa trên thống kê mask, không dựa trên tên ảnh và không chỉnh tay theo từng ảnh.

Tham số ảnh hưởng:

- `otsu_min_foreground_ratio`: nếu Otsu lấy quá ít foreground thì fallback.
- `otsu_max_foreground_ratio`: nếu Otsu lấy quá nhiều foreground thì fallback.
- `adaptive_block_size`, `adaptive_c`: điều khiển adaptive threshold khi fallback xảy ra.

### Làm Sạch Mask

Mask sau threshold được xóa vùng nhỏ, morphology opening/closing và fill holes. Mục tiêu là bỏ nhiễu, nối vùng hạt bị thủng nhẹ và tạo vùng candidate ổn định cho watershed.

Tham số ảnh hưởng:

- `morphology_kernel_size`: kernel càng lớn thì làm sạch mạnh hơn nhưng dễ biến dạng vùng hạt.
- `mask_dilation_iterations`: giãn mask để bù biên thiếu, nhưng tăng quá mức có thể làm dính hạt.
- `min_grain_area`: loại vùng nhỏ trước và sau morphology.

### Watershed Có Điều Kiện

Distance transform tạo bản đồ khoảng cách bên trong mask. Marker được lấy từ các cực đại cục bộ, sau đó watershed tách các component lớn. Pipeline không tách mọi component; chỉ component có diện tích lớn hơn `median_area * watershed_split_area_factor` mới được đưa vào watershed. Cách này giảm nguy cơ một hạt đơn bị tách đôi.

Tham số ảnh hưởng:

- `min_peak_distance`: khoảng cách tối thiểu giữa marker.
- `watershed_split_area_factor`: quyết định component nào đủ lớn để tách.

### Lọc Vùng Và Đếm

Sau watershed, mỗi label được đánh giá bằng `regionprops`. Vùng hợp lệ phải đạt điều kiện về diện tích, tỷ lệ trục ellipse, solidity và eccentricity.

Pipeline dùng tỷ lệ trục ellipse thay cho tỷ lệ bounding box vì hạt gạo có thể nằm chéo. Bounding box của hạt chéo dễ bị gần vuông, trong khi ellipse axis ratio phản ánh tốt hơn hình dạng thuôn dài thật của hạt.

Tham số ảnh hưởng:

- `min_grain_area`, `max_grain_area`: giới hạn diện tích.
- `min_aspect_ratio`, `max_aspect_ratio`: giới hạn tỷ lệ trục ellipse.
- `min_solidity`: loại vùng méo, rỗng hoặc biên không kín.
- `min_eccentricity`: ưu tiên vùng thuôn dài giống hạt gạo.

## 4. Kết Quả Thực Nghiệm

Kết quả hiện tại:

| Ảnh | Loại ảnh | Số hạt đếm được | Vùng bị loại | Threshold | Foreground ratio | Component sau clean |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| `gạo_bình_thường.png` | Bình thường | 101 | 2 | Otsu | 0.2720 | 97 |
| `gạo_nhiễu_muối_tiêu.png` | Nhiễu muối tiêu | 100 | 2 | Otsu | 0.2718 | 96 |
| `gạo_nền_không_đều.png` | Nền không đều | 107 | 3 | Otsu | 0.2851 | 99 |
| `gạo_tương_phản_thấp.png` | Tương phản thấp | 96 | 0 | Adaptive | 0.1431 | 92 |

Nhận xét:

- Ảnh bình thường đạt 101 hạt, khớp với mốc đếm tay hiện tại.
- Ảnh nhiễu muối tiêu vẫn gần ảnh bình thường, cho thấy median blur và morphology đang kiểm soát nhiễu tốt.
- Ảnh nền không đều được cải thiện nhờ Fourier notch, số vùng bị loại thấp hơn và ít foreground giả hơn.
- Ảnh tương phản thấp dùng adaptive fallback do Otsu lấy foreground thấp hơn ngưỡng cấu hình.

## 5. Vấn Đề Còn Lại

- Hạt bị cắt ở biên ảnh có thể bị loại nếu diện tích hoặc tỷ lệ trục không đạt ngưỡng.
- Watershed vẫn có thể tách đôi một hạt nếu marker nằm quá gần nhau.
- Nếu tăng độ nhạy để giữ thêm hạt thật, ảnh nền không đều có thể nhận thêm nhiễu nền.
- Nếu siết lọc vùng để bỏ nhiễu mạnh hơn, một số hạt thật bị yếu biên hoặc bị cắt có thể mất.

Do đó khi điều chỉnh tham số cần chạy lại toàn bộ dataset và xem cả số đếm lẫn contour overlay, không đánh giá chỉ bằng một ảnh.

## 6. Kết Luận

Pipeline hiện tại đáp ứng yêu cầu:

- Một pipeline duy nhất cho tất cả ảnh.
- Không chỉnh tham số riêng theo từng ảnh.
- Có threshold tự động bằng Otsu và adaptive fallback.
- Đầu vào xử lý chính chỉ là tên ảnh.
- Code đã chốt về một hướng hiệu chỉnh nền bằng Fourier, không còn nhánh phương pháp cũ trong preprocessing.

Phương án này cân bằng tốt giữa khả năng đếm đúng, khả năng giải thích từng bước và khả năng kiểm tra trực quan bằng ảnh trung gian.
