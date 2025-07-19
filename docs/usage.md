# 使い方ガイド

app-obsidian-abstractorの実践的な使い方を説明します。

## 📝 コマンドの使い分けについて

このドキュメントでは `python -m src.main` を使って説明しますが、インストール方法によって使用するコマンドが異なります：

- **Vaultにインストールした場合**: `./run.sh` を使用してください
  ```bash
  ./run.sh process file.pdf
  ```

- **スタンドアロンインストールの場合**: `python -m src.main` を使用してください
  ```bash
  python -m src.main process file.pdf
  ```

以降の例では `python -m src.main` で説明しますが、Vaultインストールの方は `./run.sh` に読み替えてください。

## ✨ ただ要約するだけではありません！

app-obsidian-abstractorは単なるPDF要約ツールではありません。以下のような高度な機能を備えています：

- **🤖 自動ワークフロー**: フォルダを監視して新しいPDFを自動処理
- **📊 処理統計**: 処理済みPDFの統計情報を表示・エクスポート
- **🔗 シームレスな連携**: app-obsidian_ai_organizerと組み合わせて、タグ付けやリンク生成も自動化
- **🎯 スマートフィルタリング**: 学術論文を自動判別して、関係ないPDFをスキップ
- **📁 柔軟なパス管理**: vault://記法や動的プレースホルダーで整理も自動化

詳しい使い方は以下をご覧ください。

## 🎯 基本的な使い方

### PDFファイルの処理

#### 単一ファイルの処理

```bash
# 基本的な使い方
python -m src.main process path/to/paper.pdf

# 出力先を指定
python -m src.main process paper.pdf --output ~/Obsidian/Papers

# ドライラン（実際には処理しない）
python -m src.main process paper.pdf --dry-run
```

#### フォルダの一括処理

```bash
# フォルダ内の全PDFを処理
python -m src.main batch ~/Downloads/Papers

# 特定の出力先に保存
python -m src.main batch ~/Downloads/Papers --output ~/Obsidian/inbox

# 並列処理（デフォルト: 3）
python -m src.main batch ~/Papers --workers 5
```

### フォルダ監視モード

#### 基本的な監視

```bash
# 単一フォルダを監視
python -m src.main watch ~/Downloads

# 複数フォルダを監視
python -m src.main watch ~/Downloads ~/Desktop/Research
```

#### 高度な監視設定

```bash
# 出力先を指定して監視
python -m src.main watch ~/Papers --output ~/Obsidian/inbox

# デーモンモードで実行
python -m src.main watch ~/Papers --daemon

# 設定ファイルの監視設定を使用
python -m src.main watch  # config.yamlの設定を使用
```

## 📱 Shell Commands設定

ObsidianのShell Commandsプラグインを使用すると、Obsidian内から直接PDFを処理できます。

⚠️ **セキュリティに関する注意**: Shell Commandsは強力な機能ですが、信頼できる環境でのみ使用してください。不正なファイル名による攻撃を防ぐため、コマンドでは必ず変数を二重引用符で囲んでください（例: `"{{file_path}}"`）。

### 設定手順

1. **Shell Commandsプラグインをインストール**
   - 設定 → コミュニティプラグイン → Shell Commands を検索
   - インストールして有効化

2. **新しいコマンドを追加**

#### PDFファイル処理コマンド

```bash
# コマンド名: Abstract PDF
# シェルコマンド:
cd "{{vault_path}}/.obsidian/tools/abstractor" && ./run.sh process "{{file_path}}" --output "{{folder}}"

# 使い方:
# 1. PDFファイルを右クリック
# 2. "Abstract PDF"を選択
# 3. 同じフォルダに要約ノートが生成される
```

#### フォルダ一括処理コマンド

```bash
# コマンド名: Abstract PDFs in Folder
# シェルコマンド:
cd "{{vault_path}}/.obsidian/tools/abstractor" && ./run.sh batch "{{folder}}"

# 使い方:
# 1. フォルダを右クリック
# 2. "Abstract PDFs in Folder"を選択
# 3. フォルダ内の全PDFが処理される
```

#### 設定ファイルを開く

```bash
# コマンド名: Open Abstractor Config
# シェルコマンド:
open "{{vault_path}}/.obsidian/tools/abstractor/config/config.yaml"

# Windows用:
start "" "{{vault_path}}/.obsidian/tools/abstractor/config/config.yaml"
```

### ホットキーの設定

1. 設定 → ホットキー
2. "Shell Commands: Abstract PDF"を検索
3. 好きなキーを割り当て（例: Cmd+Shift+A）

## 🔄 典型的なワークフロー

### 研究論文の整理フロー

1. **PDFダウンロード**
   - 論文を`~/Downloads/Papers`にダウンロード

2. **自動処理**
   - フォルダ監視が新しいPDFを検出
   - AIが要約を生成
   - Obsidianノートを作成

3. **自動整理**（app-obsidian_ai_organizerと連携）
   - 関連タグが自動付与
   - 既存ノートとリンク生成

### 手動処理フロー

1. **PDFをvaultにコピー**
   ```bash
   cp paper.pdf ~/Obsidian/Papers/
   ```

2. **Obsidianで処理**
   - PDFファイルを右クリック
   - "Abstract PDF"を実行

3. **ノートの確認と編集**
   - 生成されたノートを開く
   - 必要に応じて編集

## 🎨 高度な使い方

### カスタム出力パス

動的なプレースホルダーを使用した出力パス指定：

```bash
# 年月でフォルダを分ける
python -m src.main process paper.pdf --output "~/Obsidian/Papers/{{year}}/{{month}}"

# 著者名でフォルダを分ける
python -m src.main process paper.pdf --output "~/Obsidian/Papers/{{author}}"
```

利用可能なプレースホルダー：
- `{{year}}`: 現在の年（例: 2025）
- `{{month}}`: 現在の月（例: 01）
- `{{day}}`: 現在の日（例: 19）
- `{{author}}`: 第一著者の姓（PDFから抽出）

### Vault相対パス

```bash
# vault://記法を使用
python -m src.main process paper.pdf --output "vault://Papers/2025"

# 設定ファイルでも使用可能
watch:
  output_path: "vault://inbox/{{year}}/{{month}}"
```

### バッチ処理の最適化

```bash
# 大量のPDFを処理する場合
python -m src.main batch ~/LargePDFCollection \
  --workers 5 \
  --batch-size 10 \
  --progress
```

### フィルタリング設定

学術論文以外のPDFを除外：

```bash
# 強制的に全PDFを処理
python -m src.main process document.pdf --force

# フィルタリングをスキップ
python -m src.main batch ~/PDFs --no-filter
```

## 📊 処理結果の確認

### ログファイル

```bash
# ログファイルの場所
~/.obsidian/tools/abstractor/logs/abstractor_20250119.log

# リアルタイムでログを確認
tail -f ~/.obsidian/tools/abstractor/logs/abstractor_*.log
```

### 処理統計

```bash
# 処理済みファイルの確認
python -m src.main stats

# 出力例:
# 処理済みPDF: 156
# 成功: 152
# 失敗: 4
# 平均処理時間: 32.5秒
```

## 🔗 app-obsidian_ai_organizerとの連携

### 自動ワークフロー設定

1. **abstractor設定** (`config.yaml`)
   ```yaml
   output:
     add_organizer_placeholder: true  # 関連ノートセクションを追加
   ```

2. **連携スクリプト作成**
   ```bash
   #!/bin/bash
   # process-and-organize.sh
   
   # PDFを処理
   cd ~/.obsidian/tools/abstractor
   ./run.sh process "$1" --output "$2"
   
   # 5秒待機
   sleep 5
   
   # organizerを実行
   cd ~/.obsidian/tools/organizer
   ./run.sh process-file "$2/$(basename "$1" .pdf).md"
   ```

3. **Shell Commandsに登録**
   ```bash
   # コマンド名: Process and Organize PDF
   bash ~/.obsidian/tools/process-and-organize.sh "{{file_path}}" "{{folder}}"
   ```

## 💡 Tips & Tricks

### 処理速度の向上

1. **並列処理数の調整**
   ```yaml
   # config.yaml
   performance:
     max_workers: 5  # CPUコア数に応じて調整
   ```

2. **キャッシュの活用**
   ```yaml
   cache:
     enabled: true
     ttl_hours: 168  # 1週間
   ```

### メモリ使用量の削減

```yaml
# 大きなPDFを処理する場合
pdf:
  max_pages: 50  # 最初の50ページのみ処理
  chunk_size: 10  # 10ページずつ処理
```

### エラー処理

```bash
# エラーが発生したPDFをスキップして続行
python -m src.main batch ~/PDFs --skip-errors

# エラーログを別ファイルに保存
python -m src.main batch ~/PDFs --error-log errors.txt
```

## 🎯 ユースケース別設定

### 日次の論文チェック

```bash
# crontabに追加
0 9 * * * cd /path/to/abstractor && python -m src.main watch ~/Downloads --daemon --hours 8
```

### 研究プロジェクト別管理

```yaml
# プロジェクトA用の設定
projects:
  project_a:
    watch_folder: "~/Research/ProjectA/Papers"
    output: "vault://Projects/ProjectA/Literature"
    tags: ["project-a", "machine-learning"]
```

### 共同研究での使用

```bash
# 共有フォルダを監視
python -m src.main watch /Volumes/SharedDrive/Papers \
  --output ~/Obsidian/SharedResearch \
  --notify  # 処理完了時に通知
```

---

次のステップ: [設定ファイルの詳細](./configuration.md)へ進む