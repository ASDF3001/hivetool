"""hivetool の CLI インターフェース (click)。"""

from __future__ import annotations

import os
import shutil
import subprocess
import time

import click
from rich.columns import Columns
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel

from .api import HiveAPIClient, HiveAPIError, resolve_token
from .config import (
    add_player,
    get_favorite_game,
    list_players,
    set_favorite_game,
)
from .prompt import select_game_mode, select_player_slot
from .render import console, render_stats

client = HiveAPIClient()
err = Console(stderr=True)

# 起動時に上書きしたくない依存ライブラリ
_REQUIRED_LIBS = ("click", "rich", "requests")


def _check_libs() -> None:
    """必須ライブラリが import できるか確認し、欠けていれば案内。"""
    missing = []
    for lib in _REQUIRED_LIBS:
        try:
            __import__(lib)
        except ImportError:
            missing.append(lib)
    if missing:
        err.print(
            f"[red]必須ライブラリが足りません: {', '.join(missing)}[/]\n"
            "[yellow]pip install -r requirements.txt を実行してください。[/]"
        )
        raise SystemExit(1)


def _maybe_self_update() -> None:
    """起動時に git pull で自己更新（未コミット変更があればスキップ）。"""
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    git = shutil.which("git")
    if not git:
        return
    if not os.path.isdir(os.path.join(repo, ".git")):
        return
    # 未コミット変更があれば上書きを避ける
    try:
        status = subprocess.run(
            [git, "-C", repo, "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
        )
    except (subprocess.SubprocessError, OSError):
        return
    if status.stdout.strip():
        err.print("[dim]未コミットの変更があるため自動更新をスキップしました。[/]")
        return
    try:
        result = subprocess.run(
            [git, "-C", repo, "pull", "--ff-only"],
            capture_output=True, text=True, timeout=30,
        )
    except (subprocess.SubprocessError, OSError):
        return
    if result.returncode == 0 and "Already up to date" not in result.stdout:
        err.print("[dim]更新を取得しました（次回起動から反映）。[/]")


def _resolve_game(gamemode: str | None) -> str:
    """ゲームモードを解決。未指定/未知ならメニューで選ばせる。"""
    if gamemode:
        token = resolve_token(gamemode)
        if token is None:
            err.print(f"[yellow]'{gamemode}' は未知のモードです。メニューから選択してください。[/]")
            return select_game_mode(get_favorite_game())
        return token
    fav = get_favorite_game()
    if fav:
        err.print(f"[dim]お気に入りモードを使用: {fav}（変更は add で）[/]")
        return fav
    return select_game_mode()


@click.group()
@click.version_option()
def main() -> None:
    """Hivemc 戦績表示CLIツール。"""
    _check_libs()
    _maybe_self_update()


@main.command()
@click.argument("player")
@click.argument("gamemode", required=False)
def stats(player: str, gamemode: str | None) -> None:
    """指定プレイヤーの戦績を表示する。ゲームモード省略可。"""
    try:
        token = _resolve_game(gamemode)
        result = client.get_stats(player, token)
    except HiveAPIError as e:
        err.print(f"[red]{e}[/]")
        raise SystemExit(1)
    console.print(render_stats(result))


@main.command()
@click.argument("player")
@click.argument("gamemode", required=False)
@click.option("--interval", default=300, show_default=True, help="更新間隔（秒）。最小10秒。")
def watch(player: str, gamemode: str | None, interval: int) -> None:
    """戦績を自動更新し、差分を表示する。ゲームモード省略可。"""
    if interval < 10:
        interval = 10
    try:
        token = _resolve_game(gamemode)
    except HiveAPIError as e:
        err.print(f"[red]{e}[/]")
        raise SystemExit(1)
    prev = None
    err.print(f"watching {player} ({token}) — Ctrl-C で終了")
    try:
        with Live(refresh_per_second=4) as live:
            live.update(Panel("[dim]取得中...[/]", title=f"{player} — {token}"))
            while True:
                try:
                    cur = client.get_stats(player, token)
                except HiveAPIError as e:
                    live.update(Panel(f"[red]{e}[/]", title=f"{player} — {token}"))
                    time.sleep(interval)
                    continue
                live.update(render_stats(cur, prev))
                prev = cur
                time.sleep(interval)
    except KeyboardInterrupt:
        err.print("終了しました。")


@main.command()
@click.argument("player")
def add(player: str) -> None:
    """プレイヤー名とお気に入りゲームモードを保存する。"""
    players = add_player(player)
    err.print(f"[green]プレイヤーを保存: {player}[/]")
    err.print(f"保存済み: {', '.join(players)}")
    token = select_game_mode(get_favorite_game())
    set_favorite_game(token)
    err.print(f"[green]お気に入りモードを設定: {token}[/]")


@main.command(name="list")
def list_cmd() -> None:
    """保存済みプレイヤーとお気に入りモードを表示する。"""
    players = list_players()
    fav = get_favorite_game()
    if not players:
        err.print("保存されたプレイヤーはいません。")
        return
    for p in players:
        err.print(f"- {p}")
    if fav:
        err.print(f"お気に入りモード: {fav}")


@main.command()
@click.argument("gamemode", required=False)
@click.option("--interval", default=300, show_default=True, help="更新間隔（秒）。最小10秒。")
@click.option("--slots", default=2, show_default=True, help="枠数（2〜4）。")
def multiwatch(gamemode: str | None, interval: int, slots: int) -> None:
    """複数プレイヤーを同時視聴（2〜4枠）。指定/世界トップをCUIで選択。"""
    if interval < 10:
        interval = 10
    slots = max(2, min(4, slots))
    try:
        token = _resolve_game(gamemode)
    except HiveAPIError as e:
        err.print(f"[red]{e}[/]")
        raise SystemExit(1)

    # 各枠のプレイヤーを決定（'__TOP__' は世界1位）
    chosen: list[str | None] = []
    names: list[str] = []
    for i in range(1, slots + 1):
        sel = select_player_slot(i)
        if sel is None:
            continue
        if sel == "__TOP__":
            try:
                username, uuid = client.get_leaderboard_top(token)
                chosen.append(uuid)
                names.append(f"{username} (世界1位)")
            except HiveAPIError as e:
                err.print(f"[red]枠{i}: {e}[/]")
                continue
        else:
            chosen.append(sel)
            names.append(sel)
    chosen = [c for c in chosen if c]
    if not chosen:
        err.print("プレイヤーが選択されませんでした。")
        raise SystemExit(1)

    err.print(f"multiwatch: {', '.join(names)} ({token}) — Ctrl-C で終了")
    prev_map: dict[str, object] = {}
    try:
        with Live(refresh_per_second=4) as live:
            while True:
                stats_list = []
                for name, ident in zip(names, chosen):
                    try:
                        cur = client.get_stats(ident, token)
                    except HiveAPIError as e:
                        stats_list.append(Panel(f"[red]{e}[/]", title=name))
                        continue
                    prev = prev_map.get(ident)
                    stats_list.append(render_stats(cur, prev))
                    prev_map[ident] = cur
                live.update(Columns(stats_list, equal=True, column_first=False))
                time.sleep(interval)
    except KeyboardInterrupt:
        err.print("終了しました。")


if __name__ == "__main__":
    main()
