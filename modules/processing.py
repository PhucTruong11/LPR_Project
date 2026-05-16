# Phụ trách: Thành viên 3 (Trạm 3: Processing)
# Nhiệm vụ: Cắt và xử lý ảnh (OpenCV) trước khi đưa vào OCR

import cv2
import numpy as np
import os

from detection import detect_license_plate

def process_plate(image, bbox):
    # 1. Cắt ảnh (Crop)
    h_img, w_img = image.shape[:2]
    x_min, y_min, x_max, y_max = map(int, bbox)

    x_min, y_min = max(0, x_min), max(0, y_min)
    x_max, y_max = min(w_img, x_max), min(h_img, y_max)

    plate_crop = image[y_min:y_max, x_min:x_max]
    
    # Chặn lỗi nếu vùng cắt bị rỗng
    if plate_crop.size == 0:
        return None

    # 2. Xử lý ảnh (Processing)
    # gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)

    # # 3. Tăng tương phản (Contrast Enhancement)
    # clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    # enhanced = clahe.apply(gray)
    
    # # 4. Giảm nhiễu (Noise Reduction)
    # blur = cv2.GaussianBlur(enhanced, (5,5), 0)
    
    # # 5. Nhị phân hóa (Binarization)
    # # Chú ý: Dùng THRESH_BINARY_INV để chữ thành màu trắng (255) và nền đen (0) -> giúp hàm deskew tìm tọa độ chữ tốt hơn.
    # thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    # 6. Chống nghiêng (Deskewing)
    # deskewed = deskew(thresh)

    # Ép mọi biển số về cùng chiều cao 200px để thuật toán chạy ổn định
    h_crop, w_crop = plate_crop.shape[:2]
    ratio = 200.0 / float(h_crop)
    plate_crop = cv2.resize(plate_crop, (int(w_crop * ratio), 200), interpolation=cv2.INTER_CUBIC)

    # 2. Xử lý ảnh: Hệ màu HSV lấy kênh V (Độ sáng)
    hsv = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2HSV)
    v_channel = cv2.split(hsv)[2]

    # 3. Tăng tương phản (Contrast Enhancement)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(v_channel)
    
    # 4. Giảm nhiễu (Noise Reduction)
    blur = cv2.GaussianBlur(enhanced, (5,5), 0)
    
    # 5. Nhị phân hóa (Binarization)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 5)

    # 6. Xóa các hạt nhiễu li ti
    clean_thresh = cv2.medianBlur(thresh, 3)

    # 7. Nối liền các nét chữ bị đứt đoạn do rỗ ảnh
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    clean_thresh = cv2.morphologyEx(clean_thresh, cv2.MORPH_CLOSE, kernel)

    # 8. Đảo màu về chuẩn Đen/Trắng cho OCR
    final_plate = cv2.bitwise_not(clean_thresh)

    # 9. Bọc viền trắng 15px để các chữ cái sát mép không bị OCR bỏ qua
    final_plate = cv2.copyMakeBorder(final_plate, 15, 15, 15, 15, cv2.BORDER_CONSTANT, value=(255, 255, 255))


    current_dir = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(current_dir, "debug_plate2.jpg")

    # Lưu ảnh trắng đen đã xử lý xong vào chính thư mục này
    cv2.imwrite(save_path, final_plate)
    print(f"Đã lưu ảnh debug tại: {save_path}")

    return final_plate


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(current_dir, "test5.jpg")
    
    img = cv2.imread(image_path)
    
    if img is None:
        print(f"Lỗi: Không tìm thấy ảnh tại {image_path}")
    else:

        real_box = detect_license_plate(img)
        if real_box is not None:
            print("Dang tim bien so...")

            processed_img = process_plate(img, real_box)

            cv2.imshow("Anh Goc", img)
            cv2.imshow("Bien So Da Xu Ly (Trang Den)", processed_img)
            
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            print("Khong tim thay bien so")