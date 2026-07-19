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

## Game modes

`bed`(BedWars) / `sky`(SkyWars) / `bridge` / `hide`(BlockHide) / `dr`(DeathRun) /
`sg`(SurvivalGames) / `ctf`(Capture The Flag) / `grav`(Gravity) / `murder` /
`drop` / `ground`(Ground War) / `party`(Party Games) / `wars`(Wars)

Aliases: `bedwars`→`bed`, `skywars`→`sky`, `blockhide`→`hide`, `deathrun`→`dr`,
`survivalgames`→`sg`, `gravity`→`grav`, and more.

## Setup

### Easiest install (recommended)

Open a terminal and paste this one line, then press Enter:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/ASDF3001/hivetool/master/install.sh)
```

This automatically installs python → pipx and makes the `hivetool` command available.

Then open a new terminal to verify:

```bash
hivetool stats Notch bed
```

If you see real stats, install succeeded! (If it can't reach the API, see "What is real-API mode?" below.)

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

---

## What is real-API mode? (vs. mock)

hivetool has **two modes**.

| Mode | What it does | When to use |
| --- | --- | --- |
| **Real API** (default) | Fetches **real stats** from the PlayHive API | This is the normal one (when you want a friend's actual wins/losses) |
| **Mock** (`HIVETOOL_MOCK=1`) | Random dummy data generated in-code | Offline testing / development only |

**The default is the real API.** If you run `hivetool stats Notch bed` with no env var, you get the actual stats right away.

### Only when you need dummy data (offline, etc.)

**Set `HIVETOOL_MOCK=1`:**

```bash
HIVETOOL_MOCK=1 hivetool stats Notch bed
```

### How to tell (badges)

- `[MOCK]` → dummy data (not the real API)
- `[CACHE]` → real-API result served from cache (see below)

### Under the hood

- Endpoint: `https://api.playhive.com` (the old `api.hivemc.com` is defunct).
- Stats: `GET /v0/game/all/{game}/{UUID}` (a username is auto-resolved to a UUID via `/v0/player/search/{partial}`).
- Leaderboard: `GET /v0/game/leaderboard/{game}`.

### Rate limiting

The PlayHive API rate-limits per `game + player` combination. Rapid repeated requests to the same combination return `429 Too Many Attempts` and lock you out for a while. Normal interactive use is fine; space out requests when scripting.

### Local cache mitigates rate limits

In real-API mode (`HIVETOOL_MOCK=0`), fetched stats are cached under `~/.hivetool/cache/<game>/<uuid>.json` for **300 seconds**. Re-fetching the same combination within 300s serves from cache, so consecutive `watch` polls rarely hit 429. A `[CACHE]` badge shows on the title when served from cache.

## Real field names (verified)

Per-game raw field names are defined in `GAME_FIELDS` in `hivetool/api.py`.
Common: `kills` / `deaths` / `victories` / `played` / `xp`.
Mode-specific examples: `beds_destroyed`(bed), `murders`(murder), `goals`(bridge),
`flags_captured`(ctf), `maps_completed`(grav), etc.

## License

MIT
