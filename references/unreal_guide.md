# Unreal Engine Game Localization Reference

Hướng dẫn dịch game phát triển bằng Unreal Engine 4 / Unreal Engine 5.

---

## 1. Dấu Hiệu Nhận Diện (Signatures)
- Thư mục `[GameName]/Content/Paks/` chứa các tệp `.pak`.
- Thư mục `[GameName]/Content/Localization/` hoặc `Engine/Content/Localization/`:
  - `Game/`
    - `en/Game.locres`
    - `en/Game.archive`
    - `Game.manifest`
- File thực thi: `[GameName]-Win64-Shipping.exe`.

---

## 2. Hệ Thống Chuỗi Văn Bản Của Unreal Engine

### A. Tệp `.locres` (Localization Resource)
- Đây là định dạng nhị phân chứa chuỗi văn bản bản địa hoá của Unreal Engine.
- Được phân chia theo Namespace và Key.
- Có thể dùng công cụ Python mã nguồn mở `locres_parser` hoặc Unreal Engine Editor để export/import file `.csv` hoặc `.po` tương thích 100% với LocaForge.

### B. Tệp `.pak` (Mod Packing)
- Để cài đặt bản dịch vào game Unreal Engine mà không can thiệp vào file gốc:
  - Unreal Engine hỗ trợ cơ chế nạp Mod Patch: đặt file `.pak` mới có thứ tự ưu tiên cao hơn vào thư mục `[GameName]/Content/Paks/~mods/` (ví dụ: `Vietnamese_Patch_P.pak`).
  - Hậu tố `_P` (Patch) giúp Unreal tự động ghi đè tài nguyên ngôn ngữ khi khởi động game.

---

## 3. Quy Trình Trích Xuất & Nạp Patch Với LocaForge
1. Quét tìm file `.locres`, `.csv`, `.po` trong thư mục game bằng:
   ```bash
   python3 scripts/locaforge_detect.py .
   ```
2. Trích xuất text sang LocaForge:
   ```bash
   python3 scripts/locaforge_extract.py Content/Localization Localization_Source
   ```
3. Đẩy lên web LocaForge, dịch và xuất file ZIP.
4. Nạp bản dịch bằng `locaforge_patch.py`.

