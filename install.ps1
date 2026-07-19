# hivetool インストーラー（Windows / PowerShell）
# 使い方:  powershell -ExecutionPolicy Bypass -File install.ps1
$ErrorActionPreference = "Stop"

$REPO_DIR = (Get-Item $PSScriptRoot).FullName
$PYTHON = "python"

Write-Host "=== hivetool インストーラー ==="

# --- python チェック ---
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    if (Get-Command py -ErrorAction SilentlyContinue) { $PYTHON = "py" }
    else {
        Write-Host "[エラー] python が見つかりません。python.org からインストールしてください。" -ForegroundColor Red
        exit 1
    }
}

# --- pipx チェック / なければ導入 ---
if (-not (Get-Command pipx -ErrorAction SilentlyContinue)) {
    Write-Host "[情報] pipx が見つかりません。導入します..." -ForegroundColor Cyan
    & $PYTHON -m pip install --user pipx
    # ユーザー PATH をこのセッションに反映
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$userPath;$env:Path"
    if (-not (Get-Command pipx -ErrorAction SilentlyContinue)) {
        Write-Host "[エラー] pipx の導入に失敗しました。" -ForegroundColor Red
        exit 1
    }
}

# --- インストール ---
Write-Host "[情報] pipx で hivetool をインストール..." -ForegroundColor Cyan
pipx install "$REPO_DIR" --force

# --- コマンド確認 ---
if (Get-Command hivetool -ErrorAction SilentlyContinue) {
    Write-Host "[OK] hivetool コマンドが使えるようになりました。" -ForegroundColor Green
}
else {
    Write-Host "[情報] パスが通っていません。環境変数 Path に pipx の場所を追加しますか？" -ForegroundColor Yellow
}

# --- ユーザー Path への登録（確認付き） ---
$PIPX_DIR = "$env:USERPROFILE\AppData\Local\Microsoft\WindowsApps"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$needsPath = ($userPath -notmatch [regex]::Escape($PIPX_DIR))

if ($needsPath) {
    Write-Host ""
    Write-Host "  pipx の場所がユーザー Path に含まれていません。"
    Write-Host "  追加しますか？ (Y/n)"
    $ans = Read-Host "  >"
    if ($ans -eq "" -or $ans -match "^[Yy]$") {
        if ($userPath -eq "") { $newPath = $PIPX_DIR }
        else { $newPath = "$userPath;$PIPX_DIR" }
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        $env:Path = "$newPath;$env:Path"
        Write-Host "  -> ユーザー Path に追加しました。新しいターミナルで反映されます。" -ForegroundColor Green
    }
    else {
        Write-Host "[情報] スキップしました。手動で Path に $PIPX_DIR を追加してください。" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== インストール完了 ===" -ForegroundColor Cyan
Write-Host "使い方:"
Write-Host "  hivetool stats <player> [gamemode]"
Write-Host "  hivetool watch <player> [gamemode]"
Write-Host "  hivetool multiwatch [gamemode]"
Write-Host "詳しくは README_ja.md を参照してください。"
