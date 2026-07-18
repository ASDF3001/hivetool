"""ローカル設定の保存・読み込み (~/.hivetool/config.json)。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".hivetool"
CONFIG_FILE = CONFIG_DIR / "config.json"


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
