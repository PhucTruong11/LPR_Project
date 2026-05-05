# 👥 Phân công công việc Dự án LPR (4 Thành viên)

Dự án Nhận diện Biển số xe (LPR) được chia làm 5 trạm (Station) xử lý chính. Dưới đây là phân công chi tiết cho 4 thành viên (bao gồm Bạn - Nhóm trưởng) gắn liền với từng trạm.

## 🧑‍💻 Thành viên 1: Quản lý & Huấn luyện mô hình YOLO
**Phụ trách: 🚉 Trạm 2 (Detection)**
**Nhiệm vụ:**
- Quản lý tiến độ chung của toàn dự án, viết tài liệu báo cáo, file README và chuẩn bị demo/thuyết trình.
- Tìm kiếm, tải, làm sạch dữ liệu và gán nhãn (labeling) dataset biển số xe (khuyên dùng Roboflow).
- Thiết lập môi trường và cấu hình mô hình **YOLOv8** hoặc YOLOv11.
- Huấn luyện (Train) mô hình nhận diện khung chứa biển số xe.
- Đánh giá độ chính xác (mAP) và xuất mô hình sang định dạng `.pt` để sử dụng.
**Output cần đạt:** Một file `best.pt` (model) chất lượng cao và hàm Python nhận đầu vào là một bức ảnh, trả về tọa độ `[x_min, y_min, x_max, y_max]` của biển số.

## 🧑‍💻 Thành viên 2: Gộp Pipeline & Thiết kế Giao diện (UI)
**Phụ trách: 🚉 Trạm 1 (Input) & 🚉 Trạm 5 (Output)**
**Nhiệm vụ:**
- **[Trạm 1]** Xây dựng giao diện web sử dụng **Streamlit** để người dùng có thể upload ảnh/video đầu vào một cách dễ dàng.
- Viết code gộp các module rời rạc của Thành viên 1, 3, 4 lại thành một pipeline hoàn chỉnh (`Image -> YOLO -> OpenCV -> OCR -> Final Result`).
- **[Trạm 5]** Tiếp nhận chuỗi text đầu ra, áp dụng RegEx hoặc logic làm sạch nếu cần (hỗ trợ Thành viên 4) và hiển thị kết quả cuối (ảnh đã vẽ bounding box + text biển số) lên giao diện.
**Output cần đạt:** Giao diện Streamlit chạy trơn tru, xử lý mượt mà luồng dữ liệu 5 trạm từ đầu đến cuối để người dùng tương tác.

## 🧑‍💻 Thành viên 3: Chuyên viên Xử lý ảnh (OpenCV - Image Processing)
**Phụ trách: 🚉 Trạm 3 (Processing)**
**Nhiệm vụ:**
- Viết script nhận toạ độ (từ kết quả của Thành viên 1) để cắt (Crop) phần ảnh chỉ chứa biển số.
- Chuyển ảnh màu sang ảnh xám (Grayscale).
- Tăng độ tương phản (CLAHE) và áp dụng nhị phân hóa (Thresholding) để tách nền và chữ (làm chữ nổi bật lên).
- (Nâng cao) Xử lý xoay ảnh (Deskewing) nếu biển số bị nghiêng so với mặt phẳng ngang.
**Output cần đạt:** Hàm Python nhận đầu vào là ảnh gốc + toạ độ, trả về ảnh chỉ chứa biển số đã được làm rõ nét (ảnh nhị phân trắng/đen), sẵn sàng để đưa cho máy đọc chữ (OCR).

## 🧑‍💻 Thành viên 4: Chuyên viên Nhận dạng ký tự (OCR) & Hậu xử lý
**Phụ trách: 🚉 Trạm 4 (OCR) & Hỗ trợ Trạm 5 (Post-processing)**
**Nhiệm vụ:**
- Cài đặt và sử dụng **EasyOCR** hoặc **PaddleOCR** để đọc chữ từ ảnh biển số đã qua xử lý của Thành viên 3.
- Xử lý bài toán đọc sai thứ tự đối với biển số vuông (biển có 2 dòng).
- Viết các đoạn code (hoặc biểu thức chính quy - RegEx) dựa theo luật biển số xe Việt Nam để tự động sửa lỗi sai phổ biến (Ví dụ: OCR hay nhầm số `8` thành chữ `B`, số `0` thành chữ `D` ở phần chứa số).
**Output cần đạt:** Hàm Python nhận đầu vào là ảnh biển số đã qua xử lý, trả về chuỗi văn bản (String) cuối cùng cực kỳ chính xác (VD: `"30G12345"`).
