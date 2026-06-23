# Smart Parking System - Hệ thống Quản lý Bãi xe Thông minh sử dụng AI

[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/Status-In%20Development-yellow)]()

## 📋 Mục lục
- [Giới thiệu](#-giới-thiệu)
- [Tính năng chính](#-tính-năng-chính)
- [Công cụ & Thư viện](#-công-nghệ-sử-dụng)
- [Cấu trúc thư mục](#-cấu-trúc-thư-mục)
- [Hướng dẫn cài đặt](#-cài-đặt)
- [Hướng dẫn sử dụng](#chạy-ứng-dụng)
- [Pipeline xử lý](#-pipeline-xử-lý)
- [Lộ trình phát triển](#️-lộ-trình-phát-triển)
- [Hướng dẫn đóng góp](#-hướng-dẫn-đóng-góp)
- [Xử lý sự cố](#-xử-lý-sự-cố)

---

## 📝 Giới thiệu
Dự án tập trung vào việc tự động hóa quy trình check-in/check-out tại các bãi giữ xe sử dụng công nghệ nhận diện biển số (LPR). Hệ thống tự động ghi nhận thời gian, quản lý danh sách xe trong bãi và tính toán chi phí gửi xe, giúp giảm thiểu sai sót thủ công và tăng tốc độ xử lý.

## 🚀 Tính năng chính
- **Tự động Check-in:** Nhận diện biển số, lưu thời gian vào và cấp mã vé điện tử vào Database.
- **Tự động Check-out:** Quét lại biển số khi xe ra, tự động đối soát thời gian và tính toán tiền phí.
- **Quản lý Dữ liệu:** Lưu trữ lịch sử gửi xe bằng SQLite.
- **Giao diện Giám sát:** Dashboard trực quan bằng Streamlit cho phép xem video real-time và thống kê doanh thu.

## 🛠️ Công nghệ sử dụng

### Framework & Thư viện
| Công nghệ | Mục đích |
|-----------|---------|
| **PyTorch** | Deep Learning framework cho YOLO |
| **Ultralytics YOLO** | Mô hình phát hiện đối tượng (YOLOv8) |
| **OpenCV** | Xử lý ảnh và video |
| **PaddleOCR** | Nhận dạng ký tự (OCR) |
| **Streamlit** | Giao diện web |
| **NumPy** | Xử lý dữ liệu mảng |
| **SQLite3** | Quản lý Cơ sở dữ liệu (Log xe ra vào) |
| **OpenVINO** | Tối ưu hóa suy luận mô hình AI |
| **Plotly** | Trực quan hóa biểu đồ doanh thu |

### Công cụ & Nền tảng
- **Ngôn ngữ**: Python 3.9+ (Khuyến nghị 3.11)
- **IDE**: VS Code, PyCharm
- **Quản lý phiên bản**: Git & GitHub
- **Quản lý dữ liệu**: Roboflow
- **Quản lý môi trường**: venv, Conda

---

## 📁 Cấu trúc thư mục

```
LPR_Project/
├── app_trial.py                    # Ứng dụng Streamlit chính (Giao diện Dashboard)
├── parking.db                      # File Database SQLite3 (tự sinh khi chạy lần đầu)
├── yolov8n.pt                      # Model YOLO pre-trained gốc (auto download)
├── requirements.txt                # Danh sách thư viện Python
├── README.md                       # Tài liệu này
├── LPR_Project_Roadmap.md          # Kế hoạch phát triển chi tiết
├── Implementation_Guide.md         # Hướng dẫn cài đặt chi tiết
├── Git_Workflow.md                 # Quy trình Git của dự án
├── note.txt                        # Ghi chú tạm
│
├── models/                         # Thư mục lưu trữ các mô hình đã huấn luyện
│   ├── best.pt                     # Model YOLO custom đã train (biển số VN)
│   └── best_second.pt              # Model YOLO phiên bản 2 (đang dùng)
│
├── modules/                        # Các module xử lý chính
│   ├── config.py                   # Cấu hình tập trung toàn hệ thống
│   ├── detection.py                # Module phát hiện biển số (YOLO)
│   ├── processing.py               # Module xử lý ảnh (OpenCV - CLAHE, resize)
│   ├── ocr_engine.py               # Module nhận dạng ký tự (PaddleOCR + RegEx)
│   ├── ocr_worker_proc.py          # Worker OCR chạy trên Process riêng (Multiprocessing)
│   ├── database_manager.py         # Logic quản lý DB (Check-in/Out, thống kê, phí)
│   ├── live_test.py                # Script chạy camera ngoài (OpenCV + YOLO live)
│   └── test_img.py                 # Script test nhanh với ảnh tĩnh
│
└── tech_docs/                      # Tài liệu kỹ thuật chi tiết (cho báo cáo/thuyết trình)
    ├── 01_streamlit.md             # Kiến trúc Streamlit Dashboard
    ├── 02_yolo_v8.md               # Lý thuyết & ứng dụng YOLOv8
    ├── 03_opencv.md                # Pipeline xử lý ảnh OpenCV
    ├── 04_paddle_ocr.md            # OCR Engine & hậu xử lý biển số
    ├── 05_sqlite.md                # Thiết kế Database & tối ưu WAL
    └── 06_architecture_multiprocessing.md  # Kiến trúc Multiprocessing & IPC
```

### Mô tả chi tiết các module

| Module | Chức năng |
|--------|-----------|
| **config.py** | Cấu hình tập trung: thông số camera, YOLO, OCR, bảng giá, dashboard |
| **detection.py** | Tích hợp YOLOv8 (model `best_second.pt`) để phát hiện biển số, trả về bounding box |
| **processing.py** | Xử lý ảnh: crop ROI, resize, chuyển YUV, CLAHE tăng tương phản |
| **ocr_engine.py** | Tích hợp PaddleOCR, sắp xếp multi-line, hậu xử lý vị trí ký tự, validate RegEx |
| **ocr_worker_proc.py** | Worker chạy OCR trên Process riêng biệt, giao tiếp qua `multiprocessing.Queue` |
| **database_manager.py** | Check-in/Check-out, tính phí lũy tiến, thống kê doanh thu, chia sẻ biển số Semi-manual |
| **live_test.py** | Vòng lặp camera chính: YOLO detect → crop → gửi OCR → voting → ghi DB |

---

## 📦 Cài đặt

**Yêu cầu**: Python 3.9–3.11, pip, Git

**Cài đặt cơ bản:**
- Clone repository
- Tạo môi trường ảo: `python -m venv lpr_env`
- Kích hoạt môi trường
- Cài đặt dependencies: `pip install -r requirements.txt`

## Chạy ứng dụng

Hệ thống hỗ trợ 2 chế độ vận hành chính:

### 1. Chế độ 1: Chạy cơ bản (Chỉ chạy Web Streamlit)
Thích hợp để kiểm thử nhanh hoặc chạy trên máy chủ tập trung không có camera kết nối trực tiếp.

*   **Lệnh khởi động:**
    ```bash
    streamlit run app_trial.py
    ```
*   **Luồng vận hành:**
    ```
    ┌──────────────────────────────────┐
    │   CHẾ ĐỘ 1: CHỈ CHẠY WEB APP     │
    └────────────┬─────────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────┐
    │  Tải ảnh lên / Bật webcam web    │
    └────────────┬─────────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────┐
    │  Web Streamlit tự chạy xử lý AI: │
    │  YOLO (Detect) -> OCR (Đọc chữ)  │
    └────────────┬─────────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────┐
    │  Nhân viên kiểm tra kết quả      │
    │  và bấm [XÁC NHẬN] trên web      │
    └────────────┬─────────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────┐
    │  Lưu giao dịch Check-in/Out      │
    │  vào Database (parking_logs)     │
    └──────────────────────────────────┘
    ```
    *   **Ưu điểm:** Tiện lợi, không cần cài đặt camera ngoài phức tạp.
    *   **Nhược điểm:** Tải xử lý AI dồn lên luồng web Streamlit, tốc độ phản hồi chậm hơn khi xử lý video thời gian thực.

### 2. Chế độ 2: Chạy kết hợp Semi-manual (Live Camera + Streamlit Dashboard)
Chế độ khuyên dùng cho môi trường bãi đỗ thực tế. Tách biệt hoàn toàn luồng xử lý video AI nặng nề (Camera OpenCV) khỏi luồng hiển thị (Streamlit Web).

*   **Lệnh khởi động (Chạy trên 2 Terminal song song):**
    *   *Terminal 1 (Giao diện giám sát):* `streamlit run app_trial.py`
    *   *Terminal 2 (Camera quét):* `python modules/live_test.py`
*   **Luồng vận hành:**
    ```
    ┌──────────────────────────────────┐
    │   CHẾ ĐỘ 2: CHẠY KẾT HỢP SEMI    │
    └────────────┬─────────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────┐
    │  Terminal 2: Camera quét ngầm    │
    │  YOLO + OCR chạy liên tục ở nền  │
    └────────────┬─────────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────┐
    │  Quét thấy biển số hợp lệ:       │
    │  Voting 2 lần → Ghi tạm DB       │
    │  (parking_config → detected)     │
    └────────────┬─────────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────┐
    │  Terminal 1: Web Streamlit đọc DB│
    │  và tự điền biển số vào Form     │
    └────────────┬─────────────────────┘
                 │
                 ▼
    ┌─────────────────────────────────┐
    │  Nhân viên đối chiếu thực tế và │
    │  chọn một trong hai hành động:  │
    └─────┬────────────────────┬──────┘
          │                    │
      Xác nhận               Bỏ qua
          │                    │
          ▼                    ▼
    ┌─────────────┐       ┌─────────────┐
    │Lưu giao dịch│       │Xóa hàng đợi │
    │  vào DB     │       │  trong DB   │
    └─────────────┘       └─────────────┘
    ```
    *   **Ưu điểm:**
        *   Tối ưu hiệu năng vượt trội nhờ kiến trúc **Multiprocessing** (OCR chạy trên Process riêng, không block giao diện camera/web).
        *   Cơ chế **Voting** (tích lũy 3 lần OCR liên tiếp cùng kết quả) giúp lọc bỏ nhiễu, tránh gửi biển sai lên Dashboard.
        *   Nhân viên chỉ cần kiểm tra lại rồi bấm 1 nút Xác nhận, vô cùng nhanh chóng.
    *   **Cơ chế liên lạc:** Hai tiến trình giao tiếp bất đồng bộ thông qua SQLite bằng bảng cấu hình tạm `parking_config`.

Chi tiết hướng dẫn cài đặt xem tại [Implementation_Guide.md](Implementation_Guide.md)

---

## 🗺️ Lộ trình phát triển

### Phase 1: Chuẩn bị Dataset & Train YOLO (Tuần 1)
- ✅ Setup môi trường Python
- ✅ Cài đặt PyTorch, OpenCV, Ultralytics
- ✅ Tải dataset từ Roboflow
- ✅ Train mô hình YOLOv8 trên tập dữ liệu biển số Việt Nam
- ✅ Xuất mô hình sang định dạng `.pt`

**Kết quả**: Mô hình YOLO nhận diện chính xác vị trí biển số

### Phase 2: Xử lý ảnh - Image Processing (Tuần 2)
- ✅ Viết module cắt ảnh (Crop ROI)
- ✅ Tích hợp các kỹ thuật xử lý: YUV, CLAHE, Resize
- ✅ Tối ưu hóa cho các điều kiện ánh sáng khác nhau

**Kết quả**: Ảnh biển số được chuẩn bị tốt cho OCR

### Phase 3: Tích hợp OCR & Hậu xử lý (Tuần 3-4)
- ✅ Cài đặt PaddleOCR
- ✅ Xử lý xếp dòng (1 dòng vs 2 dòng)
- ✅ Viết logic hậu xử lý với RegEx
- ✅ Kiểm tra định dạng biển số Việt Nam
- ✅ Sửa lỗi OCR phổ biến (0→O, 1→I, v.v.)

**Kết quả**: Nhận dạng text chính xác từ biển số

### Phase 4: Giao diện & Triển khai (Tuần 5)
- ✅ Build UI với Streamlit
- ✅ Tích hợp toàn bộ pipeline
- ✅ Hỗ trợ upload ảnh/video
- ⏳ Hoàn thiện tài liệu
- ⏳ Testing & Demo

**Kết quả**: Ứng dụng hoàn chỉnh sẵn sàng demo

---

## 🔧 Pipeline xử lý

```
┌─────────────────────────────────────────────────────────────┐
│                  Ảnh đầu vào / Video                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │  Module Detection (YOLO)         │
        │  → Phát hiện biển số             │
        │  → Model: best_second.pt         │
        └────────────┬─────────────────────┘
                     │
                     ▼
          ┌────────────────────┐
          │  Tìm thấy biển số? │
          └─────┬──────┬───────┘
                │      │
           Có   │      │ Không
                ▼      ▼
         ┌────────┐  ┌──────────────────┐
         │Tiếp tục│  │Không có biển số  │
         └────┬───┘  └──────────────────┘
              │
              ▼
        ┌──────────────────────────────────┐
        │  Module Processing (OpenCV)      │
        │  → Crop, Resize, YUV             │
        │  → CLAHE tăng tương phản         │
        └────────────┬─────────────────────┘
                     │
                     ▼
        ┌──────────────────────────────────┐
        │  Module OCR Engine               │
        │  → PaddleOCR (Process riêng)     │
        │  → Đọc ký tự, sắp xếp dòng       │
        └────────────┬─────────────────────┘
                     │
                     ▼
        ┌──────────────────────────────────┐
        │  Hậu xử lý (Post-processing)     │
        │  → Ép kiểu vị trí (chữ/số)       │
        │  → RegEx validate format VN      │
        │  → Voting 3 lần liên tiếp        │
        └────────────┬─────────────────────┘
                     │
                     ▼
        ┌──────────────────────────────────┐
        │  Kết quả cuối cùng               │
        │  (VD: 30G12345 hoặc 29A123456)   │
        └──────────────────────────────────┘
```

---

## 👥 Hướng dẫn đóng góp

Chúng tôi hoan nghênh đóng góp từ cộng đồng! Vui lòng fork repository, tạo branch mới và gửi Pull Request.

Xem [Git_Workflow.md](Git_Workflow.md) để chi tiết.

---

## 🐛 Xử lý sự cố

Một số vấn đề phổ biến:
- **YOLO không phát hiện biển số**: Kiểm tra mô hình `models/best_second.pt` và chất lượng ảnh
- **OCR nhận dạng sai**: Điều chỉnh xử lý ảnh (CLAHE clipLimit, resize ratio)
- **GPU không được dùng**: Cài PyTorch với CUDA support
- **Lỗi `database is locked`**: Đảm bảo cả 2 tiến trình đều dùng WAL mode (đã cấu hình sẵn trong code)
- **Camera bị giật/trễ**: Kiểm tra `YOLO_INTERVAL` và `OCR_COOLDOWN` trong `modules/config.py`

---

## 📚 Tài liệu tham khảo

- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [OpenCV Docs](https://docs.opencv.org/)
- [PaddleOCR GitHub](https://github.com/PaddlePaddle/PaddleOCR)
- [Streamlit Docs](https://docs.streamlit.io/)
- [LPR_Project_Roadmap.md](LPR_Project_Roadmap.md) - Kế hoạch chi tiết
- [Implementation_Guide.md](Implementation_Guide.md) - Hướng dẫn triển khai
- [tech_docs/](tech_docs/) - Tài liệu kỹ thuật chuyên sâu (6 file)

---

**Phiên bản**: 1.0.0  
**Cập nhật lần cuối**: Tháng 6, 2026  
**Trạng thái**: 🟡 Đang phát triển
