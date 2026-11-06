---
name: locaforge
description: >-
  Universal game localization and Vietnamese translation workflow using LocaForge for any game engine (Unity, Unreal Engine, RPG Maker, Ren'Py, Godot, GameMaker, and Direct Text/Config). Activate this skill when the user asks to:
  (0) Kiểm tra game đã có trên web chưa, gửi link dịch thêm, và cài Việt Hoá khi OK ("kiểm tra game trên web", "dịch game này", "Việt hoá game", "OK rồi cài luôn", "cài bản dịch hiện tại"),
  (1) Trích xuất file source text từ game để dịch ("trích xuất file source text", "tìm file text game", "extract game strings", "chuẩn bị file dịch"),
  (2) Tạo project trên web LocaForge và đẩy file source lên ("tạo project trên web", "đẩy file source lên locaforge", "upload bảng dịch lên web"),
  (3) Cài đặt bản dịch Việt hoá vào game từ web hoặc ZIP ("cài Việt Hoá", "import bản dịch vào game", "patch tiếng Việt"),
  (4) Đóng gói bản cài đặt game và đẩy link tải lên project web ("đẩy file zip lên project", "đóng gói bản zip", "tạo file zip cài game").
---

# LocaForge Universal Game Localization Skill

Bộ quy chuẩn và công cụ tự động hóa toàn diện giúp AI Agent và Game Modder thực hiện trọn vẹn quy trình Việt hoá cho **mọi tựa game** thông qua nền tảng LocaForge.

---

## 🧭 Tổng Quan Quy Trình Thông Minh (Smart Workflow)

```
┌────────────────────────────────────────────────────────────────────────┐
│ BƯỚC 0: SMART PRE-CHECK (BẮT BUỘC KIỂM TRA TRÊN WEB TRƯỚC)            │
│ Game Folder ──► [locaforge_sync check-game] ──► Kiểm tra Supabase Web │
│   ├── [ĐÃ CÓ TRÊN WEB] ──► Gửi Link Studio dịch thêm ──► Chờ "OK"     │
│   │                        └── Người dùng gõ "OK" ──► Cài đặt VH luôn!│
│   └── [CHƯA CÓ TRÊN WEB] ──► Tiến hành Bước 1 & 2 bên dưới            │
├────────────────────────────────────────────────────────────────────────┤
│ BƯỚC 1: TRÍCH XUẤT SOURCE TEXT (NẾU CHƯA CÓ TRÊN WEB)                 │
│ Game Folder ──► [locaforge_detect] ──► [locaforge_extract] ──► Source  │
├────────────────────────────────────────────────────────────────────────┤
│ BƯỚC 2: TẠO PROJECT & ĐỒNG BỘ LÊN LOCAFORGE WEB                        │
│ Localization_Source/ ──► [locaforge_sync] ──► Gửi link Web Studio     │
├────────────────────────────────────────────────────────────────────────┤
│ BƯỚC 3: DỊCH XONG / NGƯỜI DÙNG BÁO "OK" ──► CÀI ĐẶT VIỆT HOÁ VÀO GAME │
│ [locaforge_patch --project-id] ──► Tự động kéo bản dịch & patch game! │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 0. Quy Chuẩn Bắt Buộc: Kiểm Tra Game Trên LocaForge Web (Smart Pre-Check)

> [!IMPORTANT]
> **QUY TẮC BẮT BUỘC:** Khi người dùng đưa ra bất kỳ yêu cầu nào liên quan đến **trích xuất bản dịch, tìm file text, tạo project, dịch game, hoặc Việt hoá game**, Agent **PHẢI LUÔN KIỂM TRA XEM GAME ĐÃ CÓ TRÊN WEB CHƯA TRƯỚC KHI LÀM BẤT KỲ ĐIỀU GÌ KHÁC**.

### 0.1. Chạy Lệnh Quét & Đối Soát Web Tự Động
```bash
python3 scripts/locaforge_sync.py check-game .
```
*(Hoặc tra cứu theo tên game cụ thể: `python3 scripts/locaforge_sync.py find-project --title "<Tên Game>" `)*

---

### 0.2. Trường Hợp 1: Game ĐÃ CÓ Trên LocaForge Web
Nếu tìm thấy dự án đã tồn tại trên Web:
1. **KHÔNG** tạo project trùng lặp, **KHÔNG** trích xuất đè tệp làm mất dữ liệu cộng đồng đã đóng góp.
2. **Báo cáo tiến độ chi tiết**: Tên dự án, Project ID, Target Engine, số câu đã dịch / tổng số câu và tỉ lệ hoàn thành (`%`).
3. **Gửi ngay link Web Studio** cho người dùng mở ra kiểm tra hoặc dịch thêm:
   ```
   🌐 Link Web Studio: https://locaforge-web.vercel.app/project/<PROJECT_ID>
   ```
4. **Hướng dẫn người dùng hành động rõ ràng**:
   > *"Game này đã có sẵn trên LocaForge Web với tiến độ dịch là **XX%**. Bạn có thể nhấp vào link Web Studio ở trên để duyệt hoặc dịch thêm các câu còn thiếu (qua AI Gemini hoặc dịch tay).  
   > Khi bạn thấy bản dịch đã **OK** (hoặc sau khi bạn dịch xong), bạn chỉ cần gõ **'OK'** hoặc **'Cài luôn'**, Agent sẽ tự động nạp bản dịch mới nhất vào game ngay lập tức!"*

5. **KHI NGƯỜI DÙNG BÁO "OK", "CÀI LUÔN", "ĐÃ DỊCH XONG", "CÀI VIỆT HOÁ":**
   Agent kích hoạt ngay cơ chế nạp bản dịch tự động:
   ```bash
   python3 scripts/locaforge_patch.py --project-id "<PROJECT_ID>"
   ```
   Lệnh sẽ tự động:
   - Tải toàn bộ bản dịch tiếng Việt mới nhất trực tiếp từ Supabase backend.
   - Sao lưu dữ liệu gốc vào `Localization_Backup/`.
   - Nạp chuỗi tiếng Việt vào đúng engine game (Unity / Ren'Py / RPG Maker / Generic).
   - Kiểm tra mã hoá UTF-8 và thông báo người chơi vào game test ngay!

---

### 0.3. Trường Hợp 2: Game CHƯA CÓ Trên LocaForge Web
Nếu chưa có dự án, Agent tiếp tục thực hiện tuần tự:
1. **Bước 1**: Nhận diện engine & trích xuất source text sang `Localization_Source/` (xem Mục 1).
2. **Bước 2**: Khởi tạo project mới trên web và đẩy các file bảng text lên (xem Mục 2).
3. **Gửi link Web Studio** để người dùng dịch (Gemini Flash Batch 1-click hoặc chỉnh sửa).
4. **Khi người dùng báo "OK"**: Thực hiện nạp bản dịch vào game bằng lệnh `python3 scripts/locaforge_patch.py --project-id "<PROJECT_ID>"`.

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
Chạy lệnh tạo dự án trên Supabase Backend của LocaForge (kèm định dạng engine đã nhận diện):
```bash
python3 scripts/locaforge_sync.py create-project --title "<Tên Game>" --desc "<Mô tả dự án>" --engine "<unity|renpy|rpgmaker|generic>"
```
Lệnh sẽ in ra `Project ID` và đường link truy cập dự án trên web. Web sẽ tự động chọn sẵn định dạng engine tương ứng khi xuất patch.
Nếu muốn cập nhật lại engine cho dự án có sẵn:
```bash
python3 scripts/locaforge_sync.py set-engine --project-id "<PROJECT_ID>" --engine "<unity|renpy|rpgmaker|generic>"
```

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

## 4. Yêu Cầu 4: Đóng Gói Bản Cài Game & Đẩy File ZIP Lên Project

Khi người dùng ra lệnh:
> *"Đã test game xong, đẩy file zip Việt Hoá lên project"*  
> *"Đóng gói bản zip việt hoá này và đẩy lên project"*  
> *"Tạo file zip cài game và gắn link lên web"*

### Hành Động Bắt Buộc Của Agent:

#### 4.1. Đóng Gói Bản Cài Đặt Game (.ZIP) Plug & Play
Chạy lệnh gom các file game đã được patch thành gói cài đặt độc lập:
```bash
python3 scripts/locaforge_patch.py --pack-patch --project-id "<PROJECT_ID>"
```
Lệnh sẽ sinh ra gói `[GameName]_Vietnamese_Patch.zip` chứa cấu trúc thư mục game sẵn sàng sao chép đè kèm theo tệp `HUONG_DAN_CAI_DAT.txt`.

#### 4.2. Tải File ZIP Trực Tiếp Lên Storage Hoặc Gắn Link Web
- **Cách 1: Tải file ZIP thẳng lên LocaForge Cloud Storage (Tự động 100%)**:
  ```bash
  python3 scripts/locaforge_sync.py upload-patch --project-id "<PROJECT_ID>" "<File_Patch.zip>"
  ```
  Script sẽ đẩy file nén lên bucket Storage công khai và tự động cập nhật direct download URL vào dự án.
- **Cách 2: Gắn URL có sẵn (Google Drive / Direct link)**:
  ```bash
  python3 scripts/locaforge_sync.py set-patch --project-id "<PROJECT_ID>" --url "<URL_GDRIVE_HOẶC_DIRECT_ZIP>"
  ```
- Khi hoàn tất, nút **"Bản Cài Game (.ZIP)"** màu xanh ngọc trên LocaForge Web sẽ tự động kích hoạt để cộng đồng người chơi có thể tải về cài đặt 1-click.

---

## ⚠️ Quy Tắc Bất Di Bất Dịch (Golden Rules)

1. **Tuyệt Đối Không Thay Đổi Key / ID**: Game Engine truy xuất chuỗi văn bản thông qua `id` và `key`. Mọi hành động thay đổi các giá trị này sẽ gây crash game hoặc không hiển thị text.
2. **Bảo Toàn Placeholder**: Các biến số như `{0}`, `{1}`, `%s`, `{player}`, mã màu `<color=#FF0000>` phải được giữ nguyên vẹn trong bản dịch.
3. **Luôn Luôn Backup Trước Khi Patch**: Phải lưu bản sao nguyên gốc vào `Localization_Backup/` để người chơi có thể khôi phục bất cứ lúc nào.
4. **Mã Hoá UTF-8 Chuẩn**: Toàn bộ tệp bản dịch xuất ra và nạp vào phải sử dụng UTF-8 (hoặc UTF-8 with BOM đối với CSV trên Windows) để hiển thị trọn vẹn dấu tiếng Việt.

