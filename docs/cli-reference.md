# CLIリファレンス

app-obsidian-abstractorのコマンドラインインターフェース（CLI）の完全なリファレンスです。

## 基本的な使い方

```bash
python -m src.main [COMMAND] [OPTIONS] [ARGUMENTS]
```

### グローバルオプション

| オプション | 説明 | デフォルト |
|-----------|------|------------|
| `--help`, `-h` | ヘルプを表示 | - |
| `--version`, `-v` | バージョンを表示 | - |
| `--config`, `-c` | 設定ファイルのパス | `config/config.yaml` |
| `--show-config` | 現在の設定を表示 | - |
| `--debug` | デバッグモードを有効化 | False |
| `--quiet`, `-q` | 最小限の出力のみ | False |
| `--verbose` | 詳細な出力 | False |

## コマンド一覧

### process - 単一PDFの処理

PDFファイルを処理して要約ノートを生成します。

```bash
python -m src.main process [OPTIONS] PDF_PATH
```

#### 引数

- `PDF_PATH`: 処理するPDFファイルのパス（必須）

#### オプション

| オプション | 短縮形 | 説明 | デフォルト |
|-----------|--------|------|------------|
| `--output` | `-o` | 出力先ディレクトリ | PDFと同じディレクトリ |
| `--template` | `-t` | 使用するテンプレート | `default` |
| `--language` | `-l` | 要約の言語（ja/en） | `ja` |
| `--force` | `-f` | 既存の処理結果を上書き | False |
| `--dry-run` | - | 実際には処理しない | False |
| `--visual` | - | 視覚的処理を有効化 | False |
| `--no-filter` | - | PDFフィルタリングをスキップ | False |

#### 使用例

```bash
# 基本的な使用
python -m src.main process paper.pdf

# 出力先を指定
python -m src.main process paper.pdf --output ~/Obsidian/Papers

# 英語で要約を生成
python -m src.main process paper.pdf --language en

# ドライランで確認
python -m src.main process paper.pdf --dry-run

# 視覚的処理を有効化
python -m src.main process paper.pdf --visual
```

### batch - フォルダの一括処理

フォルダ内の全PDFファイルを一括処理します。

```bash
python -m src.main batch [OPTIONS] FOLDER_PATH
```

#### 引数

- `FOLDER_PATH`: 処理するフォルダのパス（必須）

#### オプション

| オプション | 短縮形 | 説明 | デフォルト |
|-----------|--------|------|------------|
| `--output` | `-o` | 出力先ディレクトリ | 入力フォルダと同じ |
| `--recursive` | `-r` | サブフォルダも処理 | False |
| `--workers` | `-w` | 並列処理数 | 3 |
| `--batch-size` | `-b` | バッチサイズ | 5 |
| `--skip-errors` | - | エラーをスキップして続行 | False |
| `--progress` | `-p` | 進捗バーを表示 | True |
| `--filter` | - | ファイル名フィルター | `*.pdf` |

#### 使用例

```bash
# フォルダ内の全PDFを処理
python -m src.main batch ~/Downloads/Papers

# サブフォルダも含めて処理
python -m src.main batch ~/Papers --recursive

# 並列処理数を増やす
python -m src.main batch ~/Papers --workers 5

# エラーをスキップして続行
python -m src.main batch ~/Papers --skip-errors
```

### watch - フォルダ監視

指定されたフォルダを監視し、新しいPDFを自動的に処理します。

```bash
python -m src.main watch [OPTIONS] [FOLDERS...]
```

#### 引数

- `FOLDERS`: 監視するフォルダのパス（オプション、複数指定可）

#### オプション

| オプション | 短縮形 | 説明 | デフォルト |
|-----------|--------|------|------------|
| `--output` | `-o` | 出力先ディレクトリ | 設定ファイルの値 |
| `--daemon` | `-d` | バックグラウンドで実行 | False |
| `--interval` | `-i` | 監視間隔（秒） | 10 |
| `--recursive` | `-r` | サブフォルダも監視 | True |
| `--hours` | - | 実行時間（時間） | 無制限 |
| `--pattern` | - | 監視パターン | `*.pdf` |

#### 使用例

```bash
# 単一フォルダを監視
python -m src.main watch ~/Downloads

# 複数フォルダを監視
python -m src.main watch ~/Downloads ~/Desktop/Papers

# バックグラウンドで実行
python -m src.main watch ~/Papers --daemon

# 8時間だけ監視
python -m src.main watch ~/Papers --hours 8

# 設定ファイルの監視設定を使用
python -m src.main watch
```

### info - PDF情報の表示

PDFファイルの詳細情報を表示します（処理はしません）。

```bash
python -m src.main info [OPTIONS] PDF_PATH
```

#### 引数

- `PDF_PATH`: 情報を表示するPDFファイルのパス（必須）

#### オプション

| オプション | 短縮形 | 説明 | デフォルト |
|-----------|--------|------|------------|
| `--json` | `-j` | JSON形式で出力 | False |
| `--metadata` | `-m` | メタデータのみ表示 | False |
| `--structure` | `-s` | 構造情報を表示 | False |

#### 使用例

```bash
# 基本情報を表示
python -m src.main info paper.pdf

# JSON形式で出力
python -m src.main info paper.pdf --json

# メタデータのみ
python -m src.main info paper.pdf --metadata
```

### stats - 統計情報の表示

処理統計を表示します。

```bash
python -m src.main stats [OPTIONS]
```

#### オプション

| オプション | 短縮形 | 説明 | デフォルト |
|-----------|--------|------|------------|
| `--period` | `-p` | 期間（today/week/month/all） | `all` |
| `--format` | `-f` | 出力形式（text/json/csv） | `text` |
| `--output` | `-o` | 出力ファイル | 標準出力 |

#### 使用例

```bash
# 全期間の統計を表示
python -m src.main stats

# 今週の統計をJSON形式で
python -m src.main stats --period week --format json

# CSV形式でファイルに保存
python -m src.main stats --format csv --output stats.csv
```

### validate-config - 設定の検証

設定ファイルの妥当性を検証します。

```bash
python -m src.main validate-config [OPTIONS]
```

#### オプション

| オプション | 短縮形 | 説明 | デフォルト |
|-----------|--------|------|------------|
| `--config` | `-c` | 検証する設定ファイル | `config/config.yaml` |
| `--strict` | - | 厳密な検証 | False |

#### 使用例

```bash
# デフォルト設定を検証
python -m src.main validate-config

# 特定の設定ファイルを検証
python -m src.main validate-config --config my-config.yaml

# 厳密な検証
python -m src.main validate-config --strict
```

### clear-cache - キャッシュのクリア

処理キャッシュをクリアします。

```bash
python -m src.main clear-cache [OPTIONS]
```

#### オプション

| オプション | 短縮形 | 説明 | デフォルト |
|-----------|--------|------|------------|
| `--all` | `-a` | 全てのキャッシュを削除 | False |
| `--older-than` | - | 指定日数より古いキャッシュのみ | - |
| `--dry-run` | - | 実際には削除しない | False |

#### 使用例

```bash
# 全キャッシュをクリア
python -m src.main clear-cache --all

# 7日以上古いキャッシュをクリア
python -m src.main clear-cache --older-than 7

# ドライランで確認
python -m src.main clear-cache --all --dry-run
```

### diagnose - 診断情報の生成

トラブルシューティング用の診断情報を生成します。

```bash
python -m src.main diagnose [OPTIONS]
```

#### オプション

| オプション | 短縮形 | 説明 | デフォルト |
|-----------|--------|------|------------|
| `--output` | `-o` | 出力ファイル | `diagnosis.txt` |
| `--include-logs` | - | ログファイルを含める | True |
| `--anonymize` | - | 個人情報を匿名化 | True |

#### 使用例

```bash
# 診断情報を生成
python -m src.main diagnose

# ログを含めない
python -m src.main diagnose --no-include-logs

# 特定のファイルに出力
python -m src.main diagnose --output my-diagnosis.txt
```

## 環境変数

以下の環境変数を使用できます：

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `GOOGLE_AI_API_KEY` | Google AI APIキー | `AIza...` |
| `ABSTRACTOR_CONFIG` | デフォルト設定ファイルパス | `/path/to/config.yaml` |
| `ABSTRACTOR_LOG_LEVEL` | ログレベル | `DEBUG` |
| `ABSTRACTOR_CACHE_DIR` | キャッシュディレクトリ | `~/.cache/abstractor` |
| `HTTP_PROXY` | HTTPプロキシ | `http://proxy:8080` |
| `HTTPS_PROXY` | HTTPSプロキシ | `https://proxy:8443` |

## 終了コード

| コード | 意味 |
|--------|------|
| 0 | 正常終了 |
| 1 | 一般的なエラー |
| 2 | コマンドライン引数エラー |
| 3 | 設定ファイルエラー |
| 4 | PDFファイルが見つからない |
| 5 | PDF処理エラー |
| 6 | API接続エラー |
| 7 | 権限エラー |
| 8 | キャンセル（Ctrl+C） |

## コマンドの組み合わせ

### パイプラインでの使用

```bash
# 処理結果をjqで解析
python -m src.main info paper.pdf --json | jq '.metadata'

# 統計をCSVに出力してExcelで開く
python -m src.main stats --format csv | open -a "Microsoft Excel"
```

### スクリプトでの使用

```bash
#!/bin/bash
# process-all.sh

# エラーログを準備
ERROR_LOG="errors_$(date +%Y%m%d).log"

# フォルダを処理
python -m src.main batch ~/Papers \
  --skip-errors \
  --workers 5 \
  2> "$ERROR_LOG"

# エラーがあれば通知
if [ -s "$ERROR_LOG" ]; then
  echo "Errors occurred. Check $ERROR_LOG"
fi
```

## デバッグとトラブルシューティング

### 詳細ログの有効化

```bash
# デバッグモードで実行
python -m src.main --debug process paper.pdf

# 環境変数で設定
export ABSTRACTOR_LOG_LEVEL=DEBUG
python -m src.main process paper.pdf
```

### ドライラン

```bash
# 実際には処理せず、何が実行されるか確認
python -m src.main process paper.pdf --dry-run --verbose
```

### プロファイリング

```bash
# パフォーマンス分析
python -m cProfile -o profile.stats src.main process paper.pdf
python -m pstats profile.stats
```

---

より詳細な使用方法については[使い方ガイド](./usage.md)を参照してください。