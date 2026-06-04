# PaddleOCR — Động cơ Nhận diện Ký tự quang học (OCR) Chuyên sâu

## 1. Giới thiệu tổng quan và Cơ sở lý thuyết Học sâu của OCR

### 1.1. Sự phát triển của các phương pháp OCR
Nhận diện ký tự quang học (**OCR - Optical Character Recognition**) là quá trình chuyển đổi hình ảnh chứa văn bản thành chuỗi ký tự máy tính có thể biên tập và tìm kiếm được. 
* **Phương pháp cổ điển (Tesseract OCR):** Dựa trên việc phân tích đường biên ký tự và so khớp mẫu (template matching) hoặc sử dụng mạng neural nông. Tesseract hoạt động rất tốt với tài liệu quét (scanned document) chữ đen nền trắng phẳng, nhưng cực kỳ kém hiệu quả đối với các ảnh chụp ngoài thực tế (như biển số xe bị nghiêng, chói sáng, rung nhiễu) do không có khả năng tự trích xuất đặc trưng sâu sắc từ môi trường.
* **Phương pháp học sâu hiện đại (Deep Learning OCR):** Coi OCR là một pipeline gồm hai mô hình học sâu nối tiếp nhau: **Phát hiện văn bản (Text Detection)** và **Nhận diện văn bản (Text Recognition)**.

### 1.2. Kiến trúc cốt lõi của PaddleOCR
**PaddleOCR** phát triển bởi Baidu dựa trên nền tảng **PaddlePaddle**, được đánh giá là một trong những thư viện OCR học sâu tốt nhất thế giới hiện nay nhờ sự kết hợp tối ưu giữa độ chính xác vượt trội và tốc độ xử lý nhanh:
1. **Mô hình Phát hiện văn bản (Text Detection - DBNet):** Sử dụng mạng **DBNet (Differentiable Binarization)**. Thay vì dùng ngưỡng nhị phân hóa cứng không thể đạo hàm, DBNet tích hợp một bước nhị phân hóa có thể vi phân trực tiếp vào mạng neural để huấn luyện đồng thời. Điều này giúp mạng xác định chính xác đường bao đa giác bao quanh từng từ, cụm từ ngay cả trong điều kiện ánh sáng cực kỳ phức tạp.
2. **Mô hình Nhận diện văn bản (Text Recognition - CRNN + CTC):**
   * **Mạng CNN (Convolutional Neural Network):** Trích xuất các bản đồ đặc trưng trực quan (visual feature map) từ vùng ảnh chữ đã được phát hiện.
   * **Mạng RNN (Recurrent Neural Network - cụ thể là BiLSTM):** Xử lý đặc trưng dạng chuỗi theo thời gian để hiểu được sự liên kết ngữ cảnh giữa các chữ cái đứng liền nhau.
   * **Lớp phân loại CTC (Connectionist Temporal Classification Loss):** Giải quyết bài toán liên kết chuỗi khi không có sự căn hàng (alignment) chính xác giữa vị trí pixel ảnh đầu vào và chuỗi văn bản đầu ra. CTC tự động gộp các ký tự trùng lặp và loại bỏ các khoảng trắng đặc biệt để tạo ra chuỗi văn bản cuối cùng.

---

## 2. Giải pháp xử lý biển số nhiều dòng (Multi-line License Plate Sorting Algorithm)

Một thách thức lớn đối với việc nhận diện biển số xe tại Việt Nam là sự tồn tại song song của hai loại biển số: **Biển số dài (1 dòng)** và **Biển số vuông (2 dòng)**. 
* Biển vuông có dòng trên chứa mã tỉnh và ký tự series (ví dụ: `29C1`), dòng dưới chứa số thứ tự ngẫu nhiên (ví dụ: `234.56`).
* Khi quét, các mô hình học sâu thường nhận diện các cụm ký tự rời rạc và trả về tọa độ không theo thứ tự đọc tự nhiên (từ trái sang phải, từ trên xuống dưới). Nếu ghép trực tiếp chuỗi thô từ OCR, kết quả thu được sẽ bị đảo lộn (ví dụ: dòng dưới bị ghép lên trước dòng trên).

Dự án xử lý triệt để bài toán này bằng thuật toán **Phân cụm dòng theo trục Y (Y-axis Line Clustering Algorithm)**:

### 2.1. Mã giả thuật toán (Pseudocode)
```text
Thuật toán: Sắp xếp và Ghép chữ biển số xe nhiều dòng
Đầu vào: Danh sách kết quả OCR dạng [ [Tọa độ 4 đỉnh hộp chữ], Chuỗi_chữ, Độ_tin_cậy ]
Đầu ra: Chuỗi biển số được ghép đúng thứ tự tự nhiên

1. Lọc bỏ các kết quả có Độ_tin_cậy < MIN_CONFIDENCE (40%)
2. Hàm Center_Y(hộp): Tính trung điểm trục Y của hộp chữ
3. Hàm Center_X(hộp): Tính trung điểm trục X của hộp chữ
4. Sắp xếp danh sách kết quả theo chiều tăng dần của Center_Y
5. Ngưỡng phân tách dòng (line_threshold) = Chiều cao ảnh biển số * 0.30
6. Khởi tạo danh sách các dòng rỗng: Lines = [ [Phần tử đầu tiên] ]

7. Với mỗi phần tử tiếp theo (R) trong danh sách đã sắp xếp:
       Tính trung bình Y của dòng hiện tại (Avg_Y)
       Nếu | Center_Y(R) - Avg_Y | <= line_threshold:
           Thêm R vào dòng hiện tại
       Ngược lại:
           Tạo một dòng mới chứa R và thêm vào danh sách Lines

8. Với mỗi dòng (Line) trong danh sách Lines:
       Sắp xếp các phần tử bên trong dòng theo chiều tăng dần của Center_X (Trái sang Phải)

9. Ghép chuỗi: Chuỗi_kết_quả = Ghép tất cả Chuỗi_chữ từ các dòng theo thứ tự từ trên xuống dưới
10. Trả về Chuỗi_kết_quả
```

---

## 3. Bộ lọc Hậu xử lý & Hiệu chỉnh Lập quy tắc (Rule-based Post-processing)

Do camera chụp trong môi trường thực tế, hình ảnh các ký tự chữ cái và chữ số rất dễ bị nhầm lẫn với nhau do cấu trúc hình học tương đồng (ví dụ: chữ `O` trông rất giống số `0`, chữ `I` giống số `1`). Dự án phát triển một hệ thống hiệu chỉnh chủ động dựa trên luật cứng (Rule-based) để sửa lỗi và chuẩn hóa biển số.

### 3.1. Phân tích cấu trúc biển số xe Việt Nam
Theo thông tư của Bộ Công an, biển số xe dân sự của Việt Nam luôn tuân theo một quy tắc định dạng vị trí ký tự cực kỳ nghiêm ngặt:
* **Vị trí 0 và 1 (Mã tỉnh):** Bắt buộc phải là hai chữ số (Ví dụ: `29`, `30`, `51`).
* **Vị trí 2 (Ký tự Series):** Bắt buộc phải là một chữ cái từ `A` đến `Z` (Ví dụ: `A`, `G`, `K`).
* **Vị trí 3 (Ký tự thứ tư):** Có thể là chữ cái hoặc chữ số tùy thuộc vào loại xe (xe máy phân khối lớn, xe tải, hoặc biển số xe con thông thường).
* **Vị trí 4 trở đi (Đuôi số thứ tự):** Bắt buộc phải là các chữ số (Ví dụ: `1234`, `56789`).

### 3.2. Bảng ánh xạ sửa lỗi ký tự tương đồng
Hệ thống định nghĩa hai bảng ánh xạ chuyển đổi ký tự dựa trên lỗi phổ biến của mô hình AI:

| Hướng chuyển đổi | Ký tự gốc (AI đọc sai) | Ký tự đích (Được chuẩn hóa) | Lý do |
| :--- | :---: | :---: | :--- |
| **Chữ $\rightarrow$ Số** | `O`, `Q`, `D` | `0` | Vòng khép kín tròn trịa dễ nhầm lẫn |
| (Áp dụng cho vị trí 0, 1 và đuôi số) | `I`, `L` | `1` | Dạng nét thẳng đứng |
| | `Z` | `2` | Nét gấp khúc ngang |
| | `S` | `5` | Nét cong tròn phần dưới |
| | `G` | `6` | Đường cong khép kín đuôi |
| | `T` | `7` | Nét gạch ngang đầu |
| | `B` | `8` | Hai vòng khép kín chồng lên nhau |
| **Số $\rightarrow$ Chữ** | `0` | `O` | Nhầm lẫn ngược lại |
| (Áp dụng cho vị trí Series thứ 3) | `1`, `4` | `A` | Dạng chóp nhọn phía trên |
| | `2` | `Z` | Nét gấp khúc |
| | `5` | `S` | Nét cong chữ S |
| | `8` | `B` | Dạng hai cung tròn đứng |

### 3.3. Kiểm chứng Định dạng bằng Regular Expression (RegEx)
Để loại bỏ hoàn toàn các trường hợp OCR nhận diện rác từ môi trường xung quanh biển số (như đinh vít, logo xe, chữ in trên khung bảo vệ biển số), hệ thống áp dụng bộ lọc RegEx nghiêm ngặt:
```regex
PLATE_REGEX = r"^\d{2}[A-Z]\d?[-–]?\d{3,5}\.?\d{0,2}$"
```
* **Ý nghĩa cấu trúc:**
  * `^\d{2}`: Bắt đầu bằng chính xác 2 chữ số (mã tỉnh).
  * `[A-Z]`: Tiếp theo là 1 chữ cái in hoa (series chính).
  * `\d?`: Có thể có thêm 1 số phụ hoặc không (ví dụ: `51G1` hoặc `29A`).
  * `[-–]?`: Có hoặc không có dấu gạch ngang phân tách giữa series và đuôi số.
  * `\d{3,5}`: Phần đuôi số chứa từ 3 đến 5 chữ số liên tục.
  * `\.?`: Có hoặc không có dấu chấm phân cách hàng nghìn (ví dụ: `.11` trong `123.11`).
  * `\d{0,2}$`: 2 chữ số cuối sau dấu chấm (nếu có).

Tất cả các kết quả nhận diện không vượt qua được bộ lọc RegEx này sẽ bị cảnh báo hoặc đánh dấu là biển số không đạt chuẩn, yêu cầu nhân viên vận hành hỗ trợ nhập thủ công, đảm bảo tính toàn vẹn dữ liệu tuyệt đối trước khi ghi vào cơ sở dữ liệu.
