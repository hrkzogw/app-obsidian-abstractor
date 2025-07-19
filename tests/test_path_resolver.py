"""
Tests for path resolution functionality.
"""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

from src.utils.path_resolver import PathResolver, create_resolver


class TestPathResolver:
    """Test cases for PathResolver class."""
    
    @pytest.fixture
    def vault_path(self, tmp_path):
        """Create temporary vault path."""
        vault = tmp_path / "ObsidianVault"
        vault.mkdir()
        return vault
    
    @pytest.fixture
    def resolver(self, vault_path):
        """Create PathResolver instance."""
        return PathResolver(vault_path)
    
    def test_vault_relative_path(self, resolver, vault_path):
        """Test vault-relative path resolution."""
        # Basic vault path
        result = resolver.resolve_path("vault://Papers/Inbox")
        expected = vault_path / "Papers" / "Inbox"
        assert result == expected
        
        # With leading slash after prefix
        result = resolver.resolve_path("vault:///Papers/Inbox")
        assert result == expected
    
    def test_home_relative_path(self, resolver):
        """Test home directory relative path resolution."""
        result = resolver.resolve_path("~/Documents")
        expected = Path.home() / "Documents"
        assert result == expected
    
    def test_absolute_path(self, resolver):
        """Test absolute path resolution."""
        if Path("/tmp").exists():
            result = resolver.resolve_path("/tmp/test")
            assert result == Path("/tmp/test")
    
    def test_relative_path(self, resolver, tmp_path):
        """Test relative path resolution."""
        # With base path
        base = tmp_path / "base"
        base.mkdir()
        result = resolver.resolve_path("subfolder/file.txt", base)
        assert result == (base / "subfolder" / "file.txt").resolve()
        
        # Without base path (current directory)
        result = resolver.resolve_path("test.txt")
        assert result == Path("test.txt").resolve()
    
    def test_vault_path_without_vault(self):
        """Test vault path resolution without vault set."""
        resolver = PathResolver(None)
        with pytest.raises(ValueError, match="Vault path not set"):
            resolver.resolve_path("vault://Papers")
    
    def test_empty_path(self, resolver):
        """Test empty path string."""
        with pytest.raises(ValueError, match="Path string cannot be empty"):
            resolver.resolve_path("")
    
    def test_cross_platform_paths(self, resolver):
        """Test cross-platform path handling."""
        # Windows-style path should be normalized
        result = resolver.resolve_path("folder\\subfolder\\file.txt")
        # Should be converted to forward slashes internally
        assert "folder" in str(result)
        assert "subfolder" in str(result)
    
    @patch('src.utils.path_resolver.datetime')
    def test_placeholders(self, mock_datetime, resolver):
        """Test placeholder substitution."""
        # Mock datetime
        mock_now = mock_datetime.now.return_value
        mock_now.strftime.side_effect = lambda fmt: {
            "%Y": "2024",
            "%m": "01",
            "%d": "15",
            "%Y-%m-%d": "2024-01-15"
        }.get(fmt, "")
        
        # Test date placeholders
        result = resolver.resolve_with_placeholders("vault://Papers/{{year}}/{{month}}")
        expected = resolver.vault_path / "Papers" / "2024" / "01"
        assert result == expected
        
        # Test with custom context
        context = {
            "author": "Smith",
            "paper_year": "2023",
            "title": "Deep Learning"
        }
        result = resolver.resolve_with_placeholders(
            "vault://Papers/{{paper_year}}/{{author}}/{{title}}", 
            context
        )
        expected = resolver.vault_path / "Papers" / "2023" / "Smith" / "Deep Learning"
        assert result == expected
    
    def test_unresolved_placeholders(self, resolver, caplog):
        """Test warning for unresolved placeholders."""
        resolver.resolve_with_placeholders("vault://Papers/{{unknown}}/{{missing}}")
        assert "Unresolved placeholders" in caplog.text
        assert "unknown" in caplog.text
        assert "missing" in caplog.text
    
    def test_is_vault_path(self, resolver):
        """Test vault path detection."""
        assert resolver.is_vault_path("vault://Papers")
        assert resolver.is_vault_path("vault:///Papers")
        assert not resolver.is_vault_path("~/Papers")
        assert not resolver.is_vault_path("/Papers")
    
    def test_to_vault_relative(self, resolver, vault_path):
        """Test conversion to vault-relative path."""
        # Path within vault
        path = vault_path / "Papers" / "2024" / "paper.md"
        result = resolver.to_vault_relative(path)
        assert result == "vault://Papers/2024/paper.md"
        
        # Path outside vault
        result = resolver.to_vault_relative(Path("/tmp/outside"))
        assert result is None
        
        # No vault set
        resolver_no_vault = PathResolver(None)
        result = resolver_no_vault.to_vault_relative(path)
        assert result is None
    
    def test_validate_path(self, resolver, tmp_path):
        """Test path validation."""
        # Valid existing path
        existing = tmp_path / "existing.txt"
        existing.write_text("test")
        result = resolver.validate_path(str(existing), must_exist=True)
        assert result == existing
        
        # Non-existing path with must_exist
        with pytest.raises(ValueError, match="Path does not exist"):
            resolver.validate_path("vault://nonexistent", must_exist=True)
        
        # Create parents
        new_path = tmp_path / "new" / "deep" / "file.txt"
        result = resolver.validate_path(str(new_path), create_parents=True)
        assert result.parent.exists()
    
    def test_create_resolver(self):
        """Test resolver creation from config."""
        # New config structure
        config = {
            "vault": {"path": "~/ObsidianVault"},
            "output": {"default_path": "vault://Papers"}
        }
        resolver = create_resolver(config)
        assert resolver.vault_path == Path("~/ObsidianVault").expanduser()
        
        # Old config structure
        config_old = {
            "output": {"vault_path": "~/ObsidianVault"}
        }
        resolver = create_resolver(config_old)
        assert resolver.vault_path == Path("~/ObsidianVault").expanduser()
        
        # No vault path
        config_empty = {}
        resolver = create_resolver(config_empty)
        assert resolver.vault_path is None