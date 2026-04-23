# Bao cao bai toan dem hat gao

## 1. Gioi thieu

Tai lieu nay se tong hop phan tich bai toan, pipeline xu ly anh, ket qua thuc nghiem va nhan xet cho bai tap dem hat gao.

## 2. Phan tich du lieu

- Anh binh thuong
- Anh nhieu muoi tieu
- Anh nen khong deu
- Anh tuong phan thap

## 3. Pipeline xu ly

Pipeline chinh duoc chon: tien xu ly robust, hieu chinh nen, CLAHE, threshold va watershed.

## 4. Ket qua thuc nghiem

Notebook da chay thanh cong tren 4 anh trong `Dataset/`. Ket qua duoc luu tam thoi tai `output/results.csv` va cac anh minh hoa duoc tao trong `output/masks/`, `output/labels/`, `output/contours/`, `output/intermediate/`.

Bang ket qua:

| Anh | Loai anh | So hat dem duoc | Vung bi loai | Threshold | Foreground ratio | Component sau clean |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| `gạo_bình_thường.png` | Bình thường | 111 | 56 | Otsu | 0.2920 | 124 |
| `gạo_nhiễu_muối_tiêu.png` | Nhiễu muối tiêu | 111 | 55 | Otsu | 0.2875 | 124 |
| `gạo_nền_không_đều.png` | Nền không đều | 143 | 58 | Adaptive | 0.4578 | 120 |
| `gạo_tương_phản_thấp.png` | Tương phản thấp | 110 | 38 | Otsu | 0.1513 | 95 |

Nhan xet nhanh:

- Anh binh thuong va anh nhieu muoi tieu cho ket qua gan nhau, cho thay median blur va morphology giup pipeline on dinh truoc nhieu muoi tieu.
- Anh nen khong deu duoc chuyen sang adaptive threshold, dung voi ky vong vi nen sinus lam threshold toan cuc kem on dinh hon.
- Anh tuong phan thap co foreground ratio thap hon, nhung CLAHE giup hat van duoc tach ra de dem.
- So vung bi loai cho thay buoc loc hinh dang dang loai nhieu vung khong dat dieu kien area/aspect ratio/solidity.

## 5. Nhan xet

### Nhieu

Nhiễu muối tiêu tạo nhiều điểm trắng/đen nhỏ. Pipeline dùng median blur trước threshold và remove small objects sau threshold nên kết quả của ảnh nhiễu muối tiêu vẫn giữ cùng số đếm 111 như ảnh bình thường.

### Hat dinh nhau

Hat gan nhau co the bi gop thanh mot component. Buoc distance transform va watershed tao marker tai cac tam hat de tach cac vung cham nhau. Tuy nhien neu marker qua day thi mot hat co the bi tach qua muc; neu marker qua thua thi cac hat dinh nhau van bi dem thieu.

### Anh sang khong deu

Anh nen sinus la truong hop kho nhat vi nen co vung sang toi manh. Pipeline dung background correction va adaptive threshold fallback. Ket qua dem la 143, cao hon anh binh thuong, nen can kiem tra contour overlay de xac dinh co dem du hay dem nham nen sang.

### Tương phản thấp

Anh tuong phan thap co foreground ratio 0.1513, thap hon cac anh con lai. CLAHE giup tang tuong phan cuc bo, nhung bien hat co the van yeu. Khi kiem tra overlay, can chu y cac hat o vung toi hoac sat bien anh.

### Loi con lai

- Hat bi cat o bien anh co the bi loai neu dien tich hoac aspect ratio khong dat nguong.
- Hat qua gan nhau co the bi watershed tach sai.
- Nền không đều có thể tạo foreground giả trong vùng quá sáng.
- Tham so `min_peak_distance`, `min_grain_area`, `max_grain_area` can duoc tinh chinh neu overlay cho thay dem thieu hoac dem du.
