# Obsidian Abstractor

学術論文PDFを自動的に処理し、AIによる高品質な要約をObsidianノートとして生成するツールです。

## ✨ 主要機能

- 📁 **PDF自動監視**: 指定フォルダの新規論文を監視して自動処理
- 🤖 **AI要約生成**: Google Geminiで詳細な要約を作成
- 📝 **Obsidian統合**: YAMLフロントマター付きのフォーマット済みノート作成
- 🔍 **スマートフィルタリング**: 学術論文を自動判別して処理
- 🔗 **シームレスな連携**: [app-obsidian_ai_organizer](https://github.com/hrkzogw/app-obsidian_ai_organizer)と完璧に連携

## 🚀 クイックスタート

### Obsidian Vaultにインストール（推奨）

```bash
# リポジトリをクローン
git clone https://github.com/hrkzogw/app-obsidian-abstractor.git
cd app-obsidian-abstractor

# Obsidian vaultにインストール
python tools/install_to_vault.py
```

### Google AI APIキーの取得

[Google AI Studio](https://makersuite.google.com/app/apikey)でAPIキーを取得し、設定ファイルに記入してください。

## 📚 詳細ドキュメント

詳しい使い方や設定方法については、[docs/index.md](./docs/index.md)をご覧ください：

- **[はじめに](./docs/index.md)**: ドキュメントの目次とナビゲーション
- **[インストール](./docs/installation.md)**: 詳細なインストール手順
- **[使い方](./docs/usage.md)**: 実践的な使用方法
- **[設定](./docs/configuration.md)**: 設定ファイルの詳細
- **[トラブルシューティング](./docs/troubleshooting.md)**: 問題解決ガイド

## 📄 ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルを参照してください。

---

*Currently, the primary documentation is maintained in Japanese. We welcome contributions for English translation!*