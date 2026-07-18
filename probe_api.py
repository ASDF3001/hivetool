"""PlayHive API の実フィールド名を確認するためのプローブ。

使い方:
    # 全ゲームの統計を一括取得（レート制限に強い・推奨）
    python probe_api.py <player>

    # 特定ゲームのみ
    python probe_api.py <player> <game>
    game は bed/sky/bridge/hide/dr/sg/ctf/grav/murder/drop/ground/party/wars

実レスポンスの生 JSON をそのまま出力するので、そこから
hivetool/api.py の GAME_FIELDS の生キー名を埋める。
（api.hivemc.com は廃止。PlayHive = api.playhive.com を使用）
"""

from __future__ import annotations

import sys

import requests

BASE_URL = "https://api.playhive.com"


def _resolve_uuid(player: str) -> str:
    if len(player) >= 32 and "-" in player:
        return player
    s = requests.get(f"{BASE_URL}/v0/player/search/{player}", timeout=10)
    if s.status_code != 200 or not s.json():
        raise SystemExit(f"プレイヤーが見つかりません: {player}")
    return s.json()[0]["UUID"]


def main() -> None:
    if len(sys.argv) < 2:
        print("使い方: python probe_api.py <player> [<game>]")
        raise SystemExit(1)
    player = sys.argv[1]
    uuid = _resolve_uuid(player)
    print(f"UUID: {uuid}")

    if len(sys.argv) >= 3:
        game = sys.argv[2].lower()
        url = f"{BASE_URL}/v0/game/all/{game}/{uuid}"
    else:
        url = f"{BASE_URL}/v0/game/all/all/{uuid}"
    print(f"GET {url}")
    resp = requests.get(url, timeout=15)
    print(f"status: {resp.status_code}")
    try:
        data = resp.json()
    except ValueError:
        print("JSONデコード失敗。本文:")
        print(resp.text[:2000])
        raise SystemExit(1)
    print("=== 生レスポンス (キー名がそのまま GAME_FIELDS の生キー) ===")
    print(data)


if __name__ == "__main__":
    main()
