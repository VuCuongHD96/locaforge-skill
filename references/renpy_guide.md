# Ren'Py Game Localization Reference

Hướng dẫn dịch game phát triển bằng Ren'Py Visual Novel Engine.

---

## 1. Dấu Hiệu Nhận Diện (Signatures)
- Thư mục `game/` chứa:
  - `*.rpy`: Script nguồn Ren'Py (chứa đối thoại, menu, biến số).
  - `*.rpyc`: Mã bytecode Ren'Py đã biên dịch.
  - `*.rpa`: Gói tài nguyên lưu trữ nén của Ren'Py.
  - Thư mục `renpy/` chứa framework engine.

---

## 2. Hệ Thống Đa Ngôn Ngữ Chuẩn Của Ren'Py
Ren'Py có hệ sinh thái bản địa hoá tích hợp sẵn tại `game/tl/<language>/`:
```
game/
├── tl/
│   └── vietnamese/
│       ├── common.rpy
│       ├── options.rpy
│       ├── screens.rpy
│       └── script.rpy
```

### Cấu Trúc File Bản Dịch:
```renpy
# Dịch lời thoại:
translate vietnamese start_a1b2c3d4:
    # "Hello, world!"
    "Xin chào thế giới!"

# Dịch chuỗi giao diện (String translation):
translate vietnamese strings:
    old "Start Game"
    new "Bắt Đầu Trò Chơi"

    old "Preferences"
    new "Cài Đặt"
```

---

## 3. Quy Trình Trích Xuất & Cài Đặt Với LocaForge

### Bước 1: Trích xuất
Nếu game đã có file `.rpy`:
```bash
python3 scripts/locaforge_extract.py game Localization_Source
```
Nếu game chỉ có `.rpa`: dùng công cụ `unrpa` (`pip install unrpa`) để bung `scripts.rpa` lấy `.rpyc` và dịch ngược bằng `unrpyc`.

### Bước 2: Dịch trên LocaForge
Đẩy các file lên LocaForge để dịch.

### Bước 3: Cài đặt Patch
```bash
python3 scripts/locaforge_patch.py --zip Vietnamese_Patch.zip
```
`locaforge_patch.py` sẽ tự động chuyển đổi JSON bản dịch từ LocaForge sang file `.rpy` chuẩn Ren'Py và đặt vào `game/tl/vietnamese/`.
Người chơi chỉ cần vào game chọn ngôn ngữ "Vietnamese" trong Settings hoặc Ren'Py sẽ kích hoạt ngay!

