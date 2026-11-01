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
from datetime import datetime
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
DEFAULT_WEB_URL = os.environ.get(
    "LOCAFORGE_WEB_URL",
    "https://locaforge-web.vercel.app"
)
DEFAULT_AVATAR_ID = "87877a37-4ff2-4673-a604-e51185f77099"


class LocaForgeSync:
    def __init__(self, supabase_url: str = DEFAULT_SUPABASE_URL, supabase_key: str = DEFAULT_SUPABASE_KEY):
        self.base_url = supabase_url.rstrip("/")
        self.key = supabase_key
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

    def create_project(self, title: str, description: str = "", user_id: Optional[str] = None) -> Dict[str, Any]:
        proj_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"
        payload = {
            "id": proj_id,
            "title": title.strip(),
            "description": description.strip() if description else f"Localization project for {title}",
            "avatar_id": DEFAULT_AVATAR_ID,
            "created_at": now,
            "updated_at": now,
            "download_count": 0,
        }
        if user_id:
            payload["user_id"] = user_id

        res = self._request("projects", method="POST", data=payload)
        return res[0] if res else payload

    def push_file(self, project_id: str, file_path: str, folder_path: str = "") -> Dict[str, Any]:
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        file_id = str(uuid.uuid4())
        file_name = path.name
        ext = path.suffix.lower().lstrip(".") or "json"
        now = datetime.utcnow().isoformat() + "Z"

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
            # Count strings
            s_res = self._request(f"source_strings?select=id&file_id=eq.{fid}")
            s_ids = [s["id"] for s in (s_res or [])]
            total_strings += len(s_ids)

            if s_ids:
                # Count translations
                # Batch in groups of 50
                for i in range(0, len(s_ids), 50):
                    batch = s_ids[i:i + 50]
                    ids_str = ",".join(batch)
                    t_res = self._request(f"translations?select=id,source_id&lang=eq.vi&source_id=in.({ids_str})")
                    translated_count += len(t_res or [])

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

                # Fetch source strings
                source_strings = self._request(f"source_strings?select=id,key,original_text,context_note,order_index&file_id=eq.{fid}&order=order_index.asc")
                if not source_strings:
                    continue

                # Fetch translations for these strings
                s_ids = [s["id"] for s in source_strings]
                translations_map: Dict[str, str] = {}
                for i in range(0, len(s_ids), 50):
                    batch = s_ids[i:i + 50]
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


def main():
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        print("Usage: locaforge_sync.py <command> [options]")
        print("\nCommands:")
        print("  list-projects")
        print("  create-project --title <title> [--desc <desc>]")
        print("  push-files     --project-id <id> [--dir <dir>] [file1 file2 ...]")
        print("  status         --project-id <id>")
        print("  export-zip     --project-id <id> [--output <file.zip>]")
        sys.exit(0)

    cmd = sys.argv[1]
    sync = LocaForgeSync()

    if cmd == "list-projects":
        projects = sync.list_projects()
        print("\n📋 LocaForge Projects:")
        for p in projects:
            print(f"  • [{p['id'][:8]}] {p['title']} ({p.get('created_at', '')[:10]})")
            print(f"    ID: {p['id']}")

    elif cmd == "create-project":
        title = "My Game Translation"
        desc = ""
        for i, arg in enumerate(sys.argv):
            if arg == "--title" and i + 1 < len(sys.argv):
                title = sys.argv[i + 1]
            elif arg == "--desc" and i + 1 < len(sys.argv):
                desc = sys.argv[i + 1]

        proj = sync.create_project(title, desc)
        pid = proj["id"]
        web_link = f"{DEFAULT_WEB_URL}/project/{pid}"
        print("✨ =========================================")
        print("   LOCAFORGE PROJECT CREATED SUCCESSFULLY")
        print("=========================================\n")
        print(f"📌 Project ID : {pid}")
        print(f"🎮 Title      : {proj['title']}")
        print(f"🌐 Web Link   : {web_link}\n")
        print("👉 You can now push source files using:")
        print(f"   locaforge_sync.py push-files --project-id {pid} --dir Localization_Source/tables")

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


if __name__ == "__main__":
    main()
