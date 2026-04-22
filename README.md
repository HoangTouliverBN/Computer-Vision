# Computer Vision - Rice Grain Counting

## 1. Phân tích bài toán

Bài toán là đếm số hạt gạo trong ảnh bằng các kỹ thuật xử lý ảnh cổ điển. Đầu vào là ảnh grayscale hoặc RGB, đầu ra gồm số lượng hạt gạo, ảnh mask phân đoạn, ảnh contour hoặc label để kiểm tra trực quan.

Dataset hiện tại có các trường hợp chính:

### Ảnh bình thường

- Hạt gạo sáng hơn nền.
- Nền tương đối đồng đều.
- Biên hạt khá rõ.
- Có một số hạt bị cắt ở rìa ảnh.
- Một vài hạt gần nhau hoặc dính nhau.

Cách xử lý phù hợp: lọc nhẹ, threshold toàn cục hoặc Otsu, morphology, connected components.

### Ảnh nhiễu muối tiêu

- Có nhiều điểm trắng/đen rải rác.
- Nếu threshold trực tiếp, nhiễu trắng có thể bị đếm nhầm là hạt nhỏ.
- Nhiễu đen có thể làm thủng vùng hạt gạo.

Cách xử lý phù hợp: median filter trước khi threshold, sau đó morphology opening/closing và lọc object theo diện tích.

### Ảnh nền không đều

- Nền có biến thiên sáng tối dạng sóng.
- Một số vùng nền sáng gần bằng hoặc cao hơn vùng hạt tối.
- Threshold toàn cục dễ sai: vùng nền sáng bị nhận là hạt, vùng hạt tối bị mất.

Cách xử lý phù hợp: hiệu chỉnh nền trước, ví dụ Gaussian background subtraction, top-hat, hoặc adaptive threshold.

### Ảnh tương phản thấp

- Hạt và nền khác nhau ít về cường độ.
- Biên hạt yếu.
- Threshold dễ mất hạt hoặc tạo vùng hạt không đầy đủ.

Cách xử lý phù hợp: tăng tương phản bằng CLAHE, chuẩn hóa cường độ, sau đó threshold thích nghi.

## 2. Đề xuất pipeline xử lý ảnh

### Pipeline 1: Threshold cơ bản + Connected Components

Các bước:

1. Đọc ảnh.
2. Chuyển ảnh sang grayscale.
3. Làm mượt nhẹ bằng Gaussian blur hoặc median blur.
4. Dùng Otsu threshold để tách hạt sáng khỏi nền tối.
5. Morphology opening để xóa nhiễu nhỏ.
6. Morphology closing hoặc fill holes để làm đầy hạt.
7. Dùng connected components hoặc find contours.
8. Lọc object theo diện tích, kích thước bounding box và aspect ratio.
9. Đếm số component hợp lệ.

Ưu điểm:

- Đơn giản, dễ implement.
- Chạy nhanh.
- Tốt với ảnh bình thường.

Nhược điểm:

- Kém với nền không đều.
- Kém với ảnh tương phản thấp.
- Hạt dính nhau dễ bị đếm thành một.
- Nhạy với nhiễu nếu lọc chưa đủ tốt.

### Pipeline 2: Tiền xử lý robust + Threshold + Watershed

Các bước:

1. Đọc ảnh và chuyển sang grayscale.
2. Khử nhiễu bằng median blur cho nhiễu muối tiêu, kết hợp Gaussian blur nhẹ nếu cần.
3. Hiệu chỉnh nền không đều bằng Gaussian blur kernel lớn hoặc morphological opening.
4. Chuẩn hóa ảnh bằng phép trừ nền hoặc chia nền đã làm mượt.
5. Tăng tương phản bằng CLAHE.
6. Threshold bằng Otsu trên ảnh đã hiệu chỉnh, hoặc adaptive threshold nếu nền vẫn không đều.
7. Morphology opening để bỏ nhiễu nhỏ.
8. Morphology closing và fill holes để làm đầy vùng hạt.
9. Tách hạt dính nhau bằng distance transform, marker extraction và watershed.
10. Lọc kết quả theo diện tích, aspect ratio, solidity hoặc extent.
11. Đếm số label cuối cùng.
12. Xuất ảnh kiểm tra gồm mask, contour và label màu.

Ưu điểm:

- Phù hợp nhất cho cả bốn loại ảnh.
- Xử lý được nhiễu muối tiêu.
- Có bước sửa nền không đều.
- CLAHE hỗ trợ ảnh tương phản thấp.
- Watershed giúp tách các hạt dính nhau.

Nhược điểm:

- Nhiều bước hơn, cần chọn tham số cẩn thận.
- Watershed có thể tách quá mức nếu marker sai.
- Cần debug bằng ảnh trung gian.
- Chậm hơn pipeline đơn giản, nhưng vẫn phù hợp với ảnh kích thước nhỏ hoặc vừa.

### Pipeline 3: Edge/Contour + Shape Filtering

Các bước:

1. Chuyển ảnh sang grayscale.
2. Khử nhiễu và tăng tương phản.
3. Dùng Canny, gradient hoặc morphological gradient để tìm biên.
4. Đóng biên bằng morphology closing.
5. Fill contour để tạo vùng hạt.
6. Dùng find contours.
7. Fit ellipse hoặc rotated bounding rectangle.
8. Lọc contour theo diện tích, chiều dài/rộng, độ thuôn dài và hình ellipse.
9. Đếm contour hợp lệ.

Ưu điểm:

- Dựa vào hình dạng hạt, không chỉ dựa vào cường độ sáng.
- Có thể tốt khi threshold intensity khó.
- Dễ minh họa bằng contour và ellipse.

Nhược điểm:

- Kém khi mất biên hoặc biên yếu.
- Nhiễu làm sinh nhiều edge giả.
- Hạt dính nhau vẫn khó tách.
- Cần nhiều điều kiện lọc hình học hơn.

## 3. Các vấn đề có thể gặp

### Nhiễu

- Nhiễu muối tiêu tạo điểm trắng nhỏ giống hạt.
- Nhiễu đen làm hạt bị thủng hoặc đứt vùng.

Cách xử lý:

- Dùng median blur.
- Dùng morphology opening để bỏ vùng nhỏ.
- Lọc connected component theo diện tích tối thiểu.

### Hạt dính nhau

- Hai hoặc nhiều hạt sát nhau có thể thành một component.
- Nếu chỉ dùng connected components thì sẽ bị đếm thiếu.

Cách xử lý:

- Dùng distance transform để tìm tâm từng hạt.
- Dùng watershed để tách theo marker.
- Dùng diện tích trung bình để phát hiện component quá lớn.

### Ánh sáng không đều

- Threshold toàn cục thất bại khi nền thay đổi sáng tối.
- Vùng nền sáng có thể bị nhận nhầm là hạt.

Cách xử lý:

- Background subtraction.
- Top-hat transform.
- Adaptive threshold.
- CLAHE sau khi chuẩn hóa nền.

### Mất biên

- Ảnh tương phản thấp làm biên không rõ.
- Morphology quá mạnh có thể làm mất hạt nhỏ hoặc làm dính hạt.

Cách xử lý:

- Tăng tương phản bằng CLAHE.
- Dùng closing nhẹ để nối biên.
- Fill holes để khôi phục vùng hạt.
- Tránh erosion/dilation kernel quá lớn.

## 4. Pipeline cuối cùng được chọn

Pipeline được chọn là **Pipeline 2: Tiền xử lý robust + hiệu chỉnh nền + CLAHE + threshold + watershed**.

Lý do chọn:

- Dataset có đủ bốn tình huống: ảnh bình thường, ảnh nhiễu muối tiêu, ảnh nền không đều và ảnh tương phản thấp.
- Pipeline 1 quá đơn giản, dễ lỗi với nền sinus và ảnh tối hoặc tương phản thấp.
- Pipeline 3 phụ thuộc nhiều vào biên, trong khi ảnh tương phản thấp có thể mất biên.
- Pipeline 2 xử lý trực tiếp từng vấn đề:
  - Median blur xử lý nhiễu muối tiêu.
  - Background correction xử lý nền không đều.
  - CLAHE xử lý tương phản thấp.
  - Watershed xử lý hạt dính nhau.
  - Shape filtering giảm đếm sai.

Pipeline cuối nên là một pipeline thống nhất cho tất cả ảnh, không cần viết riêng chương trình cho từng loại ảnh. Các bước tiền xử lý có thể bật mặc định với tham số vừa phải để không làm hỏng ảnh bình thường.

Pipeline cuối:

1. Load image.
2. Convert grayscale.
3. Median blur.
4. Estimate background bằng Gaussian blur kernel lớn hoặc morphological opening.
5. Normalize/correct illumination.
6. Apply CLAHE.
7. Threshold bằng Otsu, fallback sang adaptive threshold nếu mask bất thường.
8. Morphology opening/closing.
9. Fill holes.
10. Distance transform.
11. Generate markers.
12. Watershed.
13. Filter labels by area and shape.
14. Count rice grains.
15. Save outputs.

## 5. Kế hoạch implement

Thư viện sử dụng:

- `opencv-python`: xử lý ảnh chính.
- `numpy`: tính toán ma trận ảnh.
- `scipy`: fill holes, distance transform hoặc local maxima nếu cần.
- `scikit-image`: watershed, measure regionprops, morphology.
- `matplotlib`: lưu ảnh visualization.
- `pandas`: lưu bảng kết quả CSV.
- `argparse`: chạy script từ command line.

Các bước implement:

1. Tạo cấu trúc project.
2. Viết module đọc ảnh và chuẩn hóa input.
3. Viết module preprocessing:
   - grayscale
   - median blur
   - background correction
   - CLAHE
4. Viết module segmentation:
   - threshold Otsu/adaptive
   - morphology
   - fill holes
5. Viết module separation:
   - distance transform
   - marker extraction
   - watershed
6. Viết module counting:
   - regionprops
   - lọc theo area, aspect ratio, solidity
   - trả về số lượng hạt
7. Viết module visualization:
   - lưu mask
   - lưu contour overlay
   - lưu label màu
8. Viết script chạy toàn bộ dataset.
9. Xuất kết quả:
   - ảnh trung gian
   - ảnh cuối cùng
   - file CSV tổng hợp count từng ảnh
10. Viết báo cáo:
   - phân tích bài toán
   - mô tả pipeline
   - so sánh pipeline
   - kết quả thực nghiệm
   - nhận xét lỗi còn lại.

### Chạy theo notebook

Ngoài cấu trúc code trong `src/`, project có thể chạy trực tiếp bằng notebook:

```text
notebooks/rice_counting_pipeline.ipynb
```

Notebook này được tổ chức theo từng bước xử lý ảnh. Sau mỗi hàm xử lý chính đều có lệnh `print` hoặc `display` để in kết quả ngay lập tức, đồng thời có ảnh trực quan để kiểm tra kết quả trung gian:

- Đọc ảnh: in số ảnh, tên ảnh, shape/dtype/min/max/mean/std của ảnh mẫu và hiển thị toàn bộ ảnh trong `Dataset/`.
- Tiền xử lý: sau `to_grayscale`, `denoise_image`, `correct_illumination`, `enhance_contrast` đều in thống kê ảnh; sau đó hiển thị ảnh trung gian và histogram.
- Phân đoạn: sau `threshold_grains` và `clean_mask` đều in foreground ratio, số foreground pixels và số connected components.
- Watershed/counting: sau `watershed_separation`, `filter_grain_regions`, `count_grains` đều in số label, số vùng accepted/rejected và số hạt cuối cùng.
- Batch run: sau mỗi lần `run_one_image` đều in dictionary kết quả, lưu output và xuất bảng `output/results.csv`.

Cách chạy:

1. Mở `notebooks/rice_counting_pipeline.ipynb` bằng Jupyter Notebook, JupyterLab hoặc VS Code.
2. Cài thư viện nếu thiếu:

```powershell
pip install -r requirements.txt
```

3. Chạy lần lượt các cell từ trên xuống.
4. Nếu kết quả đếm chưa tốt, chỉnh các tham số trong biến `PARAMS` ở đầu notebook rồi chạy lại.

## 6. Cấu trúc project đề xuất

```text
Assigment/
|-- Dataset/
|   |-- rice_normal.png
|   |-- rice_salt_pepper_noise.png
|   |-- rice_uneven_background.png
|   `-- rice_low_contrast.png
|
|-- src/
|   |-- main.py
|   |-- config.py
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
|   |-- masks/
|   |-- contours/
|   |-- labels/
|   |-- intermediate/
|   `-- results.csv
|
|-- report/
|   `-- rice_counting_report.md
|
|-- requirements.txt
`-- README.md
```

Vai trò từng file:

- `main.py`: chạy toàn bộ pipeline cho một ảnh hoặc toàn bộ thư mục.
- `config.py`: chứa tham số như kernel size, area min/max, CLAHE clip limit.
- `preprocess.py`: xử lý grayscale, denoise, background correction, CLAHE.
- `segment.py`: threshold, morphology, fill holes.
- `watershed_count.py`: distance transform, watershed, lọc vùng, đếm hạt.
- `visualize.py`: vẽ contour, label màu, lưu ảnh kết quả.
- `utils.py`: helper đọc ảnh, tạo thư mục output, lưu CSV.
- `results.csv`: bảng kết quả gồm tên ảnh, số hạt đếm được, số object bị loại.
- `rice_counting_report.md`: báo cáo cuối cùng.

## Kết luận

Nên dùng Pipeline 2 làm pipeline chính vì đây là phương án cân bằng nhất giữa độ ổn định và khả năng giải thích. Pipeline này có đủ các bước để xử lý nhiễu, nền không đều, tương phản thấp và hạt dính nhau, đồng thời vẫn dựa trên các kỹ thuật xử lý ảnh cổ điển phù hợp với bài tập Computer Vision.
