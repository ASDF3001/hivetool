# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Fixed
- `watch`/`stats` mixing mock and real API (huge delta values): added a `[MOCK]` badge to the title and documented that `HIVETOOL_MOCK=0` is required for real data
- `render_stats` KDR/WinRate delta showing `-0.00` due to float rounding error
- `add` command crashing with `ValueError` when the favorite game was unset or an unknown token

### Changed
- UI polish: emphasised section divider, bold KDR/WinRate rows, per-line green ▲ / red ▼ delta summary
- Richer per-command `--help` text (arguments and options explained)

### Added
- `install.ps1` (Windows / PowerShell installer): python → pipx install, `pipx install`, user Path registration (confirmation)
- `hivetool update` command: force-update from GitHub via `git pull` → pipx reinstall (pip-style progress, skips on uncommitted changes)
- `install.sh`: pipx-based install, dependency check, PATH registration to rc files (confirmation)
- Launch-time auto-update (`git pull --ff-only`, skips if dirty)
- Launch-time required-library check (click / rich / requests)
- README split ja/en (README.md = English, README_ja.md / README_en.md)
- One-line install: `bash <(curl -fsSL https://raw.githubusercontent.com/ASDF3001/hivetool/master/install.sh)`
- PlayHive API rate-limit (429) handling: read `Retry-After` header and auto-wait + retry (max 3, bail if >600s)
- Custom User-Agent on real API requests (`hivetool/1.0`)
- `install.sh` hardening: `pyproject.toml` existence check, trailing-slash trim on `REPO_DIR`
- `watch` / `multiwatch` default poll interval changed 120s → 300s (PlayHive rate-limit mitigation)
- `multiwatch` slot cap raised to 4 (`--slots 2..4`)
- Local cache layer: real API responses are stored under `~/.hivetool/cache/<game>/<uuid>.json` with a 300s TTL, and polls serve from cache to avoid rate limits (429). A `[CACHE]` badge shows on the title when served from cache
- `hivetool history <player> [gamemode]` command: records every `watch`/`multiwatch` poll under `~/.hivetool/history/` and shows "when / what changed" for the last N entries (`--limit`; up = green, down = red)

## [0.1.0] - 2026-07-18

### Added
- Initial release
- `stats` / `watch` / `multiwatch` / `add` / `list` commands
- PlayHive official API (`api.playhive.com`) support, 13 game modes + aliases
- Mock / real API toggle (`HIVETOOL_MOCK` env var)
- Verified real field names for all 13 games
