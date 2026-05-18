import streamlit as st
import datetime
import random

# streamlit run app.py

# -----------------------------------------------------------------------
# CẤU HÌNH TRANG
# -----------------------------------------------------------------------
st.set_page_config(
    page_title="Hệ thống Nhận diện Biển số xe",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------
# SESSION STATE – dữ liệu xe trong bãi + lịch sử
# -----------------------------------------------------------------------
if "parking_lot" not in st.session_state:
    st.session_state.parking_lot = [
        {"plate": "29A-111.11", "type": "Xe máy", "time_in": "08:00:15", "slot": "A01"},
        {"plate": "30K-999.99", "type": "Ô tô",   "time_in": "08:15:30", "slot": "B03"},
        {"plate": "15C-456.78", "type": "Xe máy", "time_in": "08:45:00", "slot": "A02"},
        {"plate": "51B-888.88", "type": "Ô tô",   "time_in": "09:10:22", "slot": "B01"},
    ]

if "history" not in st.session_state:
    st.session_state.history = [
        {"plate": "30A-123.45", "type": "Xe máy", "time_in": "07:15:02", "time_out": "09:15:02", "fee": "4.000đ"},
        {"plate": "51F-999.99", "type": "Ô tô",   "time_in": "08:20:45", "time_out": "10:20:45", "fee": "20.000đ"},
        {"plate": "29C-321.00", "type": "Xe máy", "time_in": "06:00:00", "time_out": "11:00:00", "fee": "10.000đ"},
    ]

if "last_scanned" not in st.session_state:
    st.session_state.last_scanned = None

now = datetime.datetime.now()

# -----------------------------------------------------------------------
# TIÊU ĐỀ
# -----------------------------------------------------------------------
st.markdown("<h1 style='text-align: center;'>Hệ thống nhận diện biển số xe</h1>", unsafe_allow_html=True)
st.write("<p style='text-align: center;'>Đồ án Python - Hệ thống quản lý bãi gửi xe</p>", unsafe_allow_html=True)
st.divider()

# -----------------------------------------------------------------------
# STAT CARDS – 3 thẻ (bỏ tỷ lệ lấp đầy)
# -----------------------------------------------------------------------
lot = st.session_state.parking_lot
n_motorbike = sum(1 for c in lot if c["type"] == "Xe máy")
n_car       = sum(1 for c in lot if c["type"] == "Ô tô")
capacity    = 30

s1, s2, s3 = st.columns(3)
s1.metric("🚗 Xe đang trong bãi", len(lot), f"Còn trống {capacity - len(lot)} chỗ")
s2.metric("🛵 Xe máy", n_motorbike)
s3.metric("🚙 Ô tô", n_car)

st.divider()

# -----------------------------------------------------------------------
# BỐ CỤC CHÍNH: 3 CỘT
# -----------------------------------------------------------------------
col_left, col_center, col_right = st.columns([1, 2, 1], gap="medium")

# ══════════════════════════════════════════════════════════════════════
# CỘT TRÁI
# ══════════════════════════════════════════════════════════════════════
with col_left:
    # ── Danh sách xe hiện tại ──────────────────────────────────────
    st.subheader("Danh sách xe trong bãi")
    search_in = st.text_input("Tìm xe trong bãi (nhập biển số):", key="search_in")

    filtered = [c for c in lot if search_in.upper() in c["plate"].upper()] if search_in else lot

    if not filtered:
        st.caption("Không tìm thấy xe.")
    for car in filtered:
        st.info(f"**{car['plate']}** – {car['type']}\nVào lúc: {car['time_in']} | Slot: {car['slot']}")

    st.divider()

    # ── Lịch sử hệ thống ──────────────────────────────────────────
    st.subheader("Lịch sử hệ thống")
    search_hist = st.text_input("Tìm lịch sử (nhập biển số):", key="search_hist")
    selected_date = st.date_input("Chọn ngày:", datetime.date.today())

    t1, t2 = st.columns(2)
    with t1:
        start_t = st.time_input("Từ:", datetime.time(0, 0))
    with t2:
        end_t = st.time_input("Đến:", datetime.time(23, 59))

    hist_filtered = [h for h in st.session_state.history
                     if search_hist.upper() in h["plate"].upper()] \
                    if search_hist else st.session_state.history

    if not hist_filtered:
        st.caption("Không có dữ liệu.")
    for h in hist_filtered:
        st.success(
            f"**{h['plate']}** – {h['type']}\n"
            f"Vào: {h['time_in']} | Ra: {h['time_out']} | Phí: {h['fee']}"
        )

# ══════════════════════════════════════════════════════════════════════
# CỘT GIỮA – CAMERA & NHẬP THỦ CÔNG
# ══════════════════════════════════════════════════════════════════════
with col_center:
    st.subheader("Màn hình nhận diện")
    img_buffer = st.camera_input("Quét biển số xe")

    if img_buffer:
        # Giả lập nhận diện (thực tế gọi model OCR)
        fake_plates = ["29A-111.11", "30K-999.99", "51G-777.77", "43B-654.32"]
        detected = random.choice(fake_plates)
        st.session_state.last_scanned = detected
        st.success(f"✅ Nhận diện thành công: **{detected}**")
    else:
        st.warning("Đang đợi dữ liệu từ camera...")

    st.divider()

    # ── Nhập thủ công / Xác nhận ──────────────────────────────────
    st.subheader("Nhập thủ công / Xác nhận")

    manual_plate = st.text_input(
        "Biển số xe:",
        value=st.session_state.last_scanned or "",
        placeholder="VD: 29A-123.45",
        key="manual_plate"
    )

    vehicle_type = st.selectbox("Loại xe:", ["Xe máy", "Ô tô"], key="vtype")

    btn1, btn2 = st.columns(2)
    with btn1:
        if st.button("🟢 XE VÀO", use_container_width=True):
            if manual_plate.strip():
                if manual_plate.strip().upper() in [c["plate"].upper() for c in st.session_state.parking_lot]:
                    st.error("Xe đã có trong bãi!")
                else:
                    new_slot = f"{random.choice('ABCD')}{random.randint(1, 9):02d}"
                    st.session_state.parking_lot.append({
                        "plate":   manual_plate.strip().upper(),
                        "type":    vehicle_type,
                        "time_in": now.strftime("%H:%M:%S"),
                        "slot":    new_slot,
                    })
                    st.success(f"Đã ghi nhận vào bãi – Slot: **{new_slot}**")
                    st.rerun()
            else:
                st.warning("Vui lòng nhập biển số!")

    with btn2:
        if st.button("🔴 XE RA", use_container_width=True):
            if manual_plate.strip():
                found = next((c for c in st.session_state.parking_lot
                              if c["plate"].upper() == manual_plate.strip().upper()), None)
                if found:
                    try:
                        h_in  = int(found["time_in"].split(":")[0])
                        hours = max(1, now.hour - h_in)
                    except Exception:
                        hours = 1
                    rate = 2000 if found["type"] == "Xe máy" else 5000
                    fee  = hours * rate

                    st.session_state.parking_lot.remove(found)
                    st.session_state.history.insert(0, {
                        "plate":    found["plate"],
                        "type":     found["type"],
                        "time_in":  found["time_in"],
                        "time_out": now.strftime("%H:%M:%S"),
                        "fee":      f"{fee:,}đ",
                    })
                    st.success(f"Xe ra bãi ✓ | Phí: **{fee:,}đ** ({hours}h)")
                    st.rerun()
                else:
                    st.error("Không tìm thấy xe trong bãi!")
            else:
                st.warning("Vui lòng nhập biển số!")

# ══════════════════════════════════════════════════════════════════════
# CỘT PHẢI – THÔNG TIN CHI TIẾT
# ══════════════════════════════════════════════════════════════════════
with col_right:
    st.subheader("Thông tin chi tiết")

    # Đồng hồ
    st.write("**Thời gian hệ thống:**")
    st.code(now.strftime("%H:%M:%S\n%d/%m/%Y"), language="text")

    st.divider()

    # Biển số vừa quét
    st.write("**Biển số vừa quét:**")
    plate_display = st.session_state.last_scanned or "-- --- --"
    st.code(plate_display, language="text")

    # Tra cứu chi tiết xe
    st.write("**Đối chiếu thời gian:**")
    if st.session_state.last_scanned:
        found_car = next((c for c in st.session_state.parking_lot
                          if c["plate"].upper() == st.session_state.last_scanned.upper()), None)
        if found_car:
            try:
                h_in  = int(found_car["time_in"].split(":")[0])
                hours = max(1, now.hour - h_in)
            except Exception:
                hours = 1
            rate = 2000 if found_car["type"] == "Xe máy" else 5000
            est  = hours * rate

            st.write(f"Ngày vào: {now.strftime('%d/%m/%Y')}")
            st.write(f"Giờ vào: {found_car['time_in']}")
            st.write(f"Loại xe: {found_car['type']}")
            st.write(f"Vị trí: {found_car['slot']}")
            st.write(f"Thời gian: ~{hours}h")
            st.write(f"Phí dự kiến: **{est:,}đ**")
        else:
            st.write("Ngày ra: --/--/----")
            st.write("Giờ ra: --:--:--")
            st.info("Xe không có trong bãi.")
    else:
        st.write("Đang đợi quét xe...")

    st.divider()
    st.caption("Ghi chú: Hệ thống tự động phân loại xe máy/ô tô và tính phí dựa trên thời gian thực tế.")