#!/usr/bin/env bash
# hivetool インストーラー（Linux/macOS）
# 使い方: bash install.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" || REPO_DIR="$(pwd)"
REPO_DIR="${REPO_DIR%/}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "=== hivetool インストーラー ==="

# --- python チェック ---
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "[エラー] python3 が見つかりません。インストールしてください。" >&2
  exit 1
fi

# --- pipx チェック / なければインストール ---
if ! command -v pipx >/dev/null 2>&1; then
  echo "[情報] pipx が見つかりません。インストールします..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -qq && sudo apt-get install -y pipx
  elif command -v brew >/dev/null 2>&1; then
    brew install pipx
  else
    # pip 経由でユーザー領域に
    "$PYTHON_BIN" -m pip install --user pipx
  fi
  # pipx の PATH をこのシェルに反映
  export PATH="$HOME/.local/bin:$PATH"
  if [ -f "$HOME/.local/bin/pipx" ]; then
    PIPX_BIN="$HOME/.local/bin/pipx"
  else
    PIPX_BIN="$(command -v pipx || true)"
  fi
  # pipx の環境セットアップ（PATH 登録）
  "$PIPX_BIN" ensurepath >/dev/null 2>&1 || true
else
  PIPX_BIN="$(command -v pipx)"
fi

echo "[情報] pipx: ${PIPX_BIN:-pipx}"

# --- インストール ---
if [ ! -f "$REPO_DIR/pyproject.toml" ]; then
  echo "[エラー] $REPO_DIR に pyproject.toml が見つかりません。install.sh をリポジトリ内で実行してください。" >&2
  exit 1
fi
echo "[情報] pipx で hivetool をインストール..."
"$PIPX_BIN" install "$REPO_DIR" --force

# --- コマンド確認 ---
if command -v hivetool >/dev/null 2>&1; then
  echo "[OK] hivetool コマンドが使えるようになりました。"
else
  echo "[情報] パスが通っていません。以下をシェルの設定ファイルに追記しますか？"
fi

# --- .zshrc / .bashrc への PATH 登録（確認付き） ---
LOCAL_BIN="$HOME/.local/bin"
NEED_PATH=0
case ":$PATH:" in
  *":$LOCAL_BIN:"*) NEED_PATH=0 ;;
  *) NEED_PATH=1 ;;
esac

if [ "$NEED_PATH" -eq 1 ]; then
  echo ""
  echo "  ~/.local/bin が PATH に含まれていません。"
  echo "  .zshrc / .bashrc に以下を追記しますか？"
  echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
  read -r -p "  追記しますか？ [Y/n] " ANS
  ANS="${ANS:-Y}"
  if [[ "$ANS" =~ ^[Yy]$ ]]; then
    for rc in "$HOME/.zshrc" "$HOME/.bashrc"; do
      if [ -f "$rc" ]; then
        if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$rc" 2>/dev/null; then
          printf '\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$rc"
          echo "  -> $rc に追記しました"
        fi
      fi
    done
    echo "[情報] 新しいシェルを開くか 'source ~/.zshrc' で反映してください。"
  else
    echo "[情報] スキップしました。手動で PATH に ~/.local/bin を追加してください。"
  fi
fi

echo ""
echo "=== インストール完了 ==="
echo "使い方:"
echo "  hivetool stats <player> [gamemode]"
echo "  hivetool watch <player> [gamemode]"
echo "  hivetool multiwatch [gamemode]"
echo "詳しくは README_ja.md を参照してください。"
