# hivetool

PlayHive（旧 Hivemc）公式APIから戦績を取得し、ターミナル上に `rich` で美しく表示するCLIツール。

## コマンド

- `hivetool stats <player> [gamemode]` — 指定プレイヤーの戦績を表示（KDR・勝率などの計算値付き）。ゲームモード省略可（お気に入り or メニューで選択）
- `hivetool watch <player> [gamemode]` — 300秒（デフォルト）ごとに自動更新し、前回からの差分を表示（緑=増加、赤=減少）
- `hivetool multiwatch [gamemode]` — 2〜4枠を同時視聴（`--slots 2..4`）。各枠で「プレイヤー名 / `top`(世界1位) / 空Enter(スキップ)」をCUIで選択
- `hivetool add <player>` — プレイヤー名とお気に入りゲームモードを `~/.hivetool/config.json` に保存
- `hivetool list` — 保存済みプレイヤーとお気に入りモードを表示
- `hivetool update` — hivetool 自身を最新版に強制更新（GitHub から `git pull` → pipx で再インストール）。未コミット変更時はスキップ

## ゲームモード

`bed`(BedWars) / `sky`(SkyWars) / `bridge` / `hide`(BlockHide) / `dr`(DeathRun) /
`sg`(SurvivalGames) / `ctf`(Capture The Flag) / `grav`(Gravity) / `murder` /
`drop` / `ground`(Ground War) / `party`(Party Games) / `wars`(Wars)

エイリアス: `bedwars`→`bed`, `skywars`→`sky`, `blockhide`→`hide`, `deathrun`→`dr`,
`survivalgames`→`sg`, `gravity`→`grav` など。

## セットアップ

### ワンラインインストール（直URL）

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/ASDF3001/hivetool/master/install.sh)
```

### または clone + 実行

```bash
git clone https://github.com/ASDF3001/hivetool.git
cd hivetool
bash install.sh
```

### Windows の場合（PowerShell）

`install.ps1` を使います（管理者権限は不要）。

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

内部で python → pipx を導入し、`pipx install` で hivetool を入れます。
pipx の場所（ユーザー Path）への登録は確認付きで行われます。

> 注意: `install.ps1` は Linux/macOS 環境では未検証です。Windows で動作確認が必要な場合は issue で報告してください。

### すでに古い版が入っている場合（アップデート）

`hivetool update` コマンドは **v0.1.0 以降** で追加されました。それより古い版には存在しないため、以下のいずれかで最新を持ってきてください。

**A. ワンライナーで強制再インストール（推奨）**

`bash <(curl ...)` のプロセス置換では `install.sh` が自身の場所を正しく解決できないため、いったんファイルに落としてから実行します:

```bash
curl -fsSL https://raw.githubusercontent.com/ASDF3001/hivetool/master/install.sh -o /tmp/install.sh
bash /tmp/install.sh
```

**B. すでにクローン済みの場合**

```bash
cd ~/hivetool            # クローンしたディレクトリ
git pull origin master   # 最新を取得
bash install.sh           # または: pipx install . --force
```

更新後は `hivetool update` だけで今後は済むようになります。

上記で pipx 経由でインストールされ、シェルの設定ファイル（`.zshrc`/`.bashrc`）への PATH 登録も確認付きで行われます。
手動で行う場合:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 起動時の自動更新

`hivetool` を実行するたびに `git pull --ff-only` で更新を取得します。
リポジトリに**未コミットの変更**がある場合は自動更新をスキップするので、あなたの作業が上書きされることはありません。
また起動時に必須ライブラリ（`click` / `rich` / `requests`）の欠損チェックも行い、足りない場合はインストール案内を出して終了します。

## 実APIについて

- エンドポイント: `https://api.playhive.com`（旧 `api.hivemc.com` は廃止）
- 統計: `GET /v0/game/all/{game}/{UUID}`（プレイヤー名は `/v0/player/search/{partial}` でUUIDに解決）
- リーダーボード: `GET /v0/game/leaderboard/{game}`

### モック / 実API の切替

環境変数で切り替え（コード変更不要）:

```bash
HIVETOOL_MOCK=1  python -m hivetool.cli stats Notch bed   # モック（デフォルト・オフライン可）
HIVETOOL_MOCK=0  python -m hivetool.cli stats Notch bed   # 実API
```

**重要**: 環境変数を付けずに実行するとモック（ダミーデータ）になります。
実際の戦績を見るには **必ず `HIVETOOL_MOCK=0` を付けてください**。
`watch` / `stats` の表示タイトルには、モック動作時は `[MOCK]` バッジが出るので一目で見分けられます。

### レート制限に注意

PlayHive API は「ゲーム + プレイヤー」の組み合わせごとにレート制限があります。
短時間に同じ組み合わせへ連続アクセスすると `429 Too Many Attempts` になり、
しばらく利用できなくなります。通常の使い方（人が `stats` を叩く程度）では問題ありませんが、
スクリプト等で連続アクセスする際は間隔を空けてください。

## 実フィールド名（確認済み）

各ゲームの生フィールド名は `hivetool/api.py` の `GAME_FIELDS` に定義。
共通: `kills` / `deaths` / `victories` / `played` / `xp`。
モード別例: `beds_destroyed`(bed), `murders`(murder), `goals`(bridge),
`flags_captured`(ctf), `maps_completed`(grav) など。

## ライセンス

MIT

## チェンジログ

詳しくは [CHANGELOG_ja.md](CHANGELOG_ja.md) を参照。
