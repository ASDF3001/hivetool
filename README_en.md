# hivetool

[日本語 / Japanese](README_ja.md) | [English](README_en.md)

A CLI tool that fetches PlayHive (formerly Hivemc) stats from the official API and displays them beautifully in the terminal with `rich`.

## Commands

- `hivetool stats <player> [gamemode]` — Show a player's stats (with computed values like KDR / win rate). Gamemode is optional (uses favorite or a menu).
- `hivetool watch <player> [gamemode]` — Auto-refresh every 300s (default), showing deltas since the last refresh (green = up, red = down).
- `hivetool multiwatch [gamemode]` — Watch 2–4 slots side by side (`--slots 2..4`). Per slot, pick a player name / `top` (world #1) / blank Enter (skip) via the CUI menu.
- `hivetool add <player>` — Save a player name and favorite gamemode to `~/.hivetool/config.json`.
- `hivetool list` — Show saved players and the favorite mode.
- `hivetool history <player> [gamemode]` — Show the `watch`/`multiwatch` poll history (when / what changed; `--limit` sets the count).
- `hivetool update` — Force-update hivetool itself (git pull from GitHub → pipx reinstall). Skips if you have uncommitted changes.

## Game modes

`bed`(BedWars) / `sky`(SkyWars) / `bridge` / `hide`(BlockHide) / `dr`(DeathRun) /
`sg`(SurvivalGames) / `ctf`(Capture The Flag) / `grav`(Gravity) / `murder` /
`drop` / `ground`(Ground War) / `party`(Party Games) / `wars`(Wars)

Aliases: `bedwars`→`bed`, `skywars`→`sky`, `blockhide`→`hide`, `deathrun`→`dr`,
`survivalgames`→`sg`, `gravity`→`grav`, and more.

## Setup

### 🚀 Easiest install (recommended)

Open a terminal and paste this one line, then press Enter:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/ASDF3001/hivetool/master/install.sh)
```

This automatically installs python → pipx and makes the `hivetool` command available.
(If you're asked `Append PATH? [Y/n]` during install, press `Y`.)

Then open a new terminal to verify:

```bash
hivetool stats Notch bed
```

If you see `[MOCK]`, install succeeded! (What that dummy data means is covered below in "What is real-API mode?")

---

### 🪟 On Windows (PowerShell)

No admin rights needed. Open PowerShell and run:

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

> Note: `install.ps1` is untested on Linux/macOS. If it doesn't work on Windows, please report it in an issue.

---

### 💻 More manual: clone + run

```bash
git clone https://github.com/ASDF3001/hivetool.git
cd hivetool
bash install.sh
```

---

### ⬆️ Already installed but it's an old version? (update)

If you have the `hivetool update` command (v0.1.0+), just run it:

```bash
hivetool update
```

Older installs don't have `update`, so force-reinstall instead:

```bash
curl -fsSL https://raw.githubusercontent.com/ASDF3001/hivetool/master/install.sh -o /tmp/install.sh
bash /tmp/install.sh
```

(The one-liner `bash <(curl ...)` breaks `install.sh`'s path resolution, so we download it to a file first.)

---

### 🔧 For developers (run directly in a venv)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 🔄 Auto-update on launch

Every time `hivetool` runs, it does a `git pull --ff-only` to fetch updates.
If you have **uncommitted changes** in the repo, the auto-update is skipped so your work is never overwritten.
The required libraries (`click`, `rich`, `requests`) are also checked at launch; a missing one prints an install hint and exits.

---

## What is real-API mode? (vs. mock)

hivetool has **two modes**.

| Mode | What it does | When to use |
| --- | --- | --- |
| **Mock** (`HIVETOOL_MOCK=1`) | Random dummy data generated in-code | Install check, offline, development |
| **Real API** (`HIVETOOL_MOCK=0`) | Fetches **real stats** from the PlayHive API | When you want to see a friend's actual wins/losses |

**The default is mock (dummy data).** If you run `hivetool stats Notch bed` with no env var, you get made-up numbers (they look real but they're fake).

### To see real stats

**Always set `HIVETOOL_MOCK=0`:**

```bash
HIVETOOL_MOCK=0 hivetool stats Notch bed
HIVETOOL_MOCK=0 hivetool watch Notch bridge
```

Tired of typing `HIVETOOL_MOCK=0` every time? Persist it by adding one line to your shell rc (`.zshrc` / `.bashrc`):

```bash
echo 'export HIVETOOL_MOCK=0' >> ~/.zshrc
source ~/.zshrc
```

### How to tell (badges)

The title shows a badge so you know at a glance:

- `[MOCK]` → dummy data (not the real API)
- `[CACHE]` → real-API result served from cache (see below)

### Under the hood

- Endpoint: `https://api.playhive.com` (the old `api.hivemc.com` is defunct).
- Stats: `GET /v0/game/all/{game}/{UUID}` (a username is auto-resolved to a UUID via `/v0/player/search/{partial}`).
- Leaderboard: `GET /v0/game/leaderboard/{game}`.

### ⚠️ Rate limiting

The PlayHive API rate-limits per `game + player` combination. Rapid repeated requests to the same combination return `429 Too Many Attempts` and lock you out for a while. Normal interactive use (a human running `stats`) is fine; space out requests when scripting.

### 💾 Local cache mitigates rate limits

In real-API mode (`HIVETOOL_MOCK=0`), fetched stats are cached under `~/.hivetool/cache/<game>/<uuid>.json` for **300 seconds**.
Re-fetching the same combination within 300s returns the cached data without hitting the API, so consecutive `watch` polls are far less likely to hit 429.
When served from cache, a `[CACHE]` badge appears in the title (the cache refreshes automatically once the TTL expires).

## Real field names (verified)

Per-game raw field names are defined in `GAME_FIELDS` in `hivetool/api.py`.
Common: `kills` / `deaths` / `victories` / `played` / `xp`.
Mode-specific examples: `beds_destroyed`(bed), `murders`(murder), `goals`(bridge),
`flags_captured`(ctf), `maps_completed`(grav), etc.

## License

MIT

## Changelog

See [CHANGELOG_en.md](CHANGELOG_en.md).
