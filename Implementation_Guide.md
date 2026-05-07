# 🛠️ Hướng dẫn chi tiết các bước triển khai Dự án LPR

Tài liệu này cung cấp hướng dẫn cài đặt và các đoạn code/cấu trúc cơ bản cho từng thành viên để dễ dàng bắt đầu lập trình.

## ⚙️ Bước 0: Thiết lập Môi trường & Công cụ cơ bản (Dành cho tất cả thành viên)

Trước khi bắt tay vào code, cả nhóm cần thống nhất các công cụ và thiết lập môi trường làm việc chung:

### 1. Công cụ làm việc (Tools)
- **Quản lý mã nguồn:** Sử dụng **Git** và tạo một Repository chung trên **GitHub** hoặc **GitLab** để chia sẻ và quản lý code.
- **IDE / Trình soạn thảo:** Khuyên dùng **VS Code** hoặc **PyCharm**. Nếu dùng VS Code, nên cài thêm các extension như *Python*, *Pylance*, và *GitLens*.
- **Công cụ làm việc với dữ liệu:** Sử dụng **Roboflow** (nền tảng web tiện lợi) hoặc **LabelImg** (tool chạy local) để dán nhãn dữ liệu cho YOLO.

### 2. Thiết lập Môi trường Ảo (Virtual Environment)
Để tránh xung đột thư viện và đảm bảo tương thích hoàn toàn với các thư viện AI (như `easyocr`, `opencv`), nhóm sẽ thống nhất sử dụng **Python 3.11**. Nếu bạn đang dùng bản mới hơn (như 3.13) có thể gặp lỗi khi cài đặt, vui lòng [tải và cài đặt Python 3.11.9 tại đây](https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe) (nhớ tick "Add python.exe to PATH" khi cài).

**Cách tạo và kích hoạt môi trường ảo (bằng `venv`):**
```bash
# Xóa môi trường cũ nếu có (bỏ qua nếu mới làm lần đầu):
# Để thoát môi trường cũ: deactivate
# Trên Windows PowerShell: Remove-Item -Recurse -Force lpr_env
# Hoặc xóa thủ công thư mục lpr_env bằng File Explorer

# 1. Tạo môi trường ảo mới bằng Python 3.11 có tên 'lpr_env'
py -3.11 -m venv lpr_env

# 2. Kích hoạt môi trường (trên Windows):
.\lpr_env\Scripts\activate

# Kích hoạt môi trường (trên MacOS/Linux):
source lpr_env/bin/activate
```
*(Lưu ý: Bạn sẽ thấy chữ `lpr_env` xuất hiện ở đầu dòng lệnh terminal khi kích hoạt thành công)*

### 3. Cài đặt thư viện (Dependencies)
Tạo file `requirements.txt` tại thư mục gốc của dự án với nội dung sau:
```txt
opencv-python
ultralytics
easyocr
streamlit
numpy
torch
```
Đảm bảo bạn **đã kích hoạt môi trường ảo**, sau đó chạy lệnh cài đặt:
```bash
pip install -r requirements.txt
```

> **Lưu ý quan trọng khi cài đặt:**
> Nếu bị lỗi `[WinError 32] The process cannot access the file because it is being used by another process` (thường do Windows Defender quét file), bạn chỉ cần **chạy lại lệnh `pip install -r requirements.txt` một lần nữa** là sẽ thành công.

---

## 🟢 Bước 1: Huấn luyện mô hình YOLO (Dành cho Thành viên 2)
1. Đăng ký tài khoản [Roboflow](https://roboflow.com/), tìm kiếm dataset với từ khoá "Vietnamese License Plate".
2. Tải dataset về định dạng phù hợp cho **YOLOv8**.
3. Tạo file `train_yolo.py`:
```python
from ultralytics import YOLO

# Khởi tạo mô hình YOLOv8 (dùng phiên bản 'nano' - n cho nhẹ và nhanh)
model = YOLO('yolov8n.pt')

# Train model với dataset đã tải
results = model.train(data='path/to/dataset/data.yaml', epochs=50, imgsz=640)
```
4. Sau khi quá trình train hoàn tất, model tốt nhất sẽ nằm ở thư mục `runs/detect/train/weights/best.pt`. File này sẽ được gửi cho Thành viên 1.

---

## 🟡 Bước 2: Xử lý ảnh bằng OpenCV (Dành cho Thành viên 3)
Tạo file `image_processing.py`:
```python
import cv2
import numpy as np

def process_license_plate(image, bbox):
    """
    Hàm cắt và xử lý ảnh biển số xe.
    :param image: Ảnh gốc (đã đọc bằng cv2)
    :param bbox: Toạ độ bounding box [x_min, y_min, x_max, y_max]
    :return: Ảnh biển số đã xử lý nhị phân hoá
    """
    x_min, y_min, x_max, y_max = [int(v) for v in bbox]
    
    # 1. Cắt ảnh (Crop) để lấy đúng phần biển số
    plate_img = image[y_min:y_max, x_min:x_max]
    
    # 2. Chuyển sang ảnh xám (Grayscale)
    gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
    
    # 3. Tăng độ tương phản bằng CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray_clahe = clahe.apply(gray)
    
    # 4. Giảm nhiễu và Nhị phân hóa (Thresholding)
    blur = cv2.GaussianBlur(gray_clahe, (5,5), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return thresh
```

---

## 🟠 Bước 3: Đọc chữ OCR & Hậu xử lý (Dành cho Thành viên 4)
Tạo file `ocr_processing.py`:
```python
import easyocr
import re

# Khởi tạo reader, hỗ trợ tiếng Anh (dành cho biển số dùng ký tự Latin)
reader = easyocr.Reader(['en'], gpu=True) # Set gpu=False nếu không có card rời

def read_and_format_plate(processed_img):
    """
    Hàm đọc ký tự từ ảnh và xử lý chuỗi trả về.
    :param processed_img: Ảnh nhị phân từ Thành viên 3
    :return: Chuỗi text biển số hoàn chỉnh
    """
    # Đọc text từ ảnh
    results = reader.readtext(processed_img)
    
    raw_text = ""
    for (bbox, text, prob) in results:
        raw_text += text
        
    # Làm sạch chuỗi (xoá khoảng trắng, ký tự đặc biệt)
    clean_text = re.sub(r'[^A-Z0-9]', '', raw_text.upper())
    
    # (Nâng cao) Viết thêm RegEx tại đây để map đổi số/chữ bị sai lệch do OCR
    # Ví dụ: Biển số dạng 30G-123.45 thì chữ số thứ 3 chắc chắn là chữ cái.
    # clean_text = ... (Code tự custom)
    
    return clean_text
```

---

## 🔵 Bước 4: Tích hợp Pipeline & Giao diện Streamlit (Dành cho Bạn / Tui)
Tạo file `app.py`:
```python
import streamlit as st
import cv2
import numpy as np
from ultralytics import YOLO

# Import hàm từ các module của TV3 và TV4 (sau khi đã có code từ họ)
# from image_processing import process_license_plate
# from ocr_processing import read_and_format_plate

st.set_page_config(page_title="Nhận diện Biển số xe", page_icon="🚗")
st.title("🚗 Hệ thống nhận diện biển số xe (LPR)")

# Load mô hình do TV2 train
try:
    model = YOLO('best.pt')
except:
    st.warning("Chưa có file mô hình 'best.pt'.")

uploaded_file = st.file_uploader("Tải lên ảnh chứa xe/biển số", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    # Chuyển đổi file upload sang numpy array cho OpenCV
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, 1)
    
    # Chia cột hiển thị
    col1, col2 = st.columns(2)
    with col1:
        st.image(image, channels="BGR", caption="Ảnh gốc")
    
    if st.button("Nhận diện", type="primary"):
        # --- BƯỚC 1: YOLO DETECT ---
        results = model(image)
        boxes = results[0].boxes.xyxy.cpu().numpy()
        
        if len(boxes) > 0:
            bbox = boxes[0] # Lấy biển số đầu tiên tìm thấy
            
            # --- BƯỚC 2: OPENCV ---
            # processed_img = process_license_plate(image, bbox)
            
            # --- BƯỚC 3: OCR ---
            # text_result = read_and_format_plate(processed_img)
            
            # Mock Data (thay bằng text_result khi có code thật)
            text_result = "TEST-30G12345" 
            
            st.success(f"**Biển số:** {text_result}")
            
            # Vẽ Bounding Box lên ảnh hiển thị
            cv2.rectangle(image, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), (0, 255, 0), 3)
            with col2:
                st.image(image, channels="BGR", caption="Ảnh Kết quả")
        else:
            st.error("Không tìm thấy biển số nào trong ảnh!")
```
Để chạy thử giao diện, bạn gõ lệnh trên terminal:
```bash
streamlit run app.py
```

---

## 📁 Bước 5: Cấu trúc Thư mục Chuẩn của Dự án

Toàn bộ dự án cần được tổ chức theo cấu trúc sau để các thành viên dễ tích hợp:

```
LPR_Project/
├── models/
│   └── best.pt               # Sản phẩm của Thành viên 2 (YOLO model đã train)
├── modules/
│   ├── detection.py          # Logic nhận diện biển số (gọi YOLO, trả về bbox)
│   ├── processing.py         # Sản phẩm của Thành viên 3 (OpenCV pipeline)
│   └── ocr_engine.py         # Sản phẩm của Thành viên 4 (EasyOCR + RegEx)
├── app.py                    # File chính — Sản phẩm của Nhóm trưởng (UI & Pipeline)
├── requirements.txt          # Danh sách thư viện cần cài đặt
└── Implementation_Guide.md   # File hướng dẫn này
```

> **Lưu ý:** `app.py` chỉ import và gọi hàm từ các module — không chứa logic xử lý ảnh hay OCR trực tiếp bên trong.

---

## 🚉 Bước 6: Hiểu rõ Workflow — 5 Trạm xử lý

```
[Trạm 1] Người dùng upload ảnh/video (Streamlit UI)
     ↓
[Trạm 2] YOLOv8n quét ảnh → trả về tọa độ bbox biển số
     ↓
[Trạm 3] OpenCV: Crop → Grayscale → CLAHE → Blur → Binarize (Nhị phân hóa)
     ↓
[Trạm 4] EasyOCR đọc ảnh nhị phân → chuỗi ký tự thô (raw text)
     ↓
[Trạm 5] RegEx làm sạch & định dạng → Hiển thị kết quả lên UI
```

**Ví dụ luồng dữ liệu thực tế:**
- Đầu vào: Ảnh xe với biển số `30G-123.45`
- Trạm 2 → bbox: `[145, 320, 410, 390]`
- Trạm 3 → ảnh trắng đen biển số đã cắt
- Trạm 4 → raw text: `"30G-123.45#"`
- Trạm 5 → kết quả cuối: `"30G12345"` ✅

---

## ⚡ Bước 7: Giải pháp thực tế khi triển khai

### 🔴 Vấn đề 1: Train nhanh để chạy Real-time

1. **Dùng YOLOv8n pre-trained** — không train từ đầu, chỉ fine-tune trên dataset VN.
2. **Roboflow** — tìm "Vietnamese License Plate", tải dataset đã gán nhãn, export định dạng YOLOv8.
3. **Google Colab** — dùng GPU miễn phí để train, xong trong vài tiếng.

```python
# Train nhanh trên Colab
from ultralytics import YOLO
model = YOLO('yolov8n.pt')  # Nano — nhẹ nhất
model.train(data='vietnamese_plates/data.yaml', epochs=50, imgsz=640)
```

### 🟠 Vấn đề 2: Giảm Delay khi xử lý Video

```python
frame_count = 0
SKIP_FRAMES = 5  # OCR chỉ chạy mỗi 5 frame
plate_buffer = []  # Buffer lưu kết quả tạm

while cap.isOpened():
    ret, frame = cap.read()
    frame_count += 1

    # YOLO chạy mỗi frame (nhanh)
    results = yolo_model(frame)

    # OCR chỉ chạy mỗi SKIP_FRAMES (nặng hơn)
    if frame_count % SKIP_FRAMES == 0 and len(results[0].boxes) > 0:
        text = ocr_engine.read(frame, results[0].boxes[0])
        plate_buffer.append(text)

        # Chỉ lưu khi ổn định 3 frame liên tiếp
        if len(plate_buffer) >= 3 and len(set(plate_buffer[-3:])) == 1:
            save_to_csv(plate_buffer[-1])  # Lưu kết quả chắc chắn
```

### 🟢 Vấn đề 3: Plan B nếu Real-time quá chậm

Nếu webcam thật sự lag không thể chịu được, giới hạn chức năng lại:

```python
# Chế độ Upload Video (thay cho live webcam)
uploaded_video = st.file_uploader("Upload Video", type=["mp4", "avi"])
if uploaded_video and st.button("Xử lý Video"):
    # Xử lý từng frame, lưu kết quả vào CSV
    # Hiển thị tóm tắt sau khi xử lý xong
    st.success("Đã xử lý xong! Xem kết quả bên dưới.")
```

### 🔵 RegEx chuẩn hóa biển số Việt Nam

```python
import re

def format_plate(raw_text: str) -> str:
    """Làm sạch và định dạng biển số xe Việt Nam."""
    # Xóa mọi ký tự không phải chữ cái hoặc chữ số
    clean = re.sub(r'[^A-Z0-9]', '', raw_text.upper())

    # Sửa lỗi OCR phổ biến: ký tự thứ 3 phải là chữ cái
    # (OCR hay nhầm B->8, D->0 ở vị trí số; 8->B, 0->D ở vị trí chữ)
    char_map = {'0': 'D', '1': 'I', '5': 'S', '8': 'B', '6': 'G'}
    if len(clean) >= 3 and clean[2].isdigit():
        clean = clean[:2] + char_map.get(clean[2], clean[2]) + clean[3:]

    return clean

# Ví dụ:
# format_plate("30G-123.45#") → "30G12345"
# format_plate("51F80234")    → "51F80234"
```

---

> **💡 Tip cuối:** Thứ tự tích hợp tốt nhất là `TV2 → TV3 → TV4 → TV1`. Nhóm trưởng (TV1) chờ output của từng người rồi mới lắp vào pipeline `app.py`. Hãy dùng **mock data** trước để test giao diện trong khi chờ các thành viên hoàn thiện module.
