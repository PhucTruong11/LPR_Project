# OpenCV — Xử lý Ảnh & Tối ưu hóa Luồng Video Thời gian thực

## 1. Giới thiệu tổng quan và Cơ sở lý thuyết của Thị giác Máy tính

**OpenCV (Open Source Computer Vision Library)** là thư viện mã nguồn mở tiêu chuẩn công nghiệp dành cho thị giác máy tính và xử lý ảnh. Chứa đựng hơn 2500 thuật toán tối ưu hóa, OpenCV cung cấp nền tảng vững chắc để thực hiện các thao tác xử lý ma trận điểm ảnh (pixel manipulation), biến đổi không gian màu, phát hiện cạnh biên và lọc nhiễu tần số.

Trong bài toán nhận diện biển số xe (LPR), ảnh thu được từ camera giao thông thực tế thường có chất lượng không đồng đều do nhiều yếu tố tác động:
* Ánh sáng không đều (chói nắng ban ngày, thiếu sáng ban đêm).
* Góc chụp nghiêng do camera lắp đặt ở vị trí cao hoặc lệch bên đường.
* Xe di chuyển gây ra hiện tượng nhòe chuyển động (motion blur).
* Nhiễu hạt do cảm biến camera chất lượng thấp.

Do đó, **OpenCV** đóng vai trò cực kỳ quan trọng làm "màng lọc tiền xử lý" (pre-processing pipeline). Việc đưa trực tiếp ảnh thô cắt từ YOLOv8 vào động cơ OCR mà không qua OpenCV tinh chỉnh sẽ làm giảm độ chính xác nhận diện chữ xuống dưới 50%. Nhờ có OpenCV làm sạch ảnh, tỷ lệ này có thể nâng cao vượt mốc 95%.

---

## 2. Đường ống tiền xử lý ảnh biển số xe chi tiết (Image Processing Pipeline)

Khi YOLOv8 xác định được tọa độ hộp giới hạn (Bounding Box) của biển số xe, OpenCV thực hiện cắt (crop) vùng ảnh đó (được gọi là ROI - Region of Interest) và đưa qua một chuỗi biến đổi hình học và màu sắc phức tạp:

```
 ┌───────────────┐      ┌───────────────┐      ┌───────────────┐      ┌───────────────┐
 │   Ảnh Crop    ├─────►│  Ảnh Xám      ├─────►│     CLAHE     ├─────►│  Nhị Phân Hóa │
 │ (Từ YOLOv8)   │      │  (Grayscale)  │      │ (Tăng t.phản) │      │ (Thresholding)│
 └───────────────┘      └───────────────┘      └───────────────┘      └───────┬───────┘
                                                                              │
                                                                              ▼
 ┌───────────────┐      ┌───────────────┐      ┌───────────────┐      ┌───────────────┐
 │   Đưa vào     │◄─────│ Phép toán hình│◄─────│ Xoay thẳng    │◄─────│ Tìm góc nghiêng│
 │  PaddleOCR    │      │ học (Morph)   │      │  (Deskew)     │      │ (Contours/Rad)│
 └───────────────┘      └───────────────┘      └───────────────┘      └───────────────┘
```

### 2.1. Chuyển đổi ảnh xám (Grayscale Conversion)
Ảnh màu từ camera thường có định dạng BGR (Blue-Green-Red) với 3 kênh màu riêng biệt. Để giảm dung lượng tính toán đi 3 lần và loại bỏ thông tin màu sắc không cần thiết cho việc nhận diện ký tự, ảnh được chuyển về ảnh xám (1 kênh màu, giá trị pixel chạy từ 0 đến 255) sử dụng công thức Luminance tiêu chuẩn:
$$Y = 0.299 \cdot R + 0.587 \cdot G + 0.114 \cdot B$$
Công thức này phản ánh chính xác độ nhạy cảm ánh sáng của mắt người đối với các dải màu khác nhau.

### 2.2. Cân bằng lược đồ xám thích ứng giới hạn độ tương phản (CLAHE)
Các kỹ thuật cân bằng lược đồ xám thông thường (Global Histogram Equalization) thường làm sáng đều toàn bộ bức ảnh, dẫn đến việc chói sáng ở các vùng vốn đã sáng và làm mất chi tiết chữ. Hệ thống áp dụng **CLAHE (Contrast Limited Adaptive Histogram Equalization)**:
* **Cơ chế hoạt động:** Chia nhỏ ảnh biển số thành các ô lưới con (ví dụ: $8 \times 8$ pixel). Thực hiện cân bằng lược đồ xám riêng biệt cho từng ô con này.
* **Giới hạn độ tương phản (Contrast Limiting):** Nếu một ô lưới có đỉnh lược đồ xám quá cao (gây nhiễu), CLAHE sẽ cắt phần đỉnh đó và phân phối đều sang các giá trị khác trước khi thực hiện cân bằng.
* **Nội suy tuyến tính:** Sử dụng phép nội suy song tuyến tính để ghép các ô con lại với nhau, loại bỏ hoàn toàn các đường ranh giới nhân tạo giữa các ô lưới.
* **Kết quả:** Các ký tự chữ đen trên nền biển trắng (hoặc ngược lại) được tăng cường độ tương phản vượt trội ngay cả dưới điều kiện ngược sáng hoặc bị đèn pha xe chiếu trực tiếp.

### 2.3. Nhị phân hóa ảnh (Image Thresholding)
Mục tiêu của bước này là biến đổi bức ảnh xám thành ảnh đen trắng tuyệt đối (giá trị pixel chỉ có thể là 0 - Đen hoặc 255 - Trắng). Dự án sử dụng phương pháp **Nhị phân hóa thích ứng (Adaptive Thresholding)** kết hợp thuật toán **Otsu**:
* Thay vì sử dụng một ngưỡng cố định (ví dụ: $T = 127$), ngưỡng nhị phân được tính toán động cho từng điểm ảnh dựa trên giá trị trung bình có trọng số của các điểm lân cận trong một cửa sổ kích thước $S \times S$.
* Thuật toán **Otsu** tự động phân tích lược đồ xám của ảnh biển số, tìm kiếm ngưỡng tối ưu $T$ để giảm thiểu phương sai trong nhóm (intra-class variance) giữa hai nhóm pixel nền và nhóm pixel ký tự.
* **Kết quả:** Tách biệt hoàn hảo hình dáng chữ ra khỏi nền biển số xe, loại bỏ bóng mờ và vết bẩn trên bề mặt biển.

### 2.4. Thuật toán xoay thẳng biển số bị nghiêng (Deskewing / Affine Transformation)
Trong thực tế, do camera lắp lệch góc, biển số xe chụp được thường bị nghiêng một góc $\theta$. Việc nghiêng góc làm cho các ký tự bị biến dạng hình học, khiến OCR dễ đọc sai chữ. Hệ thống sửa lỗi này bằng thuật toán Deskewing:
1. **Phát hiện đường biên và góc nghiêng:** Sử dụng thuật toán tìm Contour (đường viền liên tục) trên ảnh nhị phân để định vị khung ngoài của biển số hoặc phân bố các ký tự bên trong.
2. **Tính toán góc xoay $\theta$:** Sử dụng hàm `cv2.minAreaRect` để tìm hình chữ nhật có diện tích nhỏ nhất bao quanh biển số, từ đó trích xuất góc nghiêng $\theta$ của cạnh dài so với phương ngang.
3. **Biến đổi Affine:** Xây dựng ma trận xoay 2D sử dụng hàm `cv2.getRotationMatrix2D` quanh tâm của biển số:
   $$M = \begin{bmatrix} \alpha & \beta & (1-\alpha) \cdot x_c - \beta \cdot y_c \\ -\beta & \alpha & \beta \cdot x_c + (1-\alpha) \cdot y_c \end{bmatrix}$$
   Trong đó $\alpha = \cos(\theta)$, $\beta = \sin(\theta)$, và $(x_c, y_c)$ là tọa độ tâm xoay.
4. Áp dụng hàm `cv2.warpAffine` để xoay thẳng bức ảnh về góc nghiêng bằng 0 độ.

---

## 3. Quản lý Luồng Video và Bộ đệm Camera (Camera Streaming Optimization)

Một vấn đề phổ biến khi lập trình camera với OpenCV là hàm `cv2.VideoCapture.read()` chạy đồng bộ (synchronous). Khi xử lý AI bị trễ, OpenCV sẽ tự động lưu các frame chưa đọc vào hàng đợi đệm (buffer) của hệ điều hành. Khi luồng chính đọc lại, nó sẽ nhận được frame cũ trong hàng đợi chứ không phải khung hình thực tế bên ngoài, tạo ra hiện tượng giật hình và trễ hình kéo dài (latency accumulation).

Dự án giải quyết triệt để lỗi này bằng việc thiết kế lớp `CameraStream` chạy đa luồng (**Multithreading**):
* **Cấu hình kích thước bộ đệm nhỏ tối thiểu:** Đặt thuộc tính `cv2.CAP_PROP_BUFFERSIZE` bằng 1 để hệ điều hành không tích lũy nhiều frame cũ.
* **Cơ chế đọc bất đồng bộ (Asynchronous Grabbing):** Khởi chạy một luồng con daemon chuyên trách chỉ làm nhiệm vụ liên tục giải phóng bộ đệm và lưu khung hình mới nhất vào biến `self.frame`:
  ```python
  def update(self):
      while not self.stopped:
          grabbed, frame = self.stream.read()
          with self._lock:
              self.grabbed = grabbed
              self.frame = frame
  ```
* **Sử dụng Khóa (Locking Mechanism):** Sử dụng `threading.Lock` khi đọc và ghi biến `self.frame` để tránh hiện tượng tranh chấp bộ nhớ (Race Condition) khi luồng chính và luồng camera truy cập biến cùng một thời điểm, loại bỏ hoàn toàn lỗi vỡ hình (frame tearing).
