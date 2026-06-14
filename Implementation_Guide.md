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

Hệ thống hỗ trợ 2 chế độ chạy khác nhau tùy thuộc vào nhu cầu kiểm thử:

### Chế độ 1: Chạy cơ bản (Chỉ chạy Web Streamlit)
Dành cho kiểm thử nhanh bằng ảnh tải lên hoặc dùng webcam của trình duyệt:
```bash
streamlit run app_trial.py
```
Trình duyệt sẽ tự động mở tại địa chỉ `http://localhost:8501`.

### Chế độ 2: Chạy kết hợp Semi-manual (Khuyên dùng - Chạy song song 2 Terminal)
Chế độ này cho phép camera ngoài chạy ngầm xử lý nhận dạng liên tục và đồng bộ kết quả lên giao diện web theo thời gian thực (thông qua SQLite).

Bạn mở **2 terminal riêng biệt** trong VS Code và chạy các lệnh sau:

*   **Terminal 1 (Chạy giao diện Web Streamlit):**
    ```bash
    cd <đường-dẫn-đến-LPR_Project>
    .\lpr_env\Scripts\activate
    streamlit run app_trial.py
    ```
*   **Terminal 2 (Chạy Camera quét OpenCV):**
    ```bash
    cd <đường-dẫn-đến-LPR_Project>
    .\lpr_env\Scripts\activate
    python modules/live_test.py
    ```

**Cách hoạt động (Luồng Semi-manual chi tiết):**
1. `live_test.py` khởi chạy **3 thành phần song song**: Luồng đọc camera (`CameraStream` thread), Vòng lặp YOLO chính (Main loop), và Tiến trình OCR con (`ocr_worker_proc.py` - Process riêng).
2. YOLO chạy mỗi **3 frame** (`YOLO_INTERVAL = 3`) để phát hiện biển số, crop vùng ROI.
3. OpenCV xử lý ảnh (resize, CLAHE tăng tương phản), chuyển grayscale rồi gửi qua `multiprocessing.Queue` sang tiến trình OCR.
4. Tiến trình OCR con chạy **PaddleOCR** trích xuất chữ, sửa lỗi vị trí ký tự, validate RegEx.
5. Kết quả gửi ngược lại Main loop. Cơ chế **Voting** tích lũy — chỉ khi OCR đọc ra **cùng một biển số 3 lần liên tiếp** (`CONFIRM_THRESHOLD = 3`) mới ghi vào DB (`update_detected_plate`).
6. Giao diện web (`app_trial.py`) tự động quét DB mỗi **5 giây** (`AUTO_REFRESH_SEC = 5`) và điền biển số vào Form.
7. Nhân viên kiểm tra → bấm **XÁC NHẬN** (ghi giao dịch) hoặc **BỎ QUA** (xóa hàng đợi).

---

## 🛠️ Kế hoạch cải tiến và Khắc phục lỗi (Design Improvements)

Để tối ưu hóa trải nghiệm và khắc phục các vấn đề phát sinh khi chạy chế độ Semi-manual, dự án áp dụng hai giải pháp thiết kế sau:

### 1. Bổ sung nút "BỎ QUA" (Ignore Button) trên Giao diện Web
*   **Vấn đề:** Khi camera ngoài quét sai biển số (do góc chụp hoặc ánh sáng), biển số sai tự động điền lên web. Nhân viên không có cách nào xóa biển này để giải phóng hàng đợi, dẫn đến bị kẹt luồng quét.
*   **Giải pháp:** Bổ sung thêm nút **"BỎ QUA"** màu cam/xám nằm ngay cạnh nút "XÁC NHẬN" trên giao diện `app_trial.py`. Khi nhấn nút này, hệ thống sẽ:
    *   Xóa biển số đang hiển thị khỏi `st.session_state`.
    *   Gọi hàm `db.clear_detected_plate()` để xóa biển số quét sai khỏi database.
    *   Giải phóng luồng để camera ngoài tiếp tục quét biển số mới.

### 2. Thuật toán Đồng thuận Nhận diện (Frame Consensus Voting) trong Camera Script
*   **Vấn đề:** Khi camera bị mờ, rung hoặc biển số di chuyển, OCR chạy liên tục ở mỗi frame có thể trả về một số kết quả sai lệch ngẫu nhiên và gửi ngay lên web gây phiền toái.
*   **Giải pháp:** File `modules/live_test.py` đã triển khai cơ chế bỏ phiếu đồng thuận (Consensus/Voting):
    *   Thay vì gửi kết quả ngay lập tức khi đọc được biển số hợp lệ lần đầu, hệ thống lưu kết quả vào biến `confirm_candidate` và đếm `confirm_count`.
    *   Chỉ khi OCR nhận diện ra **cùng một chuỗi biển số chính xác trong 3 lần liên tiếp** (`CONFIRM_THRESHOLD = 3`), kết quả đó mới được coi là ổn định và gửi lên database.
    *   Nếu biển số thay đổi giữa chừng (xe khác đi qua), bộ đếm tự động reset.
    *   Kết hợp với `BBOX_JUMP_THRESHOLD = 60px`: nếu tâm bbox dịch chuyển quá 60px, hệ thống coi là biển mới → reset toàn bộ state.

---

## 📁 Cấu trúc dự án hiện tại

- `app_trial.py`: File chạy chính của ứng dụng web Streamlit (bản đầy đủ tính năng).
- `modules/config.py`: Cấu hình tập trung toàn hệ thống (camera, YOLO, OCR, bảng giá, dashboard).
- `modules/live_test.py`: Script chạy camera OpenCV, YOLO detect, và giao tiếp Multiprocessing với OCR.
- `modules/ocr_engine.py`: Xử lý nhận dạng chữ trên biển số sử dụng PaddleOCR + sửa lỗi vị trí + RegEx.
- `modules/ocr_worker_proc.py`: Worker chạy OCR độc lập trên Process riêng để tránh block giao diện camera.
- `modules/detection.py`: Module chạy mô hình YOLO (`best_second.pt`) để xác định vị trí biển số.
- `modules/processing.py`: Module tiền xử lý ảnh cắt (Resize, YUV, CLAHE).
- `modules/database_manager.py`: Quản lý lưu trữ log xe ra vào, tính phí, thống kê doanh thu với SQLite.
- `requirements.txt`: Chứa danh sách các thư viện cần cài đặt.
- `parking.db`: Database cục bộ (tự động tạo ra khi chạy ứng dụng lần đầu).

> **💡 Xử lý lỗi phổ biến:**
> - Nếu gặp lỗi liên quan đến OCR (ví dụ thiếu thư viện khi chạy `app_trial.py`), hãy chạy lại `pip install paddlepaddle paddleocr` để đảm bảo đã cài đúng bản mới nhất.
> - Lỗi thiếu model YOLO (`yolov8n.pt`): Model sẽ tự động được tải xuống khi chạy lần đầu, hãy giữ kết nối mạng.
> - Để thoát màn hình camera OpenCV (`live_test.py`), hãy active cửa sổ camera và nhấn phím **`q`**.
> - Nếu gặp lỗi `database is locked`: Đảm bảo code đã bật `PRAGMA journal_mode=WAL` (đã cấu hình sẵn trong `database_manager.py`).
