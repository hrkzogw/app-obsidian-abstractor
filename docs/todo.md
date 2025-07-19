# TODO: Obsidian Abstractor 開発タスク

## 現在の進捗 (2025-01-19)

### 完了したタスク
- [x] プロジェクトディレクトリ構造の作成
- [x] README.md（英語）の作成
- [x] README_ja.md（日本語詳細ガイド）の作成
- [x] pyproject.tomlとrequirements.txtの作成
- [x] 基本的なCLIインターフェース（src/main.py）の実装
- [x] 設定ローダー（src/config_loader.py）の実装
- [x] CLAUDE.md（開発ガイドライン）の作成
- [x] **pdf_extractor.py**: PyMuPDFを使用したPDF解析機能
  - [x] テキスト抽出
  - [x] メタデータ抽出（タイトル、著者、出版年）
  - [x] セクション構造の認識
  - [x] 図表キャプションの抽出
  - [x] 参考文献の抽出
- [x] **paper_abstractor.py**: Gemini APIを使用した要約生成
  - [x] プロンプトテンプレートの作成
  - [x] 構造化された要約の生成
  - [x] 言語切り替え機能（日本語/英語）
  - [x] レート制限の実装
- [x] **note_formatter.py**: Obsidianノート生成
  - [x] YAMLフロントマターの生成
  - [x] マークダウン形式での要約整形
  - [x] テンプレートシステムの実装
- [x] **pdf_monitor.py**: フォルダ監視機能
  - [x] watchdogを使用したファイル監視
  - [x] 新規PDFの検出
  - [x] 処理キューの管理
  - [x] デーモンモードの実装
- [x] **prompts/academic_abstract_ja.txt**: 日本語AIプロンプトテンプレート
- [x] **prompts/academic_abstract_en.txt**: 英語AIプロンプトテンプレート
- [x] **main.pyの全コマンド実装**: watch, batch, process
- [x] **エラーハンドリング**: 破損PDF、大容量ファイル対応
- [x] **キャッシュシステム**: 処理済みPDFの管理

### 次のステップ

#### テストとドキュメント
- [ ] 単体テストの作成
- [ ] 統合テストの作成
- [ ] installation.mdの作成
- [ ] usage.mdの作成
- [ ] configuration.mdの作成

### 将来の機能拡張
- [ ] 図表の画像抽出とノート埋め込み
- [ ] arXiv/PubMed APIとの連携
- [ ] 引用ネットワークの可視化
- [ ] バッチ処理の並列化
- [ ] Web UIの追加
- [ ] 複数言語の論文対応（中国語、韓国語）
- [ ] Zoteroとの連携

## 実装レビュー (2025-01-19)

### 実装完了モジュール

1. **pdf_extractor.py** - PDF処理エンジン
   - PyMuPDFによる堅牢なPDF解析
   - メタデータ、構造、図表、参考文献の抽出
   - 暗号化PDF、大容量ファイルのハンドリング

2. **paper_abstractor.py** - AI要約エンジン
   - Google Gemini APIとの統合
   - 構造化された要約生成
   - 日英バイリンガル対応
   - レート制限とリトライ機能

3. **note_formatter.py** - ノート生成エンジン
   - Obsidian形式のマークダウン生成
   - YAMLフロントマターの自動生成
   - カスタマイズ可能なファイル名パターン

4. **pdf_monitor.py** - フォルダ監視エンジン
   - watchdogによるリアルタイム監視
   - 非同期処理による高速化
   - キャッシュによる重複回避

5. **CLIインターフェース**
   - 3つのコマンド（watch, batch, process）
   - Richライブラリによる美しい出力
   - プログレスバーとステータス表示

### 技術的特徴

- **非同期処理**: asyncio/aiofiesによる高速処理
- **エラーハンドリング**: 様々なPDF形式に対応
- **設定の柔軟性**: YAMLによる詳細な設定
- **拡張性**: モジュール設計による容易な機能追加