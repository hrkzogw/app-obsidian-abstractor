# トラブルシューティング

app-obsidian-abstractorで発生する可能性のある問題と解決方法をまとめています。

## 🔍 問題の診断

### ログファイルの確認

```bash
# ログファイルの場所
~/.obsidian/tools/abstractor/logs/abstractor_YYYYMMDD.log

# 最新のエラーを確認
tail -n 50 ~/.obsidian/tools/abstractor/logs/abstractor_*.log | grep ERROR

# リアルタイムでログを監視
tail -f ~/.obsidian/tools/abstractor/logs/abstractor_*.log
```

### デバッグモードの有効化

```yaml
# config.yaml
advanced:
  log_level: "DEBUG"
```

## 🚫 よくあるエラーと解決方法

### インストール関連

#### Python仮想環境の作成に失敗

**エラー**:
```
Error: Unable to create virtual environment
```

**解決方法**:
```bash
# Pythonバージョンを確認
python --version

# venvモジュールをインストール（Ubuntu/Debian）
sudo apt-get install python3-venv

# 特定のPythonバージョンを使用
python3.11 -m venv venv

# Windows（Python Launcherを使用）
py -3.11 -m venv venv
```

#### 依存関係のインストールエラー

**エラー**:
```
ERROR: Could not find a version that satisfies the requirement
```

**解決方法**:
```bash
# pipをアップグレード
pip install --upgrade pip

# キャッシュをクリア
pip cache purge

# 個別にインストール
pip install google-genai>=0.7.0
pip install pymupdf>=1.24.0
pip install pyyaml>=6.0
```

### API関連

#### APIキーエラー

**エラー**:
```
Error: Invalid API key provided
```

**解決方法**:
1. APIキーが正しくコピーされているか確認
2. 余分な空白や改行が含まれていないか確認
3. 環境変数を使用する場合:
   ```bash
   export GOOGLE_AI_API_KEY="your-key"
   echo $GOOGLE_AI_API_KEY  # 確認
   ```

#### APIレート制限

**エラー**:
```
Error: Rate limit exceeded
```

**解決方法**:
```yaml
# config.yaml
rate_limit:
  requests_per_minute: 30  # 制限を下げる
  request_delay: 2         # 遅延を増やす
  batch_size: 3           # バッチサイズを減らす
```

### PDF処理関連

#### PDF解析エラー

**エラー**:
```
Error: Failed to extract text from PDF
```

**解決方法**:
1. PDFが破損していないか確認
   ```bash
   # PDFの情報を表示
   python -m src.main info file.pdf
   ```

2. 別の抽出モードを試す
   ```yaml
   pdf:
     extraction_mode: "layout"  # または "simple"
   ```

3. 視覚的処理を有効化
   ```yaml
   pdf:
     enable_visual_extraction: true
   ```

#### メモリ不足

**エラー**:
```
MemoryError: Unable to allocate memory
```

**解決方法**:
```yaml
# config.yaml
pdf:
  max_size_mb: 50        # ファイルサイズ制限
  max_pages: 100         # ページ数制限
  chunk_size: 10         # チャンクサイズ

advanced:
  workers: 1             # ワーカー数を減らす
```

#### 文字化け

**症状**: 日本語が正しく表示されない

**解決方法**:
1. PDFのエンコーディングを確認
2. フォント埋め込みを確認
3. 視覚的処理を使用:
   ```bash
   python -m src.main process file.pdf --visual
   ```

### フォルダ監視関連

#### 監視が開始されない

**エラー**:
```
Error: Failed to start watching folders
```

**解決方法**:
1. フォルダパスが存在するか確認
   ```bash
   ls -la ~/Downloads/Papers
   ```

2. 権限を確認
   ```bash
   # 読み取り権限があるか確認
   test -r ~/Downloads/Papers && echo "OK" || echo "NG"
   ```

3. 設定を確認
   ```bash
   python -m src.main --show-config | grep watch -A 10
   ```

#### ファイルが検出されない

**症状**: PDFを追加しても処理されない

**解決方法**:
1. ファイルパターンを確認
   ```yaml
   watch:
     patterns:
       - "*.pdf"
       - "*.PDF"
   ```

2. 無視パターンを確認
   ```yaml
   watch:
     ignore_patterns: []  # 一時的に空にする
   ```

3. ログでイベントを確認
   ```bash
   grep "New file detected" ~/.obsidian/tools/abstractor/logs/*.log
   ```

### Shell Commands関連

#### コマンドが実行されない

**症状**: Obsidianから実行してもエラー

**解決方法**:
1. 実行権限を付与
   ```bash
   chmod +x ~/.obsidian/tools/abstractor/run.sh
   ```

2. パスの空白をエスケープ
   ```bash
   # Shell Commandsで設定
   cd "{{vault_path}}/.obsidian/tools/abstractor" && ./run.sh process "{{file_path}}"
   ```

3. 直接Pythonを実行
   ```bash
   # run.shの代わりに
   cd "{{vault_path}}/.obsidian/tools/abstractor" && ./venv/bin/python -m src.main process "{{file_path}}"
   ```

### ノート生成関連

#### YAMLフロントマターエラー

**エラー**:
```
Error: Invalid YAML frontmatter
```

**解決方法**:
1. 特殊文字をエスケープ
2. タイトルに引用符を使用
   ```yaml
   title: "Deep Learning: A Comprehensive Review"
   ```

#### ファイル名の重複

**症状**: 同じ名前のファイルが上書きされる

**解決方法**:
```yaml
# config.yaml
output:
  file_pattern: "{timestamp}_{first_author}_{title_short}"
  # または
  duplicate_handling: "increment"  # file_1.md, file_2.md...
```

## 🛠️ 高度なトラブルシューティング

### プロセスのデバッグ

```bash
# ドライランモードで確認
python -m src.main process file.pdf --dry-run --debug

# ステップごとに実行
python -m src.main extract file.pdf  # テキスト抽出のみ
python -m src.main analyze file.pdf  # 分析のみ
```

### パフォーマンス問題

```bash
# プロファイリング
python -m cProfile -o profile.stats src.main process file.pdf

# 結果を分析
python -m pstats profile.stats
```

### ネットワーク問題

```bash
# プロキシ設定
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080

# 接続テスト
curl -I https://generativelanguage.googleapis.com
```

## 🔧 リセットと再インストール

### 設定のリセット

```bash
# 設定をバックアップ
cp config/config.yaml config/config.yaml.bak

# デフォルトに戻す
cp config/config.yaml.example config/config.yaml
```

### キャッシュのクリア

```bash
# キャッシュディレクトリを削除
rm -rf ~/.cache/obsidian-abstractor/*

# ログをクリア（古いログのみ）
find ~/.obsidian/tools/abstractor/logs -name "*.log" -mtime +7 -delete
```

### 完全な再インストール

```bash
# アンインストール
python tools/install_to_vault.py --uninstall

# 最新版を取得
git pull

# 再インストール
python tools/install_to_vault.py
```

## 📊 診断ツール

### システム情報の収集

```bash
# 診断情報を出力
python -m src.main diagnose > diagnosis.txt
```

診断情報に含まれる内容：
- Pythonバージョン
- インストール済みパッケージ
- 設定ファイルの内容（APIキーは除く）
- 最近のエラーログ
- システム情報

### ヘルスチェック

```bash
# システムの健全性を確認
python -m src.main health-check

# 出力例：
# ✓ Python version: 3.11.0
# ✓ API key configured
# ✓ Vault path exists
# ✓ Write permissions OK
# ✗ Cache directory full (90%)
```

## 💬 サポートを受ける

### Issueを作成する前に

1. **ログを確認**: エラーメッセージを特定
2. **設定を確認**: config.yamlの設定を再確認
3. **最新版を確認**: `git pull`で最新版に更新
4. **既存のIssueを検索**: 同じ問題が報告されていないか確認

### Issue作成時に含める情報

```markdown
## 環境
- OS: macOS 14.0
- Python: 3.11.0
- app-obsidian-abstractor: v1.0.0
- Obsidian: v1.5.0

## 問題の説明
[具体的な症状を記述]

## 再現手順
1. [手順1]
2. [手順2]

## エラーメッセージ
```
[エラーメッセージをペースト]
```

## 試したこと
- [解決策1]
- [解決策2]
```

## 🔄 よくある質問（FAQ）

**Q: PDFが処理されるまでどのくらい時間がかかりますか？**
A: 通常、10ページのPDFで30-60秒程度です。初回は少し長くかかる場合があります。

**Q: 同時に複数のPDFを処理できますか？**
A: はい、`workers`設定で並列処理数を調整できます。

**Q: 処理済みのPDFを再処理するには？**
A: `--force`オプションを使用するか、キャッシュをクリアしてください。

**Q: エラーが発生したPDFをスキップするには？**
A: `--skip-errors`オプションを使用してください。

---

問題が解決しない場合は、[GitHubのIssues](https://github.com/hrkzogw/app-obsidian-abstractor/issues)でお問い合わせください。