# RPG Maker Game Localization Reference

Hướng dẫn chi tiết cho các phiên bản RPG Maker: MV, MZ, VX Ace, XP.

---

## 1. Dấu Hiệu Nhận Diện (Signatures)

### RPG Maker MV / MZ
- Thư mục `data/` hoặc `www/data/` chứa các tệp JSON:
  - `System.json`: Tiêu đề game, tên lệnh menu (New Game, Continue, Options), thông điệp hệ thống.
  - `Actors.json`: Tên nhân vật, biệt danh, profile giới thiệu.
  - `Classes.json`, `Skills.json`, `Items.json`, `Weapons.json`, `Armors.json`: Tên trang bị, vật phẩm, mô tả công dụng.
  - `Enemies.json`, `Troops.json`: Tên quái vật, sự kiện chạm trán.
  - `States.json`: Hiệu ứng trạng thái (Trúng độc, Choáng...).
  - `Map001.json`, `Map002.json`...: Sự kiện hội thoại map (Message Event code `401`, Choice Event code `102`).
  - `CommonEvents.json`: Sự kiện chung, nhiệm vụ phụ, cutscenes.
- Tệp `package.json` với `"main": "index.html"`.

### RPG Maker VX Ace / XP
- Thư mục `Data/` chứa file nhị phân Ruby Marshal:
  - `.rvdata2` (VX Ace)
  - `.rxdata` (XP)

---

## 2. Quy Tắc Trích Xuất & Lưu Ý Quan Trọng

### RPG Maker MV & MZ (JSON Native)
`locaforge_extract.py` có parser chuyên biệt cho RPG Maker:
```bash
python3 scripts/locaforge_extract.py data Localization_Source
# hoặc www/data
python3 scripts/locaforge_extract.py www/data Localization_Source
```

**Các mã sự kiện (Event Codes) cần dịch:**
- Code `401`: Lời thoại nhân vật (`Show Text`).
- Code `102`: Lựa chọn tương tác (`Show Choices`).
- Các trường đối tượng: `name`, `description`, `message1`, `message2`.
- **CẤM SỬA**: `id`, `switchId`, `variableId`, các mã script code `355` / `655` (trừ khi là chuỗi hiển thị).

---

## 3. Quy Trình Cài Đặt Patch Việt Hoá
```bash
python3 scripts/locaforge_patch.py --project-id <id>
```
1. Tự động backup `data/` vào `Localization_Backup/data/`.
2. Ghi đè các chuỗi tiếng Việt đã dịch vào `data/*.json`.
3. Kiểm tra mã hoá UTF-8 chuẩn xác, không bị lỗi dấu tiếng Việt khi load trong trình duyệt Chromium / Electron của RPG Maker.

