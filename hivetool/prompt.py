"""対話メニュー選択のヘルパー（rich + click.prompt）。"""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from .api import GAME_LABELS, available_tokens

console = Console()


def select_game_mode(default_token: str | None = None) -> str:
    """利用可能なゲームモードを番号メニューで表示し、選ばせてトークンを返す。

    default_token が指定されていれば、それを '[Enter]で選択' の既定値にする。
    """
    tokens = available_tokens()
    table = Table(title="ゲームモードを選択", show_lines=False)
    table.add_column("#", justify="right", style="bold cyan")
    table.add_column("モード")
    for i, tok in enumerate(tokens, 1):
        mark = " ★" if tok == default_token else ""
        table.add_row(str(i), GAME_LABELS.get(tok, tok) + mark)
    console.print(table)

    default_hint = ""
    if default_token:
        idx = tokens.index(default_token) + 1
        default_hint = f" (既定: {idx})"
    while True:
        choice = console.input(f"[cyan]番号を入力{default_hint}: [/]").strip()
        if not choice and default_token:
            return default_token
        if not choice.isdigit():
            console.print("[red]数字を入力してください。[/]")
            continue
        n = int(choice)
        if 1 <= n <= len(tokens):
            return tokens[n - 1]
        console.print(f"[red]{n} は範囲外です。[/]")


def select_player_slot(slot_index: int, default_player: str | None = None) -> str | None:
    """1つの枠のプレイヤーを選ばせる。

    戻り値: プレイヤー名/UUID。空入力でスキップ（その枠を使わない）なら None。
    """
    console.print(f"\n[bold cyan]枠 {slot_index} のプレイヤー[/]")
    console.print("  [dim]プレイヤー名を入力、'top' で世界1位、空Enterでスキップ[/]")
    while True:
        choice = console.input("[cyan]> [/]").strip()
        if not choice:
            return None
        if choice.lower() == "top":
            return "__TOP__"
        if len(choice) < 4 and not _looks_like_uuid(choice):
            console.print("[red]プレイヤー名は4文字以上、またはUUIDを入力してください。[/]")
            continue
        return choice


def _looks_like_uuid(s: str) -> bool:
    return len(s) >= 32 and "-" in s
