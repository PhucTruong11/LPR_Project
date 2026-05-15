# Phụ trách: Thành viên 1 (Trạm 2: Detection)
# Nhiệm vụ: Tích hợp mô hình YOLO để nhận diện vùng chứa biển số

# from ultralytics import YOLO

from ultralytics import YOLO
import numpy as np

# Load mô hình YOLO
model = YOLO("models/best_second.pt")

def detect_license_plate(image):
    """
    Hàm phát hiện biển số trong ảnh bằng YOLO.
    
    Args:
        image: Ảnh đầu vào.
    
    Returns:
        list: Tọa độ bounding box [x_min, y_min, x_max, y_max].
    """
    # TODO: Viết logic load model YOLO ('models/best.pt') và dự đoán

    # Run model để dự đoán (tắt verbose để terminal không bị rác chữ)
    results = model(image, verbose=False)

    # Lấy danh sách các bounding boxes
    boxes = results[0].boxes.xyxy.cpu().numpy()
    
    if len(boxes) > 0:
        # Nếu tìm thấy nhiều biển số trong 1 ảnh, tạm thời lấy cái đầu tiên
        # Có thể nâng cấp vòng lặp for nếu muốn nhận diện nhiều xe cùng lúc
        bbox = boxes[0] 
        return bbox
    else:
        return None
if __name__ == "__main__":
    # Test thử trực tiếp file detection.py
    import cv2
    
    import os
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_path = os.path.join(current_dir, "test5.jpg")
    test_img = cv2.imread(test_path)
    
    if test_img is not None:
        bbox = detect_license_plate(test_img)
        
        if bbox is not None:
            print(f"🎉 YOLO đã tìm thấy biển số tại tọa độ: {bbox}")
            
            # Vẽ thử cái khung xanh lá cây lên ảnh để kiểm tra mắt YOLO
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(test_img, (x1, y1), (x2, y2), (0, 255, 0), 3)
            cv2.imshow("YOLO Detect", test_img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            print("YOLO không nhìn thấy biển số nào trong ảnh này.")
    else:
        print("Lỗi đọc ảnh test.")
