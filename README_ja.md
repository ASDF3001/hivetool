# hivetool

PlayHive（旧 Hivemc）公式APIから戦績を取得し、ターミナル上に `rich` で美しく表示するCLIツール。

## コマンド

- `hivetool stats <player> [gamemode]` — 指定プレイヤーの戦績を表示（KDR・勝率などの計算値付き）。ゲームモード省略可（お気に入り or メニューで選択）
- `hivetool watch <player> [gamemode]` — 300秒（デフォルト）ごとに自動更新し、前回からの差分を表示（緑=増加、赤=減少）
- `hivetool multiwatch [gamemode]` — 2〜4枠を同時視聴（`--slots 2..4`）。各枠で「プレイヤー名 / `top`(世界1位) / 空Enter(スキップ)」をCUIで選択
- `hivetool add <player>` — プレイヤー名とお気に入りゲームモードを `~/.hivetool/config.json` に保存
- `hivetool list` — 保存済みプレイヤーとお気に入りモードを表示
- `hivetool history <player> [gamemode]` — `watch`/`multiwatch` のポール履歴を表示（いつ・何が増減したか、`--limit` で件数指定）
- `hivetool update` — hivetool 自身を最新版に強制更新（GitHub から `git pull` → pipx で再インストール）。未コミット変更時はスキップ

## ゲームモード

`bed`(BedWars) / `sky`(SkyWars) / `bridge` / `hide`(BlockHide) / `dr`(DeathRun) /
`sg`(SurvivalGames) / `ctf`(Capture The Flag) / `grav`(Gravity) / `murder` /
`drop` / `ground`(Ground War) / `party`(Party Games) / `wars`(Wars)

エイリアス: `bedwars`→`bed`, `skywars`→`sky`, `blockhide`→`hide`, `deathrun`→`dr`,
`survivalgames`→`sg`, `gravity`→`grav` など。

## セットアップ

### 一番簡単なインストール（おすすめ）

ターミナルを開いて、これを1行コピペして Enter を押すだけ：

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/ASDF3001/hivetool/master/install.sh)
```

これで自動的に python → pipx を導入し、`hivetool` コマンドが使えるようになります。
（※ インストール中に `PATH を追記しますか？ [Y/n]` と聞かれたら `Y` を押してね）

終わったら、新しいターミナルを開いて動作確認：

```bash
hivetool stats Notch bed
```

本当の戦績が表示されればインストール成功！（アクセスできない時は下の「実APIモードってなに？」を参照）

---

### Windows の場合（PowerShell）

管理者権限は不要です。PowerShell を開いて以下を実行：

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

> 注意: `install.ps1` は Linux/macOS では未検証です。Windows で動かなくても issue で教えてもらえれば対応します。

---

### もっと手動でやりたい人（clone + 実行）

```bash
git clone https://github.com/ASDF3001/hivetool.git
cd hivetool
bash install.sh
```

---

### すでに入ってるけど古い版です（アップデート）

`hivetool update` コマンド（v0.1.0 以降）があればそれでOK：

```bash
hivetool update
```

それより古い版には `update` が無いので、以下で強制再インストール：

```bash
curl -fsSL https://raw.githubusercontent.com/ASDF3001/hivetool/master/install.sh -o /tmp/install.sh
bash /tmp/install.sh
```

（ワンライナー `bash <(curl ...)` だとインストーラーが自身の場所を解決できないため、いったんファイルに落としてから実行してます）

---

### 開発者向け（仮想環境で直接動かす）

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 起動時の自動更新

`hivetool` を実行するたびに `git pull --ff-only` で更新を取得します。
リポジトリに**未コミットの変更**がある場合は自動更新をスキップするので、あなたの作業が上書きされることはありません。
また起動時に必須ライブラリ（`click` / `rich` / `requests`）の欠損チェックも行い、足りない場合はインストール案内を出して終了します。

---

## 実APIモードってなに？（モックとの違い）

hivetool には **2つの動作モード** があります。

| モード | 内容 | いつ使う？ |
| --- | --- | --- |
| **実API**（デフォルト） | PlayHive の公式APIから**本当の戦績**を取得 | 普段使うのはこれ（友達の実際の勝敗を見たい時） |
| **モック** (`HIVETOOL_MOCK=1`) | プログラム内で適当に生成したダミーデータ | オフライン検証・開発中のみ |

**デフォルトは実API（本物）です。** 環境変数を何も付けずに `hivetool stats Notch bed` と打つと、そのまま本当の戦績が取れます。

### オフライン等でダミーデータが必要な時だけ

**`HIVETOOL_MOCK=1` を付けてください：**

```bash
HIVETOOL_MOCK=1 hivetool stats Notch bed
HIVETOOL_MOCK=1 hivetool watch Notch bridge
```

### 見分け方（バッジ）

表示タイトルにバッジが出るので一目でわかります：

- `[MOCK]` → ダミーデータ（実APIじゃない）
- `[CACHE]` → 実APIの取得結果をキャッシュから表示（下記参照）

### 実APIの裏側

- エンドポイント: `https://api.playhive.com`（旧 `api.hivemc.com` は廃止）
- 統計: `GET /v0/game/all/{game}/{UUID}`（プレイヤー名は `/v0/player/search/{partial}` でUUIDに自動変換）
- リーダーボード: `GET /v0/game/leaderboard/{game}`

### レート制限に注意

PlayHive API は「ゲーム + プレイヤー」の組み合わせごとにレート制限があります。
短時間に同じ組み合わせへ連続アクセスすると `429 Too Many Attempts` になり、しばらく利用できなくなります。
通常の使い方（人が `stats` を叩く程度）では問題ありませんが、スクリプト等で連続アクセスする際は間隔を空けてください。

### ローカルキャッシュでレート制限を緩和

実APIモード（`HIVETOOL_MOCK=0`）では、取得した戦績を `~/.hivetool/cache/<game>/<uuid>.json` に **300秒間** キャッシュします。
同じ組み合わせを 300秒以内に再取得する場合は API を叩かずキャッシュから返すため、`watch` の連続ポールでも 429 になりにくくなります。
キャッシュから表示された場合はタイトルに `[CACHE]` バッジが出ます（キャッシュは TTL 経過後に自動で更新されます）。

## 実フィールド名（確認済み）

各ゲームの生フィールド名は `hivetool/api.py` の `GAME_FIELDS` に定義。
共通: `kills` / `deaths` / `victories` / `played` / `xp`。
モード別例: `beds_destroyed`(bed), `murders`(murder), `goals`(bridge),
`flags_captured`(ctf), `maps_completed`(grav) など。

## ライセンス

MIT

## チェンジログ

詳しくは [CHANGELOG_ja.md](CHANGELOG_ja.md) を参照。
