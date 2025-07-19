# アーキテクチャ

app-obsidian-abstractorのシステムアーキテクチャと設計思想について説明します。

## 🏗️ システム概要

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   PDFFile   │────▶│ PDFExtractor │────▶│   AIClient  │
└─────────────┘     └──────────────┘     └─────────────┘
                            │                     │
                            ▼                     ▼
                    ┌──────────────┐     ┌─────────────┐
                    │  PDFFilter   │     │ NoteWriter  │
                    └──────────────┘     └─────────────┘
                                                 │
                                                 ▼
                                         ┌─────────────┐
                                         │ObsidianNote │
                                         └─────────────┘
```

## 📦 主要コンポーネント

### 1. PDFExtractor（PDF処理エンジン）

**責務**: PDFファイルからテキスト、メタデータ、画像を抽出

```python
class PDFExtractor:
    def extract_text(self, pdf_path: Path) -> str
    def extract_metadata(self, pdf_path: Path) -> Dict[str, Any]
    def extract_page_images(self, pdf_path: Path) -> List[Dict[str, Any]]
```

**設計思想**:
- PyMuPDFを使用した高速処理
- メモリ効率的なストリーミング処理
- エラー耐性（破損PDFへの対応）

### 2. PaperAbstractor（AI要約エンジン）

**責務**: 抽出されたデータからAIを使用して要約を生成

```python
class PaperAbstractor:
    async def generate_abstract(self, pdf_data: Dict) -> Dict
    async def _call_gemini_api(self, prompt: str) -> str
```

**設計思想**:
- 非同期処理によるスケーラビリティ
- プロンプトテンプレートの外部化
- マルチモーダル対応（テキスト＋画像）

### 3. PDFFilter（フィルタリングシステム）

**責務**: 学術論文とその他のPDFを判別

```python
class PDFFilter:
    def filter_pdf(self, pdf_path: Path) -> FilterResult
    def calculate_academic_score(self, features: Dict) -> int
```

**設計思想**:
- Funnel方式による効率的な処理
- カスタマイズ可能なスコアリングルール
- 早期終了による最適化

### 4. PDFMonitor（監視システム）

**責務**: フォルダを監視して新しいPDFを検出・処理

```python
class PDFMonitor:
    async def start(self) -> None
    async def _process_worker(self) -> None
    def _on_file_created(self, event: FileSystemEvent) -> None
```

**設計思想**:
- イベント駆動アーキテクチャ
- Producer-Consumerパターン
- asyncio.Queueによる非同期処理

### 5. PathResolver（パス解決システム）

**責務**: vault://などの特殊なパス記法を解決

```python
class PathResolver:
    def resolve_path(self, path_str: str) -> Path
    def resolve_with_placeholders(self, path_str: str) -> Path
```

**設計思想**:
- 拡張可能なパスプレフィックス
- 動的プレースホルダーサポート
- クロスプラットフォーム対応

## 🔄 データフロー

### 1. 単一PDF処理フロー

```
1. CLI Command
   └─> 2. PDFExtractor
       ├─> 3. Text Extraction
       ├─> 4. Metadata Extraction
       └─> 5. Image Extraction (optional)
           └─> 6. PaperAbstractor
               ├─> 7. Prompt Generation
               └─> 8. Gemini API Call
                   └─> 9. NoteWriter
                       └─> 10. Obsidian Note
```

### 2. フォルダ監視フロー

```
1. File System Event
   └─> 2. Event Handler
       └─> 3. Processing Queue
           └─> 4. Worker Pool
               └─> 5. PDF Processing Flow
```

## 🎯 設計原則

### 1. 非同期ファースト

```python
# 非同期処理の例
async def process_pdfs(pdf_paths: List[Path]):
    tasks = [process_single_pdf(path) for path in pdf_paths]
    results = await asyncio.gather(*tasks)
    return results
```

### 2. 疎結合

- 各コンポーネントは独立して動作
- 依存性注入による柔軟な構成
- インターフェースベースの設計

### 3. エラー耐性

```python
# エラーハンドリングの例
try:
    result = await process_pdf(pdf_path)
except PDFExtractionError:
    logger.error(f"Failed to extract: {pdf_path}")
    return None
```

### 4. 設定の外部化

- YAML形式の設定ファイル
- 環境変数のサポート
- ランタイム設定の変更

## 🔌 拡張ポイント

### 1. カスタムプロセッサ

```python
# カスタムプロセッサの実装例
class CustomProcessor(BaseProcessor):
    def process(self, data: Dict) -> Dict:
        # カスタム処理
        return processed_data

# 登録
processor_registry.register("custom", CustomProcessor)
```

### 2. プロンプトテンプレート

```
config/prompts/
├── academic_abstract_ja.txt
├── academic_abstract_en.txt
└── custom_template.txt
```

### 3. 出力フォーマット

```python
# カスタム出力フォーマット
class CustomNoteFormatter(BaseFormatter):
    def format(self, data: Dict) -> str:
        # カスタムフォーマット
        return formatted_note
```

## 📊 パフォーマンス考慮事項

### メモリ管理

- 大きなPDFはチャンク単位で処理
- 画像は必要に応じてリサイズ
- 処理完了後の即座なガベージコレクション

### 並列処理

```python
# ワーカープールの実装
class WorkerPool:
    def __init__(self, max_workers: int = 3):
        self.semaphore = asyncio.Semaphore(max_workers)
    
    async def process(self, task):
        async with self.semaphore:
            return await task
```

### キャッシング戦略

- LRUキャッシュによるAPI呼び出しの削減
- ファイルハッシュベースの重複検出
- 設定可能なTTL

## 🔐 セキュリティ考慮事項

### APIキー管理

- 環境変数による管理
- 設定ファイルのマスキング
- ログへの出力防止

### ファイルアクセス

- パストラバーサル攻撃の防止
- 読み取り専用アクセス
- サンドボックス内での実行

## 🚀 将来の拡張計画

### 計画中の機能

1. **プラグインシステム**
   - 動的なプロセッサローディング
   - カスタムフィルター
   - 外部統合

2. **分散処理**
   - ジョブキューシステム
   - 複数マシンでの処理
   - ロードバランシング

3. **Web API**
   - RESTful API
   - WebSocket通知
   - 管理画面

### アーキテクチャの進化

```
現在: Monolithic CLI Application
  ↓
次期: Modular Plugin System
  ↓
将来: Distributed Processing System
```

---

技術的な質問や提案がある場合は、[GitHubのDiscussions](https://github.com/hrkzogw/app-obsidian-abstractor/discussions)でお聞かせください。