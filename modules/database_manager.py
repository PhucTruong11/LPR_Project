# import sqlite3
# import datetime
# import os

# DB_PATH = 'parking.db'

# def init_db():
#     """
#     TODO: Khởi tạo cơ sở dữ liệu SQLite
#     1. Kết nối tới file được định nghĩa ở DB_PATH.
#     2. Khởi tạo con trỏ cursor.
#     3. Tạo bảng 'parking_logs' nếu chưa tồn tại.
#        Các cột gợi ý: 
#        - ticket_id (Khóa chính, tự động tăng)
#        - plate_number (Văn bản)
#        - time_in (Thời gian vào)
#        - time_out (Thời gian ra)
#        - status (Văn bản: 'IN' hoặc 'OUT')
#        - fee (Số thực: Phí gửi xe)
#     4. Ghi nhận thay đổi (commit) và trả về đối tượng connection.
#     """
#     # Kết nối tới database
#     conn = sqlite3.connect(DB_PATH)
    
#     # Khởi tạo cursor
#     cursor = conn.cursor()
    
#     # Tạo bảng parking_logs nếu chưa tồn tại
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS parking_logs (
#             ticket_id INTEGER PRIMARY KEY AUTOINCREMENT, 
#             plate_number TEXT NOT NULL,
#             time_in TIMESTAMP NOT NULL,
#             time_out TIMESTAMP,
#             status TEXT CHECK(status IN ('IN', 'OUT')),
#             fee REAL DEFAULT 0.0
#         )
#     ''')
    
#     # Ghi nhận thay đổi và trả về connection
#     conn.commit()
#     return conn

# def process_vehicle(plate_number):
#     """
#     TODO: Xử lý logic Check-in / Check-out cho một biển số xe được phát hiện
    
#     1. Kết nối DB và tìm kiếm:
#        - Tìm trong bảng parking_logs xem biển số này có bản ghi nào đang có status='IN' không.
       
#     2. Nếu KHÔNG có (Xe đang vào bãi):
#        - Thực hiện Check-in.
#        - Lưu bản ghi mới: plate_number, time_in (thời gian hiện tại), status='IN'.
#        - Trả về kết quả: "CHECK-IN", chuỗi định dạng thời gian, phí = 0.
       
#     3. Nếu ĐÃ CÓ (Xe đang ra khỏi bãi):
#        - Thực hiện Check-out.
#        - Tính thời gian đã đỗ (Thời gian hiện tại - time_in).
#        - Tính phí gửi xe (Ví dụ: tính theo giờ).
#        - Cập nhật bản ghi: Thêm time_out, fee, đổi status='OUT'.
#        - Trả về kết quả: "CHECK-OUT", chuỗi định dạng thời gian, số tiền phí.
#     """
#     # Kết nối database
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()
    
#     # Tìm bản ghi có status='IN' cho biển số này
#     cursor.execute(
#         "SELECT ticket_id, time_in FROM parking_logs WHERE plate_number = ? AND status = 'IN'",
#         (plate_number,)
#     )
#     result = cursor.fetchone()
    
#     current_time = datetime.datetime.now()
    
#     # Nếu KHÔNG có bản ghi (Xe đang vào)
#     if result is None:
#         # Thực hiện CHECK-IN
#         cursor.execute(
#             "INSERT INTO parking_logs (plate_number, time_in, status, fee) VALUES (?, ?, ?, ?)",
#             (plate_number, current_time, 'IN', 0.0)
#         )
#         conn.commit()
#         conn.close()
        
#         return {
#             "status": "CHECK-IN",
#             "time": current_time.strftime("%H:%M:%S"),
#             "fee": 0
#         }
    
#     # Nếu ĐÃ CÓ bản ghi (Xe đang ra)
#     else:
#         ticket_id, time_in_str = result
        
#         # Chuyển time_in từ string thành datetime
#         time_in = datetime.datetime.fromisoformat(time_in_str)
        
#         # Tính thời gian đã đỗ (giờ)
#         duration = current_time - time_in
#         total_minutes = int(duration.total_seconds() / 60)

#         # Lấy phần nguyên là số giờ trọn ven, phần dư là số phút lẻ
#         full_hours = total_minutes // 60
#         remaning_minites = total_minutes % 60

#         # Tính phí gửi xe
#         fee = 0
#         if total_minutes <= 30:
#             fee = 5000
#         elif total_minutes < 60:
#             fee = 8000
#         else:
#             fee = full_hours * 10000
#             # Tính tiền cho số phút lẻ (nếu có)
#             if 0 < remaning_minites <= 30:
#                 fee += 5000
#             elif remaning_minites > 30:
#                 fee += 8000
        
#         # Cập nhật bản ghi: Thêm time_out, fee, đổi status='OUT'
#         cursor.execute(
#             "UPDATE parking_logs SET time_out = ?, fee = ?, status = 'OUT' WHERE ticket_id = ?",
#             (current_time, fee, ticket_id)
#         )
#         conn.commit()
#         conn.close()
        
#         return {
#             "status": "CHECK-OUT",
#             "time": current_time.strftime("%H:%M:%S"),
#             "fee": fee,
#             "hours": full_hours,
#             "minutes": remaning_minites,
#             "total_minutes": total_minutes
#         }

# if __name__ == "__main__":
#     conn = init_db()
#     conn.close()
#     print(f"Database đã được khởi tạo thành công!")
#     print(f"File: {os.path.abspath(DB_PATH)}")


import sqlite3
import datetime
import os
import logging

# ---------------------------------------------------------------------------
# CẤU HÌNH
# ---------------------------------------------------------------------------

DB_PATH = os.environ.get("PARKING_DB_PATH", "parking.db")

# Sức chứa tối đa của bãi (chỉnh lại tuỳ thực tế)
MAX_CAPACITY: int = 50

# Bảng giá (VNĐ) — chỉnh tại một nơi duy nhất, hiệu lực toàn hệ thống
PRICE_FLOOR      = 5_000    # Giá sàn (≤ 30 phút đầu)
PRICE_HALF_HOUR  = 8_000    # 30 phút < t < 60 phút
PRICE_PER_HOUR   = 10_000   # Mỗi giờ trọn vẹn
PRICE_EXTRA_HALF = 5_000    # Phút lẻ sau giờ trọn: ≤ 30 phút
PRICE_EXTRA_FULL = 8_000    # Phút lẻ sau giờ trọn: > 30 phút

# Định dạng timestamp thống nhất toàn hệ thống (ISO-8601 microseconds)
DT_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("parking_db")


# ---------------------------------------------------------------------------
# KHỞI TẠO DATABASE
# ---------------------------------------------------------------------------

def init_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    Khởi tạo (hoặc mở) database SQLite và đảm bảo schema đúng chuẩn.

    Thay đổi so với phiên bản cũ
    ----------------------------
    - Cột `status` thêm ràng buộc NOT NULL  ← yêu cầu bắt buộc
    - Thêm bảng `parking_config` để lưu MAX_CAPACITY linh hoạt
    - PRAGMA foreign_keys + journal_mode WAL để an toàn khi ghi đồng thời
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row          # truy cập cột bằng tên
    conn.execute("PRAGMA journal_mode=WAL") # ghi an toàn khi nhiều reader
    conn.execute("PRAGMA foreign_keys=ON")

    conn.executescript("""
        -- Bảng lịch sử giao dịch chính
        CREATE TABLE IF NOT EXISTS parking_logs (
            ticket_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_number TEXT    NOT NULL,
            time_in      TEXT    NOT NULL,   -- ISO-8601 microseconds
            time_out     TEXT,               -- NULL khi xe đang trong bãi
            status       TEXT    NOT NULL    -- ← NOT NULL bắt buộc
                             CHECK(status IN ('IN', 'OUT')),
            fee          REAL    NOT NULL DEFAULT 0.0
                             CHECK(fee >= 0)
        );

        -- Index tăng tốc truy vấn tìm xe đang trong bãi
        CREATE INDEX IF NOT EXISTS idx_plate_status
            ON parking_logs (plate_number, status);

        -- Bảng cấu hình bãi (sức chứa, tên bãi, …)
        CREATE TABLE IF NOT EXISTS parking_config (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        -- Giá trị mặc định cho MAX_CAPACITY (chỉ INSERT khi chưa có)
        INSERT OR IGNORE INTO parking_config (key, value)
        VALUES ('max_capacity', '50');
    """)

    conn.commit()
    log.info("Database khởi tạo thành công: %s", os.path.abspath(db_path))
    return conn


# ---------------------------------------------------------------------------
# TIỆN ÍCH NỘI BỘ
# ---------------------------------------------------------------------------

def _get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Mở kết nối ngắn hạn (mỗi request một connection)."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _get_max_capacity(conn: sqlite3.Connection) -> int:
    """Đọc sức chứa tối đa từ bảng config (fallback về hằng số)."""
    row = conn.execute(
        "SELECT value FROM parking_config WHERE key = 'max_capacity'"
    ).fetchone()
    return int(row["value"]) if row else MAX_CAPACITY


def _count_vehicles_inside(conn: sqlite3.Connection) -> int:
    """
    Đếm số xe đang trong bãi (status = 'IN').
    NOT NULL trên cột status đảm bảo không bao giờ bị đếm lẫn NULL.
    """
    row = conn.execute(
        "SELECT COUNT(*) AS cnt FROM parking_logs WHERE status = 'IN'"
    ).fetchone()
    return row["cnt"]


def _calculate_fee(total_minutes: int) -> float:
    """
    Tính phí gửi xe theo bảng giá luỹ tiến.

    Quy tắc:
        ≤ 30 phút             → PRICE_FLOOR  (5.000 VNĐ)
        > 30 phút & < 60 phút → PRICE_HALF_HOUR (8.000 VNĐ)
        ≥ 60 phút             → full_hours × PRICE_PER_HOUR
                                + phút lẻ (≤ 30 → 5.000 | > 30 → 8.000)

    Giá sàn tuyệt đối: PRICE_FLOOR.  Fee không bao giờ âm.
    """
    if total_minutes <= 0:
        return float(PRICE_FLOOR)

    if total_minutes <= 30:
        return float(PRICE_FLOOR)

    if total_minutes < 60:
        return float(PRICE_HALF_HOUR)

    full_hours      = total_minutes // 60
    remaining_mins  = total_minutes % 60

    fee = full_hours * PRICE_PER_HOUR
    if 0 < remaining_mins <= 30:
        fee += PRICE_EXTRA_HALF
    elif remaining_mins > 30:
        fee += PRICE_EXTRA_FULL

    return max(float(PRICE_FLOOR), float(fee))


# ---------------------------------------------------------------------------
# API CÔNG KHAI
# ---------------------------------------------------------------------------

def process_vehicle(plate_number: str, db_path: str = DB_PATH) -> dict:
    """
    Điểm tích hợp chính — gọi từ live_test.py khi OCR đọc được biển số.

    Tham số
    -------
    plate_number : str  — biển số xe (đã qua hậu xử lý RegEx từ OCR)

    Trả về
    ------
    dict với các key:
        status        : "CHECK-IN" | "CHECK-OUT" | "ERROR"
        plate_number  : biển số
        message       : mô tả kết quả (tiếng Việt)
        time          : thời gian thực hiện (HH:MM:SS)
        fee           : số tiền (VNĐ)  — 0 khi CHECK-IN
        ticket_id     : mã vé
        -- Chỉ có khi CHECK-OUT --
        total_minutes : tổng thời gian gửi xe
        hours         : số giờ trọn vẹn
        minutes       : số phút lẻ

    Luồng xử lý
    -----------
    CHECK-IN:
        1. Kiểm tra bãi còn chỗ không → từ chối nếu đầy
        2. Kiểm tra xe chưa có bản ghi IN → chống spam quét lại
        3. Lưu bản ghi mới status='IN'

    CHECK-OUT:
        1. Tìm bản ghi IN của biển số
        2. Tính thời gian & phí
        3. Cập nhật time_out, fee, status='OUT'
    """
    plate_number = plate_number.strip().upper()

    if not plate_number:
        return _error_result("", "Biển số rỗng — bỏ qua.")

    conn = _get_connection(db_path)
    try:
        # --- Tìm bản ghi đang IN của biển số này ---
        existing = conn.execute(
            """SELECT ticket_id, time_in
               FROM parking_logs
               WHERE plate_number = ? AND status = 'IN'
               LIMIT 1""",
            (plate_number,),
        ).fetchone()

        now     = datetime.datetime.now()
        now_str = now.strftime(DT_FORMAT)

        # ================================================================
        # TRƯỜNG HỢP 1 — KHÔNG TÌM THẤY BẢN GHI IN → CHECK-IN
        # ================================================================
        if existing is None:
            # Kiểm tra sức chứa
            current_count = _count_vehicles_inside(conn)
            max_cap       = _get_max_capacity(conn)

            if current_count >= max_cap:
                log.warning("BÃI ĐẦY: %d/%d — từ chối %s", current_count, max_cap, plate_number)
                return _error_result(
                    plate_number,
                    f"Bãi xe đã đầy ({current_count}/{max_cap} chỗ). Không thể Check-in.",
                    code="FULL",
                )

            # Lưu bản ghi CHECK-IN
            cursor = conn.execute(
                """INSERT INTO parking_logs (plate_number, time_in, status, fee)
                   VALUES (?, ?, 'IN', 0.0)""",
                (plate_number, now_str),
            )
            conn.commit()
            ticket_id = cursor.lastrowid
            occupancy = current_count + 1

            log.info("CHECK-IN  | %s | vé #%d | chỗ: %d/%d",
                     plate_number, ticket_id, occupancy, max_cap)

            return {
                "status":       "CHECK-IN",
                "plate_number": plate_number,
                "message":      f"Check-in thành công. Vé #{ticket_id}. Bãi còn {max_cap - occupancy} chỗ.",
                "time":         now.strftime("%H:%M:%S"),
                "fee":          0,
                "ticket_id":    ticket_id,
                "occupancy":    occupancy,
                "max_capacity": max_cap,
            }

        # ================================================================
        # TRƯỜNG HỢP 2 — TÌM THẤY BẢN GHI IN → CHECK-OUT
        # ================================================================
        ticket_id   = existing["ticket_id"]
        time_in_str = existing["time_in"]

        # Parse time_in — hỗ trợ cả format cũ (không có microseconds)
        try:
            time_in = datetime.datetime.strptime(time_in_str, DT_FORMAT)
        except ValueError:
            time_in = datetime.datetime.fromisoformat(time_in_str)

        duration       = now - time_in
        total_minutes  = max(0, int(duration.total_seconds() / 60))
        full_hours     = total_minutes // 60
        remaining_mins = total_minutes % 60
        fee            = _calculate_fee(total_minutes)

        conn.execute(
            """UPDATE parking_logs
               SET time_out = ?, fee = ?, status = 'OUT'
               WHERE ticket_id = ?""",
            (now_str, fee, ticket_id),
        )
        conn.commit()

        occupancy = _count_vehicles_inside(conn)   # đếm lại sau khi xe ra
        max_cap   = _get_max_capacity(conn)

        log.info("CHECK-OUT | %s | vé #%d | %dh%dm | phí: %s VNĐ",
                 plate_number, ticket_id, full_hours, remaining_mins, f"{fee:,.0f}")

        return {
            "status":        "CHECK-OUT",
            "plate_number":  plate_number,
            "message":       (
                f"Check-out thành công. Vé #{ticket_id}. "
                f"Thời gian: {full_hours}h {remaining_mins}m. "
                f"Phí: {fee:,.0f} VNĐ."
            ),
            "time":          now.strftime("%H:%M:%S"),
            "fee":           fee,
            "ticket_id":     ticket_id,
            "total_minutes": total_minutes,
            "hours":         full_hours,
            "minutes":       remaining_mins,
            "occupancy":     occupancy,
            "max_capacity":  max_cap,
        }

    except sqlite3.Error as exc:
        conn.rollback()
        log.error("DB error khi xử lý %s: %s", plate_number, exc)
        return _error_result(plate_number, f"Lỗi cơ sở dữ liệu: {exc}")

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CÁC HÀM THỐNG KÊ (dùng cho Dashboard / Streamlit)
# ---------------------------------------------------------------------------

def get_status(db_path: str = DB_PATH) -> dict:
    """
    Trả về snapshot trạng thái hiện tại của bãi.

    Dùng để cập nhật Dashboard real-time.
    """
    conn = _get_connection(db_path)
    try:
        occupancy = _count_vehicles_inside(conn)
        max_cap   = _get_max_capacity(conn)
        vehicles_inside = [
            dict(row)
            for row in conn.execute(
                "SELECT ticket_id, plate_number, time_in FROM parking_logs "
                "WHERE status = 'IN' ORDER BY time_in DESC"
            ).fetchall()
        ]
        return {
            "occupancy":        occupancy,
            "max_capacity":     max_cap,
            "available_spaces": max_cap - occupancy,
            "is_full":          occupancy >= max_cap,
            "vehicles_inside":  vehicles_inside,
        }
    finally:
        conn.close()


def get_revenue_today(db_path: str = DB_PATH) -> dict:
    """Doanh thu và số lượt ra trong ngày hôm nay."""
    today = datetime.date.today().isoformat()
    conn  = _get_connection(db_path)
    try:
        row = conn.execute(
            """SELECT COUNT(*) AS checkouts, COALESCE(SUM(fee), 0) AS revenue
               FROM parking_logs
               WHERE status = 'OUT' AND DATE(time_out) = ?""",
            (today,),
        ).fetchone()
        return {
            "date":      today,
            "checkouts": row["checkouts"],
            "revenue":   row["revenue"],
        }
    finally:
        conn.close()


def get_recent_logs(limit: int = 20, db_path: str = DB_PATH) -> list[dict]:
    """Lấy N bản ghi gần nhất (cả IN lẫn OUT) cho bảng lịch sử."""
    conn = _get_connection(db_path)
    try:
        rows = conn.execute(
            """SELECT ticket_id, plate_number, time_in, time_out, status, fee
               FROM parking_logs
               ORDER BY ticket_id DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def set_max_capacity(new_capacity: int, db_path: str = DB_PATH) -> bool:
    """
    Cập nhật sức chứa tối đa (cho phép quản trị viên điều chỉnh qua UI).
    Trả về False nếu new_capacity nhỏ hơn số xe đang trong bãi.
    """
    if new_capacity < 1:
        return False
    conn = _get_connection(db_path)
    try:
        current = _count_vehicles_inside(conn)
        if new_capacity < current:
            log.warning(
                "Không thể giảm capacity xuống %d — hiện có %d xe trong bãi.",
                new_capacity, current,
            )
            return False
        conn.execute(
            "INSERT OR REPLACE INTO parking_config (key, value) VALUES ('max_capacity', ?)",
            (str(new_capacity),),
        )
        conn.commit()
        log.info("Đã cập nhật MAX_CAPACITY = %d", new_capacity)
        return True
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# TIỆN ÍCH NỘI BỘ
# ---------------------------------------------------------------------------

def _error_result(plate_number: str, message: str, code: str = "ERROR") -> dict:
    return {
        "status":       code,
        "plate_number": plate_number,
        "message":      message,
        "time":         datetime.datetime.now().strftime("%H:%M:%S"),
        "fee":          0,
        "ticket_id":    None,
    }


# ---------------------------------------------------------------------------
# CHẠY TRỰC TIẾP — kiểm tra nhanh khi debug
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    print("=" * 60)
    print("Khởi tạo database …")
    conn = init_db()
    conn.close()

    print("\n--- Kiểm tra Check-in ---")
    r = process_vehicle("51G-12345")
    print(json.dumps(r, ensure_ascii=False, indent=2))

    print("\n--- Kiểm tra spam Check-in cùng biển ---")
    r = process_vehicle("51G-12345")
    print(json.dumps(r, ensure_ascii=False, indent=2))

    print("\n--- Kiểm tra Check-out ---")
    r = process_vehicle("51G-12345")
    print(json.dumps(r, ensure_ascii=False, indent=2))

    print("\n--- Trạng thái bãi ---")
    print(json.dumps(get_status(), ensure_ascii=False, indent=2))

    print("\n--- Doanh thu hôm nay ---")
    print(json.dumps(get_revenue_today(), ensure_ascii=False, indent=2))

    print("\n--- 5 bản ghi gần nhất ---")
    for rec in get_recent_logs(5):
        print(rec)