# Paperpile同期ガイド

このガイドでは、[Paperpile](https://paperpile.com/)のGoogle Drive上の論文をObsidian vaultに自動同期する方法を説明します。rcloneという強力なツールを使用することで、複数のGoogle Driveアカウントを扱いながら、効率的に論文を同期できます。

## 📋 このガイドが解決する問題

- Google Driveデスクトップアプリが別アカウントで使用中
- Paperpileの論文を手動でダウンロードする手間
- 新しい論文の見逃し
- Obsidianとの連携の自動化

## 🚀 はじめに - まずは手動実行から

自動化の前に、**必ず手動で一度実行**して動作を確認してください。これにより：
- 設定が正しいか確認できます
- どのファイルがコピーされるか把握できます
- エラーがあれば早期に発見できます

## 📦 rcloneのインストールと設定

### 1. rcloneのインストール

#### macOS
```bash
brew install rclone
```

#### Linux
```bash
sudo -v ; curl https://rclone.org/install.sh | sudo bash
```

#### Windows
[rclone downloads](https://rclone.org/downloads/)から実行ファイルをダウンロードし、PATHに追加してください。

### 2. Google Drive認証設定

```bash
rclone config
```

対話的な設定プロセスが始まります：

```
No remotes found, make a new one?
n) New remote
s) Set configuration password
q) Quit config
n/s/q> n                    # "n"を入力

name> paperpile             # リモート名を入力
Type of storage to configure.
Storage> drive              # "drive"と入力（Google Drive）

client_id>                  # 空欄でEnter
client_secret>              # 空欄でEnter  

scope> 1                    # "1"を選択（Full access all files）

root_folder_id>             # 空欄でEnter
service_account_file>       # 空欄でEnter

Edit advanced config? n     # "n"を入力

Use auto config? y          # "y"を入力（ブラウザが開きます）

# ブラウザが自動的に開きます
# Googleアカウントにログイン（Paperpileが使用しているアカウント）
# 「rcloneがGoogleドライブへのアクセスを求めています」を許可
# 「Success!」画面が表示されたらブラウザを閉じる

Configure this as a team drive? n  # "n"を入力

# 設定内容が表示される
y) Yes this is OK (default)
e) Edit this remote
d) Delete this remote
y/e/d> y                   # "y"を入力して確定

# 設定済みリモート一覧が表示される
Current remotes:
Name                 Type
====                 ====
paperpile           drive

e) Edit existing remote
...
q) Quit config
e/n/d/r/c/s/q> q          # "q"を入力して終了
```

### 3. 設定の確認

```bash
# 設定が正しいか確認
rclone lsd paperpile:

# Google Driveの内容が表示されます
# 例:
# Paperpile
# Colab Notebooks
# ...

# Paperpileフォルダの中身を確認
rclone lsd paperpile:Paperpile

# 以下のフォルダが表示されるはず：
# All Papers      # すべての論文（アルファベット順のサブフォルダ）
# Starred Papers  # スター付き論文

# All Papersの構造を確認
rclone lsd "paperpile:Paperpile/All Papers"

# アルファベット順のフォルダが表示されます：
# A
# B
# C
# ...
```

## 📝 同期機能の設定

### 1. Paperpile同期機能について

app-obsidian-abstractorには、PaperpileのPDFをObsidian vaultに同期する機能が統合されています。これにより：

- rcloneを使用した高速で効率的な同期
- 設定ファイルによる柔軟なカスタマイズ
- 他のコマンドとの統合（watchやbatchと組み合わせ可能）
- 自動化に対応（cron、launchd）

### 2. 設定ファイルの準備

`config.yaml`に以下の設定を追加します：

```yaml
# Paperpile Sync Configuration
paperpile_sync:
  # この機能を有効化
  enabled: true
  
  # rcloneで設定したリモート名（末尾のコロンを忘れずに）
  rclone_remote: "paperpile:"
  
  # 同期対象フォルダ
  source_dirs:
    # Paperpileの実際のフォルダ構造に合わせて設定
    # 方法1: All Papersフォルダ全体を同期
    - "All Papers"
    # 方法2: 特定のアルファベットフォルダのみ（テスト用）
    # - "All Papers/A"
    # - "All Papers/B"
    # 方法3: Starred Papers（お気に入り）のみ
    # - "Starred Papers"
  
  # 同期対象期間
  # 初回: "100d" (過去100日)
  # 通常: "7d" (過去7日)
  max_age: "7d"
  
  # Vault内の同期先（vault pathからの相対パス）
  inbox_dir: "Papers/Inbox"
  
  # ログファイルの場所
  log_file: "~/.paperpile-sync.log"
```

### 3. 使用方法の確認

設定が完了したら、以下のコマンドで動作を確認します：

```bash
# app-obsidian-abstractorのディレクトリに移動
cd /path/to/app-obsidian-abstractor

# ヘルプを表示
./run.sh paperpile-sync --help

# 設定を確認（同期機能が有効か確認）
./run.sh paperpile-sync --dry-run
```

## 🏃 手動実行

### 1. ドライラン（実際にはコピーしない）

```bash
# まずはどのファイルが同期されるか確認
./run.sh paperpile-sync --dry-run
```

### 2. 実際の同期

```bash
# 問題なければ実際に実行
./run.sh paperpile-sync
```

### 3. ログの確認

```bash
# 同期の結果を確認
tail -f ~/.paperpile-sync.log

# または、詳細な出力を表示
./run.sh paperpile-sync --verbose
```

## 🔗 app-obsidian-abstractorとの連携

### 設定ファイルの更新

`config/config.yaml`に以下を追加：

```yaml
watch:
  folders:
    - "vault://Papers/Inbox/Papers"      # 整理済み論文
    - "vault://Papers/Inbox/Unsorted"    # 未整理論文
  output_path: "vault://Papers/Processed/{{year}}/{{month}}"

pdf_filter:
  enabled: false  # Paperpileからは学術論文のみなので無効化
  # 理由: Paperpileは学術文献管理ツールなので、
  # 請求書やマニュアルなどの非学術PDFは含まれない前提
```

### 推奨フォルダ構造

```
Obsidian Vault/
├── Papers/
│   ├── Inbox/              # rcloneが同期する場所
│   │   ├── Papers/         # Paperpileの整理済み論文
│   │   └── Unsorted/       # Paperpileの未整理論文
│   └── Processed/          # app-obsidian-abstractorが処理後に保存
│       └── 2025/
│           └── 01/
```

## 🤖 自動化（手動実行で問題ないことを確認してから）

### macOS/Linux (cron)

```bash
# crontabを編集
crontab -e

# 以下を追加（15分ごとに実行、フルパスで指定）
*/15 * * * * cd /path/to/app-obsidian-abstractor && ./run.sh paperpile-sync >> ~/.paperpile-cron.log 2>&1

# または営業時間内のみ（平日9-18時、30分ごと）
*/30 9-18 * * 1-5 cd /path/to/app-obsidian-abstractor && ./run.sh paperpile-sync >> ~/.paperpile-cron.log 2>&1
```

**重要**: 
- crontabでは`~`や環境変数が使えない場合があるため、フルパスを使用してください
- `cd`コマンドで適切なディレクトリに移動してから実行する必要があります

### macOS (launchd) - より信頼性が高い

1. 以下の内容で`~/Library/LaunchAgents/com.user.paperpile-sync.plist`を作成：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.paperpile-sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd /path/to/app-obsidian-abstractor && ./run.sh paperpile-sync</string>
    </array>
    <key>StartInterval</key>
    <integer>900</integer>  <!-- 15分 = 900秒 -->
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/username/.paperpile-sync-launchd.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/username/.paperpile-sync-launchd-error.log</string>
</dict>
</plist>
```

2. launchdに登録：

```bash
launchctl load ~/Library/LaunchAgents/com.user.paperpile-sync.plist
```

### Windows (タスクスケジューラ)

1. タスクスケジューラを開く（`taskschd.msc`）
2. 「基本タスクの作成」をクリック
3. 名前: "Paperpile Sync"
4. トリガー: 毎日、15分ごとに繰り返し
5. 操作: プログラムの開始
   - プログラム: `C:\Program Files\rclone\rclone.exe`
   - 引数: `copy paperpile:Paperpile "C:\Users\username\Obsidian\MyVault\Papers\Inbox" --include *.pdf --max-age 7d --ignore-existing`
   - 開始（オプション）: `C:\Program Files\rclone`

参考: [Windows Task Scheduler Documentation](https://docs.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-start-page)

## 🐛 トラブルシューティング

### 「コマンドが見つかりません」エラー

cron/launchdから実行時によく発生します。スクリプトの冒頭に以下を追加：

```bash
# PATHを明示的に設定
export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

# またはrcloneのフルパスを使用
RCLONE="/usr/local/bin/rclone"
$RCLONE copy ...
```

### 認証エラー

```bash
# トークンをリフレッシュ
rclone config reconnect paperpile:

# 設定を確認
rclone config show paperpile
```

### 同期が遅い

```bash
# 帯域幅を制限（オフィスなどで）
rclone copy ... --bwlimit 10M

# 同期対象を絞る
MAX_AGE="3d"  # 3日以内のファイルのみ
```

### ログファイルが大きくなりすぎる

```bash
# logrotateを設定（Linux/macOS）
echo "$HOME/.paperpile-sync.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}" | sudo tee /etc/logrotate.d/paperpile-sync
```

## 💡 Tips

### 初回同期の推奨手順

1. まず`MAX_AGE="100d"`で過去の論文を同期
2. 正常に動作することを確認
3. `MAX_AGE="7d"`に変更して定期実行

### メタデータの活用

同期される`.bib`ファイルには論文のメタデータが含まれています。将来的には、app-obsidian-abstractorがこの情報を読み取って：
- citekeyの自動設定
- タグの自動生成
- 引用情報の自動入力

などが可能になるかもしれません。

### パフォーマンスの最適化

```bash
# 大量のファイルがある場合
--transfers 8      # 同時転送数を増やす
--checkers 16      # チェッカー数を増やす

# ネットワークが遅い場合  
--transfers 2      # 同時転送数を減らす
--bwlimit 1M       # 帯域幅を制限
```

## ❓ よくある質問（FAQ）

### Q: 初回同期で大量のファイルがある場合は？

A: 初回は`max_age`を長めに設定することをお勧めします：

```yaml
# config.yaml
paperpile_sync:
  max_age: "100d"  # 過去100日分を同期
```

同期が完了したら、通常の設定（例：`"7d"`）に戻してください。

### Q: 複数のVaultで使いたい場合は？

A: 各Vaultごとに別々の設定ファイルを使用します：

```bash
# Research用の設定
./run.sh paperpile-sync --config config-research.yaml

# Personal用の設定
./run.sh paperpile-sync --config config-personal.yaml
```

または、各Vaultにapp-obsidian-abstractorをインストールして、それぞれで設定することも可能です。

### Q: 同期されたファイルをapp-obsidian-abstractorで自動処理するには？

A: 2つの方法があります：

1. **watchコマンドを使用**（推奨）:
   ```bash
   # 同期先フォルダを監視
   ./run.sh watch "vault://Papers/Inbox"
   ```

2. **同期後に手動でバッチ処理**:
   ```bash
   # 同期を実行
   ./run.sh paperpile-sync
   
   # 同期されたPDFを処理
   ./run.sh batch "vault://Papers/Inbox/Papers" --output "vault://Papers/Processed"
   ```

### Q: 特定のPaperpileコレクションだけを同期したい

A: 現在のバージョンではフォルダ単位の同期のみサポートしています。Paperpileでコレクションごとにフォルダを分けて管理することをお勧めします。

将来的には、Paperpileのメタデータを読み取ってコレクションベースの同期を実装する可能性があります。

## 🔄 将来の拡張可能性

このシンプルな同期スクリプトをベースに、以下の拡張も可能です：

- **Paperpileコレクション対応**: 特定のコレクションのみを同期
- **双方向同期**: ObsidianでのノートからPaperpileへのフィードバック
- **重複論文の検出**: ファイル名だけでなく内容ベースの重複チェック
- **自動タグ付け**: ファイル名やフォルダ構造からタグを自動生成

まずはこのシンプルなスクリプトから始めて、必要に応じて機能を追加していくことをお勧めします。

---

問題が発生した場合は、[GitHubのIssues](https://github.com/hrkzogw/app-obsidian-abstractor/issues)でお問い合わせください。