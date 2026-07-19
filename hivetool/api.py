"""PlayHive 公式APIクライアント。

実API: https://api.playhive.com  (api.hivemc.com は廃止)
統計エンドポイント: GET /v0/game/all/{game}/{UUID}
プレイヤー検索:     GET /v0/player/search/{partial}

現状はモック実装で動作する。実APIが利用可能なら環境変数
HIVETOOL_MOCK=0 にして有効化する（コード変更不要）。
"""

from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests
from rich.console import Console

err_console = Console(stderr=True)

# --- cache layer (mitigates PlayHive per-(game,player) rate limits) ---
CACHE_DIR = Path.home() / ".hivetool" / "cache"
CACHE_TTL = 300  # seconds; refreshed if older than this


def _cache_path(game: str, uuid: str) -> Path:
    d = CACHE_DIR / game
    return d / f"{uuid}.json"


def _cache_get(game: str, uuid: str) -> dict | None:
    p = _cache_path(game, uuid)
    if not p.exists():
        return None
    try:
        age = time.time() - p.stat().st_mtime
        if age > CACHE_TTL:
            return None
        import json
        with p.open(encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _cache_set(game: str, uuid: str, data: dict) -> None:
    try:
        d = CACHE_DIR / game
        d.mkdir(parents=True, exist_ok=True)
        import json
        with (d / f"{uuid}.json").open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except OSError:
        pass

# 実APIが使える環境では HIVETOOL_MOCK=0 にする（コード変更不要）。
USE_MOCK = os.environ.get("HIVETOOL_MOCK", "1") != "0"

BASE_URL = "https://api.playhive.com"

# ゲームモード: エイリアス(入力で使う名前) -> 実APIの game トークン
# 実トークンは bed/sky/sg/dr/ctf/grav/hide/bridge/murder/drop/ground/party/wars
GAME_MODES: dict[str, str] = {
    "bed": "bed",
    "bedwars": "bed",
    "sky": "sky",
    "skywars": "sky",
    "bridge": "bridge",
    "blockhide": "hide",
    "hide": "hide",
    "deathrun": "dr",
    "dr": "dr",
    "survivalgames": "sg",
    "sg": "sg",
    "survival": "sg",
    "ctf": "ctf",
    "gravity": "grav",
    "grav": "grav",
    "murder": "murder",
    "drop": "drop",
    "ground": "ground",
    "party": "party",
    "wars": "wars",
}

# メニュー表示用: トークン -> 表示ラベル
GAME_LABELS: dict[str, str] = {
    "bed": "BedWars (bed/bedwars)",
    "sky": "SkyWars (sky/skywars)",
    "bridge": "Bridge (bridge)",
    "hide": "BlockHide (hide/blockhide)",
    "dr": "DeathRun (dr/deathrun)",
    "sg": "SurvivalGames (sg/survivalgames)",
    "ctf": "Capture The Flag (ctf)",
    "grav": "Gravity (grav/gravity)",
    "murder": "Murder (murder)",
    "drop": "Drop (drop)",
    "ground": "Ground War (ground)",
    "party": "Party Games (party)",
    "wars": "Wars (wars)",
}

# 実APIの生フィールド名 (PlayHive /v0/game/all/{game}/{UUID} のレスポンス)。
# 全キーは /v0/game/all/all/{UUID} の実データで確認済み (2026-07-18)。
# 共通: kills/deaths/victories/played/xp（一部ゲームではキー名が異なる）。
GAME_FIELDS: dict[str, list[tuple[str, str]]] = {
    "bed": [
        ("Kills", "kills"),
        ("Deaths", "deaths"),
        ("Victories", "victories"),
        ("Beds Destroyed", "beds_destroyed"),
        ("Final Kills", "final_kills"),
        ("Played", "played"),
        ("XP", "xp"),
    ],
    "sky": [
        ("Kills", "kills"),
        ("Deaths", "deaths"),
        ("Victories", "victories"),
        ("Ores Mined", "ores_mined"),
        ("Mystery Chests", "mystery_chests_destroyed"),
        ("Spells Used", "spells_used"),
        ("Played", "played"),
        ("XP", "xp"),
    ],
    "bridge": [
        ("Kills", "kills"),
        ("Deaths", "deaths"),
        ("Victories", "victories"),
        ("Goals", "goals"),
        ("Played", "played"),
        ("XP", "xp"),
    ],
    "murder": [
        ("Murders", "murders"),
        ("Deaths", "deaths"),
        ("Victories", "victories"),
        ("Murderer Eliminations", "murderer_eliminations"),
        ("Played", "played"),
        ("XP", "xp"),
    ],
    "sg": [
        ("Kills", "kills"),
        ("Deaths", "deaths"),
        ("Victories", "victories"),
        ("Crates", "crates"),
        ("Deathmatches", "deathmatches"),
        ("Cows", "cows"),
        ("Played", "played"),
        ("XP", "xp"),
    ],
    "dr": [
        ("Kills", "kills"),
        ("Deaths", "deaths"),
        ("Victories", "victories"),
        ("Checkpoints", "checkpoints"),
        ("Activated", "activated"),
        ("Played", "played"),
        ("XP", "xp"),
    ],
    "hide": [
        ("Deaths", "deaths"),
        ("Victories", "victories"),
        ("Hider Kills", "hider_kills"),
        ("Played", "played"),
        ("XP", "xp"),
    ],
    "ctf": [
        ("Kills", "kills"),
        ("Deaths", "deaths"),
        ("Victories", "victories"),
        ("Flags Captured", "flags_captured"),
        ("Flags Returned", "flags_returned"),
        ("Assists", "assists"),
        ("Played", "played"),
        ("XP", "xp"),
    ],
    "grav": [
        ("Deaths", "deaths"),
        ("Victories", "victories"),
        ("Maps Completed", "maps_completed"),
        ("Maps W/O Dying", "maps_completed_without_dying"),
        ("Played", "played"),
        ("XP", "xp"),
    ],
    "drop": [
        ("Deaths", "deaths"),
        ("Victories", "victories"),
        ("Blocks Destroyed", "blocks_destroyed"),
        ("Powerups", "powerups_collected"),
        ("Vaults Used", "vaults_used"),
        ("Played", "played"),
        ("XP", "xp"),
    ],
    "ground": [
        ("Kills", "kills"),
        ("Deaths", "deaths"),
        ("Victories", "victories"),
        ("Blocks Destroyed", "blocks_destroyed"),
        ("Blocks Placed", "blocks_placed"),
        ("Projectiles Fired", "projectiles_fired"),
        ("Played", "played"),
        ("XP", "xp"),
    ],
    "party": [
        ("Victories", "victories"),
        ("Powerups", "powerups_collected"),
        ("Rounds Survived", "rounds_survived"),
        ("Played", "played"),
        ("XP", "xp"),
    ],
    "wars": [
        ("Deaths", "deaths"),
        ("Treasure Destroyed", "treasure_destroyed"),
        ("Played", "played"),
        ("XP", "xp"),
    ],
}

# 共通フィールド（全モードに表示。実フィールド名に合わせる）
COMMON_FIELDS: list[tuple[str, str]] = [
    ("Kills", "kills"),
    ("Deaths", "deaths"),
    ("Victories", "victories"),
    ("Played", "played"),
    ("XP", "xp"),
]


def resolve_token(game: str) -> str | None:
    """入力されたゲーム名を実APIの game トークンに解決。未知なら None。"""
    return GAME_MODES.get(game.lower())


def available_tokens() -> list[str]:
    """メニュー表示用に重複を除いたトークン一覧を返す。"""
    seen: list[str] = []
    for token in GAME_MODES.values():
        if token not in seen:
            seen.append(token)
    return seen


@dataclass
class PlayerStats:
    player: str
    game: str
    raw: dict[str, Any] = field(default_factory=dict)
    kills: int = 0
    deaths: int = 0
    wins: int = 0
    losses: int = 0
    games_played: int = 0
    points: int = 0
    extra: dict[str, int] = field(default_factory=dict)
    cached: bool = False

    @property
    def kdr(self) -> float:
        return self.kills / self.deaths if self.deaths else float(self.kills)

    @property
    def win_rate(self) -> float:
        total = self.wins + self.losses
        return (self.wins / total * 100) if total else 0.0

    def fields(self) -> list[tuple[str, int]]:
        """表示用フィールド一覧: 共通 + モード別（extra から取得）。"""
        out: list[tuple[str, int]] = []
        for label, key in COMMON_FIELDS:
            value = getattr(self, key, 0) if hasattr(self, key) else self.extra.get(key, 0)
            out.append((label, int(value)))
        for label, key in GAME_FIELDS.get(self.game.lower(), []):
            if (label, key) in COMMON_FIELDS:
                continue
            out.append((label, int(self.extra.get(key, 0))))
        return out


class HiveAPIError(Exception):
    """API通信関連のエラー（CLI側で catch して表示用）。"""


class HiveAPIClient:
    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "hivetool/1.0 (+https://github.com/ASDF3001/hivetool)"}
        )

    def get_stats(self, player: str, game: str) -> PlayerStats:
        token = resolve_token(game) or game.lower()
        if USE_MOCK:
            raw = self._mock_stats(player, token)
            return self._parse(raw, player, token)
        # real API: serve from cache if fresh, mark cached when served
        uuid = self._resolve_uuid(player)
        cached = _cache_get(token, uuid)
        if cached:
            stats = self._parse(cached, player, token)
            stats.cached = True
            return stats
        raw = self._fetch_real(player, token)
        return self._parse(raw, player, token)

    # --- 実API（PlayHive） ---

    def _get(self, url: str, retries: int = 3) -> requests.Response:
        """GET し、429 なら Retry-After を読んで自動待機→リトライ。"""
        attempt = 0
        while True:
            try:
                resp = self.session.get(url, timeout=self.timeout)
            except requests.RequestException as e:
                raise HiveAPIError(f"APIに接続できませんでした（{e}）。\n"
                                  f"オフライン検証なら HIVETOOL_MOCK=1 にしてください。") from e
            if resp.status_code != 429:
                return resp
            attempt += 1
            if attempt > retries:
                raise HiveAPIError("レート制限にかかりました。しばらく待って再試行してください。")
            wait = resp.headers.get("Retry-After")
            try:
                wait_sec = int(wait) if wait else 60
            except ValueError:
                wait_sec = 60
            # 長すぎる待機は諦める（手動再試行を促す）
            if wait_sec > 600:
                raise HiveAPIError(
                    f"レート制限中です。約{wait_sec}秒後に再試行してください。"
                )
            err_console.print(f"[yellow]レート制限中…{wait_sec}秒待機してリトライします "
                              f"({attempt}/{retries})[/]")
            time.sleep(wait_sec)

    def _resolve_uuid(self, player: str) -> str:
        """プレイヤー名/UUID から UUID を解決。すでにUUIDならそのまま。"""
        if _looks_like_uuid(player):
            return player
        url = f"{BASE_URL}/v0/player/search/{player}"
        resp = self._get(url)
        if resp.status_code == 422:
            # 短すぎる等のバリデーションエラー
            raise HiveAPIError(f"プレイヤー名 '{player}' は無効です（4文字以上で指定）。")
        if resp.status_code != 200:
            raise HiveAPIError(f"プレイヤー '{player}' が見つかりません。")
        data = resp.json()
        if not data:
            raise HiveAPIError(f"プレイヤー '{player}' が見つかりません。")
        return data[0]["UUID"]

    def get_leaderboard_top(self, game: str) -> tuple[str, str]:
        """ゲームの世界ランキング1位 (username, uuid) を返す。"""
        token = resolve_token(game) or game.lower()
        if USE_MOCK:
            return ("TopPlayer", "00000000-0000-0000-0000-000000000000")
        url = f"{BASE_URL}/v0/game/leaderboard/{token}"
        resp = self._get(url)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            raise HiveAPIError(f"ゲーム '{game}' のリーダーボードが空です。")
        top = data[0]
        return top["username"], top["UUID"]

    def _fetch_real(self, player: str, game: str) -> dict[str, Any]:
        uuid = self._resolve_uuid(player)
        # cache: return fresh-enough stored data, skip rate limit
        cached = _cache_get(game, uuid)
        if cached:
            return cached
        url = f"{BASE_URL}/v0/game/all/{game}/{uuid}"
        resp = self._get(url)
        if resp.status_code == 404:
            raise HiveAPIError(f"ゲーム '{game}' のデータが見つかりません。")
        resp.raise_for_status()
        data = resp.json()
        # 未プレイ等で空リストが返る場合は「データなし」とする
        if not isinstance(data, dict) or not data:
            raise HiveAPIError(f"プレイヤー '{player}' の '{game}' のデータがありません（未プレイ？）。")
        _cache_set(game, uuid, data)
        return data

    def _parse(self, raw: dict[str, Any], player: str, game: str) -> PlayerStats:
        if not isinstance(raw, dict):
            return PlayerStats(player=player, game=game)
        extra: dict[str, int] = {}
        for _, key in GAME_FIELDS.get(game, []):
            if key in raw:
                extra[key] = raw[key] or 0
        return PlayerStats(
            player=player,
            game=game,
            raw=raw,
            kills=raw.get("kills", 0) or 0,
            deaths=raw.get("deaths", 0) or 0,
            wins=raw.get("victories", 0) or 0,
            losses=(raw.get("played", 0) or 0) - (raw.get("victories", 0) or 0),
            games_played=raw.get("played", 0) or 0,
            points=raw.get("xp", 0) or 0,
            extra=extra,
            cached=False,
        )

    # --- モック（開発・オフライン用） ---

    def _mock_stats(self, player: str, game: str) -> dict[str, Any]:
        rng = random.Random(f"{player}:{game}:{int(time.time() // 60)}")
        played = rng.randint(50, 5000)
        victories = rng.randint(0, played)
        kills = rng.randint(victories, victories * 20)
        deaths = rng.randint(played - victories, (played - victories) * 20) or 1
        data: dict[str, Any] = {
            "kills": kills,
            "deaths": deaths,
            "victories": victories,
            "played": played,
            "xp": rng.randint(1000, 999999),
            "first_played": rng.randint(1600000000, 1700000000),
        }
        for _, key in GAME_FIELDS.get(game, []):
            if key in data:
                continue
            # モード固有フィールドのダミー（bridge の goals 等）
            data[key] = rng.randint(0, max(1, played * 2))
        return data


def _looks_like_uuid(s: str) -> bool:
    """xxx-xxxx-... 形式（ハイフン含む36文字）か判定。"""
    return len(s) >= 32 and "-" in s
