import sqlite3
import datetime
import os

DB_PATH = 'parking.db'

def init_db():
    """
    TODO: Khởi tạo cơ sở dữ liệu SQLite
    1. Kết nối tới file được định nghĩa ở DB_PATH.
    2. Khởi tạo con trỏ cursor.
    3. Tạo bảng 'parking_logs' nếu chưa tồn tại.
       Các cột gợi ý: 
       - ticket_id (Khóa chính, tự động tăng)
       - plate_number (Văn bản)
       - time_in (Thời gian vào)
       - time_out (Thời gian ra)
       - status (Văn bản: 'IN' hoặc 'OUT')
       - fee (Số thực: Phí gửi xe)
    4. Ghi nhận thay đổi (commit) và trả về đối tượng connection.
    """
    pass

def process_vehicle(plate_number):
    """
    TODO: Xử lý logic Check-in / Check-out cho một biển số xe được phát hiện
    
    1. Kết nối DB và tìm kiếm:
       - Tìm trong bảng parking_logs xem biển số này có bản ghi nào đang có status='IN' không.
       
    2. Nếu KHÔNG có (Xe đang vào bãi):
       - Thực hiện Check-in.
       - Lưu bản ghi mới: plate_number, time_in (thời gian hiện tại), status='IN'.
       - Trả về kết quả: "CHECK-IN", chuỗi định dạng thời gian, phí = 0.
       
    3. Nếu ĐÃ CÓ (Xe đang ra khỏi bãi):
       - Thực hiện Check-out.
       - Tính thời gian đã đỗ (Thời gian hiện tại - time_in).
       - Tính phí gửi xe (Ví dụ: tính theo giờ).
       - Cập nhật bản ghi: Thêm time_out, fee, đổi status='OUT'.
       - Trả về kết quả: "CHECK-OUT", chuỗi định dạng thời gian, số tiền phí.
    """
    pass
