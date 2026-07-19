# hivetool installer (Windows / PowerShell)
# Usage:  powershell -ExecutionPolicy Bypass -File install.ps1
$ErrorActionPreference = "Stop"

$a = (Get-Item $PSScriptRoot).FullName
$b = "python"

Write-Host "=== hivetool installer ==="

# --- python check ---
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    if (Get-Command py -ErrorAction SilentlyContinue) { $b = "py" }
    else {
        Write-Host "[ERROR] python not found. Install from python.org." -ForegroundColor Red
        exit 1
    }
}

# --- pipx check / install if missing ---
if (-not (Get-Command pipx -ErrorAction SilentlyContinue)) {
    Write-Host "[info] pipx not found. Installing..." -ForegroundColor Cyan
    & $b -m pip install --user pipx
    $c = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$c;$env:Path"
    if (-not (Get-Command pipx -ErrorAction SilentlyContinue)) {
        Write-Host "[ERROR] pipx install failed." -ForegroundColor Red
        exit 1
    }
}

# --- install ---
Write-Host "[info] Installing hivetool via pipx..." -ForegroundColor Cyan
pipx install "$a" --force

# --- command check ---
if (Get-Command hivetool -ErrorAction SilentlyContinue) {
    Write-Host "[OK] hivetool command is now available." -ForegroundColor Green
}
else {
    Write-Host "[info] Command not on PATH. Add pipx location to your user PATH?" -ForegroundColor Yellow
}

# --- user PATH registration (confirmation) ---
$d = Get-Command pipx -ErrorAction SilentlyContinue
if ($d -and $d.Source) { $e = Split-Path $d.Source }
else { $e = "$env:USERPROFILE\AppData\Local\Microsoft\WindowsApps" }
$f = [Environment]::GetEnvironmentVariable("Path", "User")
$g = ($f -notmatch [regex]::Escape($e))

if ($g) {
    Write-Host ""
    Write-Host "  pipx location ($e) is not in your user PATH."
    Write-Host "  Add it? (Y/n)"
    $h = Read-Host "  >"
    if ($h -eq "" -or $h -match "^[Yy]$") {
        if ($f -eq "") { $i = $e } else { $i = "$f;$e" }
        [Environment]::SetEnvironmentVariable("Path", $i, "User")
        $env:Path = "$i;$env:Path"
        Write-Host "  -> Added to user PATH. Reflects in a new terminal." -ForegroundColor Green
    }
    else {
        Write-Host "[info] Skipped. Manually add $e to PATH." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== install complete ===" -ForegroundColor Cyan
Write-Host "Usage:"
Write-Host "  hivetool stats <player> [gamemode]"
Write-Host "  hivetool watch <player> [gamemode]"
Write-Host "  hivetool multiwatch [gamemode]"
Write-Host "See README_ja.md for details."
