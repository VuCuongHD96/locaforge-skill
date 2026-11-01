#!/usr/bin/env python3
"""
LocaForge Universal Game Text Extractor
Extracts translatable strings from games and normalizes them into LocaForge-ready formats.
Preserves engine keys, IDs, and placeholders.
"""

import os
import sys
import json
import csv
import re
from pathlib import Path
from typing import Dict, List, Any, Optional


class LocaForgeExtractor:
    def __init__(self, output_dir: str = "Localization_Source"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tables_dir = self.output_dir / "tables"
        self.tables_dir.mkdir(parents=True, exist_ok=True)
        self.extracted_records: List[Dict[str, Any]] = []

    def extract_file(self, file_path: str, table_name: Optional[str] = None) -> List[Dict[str, Any]]:
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        table = table_name or path.stem
        ext = path.suffix.lower()

        records = []
        if ext == ".json":
            records = self._extract_json(path, table)
        elif ext == ".csv":
            records = self._extract_csv(path, table)
        elif ext == ".po":
            records = self._extract_po(path, table)
        elif ext == ".xml":
            records = self._extract_xml(path, table)
        elif ext in {".ini", ".lang", ".properties", ".txt"}:
            records = self._extract_keyvalue(path, table)
        elif ext == ".srt":
            records = self._extract_srt(path, table)
        else:
            # Fallback to keyvalue or raw lines
            records = self._extract_keyvalue(path, table)

        if records:
            # Save individual normalized table file
            out_json = self.tables_dir / f"{table}.json"
            out_csv = self.tables_dir / f"{table}.csv"

            with open(out_json, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)

            self._save_csv(out_csv, records)
            self.extracted_records.extend(records)

        return records

    def _extract_json(self, path: Path, table: str) -> List[Dict[str, Any]]:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)

        records = []

        # Case 1: List of objects already matching LocaForge schema
        if isinstance(data, list):
            # Check if it's RPG Maker MV/MZ
            if path.name in {"Actors.json", "Items.json", "Skills.json", "Weapons.json", "Armors.json", "Enemies.json", "States.json"}:
                return self._extract_rpgmaker_database(data, table)
            elif path.name.startswith("Map") and path.name.endswith(".json"):
                return self._extract_rpgmaker_map(data, table)
            elif path.name == "CommonEvents.json":
                return self._extract_rpgmaker_common_events(data, table)

            for idx, item in enumerate(data):
                if isinstance(item, dict):
                    # Check if already has table/id/key/english
                    if "key" in item and ("english" in item or "original" in item or "source" in item):
                        eng = item.get("english") or item.get("original") or item.get("source") or ""
                        records.append({
                            "table": str(item.get("table", table)),
                            "id": item.get("id", idx + 1),
                            "key": str(item.get("key")),
                            "english": str(eng),
                            "vietnamese": str(item.get("vietnamese", "")),
                        })
                    else:
                        # Flatten dictionary keys
                        for k, v in item.items():
                            if isinstance(v, str) and v.strip():
                                records.append({
                                    "table": table,
                                    "id": f"{idx}_{k}",
                                    "key": f"item_{idx}.{k}",
                                    "english": v,
                                    "vietnamese": "",
                                })

        # Case 2: Key-Value Dictionary or Nested Dict
        elif isinstance(data, dict):
            # Check RPG Maker System.json
            if path.name == "System.json":
                return self._extract_rpgmaker_system(data, table)

            flat = {}
            self._flatten_dict(data, "", flat)
            for idx, (k, v) in enumerate(flat.items()):
                records.append({
                    "table": table,
                    "id": idx + 1,
                    "key": k,
                    "english": v,
                    "vietnamese": "",
                })

        return records

    def _flatten_dict(self, d: Dict[str, Any], prefix: str, result: Dict[str, str]):
        for k, v in d.items():
            full_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                self._flatten_dict(v, full_key, result)
            elif isinstance(v, str) and v.strip():
                result[full_key] = v
            elif isinstance(v, (int, float, bool)):
                pass  # Skip primitives

    def _extract_csv(self, path: Path, table: str) -> List[Dict[str, Any]]:
        records = []
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            fieldnames = [c.lower().strip() for c in (reader.fieldnames or [])]

            # Detect column mappings
            table_col = next((c for c in reader.fieldnames if c.lower() in {"table", "category", "group"}), None)
            id_col = next((c for c in reader.fieldnames if c.lower() in {"id", "index", "row"}), None)
            key_col = next((c for c in reader.fieldnames if c.lower() in {"key", "id", "name", "string_id", "code"}), None)
            eng_col = next((c for c in reader.fieldnames if c.lower() in {"english", "source", "original", "text", "en", "default"}), None)
            vi_col = next((c for c in reader.fieldnames if c.lower() in {"vietnamese", "translation", "target", "vi"}), None)

            # If no english column found, pick 2nd column or best text column
            if not eng_col and len(reader.fieldnames) >= 2:
                eng_col = reader.fieldnames[1]
            if not key_col and len(reader.fieldnames) >= 1:
                key_col = reader.fieldnames[0]

            for idx, row in enumerate(reader):
                k = row.get(key_col, f"row_{idx}") if key_col else f"row_{idx}"
                eng = row.get(eng_col, "") if eng_col else ""
                vi = row.get(vi_col, "") if vi_col else ""
                t = row.get(table_col, table) if table_col else table
                row_id = row.get(id_col, idx + 1) if id_col else idx + 1

                if eng and eng.strip():
                    records.append({
                        "table": str(t),
                        "id": row_id,
                        "key": str(k),
                        "english": str(eng),
                        "vietnamese": str(vi),
                    })
        return records

    def _extract_po(self, path: Path, table: str) -> List[Dict[str, Any]]:
        records = []
        content = path.read_text(encoding="utf-8", errors="replace")
        blocks = content.split("\n\n")

        idx = 0
        for block in blocks:
            msgid_match = re.search(r'msgid\s+"(.*)"', block, re.DOTALL)
            msgstr_match = re.search(r'msgstr\s+"(.*)"', block, re.DOTALL)
            ctx_match = re.search(r'msgctxt\s+"(.*)"', block)

            if msgid_match:
                msgid = msgid_match.group(1).replace('"\n"', '')
                msgstr = msgstr_match.group(1).replace('"\n"', '') if msgstr_match else ""
                ctx = ctx_match.group(1) if ctx_match else f"str_{idx}"

                if msgid.strip():
                    idx += 1
                    records.append({
                        "table": table,
                        "id": idx,
                        "key": ctx,
                        "english": msgid,
                        "vietnamese": msgstr,
                    })
        return records

    def _extract_xml(self, path: Path, table: str) -> List[Dict[str, Any]]:
        records = []
        content = path.read_text(encoding="utf-8", errors="replace")
        # Match <string name="key">value</string>
        pattern = re.compile(r'<string\s+name=["\']([^"\']+)["\']>(.*?)</string>', re.DOTALL)
        for idx, match in enumerate(pattern.finditer(content)):
            k = match.group(1)
            v = match.group(2)
            records.append({
                "table": table,
                "id": idx + 1,
                "key": k,
                "english": v,
                "vietnamese": "",
            })
        return records

    def _extract_keyvalue(self, path: Path, table: str) -> List[Dict[str, Any]]:
        records = []
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        current_section = table

        idx = 0
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith(";"):
                continue

            # Section header [Section]
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
                continue

            if "=" in line:
                k, v = line.split("=", 1)
                idx += 1
                records.append({
                    "table": current_section,
                    "id": idx,
                    "key": k.strip(),
                    "english": v.strip(),
                    "vietnamese": "",
                })
            elif ":" in line:
                k, v = line.split(":", 1)
                idx += 1
                records.append({
                    "table": current_section,
                    "id": idx,
                    "key": k.strip(),
                    "english": v.strip(),
                    "vietnamese": "",
                })
        return records

    def _extract_srt(self, path: Path, table: str) -> List[Dict[str, Any]]:
        records = []
        content = path.read_text(encoding="utf-8", errors="replace")
        blocks = re.split(r'\n\s*\n', content.strip())

        for b in blocks:
            lines = b.strip().splitlines()
            if len(lines) >= 3:
                sub_id = lines[0].strip()
                timestamp = lines[1].strip()
                text = "\n".join(lines[2:]).strip()
                records.append({
                    "table": table,
                    "id": sub_id,
                    "key": f"{sub_id}_{timestamp}",
                    "english": text,
                    "vietnamese": "",
                })
        return records

    # RPG Maker Specialized Handlers
    def _extract_rpgmaker_database(self, items: List[Any], table: str) -> List[Dict[str, Any]]:
        records = []
        for item in items:
            if not isinstance(item, dict):
                continue
            item_id = item.get("id")
            if not item_id:
                continue

            name = item.get("name", "")
            desc = item.get("description", "")
            msg1 = item.get("message1", "")
            msg2 = item.get("message2", "")

            if name:
                records.append({"table": table, "id": f"{item_id}_name", "key": f"{item_id}.name", "english": name, "vietnamese": ""})
            if desc:
                records.append({"table": table, "id": f"{item_id}_desc", "key": f"{item_id}.description", "english": desc, "vietnamese": ""})
            if msg1:
                records.append({"table": table, "id": f"{item_id}_msg1", "key": f"{item_id}.message1", "english": msg1, "vietnamese": ""})
            if msg2:
                records.append({"table": table, "id": f"{item_id}_msg2", "key": f"{item_id}.message2", "english": msg2, "vietnamese": ""})

        return records

    def _extract_rpgmaker_map(self, data: Dict[str, Any], table: str) -> List[Dict[str, Any]]:
        records = []
        events = data.get("events", [])
        for ev in events:
            if not isinstance(ev, dict):
                continue
            ev_id = ev.get("id", 0)
            pages = ev.get("pages", [])
            for p_idx, page in enumerate(pages):
                cmd_list = page.get("list", [])
                for c_idx, cmd in enumerate(cmd_list):
                    code = cmd.get("code")
                    params = cmd.get("parameters", [])
                    # Code 401 is Show Text line, Code 102 is Show Choices
                    if code == 401 and params and isinstance(params[0], str) and params[0].strip():
                        records.append({
                            "table": table,
                            "id": f"ev{ev_id}_p{p_idx}_c{c_idx}",
                            "key": f"event_{ev_id}.page_{p_idx}.line_{c_idx}",
                            "english": params[0],
                            "vietnamese": "",
                        })
                    elif code == 102 and params and isinstance(params[0], list):
                        for choice_idx, choice_text in enumerate(params[0]):
                            if isinstance(choice_text, str) and choice_text.strip():
                                records.append({
                                    "table": table,
                                    "id": f"ev{ev_id}_choice_{choice_idx}",
                                    "key": f"event_{ev_id}.choice_{choice_idx}",
                                    "english": choice_text,
                                    "vietnamese": "",
                                })
        return records

    def _extract_rpgmaker_common_events(self, events: List[Any], table: str) -> List[Dict[str, Any]]:
        records = []
        for ev in events:
            if not isinstance(ev, dict):
                continue
            ev_id = ev.get("id")
            if not ev_id:
                continue
            for c_idx, cmd in enumerate(ev.get("list", [])):
                code = cmd.get("code")
                params = cmd.get("parameters", [])
                if code == 401 and params and isinstance(params[0], str) and params[0].strip():
                    records.append({
                        "table": table,
                        "id": f"ce_{ev_id}_{c_idx}",
                        "key": f"common_event_{ev_id}.line_{c_idx}",
                        "english": params[0],
                        "vietnamese": "",
                    })
        return records

    def _extract_rpgmaker_system(self, data: Dict[str, Any], table: str) -> List[Dict[str, Any]]:
        records = []
        game_title = data.get("gameTitle", "")
        if game_title:
            records.append({"table": table, "id": "gameTitle", "key": "gameTitle", "english": game_title, "vietnamese": ""})

        terms = data.get("terms", {})
        messages = terms.get("messages", {})
        for k, v in messages.items():
            if isinstance(v, str) and v.strip():
                records.append({"table": table, "id": f"msg_{k}", "key": f"terms.messages.{k}", "english": v, "vietnamese": ""})

        commands = terms.get("commands", [])
        for idx, cmd in enumerate(commands):
            if isinstance(cmd, str) and cmd.strip():
                records.append({"table": table, "id": f"cmd_{idx}", "key": f"terms.commands.{idx}", "english": cmd, "vietnamese": ""})

        return records

    def _save_csv(self, path: Path, records: List[Dict[str, Any]]):
        if not records:
            return
        fieldnames = ["table", "id", "key", "english", "vietnamese"]
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in records:
                writer.writerow({
                    "table": r.get("table", ""),
                    "id": r.get("id", ""),
                    "key": r.get("key", ""),
                    "english": r.get("english", ""),
                    "vietnamese": r.get("vietnamese", ""),
                })

    def save_summary(self):
        """Generates all_strings.json and all_strings.csv in Localization_Source"""
        if not self.extracted_records:
            return

        all_json = self.output_dir / "all_strings.json"
        all_csv = self.output_dir / "all_strings.csv"

        with open(all_json, "w", encoding="utf-8") as f:
            json.dump(self.extracted_records, f, indent=2, ensure_ascii=False)

        self._save_csv(all_csv, self.extracted_records)
        print(f"✅ Generated master files:")
        print(f"   • {all_json} ({len(self.extracted_records)} strings)")
        print(f"   • {all_csv}")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        print("Usage: locaforge_extract.py <file_or_directory> [output_dir]")
        print("Example: locaforge_extract.py game/data Localization_Source")
        print("         locaforge_extract.py MainMenu.json Localization_Source")
        sys.exit(0)

    target = Path(sys.argv[1])
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "Localization_Source"
    extractor = LocaForgeExtractor(out_dir)

    print("📦 =========================================")
    print("   LOCAFORGE GAME TEXT EXTRACTOR")
    print("=========================================\n")

    if target.is_file():
        records = extractor.extract_file(str(target))
        print(f" Extracted {len(records)} strings from {target.name}")
    elif target.is_dir():
        count_files = 0
        exts = {".json", ".csv", ".po", ".xml", ".ini", ".srt", ".lang", ".txt"}
        for root, _, files in os.walk(target):
            for f in sorted(files):
                if Path(f).suffix.lower() in exts:
                    full_p = Path(root) / f
                    try:
                        recs = extractor.extract_file(str(full_p))
                        if recs:
                            count_files += 1
                            print(f"  • {full_p.name:<30} ➔ {len(recs)} strings")
                    except Exception as e:
                        print(f"  ⚠️ Skip {f}: {e}")
        print(f"\n Processed {count_files} files.")

    extractor.save_summary()
    print(f"\n🎉 Finished! Source files ready in: {out_dir}/")


if __name__ == "__main__":
    main()

