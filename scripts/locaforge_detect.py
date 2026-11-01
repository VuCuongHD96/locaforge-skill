#!/usr/bin/env python3
"""
LocaForge Game Engine & Localization Scanner
Detects game engine and locates translatable asset files.
Supports: Unity, Unreal Engine, RPG Maker, Ren'Py, Godot, GameMaker, and Direct Text/Config.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any


class GameDetector:
    def __init__(self, target_dir: str = "."):
        self.root = Path(target_dir).resolve()

    def detect(self) -> Dict[str, Any]:
        results = {
            "target_dir": str(self.root),
            "engines": [],
            "translatable_files": [],
            "recommended_strategy": "",
            "source_dir": "",
        }

        # 1. Unity Check
        unity_info = self._check_unity()
        if unity_info["detected"]:
            results["engines"].append(unity_info)

        # 2. RPG Maker Check
        rpgm_info = self._check_rpg_maker()
        if rpgm_info["detected"]:
            results["engines"].append(rpgm_info)

        # 3. Ren'Py Check
        renpy_info = self._check_renpy()
        if renpy_info["detected"]:
            results["engines"].append(renpy_info)

        # 4. Unreal Engine Check
        unreal_info = self._check_unreal()
        if unreal_info["detected"]:
            results["engines"].append(unreal_info)

        # 5. Godot Check
        godot_info = self._check_godot()
        if godot_info["detected"]:
            results["engines"].append(godot_info)

        # 6. GameMaker Check
        gm_info = self._check_gamemaker()
        if gm_info["detected"]:
            results["engines"].append(gm_info)

        # 7. Generic Translatable Files Search
        direct_files = self._find_translatable_files()
        results["translatable_files"] = direct_files

        # Determine Primary Engine & Recommended Strategy
        if results["engines"]:
            primary = results["engines"][0]
            results["primary_engine"] = primary["name"]
            results["recommended_strategy"] = primary.get("strategy", "")
            results["source_dir"] = primary.get("suggested_dir", "")
        else:
            results["primary_engine"] = "Direct Text / Mod Files" if direct_files else "Unknown"
            results["recommended_strategy"] = (
                "Direct extraction from text/JSON/CSV/PO files"
                if direct_files
                else "Manual inspection needed (binary assets or custom engine)"
            )

        return results

    def _check_unity(self) -> Dict[str, Any]:
        # Look for *_Data folder or UnityPlayer / Managed
        data_dirs = list(self.root.glob("*_Data"))
        # Check Mac App bundle
        mac_data = list(self.root.glob("*.app/Contents/Resources/Data"))
        if mac_data:
            data_dirs.extend(mac_data)

        has_managed = any((d / "Managed").exists() for d in data_dirs)
        has_il2cpp = any((d / "il2cpp_data").exists() for d in data_dirs) or list(self.root.glob("*GameAssembly*"))
        has_streaming = any((d / "StreamingAssets").exists() for d in data_dirs)

        detected = bool(data_dirs or has_managed or has_il2cpp)
        return {
            "name": "Unity",
            "detected": detected,
            "backend": "IL2CPP" if has_il2cpp else "Mono" if has_managed else "Standard",
            "data_dirs": [str(d.relative_to(self.root)) for d in data_dirs],
            "streaming_assets": has_streaming,
            "strategy": "Extract TextAssets, I2Localization, or StringTables from StreamingAssets/AssetBundles",
            "suggested_dir": str(data_dirs[0].relative_to(self.root)) if data_dirs else "",
        }

    def _check_rpg_maker(self) -> Dict[str, Any]:
        # RPG Maker MV/MZ: www/data or data with Actors.json, Map001.json
        possible_dirs = [self.root / "data", self.root / "www" / "data"]
        detected_ver = None
        data_path = None

        for d in possible_dirs:
            if d.exists() and (d / "System.json").exists():
                data_path = d
                # Check MV vs MZ
                pkg = self.root / "package.json"
                if pkg.exists():
                    try:
                        content = pkg.read_text(encoding="utf-8")
                        detected_ver = "RPG Maker MZ" if "rmmz" in content.lower() else "RPG Maker MV"
                    except Exception:
                        detected_ver = "RPG Maker MV/MZ"
                else:
                    detected_ver = "RPG Maker MV/MZ"
                break

        # Check VX Ace / XP (.rvdata2, .rxdata)
        if not detected_ver:
            if list(self.root.glob("Data/*.rvdata2")) or list(self.root.glob("*.rvproj2")):
                detected_ver = "RPG Maker VX Ace"
                data_path = self.root / "Data"
            elif list(self.root.glob("Data/*.rxdata")) or list(self.root.glob("*.rxproj")):
                detected_ver = "RPG Maker XP"
                data_path = self.root / "Data"

        return {
            "name": "RPG Maker",
            "detected": detected_ver is not None,
            "version": detected_ver or "None",
            "data_dir": str(data_path.relative_to(self.root)) if data_path else "",
            "strategy": "Extract JSON dialogues, items, maps directly from data/ folder",
            "suggested_dir": str(data_path.relative_to(self.root)) if data_path else "",
        }

    def _check_renpy(self) -> Dict[str, Any]:
        game_dir = self.root / "game"
        has_rpy = list(game_dir.glob("*.rpy")) if game_dir.exists() else []
        has_rpyc = list(game_dir.glob("*.rpyc")) if game_dir.exists() else []
        has_rpa = list(game_dir.glob("*.rpa")) if game_dir.exists() else []
        has_tl = (game_dir / "tl").exists() if game_dir.exists() else False

        detected = bool(has_rpy or has_rpyc or has_rpa)
        return {
            "name": "Ren'Py",
            "detected": detected,
            "has_rpy": len(has_rpy) > 0,
            "has_rpyc_only": len(has_rpyc) > 0 and len(has_rpy) == 0,
            "has_rpa": len(has_rpa) > 0,
            "has_existing_tl": has_tl,
            "strategy": "Generate or inject translation in game/tl/vietnamese/ directory",
            "suggested_dir": "game/tl/vietnamese" if has_tl else "game",
        }

    def _check_unreal(self) -> Dict[str, Any]:
        has_content = (self.root / "Content").exists() or list(self.root.glob("*/Content"))
        paks = list(self.root.glob("**/*.pak"))
        locres = list(self.root.glob("**/*.locres"))

        detected = bool(has_content and (paks or locres))
        return {
            "name": "Unreal Engine",
            "detected": detected,
            "locres_files": [str(f.relative_to(self.root)) for f in locres[:5]],
            "paks_count": len(paks),
            "strategy": "Extract .locres text or unpack Pak using UnrealPak, then create mod pak",
            "suggested_dir": "Content/Localization" if locres else "Content/Paks",
        }

    def _check_godot(self) -> Dict[str, Any]:
        has_project = (self.root / "project.godot").exists()
        has_pck = list(self.root.glob("*.pck"))

        detected = bool(has_project or has_pck)
        return {
            "name": "Godot",
            "detected": detected,
            "strategy": "Extract PO or CSV localization from project or unpack .pck archive",
            "suggested_dir": ".",
        }

    def _check_gamemaker(self) -> Dict[str, Any]:
        has_data_win = (self.root / "data.win").exists()
        has_audiogroup = list(self.root.glob("audiogroup*.dat"))

        detected = bool(has_data_win or has_audiogroup)
        return {
            "name": "GameMaker Studio",
            "detected": detected,
            "strategy": "Extract strings using UndertaleModTool or patch data.win string table",
            "suggested_dir": ".",
        }

    def _find_translatable_files(self) -> List[Dict[str, Any]]:
        # Supported extensions in LocaForge
        exts = {".json", ".csv", ".po", ".xml", ".srt", ".ini", ".txt", ".bak", ".lang", ".properties"}
        skip_dirs = {".git", ".agents", ".gemini", "node_modules", "dist", ".next", ".vscode", "__pycache__"}
        
        found = []
        for root, dirs, files in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            rel_dir = os.path.relpath(root, self.root)
            if rel_dir.startswith("."):
                continue

            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in exts:
                    full_p = Path(root) / f
                    # Skip huge binary/compiled files (> 15MB)
                    try:
                        sz = full_p.stat().st_size
                        if 10 < sz < 15 * 1024 * 1024:
                            found.append({
                                "file": str(full_p.relative_to(self.root)),
                                "ext": ext[1:],
                                "size_bytes": sz,
                            })
                    except Exception:
                        pass

        # Sort by relevance: Localization_Source, loc, lang, text first
        def score(item):
            p = item["file"].lower()
            if "loca" in p or "lang" in p or "string" in p or "text" in p or "trans" in p:
                return 0
            return 1

        found.sort(key=score)
        return found[:50]  # Limit to 50 most relevant


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    detector = GameDetector(target)
    results = detector.detect()

    if "--json" in sys.argv:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print("🎮 =========================================")
        print("   LOCAFORGE GAME ENGINE & ASSET SCANNER")
        print("=========================================\n")
        print(f"📁 Target Directory : {results['target_dir']}")
        print(f"🎯 Primary Engine   : {results['primary_engine']}")
        print(f"💡 Strategy         : {results['recommended_strategy']}")
        if results["source_dir"]:
            print(f"📂 Suggested Path   : {results['source_dir']}")

        if results["engines"]:
            print("\n🔍 Detected Engine Details:")
            for eng in results["engines"]:
                print(f"  • {eng['name']}: {eng.get('backend', '')} {eng.get('version', '')}")

        print(f"\n📄 Found {len(results['translatable_files'])} Translatable Source Files:")
        for f in results["translatable_files"][:15]:
            sz_kb = round(f['size_bytes'] / 1024, 1)
            print(f"  • [{f['ext'].upper():<4}] {f['file']} ({sz_kb} KB)")

        if len(results["translatable_files"]) > 15:
            print(f"  ... và còn {len(results['translatable_files']) - 15} file khác.")

        print("\n✨ Ready to extract with `locaforge_extract.py`!")


if __name__ == "__main__":
    main()

