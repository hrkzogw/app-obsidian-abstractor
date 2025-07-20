"""
Paperpile PDF synchronization module for Obsidian Abstractor.

This module provides functionality to sync PDFs from Paperpile's Google Drive
storage to an Obsidian vault using rclone.
"""

import asyncio
import logging
import subprocess
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import sys

from .utils.path_resolver import PathResolver

logger = logging.getLogger(__name__)


class PaperpileSync:
    """Handles synchronization of PDFs from Paperpile to Obsidian vault."""
    
    def __init__(self, config: Dict[str, Any], resolver: PathResolver):
        """
        Initialize the Paperpile sync module.
        
        Args:
            config: Configuration dictionary
            resolver: Path resolver instance
        """
        self.config = config
        self.resolver = resolver
        
        # Get paperpile_sync configuration
        self.sync_config = config.get('paperpile_sync', {})
        self.enabled = self.sync_config.get('enabled', False)
        
        if not self.enabled:
            logger.info("Paperpile sync is disabled in configuration")
            return
            
        # Sync settings
        self.rclone_remote = self.sync_config.get('rclone_remote', 'paperpile:')
        self.source_dirs = self.sync_config.get('source_dirs', ['Papers', 'Unsorted'])
        self.max_age = self.sync_config.get('max_age', '7d')
        self.log_file = Path(self.sync_config.get('log_file', '~/.paperpile-sync.log')).expanduser()
        
        # Get inbox directory from watch config or use default
        watch_config = config.get('watch', {})
        self.inbox_dir = self.sync_config.get('inbox_dir', 'Papers/Inbox')
        
        # Resolve vault path
        self.vault_path = resolver.vault_path
        if not self.vault_path:
            raise ValueError("Could not determine Obsidian vault path")
            
        # Log file setup
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def check_rclone(self) -> bool:
        """Check if rclone is available in the system PATH."""
        if not shutil.which("rclone"):
            logger.error("rclone command not found.")
            logger.error("Please install rclone and ensure it's in your system's PATH.")
            logger.error("Visit https://rclone.org/downloads/ for installation instructions.")
            return False
        return True
    
    def check_remote_configured(self) -> bool:
        """Check if the rclone remote is properly configured."""
        try:
            # Run rclone listremotes to check if remote exists
            result = subprocess.run(
                ["rclone", "listremotes"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to list rclone remotes: {result.stderr}")
                return False
                
            # Check if our remote is in the list
            remote_name = self.rclone_remote.rstrip(':')
            configured_remotes = result.stdout.strip().split('\n')
            
            for remote in configured_remotes:
                if remote.rstrip(':') == remote_name:
                    return True
                    
            logger.error(f"Remote '{remote_name}' not found in rclone configuration.")
            logger.error("Please run 'rclone config' to set up the Paperpile remote.")
            return False
            
        except Exception as e:
            logger.error(f"Error checking rclone remote: {e}")
            return False
    
    async def sync_directory(self, source_dir: str, dry_run: bool = False) -> Tuple[bool, int]:
        """
        Sync a single directory from Paperpile to Obsidian.
        
        Args:
            source_dir: Source directory name in Paperpile
            dry_run: If True, don't actually copy files
            
        Returns:
            Tuple of (success, files_transferred)
        """
        source_path = f"{self.rclone_remote}Paperpile/{source_dir}"
        dest_path = self.vault_path / self.inbox_dir / source_dir
        
        # Create destination directory
        dest_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Syncing '{source_path}' -> '{dest_path}'")
        
        # Build rclone command
        cmd = [
            "rclone", "copy",
            source_path, str(dest_path),
            "--include", "*.pdf",
            "--include", "*.bib",
            "--max-age", self.max_age,
            "--ignore-existing",
            "--no-traverse",
            "--transfers", "4",
            "--checkers", "8",
            "--log-file", str(self.log_file),
            "--log-level", "INFO",
            "--stats", "10s",
            "--stats-one-line",
            "--stats-log-level", "NOTICE"
        ]
        
        if dry_run:
            cmd.append("--dry-run")
            
        # Run rclone with real-time output
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            files_transferred = 0
            
            # Stream output line by line
            async for line in process.stdout:
                line_str = line.decode().strip()
                if line_str:
                    # Log to file and console
                    logger.info(f"rclone: {line_str}")
                    
                    # Try to extract transfer count
                    if "Transferred:" in line_str and "files" in line_str:
                        import re
                        match = re.search(r'(\d+)\s+files', line_str)
                        if match:
                            files_transferred = int(match.group(1))
            
            await process.wait()
            
            if process.returncode == 0:
                logger.info(f"✓ Successfully synced {source_dir}")
                return True, files_transferred
            else:
                logger.error(f"✗ Error syncing {source_dir} (exit code: {process.returncode})")
                return False, 0
                
        except Exception as e:
            logger.error(f"Error running rclone: {e}")
            return False, 0
    
    async def run(self, dry_run: bool = False) -> bool:
        """
        Run the full synchronization process.
        
        Args:
            dry_run: If True, perform a dry run without copying files
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.error("Paperpile sync is disabled in configuration.")
            logger.error("Set 'paperpile_sync.enabled: true' in config.yaml to enable.")
            return False
            
        # Check prerequisites
        if not self.check_rclone():
            return False
            
        if not self.check_remote_configured():
            return False
            
        # Log start
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._log_to_file(f"\n{'='*40}")
        self._log_to_file(f"Paperpile sync started at {timestamp}")
        self._log_to_file(f"Settings: MAX_AGE={self.max_age}, DRY_RUN={dry_run}")
        self._log_to_file(f"Vault: {self.vault_path}")
        
        if dry_run:
            logger.info("DRY RUN MODE - No files will be copied")
            
        # Sync each directory
        total_synced = 0
        all_success = True
        
        for source_dir in self.source_dirs:
            success, files_count = await self.sync_directory(source_dir, dry_run)
            if success:
                total_synced += files_count
            else:
                all_success = False
                
        # Log completion
        self._log_to_file(f"Sync completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._log_to_file(f"Total files synced: {total_synced}")
        
        # Show recent files statistics (if not dry run)
        if not dry_run:
            self._show_recent_files_stats()
            
        return all_success
    
    def _log_to_file(self, message: str):
        """Write a message to the log file."""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
        except Exception as e:
            logger.warning(f"Failed to write to log file: {e}")
    
    def _show_recent_files_stats(self):
        """Show statistics about recently added files."""
        try:
            inbox_path = self.vault_path / self.inbox_dir
            if not inbox_path.exists():
                return
                
            # Find files modified in the last 24 hours
            import time
            cutoff_time = time.time() - (24 * 60 * 60)
            
            recent_pdfs = []
            recent_bibs = []
            
            for file_path in inbox_path.rglob('*'):
                if file_path.is_file() and file_path.stat().st_mtime > cutoff_time:
                    if file_path.suffix == '.pdf':
                        recent_pdfs.append(file_path)
                    elif file_path.suffix == '.bib':
                        recent_bibs.append(file_path)
                        
            logger.info(f"Files added in last 24 hours: {len(recent_pdfs)} PDFs, {len(recent_bibs)} BibTeX files")
            
        except Exception as e:
            logger.warning(f"Failed to calculate recent files statistics: {e}")


async def sync_paperpile(config: Dict[str, Any], resolver: PathResolver, dry_run: bool = False) -> bool:
    """
    Main entry point for Paperpile synchronization.
    
    Args:
        config: Configuration dictionary
        resolver: Path resolver instance
        dry_run: If True, perform a dry run
        
    Returns:
        True if successful, False otherwise
    """
    try:
        sync = PaperpileSync(config, resolver)
        return await sync.run(dry_run)
    except Exception as e:
        logger.error(f"Paperpile sync failed: {e}")
        return False