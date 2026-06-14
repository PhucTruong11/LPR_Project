# 🛠️ Hướng dẫn sử dụng Git cơ bản cho Dự án LPR

Tài liệu này hướng dẫn cách nhóm làm việc chung trên cùng một dự án LPR sử dụng Git, tránh xung đột code và đảm bảo code luôn sạch sẽ.

---

## 1️⃣ Khởi tạo và Cấu hình Git

**Bước 1: Khởi tạo repository (Chỉ Nhóm trưởng thực hiện 1 lần)**
Nhóm trưởng tạo một repository trên GitHub, sau đó đẩy code khung ban đầu lên.

**Bước 2: Cấu hình thông tin (Tất cả thành viên)**
Trước khi bắt đầu, mỗi người cần cấu hình tên và email để Git ghi nhận ai là người thực hiện thay đổi:
```bash
git config --global user.name "Tên của bạn"
git config --global user.email "email_cua_ban@example.com"
```

**Bước 3: Clone project về máy (Tất cả thành viên trừ nhóm trưởng)**
```bash
git clone <URL_CUA_REPOSITORY>
cd LPR_Project
```

---

## 2️⃣ Luồng làm việc cơ bản (Add - Commit - Push)

Mỗi khi bạn làm xong một tính năng hoặc một đoạn code chạy ổn định, hãy lưu lại theo 3 bước:

1. **Kiểm tra trạng thái các file bị thay đổi:**
   ```bash
   git status
   ```
2. **Thêm các thay đổi vào khu vực chờ (Staging Area):**
   ```bash
   git add <tên_file>     # Add 1 file cụ thể
   git add .              # Add tất cả các file có thay đổi
   ```
3. **Lưu lịch sử thay đổi (Commit):**
   *(Ghi chú rõ ràng những gì bạn đã làm)*
   ```bash
   git commit -m "Cập nhật hàm tiền xử lý ảnh biển số bằng OpenCV"
   ```
4. **Đẩy code lên server (Push):**
   ```bash
   git push origin <tên_nhánh_của_bạn>
   ```

---

## 3️⃣ Chia nhánh (Branching) & Đặt tên nhánh

Để nhiều người không sửa đè lên code của nhau, **MỖI NGƯỜI PHẢI LÀM VIỆC TRÊN MỘT NHÁNH RIÊNG**. Không ai được push trực tiếp vào nhánh `main` (hoặc `master`).

### Quy ước đặt tên nhánh:
Sử dụng format `feature-<tên-module>` để dễ nhận biết ai đang làm gì:

| Phụ trách | Nhánh |
|-----------|-------|
| Giao diện Streamlit & gộp pipeline | `feature-ui` |
| Mô hình YOLO nhận diện | `feature-yolo` |
| Xử lý ảnh OpenCV | `feature-opencv` |
| Nhận diện chữ OCR | `feature-ocr` |
| Database & tính phí | `feature-database` |
| Tài liệu & báo cáo | `feature-docs` |

### Cách tạo và chuyển nhánh:
```bash
# Tạo nhánh mới và chuyển sang nhánh đó ngay lập tức
git checkout -b <tên_nhánh>

# Ví dụ:
git checkout -b feature-yolo
```

### Cách cập nhật code mới nhất từ nhánh `main`:
Trước khi làm việc mỗi ngày, hãy cập nhật nhánh của bạn để lấy code mới nhất do Nhóm trưởng đã gộp:
```bash
git checkout main
git pull origin main
git checkout <tên_nhánh_của_bạn>
git merge main
```

---

## 4️⃣ Tạo Pull Request (PR) để gộp code vào `main`

Khi bạn hoàn thành tính năng trên nhánh của mình và muốn gộp vào `main`, **KHÔNG push trực tiếp** mà phải tạo Pull Request:

### Quy trình tạo PR:
1. **Push nhánh lên GitHub:**
   ```bash
   git push origin <tên_nhánh_của_bạn>
   ```
2. **Vào GitHub → Tab "Pull requests" → Bấm "New pull request".**
3. **Chọn nhánh nguồn** (nhánh của bạn) → **nhánh đích** (`main`).
4. **Viết mô tả rõ ràng** những gì bạn đã làm và các file bị ảnh hưởng.
5. **Gửi PR** và chờ nhóm trưởng review.

### Ai có quyền merge?
- **Nhóm trưởng** là người duy nhất có quyền merge PR vào `main` sau khi kiểm tra code.
- Nếu có lỗi, nhóm trưởng sẽ comment trên PR yêu cầu sửa → bạn sửa xong push lại → PR tự cập nhật.

---

## 5️⃣ Cứu hộ và Xử lý Xung đột (Conflicts)

Trong quá trình làm việc chung, chắc chắn sẽ có lúc 2 người cùng sửa chung 1 file dẫn đến Conflict (Xung đột).

### Tình huống 1: Đang code dở nhưng cần đổi nhánh (Lưu nháp)
Nếu bạn chưa làm xong tính năng nhưng cần chuyển nhánh khác (hoặc pull code), hãy cất tạm code vào kho:
```bash
git stash              # Cất tạm code đi
# ...làm việc khác...
git stash pop          # Lấy lại code đang làm dở
```

### Tình huống 2: Code lỡ sai, muốn quay về ban đầu
* **Hủy bỏ các thay đổi ở 1 file chưa commit:**
  ```bash
  git checkout -- <tên_file>
  ```
* **Xóa bỏ các commit gần nhất (Cẩn thận!):**
  ```bash
  git reset --hard HEAD~1   # Quay lại 1 commit trước đó, bỏ luôn code sai
  ```

### Tình huống 3: Bị Xung đột (Conflict) khi Merge hoặc Pull
Khi gộp nhánh (hoặc Pull) mà báo chữ `CONFLICT`, bạn đừng hoảng hốt:
1. Mở code editor (VS Code/PyCharm) lên. Git sẽ đánh dấu đoạn code bị xung đột bằng các ký tự `<<<<<<<`, `=======`, `>>>>>>>`.
2. Bạn (và người kia) cùng xem lại đoạn code đó, giữ lại phần đúng, xóa bỏ các phần thừa và dấu `<<<<<<<`, `=======`.
3. Sau khi file đã sửa xong, lưu file lại.
4. Chạy lại lệnh Add và Commit để hoàn tất việc sửa lỗi:
   ```bash
   git add .
   git commit -m "Fix conflict ở file xử lý ảnh"
   ```

> **Nguyên tắc vàng:** "Khi gặp conflict không biết xử lý, hãy gọi Nhóm trưởng!"
