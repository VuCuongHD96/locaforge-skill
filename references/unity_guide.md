# Unity Game Localization & Patching Reference

Hướng dẫn chi tiết dành cho AI Agent và Game Modder khi xử lý game phát triển bằng Unity Engine.

---

## 1. Dấu Hiệu Nhận Diện (Signatures)
- Thư mục `[GameName]_Data/` hoặc trên macOS: `[GameName].app/Contents/Resources/Data/`.
- File runtime: `UnityPlayer.dll`, `UnityCrashHandler64.exe`, hoặc `GameAssembly.dll` (IL2CPP).
- Thư mục con quan trọng:
  - `[GameName]_Data/StreamingAssets/`: Thường chứa text, JSON, CSV, mod assets trực tiếp.
  - `[GameName]_Data/Managed/`: Chứa mã nguồn C# đã biên dịch (.NET Mono).
  - `[GameName]_Data/il2cpp_data/`: Metadata cho game IL2CPP.
  - `*.assets`, `resources.assets`, `sharedassets*.assets`: Asset bundles đóng gói.

---

## 2. Các Kiến Trúc Bản Địa Hoá Phổ Biến Trong Unity

### A. Unity Localization Package (String Tables)
- Văn bản được lưu thành các bảng: `MainMenu`, `UI`, `Dialogue`, `Items`, `Quests`.
- Format gốc: Thường là CSV hoặc JSON với các cột:
  - `table`: Tên bảng (TUYỆT ĐỐI KHÔNG SỬA)
  - `id`: Định danh nội bộ Unity (TUYỆT ĐỐI KHÔNG SỬA)
  - `key`: Khóa định danh ngữ cảnh (TUYỆT ĐỐI KHÔNG SỬA)
  - `english`: Văn bản gốc tiếng Anh
  - `vietnamese`: Nội dung bản dịch tiếng Việt

### B. I2 Localization (Plugin Phổ Biến)
- Dữ liệu dạng CSV hoặc Google Sheets đồng bộ, chứa các cột ngôn ngữ: `Key`, `Type`, `Desc`, `English`, `Vietnamese`.
- LocaForge tự động nhận diện cấu trúc I2 Localization qua `I2LocalizationDetector`.

### C. TextAsset / MonoBehaviour Trực Tiếp Trong `StreamingAssets/`
- Thường nằm ở `StreamingAssets/Languages/`, `StreamingAssets/Localization/`, hoặc `StreamingAssets/Data/`.
- Thường là file JSON, CSV, XML hoặc INI plain text. Có thể sửa và nạp trực tiếp mà không cần unpack asset bundles!

---

## 3. Quy Trình Trích Xuất & Nạp Patch

### Bước 1: Trích xuất
```bash
python3 scripts/locaforge_extract.py "[GameName]_Data/StreamingAssets" Localization_Source
```
Nếu text nằm trong asset bundle `.assets`, sử dụng công cụ mã nguồn mở UABEA (Unity Asset Bundle Extractor Avalonia) hoặc AssetStudio để xuất `TextAsset` sang file `.txt`/`.json`/`.csv`.

### Bước 2: Dịch trên LocaForge
Đẩy lên web LocaForge để dịch bằng AI hoặc mời cộng đồng cùng dịch.

### Bước 3: Nạp bản dịch (Patch)
```bash
python3 scripts/locaforge_patch.py --zip Vietnamese_Patch.zip
```
Script sẽ tự động sao lưu file gốc vào `Localization_Backup/` và ghi đè bản dịch vào đúng vị trí.

---

## 4. Xử Lý Phông Chữ Tiếng Việt (Vietnamese Fonts)
- Nếu tiếng Việt bị lỗi hiển thị (ô vuông `□` hoặc mất dấu `?`):
  - Game Unity sử dụng TextMeshPro (TMP) cần font atlas hỗ trợ Unicode tiếng Việt (`Latin-1 Supplement` + `Latin Extended-A` + `Latin Extended Additional`).
  - Thay thế font asset trong `StreamingAssets/Fonts/` hoặc nạp font TTF/OTF hỗ trợ tiếng Việt qua Mod.
