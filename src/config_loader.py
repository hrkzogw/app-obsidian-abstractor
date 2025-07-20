"""
Configuration loader for Obsidian Abstractor.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """Load and manage configuration settings."""
    
    DEFAULT_CONFIG = {
        'api': {
            'google_ai_key': '',
            'model': 'gemini-pro',
            'max_tokens': 2048,
        },
        'watch': {
            'folders': [],
            'patterns': ['*.pdf', '*.PDF'],
            'ignore_patterns': ['*draft*', '*tmp*', '.*'],
        },
        'output': {
            'vault_path': '~/Obsidian',
            'inbox_folder': 'inbox',
            'template': 'default',
            'file_pattern': '{year}_{first_author}_{title_short}',
        },
        'abstractor': {
            'language': 'en',
            'max_length': 1000,
            'include_citations': True,
            'include_figures': True,
            'extract_keywords': True,
        },
        'pdf': {
            'max_size_mb': 100,
            'extraction_mode': 'auto',
            'handle_encrypted': False,
        },
        'advanced': {
            'pdf_cache': True,
            'cache_dir': '~/.cache/obsidian-abstractor',
            'log_level': 'INFO',
            'log_file': '~/.obsidian-abstractor/logs/app.log',
            'workers': 2,
            'retry_failed': True,
            'retry_attempts': 3,
        },
        'rate_limit': {
            'requests_per_minute': 60,
            'request_delay': 1,
            'batch_size': 5,
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration loader."""
        self.config_path = self._find_config_file(config_path)
        self.config = self._load_config()
        self._validate_config()
    
    def _find_config_file(self, config_path: Optional[str] = None) -> Optional[Path]:
        """Find configuration file."""
        if config_path:
            return Path(config_path)
        
        # Check default locations
        locations = [
            Path.cwd() / 'config' / 'config.yaml',
            Path.cwd() / 'config.yaml',
            Path.home() / '.obsidian-abstractor' / 'config.yaml',
            Path.home() / '.config' / 'obsidian-abstractor' / 'config.yaml',
        ]
        
        for location in locations:
            if location.exists():
                return location
        
        return None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        config = self.DEFAULT_CONFIG.copy()
        
        if self.config_path and self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f) or {}
                self._merge_config(config, file_config)
        
        # Expand paths
        config = self._expand_paths(config)
        
        # Load API key from environment if not in config
        # Check both old location (api.google_ai_key) and new location (google_ai_key)
        if 'api' in config and not config['api'].get('google_ai_key'):
            config['api']['google_ai_key'] = os.environ.get('GOOGLE_AI_API_KEY', '')
        
        # Also check root level google_ai_key
        if 'google_ai_key' in config and config['google_ai_key']:
            if 'api' not in config:
                config['api'] = {}
            config['api']['google_ai_key'] = config['google_ai_key']
        
        return config
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Merge override config into base config."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _expand_paths(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Expand ~ in paths."""
        if isinstance(config, dict):
            return {k: self._expand_paths(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._expand_paths(v) for v in config]
        elif isinstance(config, str) and '~' in config:
            return os.path.expanduser(config)
        else:
            return config
    
    def _validate_config(self) -> None:
        """Validate configuration."""
        if not self.config['api']['google_ai_key']:
            raise ValueError("Google AI API key not configured. Set GOOGLE_AI_API_KEY environment variable or add to config file.")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def __getitem__(self, key: str) -> Any:
        """Get configuration value."""
        return self.get(key)