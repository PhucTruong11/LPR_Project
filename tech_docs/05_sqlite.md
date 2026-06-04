# SQLite3 — Cơ sở Dữ liệu & Lưu trữ Giao dịch Bãi xe An toàn, Hiệu năng cao

## 1. Giới thiệu tổng quan và Cơ sở lý thuyết Hệ quản trị Cơ sở dữ liệu

### 1.1. Kiến trúc Serverless đặc thù của SQLite
**SQLite** là một thư viện phần mềm triển khai một hệ quản trị cơ sở dữ liệu quan hệ (RDBMS) nhúng, gọn nhẹ, tự vận hành (self-contained) và giao dịch hoàn toàn (transactional). 

Khác biệt cốt lõi giữa SQLite và các RDBMS truyền thống (như MySQL, PostgreSQL, Microsoft SQL Server):
* **Kiến trúc Client-Server:** Các hệ cơ sở dữ liệu lớn hoạt động như một tiến trình máy chủ độc lập. Ứng dụng khách (Client) phải gửi các truy vấn thông qua kết nối mạng (TCP/IP socket) đến Server để xử lý. Việc này tạo ra độ trễ mạng (network overhead) và yêu cầu cấu hình cài đặt phức tạp.
* **Kiến trúc Serverless (Không máy chủ):** SQLite không có tiến trình máy chủ chạy ngầm. Toàn bộ mã nguồn của SQLite được biên dịch trực tiếp vào ứng dụng Python. Dữ liệu được lưu trữ trong một file duy nhất trên đĩa cứng (`parking.db`). Việc đọc ghi dữ liệu được thực hiện thông qua các lệnh gọi hàm hệ thống trực tiếp lên file trên đĩa cứng, giúp tốc độ truy cập cực kỳ nhanh và loại bỏ hoàn toàn độ trễ mạng.

### 1.2. Tính toàn vẹn giao dịch (ACID)
Mặc dù nhỏ gọn, SQLite tuân thủ đầy đủ các thuộc tính **ACID** để đảm bảo an toàn dữ liệu tuyệt đối:
* **Atomicity (Tính nguyên tử):** Đảm bảo một giao dịch (transaction) được thực hiện trọn vẹn hoặc không thực hiện gì cả (Rollback nếu xảy ra lỗi giữa chừng).
* **Consistency (Tính nhất quán):** Dữ liệu luôn tuân thủ các ràng buộc schema (Constraint).
* **Isolation (Tính cô lập):** Các giao dịch chạy song song không nhìn thấy dữ liệu trung gian của nhau cho đến khi được Commit.
* **Durability (Tính bền vững):** Dữ liệu đã được Commit sẽ được lưu trữ vĩnh viễn trên đĩa cứng ngay cả khi mất điện đột ngột.

---

## 2. Thiết kế Lược đồ Cơ sở dữ liệu chi tiết (Detailed Database Schema)

Hệ thống thiết kế hai bảng chính phục vụ việc quản lý logic gửi xe và chia sẻ trạng thái liên tiến trình:

```
            ┌──────────────────────────────────────────────┐
            │                 parking_logs                 │
            ├──────────────────────────────────────────────┤
            │ ticket_id     : INTEGER PRIMARY KEY AUTOINC  │
            │ plate_number  : TEXT NOT NULL                │
            │ time_in       : TEXT NOT NULL                │
            │ time_out      : TEXT NULL                    │
            │ status        : TEXT NOT NULL (IN/OUT)       │
            │ fee           : REAL NOT NULL DEFAULT 0.0    │
            └──────────────────────┬───────────────────────┘
                                   │
                                   │ index
                                   ▼
            ┌──────────────────────────────────────────────┐
            │              idx_plate_status                │
            │        ON (plate_number, status)             │
            └──────────────────────────────────────────────┘
```

### 2.1. Bảng `parking_logs` (Nhật ký giao dịch xe)
Lưu trữ thông tin chi tiết từng lượt xe ra vào bãi để quản lý và tính phí:

```sql
CREATE TABLE IF NOT EXISTS parking_logs (
    ticket_id    INTEGER PRIMARY KEY AUTOINCREMENT, -- Khóa chính tự tăng
    plate_number TEXT    NOT NULL,                  -- Biển số xe đã chuẩn hóa
    time_in      TEXT    NOT NULL,                  -- Thời gian xe vào (ISO-8601)
    time_out     TEXT,                              -- Thời gian xe ra (Null khi xe đang trong bãi)
    status       TEXT    NOT NULL                   -- Trạng thái hiện tại
                     CHECK(status IN ('IN', 'OUT')), -- Ràng buộc cứng: chỉ nhận giá trị 'IN' hoặc 'OUT'
    fee          REAL    NOT NULL DEFAULT 0.0       -- Phí gửi xe
                     CHECK(fee >= 0)                -- Đảm bảo phí không bao giờ âm
);
```

### 2.2. Bảng `parking_config` (Cấu hình và trạng thái chia sẻ)
Lưu trữ cấu hình tĩnh của bãi xe và hoạt động như một Message Queue chia sẻ biển số quét từ camera sang cho Web Streamlit:

```sql
CREATE TABLE IF NOT EXISTS parking_config (
    key   TEXT PRIMARY KEY,  -- Khóa cấu hình (ví dụ: 'max_capacity', 'last_detected_plate')
    value TEXT NOT NULL      -- Giá trị tương ứng dạng chuỗi
);
```

---

## 3. Các kỹ thuật Tối ưu hóa Hiệu năng nâng cao

Vì hệ thống vận hành theo kiến trúc song song (tiến trình camera liên tục quét và ghi biển số quét tạm thời vào DB; cùng lúc đó tiến trình web Streamlit liên tục đọc dữ liệu cấu hình và doanh thu từ DB), việc tối ưu hóa SQLite để tránh xung đột ghi/đọc là điều bắt buộc.

### 3.1. Kích hoạt Chế độ WAL (Write-Ahead Logging)
Mặc định, SQLite sử dụng chế độ khóa cơ sở dữ liệu truyền thống (Rollback Journal): Khi một tiến trình đang ghi dữ liệu (Write), toàn bộ file cơ sở dữ liệu sẽ bị khóa lại, khiến các tiến trình khác không thể đọc (Read) hay ghi dữ liệu, gây ra lỗi nghiêm trọng `database is locked`.

Dự án giải quyết triệt để lỗi này bằng cách kích hoạt chế độ **WAL Mode**:
```sql
PRAGMA journal_mode=WAL;
```
* **Cơ chế hoạt động:** Ở chế độ WAL, các thay đổi ghi dữ liệu mới không ghi đè trực tiếp lên file cơ sở dữ liệu gốc (`parking.db`). Thay vào đó, chúng được ghi nối tiếp vào một file nhật ký phụ riêng biệt gọi là file **WAL** (`parking.db-wal`).
* **Không chặn lẫn nhau (Non-blocking Reads/Writes):** Nhờ có file WAL, tiến trình đọc dữ liệu (Dashboard Streamlit) có thể đọc dữ liệu trực tiếp từ file gốc tại thời điểm ổn định gần nhất mà không bị cản trở bởi tiến trình ghi (Camera). Đồng thời, tiến trình ghi vẫn có thể ghi tiếp các bản ghi mới vào file WAL. 
* **Cơ chế Checkpoint:** Định kỳ, SQLite sẽ tự động gộp các thay đổi từ file WAL quay trở lại file gốc (`parking.db`) khi không có tiến trình đọc nào hoạt động, giúp giữ cho kích thước file WAL luôn ở mức nhỏ.

### 3.2. Tối ưu hóa truy vấn bằng Chỉ mục kép (Composite Index)
Khi một xe đi ra khỏi bãi, hệ thống cần đối soát cực nhanh để tìm xem xe này có đang ở trong bãi hay không (`status = 'IN'`) nhằm tính toán thời gian gửi xe. Nếu không có chỉ mục, SQLite sẽ phải quét tuần tự từ đầu đến cuối bảng (Table Scan - độ phức tạp thuật toán là $O(N)$):
```sql
SELECT ticket_id, time_in FROM parking_logs 
WHERE plate_number = ? AND status = 'IN' LIMIT 1;
```
Để tối ưu hóa, hệ thống tạo chỉ mục kép:
```sql
CREATE INDEX IF NOT EXISTS idx_plate_status ON parking_logs (plate_number, status);
```
* **Cơ chế hoạt động:** SQLite xây dựng một cấu trúc cây **B-Tree** dựa trên giá trị kết hợp của hai trường `plate_number` và `status`.
* **Hiệu quả:** Thay vì quét toàn bộ bảng, SQLite thực hiện tìm kiếm nhị phân trên cây B-Tree với độ phức tạp thuật toán giảm xuống còn $O(\log N)$. Thời gian phản hồi đối soát xe giảm từ hàng chục mili-giây xuống dưới **0.1 mili-giây**, đảm bảo hệ thống chạy mượt mà ngay cả khi bãi giữ xe lưu trữ hàng triệu lượt xe lịch sử.

### 3.3. Thiết kế Kết nối an toàn đa luồng (Thread-local Connection)
SQLite mặc định không cho phép chia sẻ chung một đối tượng kết nối `sqlite3.Connection` giữa nhiều luồng (thread) khác nhau vì sẽ gây ra lỗi tranh chấp con trỏ (Race Condition).
Dự án thiết kế một giải pháp thông minh:
* **Thread-local Storage (`threading.local`):** Tạo một vùng nhớ lưu trữ kết nối SQLite riêng cho từng luồng hoạt động. Mỗi luồng khi gọi hàm kết nối sẽ tự động nhận về một kết nối độc lập được duy trì dài hạn trong luồng đó:
  ```python
  _local_db = threading.local()
  ```
* **Wrapper chống đóng sớm (`SQLiteConnectionWrapper`):** Định nghĩa một lớp bọc kết nối để biến hàm `close()` thành rỗng (no-op). Kỹ thuật này giúp giữ cho các kết nối Thread-local luôn mở để tái sử dụng nhiều lần mà không mất chi phí đóng/mở file liên tục, tăng hiệu năng ghi dữ liệu lên gấp nhiều lần.
