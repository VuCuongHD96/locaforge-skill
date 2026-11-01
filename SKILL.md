---
name: locaforge
description: >-
  Universal game localization and Vietnamese translation workflow using LocaForge for any game engine (Unity, Unreal Engine, RPG Maker, Ren'Py, Godot, GameMaker, and Direct Text/Config). Activate this skill when the user asks to:
  (1) Trích xuất file source text từ game để dịch ("trích xuất file source text", "tìm file text game", "extract game strings", "chuẩn bị file dịch"),
  (2) Tạo project trên web LocaForge và đẩy file source lên ("tạo project trên web", "đẩy file source lên locaforge", "upload bảng dịch lên web"),
  (3) Cài đặt bản dịch Việt hoá vào game từ file ZIP ("cài Việt Hoá", "import bản dịch vào game", "patch tiếng Việt"),
  (4) Đóng gói bản ZIP việt hoá thành phẩm & đẩy lên Google Drive / Web ("đóng file zip việt hoá", "đẩy bản zip lên web", "tạo bản cài game việt hoá", "pack patch zip").
---

# LocaForge Universal Game Localization Skill

Bộ quy chuẩn và công cụ tự động hóa toàn diện giúp AI Agent và Game Modder thực hiện trọn vẹn quy trình Việt hoá cho **mọi tựa game** thông qua nền tảng LocaForge.

---

## 🧭 Tổng Quan Quy Trình 4 Bước

```
┌────────────────────────────────────────────────────────────────────────┐
│ BƯỚC 1: TRÍCH XUẤT SOURCE TEXT                                         │
│ Game Folder ──► [locaforge_detect] ──► [locaforge_extract] ──► Source  │
├────────────────────────────────────────────────────────────────────────┤
│ BƯỚC 2: TẠO PROJECT & ĐỒNG BỘ LÊN LOCAFORGE WEB                        │
│ Localization_Source/ ──► [locaforge_sync] ──► Web Translation Studio   │
├────────────────────────────────────────────────────────────────────────┤
│ BƯỚC 3: DỊCH XONG ──► CÀI ĐẶT VIỆT HOÁ VÀO GAME                        │
│ LocaForge Export ZIP ──► [locaforge_patch] ──► Game Ready in VN!       │
├────────────────────────────────────────────────────────────────────────┤
│ BƯỚC 4: ĐÓNG GÓI BẢN CÀI CHO GAME THỦ (.ZIP) & LƯU GOOGLE DRIVE        │
│ Game Files ──► [locaforge_patch --pack-patch] ──► Google Drive Hub 🌐  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Yêu Cầu 1: Trích Xuất File Source Text Để Dịch

Khi người dùng ra lệnh:
> *"Tìm File source text để tôi có thể Việt Hoá"*  
> *"Trích xuất file source text để dịch, tinh chỉnh sang dạng JSON/CSV"*

### Hành Động Bắt Buộc Của Agent:

#### 1.1. Chạy Quét Nhận Diện Engine Game
Thực thi script quét engine để xác định kiến trúc game hiện tại:
```bash
python3 scripts/locaforge_detect.py .
```
- Nếu là **Unity**: Xem chi tiết tại [Unity Guide](./references/unity_guide.md). Kiểm tra `*_Data/StreamingAssets/`, `Localization_Source/`, hoặc Asset Bundles.
- Nếu là **RPG Maker (MV/MZ/VX Ace/XP)**: Xem [RPG Maker Guide](./references/rpgmaker_guide.md). Kiểm tra `data/` hoặc `www/data/`.
- Nếu là **Ren'Py**: Xem [Ren'Py Guide](./references/renpy_guide.md). Kiểm tra `game/*.rpy` hoặc `game/tl/`.
- Nếu là **Unreal Engine**: Xem [Unreal Guide](./references/unreal_guide.md). Kiểm tra `Content/Localization/` hoặc `Content/Paks/`.
- Nếu là **Direct Text/Config**: Quét các file `.json`, `.csv`, `.po`, `.xml`, `.ini`, `.srt`, `.txt`, `.bak`.

#### 1.2. Trích Xuất & Chuẩn Hoá Dữ Liệu
Chạy script trích xuất để tạo cấu trúc LocaForge chuẩn:
```bash
python3 scripts/locaforge_extract.py "<thư_mục_chứa_text>" Localization_Source
```
Kết quả sẽ được lưu tại:
- `Localization_Source/tables/`: Các bảng text độc lập theo chuyên mục (ví dụ `MainMenu.json`, `UI.json`, `Dialogue.json`, `Item.json`...).
- `Localization_Source/all_strings.json` & `all_strings.csv`: Bảng tổng hợp toàn bộ chuỗi text của game.

#### 1.3. Báo Cáo Quy Chuẩn Cho Người Dùng
Báo cáo rõ cho người dùng cấu trúc cột dữ liệu:
| Tên Cột | Ý Nghĩa | Quy Tắc Bắt Buộc |
| :--- | :--- | :--- |
| `table` | Tên bảng / Chuyên mục | **TUYỆT ĐỐI KHÔNG SỬA** |
| `id` | ID định danh nội bộ game | **TUYỆT ĐỐI KHÔNG SỬA** |
| `key` | Khóa định danh chuỗi | **TUYỆT ĐỐI KHÔNG SỬA** |
| `english` | Văn bản tiếng Anh gốc | Dùng để đối chiếu ngữ cảnh |
| `vietnamese` | Nội dung dịch tiếng Việt | **ĐIỀN BẢN DỊCH VÀO CỘT NÀY** |

---

## 2. Yêu Cầu 2: Tạo Project Trên Web & Đẩy File Source Lên

Khi người dùng ra lệnh:
> *"Tạo project trên web rồi đẩy các file source text mong muốn"*  
> *"Đưa source text lên web LocaForge để dịch"*

### Hành Động Bắt Buộc Của Agent:

#### 2.1. Khởi Tạo Project Trên LocaForge Web
Chạy lệnh tạo dự án trên Supabase Backend của LocaForge:
```bash
python3 scripts/locaforge_sync.py create-project --title "<Tên Game>" --desc "<Mô tả dự án>"
```
Lệnh sẽ in ra `Project ID` và đường link truy cập dự án trên web.

#### 2.2. Đẩy Toàn Bộ Bảng Text Lên Dự Án
Đẩy toàn bộ file trong `Localization_Source/tables/` hoặc các file cụ thể mà người dùng yêu cầu:
```bash
python3 scripts/locaforge_sync.py push-files --project-id "<PROJECT_ID>" --dir Localization_Source/tables
```
Script sẽ tự động:
1. Đăng ký metadata tệp trong `project_files`.
2. Phân tích từng chuỗi văn bản và nạp theo lô (batch) vào `source_strings`.
3. Bảo toàn nguyên vẹn `key`, `table`, `id` và các biến placeholders (`{0}`, `{player_name}`).

#### 2.3. Hướng Dẫn Người Dùng Dịch Thuật
Gửi đường dẫn trực tiếp:
```
🌐 Link dịch thuật: https://locaforge-web.vercel.app/project/<PROJECT_ID>
```
Nêu các tính năng nổi bật:
- **Dịch File AI (Batch Translation)** với Gemini Flash: Dịch liên tục toàn bộ file tự động với 1 click.
- **Bình Chọn & Cộng Tác**: Dễ dàng chia sẻ đường dẫn cho đồng đội vào cùng đóng góp bản dịch.
- **Bảo Toàn Placeholder**: Giữ nguyên thẻ định dạng màu sắc (`<color>`), biến số (`{0}`), mã xuống dòng (`\n`).

---

## 3. Yêu Cầu 3: Cài Việt Hoá Vào Game (Download ZIP, Unpack & Patch)

Khi người dùng ra lệnh:
> *"Tôi đã dịch trên web xong, cài Việt Hoá vào game"*  
> *"Import bản dịch vào game"*  
> *"Tải file ZIP về, giải nén và đóng gói thành file Việt hoá"*

### Hành Động Bắt Buộc Của Agent:

#### 3.1. Tự Động Tải & Nạp Bản Dịch
Nếu có `PROJECT_ID`:
```bash
python3 scripts/locaforge_patch.py --project-id "<PROJECT_ID>"
```
Hoặc nếu người dùng đã có file ZIP xuất từ web:
```bash
python3 scripts/locaforge_patch.py --zip "<Đường_dẫn_file_ZIP>"
```

#### 3.2. Cơ Chế Nạp Bản Dịch Của Script (Tự Động 100%)
1. **Tải File & Giải Nén**: Tải gói ZIP từ LocaForge xuống và giải nén vào vùng đệm staging tạm thời.
2. **Sao Lưu Dự Phòng (Safety Backup)**: Tự động sao lưu tất cả file gốc trước khi sửa vào thư mục `Localization_Backup/`. Đảm bảo người chơi không bao giờ bị hỏng game!
3. **Nạp Chuỗi Tiếng Việt Vào Engine**:
   - **Unity**: Cập nhật file source tables, thực thi kịch bản patch nhúng asset (`apply_vietnamese.py` hoặc `.sh`), hoặc ghi đè vào `StreamingAssets/`.
   - **RPG Maker (MV/MZ)**: Nạp chuỗi tiếng Việt vào `data/*.json` (lời thoại code `401`, tên vật phẩm, mô tả) với mã hoá UTF-8.
   - **Ren'Py**: Tạo và nạp các tệp bản dịch `translate vietnamese strings:` vào `game/tl/vietnamese/`.
   - **Unreal Engine**: Đặt file ngôn ngữ vào `Content/Localization/` hoặc tạo mod pak trong `Content/Paks/~mods/`.
   - **Direct Text/Mod**: Ghi đè file dịch với định dạng gốc được bảo toàn.
4. **Đối Soát & Kiểm Tra Mã Hoá (Sanity Check)**:
   - Quét kiểm tra các ký tự có dấu tiếng Việt (`à, á, ả, ã, ạ, ă, ắ, đ, ê, ơ, ư, ô...`).
   - Kiểm tra không xảy ra hiện tượng vỡ font (Mojibake) hoặc lỗi encoding UTF-8.

#### 3.3. Bàn Giao & Hướng Dẫn Test In-Game
Thông báo kết quả cho người dùng:
- Liệt kê số lượng file và chuỗi văn bản đã nạp thành công.
- Vị trí thư mục sao lưu dự phòng: `Localization_Backup/`.
- Hướng dẫn người dùng khởi động game để chiêm ngưỡng kết quả thực tế.

---

## 4. Yêu Cầu 4: Đóng Gói Bản Cài Đặt Game (.ZIP) & Lưu Trữ Lên Google Drive

Khi người dùng ra lệnh:
> *"Đóng gói bản zip việt hoá này để gửi cho người khác chơi"*  
> *"Đẩy bản zip việt hoá lên web"*  
> *"Tạo bản cài đặt game hoàn chỉnh"*  
> *"Đóng file zip giải nén ra là có việt hoá ngay"*

### Kho Lưu Trữ Mặc Định:
- **Google Drive Hub**: `https://drive.google.com/drive/folders/1epqsQJfXL2fEEHuhoWZ8AyO67LdIXRgi?usp=sharing`
- **Folder ID**: `1epqsQJfXL2fEEHuhoWZ8AyO67LdIXRgi`

### Hành Động Bắt Buộc Của Agent:

#### 4.1. Đóng Gói File ZIP Thành Phẩm Cho Game Thủ
Agent chạy script tự động quét các file đã patch (dựa trên `Localization_Backup/`) và nén theo đúng cây thư mục game:
```bash
python3 scripts/locaforge_patch.py --pack-patch
```
Hoặc chỉ định tên file:
```bash
python3 scripts/locaforge_patch.py --pack-patch --output "<Tên_Game>_Vietnamese_Patch.zip"
```
Script sẽ tự động:
1. Chỉ nén các file game đã thay đổi (`.bundle`, `.json`, `catalog.json`, `game/tl/vietnamese/`).
2. Giữ nguyên 100% cấu trúc thư mục tương đối để game thủ chỉ việc "Extract Here" đè vào thư mục game.
3. Tự động sinh file `Huong_Dan_Cai_Dat.txt` bỏ vào root của ZIP.
4. Báo cáo dung lượng (thường chỉ 1MB - 15MB, nén mức tối đa level 9).

#### 4.2. Bàn Giao Link Tải & Lưu Trữ Lên Google Drive
Sau khi đóng gói xong, Agent gửi báo cáo:
- Tên file ZIP và vị trí lưu trên máy.
- Hướng dẫn đưa lên kho Google Drive chung của LocaForge:
  ```text
  📁 Kho Google Drive: https://drive.google.com/drive/folders/1epqsQJfXL2fEEHuhoWZ8AyO67LdIXRgi?usp=sharing
  ```
- Nếu có `PROJECT_ID`: Agent hỗ trợ gắn link tải Google Drive vào dự án trên web LocaForge.

---

## ⚠️ Quy Tắc Bất Di Bất Dịch (Golden Rules)

1. **Chuẩn 1-Click "Extract & Play"**: Bản ZIP đóng gói cho game thủ phải giải nén đè vào game là chơi được ngay, không bắt game thủ phải cài đặt môi trường lập trình hay cấu hình thủ công.
2. **Tối Ưu Dung Lượng (Zero Bloat)**: Chỉ đóng gói các file thực sự đã được Việt hoá (so khớp từ `Localization_Backup/`). Tuyệt đối không nén toàn bộ thư mục game hoặc file `.exe` nặng.
3. **Tuyệt Đối Không Thay Đổi Key / ID**: Game Engine truy xuất chuỗi văn bản thông qua `id` và `key`. Mọi hành động thay đổi các giá trị này sẽ gây crash game hoặc không hiển thị text.
4. **Bảo Toàn Placeholder**: Các biến số như `{0}`, `{1}`, `%s`, `{player}`, mã màu `<color=#FF0000>` phải được giữ nguyên vẹn trong bản dịch.
5. **Luôn Luôn Backup Trước Khi Patch**: Phải lưu bản sao nguyên gốc vào `Localization_Backup/` để người chơi có thể khôi phục bất cứ lúc nào.
6. **Mã Hoá UTF-8 Chuẩn**: Toàn bộ tệp bản dịch xuất ra và nạp vào phải sử dụng UTF-8 (hoặc UTF-8 with BOM đối với CSV trên Windows) để hiển thị trọn vẹn dấu tiếng Việt.

