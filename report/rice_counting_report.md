# Báo Cáo Bài Toán Đếm Hạt Gạo

## 1. Giới thiệu

Tài liệu này tổng hợp phân tích bài toán, pipeline xử lý ảnh, kết quả thực nghiệm và nhận xét cho bài tập đếm hạt gạo trong ảnh.

Mục tiêu của bài toán là đếm số lượng hạt gạo trong từng ảnh đầu vào bằng một pipeline xử lý ảnh duy nhất. Pipeline không chỉnh tham số thủ công theo từng ảnh và chỉ nhận tên ảnh làm đầu vào khi chạy xử lý.

## 2. Phân tích dữ liệu

Bộ dữ liệu gồm 4 trường hợp chính:

- Ảnh bình thường.
- Ảnh nhiễu muối tiêu.
- Ảnh nền không đều.
- Ảnh tương phản thấp.

Các trường hợp này đại diện cho những khó khăn thường gặp trong bài toán phân đoạn ảnh:

- Nhiễu nhỏ có thể bị nhận nhầm là hạt gạo.
- Hạt dính nhau có thể bị đếm thiếu nếu chỉ dùng connected components.
- Ánh sáng không đều làm threshold toàn cục kém ổn định.
- Tương phản thấp làm biên hạt yếu và dễ mất vùng foreground.

## 3. Pipeline xử lý

Pipeline chính được chọn là:

Đọc ảnh
-> Chuyển grayscale
-> Lọc median
-> Hiệu chỉnh nền
-> Tăng tương phản bằng CLAHE
-> Threshold tự động
-> Morphology, fill holes và tùy chọn giãn mask nhẹ
-> Distance transform
-> Watershed có điều kiện cho component lớn
-> Lọc vùng theo diện tích, tỷ lệ trục ellipse, solidity và eccentricity
-> Đếm hạt

Pipeline sử dụng Otsu threshold làm lựa chọn mặc định. Nếu mask sau Otsu có tỷ lệ foreground bất thường, pipeline tự động chuyển sang adaptive threshold. Đây vẫn là một pipeline duy nhất vì việc chuyển threshold được quyết định tự động từ đặc trưng của mask, không dựa trên tên ảnh và không chỉnh tay theo từng ảnh.

Ở bước lọc vùng, pipeline không dùng tỷ lệ dài/ngắn của bounding box làm tiêu chí chính nữa. Thay vào đó, vùng được đánh giá bằng tỷ lệ trục ellipse (`axis_major_length / axis_minor_length`) từ `regionprops`. Cách này phù hợp hơn với hạt gạo nằm chéo, vì bounding box của hạt chéo có thể gần vuông dù bản thân hạt vẫn thuôn dài.

## 4. Kết quả thực nghiệm

Notebook và script đã chạy thành công trên 4 ảnh trong `Dataset/`. Kết quả tổng hợp được lưu tại `output/results.csv`. Các ảnh minh họa được tạo trong:

- `output/masks/`
- `output/labels/`
- `output/contours/`
- `output/intermediate/`

Bảng kết quả:

| Ảnh | Loại ảnh | Số hạt đếm được | Vùng bị loại | Threshold | Foreground ratio | Component sau clean |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| `gạo_bình_thường.png` | Bình thường | 101 | 0 | Otsu | 0.2726 | 97 |
| `gạo_nhiễu_muối_tiêu.png` | Nhiễu muối tiêu | 100 | 1 | Otsu | 0.2708 | 96 |
| `gạo_nền_không_đều.png` | Nền không đều | 139 | 21 | Adaptive | 0.4684 | 90 |
| `gạo_tương_phản_thấp.png` | Tương phản thấp | 96 | 0 | Otsu | 0.1516 | 93 |

Nhận xét nhanh:

- Ảnh bình thường đạt 101 hạt, khớp với số đếm tay dùng làm mốc hiệu chỉnh.
- Sau khi đổi sang tỷ lệ trục ellipse, nhiều hạt nằm chéo được giữ lại tốt hơn so với cách dùng bounding box aspect ratio.
- Ảnh nhiễu muối tiêu vẫn giữ kết quả gần ảnh bình thường, cho thấy median blur và morphology đã giảm nhiễu nhỏ trước khi đếm.
- Ảnh nền không đều được chuyển sang adaptive threshold, đúng với kỳ vọng vì nền sáng tối không đều làm threshold toàn cục kém ổn định. Đây vẫn là ảnh khó nhất và cần kiểm tra contour overlay để phát hiện foreground giả.
- Ảnh tương phản thấp có foreground ratio thấp hơn, nhưng CLAHE giúp hạt vẫn được tách ra để đếm.

## 5. Nhận xét chi tiết

### Nhiễu

Nhiễu muối tiêu tạo nhiều điểm trắng hoặc đen nhỏ trên ảnh. Nếu threshold trực tiếp, các điểm nhiễu sáng có thể bị nhận nhầm là hạt gạo nhỏ. Pipeline xử lý bằng median blur trước threshold, sau đó dùng morphology, remove small objects và lọc hình dạng để loại các vùng nhiễu nhỏ hoặc không có dạng thuôn dài. Kết quả hiện tại của ảnh nhiễu muối tiêu là 100, gần với ảnh bình thường, cho thấy nhiễu nhỏ đã được xử lý trước khi bước watershed và filter quyết định số lượng cuối.

### Hạt dính nhau

Các hạt gạo gần nhau có thể bị gộp thành một component lớn. Nếu chỉ dùng connected components, các vùng này dễ bị đếm thiếu. Pipeline dùng distance transform và watershed để tạo marker tại vùng trung tâm của từng hạt, sau đó tách các vùng chạm nhau. Để tránh một hạt dài bị tách đôi, watershed chỉ được áp dụng cho các connected component có diện tích lớn hơn median area của các vùng ứng viên theo hệ số `watershed_split_area_factor`.

Tuy nhiên watershed vẫn có rủi ro:

- Nếu marker quá dày, một hạt có thể bị tách thành nhiều vùng.
- Nếu marker quá thưa, các hạt dính nhau vẫn có thể bị đếm thiếu.

### Ánh sáng không đều

Ảnh nền không đều là trường hợp khó nhất vì nền có vùng sáng tối thay đổi mạnh. Pipeline dùng bước hiệu chỉnh nền trước threshold. Sau đó, nếu Otsu tạo mask bất thường, pipeline tự động chuyển sang adaptive threshold.

Kết quả đếm của ảnh nền không đều là 139, cao hơn ảnh bình thường. Điều này cho thấy adaptive threshold giúp giữ lại vùng hạt trong nền khó, nhưng cũng có thể giữ thêm foreground giả ở các vùng nền sáng. Đây là trường hợp cần đánh giá trực quan kỹ nhất bằng label màu và contour overlay.

### Tương phản thấp

Ảnh tương phản thấp có foreground ratio 0.1516, thấp hơn các ảnh còn lại. CLAHE giúp tăng tương phản cục bộ, làm hạt rõ hơn trước khi threshold. Việc bỏ dilation sau mask giúp contour ít bị phình nhưng cũng cần theo dõi nguy cơ mất biên ở các hạt yếu.

Dù vậy, biên hạt trong ảnh tương phản thấp vẫn có thể yếu. Khi kiểm tra overlay, cần chú ý các hạt ở vùng tối hoặc sát biên ảnh vì chúng dễ bị mất biên hoặc bị lọc bỏ.

### Lỗi còn lại

- Hạt bị cắt ở biên ảnh có thể bị loại nếu diện tích hoặc tỷ lệ trục không đạt ngưỡng.
- Hạt quá gần nhau có thể bị watershed tách sai.
- Nền không đều có thể tạo foreground giả trong vùng quá sáng.
- Nếu dữ liệu mới khác nhiều về kích thước hạt hoặc độ phân giải, cần chọn lại một bộ tham số chung cho toàn bộ tập ảnh, không chỉnh riêng từng ảnh khi đánh giá.

## 6. Kết luận

Pipeline hiện tại đáp ứng các yêu cầu bắt buộc:

- Sử dụng một pipeline xử lý ảnh duy nhất cho tất cả ảnh.
- Không chỉnh tham số thủ công theo từng ảnh.
- Sử dụng threshold tự động gồm Otsu và adaptive fallback.
- Khi chạy script, đầu vào xử lý chính chỉ là tên ảnh.

Pipeline cho kết quả ổn định với ảnh bình thường, ảnh nhiễu muối tiêu và ảnh tương phản thấp. Trường hợp nền không đều vẫn là trường hợp khó nhất và cần được đánh giá trực quan bằng ảnh contour overlay.
