# 🚗 Hệ thống Nhận diện Biển số xe (LPR - License Plate Recognition)

[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/Status-In%20Development-yellow)]()

## 📋 Mục lục
- [Giới thiệu](#-giới-thiệu)
- [Tính năng](#-tính-năng)
- [Công nghệ sử dụng](#-công-nghệ-sử-dụng)
- [Cấu trúc thư mục](#-cấu-trúc-thư-mục)
- [Hướng dẫn cài đặt](#-hướng-dẫn-cài-đặt)
- [Hướng dẫn sử dụng](#-hướng-dẫn-sử-dụng)
- [Lộ trình phát triển](#-lộ-trình-phát-triển)
- [Hướng dẫn đóng góp](#-hướng-dẫn-đóng-góp)
- [Xử lý sự cố](#-xử-lý-sự-cố)

---

## 🎯 Giới thiệu

Dự án **LPR (License Plate Recognition)** là một hệ thống nhận diện biển số xe tích hợp các công nghệ **Deep Learning** và **Computer Vision** tiên tiến:

- **YOLO v8/v11**: Phát hiện vị trí biển số trong ảnh/video
- **OpenCV**: Xử lý ảnh và làm rõ ký tự
- **EasyOCR/PaddleOCR**: Nhận dạng ký tự từ biển số
- **Streamlit**: Giao diện web thân thiện người dùng

Hệ thống được thiết kế để nhận diện **biển số xe Việt Nam** với độ chính xác cao, hỗ trợ các điều kiện ánh sáng khác nhau và xử lý real-time.

---

## ✨ Tính năng

- ✅ **Phát hiện biển số**: Sử dụng YOLO để xác định vị trí biển số với bounding box chính xác
- ✅ **Xử lý ảnh thông minh**: 
  - Chuyển đổi Grayscale, tăng độ tương phản (CLAHE)
  - Thresholding nhị phân hóa
  - Giảm nhiễu và làm rõ ký tự
  - Căn chỉnh góc (Deskewing) nếu cần
- ✅ **Nhận dạng ký tự**: OCR với hỗ trợ tiếng Việt
- ✅ **Hậu xử lý thông minh**: 
  - Kiểm tra định dạng biển số Việt Nam
  - Sửa lỗi phổ biến bằng Regular Expression
  - Xử lý biển số dài (1 dòng) và vuông (2 dòng)
- ✅ **Giao diện web**: Upload ảnh/video và xem kết quả trực quan
- ✅ **Xử lý video**: Hỗ trợ nhận diện từ file video hoặc camera

---

## 🛠️ Công nghệ sử dụng

### Framework & Thư viện
| Công nghệ | Mục đích |
|-----------|---------|
| **PyTorch** | Deep Learning framework cho YOLO |
| **Ultralytics YOLO** | Mô hình phát hiện đối tượng |
| **OpenCV** | Xử lý ảnh và video |
| **EasyOCR** | Nhận dạng ký tự (OCR) |
| **Streamlit** | Giao diện web |
| **NumPy** | Xử lý dữ liệu mảng |

### Công cụ & Nền tảng
- **Ngôn ngữ**: Python 3.9+
- **IDE**: VS Code, PyCharm
- **Quản lý phiên bản**: Git & GitHub
- **Quản lý dữ liệu**: Roboflow
- **Quản lý môi trường**: venv, Conda

---

## 📁 Cấu trúc thư mục

```
LPR_Project/
├── app.py                          # Ứng dụng Streamlit chính
├── requirements.txt                # Danh sách thư viện Python
├── README.md                       # Tài liệu này
├── LPR_Project_Roadmap.md         # Kế hoạch phát triển chi tiết
├── Implementation_Guide.md         # Hướng dẫn cài đặt chi tiết
├── Task_Assignment.md              # Phân công nhiệm vụ thành viên
├── Git_Workflow.md                 # Quy trình Git của dự án
├── note.md                         # Ghi chú tạm
│
├── models/                         # Thư mục lưu trữ các mô hình đã huấn luyện
│   └── .gitkeep                   
│
└── modules/                        # Các module xử lý chính
    ├── detection.py               # Module phát hiện biển số (YOLO)
    ├── processing.py              # Module xử lý ảnh (OpenCV)
    └── ocr_engine.py              # Module nhận dạng ký tự (OCR)
```

### Mô tả chi tiết các module

| Module | Chức năng |
|--------|-----------|
| **detection.py** | Tích hợp YOLO v8/v11 để phát hiện biển số, trả về bounding box |
| **processing.py** | Xử lý ảnh: crop, grayscale, threshold, deskew, tăng tương phản |
| **ocr_engine.py** | Tích hợp EasyOCR/PaddleOCR, hậu xử lý và kiểm tra định dạng |

---

## 📦 Cài đặt

**Yêu cầu**: Python 3.9+, pip, Git

**Cài đặt cơ bản:**
- Clone repository
- Tạo môi trường ảo: `python -m venv lpr_env`
- Kích hoạt môi trường
- Cài đặt dependencies: `pip install -r requirements.txt`

**Chạy ứng dụng:**
```bash
streamlit run app.py
```

Chi tiết xem [Implementation_Guide.md](Implementation_Guide.md)

---

## 🗺️ Lộ trình phát triển

### Phase 1: Chuẩn bị Dataset & Train YOLO (Tuần 1)
- ✅ Setup môi trường Python
- ✅ Cài đặt PyTorch, OpenCV, Ultralytics
- ⏳ Tải dataset từ Roboflow
- ⏳ Train mô hình YOLOv8 trên tập dữ liệu biển số Việt Nam
- ⏳ Xuất mô hình sang định dạng `.pt`

**Kết quả**: Mô hình YOLO nhận diện chính xác vị trí biển số

### Phase 2: Xử lý ảnh - Image Processing (Tuần 2)
- ⏳ Viết module cắt ảnh (Crop ROI)
- ⏳ Tích hợp các kỹ thuật xử lý: Grayscale, CLAHE, Threshold
- ⏳ Tối ưu hóa cho các điều kiện ánh sáng khác nhau
- ⏳ Implement Deskewing cho biển số bị lệch góc

**Kết quả**: Ảnh biển số được chuẩn bị tốt cho OCR

### Phase 3: Tích hợp OCR & Hậu xử lý (Tuần 3-4)
- ⏳ Cài đặt EasyOCR/PaddleOCR
- ⏳ Xử lý xếp dòng (1 dòng vs 2 dòng)
- ⏳ Viết logic hậu xử lý với RegEx
- ⏳ Kiểm tra định dạng biển số Việt Nam
- ⏳ Sửa lỗi OCR phổ biến (0→O, 1→I, v.v.)

**Kết quả**: Nhận dạng text chính xác từ biển số

### Phase 4: Giao diện & Triển khai (Tuần 5)
- ⏳ Build UI với Streamlit
- ⏳ Tích hợp toàn bộ pipeline
- ⏳ Hỗ trợ upload ảnh/video
- ⏳ Hoàn thiện tài liệu
- ⏳ Testing & Demo

**Kết quả**: Ứng dụng hoàn chỉnh sẵn sàng demo

---

## 🔧 Pipeline xử lý

```
┌─────────────────────────────────────────────────────────────┐
│                  Ảnh đầu vào / Video                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │  Module Detection (YOLO)          │
        │  → Phát hiện biển số              │
        └────────────┬─────────────────────┘
                     │
          ┌──────────▼──────────┐
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
        │  → Crop, Grayscale, Threshold    │
        │  → Tăng tương phản, Deskew       │
        └────────────┬─────────────────────┘
                     │
                     ▼
        ┌──────────────────────────────────┐
        │  Module OCR Engine                │
        │  → EasyOCR / PaddleOCR           │
        │  → Đọc ký tự                     │
        └────────────┬─────────────────────┘
                     │
                     ▼
        ┌──────────────────────────────────┐
        │  Hậu xử lý (Post-processing)     │
        │  → RegEx kiểm tra format         │
        │  → Sửa lỗi OCR                   │
        │  → Xử lý biển dài / vuông        │
        └────────────┬─────────────────────┘
                     │
                     ▼
        ┌──────────────────────────────────┐
        │  Kết quả cuối cùng                │
        │  (VD: 30G-12345 hoặc 29HK)      │
        └──────────────────────────────────┘
```

---

## 👥 Hướng dẫn đóng góp

Chúng tôi hoan nghênh đóng góp từ cộng đồng! Vui lòng fork repository, tạo branch mới và gửi Pull Request.

Xem [Git_Workflow.md](Git_Workflow.md) để chi tiết.

---

## 🐛 Xử lý sự cố

Gặp vấn đề? Vui lòng:
- Kiểm tra [Implementation_Guide.md](Implementation_Guide.md) để hướng dẫn chi tiết
- Tạo issue trên [GitHub Issues](https://github.com/your-username/LPR_Project/issues)

Một số vấn đề phổ biến:
- **YOLO không phát hiện biển số**: Kiểm tra mô hình và chất lượng ảnh
- **OCR nhận dạng sai**: Điều chỉnh xử lý ảnh (threshold, contrast)
- **GPU không được dùng**: Cài PyTorch với CUDA support

---

## 📚 Tài liệu tham khảo

- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [OpenCV Docs](https://docs.opencv.org/)
- [EasyOCR GitHub](https://github.com/JaidedAI/EasyOCR)
- [Streamlit Docs](https://docs.streamlit.io/)
- [LPR_Project_Roadmap.md](LPR_Project_Roadmap.md) - Kế hoạch chi tiết
- [Implementation_Guide.md](Implementation_Guide.md) - Hướng dẫn triển khai

---

## � Giấy phép

MIT License - xem file `LICENSE`

---

**Phiên bản**: 1.0.0  
**Cập nhật lần cuối**: Tháng 5, 2026  
**Trạng thái**: 🟡 Đang phát triển
