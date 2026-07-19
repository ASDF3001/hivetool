# Changelog

すべての notable な変更をここに記録します。
形式は [Keep a Changelog](https://keepachangelog.com/) に準拠しています。

## [Unreleased]

### Fixed
- `watch`/`stats` で mock と実API が混ざって桁違いの差分が出るバグを修正: タイトルに `[MOCK]` バッジを表示し、実行時に `HIVETOOL_MOCK=0` が必須なことを明示
- `render_stats` の KDR/WinRate 差分表示で float 丸め誤差による `-0.00` 表示を修正

### Changed
- UI ブラッシュアップ: セクション区切りの強調、KDR/WinRate を太字強調行に、差分サマリーを行ごとに ▲緑/▼赤 で色分け
- 各コマンドの `--help` を充実（引数・オプションの説明追加）

### Added
- `install.sh`: pipx 経由のインストール、依存チェック、rc ファイルへの PATH 登録（確認付き）
- 起動時の自動更新（`git pull --ff-only`、未コミット変更があればスキップ）
- 起動時の必須ライブラリチェック（click / rich / requests）
- README の ja/en 分割（README.md = 英語、README_ja.md / README_en.md）
- 直 URL インストール対応: `bash <(curl -fsSL https://raw.githubusercontent.com/ASDF3001/hivetool/master/install.sh)`

### Changed
- `watch` / `multiwatch` のデフォルト更新間隔を 120s → 300s に変更（PlayHive API のレート制限対策）
- `multiwatch` のスロット数上限を 4 に拡張（`--slots 2..4`）

### Fixed
- PlayHive API のレート制限（429）時に `Retry-After` ヘッダーを読み取り、自動待機→リトライするよう修正（最大3回、600秒超は即諦め）
- 実 API リクエストにカスタム User-Agent を設定（`hivetool/1.0`）
- `install.sh` の堅牢化: `pyproject.toml` 存在チェック、`REPO_DIR` 末尾スラッシュ除去

## [0.1.0] - 2026-07-18

### Added
- 初期リリース
- `stats` / `watch` / `multiwatch` / `add` / `list` コマンド
- PlayHive 公式 API（`api.playhive.com`）対応、13 ゲームモード + エイリアス
- モック / 実 API 切替（`HIVETOOL_MOCK` 環境変数）
- 実フィールド名の確定（13 ゲーム全て）
