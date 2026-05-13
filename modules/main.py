import cv2
import numpy as np
from detection_vipham import detect_vehicles, get_plate_coordinates
from processing import process_plate # Gọi hàm của bạn (Phú)

# --- CÀI ĐẶT THÔNG SỐ VƯỢT ĐÈN ĐỎ ---
# Tọa độ Y của vạch dừng (Cần chỉnh lại cho khớp với video/ảnh thực tế)
STOP_LINE_Y = 400 
# Giả lập đèn đang Đỏ (Khi làm UI web, bạn có thể biến nó thành nút bấm)
IS_RED_LIGHT = True 

def run_traffic_system(image_path):
    img = cv2.imread(image_path)
    if img is None:
        print("Lỗi đọc ảnh!")
        return
    
    h_img, w_img = img.shape[:2]
    
    # 1. Vẽ vạch dừng màu vàng lên ảnh để dễ nhìn
    cv2.line(img, (0, STOP_LINE_Y), (w_img, STOP_LINE_Y), (0, 255, 255), 2)
    cv2.putText(img, "VACH DUNG", (10, STOP_LINE_Y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    # 2. Tìm tất cả các xe đang chạy trên đường
    vehicle_boxes = detect_vehicles(img)
    print(f"🚗 Tìm thấy {len(vehicle_boxes)} phương tiện.")

    # 3. Quét từng chiếc xe để phán xét
    for v_box in vehicle_boxes:
        vx1, vy1, vx2, vy2 = map(int, v_box)
        
        # LOGIC PHÁN XÉT VƯỢT ĐÈN ĐỎ:
        # Nếu đáy của chiếc xe (vy2) vượt qua Vạch Dừng (STOP_LINE_Y) VÀ Đèn đang Đỏ
        if vy2 > STOP_LINE_Y and IS_RED_LIGHT:
            color = (0, 0, 255) # Khung Đỏ (Vi phạm)
            label = "VI PHAM"
            
            # --- BẮT ĐẦU XỬ LÝ BIỂN SỐ ---
            # Cắt riêng tấm ảnh chiếc xe vi phạm này ra
            vehicle_crop = img[max(0, vy1):min(h_img, vy2), max(0, vx1):min(w_img, vx2)]
            
            # Đưa tấm ảnh chiếc xe cho YOLO số 2 tìm biển số
            plate_box = get_plate_coordinates(vehicle_crop)
            
            if plate_box is not None:
                print("🚨 Đã túm được biển số xe vi phạm!")
                # Lưu ý: Tọa độ plate_box lúc này là tọa độ tương đối bên trong tấm ảnh vehicle_crop
                # Đưa cho hàm xử lý của Phú làm rõ nét chữ
                processed_plate = process_plate(vehicle_crop, plate_box)
                
                # Hiển thị biển số trắng đen (Giả lập việc gửi cho OCR đọc)
                cv2.imshow("Bien So Vi Pham", processed_plate)
                
        else:
            color = (0, 255, 0) # Khung Xanh (Ngoan ngoãn)
            label = "HOP LE"

        # Vẽ khung bao quanh chiếc xe
        cv2.rectangle(img, (vx1, vy1), (vx2, vy2), color, 3)
        cv2.putText(img, label, (vx1, vy1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # Hiển thị ảnh tổng quan
    cv2.imshow("He Thong Giam Sat", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Đi kiếm 1 tấm ảnh ngã tư có xe chạy qua để test nhé!
    run_traffic_system("modules/test_ngatu.jpg")