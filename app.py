import streamlit as st
import datetime
import sys
import os
import cv2
import numpy as np
from PIL import Image
# streamlit run app.py



# PATH SETUP — đảm bảo import được modules/
MODULES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules")
if MODULES_DIR not in sys.path:
    sys.path.insert(0, MODULES_DIR)

import modules.database_manager as db
from modules.config import AUTO_REFRESH_SEC, HISTORY_DISPLAY_LIMIT

from modules.detection import detect_license_plate
from modules.processing import process_plate
from modules.ocr_engine import PlateOCR


# CẤU HÌNH TRANG
st.set_page_config(
    page_title="Hệ thống Nhận diện Biển số xe",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS TỐI ƯU GIAO DIỆN
st.markdown("""
<style>
.block-container { padding-top: 0.6rem !important; padding-bottom: 0.6rem !important; max-width: 100% !important; }
div[data-testid="stVerticalBlock"] > div { padding-bottom: 0rem !important; }
h1 { margin-top: 2rem !important; margin-bottom: 0.5rem !important; padding-top: 0 !important; text-align: center; }
h2, h3 { margin-top: 0 !important; margin-bottom: 0.2rem !important; padding-top: 0 !important; }
.stTabs [data-baseweb="tab-list"] { gap: 4px; }
.stTabs [data-baseweb="tab"] { padding: 4px 10px; font-weight: bold; }
hr { margin: 0.4rem 0 !important; }
div[data-testid="stFormSubmitButton"] > button, .stButton > button { margin-top: 0rem !important; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_db_initialized():
    """Khởi tạo DB một lần duy nhất suốt vòng đời app."""
    conn = db.init_db()
    conn.close()
    return True

get_db_initialized()

@st.cache_resource
def get_ocr_engine():
    """Khởi tạo mô hình OCR một lần duy nhất."""
    return PlateOCR()

ocr_engine = get_ocr_engine()

# SESSION STATE
if "last_action"       not in st.session_state: st.session_state.last_action        = None
if "last_action_plate" not in st.session_state: st.session_state.last_action_plate  = ""
if "last_action_fee"   not in st.session_state: st.session_state.last_action_fee    = ""
if "last_action_slot"  not in st.session_state: st.session_state.last_action_slot   = ""
if "last_scanned"      not in st.session_state: st.session_state.last_scanned       = None
if "last_out_info"     not in st.session_state: st.session_state.last_out_info      = {}

# ĐỌC DỮ LIỆU THỰC TỪ DATABASE
status_data  = db.get_status()
recent_logs  = db.get_recent_logs(limit=HISTORY_DISPLAY_LIMIT)
revenue_data = db.get_revenue_today()

# SEMI-MANUAL: đọc biển số camera vừa phát hiện (nếu có)
camera_detected = db.get_detected_plate()

capacity    = status_data["max_capacity"]
occupancy   = status_data["occupancy"]
vehicles_in = status_data["vehicles_inside"]  # list[dict]: ticket_id, plate_number, time_in


def fmt_time(raw: str) -> str:
    """Lấy HH:MM:SS từ chuỗi ISO timestamp."""
    try:
        return raw[11:19]
    except Exception:
        return raw or "--:--:--"

def fmt_date(raw: str) -> str:
    """Lấy dd/mm/yyyy từ chuỗi ISO timestamp."""
    try:
        dt = datetime.datetime.fromisoformat(raw)
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return raw or "--/--/----"


st.markdown("<h1>Hệ thống bãi đỗ xe</h1>", unsafe_allow_html=True)
st.divider()

# BỐ CỤC CHÍNH
col_left, col_center, col_right = st.columns([1.2, 1.6, 1.2], gap="large")

# CỘT TRÁI – XE TRONG BÃI & LỊCH SỬ
with col_left:
    tab_current, tab_hist = st.tabs([f"Xe trong bãi ({occupancy})", "Lịch sử hệ thống"])

    # --- TAB 1: XE ĐANG TRONG BÃI ---
    with tab_current:
        search_in = st.text_input("Tìm xe:", placeholder="Nhập biển số...", key="search_in", label_visibility="collapsed")
        filtered = [
            v for v in vehicles_in
            if search_in.upper() in v["plate_number"].upper()
        ] if search_in else vehicles_in

        with st.container(height=490, border=True):
            if not filtered:
                st.caption("Không tìm thấy xe." if search_in else "Bãi đang trống.")
            else:
                for v in filtered:
                    st.info(
                        f"**{v['plate_number']}**\n\n"
                        f"Vào: {fmt_date(v['time_in'])} {fmt_time(v['time_in'])} | Vé: **#{v['ticket_id']}**"
                    )

    # --- TAB 2: LỊCH SỬ ---
    with tab_hist:
        search_hist = st.text_input("Tìm lịch sử:", placeholder="Nhập biển số...", key="search_hist", label_visibility="collapsed")
        selected_date = st.date_input("Chọn ngày:", datetime.date.today())
        t1, t2 = st.columns(2)
        with t1:
            start_t = st.time_input("Từ:", datetime.time(0, 0))
        with t2:
            end_t   = st.time_input("Đến:", datetime.time(23, 59))

        hist_filtered = [
            h for h in recent_logs
            if search_hist.upper() in h["plate_number"].upper()
        ] if search_hist else recent_logs

        with st.container(height=240, border=True):
            if not hist_filtered:
                st.caption("Không có dữ liệu.")
            else:
                for h in hist_filtered:
                    time_out_disp = fmt_time(h["time_out"]) if h.get("time_out") else "--:--:--"
                    date_out_disp = fmt_date(h["time_out"]) if h.get("time_out") else "--/--/----"
                    fee_disp      = f"{h['fee']:,.0f}đ" if h.get("status") == "OUT" else "Đang trong bãi"

                    if h.get("status") == "OUT":
                        st.success(
                            f"**{h['plate_number']}** (Vé #{h['ticket_id']})\n\n"
                            f"Vào: {fmt_date(h['time_in'])} {fmt_time(h['time_in'])}\n\n"
                            f"Ra:  {date_out_disp} {time_out_disp}\n\n"
                            f"Phí: **{fee_disp}**"
                        )
                    else:
                        st.info(
                            f"**{h['plate_number']}** (Vé #{h['ticket_id']})\n\n"
                            f"Vào: {fmt_date(h['time_in'])} {fmt_time(h['time_in'])}\n\n"
                            f"Phí: **{fee_disp}**"
                        )

# CỘT GIỮA – CAMERA & ĐIỀU KHIỂN (SEMI-MANUAL)
with col_center:
    st.markdown("<p style='font-weight:bold; margin:0;'>Màn hình nhận diện</p>", unsafe_allow_html=True)
    img_buffer = st.camera_input("Quét biển số xe", label_visibility="collapsed")

    # Khi chụp ảnh qua camera trình duyệt → OCR một lần
    if img_buffer:
        # Đọc ảnh từ buffer của Streamlit
        image = Image.open(img_buffer)
        # Chuyển sang mảng numpy format BGR của OpenCV
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # 1. Phát hiện biển số bằng YOLO
        bbox = detect_license_plate(frame)
        if bbox is not None:
            # 2. Cắt và tiền xử lý
            processed_crop = process_plate(frame, bbox)
            if processed_crop is not None:
                # 3. Đọc chữ bằng OCR
                text = ocr_engine.read_plate(processed_crop)
                if text:
                    # Gán vào biển số thủ công để user chỉ việc bấm xác nhận
                    st.session_state.last_scanned = text
                    st.success(f"OCR thành công: **{text}**")
                else:
                    st.warning("Tìm thấy biển nhưng không đọc được chữ!")
            else:
                st.warning("Lỗi tiền xử lý ảnh crop!")

            # Vẽ khung nhận diện lên ảnh để hiển thị
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            if 'text' in locals() and text:
                cv2.rectangle(frame, (x1, max(0, y1 - 35)), (x2, y1), (0, 0, 0), -1)
                cv2.putText(frame, text, (x1 + 5, max(20, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        else:
            st.warning("Không tìm thấy biển số trong ảnh!")

        # Hiển thị ảnh đã được vẽ box
        st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_container_width=True)

    # ── SEMI-MANUAL: Hiển thị biển số camera phát hiện ──
    # live_test.py ghi vào DB → Dashboard đọc → nhân viên confirm
    if camera_detected:
        # Nếu camera phát hiện biển mới, cập nhật vào session
        if camera_detected != st.session_state.get("last_scanned", ""):
            st.session_state.last_scanned = camera_detected
        st.success(f"Camera phát hiện: **{camera_detected}** — Nhấn XE VÀO hoặc XE RA để xác nhận")

    st.markdown("<p style='font-weight:bold; margin-top:0.4rem; margin-bottom:0;'>Xác nhận giao dịch</p>", unsafe_allow_html=True)
    
    # Lấy trực tiếp từ kết quả quét, bỏ qua ô nhập tay
    current_plate = st.session_state.last_scanned or ""

    now = datetime.datetime.now()
    btn1, btn2 = st.columns(2)

    with btn1:
        if st.button("XE VÀO", use_container_width=True, type="primary"):
            plate = current_plate.strip().upper()
            if not plate:
                st.warning("Vui lòng nhập biển số!")
            else:
                result = db.process_vehicle(plate)
                s = result.get("status")
                if s == "CHECK-IN":
                    st.session_state.last_action       = "in"
                    st.session_state.last_action_plate = plate
                    st.session_state.last_action_slot  = f"Vé #{result.get('ticket_id')}"
                    st.session_state.last_action_fee   = ""
                    st.session_state.last_out_info     = {}
                    db.clear_detected_plate()   # Xóa biển đã xử lý khỏi queue camera
                    st.rerun()
                elif s == "CHECK-OUT":
                    st.error("⚠️ Xe đã có trong bãi — vui lòng dùng nút XE RA!")
                elif s == "FULL":
                    st.error(result.get("message", "Bãi đã đầy!"))
                else:
                    st.error(result.get("message", "Lỗi không xác định!"))

    with btn2:
        if st.button("XE RA", use_container_width=True):
            plate = current_plate.strip().upper()
            if not plate:
                st.warning("Vui lòng nhập biển số!")
            else:
                result = db.process_vehicle(plate)
                s = result.get("status")
                if s == "CHECK-OUT":
                    record = {
                        "plate":     plate,
                        "ticket_id": result.get("ticket_id"),
                        "fee":       f"{result.get('fee', 0):,.0f}đ",
                        "hours":     result.get("hours", 0),
                        "minutes":   result.get("minutes", 0),
                        "time_out":  now.strftime("%H:%M:%S"),
                        "date_out":  now.strftime("%d/%m/%Y"),
                    }
                    st.session_state.last_action       = "out"
                    st.session_state.last_action_plate = plate
                    st.session_state.last_action_fee   = f"{result.get('fee', 0):,.0f}đ"
                    st.session_state.last_action_slot  = ""
                    st.session_state.last_out_info     = record
                    db.clear_detected_plate()   # Xóa biển đã xử lý khỏi queue camera
                    st.rerun()
                elif s == "CHECK-IN":
                    st.error("Xe chưa vào bãi — vui lòng dùng nút XE VÀO!")
                else:
                    st.error(result.get("message", "Không tìm thấy xe trong bãi!"))

# CỘT PHẢI – TRẠNG THÁI, ĐỐI CHIẾU & CÀI ĐẶT
with col_right:
    # ── 1. TRẠNG THÁI CHỖ TRỐNG ──
    free_slots = capacity - occupancy
    st.markdown(f"Chỗ còn trống: **{free_slots} / {capacity}**")
    st.progress(occupancy / capacity if capacity > 0 else 0)

    # ── Doanh thu hôm nay ──
    rev       = revenue_data.get("revenue", 0)
    checkouts = revenue_data.get("checkouts", 0)
    st.caption(f"Doanh thu hôm nay: **{rev:,.0f}đ** ({checkouts} lượt ra)")

    st.divider()
    st.subheader("Thông tin chi tiết")

    # ── Thông báo trạng thái ──
    action = st.session_state.last_action
    if action == "in":    st.success("XE VÀO THÀNH CÔNG ✅")
    elif action == "out": st.error("XE RA THÀNH CÔNG 🚗")
    else:                 st.info("Đang chờ quét xe...")

    # ── 2. BIỂN SỐ XE ──
    st.write("**Biển số xe:**")
    st.code(st.session_state.last_scanned or "-- --- --", language="text")

    # ── 3. KHUNG ĐỐI CHIẾU THỜI GIAN ──
    st.write("**Đối chiếu thời gian:**")

    p_date_in = p_time_in = p_date_out = p_time_out = "--"
    p_fee = "0đ"

    if action == "in" and st.session_state.last_action_plate:
        found = next(
            (v for v in vehicles_in if v["plate_number"].upper() == st.session_state.last_action_plate.upper()),
            None,
        )
        if found:
            p_date_in = fmt_date(found["time_in"])
            p_time_in = fmt_time(found["time_in"])
            p_fee     = "Xe đang trong bãi"
            p_date_out = "--"
            p_time_out = "--"

    elif action == "out":
        info = st.session_state.last_out_info
        if info:
            p_date_in  = info.get("date_out", "--")
            p_time_in  = f"{info.get('hours', 0)}h {info.get('minutes', 0)}m (tổng)"
            p_date_out = info.get("date_out", "--")
            p_time_out = info.get("time_out", "--")
            p_fee      = info.get("fee", "0đ")

    st.write(f"Ngày vào:     {p_date_in}")
    st.write(f"Giờ vào:      {p_time_in}")
    st.write(f"Ngày ra:      {p_date_out}")
    st.write(f"Giờ ra:       {p_time_out}")
    st.write(f"Phí gửi:  **{p_fee}**")

    st.divider()

    # ── 4. CÀI ĐẶT HỆ THỐNG ──
    with st.popover("Cài đặt hệ thống", use_container_width=True):
        st.markdown("**Cấu hình thông số bãi xe**")
        new_capacity = st.number_input(
            "Sức chứa tối đa (chỗ):",
            min_value=1, max_value=500, value=capacity, step=1,
        )
        if st.button("Lưu sức chứa", use_container_width=True):
            ok = db.set_max_capacity(new_capacity)
            if ok:
                st.toast(f"Đã lưu sức chứa: {new_capacity} chỗ!")
                st.rerun()
            else:
                st.error(f"Không thể giảm xuống {new_capacity} — hiện có {occupancy} xe trong bãi!")

        st.divider()
        st.caption(
            "Giá vé: chỉnh trong `modules/config.py`\n\n"
            "Camera thật: `python modules/live_test.py`\n\n"
            "Dashboard tự làm mới mỗi 5s khi cài `streamlit-autorefresh`"
        )

    # ── 5. AUTO-REFRESH ──
    if AUTO_REFRESH_SEC > 0:
        try:
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=AUTO_REFRESH_SEC * 1000, key="dashboard_refresh")
        except ImportError:
            if st.button("Làm mới", use_container_width=True):
                st.rerun()
