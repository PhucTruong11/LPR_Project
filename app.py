import streamlit as st
import datetime
import random 
import io

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
# CSS TỐI ƯU GIAO DIỆN
# -----------------------------------------------------------------------
st.markdown("""
<style>
.block-container { padding-top: 0.6rem !important; padding-bottom: 0.6rem !important; max-width: 100% !important; }
div[data-testid="stVerticalBlock"] > div { padding-bottom: 0rem !important; }

/* Đẩy tiêu đề xuống một chút để không bị che khuất bởi thanh công cụ Streamlit */
h1 { margin-top: 2rem !important; margin-bottom: 0.5rem !important; padding-top: 0 !important; text-align: center; }
h2, h3 { margin-top: 0 !important; margin-bottom: 0.2rem !important; padding-top: 0 !important; }

.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] { padding: 4px 10px; font-weight: bold; }
hr { margin: 0.4rem 0 !important; }
div[data-testid="stFormSubmitButton"] > button, .stButton > button { margin-top: 0rem !important; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------
# SESSION STATE
# -----------------------------------------------------------------------
if "parking_lot" not in st.session_state:
    st.session_state.parking_lot = [
        {"plate": "29A-111.11", "time_in": "08:00:15", "date_in": "21/05/2026", "slot": "A01"},
        {"plate": "30K-999.99", "time_in": "08:15:30", "date_in": "21/05/2026", "slot": "B03"},
        {"plate": "15C-456.78", "time_in": "08:45:00", "date_in": "21/05/2026", "slot": "A02"},
        {"plate": "51B-888.88", "time_in": "09:10:22", "date_in": "21/05/2026", "slot": "B01"},
    ]

if "history" not in st.session_state:
    st.session_state.history = [
        {"plate": "30A-123.45", "date_in": "21/05/2026", "time_in": "07:15:02",
         "date_out": "21/05/2026", "time_out": "09:15:02", "fee": "4.000đ"},
        {"plate": "51F-999.99", "date_in": "21/05/2026", "time_in": "08:20:45",
         "date_out": "21/05/2026", "time_out": "10:20:45", "fee": "20.000đ"},
        {"plate": "29C-321.00", "date_in": "21/05/2026", "time_in": "06:00:00",
         "date_out": "21/05/2026", "time_out": "11:00:00", "fee": "10.000đ"},
    ]

if "last_scanned"      not in st.session_state: st.session_state.last_scanned      = None
if "last_action"       not in st.session_state: st.session_state.last_action        = None
if "last_action_plate" not in st.session_state: st.session_state.last_action_plate  = ""
if "last_action_fee"   not in st.session_state: st.session_state.last_action_fee    = ""
if "last_action_slot"  not in st.session_state: st.session_state.last_action_slot   = ""
if "fee_per_hour"      not in st.session_state: st.session_state.fee_per_hour       = 2000
if "capacity"          not in st.session_state: st.session_state.capacity           = 30

# Tính toán dữ liệu chung
capacity = st.session_state.capacity
lot      = st.session_state.parking_lot

def parse_fee(fee_str):
    try:
        return int(fee_str.replace("đ", "").replace(".", "").replace(",", ""))
    except Exception:
        return 0

total_revenue = sum(parse_fee(h["fee"]) for h in st.session_state.history)

# -----------------------------------------------------------------------
# TIÊU ĐỀ CHÍNH
# -----------------------------------------------------------------------
st.markdown("<h1>Hệ thống bãi đỗ xe</h1>", unsafe_allow_html=True)
st.divider()

# -----------------------------------------------------------------------
# BỐ CỤC CHÍNH (Khoảng cách cột rộng rãi: gap="large")
# -----------------------------------------------------------------------
col_left, col_center, col_right = st.columns([1.2, 1.6, 1.2], gap="large")

# ══════════════════════════════════════════════════════════════════════
# CỘT TRÁI – TAB: XE TRONG BÃI & LỊCH SỬ HỆ THỐNG
# ══════════════════════════════════════════════════════════════════════
with col_left:
    tab_current, tab_hist = st.tabs([f"Xe trong bãi ({len(lot)})", "Lịch sử hệ thống"])
    
    # --- TAB 1: XE ĐANG TRONG BÃI ---
    with tab_current:
        search_in = st.text_input("Tìm xe:", placeholder="Nhập biển số...", key="search_in", label_visibility="collapsed")
        filtered = [c for c in lot if search_in.upper() in c["plate"].upper()] if search_in else lot
        
        with st.container(height=490, border=True):
            if not filtered:
                st.caption("Không tìm thấy xe.")
            else:
                for car in filtered:
                    st.info(f"**{car['plate']}** \n\n Giờ vào: {car['time_in']} | Vị trí: **{car['slot']}**")

    # --- TAB 2: LỊCH SỬ HỆ THỐNG KÈM ĐẦY ĐỦ BỘ LỌC NGÀY GIỜ ---
    with tab_hist:
        search_hist = st.text_input("Tìm lịch sử:", placeholder="Nhập biển số...", key="search_hist", label_visibility="collapsed")
        
        selected_date = st.date_input("Chọn ngày:", datetime.date.today())
        t1, t2 = st.columns(2)
        with t1:
            start_t = st.time_input("Từ:", datetime.time(0, 0))
        with t2:
            end_t   = st.time_input("Đến:", datetime.time(23, 59))
            
        hist_filtered = [h for h in st.session_state.history if search_hist.upper() in h["plate"].upper()] if search_hist else st.session_state.history
        
        with st.container(height=240, border=True):
            if not hist_filtered:
                st.caption("Không có dữ liệu.")
            else:
                for h in hist_filtered:
                    st.success(
                        f"**{h['plate']}** \n\n"
                        f"Vào: {h['date_in']} {h['time_in']} \n\n"
                        f"Ra:  {h['date_out']} {h['time_out']} \n\n"
                        f"Phí: **{h['fee']}**"
                    )

# ══════════════════════════════════════════════════════════════════════
# CỘT GIỮA – MÀN HÌNH CAMERA NHẬN DIỆN VÀ THAO TÁC ĐIỀU KHIỂN
# ══════════════════════════════════════════════════════════════════════
with col_center:
    st.markdown("<p style='font-weight:bold; margin:0;'>Màn hình nhận diện</p>", unsafe_allow_html=True)
    img_buffer = st.camera_input("Quét biển số xe", label_visibility="collapsed")

    if img_buffer:
        fake_plates = ["29A-111.11", "30K-999.99", "51G-777.77", "43B-654.32"]
        detected = random.choice(fake_plates)
        st.session_state.last_scanned = detected
    
    st.markdown("<p style='font-weight:bold; margin-top:0.4rem; margin-bottom:0;'>Nhập thủ công / Xác nhận</p>", unsafe_allow_html=True)
    manual_plate = st.text_input(
        "Biển số xe:",
        value=st.session_state.last_scanned or "",
        placeholder="VD: 29A-123.45",
        key="manual_plate",
        label_visibility="collapsed"
    )

    # Đồng bộ hiển thị: Khi người dùng nhập tay, vùng hiển thị "Biển số xe" ở cột phải cũng cập nhật theo
    if manual_plate:
        st.session_state.last_scanned = manual_plate.strip().upper()

    now = datetime.datetime.now()
    btn1, btn2 = st.columns(2)

    with btn1:
        if st.button("XE VÀO", use_container_width=True, type="primary"):
            plate = manual_plate.strip().upper()
            if not plate:
                st.warning("Vui lòng nhập biển số!")
            elif plate in [c["plate"].upper() for c in lot]:
                st.error("Xe đã có trong bãi!")
            elif len(lot) >= capacity:
                st.error("Bãi đã đầy!")
            else:
                new_slot = f"{random.choice('ABCD')}{random.randint(1,9):02d}"
                st.session_state.parking_lot.append({
                    "plate": plate, "time_in": now.strftime("%H:%M:%S"),
                    "date_in": now.strftime("%d/%m/%Y"), "slot": new_slot,
                })
                st.session_state.last_action, st.session_state.last_action_plate, st.session_state.last_action_slot, st.session_state.last_action_fee = "in", plate, new_slot, ""
                st.rerun()

    with btn2:
        if st.button("XE RA", use_container_width=True):
            plate = manual_plate.strip().upper()
            if not plate:
                st.warning("Vui lòng nhập biển số!")
            else:
                found = next((c for c in lot if c["plate"].upper() == plate), None)
                if not found:
                    st.error("Không tìm thấy xe trong bãi!")
                else:
                    try: hours = max(1, now.hour - int(found["time_in"].split(":")[0]))
                    except: hours = 1
                    fee = hours * st.session_state.fee_per_hour
                    st.session_state.parking_lot.remove(found)
                    record = {
                        "plate": found["plate"], "date_in": found["date_in"], "time_in": found["time_in"],
                        "date_out": now.strftime("%d/%m/%Y"), "time_out": now.strftime("%H:%M:%S"), "fee": f"{fee:,}đ",
                    }
                    st.session_state.history.insert(0, record)
                    st.session_state.last_action, st.session_state.last_action_plate, st.session_state.last_action_fee, st.session_state.last_action_slot, st.session_state.last_out_info = "out", found["plate"], f"{fee:,}đ", found["slot"], record
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════
# CỘT PHẢI – CHỖ TRỐNG TINH GỌN, ĐỐI CHIẾU CỐ ĐỊNH & CÀI ĐẶT ẨN
# ══════════════════════════════════════════════════════════════════════
with col_right:
    # ── 1. TRẠNG THÁI CHỖ TRỐNG TINH GỌN ──
    free_slots = capacity - len(lot)
    st.markdown(f"Chỗ còn trống: **{free_slots} / {capacity}**")
    st.progress(len(lot) / capacity)
    
    st.divider()
    st.subheader("Thông tin chi tiết")

    # Thông báo trạng thái hành động vừa click
    action = st.session_state.last_action
    if action == "in": st.success("XE VÀO THÀNH CÔNG")
    elif action == "out": st.error("XE RA THÀNH CÔNG")
    else: st.info("Đang chờ quét xe...")

    # ── 2. BIỂN SỐ XE (Hiển thị đồng bộ khi quét hoặc nhập tay) ──
    st.write("**Biển số xe:**")
    st.code(st.session_state.last_scanned or "-- --- --", language="text")

    # ── 3. KHUNG ĐỐI CHIẾU THỜI GIAN CỐ ĐỊNH ──
    st.write("**Đối chiếu thời gian:**")
    
    # Thiết lập giá trị mặc định liên tục xuất hiện trên form
    p_date_in, p_time_in, p_date_out, p_time_out, p_fee = "--/--/----", "--:--:--", "--/--/----", "--:--:--", "0đ"
    
    if action == "in" and st.session_state.last_action_plate:
        found_car = next((c for c in lot if c["plate"].upper() == st.session_state.last_action_plate.upper()), None)
        if found_car:
            p_date_in  = found_car['date_in']
            p_time_in  = found_car['time_in']
            p_fee      = "Xe đang trong bãi"
            
    elif action == "out" and st.session_state.last_action_plate:
        info = st.session_state.get("last_out_info", {})
        if info:
            p_date_in  = info['date_in']
            p_time_in  = info['time_in']
            p_date_out = info['date_out']
            p_time_out = info['time_out']
            p_fee      = info['fee']

    # Hiển thị biểu mẫu thông tin thời gian cố định (Đã bỏ dòng hiển thị biển số lặp ở đây)
    st.write(f"Ngày vào: {p_date_in}")
    st.write(f"Giờ vào:  {p_time_in}")
    st.write(f"Ngày ra:  {p_date_out}")
    st.write(f"Giờ ra:   {p_time_out}")
    st.write(f"Phí gửi:  **{p_fee}**")

    st.divider()

    # ── 4. CÀI ĐẶT HỆ THỐNG DẠNG ẨN ──
    with st.popover("Cài đặt hệ thống", use_container_width=True):
        st.markdown("**Cấu hình thông số bãi xe**")
        new_capacity = st.number_input("Sức chứa tối đa (chỗ):", min_value=1, max_value=500, value=st.session_state.capacity, step=1)
        new_fee = st.number_input("Giá gửi xe (đ/giờ):", min_value=500, max_value=100000, value=st.session_state.fee_per_hour, step=500)
        if st.button("Lưu cấu hình", use_container_width=True):
            st.session_state.capacity = new_capacity
            st.session_state.fee_per_hour = new_fee
            st.toast("Đã lưu cài đặt!")
            st.rerun()