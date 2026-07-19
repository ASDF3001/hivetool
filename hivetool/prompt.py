"""対話メニュー選択のヘルパー（rich + click.prompt）。"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .api import GAME_LABELS, available_tokens

console = Console()

# 枠ごとのカラー（GUI 負けしない派手さ）
SLOT_COLORS = ["cyan", "green", "yellow", "magenta"]


def select_game_mode(default_token: str | None = None) -> str:
    """利用可能なゲームモードを番号メニューで表示し、選ばせてトークンを返す。

    default_token が指定されていれば、それを '[Enter]で選択' の既定値にする。
    """
    tokens = available_tokens()
    table = Table(title="ゲームモードを選択", show_lines=False, border_style="cyan")
    table.add_column("#", justify="right", style="bold cyan", width=4)
    table.add_column("モード", style="bold")
    for i, tok in enumerate(tokens, 1):
        mark = " [green]★[/]" if tok == default_token else ""
        table.add_row(str(i), GAME_LABELS.get(tok, tok) + mark)
    console.print(table)

    default_hint = ""
    if default_token:
        idx = tokens.index(default_token) + 1
        default_hint = f" [dim](既定: {idx})[/]"
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
    color = SLOT_COLORS[(slot_index - 1) % len(SLOT_COLORS)]
    panel = Panel(
        "[dim]プレイヤー名 または UUID を入力[/]\n"
        "[bold]top[/] → 世界1位を自動選択\n"
        "[bold]空 Enter[/] → この枠をスキップ",
        title=f"[bold {color}]枠 {slot_index}[/]",
        border_style=color,
        padding=(1, 2),
    )
    console.print(panel)
    while True:
        prompt = f"[bold {color}]枠 {slot_index} > [/]" if not default_player \
            else f"[bold {color}]枠 {slot_index} (既定: {default_player}) > [/]"
        choice = console.input(prompt).strip()
        if not choice:
            if default_player:
                return default_player
            console.print(f"[dim]{color and ''}枠 {slot_index} をスキップします。[/]")
            return None
        if choice.lower() == "top":
            return "__TOP__"
        if len(choice) < 4 and not _looks_like_uuid(choice):
            console.print("[red]プレイヤー名は4文字以上、またはUUIDを入力してください。[/]")
            continue
        return choice


def _looks_like_uuid(s: str) -> bool:
    """xxx-xxxx-... 形式（ハイフン含む36文字）か判定。"""
    return len(s) >= 32 and "-" in s
