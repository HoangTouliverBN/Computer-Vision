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
| `rice_normal.png` | Binh thuong | 111 | 56 | Otsu | 0.2920 | 124 |
| `rice_salt_pepper_noise.png` | Nhieu muoi tieu | 111 | 55 | Otsu | 0.2875 | 124 |
| `rice_uneven_background.png` | Nen khong deu | 143 | 58 | Adaptive | 0.4578 | 120 |
| `rice_low_contrast.png` | Tuong phan thap | 110 | 38 | Otsu | 0.1513 | 95 |

Nhan xet nhanh:

- Anh binh thuong va anh nhieu muoi tieu cho ket qua gan nhau, cho thay median blur va morphology giup pipeline on dinh truoc nhieu muoi tieu.
- Anh nen khong deu duoc chuyen sang adaptive threshold, dung voi ky vong vi nen sinus lam threshold toan cuc kem on dinh hon.
- Anh tuong phan thap co foreground ratio thap hon, nhung CLAHE giup hat van duoc tach ra de dem.
- So vung bi loai cho thay buoc loc hinh dang dang loai nhieu vung khong dat dieu kien area/aspect ratio/solidity.

## 5. Nhan xet

### Nhieu

Nhieu muoi tieu tao nhieu diem trang/den nho. Pipeline dung median blur truoc threshold va remove small objects sau threshold nen ket qua cua anh nhieu muoi tieu van giu cung so dem 111 nhu anh binh thuong.

### Hat dinh nhau

Hat gan nhau co the bi gop thanh mot component. Buoc distance transform va watershed tao marker tai cac tam hat de tach cac vung cham nhau. Tuy nhien neu marker qua day thi mot hat co the bi tach qua muc; neu marker qua thua thi cac hat dinh nhau van bi dem thieu.

### Anh sang khong deu

Anh nen sinus la truong hop kho nhat vi nen co vung sang toi manh. Pipeline dung background correction va adaptive threshold fallback. Ket qua dem la 143, cao hon anh binh thuong, nen can kiem tra contour overlay de xac dinh co dem du hay dem nham nen sang.

### Tuong phan thap

Anh tuong phan thap co foreground ratio 0.1513, thap hon cac anh con lai. CLAHE giup tang tuong phan cuc bo, nhung bien hat co the van yeu. Khi kiem tra overlay, can chu y cac hat o vung toi hoac sat bien anh.

### Loi con lai

- Hat bi cat o bien anh co the bi loai neu dien tich hoac aspect ratio khong dat nguong.
- Hat qua gan nhau co the bi watershed tach sai.
- Nen khong deu co the tao foreground gia trong vung qua sang.
- Tham so `min_peak_distance`, `min_grain_area`, `max_grain_area` can duoc tinh chinh neu overlay cho thay dem thieu hoac dem du.
