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

## 最新更新レビュー (2025-07-19 11:38:30)

### 完了した作業

#### 1. 仮想環境の構築と依存関係の更新
- [x] **Python 3.11.13仮想環境の作成**: 将来の拡張性を考慮した最新Python版の選択
- [x] **google-generativeai → google-genai SDKへの移行**: 新しい統一SDKへの更新（v1.26.0）
- [x] **requirements.txtの更新**: 新しいSDKとその依存関係の正確な記録

#### 2. コード更新と最適化
- [x] **paper_abstractor.pyの全面更新**:
  - 古い`google.generativeai`から新しい`google.genai`への移行
  - `genai.configure()`から`genai.Client()`への変更
  - `genai.GenerativeModel()`から`client.models.generate_content()`への更新
  - 引数の渡し方をキーワード引数形式に修正
  - デフォルトモデルを`gemini-pro`から`gemini-2.0-flash-001`に更新

- [x] **config.yamlの更新**: 新しいモデル名の設定

#### 3. テストと動作確認
- [x] **基本動作テスト**: 新しいSDKでのクライアント初期化と簡単な生成テスト
- [x] **PDF処理テスト**: サンプルPDFファイルを使用した実際の処理テスト
  - `Jonides et al. 2008 - The mind and brain of short-term memory.pdf`
  - `Van Marcke and Desender 2025 - Context-dependent role of confidence in information-seeking.pdf`
- [x] **出力確認**: 生成されたObsidianノートの品質と構造の検証

### 技術的改善点

1. **SDK移行による安定性向上**:
   - 最新の統一Google Gen AI SDKへの移行により、将来的なサポートを確保
   - 新しいAPIエンドポイントとレスポンス形式への対応

2. **環境構築の改善**:
   - Python 3.11使用による最新機能の活用可能
   - 仮想環境による依存関係の完全分離

3. **処理性能の確認**:
   - 2つのサンプルPDFで正常動作を確認
   - 認知科学論文の実験・レビュー論文自動判別機能の動作確認

### 今後の推奨事項

1. **テストケースの拡張**: より多様なPDFファイルでのテスト
2. **エラーハンドリングの強化**: 新しいSDKのエラーパターンへの対応
3. **パフォーマンスの最適化**: レート制限やリトライ機能の調整
4. **ドキュメントの更新**: 新しいSDKに関する情報の反映

## 品質改善対応 (2025-07-19 12:25:30)

### 完了した改善作業

#### 1. 要約品質問題の分析
- [x] **問題の特定**: Geminiは高品質な要約を生成しているが、パーシング処理で情報が失われていた
- [x] **デバッグ機能の追加**: Geminiの生のレスポンスを保存する機能を実装
- [x] **根本原因の特定**: `_extract_section`と`_extract_experiment_details`メソッドの不完全なパーシングロジック

#### 2. 直接Markdown生成アプローチの実装
- [x] **新プロンプトテンプレートの作成**: `academic_abstract_markdown_ja.txt`
  - 完全なObsidian形式のMarkdownを直接生成
  - YAMLフロントマターを含む完全なドキュメント生成
  - PDFを視覚的に参照して内容を補完・修正する指示を追加
- [x] **paper_abstractor.pyの拡張**:
  - `_generate_markdown_with_gemini`メソッドを追加
  - `use_markdown_format`フラグによる新方式の有効化
- [x] **note_formatter.pyの更新**:
  - 直接生成されたMarkdownをそのまま返す機能を追加
  - パーシング処理を完全にバイパス

#### 3. 改善結果の確認
- [x] **実験論文のテスト**: 実験1、2、3が正しく整理され、重複なし
- [x] **レビュー論文のテスト**: 適切な構造で主要論点、コンセンサス、論争点が整理
- [x] **情報の完全性**: 参加者数、統計手法、結果が具体的に記載

### 改善の成果

1. **情報品質の大幅向上**:
   - パーシングによる情報損失を完全に回避
   - Geminiの生成能力を最大限活用

2. **構造の一貫性**:
   - 実験論文と レビュー論文の適切な判別と構造化
   - セクションの重複や断片化の解消

3. **拡張性の向上**:
   - プロンプトテンプレートの変更だけで出力形式を柔軟に調整可能
   - 将来的な改善や多言語対応が容易