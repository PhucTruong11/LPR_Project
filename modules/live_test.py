import cv2
import multiprocessing as mp
import time
import re
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from detection import detect_license_plate
from processing import process_plate
from config import (
    VIDEO_SOURCE, DISPLAY_SIZE, YOLO_INTERVAL, YOLO_INPUT_WIDTH,
    BBOX_MISS_THRESHOLD, OCR_COOLDOWN, BBOX_JUMP_THRESHOLD,
    VERIFY_INTERVAL, PLATE_REGEX,
)
import database_manager as db

import threading

# Camera phát hiện biển số → ghi vào DB (update_detected_plate)
# Dashboard Streamlit đọc ra → hiển thị cho nhân viên
# Nhân viên bấm nút XE VÀO / XE RA → mới thực sự ghi giao dịch (process_vehicle)


def is_valid_plate(text: str) -> bool:
    """
    Kiểm tra biển số có đúng định dạng biển VN tối thiểu không.
    Tránh ghi rác vào DB khi OCR đọc sai.
    """
    if not text or len(text) < 7:
        return False
    return bool(re.match(PLATE_REGEX, text.strip().upper()))


# CAMERA STREAM (thread riêng, không block main loop)

class CameraStream:
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.grabbed, self.frame = self.stream.read()
        self.stopped = False
        self._lock = threading.Lock()

    def start(self):
        threading.Thread(target=self.update, daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            grabbed, frame = self.stream.read()
            with self._lock:
                self.grabbed = grabbed
                self.frame = frame
            if not grabbed:
                self.stop()

    def read(self):
        with self._lock:
            if self.frame is None:
                return False, None
            return self.grabbed, self.frame.copy()

    def stop(self):
        self.stopped = True
        self.stream.release()


# MAIN LOOP

def run_live_camera(video_source=VIDEO_SOURCE):
    conn = db.init_db()
    conn.close()

    # --- Hai Queue giao tiếp với OCR child process ---
    # input_q : main → OCR   (plate crop đã xử lý)
    # result_q: OCR → main   (text biển số)
    input_q  = mp.Queue(maxsize=1)
    result_q = mp.Queue(maxsize=1)

    # --- Khởi chạy OCR process (KHÔNG phải thread → không bị GIL) ---
    import ocr_worker_proc
    ocr_proc = mp.Process(
        target=ocr_worker_proc.run,
        args=(input_q, result_q),
        daemon=True,
    )
    ocr_proc.start()
    print("Đang khởi tạo OCR process...")

    print(f"Đang kết nối Camera: {video_source}...")
    cam = CameraStream(video_source).start()
    time.sleep(1.5)   # Chờ camera ổn định + OCR process load model

    if not cam.grabbed:
        print("Lỗi: Không thể mở camera!")
        input_q.put(None)
        ocr_proc.join(timeout=2)
        return

    print("Hệ thống Live LPR đã sẵn sàng! Nhấn 'q' để thoát.")

    frame_count       = 0
    last_bbox         = None
    miss_count        = 0
    last_text         = ""      # Biển số OCR hiện tại (hiển thị trên cửa sổ OpenCV)
    last_shared_plate = ""      # Biển số đã share lên DB (chống ghi trùng liên tục)
    last_ocr_time     = 0.0
    last_verify_time  = 0.0

    # Theo dõi vị trí bbox để phát hiện biển số mới
    prev_bbox_center = None

    # Cache kích thước frame để tránh tính lại
    scale = src_w = src_h = None

    while True:
        loop_start = time.time()

        ret, frame = cam.read()
        if not ret or frame is None:
            continue

        frame_count += 1

        if scale is None:
            src_h, src_w = frame.shape[:2]
            scale = YOLO_INPUT_WIDTH / src_w

        # --- YOLO chạy ngắt quãng mỗi YOLO_INTERVAL frame ---
        if frame_count % YOLO_INTERVAL == 0:
            small     = cv2.resize(frame, (int(src_w * scale), int(src_h * scale)))
            small_bbox = detect_license_plate(small)

            if small_bbox is not None:
                miss_count = 0
                sx1, sy1, sx2, sy2 = small_bbox
                new_bbox = [
                    int(sx1 / scale), int(sy1 / scale),
                    int(sx2 / scale), int(sy2 / scale),
                ]

                # --- Phát hiện biển số mới dựa vào bbox jump ---
                new_cx = (new_bbox[0] + new_bbox[2]) / 2
                new_cy = (new_bbox[1] + new_bbox[3]) / 2

                if prev_bbox_center is not None:
                    dx = abs(new_cx - prev_bbox_center[0])
                    dy = abs(new_cy - prev_bbox_center[1])
                    if dx > BBOX_JUMP_THRESHOLD or dy > BBOX_JUMP_THRESHOLD:
                        # Biển mới → xóa state cũ, ép OCR chạy ngay
                        last_text         = ""
                        last_shared_plate = ""
                        last_ocr_time     = 0.0
                        last_verify_time  = 0.0
                        # Drain kết quả cũ trong queue
                        while not result_q.empty():
                            try:
                                result_q.get_nowait()
                            except Exception:
                                break

                prev_bbox_center = (new_cx, new_cy)
                last_bbox = new_bbox

                # Nếu đã có kết quả, cứ mỗi VERIFY_INTERVAL giây verify lại
                now = time.time()
                if last_text and (now - last_verify_time) >= VERIFY_INTERVAL:
                    last_text        = ""
                    last_ocr_time    = 0.0
                    last_verify_time = now
            else:
                miss_count += 1
                if miss_count > BBOX_MISS_THRESHOLD:
                    last_bbox         = None
                    last_text         = ""
                    last_shared_plate = ""
                    prev_bbox_center  = None

        # --- Lấy kết quả OCR (non-blocking) ---
        try:
            new_text = result_q.get_nowait()
            if new_text:
                if new_text != last_text:
                    print(f"[OCR] {last_text!r} → {new_text!r}")
                last_text = new_text

                # Nhân viên sẽ xem biển số trên Dashboard và bấm XE VÀO / XE RA
                if is_valid_plate(new_text) and new_text != last_shared_plate:
                    db.update_detected_plate(new_text)
                    print(f"[DETECT] Biển số hợp lệ: {new_text} → đã gửi lên Dashboard")
                    last_shared_plate = new_text
        except Exception:
            pass   # Chưa có kết quả mới → dùng last_text cũ

        # --- Vẽ UI & Gửi crop cho OCR ---
        if last_bbox is not None:
            x1, y1, x2, y2 = map(int, last_bbox)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Gửi cho OCR: chỉ khi cooldown đã hết VÀ queue trống
            now = time.time()
            if (now - last_ocr_time) >= OCR_COOLDOWN:
                py1, py2 = max(0, y1), min(src_h, y2)
                px1, px2 = max(0, x1), min(src_w, x2)
                plate_crop = frame[py1:py2, px1:px2]

                if plate_crop.size > 0:
                    processed = process_plate(frame, last_bbox)
                    if processed is not None:
                        try:
                            input_q.put_nowait(processed)
                            last_ocr_time = now
                        except Exception:
                            pass  # Queue đầy (OCR vẫn bận) → bỏ qua

            if last_text:
                # Màu box: xanh lá nếu hợp lệ, vàng nếu chưa xác nhận
                box_color = (0, 200, 0) if is_valid_plate(last_text) else (0, 200, 255)
                cv2.rectangle(frame, (x1, max(0, y1 - 40)), (x2, y1), (0, 0, 0), -1)
                cv2.putText(frame, last_text, (x1 + 5, max(15, y1 - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, box_color, 2)

        # --- FPS ---
        elapsed = time.time() - loop_start
        fps = (1.0 / elapsed) if elapsed > 0 else 999
        cv2.putText(frame, f"FPS: {int(fps)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Live Smart Parking Camera",
                   cv2.resize(frame, DISPLAY_SIZE))

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # --- Dọn dẹp ---
    input_q.put(None)
    ocr_proc.join(timeout=3)
    cam.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    mp.freeze_support()
    run_live_camera()








# import cv2
# import multiprocessing as mp
# import time

# from detection import detect_license_plate
# from processing import process_plate

# import threading

# class CameraStream:
#     def __init__(self, src=0):
#         self.stream = cv2.VideoCapture(src)
#         self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
#         self.grabbed, self.frame = self.stream.read()
#         self.stopped = False
#         self._lock = threading.Lock()

#     def start(self):
#         threading.Thread(target=self.update, daemon=True).start()
#         return self

#     def update(self):
#         while not self.stopped:
#             grabbed, frame = self.stream.read()
#             with self._lock:
#                 self.grabbed = grabbed
#                 self.frame = frame
#             if not grabbed:
#                 self.stop()

#     def read(self):
#         with self._lock:
#             if self.frame is None:
#                 return False, None
#             return self.grabbed, self.frame.copy()

#     def stop(self):
#         self.stopped = True
#         self.stream.release()


# # MAIN
# def run_live_camera(video_source=0):
#     # --- Khởi tạo hai Queue để giao tiếp với OCR child process ---
#     # input_q : main → OCR   (plate crop đã xử lý)
#     # result_q: OCR → main   (text biển số)
#     input_q  = mp.Queue(maxsize=1)
#     result_q = mp.Queue(maxsize=1)

#     # --- Khởi chạy OCR process (KHÔNG phải thread → không bị GIL) ---
#     import ocr_worker_proc
#     ocr_proc = mp.Process(
#         target=ocr_worker_proc.run,
#         args=(input_q, result_q),
#         daemon=True
#     )
#     ocr_proc.start()
#     print("Đang khởi tạo OCR process...")

#     print(f"Đang kết nối Camera: {video_source}...")
#     cam = CameraStream(video_source).start()
#     time.sleep(1.5)   # Chờ camera ổn định + OCR process load model

#     if not cam.grabbed:
#         print("Lỗi: Không thể mở camera!")
#         input_q.put(None)
#         ocr_proc.join(timeout=2)
#         return

#     print("Hệ thống Live LPR đã sẵn sàng! Nhấn 'q' để thoát.")

#     frame_count   = 0
#     last_bbox     = None
#     miss_count    = 0
#     last_text     = ""
#     last_ocr_time = 0.0
#     OCR_COOLDOWN  = 0.5   # Giây — cooldown giữa 2 lần OCR 1.0

#     # Theo dõi vị trí bbox để phát hiện biển số mới
#     prev_bbox_center   = None
#     BBOX_JUMP_THRESHOLD = 35  # pixel — dịch chuyển > ngưỡng này = biển mới 50

#     # Cache kích thước frame để tránh tính lại
#     scale = src_w = src_h = None
#     display_size = (1024, 768)

#     while True:
#         loop_start = time.time()

#         ret, frame = cam.read()
#         if not ret or frame is None:
#             continue

#         frame_count += 1

#         if scale is None:
#             src_h, src_w = frame.shape[:2]
#             scale = 640.0 / src_w

#         # --- YOLO chạy ngắt quãng mỗi 3 frame ---
#         if frame_count % 3 == 0:
#             small = cv2.resize(frame, (int(src_w * scale), int(src_h * scale)))
#             small_bbox = detect_license_plate(small)

#             if small_bbox is not None:
#                 miss_count = 0
#                 sx1, sy1, sx2, sy2 = small_bbox
#                 new_bbox = [
#                     int(sx1 / scale), int(sy1 / scale),
#                     int(sx2 / scale), int(sy2 / scale)
#                 ]

#                 # Nếu đã có kết quả, cứ mỗi 2s verify lại để phát hiện xe mới
#                 now = time.time()
#                 if last_text and (now - last_ocr_time) >= 2.0:
#                     last_text = ""
#                     last_ocr_time = 0.0   # ép OCR chạy lại ngay
#                 last_bbox = new_bbox

#                 # --- Phát hiện biển số mới dựa vào bbox jump ---
#                 new_cx = (new_bbox[0] + new_bbox[2]) / 2
#                 new_cy = (new_bbox[1] + new_bbox[3]) / 2

#                 if prev_bbox_center is not None:
#                     dx = abs(new_cx - prev_bbox_center[0])
#                     dy = abs(new_cy - prev_bbox_center[1])
#                     if dx > BBOX_JUMP_THRESHOLD or dy > BBOX_JUMP_THRESHOLD:
#                         # Biển mới → xóa state cũ, ép OCR chạy ngay
#                         last_text     = ""
#                         last_ocr_time = 0.0
#                         # Drain kết quả cũ trong queue
#                         while not result_q.empty():
#                             try:
#                                 result_q.get_nowait()
#                             except Exception:
#                                 break
#                         # Drain luôn input_q để hủy bỏ ảnh xe cũ đang kẹt
#                         while not input_q.empty():
#                             try:
#                                 input_q.get_nowait()
#                             except Exception:
#                                 break

#                 prev_bbox_center = (new_cx, new_cy)
#                 last_bbox = new_bbox
#             else:
#                 miss_count += 1
#                 if miss_count > 2: # miss_count > 3
#                     last_bbox        = None
#                     last_text        = ""
#                     prev_bbox_center = None

#         # --- Lấy kết quả OCR (non-blocking) ---
#         try:
#             new_text = result_q.get_nowait()
#             if new_text:
#                 # last_text = new_text
#                 if new_text != last_text:   # xe mới!
#                     print(f"[NEW CAR] {last_text} → {new_text}")
#                     # TODO: ghi vào database bãi đỗ xe ở đây
#                 last_text = new_text
#         except Exception:
#             pass   # Chưa có kết quả mới → dùng last_text cũ

#         # --- Vẽ UI & Gửi crop cho OCR ---
#         if last_bbox is not None:
#             x1, y1, x2, y2 = map(int, last_bbox)
#             cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

#             # Gửi cho OCR: chỉ khi cooldown đã hết VÀ queue trống
#             now = time.time()
#             if (now - last_ocr_time) >= OCR_COOLDOWN:
#                 # Crop plate trước khi gửi → pickle nhỏ hơn nhiều so với full frame
#                 py1, py2 = max(0, y1), min(src_h, y2)
#                 px1, px2 = max(0, x1), min(src_w, x2)
#                 plate_crop = frame[py1:py2, px1:px2]

#                 if plate_crop.size > 0:
#                     # Preprocess ngay tại đây (main thread nhẹ, chạy nhanh)
#                     processed = process_plate(frame, last_bbox)
#                     if processed is not None:
#                         try:
#                             input_q.put_nowait(processed)
#                             last_ocr_time = now
#                         except Exception:
#                             pass  # Queue đầy (OCR vẫn bận) → bỏ qua

#             if last_text:
#                 cv2.rectangle(frame, (x1, max(0, y1 - 40)), (x2, y1), (0, 0, 0), -1)
#                 cv2.putText(frame, last_text, (x1 + 5, max(15, y1 - 10)),
#                             cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

#         # --- FPS ---
#         elapsed = time.time() - loop_start
#         fps = (1.0 / elapsed) if elapsed > 0 else 999
#         cv2.putText(frame, f"FPS: {int(fps)}", (10, 30),
#                     cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

#         cv2.imshow("Live Smart Parking Camera",
#                    cv2.resize(frame, display_size))

#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

#     # --- Dọn dẹp ---
#     input_q.put(None)
#     ocr_proc.join(timeout=3)
#     cam.stop()
#     cv2.destroyAllWindows()


# if __name__ == "__main__":
#     mp.freeze_support()
#     run_live_camera(0)