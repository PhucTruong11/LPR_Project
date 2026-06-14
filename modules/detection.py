from ultralytics import YOLO
import numpy as np 

model = YOLO("models/best_second.pt")


def detect_license_plate(image):
    
    results = model(image, verbose=False, imgsz=640)

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
