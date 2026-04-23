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
-> Morphology, fill holes và giãn mask nhẹ
-> Distance transform
-> Watershed có điều kiện cho component lớn
-> Lọc vùng theo diện tích, hình dạng, solidity và eccentricity
-> Đếm hạt

Pipeline sử dụng Otsu threshold làm lựa chọn mặc định. Nếu mask sau Otsu có tỷ lệ foreground bất thường, pipeline tự động chuyển sang adaptive threshold. Đây vẫn là một pipeline duy nhất vì việc chuyển threshold được quyết định tự động từ đặc trưng của mask, không dựa trên tên ảnh và không chỉnh tay theo từng ảnh.

## 4. Kết quả thực nghiệm

Notebook và script đã chạy thành công trên 4 ảnh trong `Dataset/`. Kết quả tổng hợp được lưu tại `output/results.csv`. Các ảnh minh họa được tạo trong:

- `output/masks/`
- `output/labels/`
- `output/contours/`
- `output/intermediate/`

Bảng kết quả:

| Ảnh | Loại ảnh | Số hạt đếm được | Vùng bị loại | Threshold | Foreground ratio | Component sau clean |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| `gạo_bình_thường.png` | Bình thường | 101 | 49 | Otsu | 0.3386 | 106 |
| `gạo_nhiễu_muối_tiêu.png` | Nhiễu muối tiêu | 93 | 55 | Otsu | 0.3338 | 104 |
| `gạo_nền_không_đều.png` | Nền không đều | 133 | 67 | Adaptive | 0.5312 | 109 |
| `gạo_tương_phản_thấp.png` | Tương phản thấp | 93 | 40 | Otsu | 0.1873 | 94 |

Nhận xét nhanh:

- Ảnh bình thường đạt 101 hạt, khớp với số đếm tay dùng làm mốc hiệu chỉnh.
- Ảnh nhiễu muối tiêu được lọc gắt hơn để giảm đếm nhầm nhiễu, nên số hạt đếm được thấp hơn ảnh bình thường.
- Ảnh nền không đều được chuyển sang adaptive threshold, đúng với kỳ vọng vì nền sáng tối không đều làm threshold toàn cục kém ổn định.
- Ảnh tương phản thấp có foreground ratio thấp hơn, nhưng CLAHE giúp hạt vẫn được tách ra để đếm.
- Số vùng bị loại tăng sau khi bổ sung lọc eccentricity và watershed có điều kiện; điều này giúp giảm các vùng nhiễu không giống hình hạt gạo.

## 5. Nhận xét chi tiết

### Nhiễu

Nhiễu muối tiêu tạo nhiều điểm trắng hoặc đen nhỏ trên ảnh. Nếu threshold trực tiếp, các điểm nhiễu sáng có thể bị nhận nhầm là hạt gạo nhỏ. Pipeline xử lý bằng median blur trước threshold, sau đó dùng morphology, remove small objects và lọc eccentricity để loại các vùng nhiễu nhỏ hoặc không có dạng thuôn dài. Vì vậy kết quả của ảnh nhiễu muối tiêu là 93, thấp hơn ảnh bình thường do bộ lọc ưu tiên giảm đếm nhầm nhiễu.

### Hạt dính nhau

Các hạt gạo gần nhau có thể bị gộp thành một component lớn. Nếu chỉ dùng connected components, các vùng này dễ bị đếm thiếu. Pipeline dùng distance transform và watershed để tạo marker tại vùng trung tâm của từng hạt, sau đó tách các vùng chạm nhau. Để tránh một hạt dài bị tách đôi, watershed chỉ được áp dụng cho các connected component có diện tích lớn hơn median area của các vùng ứng viên.

Tuy nhiên watershed vẫn có rủi ro:

- Nếu marker quá dày, một hạt có thể bị tách thành nhiều vùng.
- Nếu marker quá thưa, các hạt dính nhau vẫn có thể bị đếm thiếu.

### Ánh sáng không đều

Ảnh nền không đều là trường hợp khó nhất vì nền có vùng sáng tối thay đổi mạnh. Pipeline dùng bước hiệu chỉnh nền trước threshold. Sau đó, nếu Otsu tạo mask bất thường, pipeline tự động chuyển sang adaptive threshold.

Kết quả đếm của ảnh nền không đều là 133, cao hơn ảnh bình thường. Điều này cho thấy adaptive threshold giúp giữ lại vùng hạt trong nền khó, nhưng vẫn cần kiểm tra contour overlay để đánh giá có bị đếm nhầm vùng nền sáng hay không.

### Tương phản thấp

Ảnh tương phản thấp có foreground ratio 0.1873, thấp hơn các ảnh nền khó nhưng cao hơn cấu hình trước do mask được giãn nhẹ để bù phần biên hạt bị threshold lấy thiếu. CLAHE giúp tăng tương phản cục bộ, làm hạt rõ hơn trước khi threshold.

Dù vậy, biên hạt trong ảnh tương phản thấp vẫn có thể yếu. Khi kiểm tra overlay, cần chú ý các hạt ở vùng tối hoặc sát biên ảnh vì chúng dễ bị mất biên hoặc bị lọc bỏ.

### Lỗi còn lại

- Hạt bị cắt ở biên ảnh có thể bị loại nếu diện tích hoặc tỷ lệ cạnh không đạt ngưỡng.
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
