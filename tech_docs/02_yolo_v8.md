# Ultralytics YOLOv8 — Phát hiện Đối tượng (License Plate Detection)

## 1. Giới thiệu tổng quan và Cơ sở lý thuyết

### 1.1. Sự phát triển của kiến trúc YOLO
**YOLO (You Only Look Once)** là một cột mốc lịch sử trong lĩnh vực thị giác máy tính, chuyển bài toán phát hiện đối tượng từ mô hình phân loại nhiều giai đoạn phức tạp (như R-CNN, Fast R-CNN cần đề xuất vùng chọn trước) thành bài toán hồi quy (regression) một giai đoạn duy nhất. Mô hình dự đoán trực tiếp tọa độ hộp giới hạn (Bounding Box) và xác suất phân lớp của vật thể từ toàn bộ bức ảnh đầu vào trong một lần lan truyền tiến (single forward pass).

Phiên bản **YOLOv8** được phát triển bởi **Ultralytics** vào năm 2023, mang lại những cải tiến vượt trội về cả tốc độ và độ chính xác nhờ các thay đổi cốt lõi trong mạng xương sống (Backbone) và đầu dự đoán (Head):
* **Thiết kế Anchor-free (Không neo):** Khác với các phiên bản trước (như YOLOv5, YOLOv7) sử dụng các hộp neo kích thước cố định sẵn để tính toán độ lệch (offset), YOLOv8 dự đoán trực tiếp tâm của đối tượng và khoảng cách từ tâm đến 4 cạnh của hộp giới hạn. Cải tiến này giúp giảm đáng kể số lượng tham số cần huấn luyện và tăng độ linh hoạt khi phát hiện các vật thể có tỷ lệ khung hình dị biệt (như biển số dài và biển số vuông).
* **Kiến trúc C2f (CSPLayer với 2 luồng chuyển tiếp):** Thay thế khối C3 cũ bằng khối C2f, kết hợp các luồng thông tin ở độ phân giải cao và thấp, giúp mạng trích xuất đặc trưng sâu sắc hơn mà không làm tăng khối lượng tính toán.
* **Đầu dự đoán phân tách (Decoupled Head):** YOLOv8 sử dụng các nhánh mạng neural riêng biệt để dự đoán lớp đối tượng (Classification) và tọa độ hộp giới hạn (Regression), giúp tăng tốc độ hội tụ khi huấn luyện và cải thiện độ chính xác định vị.

### 1.2. Phân loại cấu hình mô hình YOLOv8
Ultralytics cung cấp nhiều phiên bản YOLOv8 với kích thước mạng khác nhau để cân bằng giữa hiệu năng và độ chính xác:
* **YOLOv8n (Nano):** ~3.2 triệu tham số. Đây là phiên bản được lựa chọn trong dự án này vì nó được tối ưu hóa đặc biệt cho các thiết bị phần cứng hạn chế (CPU máy tính văn phòng, Raspberry Pi). Tốc độ suy luận đạt tới 30-50 FPS trên CPU thông thường mà vẫn đảm bảo độ chính xác phát hiện biển số đạt trên 95%.
* **YOLOv8s (Small), YOLOv8m (Medium), YOLOv8l (Large), YOLOv8x (Extra Large):** Có số lượng tham số lớn hơn, cho độ chính xác cao hơn đối với các vật thể nhỏ/xa nhưng đòi hỏi phần cứng GPU chuyên dụng để chạy thời gian thực.

---

## 2. Vai trò và Quy trình huấn luyện mô hình phát hiện biển số

Trong hệ thống **LPR Smart Parking**, nhiệm vụ của YOLOv8 chỉ tập trung vào giai đoạn **Phát hiện biển số xe (License Plate Detection)**:

```
┌─────────────────┐       ┌──────────────────────┐       ┌──────────────────┐
│   Ảnh Camera    ├──────►│  YOLOv8n Inference  ├──────►│ Tọa độ BBox (ROI)│
│ (Khung hình thô) │       │ (Định vị biển số)    │       │   [x1, y1, x2, y2]│
└─────────────────┘       └──────────────────────┘       └────────┬─────────┘
                                                                  │
                                                                  ▼
                                                         [ Cắt ảnh biển số ]
```

### 2.1. Chuẩn bị dữ liệu và Huấn luyện mô hình (Custom Training)
Mô hình YOLOv8 nguyên bản được huấn luyện trên tập dữ liệu COCO (chứa 80 lớp vật thể thông thường như người, xe hơi, cốc, ghế). Để nhận diện được biển số xe Việt Nam, mô hình phải qua quá trình tinh chỉnh (Fine-tuning) trên tập dữ liệu biển số tùy chỉnh:
* **Tập dữ liệu (Dataset):** Thu thập hàng ngàn hình ảnh phương tiện giao thông (ô tô, xe máy) trong các điều kiện thực tế tại Việt Nam (ánh sáng yếu, chói sáng, trời mưa, góc chụp nghiêng).
* **Gán nhãn (Labeling):** Sử dụng các công cụ chuyên dụng như **Roboflow** hoặc **LabelImg** để vẽ khung giới hạn (bounding box) quanh biển số xe và gán lớp `license-plate`.
* **Hàm mất mát (Loss Functions):** YOLOv8 sử dụng kết hợp hai hàm mất mát cho bài toán hồi quy hộp giới hạn:
  1. **CIoU Loss (Complete Intersection over Union):** Tính toán độ tương quan giữa hộp dự đoán và hộp nhãn thật dựa trên khoảng cách tâm, diện tích giao nhau và tỷ lệ khung hình.
  2. **DFL Loss (Distribution Focal Loss):** Tập trung tối ưu hóa các cạnh của hộp giới hạn khi ranh giới của vật thể bị mờ hoặc bị che khuất.

### 2.2. Cơ chế suy luận thời gian thực trong dự án
* **Resize ảnh đầu vào:** Trước khi đưa khung hình camera vào mô hình YOLO, ảnh được thay đổi kích thước về độ phân giải chuẩn của mô hình (thông qua hằng số `YOLO_INPUT_WIDTH = 640`), giúp đồng bộ hóa dữ liệu đầu vào và tăng tốc độ xử lý của mạng neural.
* **Ngưỡng tin cậy (Confidence Threshold):** Chỉ các hộp giới hạn có xác suất dự đoán lớn hơn ngưỡng cấu hình (thường là 0.5) mới được chấp nhận để loại bỏ hoàn toàn các trường hợp nhận diện nhầm các vật thể có vân sọc giống biển số (như lưới tản nhiệt ô tô).

---

## 3. Các thuật toán tối ưu hóa tọa độ và Hậu xử lý

### 3.1. Thuật toán Non-Maximum Suppression (NMS)
Khi mô hình suy luận, một biển số xe có thể bị bao phủ bởi nhiều hộp giới hạn dự đoán chồng chéo nhau. Hệ thống áp dụng thuật toán **NMS (Triệt tiêu phi cực đại)** để giữ lại duy nhất một hộp tối ưu:
1. Lọc bỏ tất cả các hộp có độ tin cậy (Confidence Score) thấp hơn ngưỡng cấu hình.
2. Sắp xếp các hộp còn lại theo thứ tự độ tin cậy từ cao xuống thấp.
3. Chọn hộp có độ tin cậy cao nhất làm hộp chuẩn.
4. Tính toán chỉ số **IoU (Intersection over Union)** giữa hộp chuẩn này với tất cả các hộp còn lại:
   $$\text{IoU} = \frac{\text{Diện tích vùng giao nhau}}{\text{Diện tích vùng hợp nhau}}$$
5. Loại bỏ tất cả các hộp có chỉ số $\text{IoU} > \text{ngưỡng IoU}$ (thường là 0.45) vì chúng được coi là cùng dự đoán một đối tượng.
6. Lặp lại quy trình cho đến khi tất cả các hộp được xử lý.

### 3.2. Thuật toán ổn định hộp giới hạn chống nhấp nháy (BBox Smoothing Algorithm)
Trong quá trình truyền video trực tiếp, các yếu tố môi trường (ánh sáng thay đổi, rung lắc camera) có thể khiến mô hình YOLO bị mất dấu biển số trong 1 hoặc 2 khung hình (frame drop), gây ra hiện tượng viền xanh lá vẽ trên màn hình bị chớp nháy liên tục. Dự án giải quyết vấn đề này bằng một thuật toán giữ trạng thái thông minh:
* **Hằng số `BBOX_MISS_THRESHOLD` (mặc định = 5):** Cho phép hệ thống ghi nhớ vị trí hộp giới hạn của biển số cũ trong tối đa 5 khung hình tiếp theo ngay cả khi YOLO không phát hiện được gì.
* **Cơ chế hoạt động:**
  ```python
  if small_bbox is not None:
      miss_count = 0  # Reset bộ đếm lỗi
      last_bbox = new_bbox  # Cập nhật tọa độ mới nhất
  else:
      miss_count += 1  # Tăng bộ đếm khi không phát hiện thấy biển số
      if miss_count > BBOX_MISS_THRESHOLD:
          last_bbox = None  # Chỉ xóa tọa độ khi mất dấu quá 5 frame liên tục
  ```
* **Hiệu quả:** Giao diện hiển thị camera cực kỳ mượt mà, khung viền biển số ổn định cố định, đồng thời tạo ra khoảng thời gian trễ cần thiết để thuật toán OCR có đủ dữ liệu ảnh chất lượng cao để xử lý mà không bị ngắt quãng.
