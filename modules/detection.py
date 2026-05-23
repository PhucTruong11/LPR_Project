# from ultralytics import YOLO
# import numpy as np 

# model = YOLO("models/best_second.pt")

# def detect_license_plate(image):
    
#     # Run model để dự đoán (tắt verbose để terminal không bị rác chữ)
#     results = model(image, verbose=False)

#     # Lấy danh sách các bounding boxes
#     boxes = results[0].boxes
    
#     if len(boxes) > 0:
#         # Lặp qua các box tìm được (phòng trường hợp có 2 biển số)
#         for box in boxes:
#             conf = box.conf.cpu().numpy()[0]
#             if conf > 0.5:
#                 bbox = box.xyxy.cpu().numpy()[0]
#                 return bbox 
#     return None



import os
import logging
import numpy as np
 
log = logging.getLogger("detection")
 
# ---------------------------------------------------------------------------
# CẤU HÌNH — chỉnh tại đây, không chỉnh ở nơi khác
# ---------------------------------------------------------------------------
 
# Danh sách model theo thứ tự ưu tiên (đường dẫn tương đối từ project root)
MODEL_CANDIDATES = [
    "models/best_second.pt",
    "models/best.pt",
]
 
# Ngưỡng confidence tối thiểu để chấp nhận một bounding box
CONF_THRESHOLD: float = 0.5
 
 
# ---------------------------------------------------------------------------
# LOAD MODEL — thực hiện 1 lần duy nhất khi module được import
# ---------------------------------------------------------------------------
 
def _load_model():
    """
    Duyệt qua MODEL_CANDIDATES theo thứ tự ưu tiên.
    Trả về YOLO object hoặc None nếu không load được.
    Import nặng (ultralytics) chỉ chạy ở đây — tránh crash toàn app
    khi máy chưa cài thư viện.
    """
    try:
        from ultralytics import YOLO  # type: ignore
    except ImportError:
        log.error(
            "[YOLO] Chưa cài Ultralytics.\n"
            "       Chạy: pip install ultralytics"
        )
        return None
 
    for path in MODEL_CANDIDATES:
        if os.path.exists(path):
            try:
                mdl = YOLO(path)
                log.info("[YOLO] Đã load mô hình: %s", os.path.abspath(path))
                return mdl
            except Exception as exc:
                log.error("[YOLO] Lỗi load '%s': %s", path, exc)
 
    log.warning(
        "[YOLO] Không tìm thấy file model nào trong: %s\n"
        "       Hệ thống vẫn khởi động nhưng detect_license_plate() "
        "sẽ luôn trả về None.",
        MODEL_CANDIDATES,
    )
    return None
 
 
# Singleton — chỉ load 1 lần, tái sử dụng cho mọi lần gọi
_model = _load_model()
 
 
# ---------------------------------------------------------------------------
# API CÔNG KHAI
# ---------------------------------------------------------------------------
 
def detect_license_plate(image: np.ndarray) -> "np.ndarray | None":
    """
    Phát hiện biển số trong một khung hình.
 
    Tham số
    -------
    image : np.ndarray  —  Frame BGR từ OpenCV  (H × W × 3)
 
    Trả về
    ------
    np.ndarray shape (4,)  —  [x1, y1, x2, y2] của box confidence cao nhất
    None                   —  không phát hiện được / model chưa load
 
    Bảo đảm
    --------
    - Hàm KHÔNG BAO GIỜ raise exception ra ngoài.
    - Chỉ trả về box có conf > CONF_THRESHOLD.
    - Khi có nhiều biển số trong cùng frame → lấy box conf CAO NHẤT
      (tránh nhiễu / xe nền phía sau).
    """
    if _model is None:
        return None
 
    if image is None or not isinstance(image, np.ndarray):
        log.warning("[YOLO] Ảnh đầu vào không hợp lệ: %s", type(image))
        return None
 
    try:
        results  = _model(image, verbose=False)
        boxes    = results[0].boxes
 
        if boxes is None or len(boxes) == 0:
            return None
 
        best_box = None
        max_conf = 0.0
 
        for box in boxes:
            conf = float(box.conf.cpu().numpy()[0])
            if conf > max_conf and conf > CONF_THRESHOLD:
                max_conf = conf
                best_box = box.xyxy.cpu().numpy()[0]   # [x1, y1, x2, y2]
 
        return best_box   # None nếu không box nào vượt ngưỡng
 
    except Exception as exc:
        log.error("[YOLO] Lỗi inference: %s", exc)
        return None
 
 
def is_model_loaded() -> bool:
    """Trả về True nếu YOLO model đã sẵn sàng — dùng để kiểm tra trước khi detect."""
    return _model is not None
 