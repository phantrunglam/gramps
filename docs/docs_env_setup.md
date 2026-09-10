# TÀI LIỆU CƠ SỞ DỰ ÁN: TÍCH HỢP LỊCH ÂM VIỆT NAM VÀO GRAMPS ARCHITECTURE

## 1. Thiết lập môi trường quản lý mã nguồn với GitHub

Để phát triển tính năng mới một cách an toàn và dễ dàng quản lý/đồng bộ với mã nguồn gốc của Gramps, phương pháp **Git Fork** được lựa chọn:

1. **Fork Repository chính:**
   - Truy cập repository gốc của Gramps tại [https://github.com/gramps-project/gramps](https://github.com/gramps-project/gramps).
   - Bấm nút **Fork** để tạo một bản sao repository về tài khoản cá nhân.
2. **Clone mã nguồn về máy local:**
   ```bash
   cd /d/Projects
   git clone [https://github.com/phantrunglam/gramps.git](https://github.com/phantrunglam/gramps.git)
   cd gramps

3. **Cấu hình Upstream Remote & Tạo nhánh phát triển (Branch):**
```bash
git remote add upstream [https://github.com/gramps-project/gramps.git](https://github.com/gramps-project/gramps.git)
git fetch upstream
git checkout master
git pull upstream master
git checkout -b feature/vietnamese-lunar-calendar
```

## 2. Thiết lập môi trường làm việc trên VS Code (Windows 11 / MSYS2 UCRT64 / MinGW64)

Gramps sử dụng giao diện **GTK3** và **Python 3**. Trên Windows, môi trường **MSYS2** (UCRT64 / MinGW64) được sử dụng để cung cấp đầy đủ thư viện đồ họa và công cụ biên dịch.

### Các lệnh thiết lập môi trường (Chạy trong MSYS2 UCRT64 / MinGW64 Terminal)

```bash
# 1. Cập nhật cơ sở dữ liệu hệ thống gói
pacman -Syu

# 2. Cài đặt Python 3, GTK3, PyGObject, Cairo, Gettext và công cụ biên dịch
pacman -S --needed \\
    mingw-w64-x86_64-python \\
    mingw-w64-x86_64-python-gobject \\
    mingw-w64-x86_64-gtk3 \\
    mingw-w64-x86_64-python-cairo \\
    mingw-w64-x86_64-python-certifi \\
    mingw-w64-x86_64-gettext \\
    mingw-w64-x86_64-toolchain \\
    git

# 3. Cài đặt các thư viện bổ sung cần thiết cho Gramps (tránh cảnh báo GExiv2 / Pillow)
pacman -S --needed ucrt64/mingw-w64-ucrt-x86_64-gexiv2 mingw-w64-x86_64-python-pillow

```

### Cấu hình VS Code

1. Mở thư mục mã nguồn Gramps bằng VS Code: `code .`
2. Thiết lập Python Interpreter:
* Bấm `Ctrl + Shift + P` -> gõ `Python: Select Interpreter`.
* Trỏ tới đường dẫn thi hành Python của MSYS2: `C:\\msys64\\mingw64\\bin\\python.exe` (hoặc đường dẫn UCRT64 tương ứng).


3. Chạy Gramps thử nghiệm từ terminal:
```bash
python3 Gramps.py

```

## 3. Xác định kiến trúc Date/Calendar của Gramps

Kiến trúc xử lý ngày tháng trong Gramps tách biệt rõ ràng giữa **Lưu trữ dữ liệu backend**, **Quy đổi thuật toán**, và **Hiển thị/Parse chuỗi giao diện**:

1. **Lớp Cấu trúc Dữ liệu (`Date` Object & Constants):**
* **File:** `gramps/gen/lib/date.py`
* Định nghĩa các hằng số nhận diện hệ lịch (`CAL_GREGORIAN`, `CAL_JULIAN`, `CAL_HEBREW`, v.v.) và mảng chuỗi nhận diện `CAL_STRINGS`.
* Lưu trữ thời gian dựa trên chỉ số ngày tuyệt đối **Julian Day Number (JDN / SDN)** dưới cơ sở dữ liệu để đảm bảo khả năng so sánh, sắp xếp và truy vấn độc lập.


2. **Lớp Xử lý Thuật toán quy đổi (`DateHandler` module):**
* **Thư mục:** `gramps/gen/datehandler/`
* Chứa logic chuyển đổi hai chiều giữa **Julian Day Number (JDN)** và **(Ngày, Tháng, Năm, Cờ nhuận)** của từng hệ lịch cụ thể.


3. **Lớp Định dạng & Parse chuỗi văn bản (`_dateparser.py`, `_datedisplay.py`, `_datestrings.py`):**
* **`_dateparser.py`**: Nhận diện các chuỗi gõ vào của người dùng (VD: từ khóa `lunar`, `âm`, `(A)`) để chuyển đổi về đúng `calendar_type`.
* **`_datedisplay.py`**: Định dạng ngày Âm lịch ra giao diện hiển thị cho báo cáo và cây gia hệ.
* **`_datestrings.py`**: Khai báo danh sách từ khóa ngữ pháp/tên hệ lịch hỗ trợ cho việc parse và hiển thị ngữ cảnh đa ngôn ngữ.



## 4. Giải thích mã nguồn của module `vietnamese_lunar.py`

Module `vietnamese_lunar.py` chịu trách nhiệm cung cấp thuật toán toán học thuần túy chuyển đổi giữa Âm lịch Việt Nam và Số ngày Julian (Julian Day Number / SDN):

1. **Chức năng chính:**
* **`lunar_to_jdn(day, month, year, is_leap)`**: Nhận vào thông tin Ngày, Tháng, Năm Âm lịch cùng cờ `is_leap` (xác định tháng nhuận) -> tính toán và trả về chỉ số **Julian Day Number (JDN / SDN)**.
* **`jdn_to_lunar(jdn)`**: Nhận vào chỉ số **Julian Day Number (JDN / SDN)** -> trả về tuple kết quả `(day, month, year, is_leap)` đại diện cho ngày Âm lịch Việt Nam tương ứng.


2. **Đặc điểm thuật toán:**
* Xử lý các múi giờ và điểm Sóc (New Moon), Tiết khí dựa trên tọa độ/múi giờ chuẩn của Việt Nam (UTC+7).
* Xác định chính xác các tháng nhuận và cờ nhuận `is_leap` nhằm cung cấp dữ liệu đầu vào chuẩn cho hệ thống Gramps.



## 5. Ghi nhận những thay đổi cần thiết trong các file liên quan của Gramps

Để tích hợp hệ lịch mới `CAL_VIETNAMESE_LUNAR` vào Gramps, các chỉnh sửa sau đã được thực hiện đồng bộ trên các file kiến trúc:

| File | Nội dung thay đổi / Chỉnh sửa |
| --- | --- |
| **`gramps/gen/lib/date.py`** | Khai báo hằng số hệ lịch mới `CAL_VIETNAMESE_LUNAR` (VD: `CAL_VIETNAMESE_LUNAR = 7`) và cập nhật danh sách `CAL_STRINGS` để hiển thị tùy chọn trong Dropdown giao diện. |
| **`gramps/gen/datehandler/_datevietnameselunar.py`** | Tạo mới tệp kết nối giữa `vietnamese_lunar.py` và lớp xử lý ngày của Gramps, định nghĩa lớp `VietnameseLunarDate` để giao tiếp dữ liệu JDN <-> Lunar. |
| **`gramps/gen/datehandler/_datestrings.py`** | Đồng bộ thuộc tính instance trong `__init__` (`self.vietnamese_lunar = self.vietnamese_lunar_VI`) để hệ thống nhận diện từ khóa dịch/chuỗi tên hệ lịch Âm Việt Nam. |
| **`gramps/gen/datehandler/_dateparser.py`** | Đăng ký biểu thức chính quy (Regex: `_vltext`, `_vltext2`) để parser tự động nhận diện ký hiệu/từ khóa Âm lịch do người dùng nhập vào. |
| **`gramps/gen/datehandler/_datedisplay.py`** | Định nghĩa phương thức hiển thị ngày Âm lịch ra màn hình/báo cáo (VD: `15/08/2026 (Âm lịch)` hoặc đánh dấu tháng nhuận). |
| **`gramps/gen/datehandler/_datehandler.py`** | Đăng ký handler tiếng Việt bằng `register_datehandler(...)` để Gramps nạp hệ thống lịch Âm Việt Nam vào danh sách hệ lịch hoạt động. |
| """ |  |


