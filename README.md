# Obsidian Abstractor

[English](#english) | [日本語](#japanese)

<a id="english"></a>
## 🇬🇧 English

AI-powered academic paper summarizer for Obsidian.

### ✨ Key Features

- 📁 **Auto-detect PDFs**: Watch folders for new academic papers
- 📄 **Smart Extraction**: Extract text, metadata, and structure from PDFs
- 🤖 **AI Summaries**: Generate comprehensive abstracts using Google Gemini
- 📝 **Obsidian Integration**: Create formatted notes with YAML frontmatter
- 🔗 **Seamless Workflow**: Works perfectly with [app-obsidian_ai_organizer](https://github.com/hrkzogw/app-obsidian_ai_organizer)

### 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/hrkzogw/app-obsidian-abstractor.git
cd app-obsidian-abstractor

# Install dependencies
pip install -r requirements.txt

# Copy and edit configuration
cp config/config.yaml.example config/config.yaml

# Start watching for PDFs
python -m src.main watch ~/Papers --output ~/Obsidian/inbox
```

### 📖 Documentation

- [Installation Guide](docs/installation.md)
- [Usage Guide](docs/usage.md)
- [Configuration](docs/configuration.md)

### 🔧 Requirements

- Python 3.9+
- Google AI API key (for Gemini)
- Obsidian vault

---

<a id="japanese"></a>
## 🇯🇵 日本語

学術論文PDFをAIで要約し、Obsidianノートとして整理する強力なツールです。

### ✨ 主な機能

- 📁 **PDF自動検出**: 指定フォルダの新規論文を監視
- 📄 **スマート抽出**: PDFからテキスト、メタデータ、構造を抽出
- 🤖 **AI要約生成**: Google Geminiで詳細な要約を作成
- 📝 **Obsidian統合**: YAMLフロントマター付きのフォーマット済みノート作成
- 🔗 **シームレスな連携**: [app-obsidian_ai_organizer](https://github.com/hrkzogw/app-obsidian_ai_organizer)と完璧に連携

### 🚀 クイックスタート

```bash
# リポジトリをクローン
git clone https://github.com/hrkzogw/app-obsidian-abstractor.git
cd app-obsidian-abstractor

# 依存関係をインストール
pip install -r requirements.txt

# 設定ファイルをコピーして編集
cp config/config.yaml.example config/config.yaml

# PDF監視を開始
python -m src.main watch ~/Papers --output ~/Obsidian/inbox
```

### 📖 ドキュメント

詳細な説明は[日本語README](README_ja.md)をご覧ください。

### 🔧 必要条件

- Python 3.9以上
- Google AI APIキー（Gemini用）
- Obsidian vault

### 📝 生成されるノートの例

```markdown
---
title: "Deep Learning for Natural Language Processing"
authors: ["John Doe", "Jane Smith"]
year: 2024
journal: "Nature Machine Intelligence"
tags: [deep-learning, nlp, transformer, research-paper]
created: 2024-01-19
abstract-by: gemini-pro
---

# Deep Learning for Natural Language Processing

## 📋 Abstract

This paper presents a novel approach to natural language processing using...

## 🎯 Key Contributions

1. Novel architecture for sequence modeling
2. State-of-the-art results on benchmark datasets
3. Efficient training methodology

## 🔬 Methodology

The proposed method consists of...

## 📊 Results

- **Dataset A**: 95.2% accuracy (↑ 3.1%)
- **Dataset B**: 87.5% F1-score (↑ 2.4%)

## 💡 Insights

This research demonstrates that...

## 🔗 Related Notes

*[To be added by app-obsidian_ai_organizer]*
```

### 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### 📄 License

MIT License - see [LICENSE](LICENSE) file for details.