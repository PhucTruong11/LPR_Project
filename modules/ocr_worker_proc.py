# Chạy trong process riêng biệt (multiprocessing) để tránh bị GIL của PaddleOCR
# block main thread hiển thị camera.

import cv2


def run(input_q, result_q):
    from ocr_engine import PlateOCR

    reader = PlateOCR(gpu=False)

    while True:
        item = input_q.get()   # Block cho đến khi có dữ liệu
        if item is None:
            break

        plate_crop = item

        try:
            text = reader.read_plate(plate_crop)
            if text:
                # Xóa kết quả cũ còn tồn trong queue trước khi put kết quả mới
                while not result_q.empty():
                    try:
                        result_q.get_nowait()
                    except Exception:
                        break
                result_q.put(text)
        except Exception as e:
            print(f"[OCR Process] Lỗi: {e}")
