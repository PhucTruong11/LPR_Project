# onfig.py — Cấu hình tập trung cho toàn bộ hệ thống LPR Smart Parking
# Chỉnh thông số TẠI ĐÂY — không cần đụng vào các file khác

import os

# CAMERA & YOLO

# Nguồn video: 0 = webcam mặc định, hoặc đường dẫn file / RTSP URL
VIDEO_SOURCE: int | str = 0

# Kích thước cửa sổ hiển thị OpenCV (width, height)
DISPLAY_SIZE: tuple[int, int] = (640, 480)

# Chạy YOLO mỗi N frame (giảm tải CPU, 1 = mỗi frame)
YOLO_INTERVAL: int = 3

# Resize frame về chiều rộng này (px) trước khi đưa vào YOLO
YOLO_INPUT_WIDTH: int = 640

# Số frame miss liên tiếp trước khi xóa bbox (tăng để tránh nháy)
BBOX_MISS_THRESHOLD: int = 5


# OCR

# Giây — cooldown tối thiểu giữa 2 lần gửi crop vào OCR queue
OCR_COOLDOWN: float = 0.5

# Pixel — dịch chuyển tâm bbox > ngưỡng này → coi là biển số MỚI
BBOX_JUMP_THRESHOLD: int = 60 #35

# Giây — sau thời gian này, force re-verify để phát hiện xe vào/ra
VERIFY_INTERVAL: float = 2.0

# Regex tối thiểu để coi biển số là hợp lệ (Vietnam plate)
# Ví dụ hợp lệ: 29A-111.11, 51G1-23456, 30K-999.99
PLATE_REGEX: str = r"^\d{2}[A-Z]\d?[-–]?\d{3,5}\.?\d{0,2}$"


# DATABASE

# Đường dẫn file SQLite (tương đối từ thư mục gốc project hoặc tuyệt đối)
DB_PATH: str = os.environ.get(
    "PARKING_DB_PATH",
    os.path.join(os.path.dirname(__file__), "..", "parking.db"),
)


# BẢNG GIÁ (VNĐ)

PRICE_FLOOR: int      = 5_000    # Giá sàn (≤ 30 phút đầu)
PRICE_HALF_HOUR: int  = 8_000    # 30 phút < t < 60 phút
PRICE_PER_HOUR: int   = 10_000   # Mỗi giờ trọn vẹn
PRICE_EXTRA_HALF: int = 5_000    # Phút lẻ sau giờ trọn: ≤ 30 phút
PRICE_EXTRA_FULL: int = 8_000    # Phút lẻ sau giờ trọn: > 30 phút

# Sức chứa tối đa mặc định (có thể ghi đè qua DB bảng parking_config)
MAX_CAPACITY: int = 50


# STREAMLIT DASHBOARD

# Tự động làm mới dashboard sau N giây (0 = tắt auto-refresh)
AUTO_REFRESH_SEC: int = 5

# Số bản ghi lịch sử hiển thị tối đa trong tab Lịch sử
HISTORY_DISPLAY_LIMIT: int = 50
