# import re
# import cv2
# import numpy as np
# from paddleocr import PaddleOCR as POCR

# class PlateOCR:
#     """
#     Class nhận dạng ký tự biển số xe Việt Nam sử dụng PaddleOCR.
#     Hỗ trợ cả biển dài (1 dòng) và biển vuông (2 dòng).
#     """

#     # Vị trí SỐ: sửa chữ cái trông giống số → thành số
#     CHAR_TO_NUM = {
#         'O': '0', 'Q': '0', 'D': '0',
#         'I': '1', 'L': '1',
#         'Z': '2',
#         'S': '5',
#         'G': '6',
#         'T': '7',
#         'B': '8',
#     }

#     # Vị trí CHỮ: sửa số trông giống chữ → thành chữ
#     NUM_TO_CHAR = {
#         '0': 'O',
#         '1': 'A',
#         '8': 'B',
#         '5': 'S',
#         '6': 'G',
#     }

#     def __init__(self, gpu=False):
#         """
#         Khởi tạo PaddleOCR reader.
#         """
#         print("Đang khởi tạo PaddleOCR (lần đầu có thể mất vài giây để tải mô hình)...")
#         # Nhận diện biển số xe chỉ cần ký tự tiếng Anh/Số -> Dùng lang='en' để tăng tốc và giảm dung lượng
#         self.reader = POCR(use_angle_cls=False, lang='en', enable_mkldnn=False, cpu_threads=6)
#         print("PaddleOCR đã sẵn sàng!")

#     def read_plate(self, image):
#         img = self._load_image(image)
#         if img is None:
#             return ""

#         # Nếu img.shape chỉ có 2 phần tử (ảnh xám/nhị phân), ta nhân bản nó lên 3 kênh
#         if len(img.shape) == 2:
#             img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
#         # Phòng trường hợp ảnh có dạng (H, W, 1)
#         elif len(img.shape) == 3 and img.shape[2] == 1:
#             img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

#         # --- Bước 1: Chạy PaddleOCR quét chữ ---
#         results = self.reader.ocr(img)

#         # Trường hợp PaddleOCR không đọc được gì hoặc trả về None
#         if not results or results[0] is None:
#             return ""

#         # Sắp xếp các box chữ tìm được và ghép lại thành chuỗi thô
#         raw_text = self._sort_and_merge_paddle(results[0], img)
        
#         # Làm sạch và sửa lỗi theo cấu trúc biển số Việt Nam
#         final_text = self.clean_and_fix(raw_text)
#         return final_text

#     def _sort_and_merge_paddle(self, result_list, img):
#         """
#         Sắp xếp các cụm chữ nhận diện được từ trên xuống dưới, từ trái sang phải.
#         Phù hợp cho cả biển vuông 2 dòng.
#         """
#         img_height = img.shape[0]

#         if isinstance(result_list, dict) or hasattr(result_list, 'keys'):
#             boxes = result_list.get('dt_polys', [])
#             texts = result_list.get('rec_texts', [])
#             scores = result_list.get('rec_scores', [])
            
#             # Đóng gói lại thành dạng List chuẩn: [ [box, (text, score)], ... ]
#             parsed_list = []
#             for b, t, s in zip(boxes, texts, scores):
#                 parsed_list.append([b, (t, s)])
#             result_list = parsed_list

#         # Lọc bỏ các kết quả có độ tin cậy quá thấp (Dưới 40%)
#         MIN_CONFIDENCE = 0.4
#         valid_results = []
        
#         # Xử lý trích xuất an toàn cho nhiều format khác nhau
#         for r in result_list:
#             try:
#                 box = r[0]
#                 if isinstance(r[1], (tuple, list)):
#                     text = r[1][0]
#                     conf = r[1][1]
#                 else: 
#                     # Đề phòng format trả về dạng phẳng: [box, text, conf]
#                     text = r[1]
#                     conf = r[2] if len(r) > 2 else 1.0
                
#                 if conf > MIN_CONFIDENCE:
#                     # Lưu lại với cấu trúc phẳng cho dễ dùng
#                     valid_results.append([box, text, conf]) 
#             except Exception:
#                 continue

#         if not valid_results:
#             return ""

#         # Hàm lấy tọa độ Y và X trung tâm của hộp chữ
#         def center_y(r):
#             box = r[0]
#             return (box[0][1] + box[2][1]) / 2.0

#         def center_x(r):
#             box = r[0]
#             return (box[0][0] + box[2][0]) / 2.0

#         # Sắp xếp từ trên xuống dưới trước theo trục Y
#         valid_results.sort(key=center_y)

#         # Ngưỡng phân tách dòng (30% chiều cao ảnh crop)
#         line_threshold = img_height * 0.30
#         lines = []
#         current_line = [valid_results[0]]

#         for r in valid_results[1:]:
#             current_line_avg_y = np.mean([center_y(x) for x in current_line])
#             if abs(center_y(r) - current_line_avg_y) <= line_threshold:
#                 current_line.append(r)
#             else:
#                 lines.append(current_line)
#                 current_line = [r]
#         lines.append(current_line)

#         # Trong mỗi dòng, sắp xếp ký tự từ trái sang phải theo trục X
#         for line in lines:
#             line.sort(key=center_x)

#         # Ghép văn bản thô
#         raw_text = ""
#         for line in lines:
#             for r in line:
#                 text_chunk = r[1] # Lấy chuỗi text ra (vì ở trên đã ép về chuẩn [box, text, conf])
#                 if isinstance(text_chunk, str):
#                     raw_text += text_chunk.upper()

#         return raw_text

#     def correct_plate_format(self, text):
#         text = ''.join(e for e in text if e.isalnum()).upper()
#         corrected_text = ""
        
#         for i, char in enumerate(text):
#             if i in [0, 1]:  # Mã tỉnh: BẮT BUỘC LÀ SỐ
#                 corrected_text += self.CHAR_TO_NUM.get(char, char)
#             elif i == 2:     # Series chính: BẮT BUỘC LÀ CHỮ
#                 corrected_text += self.NUM_TO_CHAR.get(char, char)
#             elif i == 3:     # Ký tự thứ 4: Giữ nguyên (có thể là chữ hoặc số tùy loại biển xe)
#                 corrected_text += char
#             elif i >= 4:     # Phần đuôi số: BẮT BUỘC LÀ SỐ
#                 corrected_text += self.CHAR_TO_NUM.get(char, char)
        
#         return corrected_text

#     def clean_and_fix(self, text):
#         text = re.sub(r'[^A-Z0-9]', '', text.upper())
#         print(f"Sau làm sạch: '{text}'")

#         if len(text) < 4:
#             return text

#         fixed_text = self.correct_plate_format(text)
#         print(f"Sau sửa lỗi vị trí: '{fixed_text}'")

#         self._validate_format(fixed_text)
#         return fixed_text

#     def _validate_format(self, text):
#         pattern = r'^[0-9]{2}[A-Z][A-Z0-9]?[0-9]{4,5}$'
#         if re.match(pattern, text):
#             print(f"Biển số HỢP LỆ: {text}")
#         else:
#             if len(text) < 7:
#                 print(f"'{text}' — Quá ngắn")
#             elif len(text) > 9:
#                 print(f"'{text}' — Quá dài")
#             else:
#                 print(f"'{text}' — Định dạng chưa khớp hoàn toàn")

#     def _load_image(self, image):
#         if isinstance(image, np.ndarray):
#             return image
#         elif isinstance(image, str):
#             img = cv2.imread(image)
#             if img is None:
#                 print(f"Lỗi: Không tìm thấy file ảnh tại '{image}'")
#             return img
#         else:
#             print(f"Lỗi: Kiểu dữ liệu không hỗ trợ: {type(image)}")
#             return None

#     def process_ocr(self, image):
#         return self.read_plate(image)
    
import re
import logging
import cv2
import numpy as np
 
log = logging.getLogger("ocr_engine")
 
# ---------------------------------------------------------------------------
# CẤU HÌNH — chỉnh tại đây, không chỉnh ở nơi khác
# ---------------------------------------------------------------------------
 
# Chỉ chấp nhận text-box có độ tin cậy cao hơn ngưỡng này
MIN_CONFIDENCE: float = 0.4
 
# Từ chối chuỗi quá ngắn (chưa đủ cấu trúc biển số)
MIN_PLATE_LEN: int = 7
 
# Regex biển số Việt Nam hợp lệ:
#   2 số (mã tỉnh) + 1 chữ (series) + chữ/số tùy chọn + 4-5 số (dãy đuôi)
#   Ví dụ: 51G12345 / 29HK99999 / 30A12345
PLATE_PATTERN = re.compile(r"^[0-9]{2}[A-Z][A-Z0-9]?[0-9]{4,5}$")
 
# Ngưỡng phân tách 2 dòng (biển vuông) = tỉ lệ * chiều cao ảnh crop
LINE_SPLIT_RATIO: float = 0.30
 
 
# ---------------------------------------------------------------------------
# BẢNG SỬA LỖI OCR — theo vị trí ký tự trong biển số
# ---------------------------------------------------------------------------
 
# Vị trí SỐ (index 0,1 và index ≥4): chữ nhìn giống số → ép thành số
_CHAR_TO_NUM = {
    "O": "0", "Q": "0", "D": "0",
    "I": "1", "L": "1",
    "Z": "2",
    "S": "5",
    "G": "6",
    "T": "7",
    "B": "8",
}
 
# Vị trí CHỮ (index 2): số nhìn giống chữ → ép thành chữ
_NUM_TO_CHAR = {
    "0": "O",
    "1": "A",
    "8": "B",
    "5": "S",
    "6": "G",
}
 
 
# ---------------------------------------------------------------------------
# CLASS CHÍNH
# ---------------------------------------------------------------------------
 
class PlateOCR:
    """
    Nhận dạng ký tự biển số xe Việt Nam bằng PaddleOCR.
    Hỗ trợ biển dài 1 dòng và biển vuông 2 dòng.
    """
 
    def __init__(self, gpu: bool = False):
        """
        Khởi tạo PaddleOCR.
        Chỉ tạo 1 instance duy nhất trong toàn bộ chương trình.
 
        Tham số
        -------
        gpu : bool  —  True để bật GPU (cần cài paddlepaddle-gpu).
                       Mặc định False (CPU).
        """
        log.info("[OCR] Đang khởi tạo PaddleOCR (lần đầu tải model ~vài giây)…")
        try:
            from paddleocr import PaddleOCR as _POCR  # type: ignore
            self._reader = _POCR(
                # use_angle_cls=False,
                lang="en",
                # use_gpu=False,
                # enable_mkldnn=False,
                # cpu_threads=6,
                # show_log=False,      # tắt log rác của PaddleOCR
            )
            log.info("[OCR] PaddleOCR đã sẵn sàng (gpu=%s).", gpu)
        except ImportError:
            log.error(
                "[OCR] Chưa cài PaddleOCR.\n"
                "       Chạy: pip install paddlepaddle paddleocr"
            )
            self._reader = None
 
    # ------------------------------------------------------------------
    # API CÔNG KHAI
    # ------------------------------------------------------------------
 
    def read_plate(self, image) -> str:
        """
        Pipeline đầy đủ: load ảnh → OCR → làm sạch → validate.
 
        Tham số
        -------
        image : np.ndarray | str
            Frame BGR (từ OpenCV) hoặc đường dẫn file ảnh.
 
        Trả về
        ------
        str  —  chuỗi biển số đã làm sạch (VD: "51G12345")
                hoặc "" nếu không đọc được / không hợp lệ.
 
        Bảo đảm
        --------
        - KHÔNG BAO GIỜ raise exception ra ngoài.
        - KHÔNG BAO GIỜ trả về None.
        """
        if self._reader is None:
            return ""
 
        try:
            img = self._load_image(image)
            if img is None:
                return ""
 
            img = self._ensure_bgr(img)
 
            # ── Bước 1: PaddleOCR quét raw text ──────────────────────
            results = self._reader.ocr(img)
            if not results or results[0] is None:
                return ""
 
            # ── Bước 2: Sắp xếp box → ghép chuỗi thô ────────────────
            raw = self._sort_and_merge(results[0], img)
            if not raw:
                return ""
 
            # ── Bước 3: Làm sạch + sửa lỗi vị trí ───────────────────
            plate = self._clean_and_fix(raw)
 
            # ── Bước 4: Kiểm tra độ dài & định dạng ──────────────────
            if len(plate) < MIN_PLATE_LEN:
                log.debug("[OCR] Quá ngắn (%d ký tự): '%s'", len(plate), plate)
                return ""
 
            if PLATE_PATTERN.match(plate):
                log.info("[OCR] Biển số HỢP LỆ: %s", plate)
            else:
                log.debug("[OCR] Không khớp pattern: '%s'", plate)
                # Vẫn trả về — caller (live_test.py) tự quyết định có dùng không
                # Trả "" nếu muốn chỉ chấp nhận biển đúng format hoàn toàn:
                # return ""
 
            return plate
 
        except Exception as exc:
            log.error("[OCR] Lỗi không xử lý được: %s", exc)
            return ""

    #     """
    # Tạm thời fake OCR để test backend.
    # """

    #     return "59A12345"
 
    # Alias tương thích ngược với code cũ dùng process_ocr()
    def process_ocr(self, image) -> str:
        return self.read_plate(image)
 
    # ------------------------------------------------------------------
    # XỬ LÝ NỘI BỘ
    # ------------------------------------------------------------------
 
    def _ensure_bgr(self, img: np.ndarray) -> np.ndarray:
        """Đảm bảo ảnh luôn ở dạng BGR 3 kênh trước khi đưa vào OCR."""
        if len(img.shape) == 2:
            # Ảnh xám → BGR
            return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        if len(img.shape) == 3 and img.shape[2] == 1:
            # (H, W, 1) → BGR
            return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        return img   # Đã là BGR — giữ nguyên
 
    def _sort_and_merge(self, result_list, img: np.ndarray) -> str:
        """
        Chuẩn hoá output PaddleOCR (hỗ trợ nhiều format trả về),
        lọc theo MIN_CONFIDENCE, sắp xếp top→bottom / left→right,
        gom nhóm dòng (biển vuông 2 dòng), rồi ghép thành chuỗi thô.
        """
        img_height = img.shape[0]
 
        # ── Chuẩn hoá về list phẳng: [ [box, text, conf], … ] ────────
        if isinstance(result_list, dict) or hasattr(result_list, "keys"):
            # Format dict (một số phiên bản PaddleOCR mới)
            boxes  = result_list.get("dt_polys", [])
            texts  = result_list.get("rec_texts", [])
            scores = result_list.get("rec_scores", [])
            result_list = [[b, (t, s)] for b, t, s in zip(boxes, texts, scores)]
 
        valid = []
        for r in result_list:
            try:
                box = r[0]
                if isinstance(r[1], (tuple, list)):
                    text, conf = r[1][0], r[1][1]
                else:
                    text = r[1]
                    conf = r[2] if len(r) > 2 else 1.0
                if conf >= MIN_CONFIDENCE and isinstance(text, str):
                    valid.append([box, text.upper(), float(conf)])
            except Exception:
                continue   # bỏ qua phần tử lỗi
 
        if not valid:
            return ""
 
        # ── Hàm tọa độ trung tâm ─────────────────────────────────────
        def cy(r):
            b = r[0]
            return (b[0][1] + b[2][1]) / 2.0
 
        def cx(r):
            b = r[0]
            return (b[0][0] + b[2][0]) / 2.0
 
        valid.sort(key=cy)
 
        # ── Phân nhóm dòng (biển vuông 2 dòng) ───────────────────────
        threshold = img_height * LINE_SPLIT_RATIO
        lines, cur = [], [valid[0]]
        for r in valid[1:]:
            avg_y = float(np.mean([cy(x) for x in cur]))
            if abs(cy(r) - avg_y) <= threshold:
                cur.append(r)
            else:
                lines.append(cur)
                cur = [r]
        lines.append(cur)
 
        # ── Trong mỗi dòng: sắp từ trái sang phải ────────────────────
        for line in lines:
            line.sort(key=cx)
 
        # ── Ghép chuỗi thô ────────────────────────────────────────────
        return "".join(r[1] for line in lines for r in line)
 
    def _clean_and_fix(self, text: str) -> str:
        """
        1. Chỉ giữ ký tự alnum, upper-case.
        2. Sửa lỗi nhầm chữ/số theo VỊ TRÍ trong cấu trúc biển số.
        """
        text = re.sub(r"[^A-Z0-9]", "", text.upper())
        log.debug("[OCR] Sau làm sạch    : '%s'", text)
 
        if len(text) < 3:
            return text
 
        out = []
        for i, ch in enumerate(text):
            if i in (0, 1):     # Mã tỉnh       → BẮT BUỘC SỐ
                out.append(_CHAR_TO_NUM.get(ch, ch))
            elif i == 2:        # Series chính  → BẮT BUỘC CHỮ
                out.append(_NUM_TO_CHAR.get(ch, ch))
            elif i == 3:        # Ký tự phụ     → giữ nguyên (chữ hoặc số)
                out.append(ch)
            else:               # Dãy đuôi số   → BẮT BUỘC SỐ
                out.append(_CHAR_TO_NUM.get(ch, ch))
 
        fixed = "".join(out)
        log.debug("[OCR] Sau sửa vị trí  : '%s'", fixed)
        return fixed
 
    @staticmethod
    def _load_image(image) -> "np.ndarray | None":
        """
        Chấp nhận np.ndarray hoặc đường dẫn file.
        Trả về np.ndarray hoặc None nếu lỗi.
        """
        if isinstance(image, np.ndarray):
            return image
        if isinstance(image, str):
            img = cv2.imread(image)
            if img is None:
                log.warning("[OCR] Không đọc được file ảnh: '%s'", image)
            return img
        log.warning("[OCR] Kiểu đầu vào không hỗ trợ: %s", type(image))
        return None
 