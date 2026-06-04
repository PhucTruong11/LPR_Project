# Streamlit — Giao diện Dashboard Giám sát và Điều khiển Bãi xe

## 1. Giới thiệu tổng quan và Cơ sở lý thuyết

### 1.1. Streamlit là gì?
**Streamlit** là một framework mã nguồn mở viết bằng Python, được thiết kế để giúp các kỹ sư dữ liệu và nhà phát triển học máy xây dựng nhanh các ứng dụng web tương tác trực quan mà không cần có kiến thức sâu về phát triển Front-end (như HTML, CSS, JavaScript, React, hay Vue). 

### 1.2. So sánh Streamlit với các Web Framework truyền thống
Trong phát triển web truyền thống (như Django, Flask kết hợp với React/Bootstrap):
* **Kiến trúc MVC/MVVM:** Cần định nghĩa rõ ràng các Router, REST API, quản lý State ở cả phía Client và Server, xây dựng giao diện kéo thả hoặc code CSS phức tạp.
* **Thời gian phát triển:** Tốn nhiều thời gian và đòi hỏi kỹ năng chuyên môn ở cả Front-end lẫn Back-end.

Đối với **Streamlit**:
* **Mô hình lập trình phản xạ (Reactive Programming Paradigm):** Streamlit hoạt động trên nguyên lý chạy lại toàn bộ script Python từ đầu đến cuối mỗi khi người dùng tương tác với một phần tử trên giao diện (ví dụ: bấm nút, kéo thanh trượt, nhập văn bản).
* **Quản lý trạng thái tự động:** Nhờ có đối tượng `st.session_state`, Streamlit cho phép lưu trữ và duy trì các biến trạng thái giữa các lần chạy lại (re-run) của mã nguồn.
* **Đơn giản hóa giao diện:** Giao diện được mô tả trực tiếp bằng mã nguồn Python ngắn gọn (ví dụ: `st.button`, `st.write`, `st.metric`) và tự động render sang định dạng giao diện React hiện đại ở phía trình duyệt khách.

---

## 2. Vai trò và Kiến trúc chức năng trong hệ thống LPR Smart Parking

Trong hệ thống **LPR Smart Parking**, Streamlit không chỉ là một trang web hiển thị dữ liệu tĩnh mà đóng vai trò là **Hệ thống Giám sát & Điều khiển Trung tâm (Central Monitoring & Control Center)**:

```
                  ┌─────────────────────────────────────────┐
                  │          STREAMLIT WEB ENGINE           │
                  └──────┬──────────────────────────▲───────┘
                         │ Đọc/Ghi trạng thái       │ Đọc dữ liệu giao dịch
                         │ & Biển số quét ngầm      │ & Doanh thu
                         ▼                          │
                  ┌─────────────────────────────────┴───────┐
                  │           SQLITE DATABASE (parking.db)  │
                  └─────────────────────────────────────────┘
```

### 2.1. Quản lý trạng thái bãi đỗ thời gian thực (Real-time Monitoring)
* **Số xe trong bãi (Occupancy):** Hiển thị số xe hiện tại đang gửi (`status = 'IN'`) dưới dạng một thẻ chỉ số lớn (Metric card) kèm theo màu sắc cảnh báo nếu bãi gần đầy.
* **Sức chứa giới hạn:** Hiển thị công suất hoạt động dưới dạng thanh tiến trình (Progress bar) trực quan, cho biết bãi đỗ còn lại bao nhiêu phần trăm dung lượng trống.
* **Tình trạng bãi đỗ:** Tự động khóa chức năng Check-in trên web hoặc cảnh báo đến nhân viên nếu số lượng xe đạt đến sức chứa tối đa (`MAX_CAPACITY`).

### 2.2. Hỗ trợ quy trình vận hành Semi-manual (Bán tự động)
Quy trình bán tự động là giải pháp tối ưu cho các bãi giữ xe thực tế để tránh sai sót của AI (như camera mờ, biển số bẩn làm chữ bị đọc sai):
1. Tiến trình quét camera ngầm (`live_test.py`) tự động cập nhật biển số xe nhận diện được vào bảng cấu hình tạm `parking_config`.
2. Giao diện Streamlit liên tục đọc bảng này. Khi phát hiện có biển số mới nằm trong danh sách chờ:
   * Streamlit tự động điền (Auto-fill) biển số vào ô nhập liệu trên Form.
   * Hiển thị cảnh báo trực quan cho nhân viên đối chiếu với hình ảnh thực tế.
   * Cung cấp hai nút bấm hành động tức thì: **Xác nhận Xe Vào/Ra** hoặc **Bỏ qua (Xóa hàng đợi)**.
3. Nhân viên kiểm tra và bấm xác nhận $\rightarrow$ Hệ thống thực hiện ghi giao dịch chính thức vào bảng `parking_logs`.

### 2.3. Báo cáo tài chính và Lịch sử giao dịch
* **Dashboard Doanh thu:** Tính toán tổng số tiền phí thu được trong ngày hiện tại (`DATE(time_out) = TODAY`).
* **Thống kê lưu lượng:** Đếm tổng số lượt xe ra và xe vào trong ngày để đánh giá hiệu suất khai thác của bãi xe.
* **Bảng lịch sử động:** Sử dụng cấu trúc bảng của Streamlit để hiển thị danh sách 50 bản ghi gần nhất có phân biệt màu sắc trạng thái (Xanh lá đối với xe đã ra - `OUT`, Vàng cam đối với xe đang trong bãi - `IN`).

---

## 3. Cách thức hoạt động chi tiết trong Mã nguồn

### 3.1. Vòng lặp tự động làm mới giao diện (Auto-refresh/Polling Loop)
Do bản chất của Streamlit là chỉ chạy lại script khi người dùng tương tác, để hệ thống có thể cập nhật thông tin biển số từ camera thời gian thực mà không cần nhân viên bấm F5, mã nguồn sử dụng cơ chế **Auto-refresh**:
* Cấu hình tham số `AUTO_REFRESH_SEC` trong `config.py` (mặc định là 5 giây).
* Streamlit sử dụng một thư viện hỗ trợ hoặc cơ chế đúp loop (hoặc component `streamlit-autorefresh`) để định kỳ kích hoạt sự kiện chạy lại toàn bộ trang web.
* Cứ mỗi chu kỳ quét:
  ```python
  # Đọc biển số xe mới phát hiện từ DB tạm
  detected_plate = db.get_detected_plate()
  if detected_plate:
      # Cập nhật vào st.session_state để hiển thị lên Form nhập liệu
      st.session_state.plate_input = detected_plate
  ```

### 3.2. Quản lý trạng thái bằng `st.session_state`
Để giữ cho dữ liệu nhập tay của nhân viên không bị mất hoặc ghi đè khi trang web tự động refresh sau mỗi 5 giây, hệ thống áp dụng kỹ thuật tách biệt trạng thái:
* Trạng thái nhập liệu (`st.session_state.plate_input`) chỉ được cập nhật tự động khi phát hiện có sự thay đổi thực sự của biển số quét từ camera (sử dụng một biến so sánh phụ lưu biển số cũ).
* Nếu nhân viên đang chỉnh sửa biển số bị sai bằng bàn phím, cơ chế tự refresh sẽ tạm thời dừng cập nhật hoặc ưu tiên giữ lại chuỗi chữ do nhân viên đang nhập để đảm bảo trải nghiệm sử dụng không bị ngắt quãng.

### 3.3. Tách biệt Tiến trình để Tối ưu hóa hiệu năng
* Nếu tích hợp trực tiếp camera OpenCV chạy trong Streamlit, luồng xử lý ảnh màu và mô hình AI sẽ chiếm hoàn toàn tài nguyên CPU/GPU của tiến trình Web. Điều này khiến giao diện Web bị đơ cứng, giật lag dữ dội và không thể phản hồi các nút bấm của người dùng.
* Bằng cách tách biệt thành **2 tiến trình độc lập** giao tiếp qua cơ sở dữ liệu SQLite, tiến trình Web Streamlit chỉ tốn chưa tới 1% CPU để thực hiện các truy vấn SQL đơn giản, duy trì độ phản hồi tức thì (<10ms) cho các thao tác click chuột của nhân viên.
