import streamlit as st

# TODO: Import từ các module sau khi các thành viên hoàn thành
# from modules.detection import detect_license_plate
# from modules.processing import process_plate
# from modules.ocr_engine import read_plate

st.set_page_config(page_title="Nhận diện Biển số xe", page_icon="🚗")

st.title("🚗 Hệ thống nhận diện biển số xe (LPR)")
st.write("Giao diện UI và luồng xử lý (Pipeline) sẽ được xây dựng tại đây bởi Thành viên 2.")

# Khung upload file (Trạm 1)
uploaded_file = st.file_uploader("Tải lên ảnh chứa xe/biển số", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    st.success("Tải ảnh thành công! (Logic xử lý đang được tích hợp)")
