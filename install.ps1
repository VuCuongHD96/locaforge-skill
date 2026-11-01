# LocaForge Skill Installer for Windows PowerShell
# Usage:
#   .\install.ps1                       -> Installs globally to ~\.gemini\config\skills\locaforge
#   .\install.ps1 -ProjectPath C:\game  -> Installs into game workspace .agents\skills\locaforge

param(
    [string]$ProjectPath = ""
)

$SourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($ProjectPath -ne "") {
    $TargetDir = Join-Path $ProjectPath ".agents\skills\locaforge"
    Write-Host "📦 Installing LocaForge Skill into workspace: $ProjectPath" -ForegroundColor Cyan
} else {
    $TargetDir = Join-Path $HOME ".gemini\config\skills\locaforge"
    Write-Host "🌍 Installing LocaForge Skill globally to: $TargetDir" -ForegroundColor Cyan
}

if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
}

Copy-Item -Path (Join-Path $SourceDir "SKILL.md") -Destination $TargetDir -Force
Copy-Item -Path (Join-Path $SourceDir "scripts") -Destination $TargetDir -Recurse -Force
Copy-Item -Path (Join-Path $SourceDir "references") -Destination $TargetDir -Recurse -Force
if (Test-Path (Join-Path $SourceDir "examples")) {
    Copy-Item -Path (Join-Path $SourceDir "examples") -Destination $TargetDir -Recurse -Force
}

Write-Host "✅ LocaForge Skill installed successfully!" -ForegroundColor Green
Write-Host "🎮 Open any game folder in Antigravity IDE and prompt:" -ForegroundColor Yellow
Write-Host "   'Tìm File source text để tôi có thể Việt Hoá'" -ForegroundColor White
