#!/usr/bin/env python3
"""
LocaForge Cloud Sync CLI
Communicates directly with LocaForge Web / Supabase Backend.
Zero external pip dependencies (Pure standard library urllib).

Commands:
  create-project  --title "..." [--desc "..."] [--genre "..."]
  push-files      --project-id "..." [--dir Localization_Source/tables] [files...]
  export-zip      --project-id "..." [--output Patch.zip]
  status          --project-id "..."
  list-projects
"""

import os
import sys
import json
import uuid
import zipfile
import csv
import io
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

DEFAULT_SUPABASE_URL = os.environ.get(
    "LOCAFORGE_SUPABASE_URL",
    "https://eyksqdefsztuaknhxyko.supabase.co"
)
DEFAULT_SUPABASE_KEY = os.environ.get(
    "LOCAFORGE_SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV5a3NxZGVmc3p0dWFrbmh4eWtvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTIzMjAwNDQsImV4cCI6MjEwNzg5NjA0NH0.TO7WQgf6HkA0V10jLMskax8jzZQkidyk3szBGEiXGwc"
)
DEFAULT_SUPABASE_SERVICE_KEY = os.environ.get(
    "LOCAFORGE_SUPABASE_SERVICE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV5a3NxZGVmc3p0dWFrbmh4eWtvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MjMyMDA0NCwiZXhwIjoyMTA3ODk2MDQ0fQ.R9sDhzGmRimZ64umJ0a7R-XNZvN4Lk2ghM7qklAqGww"
)
DEFAULT_WEB_URL = os.environ.get(
    "LOCAFORGE_WEB_URL",
    "https://locaforge-web.vercel.app"
)
DEFAULT_AVATAR_ID = "87877a37-4ff2-4673-a604-e51185f77099"


class LocaForgeSync:
    def __init__(self, supabase_url: str = DEFAULT_SUPABASE_URL, supabase_key: str = DEFAULT_SUPABASE_KEY, service_key: str = DEFAULT_SUPABASE_SERVICE_KEY):
        self.base_url = supabase_url.rstrip("/")
        self.key = supabase_key
        self.service_key = service_key
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def _request(self, endpoint: str, method: str = "GET", data: Optional[Any] = None) -> Any:
        url = f"{self.base_url}/rest/v1/{endpoint}"
        body = json.dumps(data).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=body, headers=self.headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                res_bytes = resp.read()
                if not res_bytes:
                    return None
                return json.loads(res_bytes.decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {e.code} on {method} {endpoint}: {err_body}")

    def list_projects(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._request(f"projects?select=id,title,description,created_at,download_count&order=created_at.desc&limit={limit}")

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        res = self._request(f"projects?select=*,project_files(*)&id=eq.{project_id}&limit=1")
        return res[0] if res else None

    def find_projects(self, title_query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find existing projects on LocaForge Web matching the title query."""
        clean_q = title_query.strip()
        if not clean_q:
            return []

        enc_q = urllib.parse.quote(clean_q)
        endpoint = f"projects?select=*,project_files(id,file_name)&title=ilike.*{enc_q}*&order=created_at.desc&limit={limit}"
        matches = self._request(endpoint) or []

        # If no match and query has multiple words, try matching with individual words
        if not matches and len(clean_q.split()) > 1:
            words = [w for w in clean_q.split() if len(w) > 2]
            for w in words:
                enc_w = urllib.parse.quote(w)
                res = self._request(
                    f"projects?select=*,project_files(id,file_name)&title=ilike.*{enc_w}*&order=created_at.desc&limit={limit}"
                )
                for r in (res or []):
                    if not any(m["id"] == r["id"] for m in matches):
                        matches.append(r)
                if matches:
                    break

        return matches

    def check_game_directory(self, game_dir: str = ".") -> Dict[str, Any]:
        """Inspects game folder to detect potential game titles and checks if it exists on LocaForge Web."""
        root = Path(game_dir).resolve()
        candidate_titles: List[str] = []

        # 1. From Unity *_Data folder
        for d in list(root.glob("*_Data")) + list(root.glob("*/*_Data")):
            title = d.name[:-5].strip()
            if title and title not in candidate_titles:
                candidate_titles.append(title)

        # 2. From Mac .app bundle
        for app in list(root.glob("*.app")) + list(root.glob("*/*.app")):
            title = app.stem.strip()
            if title and title not in candidate_titles:
                candidate_titles.append(title)

        # 3. From Windows .exe files
        for exe in root.glob("*.exe"):
            stem = exe.stem.strip()
            if stem.lower() not in {
                "unitycrashhandler64", "unitycrashhandler32", "unins000",
                "setup", "dxwebsetup", "install"
            }:
                if stem not in candidate_titles:
                    candidate_titles.append(stem)

        # 4. From RPG Maker package.json
        for pkg_candidate in [root / "package.json", root / "www" / "package.json"]:
            if pkg_candidate.exists():
                try:
                    with open(pkg_candidate, "r", encoding="utf-8") as f:
                        pkg_data = json.load(f)
                        name = pkg_data.get("name") or pkg_data.get("title")
                        if name and str(name).strip() not in candidate_titles:
                            candidate_titles.append(str(name).strip())
                except Exception:
                    pass

        # 5. From Ren'Py options.rpy or script.rpy
        game_sub = root / "game"
        if game_sub.exists():
            for rpy in game_sub.glob("*.rpy"):
                try:
                    content = rpy.read_text(encoding="utf-8", errors="ignore")
                    for line in content.splitlines():
                        if "config.name" in line and "=" in line:
                            val = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if val and val not in candidate_titles:
                                candidate_titles.append(val)
                                break
                except Exception:
                    pass

        # 6. Fallback: current directory name
        dir_name = root.name.strip()
        if dir_name and dir_name not in candidate_titles and dir_name not in {
            "Desktop", "project", "Downloads", "src", "bin"
        }:
            candidate_titles.append(dir_name)

        matched_projects: List[Dict[str, Any]] = []
        seen_ids = set()
        for cand in candidate_titles:
            results = self.find_projects(cand, limit=3)
            for p in results:
                if p["id"] not in seen_ids:
                    seen_ids.add(p["id"])
                    matched_projects.append(p)

        return {
            "game_dir": str(root),
            "candidate_titles": candidate_titles,
            "detected_game_name": candidate_titles[0] if candidate_titles else root.name,
            "matched_projects": matched_projects,
            "exists_on_web": len(matched_projects) > 0,
        }

    def create_project(self, title: str, description: str = "", user_id: Optional[str] = None, target_engine: str = "generic") -> Dict[str, Any]:
        proj_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        clean_engine = (target_engine or "generic").strip().lower()
        if clean_engine not in {"unity", "renpy", "rpgmaker", "generic"}:
            clean_engine = "generic"

        payload = {
            "id": proj_id,
            "title": title.strip(),
            "description": description.strip() if description else f"Localization project for {title}",
            "avatar_id": DEFAULT_AVATAR_ID,
            "created_at": now,
            "updated_at": now,
            "download_count": 0,
            "target_engine": clean_engine,
        }
        if user_id:
            payload["user_id"] = user_id

        res = self._request("projects", method="POST", data=payload)
        return res[0] if res else payload

    def set_target_engine(self, project_id: str, target_engine: str) -> None:
        clean_engine = (target_engine or "generic").strip().lower()
        if clean_engine not in {"unity", "renpy", "rpgmaker", "generic"}:
            clean_engine = "generic"

        url = f"{self.base_url}/rest/v1/projects?id=eq.{project_id}"
        body = json.dumps({"target_engine": clean_engine}).encode("utf-8")
        headers = dict(self.headers)
        headers["Prefer"] = "return=minimal"
        req = urllib.request.Request(url, data=body, headers=headers, method="PATCH")
        try:
            with urllib.request.urlopen(req) as resp:
                pass
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {e.code} on PATCH projects target_engine: {err_body}")

    def push_file(self, project_id: str, file_path: str, folder_path: str = "") -> Dict[str, Any]:
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        file_id = str(uuid.uuid4())
        file_name = path.name
        ext = path.suffix.lower().lstrip(".") or "json"
        now = datetime.now(timezone.utc).isoformat()

        # 1. Register in project_files
        file_payload = {
            "id": file_id,
            "project_id": project_id,
            "file_name": file_name,
            "folder_path": folder_path,
            "format": ext,
            "created_at": now,
            "updated_at": now,
        }
        self._request("project_files", method="POST", data=file_payload)

        # 2. Parse source strings from file
        strings = self._parse_file_strings(path, file_id)

        # 3. Batch insert into source_strings (chunks of 100)
        chunk_size = 100
        inserted_count = 0
        for i in range(0, len(strings), chunk_size):
            chunk = strings[i:i + chunk_size]
            self._request("source_strings", method="POST", data=chunk)
            inserted_count += len(chunk)

        return {
            "file_id": file_id,
            "file_name": file_name,
            "format": ext,
            "strings_count": inserted_count,
        }

    def _parse_file_strings(self, path: Path, file_id: str) -> List[Dict[str, Any]]:
        strings = []
        ext = path.suffix.lower()

        if ext == ".json":
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = []

            if isinstance(data, list):
                for idx, item in enumerate(data):
                    if isinstance(item, dict):
                        k = str(item.get("key", f"str_{idx}"))
                        eng = str(item.get("english") or item.get("source") or item.get("original") or "")
                        ctx = str(item.get("table", ""))
                        if eng.strip():
                            strings.append({
                                "id": str(uuid.uuid4()),
                                "file_id": file_id,
                                "key": k,
                                "original_text": eng,
                                "context_note": ctx or None,
                                "order_index": idx,
                            })
            elif isinstance(data, dict):
                idx = 0
                for k, v in data.items():
                    if isinstance(v, str) and v.strip():
                        strings.append({
                            "id": str(uuid.uuid4()),
                            "file_id": file_id,
                            "key": k,
                            "original_text": v,
                            "context_note": None,
                            "order_index": idx,
                        })
                        idx += 1

        elif ext == ".csv":
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames or []
                eng_col = next((c for c in fieldnames if c.lower() in {"english", "source", "original", "text"}), None)
                key_col = next((c for c in fieldnames if c.lower() in {"key", "id", "name"}), None)
                table_col = next((c for c in fieldnames if c.lower() in {"table", "category"}), None)

                if not eng_col and len(fieldnames) >= 2:
                    eng_col = fieldnames[1]
                if not key_col and len(fieldnames) >= 1:
                    key_col = fieldnames[0]

                for idx, row in enumerate(reader):
                    eng = row.get(eng_col, "") if eng_col else ""
                    k = row.get(key_col, f"row_{idx}") if key_col else f"row_{idx}"
                    ctx = row.get(table_col, "") if table_col else None
                    if eng and eng.strip():
                        strings.append({
                            "id": str(uuid.uuid4()),
                            "file_id": file_id,
                            "key": k,
                            "original_text": eng,
                            "context_note": ctx or None,
                            "order_index": idx,
                        })

        return strings

    def get_project_stats(self, project_id: str) -> Dict[str, Any]:
        proj = self.get_project(project_id)
        if not proj:
            raise ValueError(f"Project not found: {project_id}")

        files = proj.get("project_files", [])
        file_ids = [f["id"] for f in files]

        total_strings = 0
        translated_count = 0

        for fid in file_ids:
            offset = 0
            page_size = 1000
            while True:
                batch = self._request(
                    f"source_strings?select=id,translations(id)&file_id=eq.{fid}&offset={offset}&limit={page_size}"
                )
                if not batch:
                    break
                total_strings += len(batch)
                for item in batch:
                    trans = item.get("translations") or []
                    if len(trans) > 0:
                        translated_count += 1
                if len(batch) < page_size:
                    break
                offset += page_size

        pct = round((translated_count / total_strings * 100), 1) if total_strings > 0 else 0
        return {
            "project_id": project_id,
            "title": proj.get("title", ""),
            "total_files": len(files),
            "total_strings": total_strings,
            "translated_strings": translated_count,
            "completion_rate": pct,
        }

    def export_translated_zip(self, project_id: str, output_zip: Optional[str] = None) -> str:
        proj = self.get_project(project_id)
        if not proj:
            raise ValueError(f"Project not found: {project_id}")

        title = proj.get("title", "Project").replace(" ", "_")
        zip_path = Path(output_zip or f"{title}_Vietnamese_Patch.zip")

        files = proj.get("project_files", [])
        if not files:
            raise ValueError("Project has no files to export.")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_info in files:
                fid = file_info["id"]
                fname = file_info["file_name"]
                folder = (file_info.get("folder_path") or "").strip().strip("/")

                # Fetch all source strings with pagination
                source_strings = []
                offset = 0
                page_size = 1000
                while True:
                    batch = self._request(f"source_strings?select=id,key,original_text,context_note,order_index&file_id=eq.{fid}&order=order_index.asc&offset={offset}&limit={page_size}")
                    if not batch:
                        break
                    source_strings.extend(batch)
                    if len(batch) < page_size:
                        break
                    offset += page_size

                if not source_strings:
                    continue

                # Fetch translations for these strings
                s_ids = [s["id"] for s in source_strings]
                translations_map: Dict[str, str] = {}
                for i in range(0, len(s_ids), 100):
                    batch = s_ids[i:i + 100]
                    ids_str = ",".join(batch)
                    t_res = self._request(f"translations?select=source_id,translated_text&lang=eq.vi&order=upvotes.desc&source_id=in.({ids_str})")
                    for t in (t_res or []):
                        sid = t["source_id"]
                        if sid not in translations_map:
                            translations_map[sid] = t.get("translated_text", "")

                # Construct translated content
                file_ext = Path(fname).suffix.lower()
                archive_name = f"{folder}/{fname}" if folder else fname

                if file_ext == ".json":
                    # Check if original was list or dict
                    export_list = []
                    for s in source_strings:
                        sid = s["id"]
                        vi_text = translations_map.get(sid, s["original_text"])
                        export_list.append({
                            "table": s.get("context_note") or Path(fname).stem,
                            "key": s["key"],
                            "english": s["original_text"],
                            "vietnamese": vi_text,
                        })
                    json_str = json.dumps(export_list, indent=2, ensure_ascii=False)
                    zf.writestr(archive_name, json_str.encode("utf-8"))

                elif file_ext == ".csv":
                    output = io.StringIO()
                    writer = csv.DictWriter(output, fieldnames=["table", "key", "english", "vietnamese"])
                    writer.writeheader()
                    for s in source_strings:
                        sid = s["id"]
                        vi_text = translations_map.get(sid, s["original_text"])
                        writer.writerow({
                            "table": s.get("context_note") or Path(fname).stem,
                            "key": s["key"],
                            "english": s["original_text"],
                            "vietnamese": vi_text,
                        })
                    zf.writestr(archive_name, output.getvalue().encode("utf-8-sig"))

                else:
                    # Generic Key-Value
                    lines = []
                    for s in source_strings:
                        sid = s["id"]
                        vi_text = translations_map.get(sid, s["original_text"])
                        lines.append(f"{s['key']}={vi_text}")
                    zf.writestr(archive_name, "\n".join(lines).encode("utf-8"))

        return str(zip_path.resolve())

    def set_patch_url(self, project_id: str, patch_url: str) -> Dict[str, Any]:
        """Updates the patch download URL on the project to enable the web download button"""
        payload = {"patch_url": patch_url.strip()}
        res = self._request(f"projects?id=eq.{project_id}", method="PATCH", data=payload)
        return res[0] if res else payload

    def upload_patch(self, project_id: str, zip_path: str) -> str:
        """Uploads a game patch ZIP to Supabase Storage and updates project patch_url"""
        zp = Path(zip_path).resolve()
        if not zp.exists():
            raise FileNotFoundError(f"File not found: {zp}")

        with open(zp, "rb") as f:
            data = f.read()

        object_name = f"{project_id}/{zp.name}"
        url = f"{self.base_url}/storage/v1/object/patches/{object_name}"
        headers = {
            "apikey": self.service_key or self.key,
            "Authorization": f"Bearer {self.service_key or self.key}",
            "Content-Type": "application/zip",
            "x-upsert": "true",
        }
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as resp:
                pass
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Storage upload failed: {e.code} {e.read().decode()}")

        public_url = f"{self.base_url}/storage/v1/object/public/patches/{object_name}"
        self.set_patch_url(project_id, public_url)
        return public_url

    def push_zip(self, project_id: str, zip_path: str) -> Dict[str, Any]:
        """Unpacks a source ZIP and pushes all translatable tables/files to the project"""
        zp = Path(zip_path).resolve()
        if not zp.exists():
            raise FileNotFoundError(f"ZIP file not found: {zp}")

        temp_dir = zp.parent / f".locaforge_unzip_{uuid.uuid4().hex[:8]}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(zp, "r") as zf:
                zf.extractall(temp_dir)

            exts = {".json", ".csv", ".po", ".xml", ".ini", ".txt"}
            pushed_files = []
            total_strings = 0
            for root, _, files in os.walk(temp_dir):
                for f in sorted(files):
                    fp = Path(root) / f
                    if fp.suffix.lower() in exts:
                        res = self.push_file(project_id, str(fp))
                        pushed_files.append(res)
                        total_strings += res["strings_count"]
                        print(f"  ✅ Uploaded {res['file_name']} ({res['strings_count']} strings)")

            return {
                "project_id": project_id,
                "total_files": len(pushed_files),
                "total_strings": total_strings,
            }
        finally:
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        print("Usage: locaforge_sync.py <command> [options]")
        print("\nCommands:")
        print("  check-game     [--dir <dir>]                                              (Smart pre-check: scans game & checks web)")
        print("  find-project   --title <title>                                            (Find existing projects on web)")
        print("  list-projects                                                             (List recent projects)")
        print("  create-project --title <title> [--desc <desc>] [--engine <engine>]        (Create new project)")
        print("  set-engine     --project-id <id> --engine <unity|renpy|rpgmaker|generic>")
        print("  push-files     --project-id <id> [--dir <dir>] [file1 file2 ...]")
        print("  status         --project-id <id>")
        print("  export-zip     --project-id <id> [--output <file.zip>]")
        print("  set-patch      --project-id <id> --url <url>")
        print("  upload-patch   --project-id <id> <file.zip>")
        sys.exit(0)

    cmd = sys.argv[1]
    sync = LocaForgeSync()

    if cmd == "check-game":
        game_dir = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else "."
        for i, arg in enumerate(sys.argv):
            if arg in {"--dir", "-d"} and i + 1 < len(sys.argv):
                game_dir = sys.argv[i + 1]

        print("🔍 Đang quét thư mục game và đối soát trên LocaForge Web...")
        check_res = sync.check_game_directory(game_dir)
        det_name = check_res["detected_game_name"]
        matches = check_res["matched_projects"]

        print("\n🎮 ================================================================")
        print("   LOCAFORGE GAME PRE-CHECK & WEB VERIFICATION")
        print("================================================================\n")
        print(f"📁 Thư mục game : {check_res['game_dir']}")
        print(f"🎯 Nhận diện    : {det_name}")
        if check_res["candidate_titles"]:
            print(f"🔎 Từ khóa quét : {', '.join(check_res['candidate_titles'])}")

        if matches:
            print(f"\n✨ ĐÃ TÌM THẤY {len(matches)} DỰ ÁN TRÊN LOCAFORGE WEB!\n")
            for idx, p in enumerate(matches, 1):
                pid = p["id"]
                web_link = f"{DEFAULT_WEB_URL}/project/{pid}"
                stats = sync.get_project_stats(pid)
                print(f"[{idx}] {p['title']}")
                print(f"    🆔 Project ID      : {pid}")
                print(f"    ⚙️ Engine          : {p.get('target_engine', 'generic').upper()}")
                print(f"    📊 Tiến độ         : {stats['translated_strings']} / {stats['total_strings']} câu ({stats['completion_rate']}%)")
                print(f"    🌐 Link Web Studio : {web_link}\n")

            print("👉 HƯỚNG DẪN TIẾP THEO:")
            print("   1. Nhấp vào Link Web Studio để xem xét hoặc dịch thêm các câu còn lại.")
            print("   2. Khi bạn thấy bản dịch đã OK, chỉ cần gõ 'OK' hoặc 'Cài luôn',")
            print("      Agent sẽ tự động nạp bản dịch tiếng Việt vào game!")
            print(f"      (Lệnh: python3 scripts/locaforge_patch.py --project-id {matches[0]['id']})")
        else:
            print("\nℹ️  Game này CHƯA CÓ dự án trên LocaForge Web.")
            print("👉 Tiếp tục quy trình:")
            print(f"   1. Trích xuất source text: python3 scripts/locaforge_extract.py \"{game_dir}\" Localization_Source")
            print(f"   2. Khởi tạo dự án: python3 scripts/locaforge_sync.py create-project --title \"{det_name}\"")
            print("   3. Đẩy dữ liệu lên web & mở link dịch.")
        print("================================================================\n")

    elif cmd == "find-project":
        title_q = None
        for i, arg in enumerate(sys.argv):
            if arg in {"--title", "-t"} and i + 1 < len(sys.argv):
                title_q = sys.argv[i + 1]

        if not title_q:
            print("❌ Error: --title is required.")
            print("Example: locaforge_sync.py find-project --title \"Probably Stolen\"")
            sys.exit(1)

        print(f"🔎 Đang tìm kiếm dự án với từ khóa: '{title_q}'...")
        matches = sync.find_projects(title_q)
        if matches:
            print(f"\n✨ Tìm thấy {len(matches)} dự án phù hợp:\n")
            for idx, p in enumerate(matches, 1):
                pid = p["id"]
                web_link = f"{DEFAULT_WEB_URL}/project/{pid}"
                stats = sync.get_project_stats(pid)
                print(f"[{idx}] {p['title']}")
                print(f"    🆔 Project ID      : {pid}")
                print(f"    ⚙️ Engine          : {p.get('target_engine', 'generic').upper()}")
                print(f"    📊 Tiến độ         : {stats['translated_strings']} / {stats['total_strings']} câu ({stats['completion_rate']}%)")
                print(f"    🌐 Link Web Studio : {web_link}\n")
        else:
            print(f"❌ Không tìm thấy dự án nào có tên khớp với '{title_q}'.")

    elif cmd == "list-projects":
        projects = sync.list_projects()
        print("\n📋 LocaForge Projects:")
        for p in projects:
            print(f"  • [{p['id'][:8]}] {p['title']} ({p.get('created_at', '')[:10]})")
            print(f"    ID: {p['id']}")

    elif cmd == "create-project":
        title = "My Game Translation"
        desc = ""
        engine = "generic"
        for i, arg in enumerate(sys.argv):
            if arg == "--title" and i + 1 < len(sys.argv):
                title = sys.argv[i + 1]
            elif arg == "--desc" and i + 1 < len(sys.argv):
                desc = sys.argv[i + 1]
            elif arg in {"--engine", "-e"} and i + 1 < len(sys.argv):
                engine = sys.argv[i + 1]

        proj = sync.create_project(title, desc, target_engine=engine)
        pid = proj["id"]
        web_link = f"{DEFAULT_WEB_URL}/project/{pid}"
        print("✨ =========================================")
        print("   LOCAFORGE PROJECT CREATED SUCCESSFULLY")
        print("=========================================\n")
        print(f"📌 Project ID : {pid}")
        print(f"🎮 Title      : {proj['title']}")
        print(f"⚙️ Target Engine: {proj.get('target_engine', engine)}")
        print(f"🌐 Web Link   : {web_link}\n")
        print("👉 You can now push source files using:")
        print(f"   locaforge_sync.py push-files --project-id {pid} --dir Localization_Source/tables")

    elif cmd == "set-engine":
        pid = None
        engine = None
        for i, arg in enumerate(sys.argv):
            if arg == "--project-id" and i + 1 < len(sys.argv):
                pid = sys.argv[i + 1]
            elif arg in {"--engine", "-e"} and i + 1 < len(sys.argv):
                engine = sys.argv[i + 1]

        if not pid or not engine:
            print("❌ Error: --project-id and --engine are required.")
            print("Example: locaforge_sync.py set-engine --project-id <id> --engine unity")
            sys.exit(1)

        sync.set_target_engine(pid, engine)
        print(f"✅ Successfully set target engine of Project {pid[:8]} to: {engine}")

    elif cmd == "push-files":
        pid = None
        target_dir = None
        files = []

        i = 2
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg == "--project-id" and i + 1 < len(sys.argv):
                pid = sys.argv[i + 1]
                i += 2
            elif arg == "--dir" and i + 1 < len(sys.argv):
                target_dir = sys.argv[i + 1]
                i += 2
            else:
                files.append(arg)
                i += 1

        if not pid:
            print("❌ Error: --project-id is required.")
            sys.exit(1)

        target_files = []
        if target_dir:
            d = Path(target_dir)
            if d.exists():
                for f in sorted(d.glob("*")):
                    if f.suffix.lower() in {".json", ".csv", ".po", ".xml", ".ini", ".txt"}:
                        target_files.append(str(f))
        target_files.extend(files)

        if not target_files:
            print("❌ No files specified to push.")
            sys.exit(1)

        print(f"🚀 Pushing {len(target_files)} files to LocaForge Project {pid[:8]}...")
        total_strings = 0
        for f in target_files:
            try:
                res = sync.push_file(pid, f)
                total_strings += res["strings_count"]
                print(f"  ✅ Uploaded {res['file_name']} ({res['strings_count']} strings)")
            except Exception as e:
                print(f"  ❌ Failed {f}: {e}")

        web_link = f"{DEFAULT_WEB_URL}/project/{pid}"
        print(f"\n🎉 Completed! Total {total_strings} strings uploaded.")
        print(f"🌐 Translate now on Web: {web_link}")

    elif cmd == "status":
        pid = None
        for i, arg in enumerate(sys.argv):
            if arg == "--project-id" and i + 1 < len(sys.argv):
                pid = sys.argv[i + 1]
        if not pid:
            print("❌ Error: --project-id is required.")
            sys.exit(1)

        stats = sync.get_project_stats(pid)
        print("📊 =========================================")
        print(f"   TRANSLATION PROGRESS: {stats['title']}")
        print("=========================================\n")
        print(f"📁 Files              : {stats['total_files']}")
        print(f"📝 Total Strings      : {stats['total_strings']}")
        print(f"🇻🇳 Translated Strings : {stats['translated_strings']}")
        print(f"📈 Completion Rate    : {stats['completion_rate']}%")

    elif cmd == "export-zip":
        pid = None
        out = None
        for i, arg in enumerate(sys.argv):
            if arg == "--project-id" and i + 1 < len(sys.argv):
                pid = sys.argv[i + 1]
            elif arg == "--output" and i + 1 < len(sys.argv):
                out = sys.argv[i + 1]
        if not pid:
            print("❌ Error: --project-id is required.")
            sys.exit(1)

        print(f"📦 Downloading translated strings from Project {pid[:8]}...")
        zip_path = sync.export_translated_zip(pid, out)
        print(f"🎉 Exported ZIP archive successfully:")
        print(f"   📁 {zip_path}")

    elif cmd == "set-patch":
        pid = None
        url = None
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--project-id" and i + 1 < len(sys.argv):
                pid = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--url" and i + 1 < len(sys.argv):
                url = sys.argv[i + 1]
                i += 2
            else:
                i += 1

        if not pid or not url:
            print("❌ Error: --project-id and --url are required.")
            print("Example: locaforge_sync.py set-patch --project-id <id> --url <google_drive_or_zip_url>")
            sys.exit(1)

        sync.set_patch_url(pid, url)
        print(f"✅ Successfully linked patch URL to Project {pid[:8]}:")
        print(f"   🔗 {url}")
        print(f"🌐 Game patch button is now ACTIVE on Web: {DEFAULT_WEB_URL}/project/{pid}")

    elif cmd == "upload-patch":
        pid = None
        zip_f = None
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--project-id" and i + 1 < len(sys.argv):
                pid = sys.argv[i + 1]
                i += 2
            else:
                zip_f = sys.argv[i]
                i += 1

        if not pid or not zip_f:
            print("❌ Error: --project-id and zip file path are required.")
            print("Example: locaforge_sync.py upload-patch --project-id <id> <Game_Patch.zip>")
            sys.exit(1)

        print(f"🚀 Uploading patch ZIP {zip_f} to LocaForge Storage for Project {pid[:8]}...")
        pub_url = sync.upload_patch(pid, zip_f)
        print(f"✅ Successfully uploaded patch to Supabase Storage!")
        print(f"   🔗 Direct Download URL: {pub_url}")
        print(f"🌐 Game patch button is now ACTIVE on Web: {DEFAULT_WEB_URL}/project/{pid}")

    elif cmd == "push-zip":
        pid = None
        zip_f = None
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--project-id" and i + 1 < len(sys.argv):
                pid = sys.argv[i + 1]
                i += 2
            else:
                zip_f = sys.argv[i]
                i += 1

        if not pid or not zip_f:
            print("❌ Error: --project-id and zip file path are required.")
            print("Example: locaforge_sync.py push-zip --project-id <id> Localization_Source.zip")
            sys.exit(1)

        print(f"📦 Unpacking and pushing source ZIP {zip_f} to Project {pid[:8]}...")
        res = sync.push_zip(pid, zip_f)
        print(f"\n🎉 Successfully uploaded {res['total_files']} files ({res['total_strings']} strings) from ZIP!")


if __name__ == "__main__":
    main()

