#!/usr/bin/env python3
"""
Obsidian Abstractor Vault Installer

This script installs the Abstractor into an Obsidian vault as a companion tool
for the Shell Commands plugin.
"""

import os
import sys
import shutil
import platform
import subprocess
import argparse
from pathlib import Path
from typing import Optional, Tuple, List
import json
import re

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class VaultInstaller:
    """Handles installation of Abstractor into Obsidian vault."""
    
    def __init__(self, mode: str = "install"):
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent
        self.install_path: Optional[Path] = None
        self.vault_path: Optional[Path] = None
        self.mode = mode  # install, update, or uninstall
        self._config_backup: Optional[str] = None
        
    def run(self) -> bool:
        """Run the installation process."""
        try:
            if self.mode == "uninstall":
                return self._run_uninstall()
            elif self.mode == "update":
                return self._run_update()
            else:
                return self._run_install()
                
        except KeyboardInterrupt:
            print("\n\n❌ 操作がキャンセルされました。")
            return False
        except Exception as e:
            print(f"\n\n❌ エラーが発生しました: {e}")
            return False
    
    def _run_install(self) -> bool:
        """Run the installation process."""
        print(self._get_banner())
        
        # Step 1: Introduction and confirmation
        if not self._show_introduction():
            return False
            
        # Step 2: Select installation location
        if not self._select_install_location():
            return False
            
        # Step 3: Check prerequisites
        if not self._check_prerequisites():
            return False
            
        # Step 4: Copy files
        print("\n📁 ファイルをコピー中...")
        if not self._copy_files():
            return False
            
        # Step 5: Setup virtual environment
        print("\n🔧 Python環境をセットアップ中...")
        if not self._setup_virtual_environment():
            return False
            
        # Step 6: Generate configuration
        print("\n⚙️  設定ファイルを生成中...")
        if not self._generate_config():
            return False
            
        # Step 7: Generate .gitignore
        if not self._generate_gitignore():
            return False
            
        # Step 8: Show Shell Commands setup
        self._show_shell_commands_setup()
        
        # Step 9: Show completion message
        self._show_completion()
        
        return True
    
    def _run_update(self) -> bool:
        """Run the update process."""
        print(self._get_banner("update"))
        
        # Find existing installation
        if not self._find_existing_installation():
            print("❌ 既存のインストールが見つかりません。")
            print("   先に通常のインストールを実行してください。")
            return False
            
        print(f"\n📍 インストール場所: {self.install_path}")
        
        # Backup config
        config_path = self.install_path / "config" / "config.yaml"
        if config_path.exists():
            self._config_backup = config_path.read_text(encoding='utf-8')
            print("✓ 設定ファイルをバックアップしました")
            
        # Update files
        print("\n📁 ファイルを更新中...")
        if not self._copy_files():
            return False
            
        # Restore config
        if self._config_backup:
            config_path.write_text(self._config_backup, encoding='utf-8')
            print("✓ 設定ファイルを復元しました")
            
        # Update dependencies
        print("\n📦 依存関係を更新中...")
        if not self._update_dependencies():
            return False
            
        print("\n✨ アップデート完了！")
        return True
    
    def _run_uninstall(self) -> bool:
        """Run the uninstall process."""
        print(self._get_banner("uninstall"))
        
        # Find existing installation
        if not self._find_existing_installation():
            print("❌ 既存のインストールが見つかりません。")
            return False
            
        print(f"\n📍 インストール場所: {self.install_path}")
        
        # Confirmation
        print("\n⚠️  以下のディレクトリを完全に削除します:")
        print(f"   {self.install_path}")
        
        response = input("\n本当に削除しますか？ [y/N]: ").strip().lower()
        if response != 'y':
            print("キャンセルしました。")
            return False
            
        # Remove installation
        try:
            shutil.rmtree(self.install_path)
            print("✓ アンインストール完了")
            
            # Remove help document if in vault
            if self.vault_path:
                help_doc = self.vault_path / "Abstractor ヘルプ.md"
                if help_doc.exists():
                    help_doc.unlink()
                    print("✓ ヘルプドキュメントを削除しました")
                    
            return True
        except Exception as e:
            print(f"❌ 削除に失敗しました: {e}")
            return False
    
    def _get_banner(self, mode: str = "install") -> str:
        """Get the banner text."""
        if mode == "update":
            title = "Obsidian Abstractor アップデート"
        elif mode == "uninstall":
            title = "Obsidian Abstractor アンインストール"
        else:
            title = "Obsidian Abstractor インストーラー"
            
        return f"""
╔══════════════════════════════════════════════════════╗
║      {title:^48}      ║
╚══════════════════════════════════════════════════════╝
"""
    
    def _show_introduction(self) -> bool:
        """Show introduction and get confirmation."""
        print("""
このツールは、学術論文PDFをAIで要約し、Obsidianノートとして
整理するPython製のツールです。

Obsidianの「Shell Commands」プラグインと連携して動作します。

⚠️  重要な注意事項:
• これは通常のObsidianプラグインではありません
• .obsidian/tools/ にインストールされます
• Obsidian Syncを使用している場合、仮想環境（venv）が
  同期対象になる可能性があります

必要なもの:
• Obsidian
• Google AI API キー（Gemini用）

推奨:
• Shell Commandsプラグイン（Obsidian内から右クリックで使用する場合）
""")
        
        response = input("続行しますか？ [Y/n]: ").strip().lower()
        return response in ['', 'y', 'yes']
    
    def _find_existing_installation(self) -> bool:
        """Find existing installation."""
        # Check common locations
        possible_paths = []
        
        # Try to find from current directory
        current = Path.cwd()
        while current != current.parent:
            if (current / ".obsidian").exists():
                possible_paths.append(current / ".obsidian" / "tools" / "abstractor")
            current = current.parent
            
        # Check if any exist
        for path in possible_paths:
            if path.exists() and (path / "src").exists():
                self.install_path = path
                self.vault_path = path.parent.parent.parent
                return True
                
        return False
    
    def _detect_vault_paths(self) -> List[Path]:
        """Detect common Obsidian vault locations."""
        vault_paths = []
        home = Path.home()
        
        # Common vault locations
        common_paths = [
            home / "Documents" / "Obsidian",
            home / "Obsidian",
            home / "Documents",
            home / "Desktop",
            home / "OneDrive" / "Documents",
            home / "Dropbox",
            home / "iCloud Drive" / "Documents",
        ]
        
        # Search for .obsidian directories
        for base_path in common_paths:
            if base_path.exists():
                try:
                    for item in base_path.rglob(".obsidian"):
                        if item.is_dir():
                            vault_path = item.parent
                            if vault_path not in vault_paths:
                                vault_paths.append(vault_path)
                except PermissionError:
                    continue
                    
        return vault_paths
    
    def _select_install_location(self) -> bool:
        """Select installation location."""
        print("\n📍 インストール先を選択してください：\n")
        print("1. 推奨: Obsidian Vault内 (.obsidian/tools/abstractor/)")
        print("2. カスタム: 任意の場所を指定")
        
        # Detect vaults
        detected_vaults = self._detect_vault_paths()
        if detected_vaults:
            print("\n🔍 検出されたVault:")
            for i, vault in enumerate(detected_vaults[:5]):  # Show max 5
                print(f"   {i+3}. {vault}")
        
        choice = input("\n選択 [1]: ").strip() or '1'
        
        if choice == '1':
            # Manual vault path input
            vault_path = input("\nObsidian Vaultのパスを入力してください: ").strip()
            if not vault_path:
                print("❌ パスが入力されていません。")
                return False
            
            vault_path = self._normalize_path(vault_path)
            self.vault_path = Path(vault_path).expanduser().resolve()
            
            if not self._validate_vault(self.vault_path):
                return False
                
            self.install_path = self.vault_path / ".obsidian" / "tools" / "abstractor"
            
        elif choice == '2':
            custom_path = input("\nインストール先のパスを入力してください: ").strip()
            if not custom_path:
                print("❌ パスが入力されていません。")
                return False
            
            custom_path = self._normalize_path(custom_path)
            self.install_path = Path(custom_path).expanduser().resolve()
            
            # Try to find vault path from custom location
            current = self.install_path
            while current != current.parent:
                if (current / ".obsidian").exists():
                    self.vault_path = current
                    break
                current = current.parent
                
        elif choice.isdigit() and 3 <= int(choice) < 3 + len(detected_vaults):
            # Selected from detected vaults
            self.vault_path = detected_vaults[int(choice) - 3]
            self.install_path = self.vault_path / ".obsidian" / "tools" / "abstractor"
            
        else:
            print("❌ 無効な選択です。")
            return False
            
        print(f"\n✓ インストール先: {self.install_path}")
        if self.vault_path:
            print(f"✓ Vault: {self.vault_path}")
            
        return True
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path by removing quotes."""
        if (path.startswith('"') and path.endswith('"')) or \
           (path.startswith("'") and path.endswith("'")):
            return path[1:-1]
        return path
    
    def _validate_vault(self, vault_path: Path) -> bool:
        """Validate if path is a valid Obsidian vault."""
        if not (vault_path / ".obsidian").exists():
            print(f"❌ {vault_path} は有効なObsidian Vaultではありません。")
            return False
        return True
    
    def _check_prerequisites(self) -> bool:
        """Check Python version and other prerequisites."""
        print("\n🔍 環境をチェック中...")
        
        # Check Python version
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 9):
            print(f"❌ Python 3.9以上が必要です。現在: {version.major}.{version.minor}")
            return False
            
        if version.major == 3 and version.minor < 11:
            print(f"⚠️  Python {version.major}.{version.minor} を使用中。")
            print("   Python 3.11以上を推奨します（パフォーマンス向上のため）。")
        else:
            print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        
        # Check if install path already exists
        if self.install_path.exists():
            print(f"\n⚠️  {self.install_path} は既に存在します。")
            
            # Check for existing config (silently backup)
            existing_config = self.install_path / "config" / "config.yaml"
            if existing_config.exists():
                # Save existing config without mentioning it
                self._config_backup = existing_config.read_text(encoding='utf-8')
            
            response = input("既存のスクリプトや仮想環境を再インストールしますか？ [y/N]: ").strip().lower()
            if response != 'y':
                return False
                
            # Backup existing installation
            backup_path = self.install_path.with_suffix('.backup')
            if backup_path.exists():
                shutil.rmtree(backup_path)
            shutil.move(str(self.install_path), str(backup_path))
            print(f"✓ 既存のインストールをバックアップしました: {backup_path}")
            
        return True
    
    def _copy_files(self) -> bool:
        """Copy necessary files to installation directory."""
        # Create installation directory
        self.install_path.mkdir(parents=True, exist_ok=True)
        
        # Files and directories to copy
        items_to_copy = [
            ("src", "src"),
            ("config/config.yaml.example", "config/config.yaml.example"),
            ("config/prompts", "config/prompts"),  # Copy entire prompts directory
            ("pyproject.toml", "pyproject.toml"),
            ("run.sh", "run.sh"),
            ("run.bat", "run.bat"),
        ]
        
        for src_item, dst_item in items_to_copy:
            src_path = self.project_root / src_item
            dst_path = self.install_path / dst_item
            
            if not src_path.exists():
                print(f"⚠️  {src_item} が見つかりません。スキップします。")
                continue
                
            try:
                if src_path.is_dir():
                    # Ensure parent directory exists
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    # Copy directory
                    shutil.copytree(
                        src_path, 
                        dst_path, 
                        dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(
                            '__pycache__', '*.pyc', '*.pyo', '*.pyd',
                            '.DS_Store', 'Thumbs.db', '*.log'
                        )
                    )
                else:
                    # Ensure parent directory exists
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    # Copy file
                    shutil.copy2(src_path, dst_path)
                print(f"✓ {src_item}")
            except Exception as e:
                print(f"❌ {src_item} のコピーに失敗: {e}")
                return False
                
        # Create necessary directories
        for dir_name in ["logs", "output"]:
            (self.install_path / dir_name).mkdir(exist_ok=True)
            
        # Make run.sh executable on Unix-like systems
        if platform.system() != 'Windows':
            run_sh_path = self.install_path / "run.sh"
            if run_sh_path.exists():
                run_sh_path.chmod(0o755)
                print("✓ run.sh を実行可能にしました")
        
        # Copy README.md to vault root as a help document
        if self.vault_path:
            readme_src = self.project_root / "docs" / "usage.md"
            help_doc_dst = self.vault_path / "Abstractor ヘルプ.md"
            
            if readme_src.exists():
                try:
                    # Read README content
                    readme_content = readme_src.read_text(encoding='utf-8')
                    
                    # Update installation paths
                    install_path_str = str(self.install_path).replace('\\', '/')
                    
                    # Write modified content
                    help_doc_dst.write_text(readme_content, encoding='utf-8')
                    print(f"✓ ヘルプドキュメントをVaultに追加: Abstractor ヘルプ.md")
                except Exception as e:
                    print(f"⚠️  ヘルプドキュメントのコピーに失敗: {e}")
                    
        return True
    
    def _setup_virtual_environment(self) -> bool:
        """Setup virtual environment and install dependencies."""
        venv_path = self.install_path / "venv"
        
        print("仮想環境を作成中...")
        try:
            # Create virtual environment
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)],
                check=True,
                cwd=str(self.install_path)
            )
            print("✓ 仮想環境を作成しました")
            
            # Determine pip path
            if platform.system() == "Windows":
                pip_path = venv_path / "Scripts" / "pip.exe"
                python_path = venv_path / "Scripts" / "python.exe"
            else:
                pip_path = venv_path / "bin" / "pip"
                python_path = venv_path / "bin" / "python"
                
            # Upgrade pip
            print("pipをアップグレード中...")
            subprocess.run(
                [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Install dependencies
            print("依存関係をインストール中...")
            result = subprocess.run(
                [str(pip_path), "install", "-e", "."],
                cwd=str(self.install_path),
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"❌ 依存関係のインストールに失敗しました:")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                return False
            
            print("✓ 依存関係をインストールしました")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 環境セットアップに失敗しました: {e}")
            return False
    
    def _update_dependencies(self) -> bool:
        """Update dependencies in existing virtual environment."""
        venv_path = self.install_path / "venv"
        
        if not venv_path.exists():
            print("仮想環境が見つかりません。完全な再インストールが必要です。")
            return False
            
        # Determine pip path
        if platform.system() == "Windows":
            pip_path = venv_path / "Scripts" / "pip.exe"
        else:
            pip_path = venv_path / "bin" / "pip"
            
        try:
            # Update dependencies
            print("依存関係を更新中...")
            result = subprocess.run(
                [str(pip_path), "install", "-e", ".", "--upgrade"],
                cwd=str(self.install_path),
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"❌ 依存関係の更新に失敗しました:")
                print("STDERR:", result.stderr)
                return False
                
            print("✓ 依存関係を更新しました")
            return True
            
        except Exception as e:
            print(f"❌ 更新に失敗しました: {e}")
            return False
    
    def _generate_config(self) -> bool:
        """Generate config.yaml interactively."""
        config_path = self.install_path / "config" / "config.yaml"
        
        # Check if we have a backup from a previous installation
        if hasattr(self, '_config_backup') and self._config_backup:
            print("\n⚠️  以前の設定ファイルが見つかりました。")
            
            # Try to extract API key from backup
            api_key_match = re.search(r'google_ai_key:\s*["\']?([^"\'\n]+)["\']?', self._config_backup)
            if api_key_match and api_key_match.group(1) != "YOUR_GEMINI_API_KEY_HERE":
                masked_key = self._mask_api_key(api_key_match.group(1))
                print(f"   APIキー: {masked_key}")
                
            print("   既存の設定を保持しますか？")
            print("   1. はい - 既存の設定を保持（推奨）")
            print("   2. いいえ - 新しい設定を作成")
            
            keep_existing = input("\n選択 [1]: ").strip() or '1'
            
            if keep_existing == '1':
                # Restore the backed up config
                config_path.parent.mkdir(parents=True, exist_ok=True)
                config_path.write_text(self._config_backup, encoding='utf-8')
                print("✓ 既存の config.yaml を復元しました")
                return True
        
        # Generate new config.yaml
        config_content = f"""# Obsidian Abstractor 設定ファイル
# インストーラーによって生成されました

# ========================================
# 必須設定
# ========================================

# Google AI APIキー（必須）
# 取得方法: https://makersuite.google.com/app/apikey
google_ai_key: "YOUR_GEMINI_API_KEY_HERE"

# ========================================
# フォルダ設定（必須）
# ========================================
folder_settings:
  # Obsidian Vaultのフルパス
  vault_path: "{str(self.vault_path)}"
  
  # デフォルトの出力先 (process, batchコマンド用)
  # vault:// を使うとVault相対パスになります
  default_output: "vault://Abstracts"
  
  # watchコマンドで監視するフォルダ
  watch_folders:
    - "~/Downloads"
    - "vault://PDFs/Inbox"
  
  # watchコマンドの出力先 (オプション)
  watch_output: "vault://Papers/{{{{year}}}}"

# ========================================
# AI設定
# ========================================
ai:
  # 使用するモデル
  model: "gemini-2.0-flash-exp"
  # 生成時の温度パラメータ
  temperature: 0.3
  # 最大出力トークン数
  max_tokens: 8192

# ========================================
# 要約設定
# ========================================
abstractor:
  # 要約の言語 (ja: 日本語, en: 英語)
  language: "ja"
  # 要約の最大文字数
  max_length: 6000
  # キーワードを抽出するか
  extract_keywords: true
  # Obsidianリンクを作成するか
  create_links: true

# ========================================
# PDF処理設定
# ========================================
pdf:
  # 最大ファイルサイズ (MB)
  max_file_size: 50
  # 視覚的抽出を有効にするか（図表をAIに解析させる）
  enable_visual_extraction: true
  # 画像抽出の最大ページ数
  max_image_pages: 5
  # 画像抽出時のDPI
  image_dpi: 150

# ========================================
# 出力設定
# ========================================
output:
  # ファイル名パターン
  # 使用可能な変数: {{{{year}}}}, {{{{authors}}}}, {{{{title}}}}
  filename_pattern: "{{{{year}}}}_{{{{authors}}}}_{{{{title}}}}"
  # 年ごとのサブディレクトリを作成するか
  organize_by_year: false

# ========================================
# ファイル監視設定
# ========================================
watch:
  # 監視するファイルパターン
  patterns: ["*.pdf", "*.PDF"]
  # 無視するパターン
  ignore_patterns: ["**/archive/**", "**/templates/**", ".*"]
  # 処理遅延（秒）
  process_delay: 5

# ========================================
# ログ設定
# ========================================
logging:
  level: INFO
  file: ./logs/abstractor.log
  console: true
"""
        
        config_path = self.install_path / "config" / "config.yaml"
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(config_content, encoding='utf-8')
            print(f"✓ config.yamlを生成しました")
            return True
        except Exception as e:
            print(f"❌ 設定ファイルの生成に失敗しました: {e}")
            return False
    
    def _mask_api_key(self, api_key: str) -> str:
        """Mask API key for display."""
        if len(api_key) < 8:
            return "****"
        return f"{api_key[:4]}...{api_key[-4:]}"
    
    def _generate_gitignore(self) -> bool:
        """Generate .gitignore file."""
        gitignore_content = """# Virtual environment
venv/
__pycache__/
*.pyc
*.pyo
*.pyd

# Configuration (contains API key)
config/config.yaml

# Generated files
logs/
output/
*.log

# Backups
*.bak
*.backup

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.temp
"""
        
        gitignore_path = self.install_path / ".gitignore"
        try:
            gitignore_path.write_text(gitignore_content, encoding='utf-8')
            print("✓ .gitignoreを生成しました")
            return True
        except Exception as e:
            print(f"❌ .gitignoreの生成に失敗しました: {e}")
            return False
    
    def _show_shell_commands_setup(self):
        """Show Shell Commands setup instructions."""
        print(f"""
╔══════════════════════════════════════════════════════╗
║           Shell Commands 設定                        ║
╚══════════════════════════════════════════════════════╝

📖 設定方法:

1. ObsidianでShell Commandsプラグインを開く
2. 新しいコマンドを追加:

   【PDFファイル処理】
   Name: Abstract PDF
   Command: cd "{{{{vault_path}}}}/.obsidian/tools/abstractor" && ./run.sh process "{{{{file_path}}}}" --output "{{{{folder}}}}"
   
   【フォルダ一括処理】
   Name: Abstract PDFs in Folder
   Command: cd "{{{{vault_path}}}}/.obsidian/tools/abstractor" && ./run.sh batch "{{{{folder}}}}"
   
   【設定ファイルを開く】
   Name: Open Abstractor Config
   Command: {"open" if platform.system() == "Darwin" else "start" if platform.system() == "Windows" else "xdg-open"} "{{{{vault_path}}}}/.obsidian/tools/abstractor/config/config.yaml"

3. ホットキーを設定（任意）:
   - 設定 → ホットキー → "Shell Commands: Abstract PDF"を検索
   - お好みのキーを割り当て（例: Cmd+Shift+A）

💡 すぐに試すには：
1. 任意のPDFファイルをVault内に配置
2. PDFファイルを右クリック
3. "Abstract PDF"を選択
4. 同じフォルダに要約ノートが生成されます
""")
    
    def _show_completion(self):
        """Show completion message."""
        print(f"""
╔══════════════════════════════════════════════════════╗
║         ✨ インストール完了！                        ║
╚══════════════════════════════════════════════════════╝

⚠️  重要: Google AI APIキーの設定が必要です

1. 以下のファイルを開いてください：
   {self.install_path / "config" / "config.yaml"}

2. "YOUR_GEMINI_API_KEY_HERE"を実際のAPIキーに置き換えてください

APIキーの取得方法：
https://makersuite.google.com/app/apikey

───────────────────────────────────────

📚 使い始めるには：

1. config.yamlでAPIキーを設定
2. Shell Commandsプラグインでコマンドを追加（上記参照）
3. PDFファイルを右クリックして「Abstract PDF」を実行

💡 具体的な使い方：
- 単一PDF処理: PDFファイルを右クリック → "Abstract PDF"
- フォルダ一括処理: フォルダを右クリック → "Abstract PDFs in Folder"
- 自動監視: ヘルプドキュメントの「フォルダ監視の設定」を参照

📖 詳細な使い方：
Obsidianで「Abstractor ヘルプ」ノートを開いてください。
Shell Commandsの設定方法やワークフローの例が記載されています。
""")
        
        # Open config directory in file manager
        self._open_in_file_manager()
    
    def _open_in_file_manager(self):
        """Open config directory in system file manager."""
        config_path = self.install_path / "config"
        try:
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(config_path)])
                print(f"\n📂 Finderで設定フォルダを開きました")
            elif platform.system() == "Windows":
                subprocess.run(["explorer", str(config_path)])
                print(f"\n📂 エクスプローラーで設定フォルダを開きました")
            elif platform.system() == "Linux":
                # Try common Linux file managers
                for cmd in ["xdg-open", "nautilus", "dolphin", "thunar"]:
                    try:
                        subprocess.run([cmd, str(config_path)])
                        print(f"\n📂 ファイルマネージャーで設定フォルダを開きました")
                        break
                    except FileNotFoundError:
                        continue
        except Exception as e:
            # Don't fail the installation if we can't open the file manager
            print(f"\n📂 設定フォルダ: {config_path}")
            print("（自動的に開くことができませんでした）")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Obsidian Abstractor Vault Installer"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update existing installation"
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall from vault"
    )
    
    args = parser.parse_args()
    
    # Determine mode
    if args.update:
        mode = "update"
    elif args.uninstall:
        mode = "uninstall"
    else:
        mode = "install"
    
    installer = VaultInstaller(mode=mode)
    success = installer.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()