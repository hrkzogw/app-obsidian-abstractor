"""
Note utility functions for Obsidian Abstractor.

This module provides utility functions for note processing,
including YAML frontmatter extraction and filename generation.
"""

import re
import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def extract_yaml_frontmatter(content: str) -> Dict[str, Any]:
    """Extract YAML frontmatter from note content."""
    if not content.startswith('---'):
        return {}
    
    # Find the end of frontmatter
    try:
        end_index = content.index('---', 3)
        yaml_content = content[3:end_index].strip()
        return yaml.safe_load(yaml_content) or {}
    except (ValueError, yaml.YAMLError):
        return {}


def create_short_title(title: str, max_length: int = 30) -> str:
    """Create a short version of the title."""
    # Remove common words
    stop_words = {'a', 'an', 'the', 'of', 'for', 'and', 'or', 'in', 'on', 'at', 'to', 'with', 'by'}
    
    words = title.split()
    important_words = [w for w in words if w.lower() not in stop_words]
    
    # Take first few important words
    short_title = ' '.join(important_words[:3])
    
    if len(short_title) > max_length:
        short_title = short_title[:max_length].rsplit(' ', 1)[0]
    
    return short_title


def clean_filename(filename: str) -> str:
    """Clean filename to be filesystem-safe."""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '-', filename)
    filename = re.sub(r'\s+', '_', filename)
    filename = re.sub(r'_+', '_', filename)
    filename = filename.strip('_-.')
    
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename


def generate_filename_from_yaml(yaml_data: Dict[str, Any], config: Dict[str, Any]) -> str:
    """Generate filename from YAML frontmatter data."""
    # Extract fields
    year = yaml_data.get('year-published', str(datetime.now().year))
    authors_list = yaml_data.get('authors', [])
    title = yaml_data.get('title', 'Untitled')
    
    # Format authors field
    if len(authors_list) == 0:
        authors = 'Unknown'
        first_author = 'Unknown'
    elif len(authors_list) == 1:
        # "Schwartz, M. A." → "Schwartz"
        authors = authors_list[0].split(',')[0].strip()
        first_author = authors
    elif len(authors_list) == 2:
        # ["Adam, H.", "Galinsky, A. D."] → "Adam_Galinsky"
        authors = f"{authors_list[0].split(',')[0].strip()}_{authors_list[1].split(',')[0].strip()}"
        first_author = authors_list[0].split(',')[0].strip()
    else:
        # 3+ authors → "FirstAuthor_et_al"
        authors = f"{authors_list[0].split(',')[0].strip()}_et_al"
        first_author = authors_list[0].split(',')[0].strip()
    
    # Get pattern and convert double braces to single braces
    pattern = config.get('output', {}).get('filename_pattern', '{{year}}_{{authors}}_{{title}}')
    pattern = pattern.replace('{{', '{').replace('}}', '}')
    
    # Format filename
    filename = pattern.format(
        year=year,
        authors=authors,
        first_author=first_author,
        title=title,
        title_short=create_short_title(title)
    )
    
    return clean_filename(filename)


def handle_rename(temp_path: Path, final_path: Path) -> Path:
    """Safely rename file with conflict handling."""
    if final_path.exists():
        # File already exists, add counter
        counter = 1
        base_stem = final_path.stem
        while final_path.exists():
            final_path = final_path.parent / f"{base_stem}_{counter}.md"
            counter += 1
        logger.warning(f"File already exists, renamed to: {final_path.name}")
    
    try:
        temp_path.rename(final_path)
        return final_path
    except Exception as e:
        logger.error(f"Failed to rename file: {e}")
        # If rename fails, try to clean up temp file
        if temp_path.exists():
            temp_path.unlink()
        raise