# Kiến trúc Song song hóa & Giao tiếp Liên tiến trình (IPC) Hiệu năng cao

## 1. Giới thiệu tổng quan và Cơ sở lý thuyết Concurrency trong Python

### 1.1. Khái niệm GIL (Global Interpreter Lock) và Nút thắt cổ chai của Đa luồng
Trong các ngôn ngữ lập trình biên dịch như C++ hay Java, lập trình viên có thể tạo nhiều luồng (thread) chạy song song trên các nhân CPU khác nhau để tăng tốc độ tính toán. Tuy nhiên, trình thông dịch mặc định của Python (CPython) sử dụng cơ chế khóa **GIL (Global Interpreter Lock)**:
* **GIL là gì?** GIL là một khóa mutex bảo vệ các đối tượng Python, ngăn cản nhiều luồng Python thực thi bytecode cùng một lúc. Điều này có nghĩa là tại một thời điểm vật lý, chỉ có duy nhất một luồng Python được thực thi trên CPU, bất kể máy tính của bạn có bao nhiêu nhân (core) CPU.
* **Tác động đến bài toán AI thời gian thực:**
  * **Tác vụ I/O-bound (Giao tiếp mạng, đọc/ghi file):** Khi một luồng chờ đọc camera hoặc ghi đĩa, nó sẽ tự động giải phóng GIL để luồng khác chạy. Đa luồng (Multithreading) hoạt động tốt ở đây.
  * **Tác vụ CPU-bound (Suy luận mạng neural YOLO, xử lý ma trận OpenCV, suy luận OCR):** Đòi hỏi tính toán toán học liên tục trên CPU. Do có GIL, các luồng tính toán AI này sẽ tranh chấp và chặn lẫn nhau hoàn toàn.
  * Nếu chạy luồng camera (OpenCV) hiển thị giao diện và luồng nhận diện chữ (PaddleOCR) chung một tiến trình Python, luồng camera sẽ bị đơ cứng, tốc độ hiển thị khung hình giảm thảm hại xuống còn 1 - 2 FPS mỗi khi có xe đi qua và kích hoạt OCR.

### 1.2. Giải pháp: Đa tiến trình (Multiprocessing) vượt ranh giới GIL
Để vượt qua giới hạn của GIL, dự án ứng dụng mô hình **Đa tiến trình (Multiprocessing)**:
* Thay vì tạo nhiều luồng chung một vùng nhớ, hệ thống khởi chạy nhiều **tiến trình độc lập** của hệ điều hành.
* Mỗi tiến trình có một trình thông dịch Python riêng, vùng nhớ (Address Space) riêng và sở hữu một khóa GIL độc lập.
* Nhờ vậy, tiến trình phụ trách chạy PaddleOCR và tiến trình chạy camera OpenCV có thể chạy song song vật lý trên các nhân CPU khác nhau, tận dụng tối đa sức mạnh của bộ vi xử lý đa nhân mà không hề gây ảnh hưởng đến hiệu năng của nhau.

---

## 2. Bản đồ kiến trúc hệ thống chi tiết (System Architecture Map)

Hệ thống được thiết kế theo mô hình bất đồng bộ cao, chia nhỏ thành các tác vụ chuyên biệt chạy song song vật lý:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              TIẾN TRÌNH CAMERA & AI CHÍNH (live_test.py)               │
│                                                                                        │
│  ┌─────────────────────────┐               ┌────────────────────────────────────────┐  │
│  │   Luồng Đọc Camera      │  Fresh Frame  │     Luồng Vòng Lặp Chính (Main Loop)   │  │
│  │  (CameraStream Thread)  ├──────────────►│ - Chạy YOLO phát hiện biển số (3 frame)│  │
│  │  - Đọc liên tục camera  │  (Không lag)  │ - Gửi ảnh crop vùng biển số cho OCR    │  │
│  └─────────────────────────┘               └──────┬──────────────────────────▲──────┘  │
└───────────────────────────────────────────────────│──────────────────────────│─────────┘
                                                    │ Grayscale                │ Chuỗi Text
                                                    │ Crop ROI (input_q)       │ Biển Số (result_q)
                                                    ▼                          │
┌──────────────────────────────────────────────────────────────────────────────┴─────────┐
│                             TIẾN TRÌNH CON OCR (ocr_worker_proc.py)                    │
│                                                                                        │
│  - Chạy trên một Process hệ điều hành độc lập (Không bị ảnh hưởng bởi GIL)             │
│  - Chạy mô hình nặng PaddleOCR suy luận ra chữ từ ảnh nhận được                        │
└───────────────────────────────────────────────────┬────────────────────────────────────┘
                                                    │
                                                    │ update_detected_plate(plate)
                                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                CƠ SỞ DỮ LIỆU CHUNG (parking.db)                        │
│                                                                                        │
│  - Lưu trữ tạm thời biển số quét được tại bảng: parking_config (last_detected_plate)   │
│  - Bật chế độ ghi đồng thời an toàn: PRAGMA journal_mode=WAL                           │
└───────────────────────────────────────────────────▲────────────────────────────────────┘
                                                    │
                                                    │ get_detected_plate() / Polling
                                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             TIẾN TRÌNH WEB DASHBOARD (app_trial.py)                    │
│                                                                                        │
│  - Tiến trình Web Server Streamlit hiển thị giao diện giám sát cho nhân viên           │
│  - Tự động làm mới (Auto-refresh) đọc thông tin biển số chờ duyệt từ DB                │
│  - Nhân viên bấm nút duyệt -> Ghi nhận giao dịch lịch sử thực sự                       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Cơ chế Giao tiếp Liên tiến trình (IPC - Inter-Process Communication)

Do các tiến trình có vùng nhớ cô lập hoàn toàn, chúng không thể đọc ghi trực tiếp vào các biến của nhau. Dự án sử dụng hai phương thức IPC chuyên biệt:

### 3.1. Giao tiếp qua Đường ống hàng đợi (multiprocessing.Queue)
Tiến trình Camera chính và tiến trình OCR con truyền nhận dữ liệu thông qua hai hàng đợi bất đồng bộ:
* **`input_q` (Queue đầu vào):** Gửi vùng ảnh biển số xe đã được crop từ tiến trình chính sang tiến trình OCR.
* **`result_q` (Queue kết quả):** Nhận chuỗi chữ biển số xe sau khi OCR nhận diện xong gửi ngược lại tiến trình chính.
* **Cơ chế hoạt động:** `multiprocessing.Queue` được xây dựng dựa trên cơ chế kết hợp giữa **Pipes (Đường ống dẫn tuần tự)** và các khóa đồng bộ **Locks**. Khi một tiến trình đẩy dữ liệu vào Queue, dữ liệu sẽ được **tuần tự hóa (Serialization)** bằng thư viện `pickle` thành chuỗi byte, đẩy qua đường ống dẫn và được **giải tuần tự hóa (Deserialization)** tại tiến trình nhận.

### 3.2. Kỹ thuật nén payload truyền tải tối ưu tốc độ IPC
* **Vấn đề:** Ảnh màu BGR thông thường có kích thước lớn. Quá trình tuần tự hóa và giải tuần tự hóa ma trận 3 kênh qua IPC tốn rất nhiều chu kỳ CPU, gây nghẽn đường ống truyền tin.
* **Giải pháp:** Trước khi đẩy ảnh crop biển số vào `input_q`, tiến trình chính thực hiện chuyển đổi ảnh màu sang định dạng ảnh xám (**Grayscale** - 1 kênh duy nhất):
  ```python
  gray_processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
  input_q.put_nowait(gray_processed)
  ```
* **Hiệu quả:** Giảm kích thước ma trận truyền tải đi đúng 3 lần (loại bỏ hoàn toàn 2 kênh màu dư thừa), đẩy tốc độ tuần tự hóa qua IPC lên cực nhanh và tiết kiệm dung lượng RAM hệ thống.

### 3.3. Cơ chế chống tràn hàng đợi (Queue Throttling & Cooldown)
Để tránh trường hợp tiến trình chính liên tục gửi hàng chục frame ảnh trùng lặp của cùng một chiếc xe đang đỗ trước camera vào hàng đợi trong khi tiến trình OCR đang bận suy luận (gây tràn bộ nhớ và trễ kết quả nhận diện):
* **Ngưỡng Cooldown (`OCR_COOLDOWN` = 0.5s):** Chỉ cho phép gửi ảnh sang OCR tối đa 2 lần trong 1 giây.
* **Kiểm tra trạng thái hàng đợi:** Chỉ gửi ảnh mới nếu hàng đợi đầu vào đang trống (`input_q.empty()`):
  ```python
  if (now - last_ocr_time) >= OCR_COOLDOWN and input_q.empty():
      # Tiến hành gửi ảnh sang OCR
  ```
* **Xóa kết quả cũ dư thừa:** Trong tiến trình OCR, trước khi trả kết quả mới về tiến trình chính, nó sẽ chủ động giải phóng các kết quả cũ còn tồn đọng trong `result_q` để đảm bảo luồng camera luôn nhận được biển số xe tươi mới nhất:
  ```python
  while not result_q.empty():
      result_q.get_nowait()  # Giải phóng hàng đợi kết quả
  result_q.put(text)  # Gửi kết quả mới nhất
  ```

---

## 4. Hành trình Giao dịch của một chiếc xe (End-to-End Lifecycle)

Dưới đây là từng bước vận hành cụ thể từ lúc xe tiến vào bãi đỗ cho đến khi thông tin giao dịch được ghi nhận chính thức:

### Bước 1: Thu nhận hình ảnh và Phát hiện biển số (Tiến trình Camera)
1. Lớp `CameraStream` chạy luồng con đọc camera liên tục, cập nhật khung hình mới nhất.
2. Vòng lặp chính (`live_test.py`) lấy khung hình và định kỳ mỗi 3 khung hình (`YOLO_INTERVAL = 3`) gửi sang mô hình **YOLOv8** để xác định vị trí biển số xe.

### Bước 2: Tiền xử lý và Nhận diện chữ (Tiến trình OCR con)
3. Khi tìm thấy biển số, OpenCV thực hiện cắt ảnh biển số (ROI), xử lý ảnh xám, CLAHE, nhị phân hóa và xoay thẳng góc nghiêng.
4. Ảnh nhị phân xám được nén gửi qua `input_q` sang tiến trình **OCR con**.
5. Tiến trình OCR con chạy mô hình **PaddleOCR** để trích xuất văn bản thô, áp dụng bảng ánh xạ sửa lỗi vị trí chữ/số và validate cấu trúc bằng bộ lọc **RegEx Việt Nam**.
6. Kết quả biển số sạch sẽ được gửi ngược về tiến trình chính qua `result_q`.

### Bước 3: Gửi tín hiệu chờ duyệt lên Cơ sở dữ liệu tạm
7. Tiến trình chính nhận kết quả biển số từ `result_q` và vẽ viền xanh cùng văn bản biển số lên màn hình camera trực quan.
8. Tiến trình chính kiểm tra xem biển số này đã được gửi lên DB trước đó chưa (tránh gửi lặp liên tục). Nếu là biển số hợp lệ và mới, gọi hàm `db.update_detected_plate(plate)` ghi vào bảng `parking_config` khóa `last_detected_plate`.

### Bước 4: Tự động điền Form và Xác nhận giao dịch (Tiến trình Web Streamlit)
9. Giao diện Web Streamlit định kỳ quét cơ sở dữ liệu sau mỗi 5 giây (`AUTO_REFRESH_SEC = 5`).
10. Streamlit phát hiện khóa `last_detected_plate` có giá trị mới $\rightarrow$ tự động điền giá trị này vào Form hiển thị trước mắt nhân viên kiểm đỗ.
11. Nhân viên đối chiếu biển số điền sẵn trên form với hình ảnh thực tế của xe:
    * **Nếu khớp:** Nhân viên chọn hành động và bấm nút **Xác nhận (Check-in / Check-out)**. Streamlit thực thi logic SQL chính thức để lưu trữ giao dịch dài hạn vào bảng `parking_logs`, tính phí lũy tiến dựa trên thời gian thực tế nếu là xe đi ra. Gọi lệnh xóa biển quét tạm trong DB.
    * **Nếu không khớp:** Nhân viên chỉnh sửa lại biển số bị sai bằng bàn phím rồi mới bấm Xác nhận, hoặc bấm nút **Bỏ qua (Ignore)** để xóa hàng đợi tạm thời và tiếp tục chờ xe tiếp theo.
12. Giao diện Web hiển thị bảng thông báo kết quả (thành công, số tiền thu, số chỗ còn lại trong bãi) và cập nhật tức thì lên các biểu đồ báo cáo doanh thu tổng quan.
