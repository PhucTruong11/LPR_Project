from ultralytics import YOLO
import numpy as np

print("Đang tải các mô hình AI... (Có thể mất vài giây)")
# 1. Load mô hình mặc định của YOLO để nhận diện Phương tiện (Xe máy, Ô tô)
# Lần chạy đầu tiên, hệ thống sẽ tự động tải file yolov8n.pt về máy (khoảng 6MB)
vehicle = YOLO("yolov8n.pt")


plate_model = YOLO("models/best.pt")

def detect_vehicles(image):
    """
    Hàm tìm các phương tiện giao thông trong ảnh.
    Chỉ lấy Class 2 (Car), 3 (Motorcycle), 5 (Bus), 7 (Truck).
    """
    # Chạy YOLO với danh sách class cụ thể để lọc bỏ người đi bộ, con chó, v.v.
    results = vehicle(image, classes=[2, 3, 5, 7], verbose=False)
    boxes = results[0].boxes.xyxy.cpu().numpy()
    return boxes

def get_plate_coordinates(vehicle_crop_img):
    """
    Hàm tìm biển số, CHỈ áp dụng trên vùng ảnh của chiếc xe đã bị cắt ra.
    """
    results = plate_model(vehicle_crop_img, verbose=False)
    boxes = results[0].boxes.xyxy.cpu().numpy()
    
    if len(boxes) > 0:
        return boxes[0] # Trả về mảng [x_min, y_min, x_max, y_max] của biển số
    return None