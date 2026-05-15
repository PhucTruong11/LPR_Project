import cv2
import numpy as np
import os
from detection_vipham import detect_vehicles, get_plate_coordinates
from processing import process_plate

# --- CÀI ĐẶT THÔNG SỐ VƯỢT ĐÈN ĐỎ ---
# Tọa độ Y của vạch dừng (Cần chỉnh lại cho khớp với góc quay của camera trong video)
STOP_LINE_Y = 500 

# Giả lập đèn: Nhấn phím 'r' trên bàn phím để bật Đèn Đỏ, phím 'g' để bật Đèn Xanh
is_red_light = False 

def run_traffic_system_video(video_path):
    global is_red_light
    
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Lỗi: Không thể mở video tại {video_path}")
        return

    print("🚀 Đang chạy hệ thống giám sát trên video...")
    print("👉 HƯỚNG DẪN: Bấm 'r' để bật Đèn Đỏ, 'g' để bật Đèn Xanh. Bấm 'q' để thoát.")
    
    # Biến đếm frame để xử lý vấn đề FPS (Skip frames)
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        
        # Nếu đã đọc hết video thì thoát vòng lặp
        if not ret:
            print("Đã phát hết video.")
            break
            
        frame_count += 1
        
        # CHỐNG LAG: Chỉ cho YOLO quét 1 lần mỗi 3 frames (Skip Frames)
        # Giúp hệ thống chạy mượt hơn trên máy yếu
        if frame_count % 3 != 0:
            continue
            
        h_img, w_img = frame.shape[:2]
        
        # Vẽ vạch dừng và hiển thị trạng thái đèn
        line_color = (0, 0, 255) if is_red_light else (0, 255, 0)
        light_text = "DEN DO" if is_red_light else "DEN XANH"
        
        cv2.line(frame, (0, STOP_LINE_Y), (w_img, STOP_LINE_Y), line_color, 2)
        cv2.putText(frame, f"Trang thai: {light_text}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, line_color, 3)

        # YOLO số 1: Tìm tất cả các xe
        vehicle_boxes = detect_vehicles(frame)

        # Quét từng chiếc xe để phán xét
        if vehicle_boxes is not None:
            for v_box in vehicle_boxes:
                vx1, vy1, vx2, vy2 = map(int, v_box)
                
                # BẮT LỖI VƯỢT ĐÈN ĐỎ
                # Điều kiện 1: Đèn đang Đỏ
                # Điều kiện 2: Đáy chiếc xe (vy2) vượt qua vạch dừng
                # Điều kiện 3 (Mới thêm để tránh bắt nhầm xe ở tít xa): Đỉnh chiếc xe (vy1) cũng phải gần vạch dừng
                if is_red_light and vy2 > STOP_LINE_Y and vy1 < STOP_LINE_Y + 150:
                    color = (0, 0, 255) # Khung Đỏ (Vi phạm)
                    label = "VI PHAM"
                    
                    # Cắt ảnh xe vi phạm
                    vehicle_crop = frame[max(0, vy1):min(h_img, vy2), max(0, vx1):min(w_img, vx2)]
                    
                    if vehicle_crop.size > 0:
                        # YOLO số 2: Tìm biển số
                        plate_box = get_plate_coordinates(vehicle_crop)
                        
                        if plate_box is not None:
                            # Xử lý làm nét biển số
                            processed_plate = process_plate(vehicle_crop, plate_box)
                            
                            # Hiển thị biển số trắng đen ở góc màn hình để dễ theo dõi
                            cv2.imshow("Bien So Vi Pham", processed_plate)
                            # (Tương lai: Chỗ này sẽ chuyển processed_plate cho OCR đọc)
                            
                else:
                    color = (0, 255, 0) # Khung Xanh (Hợp lệ)
                    label = "HOP LE"

                # Vẽ khung và text cho chiếc xe
                cv2.rectangle(frame, (vx1, vy1), (vx2, vy2), color, 2)
                cv2.putText(frame, label, (vx1, vy1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Hiển thị Frame lên màn hình
        # Resize nhẹ lại cửa sổ nếu video quá to (Ví dụ full HD)
        display_frame = cv2.resize(frame, (1024, 768))
        cv2.imshow("He Thong Giam Sat Giao Thong LPR", display_frame)
        
        # Xử lý phím bấm (Dùng waitKey(1) để video chạy liên tục)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'): # Bấm 'q' để quit
            break
        elif key == ord('r'): # Bấm 'r' để bật đèn đỏ
            is_red_light = True
            print("Đã chuyển sang ĐÈN ĐỎ")
        elif key == ord('g'): # Bấm 'g' để bật đèn xanh
            is_red_light = False
            print("Đã chuyển sang ĐÈN XANH")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    video_path = os.path.join(current_dir, "video_ngatu.mp4") 
    
    run_traffic_system_video(video_path)