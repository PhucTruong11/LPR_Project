import sqlite3
import datetime
import os
import logging

# ---------------------------------------------------------------------------
# CẤU HÌNH — tất cả thông số được đọc từ config.py (nguồn chân lý duy nhất)
# ---------------------------------------------------------------------------
try:
    from config import (
        DB_PATH,
        MAX_CAPACITY,
        PRICE_FLOOR,
        PRICE_HALF_HOUR,
        PRICE_PER_HOUR,
        PRICE_EXTRA_HALF,
        PRICE_EXTRA_FULL,
    )
except ImportError:
    # Fallback khi chạy database_manager.py trực tiếp ngoài thư mục modules/
    DB_PATH          = os.environ.get("PARKING_DB_PATH", "parking.db")
    MAX_CAPACITY     = 50
    PRICE_FLOOR      = 5_000
    PRICE_HALF_HOUR  = 8_000
    PRICE_PER_HOUR   = 10_000
    PRICE_EXTRA_HALF = 5_000
    PRICE_EXTRA_FULL = 8_000

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

import threading

class SQLiteConnectionWrapper:
    """
    Bọc sqlite3.Connection để biến hàm close() thành no-op (bỏ qua việc đóng),
    giúp giữ kết nối dài hạn và tái sử dụng an toàn mà không cần sửa code ở nơi gọi.
    """
    def __init__(self, conn):
        self._conn = conn

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def __enter__(self):
        return self._conn.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._conn.__exit__(exc_type, exc_val, exc_tb)

    def close(self):
        # Không làm gì cả để giữ kết nối dùng chung luôn mở
        pass

_local_db = threading.local()

def _get_connection(db_path: str = DB_PATH) -> SQLiteConnectionWrapper:
    """
    Tái sử dụng kết nối trong từng luồng (Thread-local connection) 
    và trả về đối tượng bọc để chống đóng kết nối sớm.
    """
    if not hasattr(_local_db, "conn") or _local_db.conn is None:
        try:
            # Mở kết nối SQLite dài hạn cho Thread này
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            _local_db.conn = conn
        except sqlite3.Error as e:
            log.error(f"[SQLite Connection] Không thể kết nối DB: {e}")
            raise e
            
    # Bọc kết nối lại để các hàm bên ngoài khi gọi conn.close() không thực sự đóng kết nối
    return SQLiteConnectionWrapper(_local_db.conn)


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
# SEMI-MANUAL MODE — Chia sẻ biển số detect được với Dashboard
# ---------------------------------------------------------------------------

def update_detected_plate(plate_number: str, db_path: str = DB_PATH) -> None:
    """
    Ghi biển số vừa được camera/OCR phát hiện vào bảng parking_config.
    Dashboard (app.py) đọc lại để hiển thị và chờ nhân viên xác nhận.

    Dùng trong Semi-manual mode: live_test.py gọi hàm này thay vì
    gọi trực tiếp process_vehicle().
    """
    plate_number = plate_number.strip().upper()
    conn = _get_connection(db_path)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO parking_config (key, value) VALUES ('last_detected_plate', ?)",
            (plate_number,),
        )
        conn.commit()
        log.info("Camera phát hiện biển số: %s", plate_number)
    finally:
        conn.close()


def get_detected_plate(db_path: str = DB_PATH) -> str:
    """
    Lấy biển số mới nhất mà camera phát hiện (chưa được nhân viên confirm).
    Trả về chuỗi rỗng nếu chưa có.
    """
    conn = _get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT value FROM parking_config WHERE key = 'last_detected_plate'"
        ).fetchone()
        return row["value"] if row else ""
    finally:
        conn.close()


def clear_detected_plate(db_path: str = DB_PATH) -> None:
    """Xóa biển số vừa detect sau khi nhân viên đã xử lý."""
    conn = _get_connection(db_path)
    try:
        conn.execute(
            "DELETE FROM parking_config WHERE key = 'last_detected_plate'"
        )
        conn.commit()
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