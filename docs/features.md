# 機能一覧

app-obsidian-abstractorの全機能を網羅的に説明します。

## 📄 PDF処理エンジン

### コア機能

#### テキスト抽出
- **PyMuPDF (fitz)** による高精度なテキスト抽出
- レイアウト保持モードで表や図の位置関係を維持
- 複数カラムの学術論文に対応
- フォント情報を活用した見出し認識

#### メタデータ抽出
```python
# 抽出される情報
metadata = {
    'title': 'PDF title',
    'authors': ['Author 1', 'Author 2'],
    'created_date': '2025-01-19',
    'keywords': ['keyword1', 'keyword2'],
    'doi': '10.1234/example',
    'journal': 'Journal Name',
    'volume': '10',
    'issue': '2',
    'pages': '123-145'
}
```

#### 構造解析
- セクション・サブセクションの自動認識
- 図表キャプションの抽出
- 参考文献リストの分離
- 脚注・注釈の処理

### マルチモーダル処理

#### 画像抽出と分析
```python
# 画像抽出の設定
pdf:
  enable_visual_extraction: true
  max_image_pages: 5  # 重要なページを優先
  image_dpi: 200      # 高品質な画像抽出
```

優先される画像ページ：
1. Figureを含むページ
2. Tableを含むページ
3. Graphicsの多いページ
4. Abstractページ

#### AIによる視覚的理解
- 図表の内容を自然言語で説明
- グラフからのデータ読み取り
- 実験フローチャートの解釈
- 数式の意味理解

## 🤖 AI要約生成

### Google Gemini統合

#### 対応モデル
- **gemini-2.0-flash-exp**: 最新の高速モデル（推奨）
- **gemini-pro**: 標準的な処理
- **gemini-pro-vision**: マルチモーダル対応

#### 要約の構成要素

```markdown
# 生成される要約の構造

## 📚 論文全体の背景と目的
- 研究分野の背景
- 解決しようとする問題
- 研究の目的と仮説

## 🧪 実験の詳細
- 実験設計
- 使用データセット
- 評価指標
- 実験手順

## 📊 結果
- 主要な発見
- 定量的結果
- 統計的有意性

## 💡 総合考察と結論
- 結果の解釈
- 研究の貢献
- 限界と今後の課題
```

### カスタマイズ可能な要約

#### プロンプトテンプレート
```text
# config/prompts/academic_abstract_markdown_ja.txt
カスタマイズ可能な要素：
- 要約の長さ
- 含める情報の種類
- 専門用語の扱い
- 批判的分析の有無
```

#### 言語対応
- 日本語要約（デフォルト）
- 英語要約
- 自動言語検出モード

## 🔍 PDFフィルタリング

### Funnel方式の効率的フィルタリング

```python
# フィルタリング処理の流れ
1. ファイル名チェック（最速）
   - 学術的でないパターンを除外
   
2. ファイルサイズチェック（高速）
   - 極端に小さい/大きいファイルを除外
   
3. PDFメタデータチェック（中速）
   - Producer、Creator情報を確認
   
4. コンテンツスキャン（低速）
   - 本文から学術的特徴を検出
```

### スコアリングシステム

#### ポジティブスコア（学術論文の特徴）
| 特徴 | スコア | 説明 |
|------|--------|------|
| DOI検出 | +50 | DOIが含まれている |
| Abstract検出 | +20 | Abstractセクションがある |
| References検出 | +20 | 参考文献リストがある |
| 学術出版社 | +20 | Elsevier、Springerなど |
| 適切なページ数 | +15 | 8-40ページ |

#### ネガティブスコア（非学術文書）
| 特徴 | スコア | 説明 |
|------|--------|------|
| 請求書パターン | -100 | invoice、billなど |
| マニュアル | -70 | manual、guideなど |
| プレゼン資料 | -50 | slides、presentationなど |

### 隔離機能

```yaml
pdf_filter:
  quarantine_enabled: true
  quarantine_folder: "~/PDFs/Non-Academic"
```

非学術PDFは自動的に隔離フォルダに移動され、処理をスキップします。

## 📁 フォルダ監視システム

### リアルタイム監視

#### イベント検出
- ファイル作成
- ファイル移動
- ファイル更新（オプション）

#### スマートな処理
```python
# 重複処理の防止
- ファイルハッシュによる識別
- 処理済みリストの管理
- 一時ファイルの無視

# 安定性の確保
- ファイル書き込み完了の待機
- ロック機構による競合回避
- エラー時の自動リトライ
```

### 複数フォルダ対応

```yaml
watch:
  folders:
    - "~/Downloads"        # ダウンロードフォルダ
    - "~/Mendeley/PDFs"   # Mendeleyライブラリ
    - "vault://Inbox"     # Obsidian内フォルダ
    - "/shared/Papers"    # 共有フォルダ
```

## 🔗 パス解決システム

### vault:// プレフィックス

```python
# パス解決の例
"vault://Papers/2025" → "~/Obsidian/MyVault/Papers/2025"
"vault://inbox"       → "~/Obsidian/MyVault/inbox"
```

### 動的プレースホルダー

| プレースホルダー | 説明 | 例 |
|------------------|------|-----|
| `{{year}}` | 現在の年 | 2025 |
| `{{month}}` | 現在の月 | 01 |
| `{{day}}` | 現在の日 | 19 |
| `{{author}}` | 第一著者の姓 | Smith |
| `{{timestamp}}` | Unixタイムスタンプ | 1737280800 |

### パス正規化

- Windows/Unix パスの自動変換
- 相対パスの解決
- シンボリックリンクの追跡

## 📝 Obsidianノート生成

### YAMLフロントマター

```yaml
---
# 基本情報
title: "論文タイトル"
authors:
  - "山田, 太."
  - "鈴木, 花. 子."
year-published: '2025'

# 出版情報
journal: "Nature Machine Intelligence"
volume: 6
issue: 3
pages: 234-245
doi: https://doi.org/10.1038/s42256-025-00123-4

# 分類情報
language: ja
keywords:
  - deep learning
  - natural language processing
  - transformer

# メタ情報
created: '2025-01-19 14:30:00'
pdf-path: '[[Papers/original.pdf]]'
abstract-by: gemini-2.0-flash-exp

# 引用情報（APA形式）
citation: '山田太・鈴木花子 (2025). 論文タイトル. Nature Machine Intelligence, 6(3), 234-245.'
---
```

### インライン図表

```markdown
> [!info] Figure 1: 実験設定の概要 (p.5)
> **実験の流れ**: 参加者は画面中央の注視点を500ms見た後、
> 刺激が100ms提示される。その後マスク刺激が...
> **主要な結果**: 条件Aでは平均反応時間が450ms（SD=50）
```

### 相互参照

- PDFファイルへの内部リンク
- 関連ノートへのプレースホルダー
- 図表への参照リンク

## 🚀 パフォーマンス最適化

### 並列処理

```python
# 非同期処理アーキテクチャ
- asyncio による並行処理
- 複数PDFの同時処理
- API呼び出しの並列化
- I/O待機時間の最小化
```

### キャッシング

#### キャッシュ対象
- PDF解析結果
- API応答
- 画像抽出結果

#### キャッシュ戦略
```yaml
cache:
  strategy: "LRU"  # Least Recently Used
  max_size_gb: 5
  ttl_days: 7
```

### メモリ管理

- ストリーミング処理による大容量PDF対応
- 画像の段階的リサイズ
- ガベージコレクションの最適化

## 🔐 セキュリティ機能

### APIキー管理

- 環境変数サポート
- 設定ファイルのマスキング
- キーローテーション対応

### ファイルアクセス制御

- 読み取り専用モード
- サンドボックス実行
- パス traversal 攻撃の防止

## 📊 統計とレポート

### 処理統計

```bash
# 統計情報の例
処理済みPDF: 1,234
成功率: 98.5%
平均処理時間: 32.5秒
総要約文字数: 1,234,567
```

### エクスポート機能

- CSV形式での統計出力
- 処理履歴のJSON出力
- 月次レポートの生成

## 🎨 拡張性

### プラグインアーキテクチャ

```python
# カスタムプロセッサの例
class CustomProcessor:
    def process(self, pdf_data):
        # カスタム処理
        return processed_data
```

### Webhook統合

```yaml
webhooks:
  on_success: "https://example.com/success"
  on_error: "https://example.com/error"
```

### 外部ツール連携

- Zotero連携（計画中）
- Mendeley連携（計画中）
- Notion連携（計画中）

---

詳細な使い方については[使い方ガイド](./usage.md)を、設定については[設定ガイド](./configuration.md)を参照してください。