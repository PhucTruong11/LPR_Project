# Phụ trách: Thành viên 1 (Trạm 2: Detection)
# Nhiệm vụ: Tích hợp mô hình YOLO để nhận diện vùng chứa biển số

from ultralytics import YOLO
import numpy as np 

model = YOLO("models/best_second.pt")

def detect_license_plate(image):
    
    # Run model để dự đoán (tắt verbose để terminal không bị rác chữ)
    results = model(image, verbose=False)

    # Lấy danh sách các bounding boxes
    boxes = results[0].boxes
    
    if len(boxes) > 0:
        # Lặp qua các box tìm được (phòng trường hợp có 2 biển số)
        for box in boxes:
            conf = box.conf.cpu().numpy()[0]
            if conf > 0.5:
                bbox = box.xyxy.cpu().numpy()[0]
                return bbox 
    return None

if __name__ == "__main__":
    import cv2
    
    import os
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_path = os.path.join(current_dir, "test5.jpg")
    test_img = cv2.imread(test_path)
    
    if test_img is not None:
        bbox = detect_license_plate(test_img)
        
        if bbox is not None:
            print(f"YOLO đã tìm thấy biển số tại tọa độ: {bbox}")
            
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
