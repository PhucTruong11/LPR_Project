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
    # Kết nối tới database
    conn = sqlite3.connect(DB_PATH)
    
    # Khởi tạo cursor
    cursor = conn.cursor()
    
    # Tạo bảng parking_logs nếu chưa tồn tại
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parking_logs (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT, 
            plate_number TEXT NOT NULL,
            time_in TIMESTAMP NOT NULL,
            time_out TIMESTAMP,
            status TEXT CHECK(status IN ('IN', 'OUT')),
            fee REAL DEFAULT 0.0
        )
    ''')
    
    # Ghi nhận thay đổi và trả về connection
    conn.commit()
    return conn

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
    # Kết nối database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tìm bản ghi có status='IN' cho biển số này
    cursor.execute(
        "SELECT ticket_id, time_in FROM parking_logs WHERE plate_number = ? AND status = 'IN'",
        (plate_number,)
    )
    result = cursor.fetchone()
    
    current_time = datetime.datetime.now()
    
    # Nếu KHÔNG có bản ghi (Xe đang vào)
    if result is None:
        # Thực hiện CHECK-IN
        cursor.execute(
            "INSERT INTO parking_logs (plate_number, time_in, status, fee) VALUES (?, ?, ?, ?)",
            (plate_number, current_time, 'IN', 0.0)
        )
        conn.commit()
        conn.close()
        
        return {
            "status": "CHECK-IN",
            "time": current_time.strftime("%H:%M:%S"),
            "fee": 0
        }
    
    # Nếu ĐÃ CÓ bản ghi (Xe đang ra)
    else:
        ticket_id, time_in_str = result
        
        # Chuyển time_in từ string thành datetime
        time_in = datetime.datetime.fromisoformat(time_in_str)
        
        # Tính thời gian đã đỗ (giờ)
        duration = current_time - time_in
        total_minutes = int(duration.total_seconds() / 60)

        # Lấy phần nguyên là số giờ trọn ven, phần dư là số phút lẻ
        full_hours = total_minutes // 60
        remaning_minites = total_minutes % 60

        # Tính phí gửi xe
        fee = 0
        if total_minutes <= 30:
            fee = 5000
        elif total_minutes < 60:
            fee = 8000
        else:
            fee = full_hours * 10000
            # Tính tiền cho số phút lẻ (nếu có)
            if 0 < remaning_minites <= 30:
                fee += 5000
            elif remaning_minites > 30:
                fee += 8000
        
        # Cập nhật bản ghi: Thêm time_out, fee, đổi status='OUT'
        cursor.execute(
            "UPDATE parking_logs SET time_out = ?, fee = ?, status = 'OUT' WHERE ticket_id = ?",
            (current_time, fee, ticket_id)
        )
        conn.commit()
        conn.close()
        
        return {
            "status": "CHECK-OUT",
            "time": current_time.strftime("%H:%M:%S"),
            "fee": fee,
            "hours": full_hours,
            "minutes": remaning_minites,
            "total_minutes": total_minutes
        }

if __name__ == "__main__":
    conn = init_db()
    conn.close()
    print(f"Database đã được khởi tạo thành công!")
    print(f"File: {os.path.abspath(DB_PATH)}")
