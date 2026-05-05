# Phụ trách: Thành viên 3 (Trạm 3: Processing)
# Nhiệm vụ: Cắt và xử lý ảnh (OpenCV) trước khi đưa vào OCR

import cv2
import numpy as np

def process_plate(image, bbox):
    """
    Hàm cắt và xử lý ảnh biển số xe (Grayscale, CLAHE, Binarization...).
    
    Args:
        image: Ảnh gốc.
        bbox: Tọa độ biển số [x_min, y_min, x_max, y_max].
        
    Returns:
        Ảnh đã xử lý nhị phân hóa (trắng đen).
    """
    # TODO: Viết code cắt ảnh bằng numpy array (slicing)
    # TODO: OpenCV (Grayscale -> CLAHE -> Blur -> Threshold)
    
    return None
