# 設定ファイルガイド

app-obsidian-abstractorの設定ファイル（`config.yaml`）の詳細な説明です。

## 📋 設定ファイルの基本

### 設定ファイルの場所

- **Vault内インストール**: `.obsidian/tools/abstractor/config/config.yaml`
- **スタンドアロン**: `app-obsidian-abstractor/config/config.yaml`

### 初期設定

```bash
# サンプルファイルをコピー
cp config/config.yaml.example config/config.yaml

# エディタで編集
nano config/config.yaml  # またはお好みのエディタ
```

## 📁 フォルダ設定（必須）

### folder_settings セクション

すべてのフォルダ関連設定を一箇所に集約しました。これにより設定の重複を避け、管理が簡単になります。

```yaml
folder_settings:
  # Obsidian Vaultのフルパス（必須）
  # 例: "~/Documents/Obsidian/MyVault"
  # 例: "/Users/username/Obsidian/Research"
  vault_path: "~/Documents/Obsidian/MyVault"
  
  # デフォルトの出力先 (process, batchコマンド用)
  # vault:// を使うとVault相対パスになります
  # 例: "vault://Abstracts"          → Vault/Abstracts/
  # 例: "vault://Papers/2025"        → Vault/Papers/2025/
  # 例: "~/Documents/Abstracts"      → ホーム/Documents/Abstracts/
  default_output: "vault://Abstracts"
  
  # watchコマンドで監視するフォルダ
  # ブラウザのダウンロードフォルダなどを指定すると便利です
  watch_folders:
    - "~/Downloads"              # ブラウザのダウンロード先
    - "~/Desktop/Papers"         # デスクトップの論文フォルダ
    - "vault://PDFs/Inbox"       # Vault内のInboxフォルダ
  
  # watchコマンドの出力先 (オプション、未指定時はdefault_outputを使用)
  # {{year}}, {{month}}, {{day}} のプレースホルダが使用可能
  # 例: "vault://Papers/{{year}}/{{month}}" → Papers/2025/01/
  watch_output: "vault://Papers/{{year}}"
```

### パス指定の形式

- **vault://**: Vault相対パス（推奨）
- **~/**: ホームディレクトリ相対パス
- **絶対パス**: フルパスでの指定

## 🔑 API設定

### 必須設定

```yaml
# Google AI APIキー（必須）
# 取得方法: https://makersuite.google.com/app/apikey
google_ai_key: "your-gemini-api-key-here"
```

## 🤖 AI設定

### ai セクション

```yaml
ai:
  # 使用するモデル
  # 利用可能: "gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"
  model: "gemini-2.0-flash-exp"
  # 生成時の温度パラメータ（0.0-1.0、低いほど一貫性が高い）
  temperature: 0.3
  # 最大出力トークン数
  max_tokens: 8192
```

## 📤 出力設定

### output セクション

```yaml
output:
  # ファイル名パターン
  # 使用可能な変数: {{year}}, {{authors}}, {{title}}
  # 例: "{{year}}_{{authors}}_{{title}}" → "2025_Smith_et_al_Neural_Networks.md"
  filename_pattern: "{{year}}_{{authors}}_{{title}}"
  # 年ごとのサブディレクトリを作成するか
  organize_by_year: false
```

### ファイル名パターンの例

```yaml
# 例1: 日付ベース
file_pattern: "{year}{month}{day}_{title_short}"
# 結果: 20250119_Deep_Learning_for_NLP

# 例2: 著者中心
file_pattern: "{first_author}_{year}_{title_short}"
# 結果: Smith_2025_Deep_Learning_for_NLP

# 例3: タイムスタンプ付き
file_pattern: "{timestamp}_{first_author}"
# 結果: 1737280800_Smith
```

## 👁️ ファイル監視設定

### watch セクション

監視するフォルダは`folder_settings.watch_folders`で設定します。ここでは監視の動作を設定します。

```yaml
watch:
  # 監視するファイルパターン
  patterns:
    - "*.pdf"
    - "*.PDF"
  # 無視するパターン
  ignore_patterns:
    - "*draft*"        # ドラフトファイル
    - "*tmp*"          # 一時ファイル
    - ".*"             # 隠しファイル
  # 処理遅延（秒）- ファイル書き込み完了を待つ
  process_delay: 5
```

## 🤖 要約生成設定

### abstractor セクション

```yaml
abstractor:
  # 出力言語
  # - "ja": 日本語
  # - "en": 英語
  # - "auto": PDFの言語を自動検出
  language: "ja"
  
  # 要約の最大文字数
  max_length: 1000
  
  # 引用を含める
  include_citations: true
  
  # 図表の説明を含める
  include_figures: true
  
  # キーワードを抽出
  extract_keywords: true
  
  # セクション別の要約
  section_summaries: true
  
  # 批判的分析を含める
  critical_analysis: false
```

## 📄 PDF処理設定

### pdf セクション

```yaml
pdf:
  # 最大ファイルサイズ（MB）
  max_size_mb: 100
  
  # テキスト抽出モード
  # - "auto": 自動選択（推奨）
  # - "layout": レイアウトを保持
  # - "simple": シンプルな抽出
  # - "raw": 生のテキスト
  extraction_mode: "auto"
  
  # 暗号化PDFの処理
  handle_encrypted: false
  
  # 視覚的抽出（マルチモーダルAI）
  enable_visual_extraction: true
  
  # 画像抽出の最大ページ数
  max_image_pages: 5
  
  # 画像抽出のDPI
  image_dpi: 200
  
  # OCR設定（将来的な機能）
  # ocr:
  #   enabled: false
  #   language: "jpn+eng"
```

## 🔍 PDFフィルタリング

### pdf_filter セクション

```yaml
pdf_filter:
  # フィルタリングを有効化
  enabled: true
  
  # 学術論文のみ処理
  academic_only: true
  
  # 学術論文と判定する最小スコア
  academic_threshold: 50
  
  # ページ数の要件
  min_pages: 5
  max_pages: 500
  
  # ファイルサイズの要件（MB）
  min_size_mb: 0.1
  max_size_mb: 100
  
  # 隔離フォルダ（学術論文でないPDF用）
  quarantine_folder: "~/Documents/PDFs/Non-Academic"
  
  # 隔離を有効化
  quarantine_enabled: true
```

### scoring_rules セクション

```yaml
scoring_rules:
  # ポジティブスコア（学術論文の特徴）
  positive:
    doi_found: 50                # DOIが見つかった
    abstract_found: 20           # Abstractセクションあり
    references_found: 20         # Referencesセクションあり
    academic_publisher: 20       # 学術出版社
    pages_in_range: 15          # 適切なページ数（8-40）
    academic_keywords: 10        # 学術的キーワード
    
  # ネガティブスコア（非学術文書の特徴）
  negative:
    invoice_in_filename: -100    # 請求書
    receipt_in_filename: -100    # 領収書
    presentation_in_filename: -50 # プレゼンテーション
    manual_in_filename: -70      # マニュアル
    catalog_in_filename: -80     # カタログ
    report_in_content: -30       # レポート（内容ベース）
```

## ⚙️ 詳細設定

### advanced セクション

```yaml
advanced:
  # PDFキャッシュ
  pdf_cache: true
  cache_dir: "~/.cache/obsidian-abstractor"
  cache_ttl_days: 7
  
  # ログ設定
  log_level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  log_file: "~/.obsidian-abstractor/logs/app.log"
  log_rotation: "daily"
  log_retention_days: 30
  
  # 並列処理
  workers: 3
  max_concurrent_api_calls: 2
  
  # リトライ設定
  retry_failed: true
  retry_attempts: 3
  retry_delay: 5  # 秒
  
  # タイムアウト設定
  pdf_timeout: 300  # 秒
  api_timeout: 120  # 秒
```

## 🚦 レート制限

### rate_limit セクション

```yaml
rate_limit:
  # APIリクエスト制限
  requests_per_minute: 60
  
  # リクエスト間の遅延（秒）
  request_delay: 1
  
  # バッチ処理サイズ
  batch_size: 5
  
  # 日次制限（Geminiの無料枠用）
  daily_limit: 1500
  
  # 制限到達時の動作
  # - "wait": 次の期間まで待機
  # - "stop": 処理を停止
  on_limit_reached: "wait"
```

## 🎯 用途別設定例

### 最小限の設定

```yaml
# 必要最小限の設定
google_ai_key: "your-key"

folder_settings:
  vault_path: "~/Obsidian/MyVault"
  default_output: "vault://Abstracts"
```

### 研究者向け設定

```yaml
google_ai_key: "your-key"

folder_settings:
  vault_path: "~/Research/ObsidianVault"
  default_output: "vault://Literature/Inbox"
  watch_folders:
    - "~/Downloads"
    - "~/Mendeley/Papers"
  watch_output: "vault://Literature/{{year}}/{{month}}"

ai:
  model: "gemini-2.0-flash-exp"

abstractor:
  language: "en"
  max_length: 1500
  critical_analysis: true

pdf_filter:
  enabled: true
  academic_only: true
  academic_threshold: 60
```

### 高パフォーマンス設定

```yaml
advanced:
  workers: 5
  max_concurrent_api_calls: 3
  pdf_cache: true

rate_limit:
  batch_size: 10
  requests_per_minute: 120

pdf:
  max_image_pages: 0  # 画像抽出を無効化
  extraction_mode: "simple"  # 高速抽出
```

## 🔧 設定の検証

設定が正しいか確認：

```bash
# 設定の表示
python -m src.main --show-config

# 設定の検証
python -m src.main validate-config
```

## 💡 設定のヒント

1. **APIキーの安全管理**
   - 設定ファイルをGitにコミットしない
   - 環境変数の使用を検討

2. **パフォーマンス調整**
   - `workers`はCPUコア数-1程度が適切
   - 大量処理時は`rate_limit`に注意

3. **ストレージ管理**
   - キャッシュは定期的にクリア
   - ログファイルのローテーション設定

4. **エラー対策**
   - `retry_attempts`を増やすと安定性向上
   - `log_level: "DEBUG"`で詳細なデバッグ情報

---

次のステップ: [トラブルシューティング](./troubleshooting.md)へ進む