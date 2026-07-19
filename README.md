# hivetool

[日本語 / Japanese](README_ja.md) | [English](README_en.md)

A CLI tool that fetches PlayHive (formerly Hivemc) stats from the official API and displays them beautifully in the terminal with `rich`.

## Commands

- `hivetool stats <player> [gamemode]` — Show a player's stats (with computed values like KDR / win rate). Gamemode is optional (uses favorite or a menu).
- `hivetool watch <player> [gamemode]` — Auto-refresh every 300s (default), showing deltas since the last refresh (green = up, red = down).
- `hivetool multiwatch [gamemode]` — Watch 2–4 slots side by side (`--slots 2..4`). Per slot, pick a player name / `top` (world #1) / blank Enter (skip) via the CUI menu.
- `hivetool add <player>` — Save a player name and favorite gamemode to `~/.hivetool/config.json`.
- `hivetool list` — Show saved players and the favorite mode.

## Game modes

`bed`(BedWars) / `sky`(SkyWars) / `bridge` / `hide`(BlockHide) / `dr`(DeathRun) /
`sg`(SurvivalGames) / `ctf`(Capture The Flag) / `grav`(Gravity) / `murder` /
`drop` / `ground`(Ground War) / `party`(Party Games) / `wars`(Wars)

Aliases: `bedwars`→`bed`, `skywars`→`sky`, `blockhide`→`hide`, `deathrun`→`dr`,
`survivalgames`→`sg`, `gravity`→`grav`, and more.

## Setup

### One-line install (direct URL)

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/ASDF3001/hivetool/master/install.sh)
```

### Or clone + run

```bash
git clone https://github.com/ASDF3001/hivetool.git
cd hivetool
bash install.sh
```

`install.sh` installs via pipx and, after a confirmation prompt, appends the pipx PATH to your shell rc files (`.zshrc`/`.bashrc`).
To do it manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Auto-update on launch

Every time `hivetool` runs, it does a `git pull --ff-only` to fetch updates.
If you have **uncommitted changes** in the repo, the auto-update is skipped so your work is never overwritten.
The required libraries (`click`, `rich`, `requests`) are also checked at launch; a missing one prints an install hint and exits.


## Real API notes

- Endpoint: `https://api.playhive.com` (the old `api.hivemc.com` is defunct).
- Stats: `GET /v0/game/all/{game}/{UUID}` (resolve a username to a UUID via `/v0/player/search/{partial}`).
- Leaderboard: `GET /v0/game/leaderboard/{game}`.

### Mock / real API toggle

Switch with an environment variable (no code change needed):

```bash
HIVETOOL_MOCK=1  python -m hivetool.cli stats Notch bed   # mock (default, works offline)
HIVETOOL_MOCK=0  python -m hivetool.cli stats Notch bed   # real API
```

### Rate limiting

The PlayHive API rate-limits per `game + player` combination. Rapid repeated requests to the same combination return `429 Too Many Attempts` and lock you out for a while. Normal interactive use (a human running `stats`) is fine; space out requests when scripting.

## Real field names (verified)

Per-game raw field names are defined in `GAME_FIELDS` in `hivetool/api.py`.
Common: `kills` / `deaths` / `victories` / `played` / `xp`.
Mode-specific examples: `beds_destroyed`(bed), `murders`(murder), `goals`(bridge),
`flags_captured`(ctf), `maps_completed`(grav), etc.

## License

MIT
