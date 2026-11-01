# LocaForge Supported Formats Specification

LocaForge hỗ trợ 9 định dạng tệp chuẩn công nghiệp modding và game localization.

---

## 1. JSON (`.json`)
Cấu trúc danh sách đối tượng chuẩn game:
```json
[
  {
    "table": "MainMenu",
    "id": 128057131008,
    "key": "new_game",
    "english": "New Game",
    "vietnamese": "Trò Chơi Mới"
  }
]
```
Hoặc đối tượng Key-Value phẳng / lồng nhau:
```json
{
  "menu": {
    "play": "Play Game",
    "settings": "Settings"
  }
}
```

---

## 2. CSV Bảng Tính (`.csv`)
Chuẩn RFC 4180 tương thích Excel & Google Sheets. Cột bắt buộc:
`table,id,key,english,vietnamese`
- Dùng mã hoá `UTF-8 with BOM` nếu mở bằng Excel trên Windows để không bị bể font dấu tiếng Việt.

---

## 3. GNU Gettext PO (`.po`)
Chuẩn bản địa hoá mã nguồn mở phổ biến trong game:
```po
msgctxt "menu.start"
msgid "Start Game"
msgstr "Bắt Đầu Trò Chơi"
```

---

## 4. XML Resources (`.xml`)
Chuẩn chuỗi tài nguyên XML cho Unity, Unreal Engine & Android:
```xml
<resources>
  <string name="app_name">LocaForge</string>
  <string name="btn_play">Chơi Ngay</string>
</resources>
```

---

## 5. Key-Value & Cấu Hình INI (`.ini`, `.lang`, `.properties`)
```ini
[Interface]
btn_start=Bắt Đầu
btn_quit=Thoát
```

---

## 6. Phụ Đề Video / Cutscene SRT (`.srt`)
```srt
1
00:01:20,000 --> 00:01:23,500
Xin chào người du hành thời gian!
```

---

## 7. Văn Bản Thuần TXT (`.txt`)
Chỉ chứa các dòng văn bản đơn lẻ, mỗi dòng là một câu thoại.

---

## 8. Tệp Sao Lưu BAK (`.bak`)
Tệp sao lưu chuỗi văn bản hoặc bản địa hóa định dạng gốc `.bak` được khôi phục hoặc so khớp với file đang dịch.

---

## 9. Định Dạng Gốc (Original In-Place Engine)
LocaForge hỗ trợ `UniversalInPlaceEngine` ghi nhớ cấu trúc offset của file nạp vào và thay thế chuỗi dịch trực tiếp vào vị trí tương ứng mà không làm xáo trộn format gốc của game engine.

