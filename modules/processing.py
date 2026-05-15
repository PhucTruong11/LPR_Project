# Phụ trách: Thành viên 3 (Trạm 3: Processing)
# Nhiệm vụ: Cắt và xử lý ảnh (OpenCV) trước khi đưa vào OCR

import cv2
import numpy as np
import os

from detection import detect_license_plate

# def deskew(image):
#     """
#     Hàm xoay ảnh chống nghiêng (Deskewing).
#     Sử dụng khung bao nhỏ nhất (minAreaRect) chứa các pixel chữ.
#     """
#     # Lấy tọa độ của tất cả các điểm ảnh (text) có giá trị > 0 (màu trắng)
#     coords = np.column_stack(np.where(image > 0))
#     if len(coords) == 0:
#         return image
        
#     # Tính toán hình chữ nhật nhỏ nhất bao quanh cụm điểm ảnh
#     angle = cv2.minAreaRect(coords)[-1]

#     # Điều chỉnh góc xoay theo phiên bản OpenCV
#     if angle > 45:
#         angle = 90 - angle
#     else:
#         angle = -angle

#     # Tâm ảnh
#     (h, w) = image.shape[:2]
#     center = (w // 2, h // 2)
    
#     # Ma trận xoay và thực hiện xoay
#     M = cv2.getRotationMatrix2D(center, angle, 1.0)
#     # Dùng BORDER_REPLICATE để tránh viền đen khi xoay
#     rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
#     return rotated


def process_plate(image, bbox):
    """
    Hàm cắt và xử lý ảnh biển số xe (Grayscale, CLAHE, Binarization...).
    
    Args:
        image: Ảnh gốc (BGR).
        bbox: Tọa độ biển số [x_min, y_min, x_max, y_max].
        
    Returns:
        Ảnh đã xử lý nhị phân hóa (trắng đen).
    """
    # TODO: Viết code cắt ảnh bằng numpy array (slicing)
    # TODO: OpenCV (Grayscale -> CLAHE -> Blur -> Threshold)
    
    # 1. Cắt ảnh (Crop)
    h_img, w_img = image.shape[:2]
    x_min, y_min, x_max, y_max = map(int, bbox)

    x_min, y_min = max(0, x_min), max(0, y_min)
    x_max, y_max = min(w_img, x_max), min(h_img, y_max)

    plate_crop = image[y_min:y_max, x_min:x_max]
    
    if plate_crop.size == 0:
        return image

    # 2. Xử lý ảnh (Processing)
    gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)

    # 3. Tăng tương phản (Contrast Enhancement)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # 4. Giảm nhiễu (Noise Reduction)
    blur = cv2.GaussianBlur(enhanced, (5,5), 0)
    
    # 5. Nhị phân hóa (Binarization)
    # Chú ý: Dùng THRESH_BINARY_INV để chữ thành màu trắng (255) và nền đen (0) -> giúp hàm deskew tìm tọa độ chữ tốt hơn.
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    # 6. Chống nghiêng (Deskewing)
    # deskewed = deskew(thresh)
    
    # (Tuỳ chọn) Nếu OCR cần chữ đen nền trắng thì đảo ngược lại:
    # final_plate = cv2.bitwise_not(deskewed)
    final_plate = cv2.bitwise_not(thresh)

    
    return final_plate


if __name__ == "__main__":

    # image_path = "modules/test_xemay.jpg" 
    # img = cv2.imread(image_path)

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