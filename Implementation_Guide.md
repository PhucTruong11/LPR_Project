# 🛠️ Hướng dẫn Cài đặt & Triển khai Dự án (Smart Parking)

Tài liệu này hướng dẫn cách thiết lập môi trường và chạy ứng dụng quản lý bãi đỗ xe thông minh.

## ⚙️ Bước 1: Yêu cầu hệ thống
- **Hệ điều hành**: Windows 10/11, macOS, hoặc Linux.
- **Python**: Phiên bản **3.9 đến 3.11** (Khuyến nghị dùng Python 3.11). *Lưu ý: Không nên dùng Python 3.12+ để tránh lỗi tương thích thư viện.*
- **Git**: Dùng để tải mã nguồn.

## ⚙️ Bước 2: Tải mã nguồn và tạo môi trường ảo

Mở Terminal (hoặc Command Prompt / PowerShell) và chạy các lệnh sau:

```bash
# 1. Clone dự án về máy
git clone <đường-dẫn-repo-của-bạn>
cd LPR_Project

# 2. Tạo môi trường ảo (Virtual Environment)
# Trên Windows:
python -m venv lpr_env
.\lpr_env\Scripts\activate

# Trên macOS/Linux:
python3 -m venv lpr_env
source lpr_env/bin/activate
```
*(Lưu ý: Sau khi kích hoạt thành công, bạn sẽ thấy `(lpr_env)` ở đầu dòng lệnh).*

## ⚙️ Bước 3: Cài đặt thư viện (Dependencies)

Sau khi đã kích hoạt môi trường ảo, tiến hành cài đặt các thư viện cần thiết:

```bash
# Nâng cấp pip để tránh các lỗi cài đặt
python -m pip install --upgrade pip

# Cài đặt các thư viện từ requirements.txt
pip install -r requirements.txt
```

> **Lưu ý quan trọng về OCR (PaddleOCR):**
> Hệ thống sử dụng **PaddleOCR** để nhận diện biển số (đã thay thế EasyOCR ở phiên bản cũ). Quá trình cài đặt `paddlepaddle` và `paddleocr` có thể mất một chút thời gian. Nếu gặp lỗi cài đặt, hãy đảm bảo bạn đang dùng Python 3.11 và có kết nối mạng ổn định.

## ⚙️ Bước 4: Chạy ứng dụng

Sau khi cài đặt xong thư viện, bạn có thể khởi động ứng dụng giao diện web:

```bash
streamlit run app.py
```

Một cửa sổ trình duyệt sẽ tự động mở ra tại địa chỉ `http://localhost:8501`. Tại đây, bạn có thể:
1. Tải lên hình ảnh biển số xe (hoặc dùng webcam tùy cấu hình).
2. Hệ thống sẽ tự động nhận diện vị trí biển số (YOLO) và đọc chữ (PaddleOCR).
3. Quản lý trạng thái xe vào/ra (Check-in/Check-out) tự động thông qua SQLite.

---

## 📁 Cấu trúc dự án hiện tại

- `app.py`: File chạy chính của ứng dụng web Streamlit.
- `modules/ocr_engine.py`: Xử lý nhận dạng chữ trên biển số sử dụng PaddleOCR.
- `modules/database_manager.py`: Quản lý lưu trữ log xe ra vào với SQLite.
- `requirements.txt`: Chứa danh sách các thư viện cần cài đặt.
- `parking.db`: Database cục bộ (tự động tạo ra khi chạy ứng dụng lần đầu).

> **💡 Xử lý lỗi phổ biến:**
> - Nếu gặp lỗi liên quan đến OCR (ví dụ thiếu thư viện khi chạy `app.py`), hãy chạy lại `pip install paddlepaddle paddleocr` để đảm bảo đã cài đúng bản mới nhất.
> - Lỗi thiếu model YOLO (`yolov8n.pt`): Model sẽ tự động được tải xuống khi chạy lần đầu, hãy giữ kết nối mạng.
