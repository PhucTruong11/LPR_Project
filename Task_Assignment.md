# 👥 Phân công công việc Dự án LPR (4 Thành viên)

Dự án Nhận diện Biển số xe (LPR) được chia làm 5 trạm (Station) xử lý chính. Dưới đây là phân công chi tiết cho 4 thành viên gắn liền với từng trạm.

## 🧑‍💻 Thành viên 1: Quản lý & Huấn luyện mô hình YOLO
**Phụ trách: 🚉 Trạm 2 (Detection)**

**Nhiệm vụ:**
- Quản lý tiến độ chung của toàn dự án, viết tài liệu báo cáo, file README và chuẩn bị demo/thuyết trình.
- Tìm kiếm, tải, làm sạch dữ liệu và gán nhãn (labeling) dataset biển số xe (khuyên dùng Roboflow).
- Thiết lập môi trường và cấu hình mô hình **YOLOv8** hoặc YOLOv11.
- Huấn luyện (Train) mô hình nhận diện khung chứa biển số xe.
- Đánh giá độ chính xác (mAP) và xuất mô hình sang định dạng `.pt` để sử dụng.

**Output cần đạt:** Một file `best.pt` (model) chất lượng cao và hàm Python nhận đầu vào là một bức ảnh, trả về tọa độ `[x_min, y_min, x_max, y_max]` của biển số.

**📚 Cần học:**
- **Cấu trúc dữ liệu YOLO:** Cách tổ chức thư mục `train`/`test`/`val` và file `data.yaml`.
- **Google Colab:** Cách sử dụng GPU miễn phí để train mô hình nhanh hơn.
- **Ultralytics API:** Các lệnh cơ bản như `model.train()` và `model.predict()`.

**🔗 Nguồn tham khảo & Công cụ:**
- **Dataset:** Roboflow Universe (Tìm từ khóa "Vietnamese License Plate").
- **Tài liệu:** [Ultralytics YOLOv8/v11 Docs](https://docs.ultralytics.com/) - Hướng dẫn train chi tiết.
- **Công cụ:** Roboflow (Gán nhãn & tải dataset), Google Colab (Train model).

---

## 🧑‍💻 Thành viên 2: Gộp Pipeline & Thiết kế Giao diện (UI)
**Phụ trách: 🚉 Trạm 1 (Input) & 🚉 Trạm 5 (Output)**

**Nhiệm vụ:**
- **[Trạm 1]** Xây dựng giao diện web sử dụng **Streamlit** để thu thập dữ liệu đầu vào bằng cách quét hình ảnh hoặc video trực tiếp qua camera của laptop/điện thoại.
- Viết code gộp các module rời rạc của Thành viên 1, 3, 4 lại thành một pipeline hoàn chỉnh (`Image -> YOLO -> OpenCV -> OCR -> Final Result`).
- **[Trạm 5]** Tiếp nhận chuỗi text đầu ra, áp dụng RegEx hoặc logic làm sạch nếu cần (hỗ trợ Thành viên 4) và hiển thị kết quả cuối (ảnh đã vẽ bounding box + text biển số) lên giao diện.

**Output cần đạt:** Giao diện Streamlit chạy trơn tru, xử lý mượt mà luồng dữ liệu 5 trạm từ đầu đến cuối để người dùng tương tác.

**📚 Cần học:**
- **Streamlit cơ bản:** Cách tạo nút bấm (`st.button`), lấy hình ảnh từ camera (`st.camera_input`), và hiển thị ảnh/text lên web.
- **Logic Pipeline:** Cách import hàm từ các file `.py` khác nhau vào file `app.py` chính.

**🔗 Nguồn tham khảo & Công cụ:**
- **Tài liệu Streamlit:** [Streamlit Documentation](https://docs.streamlit.io/) (Rất dễ đọc).
- **UI/UX:** Streamlit Gallery (Xem các mẫu app AI để học cách bố trí giao diện).
- **Tích hợp:** Tìm kiếm YouTube các Tutorial "Streamlit YOLOv8 Object Detection".
- **Hỗ trợ RegEx:** [Regex101](https://regex101.com/) để hỗ trợ làm sạch chuỗi đầu ra.
- **Công cụ:** VS Code, Git/GitHub để quản lý code của cả nhóm.

---

## 🧑‍💻 Thành viên 3: Chuyên viên Xử lý ảnh (OpenCV - Image Processing)
**Phụ trách: 🚉 Trạm 3 (Processing)**

**Nhiệm vụ:**
- Viết script nhận toạ độ (từ kết quả của Thành viên 1) để cắt (Crop) phần ảnh chỉ chứa biển số.
- Chuyển ảnh màu sang ảnh xám (Grayscale).
- Tăng độ tương phản (CLAHE) và áp dụng nhị phân hóa (Thresholding) để tách nền và chữ (làm chữ nổi bật lên).
- (Nâng cao) Xử lý xoay ảnh (Deskewing) nếu biển số bị nghiêng so với mặt phẳng ngang.

**Output cần đạt:** Hàm Python nhận đầu vào là ảnh gốc + toạ độ, trả về ảnh chỉ chứa biển số đã được làm rõ nét (ảnh nhị phân trắng/đen), sẵn sàng để đưa cho máy đọc chữ (OCR).

**📚 Cần học:**
- **OpenCV cơ bản:** Cắt ảnh bằng mảng Numpy (Slicing), chuyển hệ màu BGR sang Gray.
- **Kỹ thuật tiền xử lý (Preprocessing):** Cân bằng độ tương phản (CLAHE), làm mờ (Gaussian Blur) và Nhị phân hóa (Thresholding).

**🔗 Nguồn tham khảo & Công cụ:**
- **Tài liệu OpenCV:** OpenCV-Python Tutorials.
- **Kỹ thuật xử lý ảnh OCR:** PyImageSearch (Tìm kiếm các bài viết về "Image preprocessing for OCR license plate" để xem các kỹ thuật tách chữ).
- **Công cụ:** Thư viện `opencv-python`, `numpy`.

---

## 🧑‍💻 Thành viên 4: Chuyên viên Nhận dạng ký tự (OCR) & Hậu xử lý
**Phụ trách: 🚉 Trạm 4 (OCR) & Hỗ trợ Trạm 5 (Post-processing)**

**Nhiệm vụ:**
- Cài đặt và sử dụng **PaddleOCR** để đọc chữ từ ảnh biển số đã qua xử lý của Thành viên 3.
- Xử lý bài toán đọc sai thứ tự đối với biển số vuông (biển có 2 dòng).
- Viết các đoạn code (hoặc biểu thức chính quy - RegEx) dựa theo luật biển số xe Việt Nam để tự động sửa lỗi sai phổ biến (Ví dụ: OCR hay nhầm số `8` thành chữ `B`, số `0` thành chữ `D` ở phần chứa số).

**Output cần đạt:** Hàm Python nhận đầu vào là ảnh biển số đã qua xử lý, trả về chuỗi văn bản (String) cuối cùng cực kỳ chính xác (VD: `"30G12345"`).

**📚 Cần học:**
- **Thư viện OCR:** Cách khởi tạo và dùng PaddleOCR để đọc chữ từ ảnh.
- **Logic biển số VN:** Phân biệt biển dài (1 dòng) và biển vuông (2 dòng) dựa trên tỷ lệ khung hình (Aspect Ratio).
- **Regular Expression (RegEx):** Cách viết các pattern để lọc ký tự rác và map lỗi (VD: map chữ thành số tùy vị trí).

**🔗 Nguồn tham khảo & Công cụ:**
- **PaddleOCR:** [GitHub PaddlePaddle/PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) (Đọc chữ cực mạnh, ít bị nhầm 0/D).
- **RegEx:** [Regex101](https://regex101.com/) để test các đoạn code RegEx; Các bài viết "Học RegEx trong 10 phút".
- **Công cụ:** `paddleocr`, thư viện `re` (có sẵn trong Python).
