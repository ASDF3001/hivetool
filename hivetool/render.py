"""rich を使った戦績の表示。"""

from __future__ import annotations

from datetime import datetime

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table

from .api import COMMON_FIELDS, GAME_FIELDS, GAME_LABELS, PlayerStats

console = Console()


def _delta_text(cur: int, prev: int | None) -> str:
    """現在値に差分を色付きで付加する。変化なしなら通常色。"""
    text = f"{cur:,}"
    if prev is None or cur == prev:
        return text
    delta = cur - prev
    color = "green" if delta > 0 else "red"
    sign = "+" if delta > 0 else ""
    return f"{text} [{color}]({sign}{delta:,})[/]"


def render_stats(stats: PlayerStats, diff: PlayerStats | None = None) -> Panel:
    """戦績を Panel + Table で表示。diff があれば差分を色付きで付記する。

    - 共通フィールド + モード別フィールドを stats.fields() から表示
    - 増加は緑、減少は赤、変化なしは通常色
    - ヘッダーに増加項目のサマリーを表示
    """
    prev_map = dict(diff.fields()) if diff is not None else {}
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold cyan")
    table.add_column(justify="right")

    # 共通フィールド（全モード累計）
    common_labels = {label for label, _ in COMMON_FIELDS}
    for label, value in stats.fields():
        if label not in common_labels:
            continue
        prev = prev_map.get(label)
        if prev is None and diff is not None:
            prev = next((v for l, v in diff.fields() if l == label), None)
        table.add_row(label, _delta_text(value, prev))

    # モード別フィールド（セクション区切り）
    mode_fields = GAME_FIELDS.get(stats.game.lower(), [])
    if mode_fields:
        section_label = GAME_LABELS.get(stats.game.lower(), stats.game.upper())
        table.add_section()
        table.add_row(f"[dim]{section_label} 専用統計[/]", "")
        for label, value in stats.fields():
            if label in common_labels:
                continue
            prev = prev_map.get(label)
            if prev is None and diff is not None:
                prev = next((v for l, v in diff.fields() if l == label), None)
            table.add_row(label, _delta_text(value, prev))

    # 計算値
    table.add_row("KDR", _calc_delta(stats.kdr, diff.kdr if diff else None, "{:.2f}"))
    table.add_row("Win Rate", _calc_delta(stats.win_rate, diff.win_rate if diff else None, "{:.1f}%"))

    title = f"[bold]{stats.player}[/] — {GAME_LABELS.get(stats.game.lower(), stats.game.upper())}"
    footer = f"取得: {datetime.now().strftime('%H:%M:%S')}"

    if diff is not None:
        summary = _diff_summary(stats, diff)
        footer = Group(summary, footer)
    return Panel(
        Group(table, footer),
        title=title,
        border_style="magenta",
    )


def _calc_delta(cur: float, prev: float | None, fmt: str) -> str:
    text = fmt.format(cur)
    if prev is None:
        return text
    if fmt.format(cur) == fmt.format(prev):
        return text
    delta = cur - prev
    color = "green" if delta > 0 else "red"
    sign = "+" if delta > 0 else ""
    return f"{text} [{color}]({sign}{fmt.format(delta)})[/]"


def _diff_summary(cur: PlayerStats, prev: PlayerStats) -> str:
    """増加した項目を1行サマリーにまとめる（なければ '変化なし'）。"""
    cmap = dict(cur.fields())
    pmap = dict(prev.fields())
    parts: list[str] = []
    for label, value in cmap.items():
        d = value - pmap.get(label, value)
        if d != 0:
            color = "green" if d > 0 else "red"
            sign = "+" if d > 0 else ""
            parts.append(f"[{color}]{label} {sign}{d:,}[/{color}]")
    if not parts:
        return "[dim]変化なし[/]"
    return "Δ " + "  ".join(parts)


def render_leaderboard(rows: list[dict]) -> Table:
    table = Table(title="Leaderboard")
    table.add_column("#", justify="right")
    table.add_column("Player")
    table.add_column("Points", justify="right")
    for i, row in enumerate(rows, 1):
        table.add_row(str(i), row.get("name", "?"), f"{row.get('points', 0):,}")
    return table
