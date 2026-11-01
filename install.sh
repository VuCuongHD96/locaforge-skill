#!/usr/bin/env bash
# LocaForge Skill Installer for macOS / Linux
# Usage:
#   ./install.sh                -> Installs globally to ~/.gemini/config/skills/locaforge
#   ./install.sh /path/to/game  -> Installs into project's .agents/skills/locaforge

set -e

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -n "$1" ]; then
    TARGET_DIR="$1/.agents/skills/locaforge"
    echo "📦 Installing LocaForge Skill into workspace: $1"
else
    TARGET_DIR="$HOME/.gemini/config/skills/locaforge"
    echo "🌍 Installing LocaForge Skill globally to: $TARGET_DIR"
fi

mkdir -p "$TARGET_DIR"
cp -R "$SOURCE_DIR/SKILL.md" "$TARGET_DIR/"
cp -R "$SOURCE_DIR/scripts" "$TARGET_DIR/"
cp -R "$SOURCE_DIR/references" "$TARGET_DIR/"
cp -R "$SOURCE_DIR/examples" "$TARGET_DIR/" 2>/dev/null || true

chmod +x "$TARGET_DIR/scripts"/*.py 2>/dev/null || true

echo "✅ LocaForge Skill installed successfully!"
echo "🎮 Open any game folder in Antigravity IDE and prompt:"
echo "   'Tìm File source text để tôi có thể Việt Hoá'"
