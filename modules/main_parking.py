import cv2
import os

from detection import detect_license_plate  # Trạm 2: YOLO
from processing import process_plate        # Trạm 3: OpenCV
from ocr_engine import PlateOCR             # Trạm 4: OCR

def run_parking_test(video_path):
    # 1. Khởi tạo Camera/Video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Lỗi: Không thể mở video tại {video_path}")
        return

    # 2. Khởi tạo OCR Engine (CHỈ KHỞI TẠO 1 LẦN Ở ĐÂY ĐỂ TRÁNH LAG)
    print("Đang tải mô hình đọc chữ (OCR)...")
    ocr_reader = PlateOCR(gpu=False) # Đổi thành True nếu máy bạn có Card màn hình rời
    print("Hệ thống Smart Parking đã sẵn sàng!")

    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Đã phát hết video.")
            break
            
        frame_count += 1
        
        # Skip frame: Chỉ xử lý 1 frame mỗi 3 frames để video không bị giật lag
        if frame_count % 3 != 0:
            continue
            
        # --- BƯỚC 1: YOLO TÌM BIỂN SỐ ---
        bbox = detect_license_plate(frame)
        
        if bbox is not None:
            # Lấy tọa độ để vẽ khung
            x1, y1, x2, y2 = map(int, bbox)
            
            # Vẽ khung Xanh lá bao quanh biển số
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # --- BƯỚC 2: OPENCV XỬ LÝ ẢNH ---
            # Truyền frame và tọa độ vào hàm của bạn để lấy ảnh trắng đen
            processed_img = process_plate(frame, bbox)
            
            if processed_img is not None and processed_img.size > 0:
                # Hiển thị cửa sổ nhỏ cho ảnh trắng đen (để debug)
                cv2.imshow("OpenCV Processing", processed_img)
                
                # --- BƯỚC 3: OCR ĐỌC CHỮ ---
                # Truyền trực tiếp ảnh trắng đen vào hàm đọc OCR
                # Chú ý: Hàm read_plate của bạn ấy có thể trả về string, tui gán vào biến text_result
                text_result = ocr_reader.read_plate(processed_img)
                
                if text_result:
                    # In ra terminal để dễ theo dõi
                    print(f"🚗 Nhận diện được xe: {text_result}")
                    
                    # Vẽ chữ lên video màn hình chính
                    # Tạo một cái nền đen mờ sau lưng chữ để dễ đọc hơn
                    cv2.rectangle(frame, (x1, y1 - 40), (x2, y1), (0, 255, 0), -1)
                    cv2.putText(frame, text_result, (x1 + 5, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

        # Hiển thị video chính
        frame_resized = cv2.resize(frame, (1024, 768)) # Thu nhỏ lại nếu video quá to
        cv2.imshow("Smart Parking Camera - Test", frame_resized)
        
        # Bấm 'q' để thoát
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_video_path = os.path.join(current_dir, "test1.jpg") 
    
    run_parking_test(test_video_path)