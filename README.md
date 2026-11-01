# 🎮 LocaForge Universal Game Localization Skill

> **Biến Antigravity AI Agent thành Chuyên Gia Việt Hoá Game Tự Động Cho Mọi Tựa Game**  
> Kết nối liền mạch giữa thư mục Game cục bộ và nền tảng dịch thuật cộng đồng **LocaForge Web**.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Antigravity Compatible](https://img.shields.io/badge/Antigravity-Skill-indigo.svg)](https://antigravity.google)
[![LocaForge](https://img.shields.io/badge/Platform-LocaForge-cyan.svg)](https://locaforge-web.vercel.app)

---

## 🚀 Tính Năng Nổi Bật

- 🔍 **Tự động nhận diện Game Engine**: Quét và xác định cấu trúc game (Unity, Unreal Engine, RPG Maker MV/MZ/VX/XP, Ren'Py, Godot, GameMaker, Mod Text).
- 📦 **Trích xuất & Chuẩn hoá nguồn text**: Bóc tách chuỗi ngôn ngữ từ file game sang định dạng LocaForge (`.json`, `.csv`, `.po`, `.xml`, `.ini`, `.srt`, `.txt`, `.bak`) mà không làm thay đổi các khóa `id`, `key`, `table` của engine.
- ☁️ **Đồng bộ 1-Click lên LocaForge Web**: Tự động tạo dự án và đẩy hàng nghìn chuỗi văn bản lên web để dịch bằng **AI Gemini Flash** hoặc mời cộng đồng cùng dịch thuật.
- ⚡ **Tự động tải & Cài đặt Patch Việt Hoá**: Tải gói ZIP bản dịch từ web về, tự động giải nén, sao lưu file gốc an toàn (`Localization_Backup/`), nạp chuỗi tiếng Việt vào game và kiểm tra mã hoá UTF-8.

---

## 📥 Hướng Dẫn Cài Đặt (Installation)

### Cách 1: Cài đặt cho 1 dự án game cụ thể
Mở terminal tại thư mục game của bạn và chạy lệnh:
```bash
git clone https://github.com/vucuonghd96s/locaforge-skill.git .agents/skills/locaforge
```

### Cách 2: Cài đặt Toàn Cục (Global) cho Antigravity IDE
Cài đặt một lần, dùng cho tất cả mọi game mở trong IDE:
```bash
# macOS / Linux:
git clone https://github.com/vucuonghd96s/locaforge-skill.git ~/.gemini/config/skills/locaforge

# Windows (PowerShell):
git clone https://github.com/vucuonghd96s/locaforge-skill.git "$HOME\.gemini\config\skills\locaforge"
```

---

## 🕹️ Cách Sử Dụng Với AI Agent

Sau khi cài đặt Skill, mở bất kỳ thư mục game nào trong **Antigravity IDE** và trò chuyện trực tiếp với AI:

### Bước 1: Yêu cầu trích xuất text
> 💬 **Bạn gõ:**  
> *"Tìm File source text để tôi có thể Việt Hoá"*  
> Hoặc:  
> *"Trích xuất file source text để dịch, tinh chỉnh sang dạng JSON"*

🤖 **AI Agent sẽ:**
1. Chạy `locaforge_detect.py` phát hiện loại engine và các file ngôn ngữ.
2. Chạy `locaforge_extract.py` tạo thư mục `Localization_Source/tables/` chứa các bảng text độc lập và file tổng hợp `all_strings.json`.

---

### Bước 2: Yêu cầu tạo project trên web và đẩy source
> 💬 **Bạn gõ:**  
> *"Tạo project trên web rồi đẩy các file source text mong muốn"*

🤖 **AI Agent sẽ:**
1. Tạo dự án mới trên LocaForge Cloud qua `locaforge_sync.py create-project`.
2. Đẩy các file trong `Localization_Source/tables/` lên dự án.
3. Gửi lại đường dẫn web: `https://locaforge-web.vercel.app/project/<ID>` để bạn và bạn bè có thể vào dịch ngay hoặc bấm **Dịch File AI (Batch Translation)**.

---

### Bước 3: Yêu cầu cài Việt Hoá vào game
> 💬 **Bạn gõ:**  
> *"Tôi đã dịch trên web xong, cài Việt Hoá vào game"*  
> Hoặc:  
> *"Tải file ZIP về, giải nén và đóng gói thành file Việt hoá"*

🤖 **AI Agent sẽ:**
1. Tự động tải gói ZIP bản dịch từ LocaForge xuống máy tính.
2. Tạo thư mục sao lưu an toàn `Localization_Backup/` chứa toàn bộ file gốc.
3. Nạp chuỗi tiếng Việt vào cấu trúc engine (Unity asset bundle, RPG Maker data JSON, Ren'Py `.rpy`, hoặc file mod text).
4. Kiểm tra đối soát mã hoá UTF-8 để đảm bảo không lỗi font trong game.

---

## 📁 Cấu Trúc Thư Mục Skill

```
locaforge-skill/
├── SKILL.md                          # Hướng dẫn chính thức cho AI Agent
├── README.md                         # Tài liệu hướng dẫn sử dụng
├── install.sh                        # Script cài đặt cho macOS / Linux
├── install.ps1                       # Script cài đặt cho Windows PowerShell
├── scripts/                          # Bộ công cụ tự động hóa (Pure Python 3)
│   ├── locaforge_detect.py           # Quét nhận diện Engine & vị trí tệp
│   ├── locaforge_extract.py          # Trích xuất chuỗi sang định dạng LocaForge
│   ├── locaforge_sync.py             # CLI đồng bộ với LocaForge Web / Supabase
│   └── locaforge_patch.py            # Nạp bản dịch, backup & kiểm tra UTF-8
├── references/                       # Tài liệu kỹ thuật chuyên sâu theo engine
│   ├── unity_guide.md                # Unity Engine (AssetBundle, I2Loc, TextAsset)
│   ├── rpgmaker_guide.md             # RPG Maker (MV, MZ, VX Ace, XP)
│   ├── renpy_guide.md                # Ren'Py Visual Novel
│   ├── unreal_guide.md               # Unreal Engine 4 / 5 (.locres, .pak)
│   └── generic_formats.md            # Đặc tả 9 định dạng tệp LocaForge
└── examples/
    ├── sample_prompts.md             # Mẫu câu lệnh tương tác với AI
    └── sample_game_table.json        # Mẫu tệp JSON chuẩn LocaForge
```

---

## 🎯 Danh Sách Game Engine Được Hỗ Trợ

| Engine | Dấu Hiệu Nhận Diện | Định Dạng Trích Xuất | Cơ Chế Nạp Patch |
| :--- | :--- | :--- | :--- |
| **Unity** | `*_Data/`, `StreamingAssets/` | JSON / CSV / TextAsset | Script Patch / StreamingAssets / AssetBundle |
| **RPG Maker MV/MZ** | `data/*.json`, `www/data/*.json` | JSON Table | Ghi đè UTF-8 có backup vào `data/` |
| **Ren'Py** | `game/*.rpy`, `game/*.rpa` | JSON / RPY | Tự sinh `game/tl/vietnamese/*.rpy` |
| **Unreal Engine** | `Content/Localization/`, `.pak` | Locres / PO / CSV | Thư mục `Content/Paks/~mods/` |
| **Godot** | `project.godot`, `*.pck` | PO / CSV | File PO translation |
| **GameMaker** | `data.win`, `strings.csv` | CSV / Key-Value | Ghi đè bảng chuỗi ngôn ngữ |
| **Direct Text/Mod** | `.json`, `.csv`, `.po`, `.xml`, `.ini`, `.srt` | Định dạng gốc | Ghi đè trực tiếp có backup an toàn |

---

## 🔒 Cam Kết An Toàn & Toàn Vẹn

1. **Bảo tồn 100% Khóa Engine**: Không bao giờ thay đổi các trường cấu trúc `id`, `key`, `table`.
2. **Bảo toàn Placeholder**: Tự động giữ nguyên biến số `{0}`, `{player_name}`, mã màu `<color=...>`, mã xuống dòng `\n`.
3. **Sao lưu nguyên bản (Fail-safe)**: Mọi thao tác patch đều sao lưu tệp gốc vào `Localization_Backup/` trước khi sửa đổi.
4. **Không cần cài đặt thư viện nặng**: Bộ công cụ viết hoàn toàn bằng Python Standard Library (`urllib`, `json`, `zipfile`, `csv`), không cần `pip install` phức tạp.

---

## 📜 Giấy Phép (License)
Dự án được phân phối dưới giấy phép **MIT License**.
Phát triển bởi đội ngũ **LocaForge** dành cho cộng đồng Việt hoá Game.
