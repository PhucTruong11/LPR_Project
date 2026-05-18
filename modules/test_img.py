import cv2
import os

from detection import detect_license_plate
from processing import process_plate
from ocr_engine import PlateOCR

def test_single_image(image_path):
    # Đọc ảnh gốc
    img = cv2.imread(image_path)
    if img is None:
        print(f"Lỗi: Không thể tìm thấy ảnh tại {image_path}")
        return

    print(f"\nĐANG XỬ LÝ ẢNH: {image_path}")

    # Khởi tạo AI Đọc chữ
    print("Đang tải mô hình OCR...")
    ocr_reader = PlateOCR(gpu=False)

    # YOLO quét tìm vị trí biển số
    print("YOLO đang tìm biển số...")
    bbox = detect_license_plate(img)

    if bbox is not None:
        x1, y1, x2, y2 = map(int, bbox)
        print(f"YOLO khoanh vùng thành công tại: [{x1}, {y1}, {x2}, {y2}]")

        # OpenCV cắt và xử lý làm rõ nét
        print("OpenCV đang nhị phân hóa ảnh...")
        processed_img = process_plate(img, bbox)
        
        if processed_img is not None and processed_img.size > 0:
            # Hiện ảnh đã cắt bởi openCV
            cv2.imshow("1. Anh da cat (Ban giao cho OCR)", processed_img)

            # OCR tiến hành đọc chữ
            print("OCR đang giải mã ký tự...")
            text_result = ocr_reader.read_plate(processed_img)

            if text_result:
                print(f"KẾT QUẢ ĐỌC ĐƯỢC: {text_result}")
                
                # Vẽ khung xanh và in chữ đỏ lên ảnh gốc
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                # Vẽ một cái viền đen mờ dưới chữ để dễ nhìn
                text_y = y1 - 10 if y1 > 35 else y2 + 25
                bg_y1 = y1 - 35 if y1 > 35 else y2
                bg_y2 = y1 if y1 > 35 else y2 + 35

                # cv2.rectangle(img, (x1, bg_y1), (x1 + 150, bg_y2), (0, 0, 0), -1)
                cv2.putText(img, text_result, (x1 + 5, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            else:
                print("OCR bó tay, không đọc được ký tự nào!")
                
            cv2.imshow("2. Ket Qua Nhan Dien", img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            print("Lỗi trong quá trình OpenCV xử lý ảnh!")
    else:
        print("YOLO không nhìn thấy biển số nào trong bức ảnh này!")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    image_name = "test4.webp" 
    
    test_image_path = os.path.join(current_dir, image_name)
    test_single_image(test_image_path)