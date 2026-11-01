# Mẫu Câu Lệnh (Prompt) Dành Cho Gamer & AI Agent

Khi người dùng mở thư mục game trong Antigravity IDE, họ có thể sử dụng các câu lệnh sau để kích hoạt bộ Skill LocaForge:

---

## 1. Yêu cầu trích xuất file source text
> **User Prompt:**  
> *"Tìm File source text để tôi có thể Việt Hoá"*  
> Hoặc:  
> *"Trích xuất file source text để dịch, xuất sang định dạng JSON"*  
> Hoặc:  
> *"Quét thư mục game này xem file ngôn ngữ nằm ở đâu"*

**Hành vi của AI Agent:**
1. Chạy `python3 scripts/locaforge_detect.py .` để phát hiện engine và vị trí file.
2. Báo cáo cấu trúc cho người dùng (ví dụ: Unity AssetBundle, RPG Maker data JSON, Ren'Py rpy, hoặc Text direct).
3. Chạy `python3 scripts/locaforge_extract.py <path> Localization_Source` để trích xuất text chuẩn hoá.
4. Liệt kê các bảng text vừa trích xuất và nhắc nhở người dùng không sửa cột `table`, `id`, `key`.

---

## 2. Yêu cầu tạo project trên web và đẩy file lên LocaForge
> **User Prompt:**  
> *"Tạo project trên web rồi đẩy các file source text mong muốn lên"*  
> Hoặc:  
> *"Đưa toàn bộ bảng text trong Localization_Source lên web LocaForge để dịch"*  
> Hoặc:  
> *"Tạo dự án dịch tên Cyberpunk Shopkeeper Sim trên LocaForge và upload file"*

**Hành vi của AI Agent:**
1. Chạy `python3 scripts/locaforge_sync.py create-project --title "<Tên Game>"`
2. Chạy `python3 scripts/locaforge_sync.py push-files --project-id <id> --dir Localization_Source/tables`
3. Trả về liên kết web: `https://locaforge-web.vercel.app/project/<id>`
4. Hướng dẫn người dùng có thể chia sẻ link cho bạn bè cùng dịch, hoặc bấm tính năng **Dịch File AI (Batch Translation)** với Gemini 3.8 Flash.

---

## 3. Yêu cầu cài đặt Việt Hoá vào game
> **User Prompt:**  
> *"Tôi đã dịch trên web xong, cài Việt Hoá vào game"*  
> Hoặc:  
> *"Import bản dịch vào game"*  
> Hoặc:  
> *"Tải file ZIP về, giải nén và đóng gói thành file Việt hoá cho game"*

**Hành vi của AI Agent:**
1. Tự động tải file ZIP từ LocaForge bằng `python3 scripts/locaforge_sync.py export-zip --project-id <id>` (hoặc tìm file ZIP sẵn có).
2. Chạy `python3 scripts/locaforge_patch.py --project-id <id>` (hoặc `--zip <path>`).
3. Tự động backup file gốc vào `Localization_Backup/`.
4. Nạp đè chuỗi tiếng Việt vào cấu trúc game và đối soát mã hoá UTF-8.
5. Thông báo người dùng khởi động game để chiêm ngưỡng kết quả thực tế.

---

## 4. Yêu cầu đóng gói & đẩy file ZIP lên project
> **User Prompt:**  
> *"Đẩy file zip lên project"*  
> Hoặc:  
> *"Đóng gói bản zip việt hoá này và đẩy lên project"*  
> Hoặc:  
> *"Tạo file zip cài game và gắn link lên web"*  
> Hoặc:  
> *"Upload file zip patch lên project"*  
> Hoặc:  
> *"Đẩy file zip Localization_Source.zip lên dự án"*

**Hành vi của AI Agent:**
1. Nếu cần đóng gói bản cài game: Chạy `python3 scripts/locaforge_patch.py --pack-patch --project-id <id>` để gom toàn bộ file đã dịch theo chuẩn Plug & Play.
2. Hướng dẫn lưu file ZIP vào Google Drive Hub: `https://drive.google.com/drive/folders/1epqsQJfXL2fEEHuhoWZ8AyO67LdIXRgi?usp=sharing`.
3. Gắn trực tiếp liên kết tải ZIP vào dự án trên Web:
   `python3 scripts/locaforge_sync.py set-patch --project-id <id> --url "<LINK_GDRIVE_HOAC_DIRECT_ZIP>"`
   Kích hoạt nút **"Bản Cài Game (.ZIP)"** màu xanh ngọc trên LocaForge Web.
4. Nếu người dùng muốn đẩy gói ZIP chứa file text nguồn:
   Chạy `python3 scripts/locaforge_sync.py push-zip --project-id <id> "<duong_dan_file.zip>"` để bung nén và đẩy toàn bộ chuỗi lên web.

