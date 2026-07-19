"""ローカル設定の保存・読み込み (~/.hivetool/config.json)。"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".hivetool"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_DIR = CONFIG_DIR / "history"


def _ensure_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, Any]:
    """config.json を読み込む。存在しない場合は空の dict を返す。"""
    if not CONFIG_FILE.exists():
        return {}
    try:
        with CONFIG_FILE.open(encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(data: dict[str, Any]) -> None:
    _ensure_dir()
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_player(name: str) -> list[str]:
    """プレイヤー名を保存リストに追加し、更新後のリストを返す。"""
    name = name.strip()
    data = load_config()
    players = data.get("players", [])
    if name not in players:
        players.append(name)
        data["players"] = players
        save_config(data)
    return players


def list_players() -> list[str]:
    return load_config().get("players", [])


# --- お気に入りゲームモード ---

def get_favorite_game() -> str | None:
    """登録済みのお気に入りゲームモード（トークン）を返す。未設定なら None。"""
    return load_config().get("favorite_game")


def set_favorite_game(token: str) -> None:
    """お気に入りゲームモード（トークン）を保存する。"""
    data = load_config()
    data["favorite_game"] = token
    save_config(data)


# --- セッション履歴（watch / multiwatch のポール記録） ---

def save_history_entry(player: str, game: str, stats: Any) -> None:
    """1ポールの結果を history/<player>_<game>_<timestamp>.json に追記。"""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    safe = f"{player}_{game}".replace("/", "_").replace("\\", "_")
    path = HISTORY_DIR / f"{safe}_{ts}.json"
    # stats は (label, value) のリストかもしれない → dict に正規化
    if isinstance(stats, (list, tuple)):
        stats = dict(stats)
    entry = {"player": player, "game": game, "ts": ts, "stats": stats}
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def load_history(player: str, game: str, limit: int = 50) -> list[dict[str, Any]]:
    """直近の履歴エントリ（新しい順）を返す。ファイル名の ts でソート。"""
    if not HISTORY_DIR.exists():
        return []
    safe = f"{player}_{game}".replace("/", "_").replace("\\", "_")
    entries = []
    for p in HISTORY_DIR.glob(f"{safe}_*.json"):
        try:
            with p.open(encoding="utf-8") as f:
                entries.append(json.load(f))
        except (OSError, ValueError):
            continue
    entries.sort(key=lambda e: e.get("ts", 0), reverse=True)
    # 旧形式（stats が (label,value) リスト）への互換: dict に正規化
    for e in entries:
        s = e.get("stats")
        if isinstance(s, (list, tuple)):
            e["stats"] = dict(s)
    return entries[:limit]
