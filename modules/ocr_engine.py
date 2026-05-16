import easyocr
import re
import cv2
import numpy as np


class PlateOCR:
    """
    Class nhận dạng ký tự biển số xe Việt Nam.
    Hỗ trợ cả biển dài (1 dòng) và biển vuông (2 dòng).
    """

    # -------------------------------------------------------------------------
    # Bảng sửa lỗi OCR theo TỪNG VAI TRÒ của ký tự trong biển số
    # -------------------------------------------------------------------------

    # Vị trí SỐ (mã tỉnh, phần đuôi số): sửa chữ cái trông giống số → thành số
    CHAR_TO_NUM = {
        'O': '0', 'Q': '0', 'D': '0',   # Ký tự trông giống số 0
        'I': '1', 'L': '1',              # Ký tự trông giống số 1
        'Z': '2',                         # Ký tự trông giống số 2
        'S': '5',                         # Ký tự trông giống số 5
        'G': '6',                         # Ký tự trông giống số 6
        'T': '7',                         # Ký tự trông giống số 7
        'B': '8',                         # Ký tự trông giống số 8
    }

    # Vị trí CHỮ (ký tự series): sửa số trông giống chữ → thành chữ
    NUM_TO_CHAR = {
        '0': 'O',  # Số 0 trông giống chữ O (hoặc D - nhưng O phổ biến hơn trong series)
        '1': 'A',  # Hiếm, nhưng phòng trường hợp
        '8': 'B',  # Số 8 trông giống chữ B
        '5': 'S',  # Số 5 trông giống chữ S
        '6': 'G',  # Số 6 trông giống chữ G
    }

    def __init__(self, gpu=False):
        """
        Khởi tạo EasyOCR reader.
        Args:
            gpu (bool): Dùng GPU nếu có, mặc định False cho máy không có card đồ họa.
        """
        print("Đang khởi tạo EasyOCR (lần đầu có thể mất vài giây)...")
        self.reader = easyocr.Reader(['en'], gpu=gpu)
        print("EasyOCR đã sẵn sàng!")

    # =========================================================================
    # HÀM CHÍNH — Thành viên 2 và main.py sẽ gọi hàm này
    # =========================================================================

    def read_plate(self, image):
        img = self._load_image(image)
        if img is None:
            return ""

        # --- BỔ SUNG: Khử nhiễu nhẹ nếu ảnh là ảnh nhị phân ---
        # Giúp loại bỏ các đốm li ti (salt and pepper noise)
        if len(img.shape) == 2: # Nếu là ảnh xám/nhị phân
             img = cv2.medianBlur(img, 3) 
        
        # --- Bước 1: Chạy EasyOCR với tham số tối ưu hơn ---
        # Tăng cường độ chính xác cho biển số vuông
        results = self.reader.readtext(
            img, 
            decoder='beamsearch', # Chậm hơn chút nhưng chính xác hơn
            paragraph=False, 
            width_ths=0.7,      # Tăng khả năng gộp các ký tự ở xa nhau
            contrast_ths=0.1,
            mag_ratio=2,       # Phóng to ảnh gấp đôi giúp đọc nét chữ nhỏ
            y_ths=0.5          # Gom dòng tốt hơn cho biển số xe máy 2 dòng
        )

        if not results:
            return ""

        # Lọc kết quả: Chỉ lấy những box có khả năng là chữ/số
        MIN_CONFIDENCE = 0.2
        results = [r for r in results if r[2] > MIN_CONFIDENCE]

        # Sắp xếp và ghép text (Dùng hàm _sort_and_merge cũ của bạn)
        raw_text = self._sort_and_merge(results, img)
        
        # Làm sạch và sửa lỗi
        final_text = self.clean_and_fix(raw_text)
        return final_text

    # =========================================================================
    # XỬ LÝ SẮP XẾP — Giải quyết bài toán biển số 2 dòng
    # =========================================================================

    def _sort_and_merge(self, results, img):
        """
        Sắp xếp các vùng text theo đúng thứ tự đọc, xử lý cả biển 1 dòng & 2 dòng.

        Vấn đề với biển số 2 dòng (biển vuông):
            Dòng 1: "30G1"  ← phần trên, Y nhỏ
            Dòng 2: "2345"  ← phần dưới, Y lớn
        EasyOCR có thể trả về không theo thứ tự, cần nhóm và sắp xếp lại.

        Logic:
            1. Tính Y trung tâm của mỗi vùng text.
            2. Nhóm các vùng có Y gần nhau vào cùng một "dòng".
            3. Trong mỗi dòng, sắp xếp từ trái → phải theo X.
            4. Ghép nối các dòng từ trên → xuống.
        """
        img_height = img.shape[0]

        # Hàm tính tọa độ trung tâm của bounding box EasyOCR
        # bbox format: [[x1,y1], [x2,y1], [x2,y2], [x1,y2]] (4 điểm góc)
        def center_y(r):
            bbox = r[0]
            return (bbox[0][1] + bbox[2][1]) / 2.0

        def center_x(r):
            bbox = r[0]
            return (bbox[0][0] + bbox[2][0]) / 2.0

        # Sắp xếp tất cả theo Y (từ trên xuống dưới) trước
        results_by_y = sorted(results, key=center_y)

        # Ngưỡng để xác định "cùng dòng" = 30% chiều cao ảnh
        # Nếu 2 vùng text có Y trung tâm cách nhau < threshold → cùng 1 dòng
        line_threshold = img_height * 0.30

        # Gom nhóm thành các dòng
        lines = []
        current_line = [results_by_y[0]]

        for r in results_by_y[1:]:
            # Y trung bình của dòng hiện tại
            current_line_avg_y = np.mean([center_y(x) for x in current_line])
            if abs(center_y(r) - current_line_avg_y) <= line_threshold:
                current_line.append(r)
            else:
                lines.append(current_line)
                current_line = [r]
        lines.append(current_line)

        # Trong mỗi dòng: sắp xếp từ trái sang phải theo X
        for line in lines:
            line.sort(key=center_x)

        # Log để debug
        if len(lines) == 1:
            print("Phát hiện: Biển số 1 DÒNG (biển dài)")
        else:
            print(f"Phát hiện: Biển số {len(lines)} DÒNG (biển vuông)")

        # Ghép tất cả text lại theo thứ tự từ trên xuống dưới, trái sang phải
        raw_text = ""
        for line in lines:
            for (_, text, _) in line:
                raw_text += text.upper()

        return raw_text

    # =========================================================================
    # HẬU XỬ LÝ — Sửa lỗi OCR theo luật biển số Việt Nam
    # =========================================================================

    def correct_plate_format(self, text):
        """
        Bộ lọc vị trí — Ép khuôn sửa lỗi ký tự dựa trên luật biển số Việt Nam.
        
        Cấu trúc: [2 số tỉnh][1 chữ series][1 chữ/số phụ][4-5 số đuôi]
        Ví dụ: 30G12345 hoặc 51FA1234
        
        Args:
            text (str): Chuỗi cần sửa (đã viết hoa).
            
        Returns:
            str: Chuỗi đã được sửa lỗi theo vị trí.
        """
        # Xóa các ký tự đặc biệt, dấu gạch ngang, dấu chấm và viết hoa
        text = ''.join(e for e in text if e.isalnum()).upper()
        
        # Từ điển dịch sai phổ biến
        dict_char_to_num = {
            'O': '0', 'Q': '0', 'D': '0',  # Chữ → số 0
            'I': '1', 'L': '1',             # Chữ → số 1
            'Z': '2',                        # Chữ → số 2
            'S': '5',                        # Chữ → số 5
            'G': '6',                        # Chữ → số 6
            'T': '7',                        # Chữ → số 7
            'B': '8',                        # Chữ → số 8
        }
        dict_num_to_char = {
            '0': 'O', '1': 'A', '2': 'Z', '5': 'S', '6': 'G', '8': 'B'  # Số → chữ
        }
        
        corrected_text = ""
        
        # Ép khuôn dựa trên vị trí
        for i, char in enumerate(text):
            if i == 0 or i == 1:
                # Vị trí 0, 1 (Mã tỉnh): BẮT BUỘC LÀ SỐ
                corrected_text += dict_char_to_num.get(char, char)
                
            elif i == 2:
                # Vị trí 2 (Series chính): BẮT BUỘC LÀ CHỮ CÁI
                corrected_text += dict_num_to_char.get(char, char)
                
            elif i == 3:
                # Vị trí 3: Có thể là chữ (series phụ) hoặc số (bắt đầu đuôi)
                # Giữ nguyên hoặc sử dụng logic nâng cao nếu cần
                corrected_text += char
                
            elif i >= 4:
                # Vị trí 4 trở đi (Phần đuôi số): BẮT BUỘC LÀ SỐ
                corrected_text += dict_char_to_num.get(char, char)
        
        return corrected_text

    def format_plate_text(self, raw_text):
        """
        Ép khuôn dựa trên vị trí ký tự — Phiên bản gọn gàng hơn.
        
        Sử dụng các bảng sửa lỗi từ class attribute (CHAR_TO_NUM, NUM_TO_CHAR).
        
        Args:
            raw_text (str): Chuỗi thô từ OCR.
            
        Returns:
            str: Chuỗi đã được sửa lỗi theo vị trí.
        """
        # Xóa ký tự đặc biệt
        text = ''.join(e for e in raw_text if e.isalnum()).upper()
        
        # Biển số VN thường có từ 7-9 ký tự
        if len(text) < 7:
            return text
            
        corrected_text = ""
        for i, char in enumerate(text):
            # Vị trí 0, 1 (Mã tỉnh) -> ÉP THÀNH SỐ
            if i in [0, 1]:
                corrected_text += self.CHAR_TO_NUM.get(char, char)
            # Vị trí 2 (Series) -> ÉP THÀNH CHỮ
            elif i == 2:
                corrected_text += self.NUM_TO_CHAR.get(char, char)
            # Vị trí đuôi (từ ký tự thứ 4 trở đi) -> ÉP THÀNH SỐ
            elif i >= 4:
                corrected_text += self.CHAR_TO_NUM.get(char, char)
            else:
                # Vị trí 3: Giữ nguyên (có thể là chữ hoặc số)
                corrected_text += char
                
        return corrected_text

    def clean_and_fix(self, text):
        """
        Làm sạch và sửa lỗi văn bản OCR theo cấu trúc biển số Việt Nam.

        Cấu trúc biển số VN (theo Thông tư 58/2020/TT-BCA):
        ┌─────────────────────────────────────────────────────┐
        │  [2 số Mã Tỉnh] [1-2 ký tự Series] [4-5 số Đuôi]  │
        │  Ví dụ:   30    G         1          2345           │
        │           51    F                    12345          │
        └─────────────────────────────────────────────────────┘
        
        Quy tắc sửa lỗi theo VỊ TRÍ:
            - Vị trí 0, 1   : Mã tỉnh → BẮT BUỘC là SỐ
            - Vị trí 2      : Ký tự series chính → BẮT BUỘC là CHỮ
            - Vị trí 3      : Series phụ (nếu có) → Chữ HOẶC số, giữ nguyên
            - Vị trí 4+     : Phần số đuôi → BẮT BUỘC là SỐ

        Args:
            text (str): Chuỗi thô từ OCR (đã viết hoa).

        Returns:
            str: Chuỗi biển số đã được sửa lỗi.
        """
        # --- Bước 1: Làm sạch sơ bộ ---
        # Xóa mọi ký tự không phải chữ cái hoặc chữ số (dấu gạch ngang, dấu cách, v.v.)
        text = re.sub(r'[^A-Z0-9]', '', text.upper())
        print(f"Sau làm sạch: '{text}'")

        if len(text) < 4:
            print("Chuỗi quá ngắn, không thể phân tích.")
            return text

        # --- Bước 2: Sửa lỗi theo VỊ TRÍ (sử dụng Bộ lọc vị trí) ---
        fixed_text = self.correct_plate_format(text)
        print(f"Sau sửa lỗi vị trí: '{fixed_text}'")

        # --- Bước 3: Validate định dạng bằng RegEx ---
        self._validate_format(fixed_text)

        return fixed_text

    def _validate_format(self, text):
        """
        Kiểm tra xem biển số có đúng định dạng Việt Nam không.
        Chỉ dùng để log cảnh báo, không thay đổi kết quả.

        Các định dạng hợp lệ:
            - Biển thường (xe máy/ô tô): 30G12345  → ^[0-9]{2}[A-Z][0-9]{4,5}$
            - Biển có series phụ:        51FA1234  → ^[0-9]{2}[A-Z][A-Z][0-9]{4,5}$
            - Biển xe máy số phụ:        30G12345  (same as first)
        """
        # Pattern tổng quát bao gồm cả 2 loại
        pattern = r'^[0-9]{2}[A-Z][A-Z0-9]?[0-9]{4,5}$'

        if re.match(pattern, text):
            print(f"Biển số HỢP LỆ: {text}")
        else:
            # Thử chẩn đoán lỗi cụ thể hơn để debug
            if len(text) < 7:
                print(f"'{text}' — Quá ngắn (cần ít nhất 7 ký tự)")
            elif len(text) > 9:
                print(f"'{text}' — Quá dài (tối đa 9 ký tự)")
            elif not text[:2].isdigit():
                print(f"'{text}' — 2 ký tự đầu không phải số (mã tỉnh sai)")
            elif not text[2].isalpha():
                print(f"'{text}' — Ký tự thứ 3 không phải chữ (series sai)")
            else:
                print(f"'{text}' — Định dạng chưa khớp, có thể OCR bị sót/thừa ký tự")

    # =========================================================================
    # TIỆN ÍCH
    # =========================================================================

    def _load_image(self, image):
        """
        Hỗ trợ nhận ảnh từ nhiều nguồn khác nhau trong pipeline.
        
        Args:
            image: numpy array (từ processing.py) hoặc str (đường dẫn file).
        
        Returns:
            numpy array hoặc None nếu lỗi.
        """
        if isinstance(image, np.ndarray):
            # Nhận trực tiếp từ processing.py (numpy array BGR hoặc Grayscale)
            return image
        elif isinstance(image, str):
            # Đọc từ đường dẫn file (dùng khi test trực tiếp)
            img = cv2.imread(image)
            if img is None:
                print(f"Lỗi: Không tìm thấy file ảnh tại '{image}'")
            return img
        else:
            print(f"Lỗi: Kiểu dữ liệu không hỗ trợ: {type(image)}")
            return None

    # Giữ lại tên cũ để tương thích với code khác trong nhóm đã viết
    def process_ocr(self, image):
        """Alias của read_plate() để tương thích ngược."""
        return self.read_plate(image)


# =============================================================================
# CHẠY THỬ NGHIỆM TRỰC TIẾP
# =============================================================================

if __name__ == "__main__":
    import os
    import sys

    ocr = PlateOCR(gpu=False)
    print("\n" + "="*55)

    # Kiểm tra xem có truyền argument từ terminal không
    # Ví dụ: python ocr_engine.py test_plate.jpg
    if len(sys.argv) > 1:
        image_input = sys.argv[1]
    else:
        # Mặc định: chạy với ảnh test trong cùng thư mục
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_input = os.path.join(current_dir, "debug_plate.jpg")

    print(f"Đang xử lý: {image_input}")
    print("="*55)

    result = ocr.read_plate(image_input)

    print("="*55)
    if result:
        print(f"KẾT QUẢ BIỂN SỐ: [ {result} ]")
    else:
        print("Không đọc được biển số.")
    print("="*55)