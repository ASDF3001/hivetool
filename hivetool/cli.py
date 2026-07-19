"""hivetool の CLI インターフェース (click)。"""

from __future__ import annotations

import importlib.metadata as md
import os
import shutil
import subprocess
import time

import click
from rich.columns import Columns
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel

from .api import HiveAPIClient, HiveAPIError, USE_MOCK, resolve_token
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


def _git_pull(repo: str) -> str | None:
    """git pull --ff-only を実行。戻り値: 'updated' / 'uptodate' / 'skipped' / 'nogit' / 'error'。"""
    git = shutil.which("git")
    if not git:
        return "nogit"
    if not os.path.isdir(os.path.join(repo, ".git")):
        return "nogit"
    # 未コミット変更があれば上書きを避ける
    try:
        status = subprocess.run(
            [git, "-C", repo, "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
        )
    except (subprocess.SubprocessError, OSError):
        return "error"
    if status.stdout.strip():
        return "skipped"
    try:
        result = subprocess.run(
            [git, "-C", repo, "pull", "--ff-only"],
            capture_output=True, text=True, timeout=60,
        )
    except (subprocess.SubprocessError, OSError):
        return "error"
    if result.returncode != 0:
        return "error"
    if "Already up to date" in result.stdout or "Already up-to-date" in result.stdout:
        return "uptodate"
    return "updated"


def _maybe_self_update() -> None:
    """起動時に git pull で自己更新（未コミット変更があればスキップ）。"""
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    res = _git_pull(repo)
    if res == "updated":
        err.print("[dim]更新を取得しました（次回起動から反映）。[/]")
    elif res == "skipped":
        err.print("[dim]未コミットの変更があるため自動更新をスキップしました。[/]")


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
@click.version_option(version="0.1.0")
def main() -> None:
    """hivetool — PlayHive 公式APIから戦績を取得し、ターミナルに表示するCLI。

    コマンド:
      stats     プレイヤー1人の戦績を表示
      watch     戦績を自動更新し差分を表示
      multiwatch 2〜4人を同時視聴
      add       プレイヤー名とお気に入りモードを保存
      list      保存済みプレイヤーを表示

    実APIを使うには環境変数 HIVETOOL_MOCK=0 を設定してください
    （未設定時はモックデータになります）。
    詳しくは README.md / README_ja.md を参照。
    """
    _check_libs()
    _maybe_self_update()


@main.command()
@click.argument("player")
@click.argument("gamemode", required=False)
def stats(player: str, gamemode: str | None) -> None:
    """指定プレイヤーの戦績を表示する。

    PLAYER: プレイヤー名またはUUID
    GAMEMODE: 省略可（bed/sky/bridge 等、エイリアス可）。
    省略時はお気に入りモード、または選択メニューになります。
    """
    try:
        token = _resolve_game(gamemode)
        result = client.get_stats(player, token)
    except HiveAPIError as e:
        err.print(f"[red]{e}[/]")
        raise SystemExit(1)
    console.print(render_stats(result, mock=USE_MOCK))


@main.command()
@click.argument("player")
@click.argument("gamemode", required=False)
@click.option("--interval", default=300, show_default=True, help="更新間隔（秒）。最小10秒。")
def watch(player: str, gamemode: str | None, interval: int) -> None:
    """戦績を自動更新し、前回からの差分を表示する。

    PLAYER: プレイヤー名またはUUID
    GAMEMODE: 省略可（bed/sky/bridge 等）。
    --interval: 更新間隔（秒、デフォルト300）。最小10秒。
    増加は緑、減少は赤で表示されます。Ctrl-C で終了。
    """
    if interval < 10:
        interval = 10
    try:
        token = _resolve_game(gamemode)
    except HiveAPIError as e:
        err.print(f"[red]{e}[/]")
        raise SystemExit(1)
    mode_badge = "[dim yellow][MOCK][/]" if USE_MOCK else ""
    prev = None
    err.print(f"watching {player} ({token}) {mode_badge}— Ctrl-C で終了")
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
                live.update(render_stats(cur, prev, mock=USE_MOCK))
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
def update() -> None:
    """hivetool 自身を最新版に強制更新する。

    GitHub から git pull で取得し、pipx で再インストールします。
    未コミットの変更がある場合は上書きを避けてスキップします。
    """
    try:
        ver = md.version("hivetool")
    except md.PackageNotFoundError:
        ver = "不明"
    err.print(f"[bold]hivetool 更新チェック[/]  (現在: v{ver})")

    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    with err.status("[cyan]GitHub から更新を確認中...[/]"):
        res = _git_pull(repo)
    if res == "updated":
        err.print("[green]✔ 新しい更新を取得しました[/]")
    elif res == "uptodate":
        err.print("[green]✔ すでに最新版です[/]")
        return
    elif res == "skipped":
        err.print("[yellow]⚠ 未コミットの変更があるためスキップしました（更新を反映させるには commit または stash してください）[/]")
        return
    elif res == "nogit":
        err.print("[yellow]⚠ git が見つからないか、git リポジトリではありません。手動で更新してください。[/]")
        return
    else:
        err.print("[red]✘ 更新チェックに失敗しました[/]")
        raise SystemExit(1)

    # pipx で再インストール（pip みたいな進捗表示）
    pipx = shutil.which("pipx")
    if not pipx:
        err.print("[yellow]⚠ pipx が見つかりません。手動で `pipx install <repo> --force` を実行してください。[/]")
        return
    err.print("[cyan]pipx で再インストール中...[/]")
    try:
        proc = subprocess.run(
            [pipx, "install", repo, "--force"],
            capture_output=True, text=True, timeout=300,
        )
    except (subprocess.SubprocessError, OSError) as e:
        err.print(f"[red]✘ 再インストールに失敗: {e}[/]")
        raise SystemExit(1)
    if proc.returncode == 0:
        err.print("[green]✔ 更新完了！次回起動から最新版が反映されます。[/]")
    else:
        err.print("[red]✘ 再インストールに失敗しました:[/]")
        err.print(proc.stderr.strip() or proc.stdout.strip())


@main.command()
@click.argument("gamemode", required=False)
@click.option("--interval", default=300, show_default=True, help="更新間隔（秒）。最小10秒。")
@click.option("--slots", default=2, show_default=True, help="枠数（2〜4）。")
def multiwatch(gamemode: str | None, interval: int, slots: int) -> None:
    """複数プレイヤーを同時視聴（2〜4枠）。

    GAMEMODE: 省略可（bed/sky/bridge 等）。
    --interval: 更新間隔（秒、デフォルト300）。最小10秒。
    --slots: 枠数（2〜4）。
    各枠でプレイヤー名 / top（世界1位）/ 空Enter（スキップ）を選択。
    """
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
                    stats_list.append(render_stats(cur, prev, mock=USE_MOCK))
                    prev_map[ident] = cur
                live.update(Columns(stats_list, equal=True, column_first=False))
                time.sleep(interval)
    except KeyboardInterrupt:
        err.print("終了しました。")


if __name__ == "__main__":
    main()
