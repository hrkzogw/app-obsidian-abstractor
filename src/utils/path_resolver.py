"""
Path resolution utilities for handling various path formats.

Supports:
- vault:// - Vault-relative paths
- ~/ - Home directory relative paths
- / - Absolute paths
- Other - Relative to base path or current directory
"""

import os
import re
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PathResolver:
    """Resolve paths with support for vault-relative paths and placeholders."""
    
    VAULT_PREFIX = "vault://"
    
    def __init__(self, vault_path: Optional[Path] = None):
        """
        Initialize PathResolver.
        
        Args:
            vault_path: Path to the Obsidian vault
        """
        self.vault_path = Path(vault_path).expanduser().resolve() if vault_path else None
        
    def resolve_path(self, path_str: str, base_path: Optional[Path] = None) -> Path:
        """
        Resolve a path string to an absolute Path object.
        
        Args:
            path_str: Path string to resolve
            base_path: Base path for relative paths (defaults to current directory)
            
        Returns:
            Resolved absolute Path object
            
        Raises:
            ValueError: If vault path is required but not set
        """
        if not path_str:
            raise ValueError("Path string cannot be empty")
        
        # Normalize path separators for cross-platform compatibility
        path_str = path_str.replace("\\", "/")
        
        # Handle vault-relative paths
        if path_str.startswith(self.VAULT_PREFIX):
            if not self.vault_path:
                raise ValueError(f"Vault path not set, cannot resolve: {path_str}")
            
            relative_path = path_str[len(self.VAULT_PREFIX):]
            # Remove leading slash if present
            relative_path = relative_path.lstrip("/")
            
            resolved = self.vault_path / relative_path
            logger.debug(f"Resolved vault path: {path_str} -> {resolved}")
            return resolved.resolve()
        
        # Create Path object
        path = Path(path_str)
        
        # Handle home directory expansion
        if path_str.startswith("~"):
            resolved = path.expanduser().resolve()
            logger.debug(f"Resolved home path: {path_str} -> {resolved}")
            return resolved
        
        # Handle absolute paths
        if path.is_absolute():
            resolved = path.resolve()
            logger.debug(f"Resolved absolute path: {path_str} -> {resolved}")
            return resolved
        
        # Handle relative paths
        if base_path:
            resolved = (base_path / path).resolve()
        else:
            resolved = path.resolve()
        
        logger.debug(f"Resolved relative path: {path_str} -> {resolved}")
        return resolved
    
    def resolve_with_placeholders(self, path_str: str, 
                                 context: Optional[Dict[str, Any]] = None,
                                 base_path: Optional[Path] = None) -> Path:
        """
        Resolve a path string with placeholder substitution.
        
        Supported placeholders:
        - {{year}} - Current year (YYYY)
        - {{month}} - Current month (MM)
        - {{day}} - Current day (DD)
        - {{date}} - Current date (YYYY-MM-DD)
        - {{vault}} - Vault path
        - Custom placeholders from context dict
        
        Args:
            path_str: Path string with placeholders
            context: Dictionary of custom placeholder values
            base_path: Base path for relative paths
            
        Returns:
            Resolved Path object with placeholders replaced
        """
        # Get current datetime
        now = datetime.now()
        
        # Build placeholder values
        placeholders = {
            "year": now.strftime("%Y"),
            "month": now.strftime("%m"),
            "day": now.strftime("%d"),
            "date": now.strftime("%Y-%m-%d"),
            "vault": str(self.vault_path) if self.vault_path else "",
        }
        
        # Add custom context values
        if context:
            placeholders.update(context)
        
        # Replace placeholders
        resolved_str = path_str
        for key, value in placeholders.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in resolved_str:
                resolved_str = resolved_str.replace(placeholder, str(value))
                logger.debug(f"Replaced {placeholder} with {value}")
        
        # Check for unresolved placeholders
        unresolved = re.findall(r'\{\{(\w+)\}\}', resolved_str)
        if unresolved:
            logger.warning(f"Unresolved placeholders: {unresolved}")
        
        # Resolve the final path
        return self.resolve_path(resolved_str, base_path)
    
    def is_vault_path(self, path_str: str) -> bool:
        """Check if a path string is a vault-relative path."""
        return path_str.startswith(self.VAULT_PREFIX)
    
    def to_vault_relative(self, path: Path) -> Optional[str]:
        """
        Convert an absolute path to a vault-relative path if possible.
        
        Args:
            path: Absolute path to convert
            
        Returns:
            Vault-relative path string, or None if not within vault
        """
        if not self.vault_path:
            return None
        
        try:
            # Resolve both paths to handle symlinks
            path = path.resolve()
            vault = self.vault_path.resolve()
            
            # Check if path is within vault
            relative = path.relative_to(vault)
            return f"{self.VAULT_PREFIX}{relative.as_posix()}"
        except ValueError:
            # Path is not within vault
            return None
    
    def validate_path(self, path_str: str, must_exist: bool = False,
                     create_parents: bool = False) -> Path:
        """
        Validate and optionally create a path.
        
        Args:
            path_str: Path string to validate
            must_exist: Whether the path must already exist
            create_parents: Whether to create parent directories
            
        Returns:
            Validated Path object
            
        Raises:
            ValueError: If validation fails
        """
        try:
            resolved = self.resolve_path(path_str)
            
            if must_exist and not resolved.exists():
                raise ValueError(f"Path does not exist: {resolved}")
            
            if create_parents and not resolved.exists():
                resolved.parent.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created parent directories for: {resolved}")
            
            return resolved
            
        except Exception as e:
            raise ValueError(f"Invalid path '{path_str}': {e}")


def create_resolver(config: Dict[str, Any]) -> PathResolver:
    """
    Create a PathResolver from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured PathResolver instance
    """
    # Try multiple possible vault path locations in config
    vault_path = None
    
    # Check new structure first
    if 'vault' in config and 'path' in config['vault']:
        vault_path = config['vault']['path']
    # Fall back to old structure
    elif 'output' in config and 'vault_path' in config['output']:
        vault_path = config['output']['vault_path']
    
    return PathResolver(vault_path)