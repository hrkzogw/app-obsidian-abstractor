# インストールガイド

このガイドでは、app-obsidian-abstractorのインストール方法を詳しく説明します。

## 🚀 クイックスタート（推奨）

ほとんどのユーザーは、ターミナルで以下のコマンドを実行するだけでインストールが完了します：

```bash
git clone https://github.com/hrkzogw/app-obsidian-abstractor.git
cd app-obsidian-abstractor
python tools/install_to_vault.py
```

インストーラーが対話形式でObsidian Vaultの場所とAPIキーを尋ねます。  
より詳細な設定や、別のインストール方法については、以下のガイドをご覧ください。

## 📋 前提条件

### 必須要件

- **Python**: 3.9以上（3.11以上を推奨）
- **Git**: リポジトリのクローン用
- **Obsidian**: ノート管理アプリ
- **Google AI APIキー**: Gemini APIの利用に必要

### 推奨環境

- **OS**: macOS、Linux、Windows 10/11
- **メモリ**: 4GB以上（大きなPDFを処理する場合は8GB推奨）
- **ストレージ**: 1GB以上の空き容量

### Obsidianプラグイン

- **Shell Commands**: Obsidianから直接ツールを実行する場合に必要

## 🚀 インストール方法

### 方法1: Obsidian Vaultへのインストール（推奨）

この方法では、ツールをObsidian vault内に直接インストールします。

#### 手順

1. **リポジトリのクローン**
   ```bash
   git clone https://github.com/hrkzogw/app-obsidian-abstractor.git
   cd app-obsidian-abstractor
   ```

2. **インストーラーの実行**
   ```bash
   python tools/install_to_vault.py
   ```

3. **インストーラーの対話的設定**
   - Obsidian vaultのパスを入力（自動検出される場合もあり）
   - Google AI APIキーを入力
   - 設定を確認してインストール

#### インストール先の構造

```
YourVault/
├── .obsidian/
│   └── tools/
│       └── abstractor/
│           ├── venv/          # Python仮想環境
│           ├── src/           # ソースコード
│           ├── config/        # 設定ファイル
│           ├── logs/          # ログファイル
│           └── run.sh         # 実行スクリプト
└── Tools/
    └── Obsidian Abstractor Help.md  # ヘルプドキュメント
```

### 方法2: スタンドアロンインストール

システム全体で使用する場合や、複数のvaultで共有する場合に適しています。

#### 手順

1. **リポジトリのクローン**
   ```bash
   git clone https://github.com/hrkzogw/app-obsidian-abstractor.git
   cd app-obsidian-abstractor
   ```

2. **仮想環境の作成（推奨）**
   ```bash
   # Python 3.11を使用する場合
   python3.11 -m venv venv
   
   # または利用可能な最新版
   python -m venv venv
   ```

3. **仮想環境の有効化**
   ```bash
   # macOS/Linux
   source venv/bin/activate
   
   # Windows
   venv\Scripts\activate
   ```

4. **依存関係のインストール**
   ```bash
   pip install -e .
   ```

5. **設定ファイルの準備**
   ```bash
   cp config/config.yaml.example config/config.yaml
   ```

6. **設定ファイルの編集**
   ```yaml
   # config/config.yaml
   api:
     google_ai_key: "your-api-key-here"
   
   vault:
     path: "~/Documents/Obsidian/YourVault"
   ```

## ⚙️ Google AI APIキーの取得

1. [Google AI Studio](https://makersuite.google.com/app/apikey)にアクセス
2. Googleアカウントでログイン
3. 「Create API Key」をクリック
4. 生成されたAPIキーをコピー
5. 設定ファイルに貼り付け

### APIキーの安全な管理

⚠️ **重要**: **APIキーはあなたのパスワードと同じです**。以下の点に必ず注意してください：

- **このキーを含む `config.yaml` ファイルを、パブリックなGitHubリポジトリなどに絶対にコミットしないでください**
- キーが漏洩した場合は、すぐに[Google AI Studio](https://makersuite.google.com/app/apikey)で無効化し、新しいキーを生成してください

より安全な管理方法：

- 環境変数として設定することも可能：
  ```bash
  export GOOGLE_AI_API_KEY="your-api-key"
  ```

- `.env`ファイルを使用：
  ```bash
  # .env
  GOOGLE_AI_API_KEY=your-api-key
  ```
  
  **注意**: `.env`ファイルも必ず`.gitignore`に追加してください

## 🔄 アップデート

### Vault内インストールの更新

```bash
cd /path/to/original/clone
git pull
python tools/install_to_vault.py --update
```

### スタンドアロンインストールの更新

```bash
cd app-obsidian-abstractor
git pull
pip install -e . --upgrade
```

## 🗑️ アンインストール

### Vault内インストールの削除

```bash
python tools/install_to_vault.py --uninstall
```

これにより：
- `.obsidian/tools/abstractor/`ディレクトリが削除されます
- ヘルプドキュメントが削除されます
- 設定ファイルのバックアップが作成されます

### スタンドアロンインストールの削除

```bash
# 仮想環境を無効化
deactivate

# ディレクトリを削除
rm -rf app-obsidian-abstractor
```

## ✅ インストールの確認

### 動作確認

```bash
# バージョン確認
python -m src.main --version

# ヘルプ表示
python -m src.main --help

# 設定確認
python -m src.main --show-config
```

### テスト実行

```bash
# サンプルPDFで動作確認
python -m src.main process tests/sample1.pdf --dry-run
```

## ✅ 最初のノートを生成してみる

インストールが完了したら、サンプルPDFを使って実際にノートを生成してみましょう。これにより、すべてが正しく設定されていることを確認できます。

### Vaultにインストールした場合

```bash
# Abstractorディレクトリに移動
cd /path/to/your/vault/.obsidian/tools/abstractor

# サンプルPDFを処理（実際のファイル書き込みを実行）
./run.sh process tests/sample1.pdf --output "path/to/your/inbox"
```

### スタンドアロンインストールの場合

```bash
# Abstractorディレクトリに移動
cd app-obsidian-abstractor

# 仮想環境を有効化（まだの場合）
source venv/bin/activate  # Mac/Linux
# または
venv\Scripts\activate     # Windows

# サンプルPDFを処理
python -m src.main process tests/sample1.pdf --output "path/to/your/inbox"
```

### 成功の確認

処理が成功すると：
1. 指定した出力フォルダに`.md`ファイルが作成されます
2. Obsidianでそのファイルを開くと、YAMLフロントマターと要約が表示されます
3. ログに「Successfully processed」というメッセージが表示されます

これで、app-obsidian-abstractorが正しく動作していることが確認できました！

## ⚠️ 注意事項

### Obsidian Syncを使用している場合

`.obsidian/tools/`内のファイルが同期対象となる可能性があります：

1. 仮想環境（venv）は容量が大きいため、同期から除外することを推奨
2. Obsidian設定で`.obsidian/tools/abstractor/venv`を同期対象外に設定
3. または、スタンドアロンインストールを選択

### 権限の問題

macOS/Linuxで実行権限エラーが発生した場合：

```bash
chmod +x run.sh
chmod +x run.bat  # Windowsでも必要な場合
```

### Pythonバージョンの問題

複数のPythonバージョンがインストールされている場合：

```bash
# 特定のバージョンを指定
python3.11 tools/install_to_vault.py

# またはpyenvを使用
pyenv local 3.11.0
python tools/install_to_vault.py
```

## 🆘 インストールで問題が発生した場合

[トラブルシューティングガイド](./troubleshooting.md)を参照するか、[GitHubのIssues](https://github.com/hrkzogw/app-obsidian-abstractor/issues)で質問してください。

---

次のステップ: [使い方ガイド](./usage.md)へ進む