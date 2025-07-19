# コントリビューションガイド

app-obsidian-abstractorへの貢献を歓迎します！このガイドでは、プロジェクトへの貢献方法を説明します。

## 🚀 はじめに

### 開発環境のセットアップ

```bash
# リポジトリをフォーク＆クローン
git clone https://github.com/YOUR_USERNAME/app-obsidian-abstractor.git
cd app-obsidian-abstractor

# 開発用の仮想環境を作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 開発用依存関係をインストール
pip install -e ".[dev]"
```

### 開発用依存関係

```toml
# pyproject.toml の [project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "pytest-cov>=4.0",
    "black>=23.0",
    "isort>=5.12",
    "ruff>=0.1",
    "mypy>=1.0",
]
```

## 📝 コーディング規約

### スタイルガイド

- **フォーマッター**: Black（行長88文字）
- **インポート順序**: isort
- **リンター**: Ruff
- **型チェック**: mypy

### 自動フォーマット

```bash
# コードをフォーマット
black src tests
isort src tests

# リントチェック
ruff check src tests

# 型チェック
mypy src
```

### コーディング原則

1. **明確で読みやすいコード**を書く
2. **Type hints**を積極的に使用
3. **Docstring**（Google style）を必ず書く
4. **非同期処理**は適切に実装
5. **エラーハンドリング**を丁寧に行う

## 🧪 テスト

### テストの実行

```bash
# 全テストを実行
pytest

# カバレッジ付きで実行
pytest --cov=src --cov-report=html

# 特定のテストのみ
pytest tests/test_pdf_extractor.py
```

### テストの書き方

```python
# tests/test_example.py
import pytest
from src.pdf_extractor import PDFExtractor

class TestPDFExtractor:
    @pytest.fixture
    def extractor(self):
        return PDFExtractor()
    
    def test_extract_text(self, extractor):
        # Arrange
        pdf_path = Path("tests/fixtures/sample.pdf")
        
        # Act
        result = extractor.extract_text(pdf_path)
        
        # Assert
        assert result is not None
        assert "expected text" in result
```

## 🔄 プルリクエストのプロセス

### 1. Issueの確認または作成

- 既存のIssueがあるか確認
- なければ新しいIssueを作成して議論

### 2. ブランチの作成

```bash
# feature/機能名 または fix/バグ名
git checkout -b feature/add-new-template
```

### 3. 変更の実装

- 小さく、焦点を絞ったコミット
- 意味のあるコミットメッセージ

### 4. テストの追加

- 新機能には必ずテストを追加
- 既存のテストが通ることを確認

### 5. プルリクエストの作成

#### PRテンプレート

```markdown
## 概要
[変更の概要を記述]

## 変更内容
- [ ] 機能A を追加
- [ ] バグB を修正

## テスト
- [ ] 単体テストを追加
- [ ] 既存のテストが通る

## 関連Issue
Fixes #123
```

## 🏗️ プロジェクト構造

```
app-obsidian-abstractor/
├── src/
│   ├── main.py           # CLIエントリーポイント
│   ├── pdf_extractor.py  # PDF処理
│   ├── paper_abstractor.py # AI要約生成
│   ├── pdf_monitor.py    # フォルダ監視
│   └── utils/           # ユーティリティ
├── tests/
│   ├── fixtures/        # テスト用データ
│   └── test_*.py       # テストファイル
├── config/
│   ├── prompts/        # プロンプトテンプレート
│   └── config.yaml.example
└── docs/               # ドキュメント
```

## 🐛 バグ報告

### 良いバグ報告の例

```markdown
## 環境
- OS: macOS 14.0
- Python: 3.11.0
- app-obsidian-abstractor: v1.0.0

## 再現手順
1. `python -m src.main process large.pdf`を実行
2. 処理が50%で停止

## 期待される動作
PDFが正常に処理される

## 実際の動作
メモリエラーが発生

## エラーログ
```
MemoryError: Unable to allocate 2GB
```
```

## 💡 機能提案

### 良い機能提案の例

```markdown
## 背景
現在、PDFの言語を自動検出できない

## 提案
PDFの本文から言語を自動検出する機能

## 実装案
- langdetectライブラリを使用
- 最初の1000文字から判定
- config.yamlでオプション化

## メリット
- ユーザーが言語を指定する必要がない
- 多言語PDFに対応可能
```

## 📚 ドキュメントの改善

ドキュメントの改善も重要な貢献です：

- 誤字脱字の修正
- 不明確な説明の改善
- 新しい使用例の追加
- 翻訳の提供

## 🎯 貢献の優先順位

### High Priority
- セキュリティ修正
- クリティカルなバグ修正
- パフォーマンス改善

### Medium Priority
- 新機能の追加
- UIの改善
- ドキュメントの更新

### Low Priority
- コードのリファクタリング
- タイポの修正

## 📞 コミュニケーション

- **GitHub Issues**: バグ報告、機能提案
- **GitHub Discussions**: 一般的な議論
- **Pull Requests**: コードレビュー

## 🙏 謝辞

貢献していただいた全ての方に感謝します！

---

質問がある場合は、遠慮なくIssueを作成してください。