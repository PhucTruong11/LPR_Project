# 🛠️ Hướng dẫn Triển khai Kỹ thuật (Smart Parking)

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

## 🔵 Bước 4: Tích hợp Database & Giao diện Dashboard (Smart Parking)
Tạo file `database_manager.py` trong thư mục `modules/` để xử lý SQLite:
```python
import sqlite3
import datetime

def init_db():
    conn = sqlite3.connect('parking.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS parking_logs
                 (ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  plate_number TEXT, time_in DATETIME, 
                  time_out DATETIME, status TEXT, fee REAL)''')
    conn.commit()
    return conn

def process_vehicle(plate_number):
    conn = sqlite3.connect('parking.db')
    c = conn.cursor()
    # Kiểm tra xem xe đang ở trong bãi không
    c.execute("SELECT * FROM parking_logs WHERE plate_number=? AND status='IN'", (plate_number,))
    record = c.fetchone()
    
    now = datetime.datetime.now()
    if record is None:
        # CHECK-IN
        c.execute("INSERT INTO parking_logs (plate_number, time_in, status) VALUES (?, ?, 'IN')", (plate_number, now))
        conn.commit()
        return "CHECK-IN", now.strftime("%H:%M:%S"), 0
    else:
        # CHECK-OUT
        ticket_id = record[0]
        time_in = datetime.datetime.strptime(record[2], "%Y-%m-%d %H:%M:%S.%f")
        hours_parked = (now - time_in).total_seconds() / 3600
        fee = max(5000, int(hours_parked * 10000)) # Logic tính tiền cơ bản
        
        c.execute("UPDATE parking_logs SET time_out=?, status='OUT', fee=? WHERE ticket_id=?", (now, fee, ticket_id))
        conn.commit()
        return "CHECK-OUT", now.strftime("%H:%M:%S"), fee
```

Tạo file `app.py` tích hợp giao diện:
```python
import streamlit as st
import cv2
from modules.database_manager import init_db, process_vehicle

# Khởi tạo DB
init_db()

st.set_page_config(page_title="Smart Parking Dashboard", layout="wide")
st.title("🅿️ Hệ thống Quản lý Bãi xe Thông minh")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📷 Camera Gate")
    uploaded_file = st.file_uploader("Upload ảnh xe qua trạm", type=["jpg", "png"])
    if uploaded_file:
        # TODO: Chạy qua pipeline YOLO -> OpenCV -> OCR để lấy text
        # Mock Data (thay thế bằng kết quả thật)
        detected_plate = "30G12345" 
        st.success(f"🔍 Hệ thống AI nhận diện biển số: **{detected_plate}**")

        with col2:
            st.subheader("💳 Cổng Thanh Toán")
            if st.button("Xác nhận & Mở cổng"):
                action, time_str, fee = process_vehicle(detected_plate)
                if action == "CHECK-IN":
                    st.info(f"✅ Đã Check-in lúc {time_str}")
                else:
                    st.warning(f"📤 Đã Check-out lúc {time_str}")
                    st.error(f"💰 Phí gửi xe: {fee:,.0f} VNĐ")
```
Để chạy thử giao diện, bạn gõ lệnh trên terminal:
```bash
streamlit run app.py
```

---

## 📁 Bước 5: Cấu trúc Thư mục Chuẩn của Dự án

Toàn bộ dự án cần được tổ chức theo cấu trúc sau để các thành viên dễ phân công:

```
LPR_Project/
├── parking.db                # File Database tự động tạo (cần đưa vào .gitignore)
├── models/
│   └── best.pt               # Sản phẩm của TV2 (YOLO model)
├── modules/
│   ├── database_manager.py   # Xử lý kết nối và truy vấn SQLite3
│   ├── detection.py          # Module phát hiện biển số (YOLO)
│   ├── processing.py         # Sản phẩm TV3 (OpenCV pipeline)
│   └── ocr_engine.py         # Sản phẩm TV4 (EasyOCR + RegEx)
├── app.py                    # File chính — UI Streamlit và ghép nối luồng
├── requirements.txt          
└── Implementation_Guide.md   
```

> **Quy tắc:** Mọi tương tác lưu/đọc dữ liệu gửi xe phải thông qua file `modules/database_manager.py`. `app.py` chỉ phụ trách UI và điều phối.

---

## 🚉 Bước 6: Cấu trúc Cơ sở dữ liệu & Logic Xử lý (Smart Parking)

### 1. Cấu trúc Cơ sở dữ liệu (SQLite)
Bảng `parking_logs`:
- `ticket_id` (TEXT): Mã vé tự động.
- `plate_number` (TEXT): Biển số xe.
- `time_in` (DATETIME): Giờ vào.
- `time_out` (DATETIME): Giờ ra.
- `status` (TEXT): 'IN' hoặc 'OUT'.
- `fee` (REAL): Số tiền.

### 2. Quy trình xử lý (Pipeline)
1. **Detection:** YOLO bắt biển số từ Video Stream.
2. **Preprocessing:** OpenCV cắt vùng biển, xử lý nhị phân.
3. **OCR:** Chuyển ảnh vùng biển thành chuỗi String.
4. **Logic Decision:**
   - Nếu biển số KHÔNG tồn tại trong DB với status 'IN' -> Thực hiện **Check-in**.
   - Nếu biển số ĐÃ tồn tại với status 'IN' -> Thực hiện **Check-out** (Tính tiền = Giờ ra - Giờ vào).
5. **UI:** Hiển thị thông báo lên màn hình Streamlit (Thành công/Thất bại/Số tiền).

### 3. Lưu ý kỹ thuật
- Sử dụng `cv2.VideoCapture(0)` cho webcam hoặc đường dẫn file video.
- Chỉnh `clipLimit` trong CLAHE nếu ảnh biển số quá chói đèn LED.

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

### 🟠 Vấn đề 2: Chống Spam Scan (Chỉ check-in 1 lần)

Khi áp dụng vào Camera bãi xe, một chiếc xe dừng ở cổng có thể bị scan hàng chục lần.

```python
import time

recent_scans = {} # Lưu {biển_số: thời_gian_scan_cuối}
COOLDOWN_TIME = 60 # Chỉ xử lý 1 lần trong 60 giây

def handle_frame(frame):
    plate_text = ai_pipeline.scan(frame)
    if not plate_text: return
    
    current_time = time.time()
    
    # Kiểm tra Cooldown để chống Spam
    if plate_text in recent_scans:
        if current_time - recent_scans[plate_text] < COOLDOWN_TIME:
            return # Bỏ qua, tránh gọi Check-in/Check-out liên tục
            
    recent_scans[plate_text] = current_time
    
    # Tiến hành xử lý DB (Check-in/Check-out)
    database.process_vehicle(plate_text)
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
