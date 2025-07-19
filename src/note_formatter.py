"""
Note formatter module for Obsidian Abstractor.

This module provides functionality to format extracted paper data and abstracts
into Obsidian-compatible markdown notes with YAML frontmatter.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NoteFormatter:
    """Format paper data into Obsidian notes."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the note formatter.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Output settings
        self.template = config.get('output', {}).get('template', 'default')
        self.file_pattern = config.get('output', {}).get('file_pattern', '{year}_{first_author}_{title_short}')
        
        # Language setting
        self.language = config.get('abstractor', {}).get('language', 'en')
    
    def format_note(self, pdf_data: Dict[str, Any], abstract_data: Dict[str, Any], pdf_path: Path) -> str:
        """
        Format all data into an Obsidian note.
        
        Args:
            pdf_data: Extracted PDF data
            abstract_data: Generated abstract data
            pdf_path: Path to the original PDF file
            
        Returns:
            Formatted markdown note content
        """
        # Generate frontmatter
        frontmatter = self.generate_frontmatter(pdf_data, abstract_data, pdf_path)
        
        # Generate note body
        body = self.format_body(pdf_data, abstract_data)
        
        # Combine frontmatter and body
        note_content = f"---\n{yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)}---\n\n{body}"
        
        return note_content
    
    def generate_frontmatter(self, pdf_data: Dict[str, Any], abstract_data: Dict[str, Any], pdf_path: Path) -> Dict[str, Any]:
        """
        Generate YAML frontmatter for the note.
        
        Args:
            pdf_data: Extracted PDF data
            abstract_data: Generated abstract data
            pdf_path: Path to the original PDF file
            
        Returns:
            Dictionary containing frontmatter data
        """
        metadata = pdf_data.get('metadata', {})
        
        # Extract authors list
        authors = self._extract_authors(metadata.get('author', ''))
        
        # Generate tags
        tags = self._generate_tags(abstract_data.get('keywords', []), pdf_data)
        
        frontmatter = {
            'title': metadata.get('title', pdf_path.stem),
            'authors': authors,
            'year': metadata.get('year', datetime.now().year),
            'journal': metadata.get('subject', ''),
            'doi': self._extract_doi(pdf_data),
            'tags': tags,
            'created': datetime.now().strftime('%Y-%m-%d'),
            'pdf-path': f"[[{pdf_path.name}]]",
            'abstract-by': abstract_data.get('model_used', 'unknown'),
            'language': abstract_data.get('abstract_language', self.language),
            'page-count': pdf_data.get('page_count', 0),
            'file-size-mb': pdf_data.get('file_size_mb', 0),
        }
        
        # Remove empty values
        frontmatter = {k: v for k, v in frontmatter.items() if v}
        
        return frontmatter
    
    def format_body(self, pdf_data: Dict[str, Any], abstract_data: Dict[str, Any]) -> str:
        """
        Format the note body content.
        
        Args:
            pdf_data: Extracted PDF data
            abstract_data: Generated abstract data
            
        Returns:
            Formatted markdown body
        """
        sections = []
        
        # Title
        title = pdf_data.get('metadata', {}).get('title', 'Untitled Paper')
        sections.append(f"# {title}\n")
        
        # Check paper type
        paper_type = abstract_data.get('paper_type', 'unknown')
        
        if paper_type == 'experimental':
            # Format experimental paper
            sections.extend(self._format_experimental_paper(abstract_data))
        elif paper_type == 'review':
            # Format review paper
            sections.extend(self._format_review_paper(abstract_data))
        else:
            # Fallback to original format
            sections.extend(self._format_generic_paper(abstract_data))
        
        # Figures and tables
        if pdf_data.get('figures'):
            if self.language == 'ja':
                sections.append("## 📈 図表\n")
            else:
                sections.append("## 📈 Figures and Tables\n")
            for fig in pdf_data['figures'][:10]:
                sections.append(f"- **{fig['type'].capitalize()} {fig['number']}**: {fig['caption']} (p.{fig['page']})")
            sections.append("")
        
        # Related notes placeholder
        if self.language == 'ja':
            sections.append("## 🔗 関連ノート\n")
            sections.append("*[app-obsidian_ai_organizerで自動追加]*\n")
        else:
            sections.append("## 🔗 Related Notes\n")
            sections.append("*[To be added by app-obsidian_ai_organizer]*\n")
        
        # References sample
        if pdf_data.get('references'):
            if self.language == 'ja':
                sections.append("## 📚 参考文献（抜粋）\n")
            else:
                sections.append("## 📚 References (Sample)\n")
            for i, ref in enumerate(pdf_data['references'][:5], 1):
                sections.append(f"{i}. {ref}")
            if len(pdf_data['references']) > 5:
                sections.append(f"\n*... and {len(pdf_data['references']) - 5} more references*")
            sections.append("")
        
        # Personal notes section
        if self.language == 'ja':
            sections.append("## 📝 個人的なメモ\n")
            sections.append("- [ ] 詳細を読む")
            sections.append("- [ ] 実装を試す")
            sections.append("- [ ] 関連研究を調査")
        else:
            sections.append("## 📝 Personal Notes\n")
            sections.append("- [ ] Read in detail")
            sections.append("- [ ] Try implementation")
            sections.append("- [ ] Research related work")
        
        return "\n".join(sections)
    
    def _format_experimental_paper(self, abstract_data: Dict[str, Any]) -> List[str]:
        """Format sections for experimental paper."""
        sections = []
        
        # Background and objectives
        if abstract_data.get('background') or abstract_data.get('objectives'):
            sections.append("## 📚 論文全体の背景と目的\n")
            if abstract_data.get('background'):
                sections.append(f"**研究の背景**: {abstract_data['background']}\n")
            if abstract_data.get('prior_research'):
                sections.append(f"**先行研究と問題点**: {abstract_data['prior_research']}\n")
            if abstract_data.get('objectives'):
                sections.append(f"**本研究の目的と仮説**: {abstract_data['objectives']}\n")
        
        # Experiments
        if abstract_data.get('experiments'):
            sections.append("## 🧪 各実験の詳細\n")
            for exp in abstract_data['experiments']:
                sections.append(f"### 実験 {exp.get('number', '1')}")
                if exp.get('objectives'):
                    sections.append(f"**目的と仮説**: {exp['objectives']}")
                if exp.get('participants'):
                    sections.append(f"**実験参加者**: {exp['participants']}")
                if exp.get('tasks'):
                    sections.append(f"**課題と刺激**: {exp['tasks']}")
                if exp.get('procedure'):
                    sections.append(f"**手続き**: {exp['procedure']}")
                if exp.get('analysis'):
                    sections.append(f"**分析方法**: {exp['analysis']}")
                if exp.get('results'):
                    sections.append(f"**結果と小括**: {exp['results']}")
                sections.append("")
        
        # Discussion
        if abstract_data.get('discussion'):
            sections.append("## 💡 総合考察と結論\n")
            sections.append(f"{abstract_data['discussion']}\n")
        
        # Contributions
        if abstract_data.get('contributions'):
            sections.append("## 🎯 学術的貢献\n")
            sections.append(f"{abstract_data['contributions']}\n")
        
        # Limitations
        if abstract_data.get('limitations'):
            sections.append("## ⚠️ 研究の限界と今後の展望\n")
            sections.append(f"{abstract_data['limitations']}\n")
        
        return sections
    
    def _format_review_paper(self, abstract_data: Dict[str, Any]) -> List[str]:
        """Format sections for review paper."""
        sections = []
        
        # Review theme and purpose
        if abstract_data.get('review_theme') or abstract_data.get('review_necessity'):
            sections.append("## 📚 レビューの主題と目的\n")
            if abstract_data.get('review_theme'):
                sections.append(f"**レビューの主題**: {abstract_data['review_theme']}\n")
            if abstract_data.get('review_necessity'):
                sections.append(f"**レビューの必要性**: {abstract_data['review_necessity']}\n")
        
        # Main theories and discussions
        sections.append("## 🔍 主要な論点と議論の整理\n")
        if abstract_data.get('main_theories'):
            sections.append(f"**主要な理論・モデル**: {abstract_data['main_theories']}\n")
        if abstract_data.get('discussion_classification'):
            sections.append(f"**議論の分類**: {abstract_data['discussion_classification']}\n")
        if abstract_data.get('landmark_studies'):
            sections.append(f"**画期的な研究**: {abstract_data['landmark_studies']}\n")
        
        # Consensus and controversies
        sections.append("## 🤝 学術的コンセンサスと論争点\n")
        if abstract_data.get('consensus'):
            sections.append(f"**コンセンサス**: {abstract_data['consensus']}\n")
        if abstract_data.get('controversies'):
            sections.append(f"**論争点**: {abstract_data['controversies']}\n")
        
        # Conclusions and future
        if abstract_data.get('conclusions') or abstract_data.get('future_directions'):
            sections.append("## 📋 著者らの結論と今後の展望\n")
            if abstract_data.get('conclusions'):
                sections.append(f"**結論と総括**: {abstract_data['conclusions']}\n")
            if abstract_data.get('future_directions'):
                sections.append(f"**今後の課題**: {abstract_data['future_directions']}\n")
        
        return sections
    
    def _format_generic_paper(self, abstract_data: Dict[str, Any]) -> List[str]:
        """Format sections for generic/unknown paper type."""
        sections = []
        
        # Summary section
        if abstract_data.get('summary'):
            if self.language == 'ja':
                sections.append("## 📋 要約\n")
            else:
                sections.append("## 📋 Abstract\n")
            sections.append(f"{abstract_data['summary']}\n")
        
        # Key contributions
        if abstract_data.get('key_contributions'):
            if self.language == 'ja':
                sections.append("## 🎯 主要な貢献\n")
            else:
                sections.append("## 🎯 Key Contributions\n")
            for contrib in abstract_data['key_contributions']:
                sections.append(f"- {contrib}")
            sections.append("")
        
        # Methodology
        if abstract_data.get('methodology'):
            if self.language == 'ja':
                sections.append("## 🔬 手法\n")
            else:
                sections.append("## 🔬 Methodology\n")
            sections.append(f"{abstract_data['methodology']}\n")
        
        # Results
        if abstract_data.get('results'):
            if self.language == 'ja':
                sections.append("## 📊 実験結果\n")
            else:
                sections.append("## 📊 Results\n")
            sections.append(f"{abstract_data['results']}\n")
        
        # Insights
        if abstract_data.get('insights'):
            if self.language == 'ja':
                sections.append("## 💡 洞察と考察\n")
            else:
                sections.append("## 💡 Insights\n")
            sections.append(f"{abstract_data['insights']}\n")
        
        # Limitations
        if abstract_data.get('limitations'):
            if self.language == 'ja':
                sections.append("## ⚠️ 限界と制限事項\n")
            else:
                sections.append("## ⚠️ Limitations\n")
            sections.append(f"{abstract_data['limitations']}\n")
        
        # Future work
        if abstract_data.get('future_work'):
            if self.language == 'ja':
                sections.append("## 🚀 今後の研究\n")
            else:
                sections.append("## 🚀 Future Work\n")
            sections.append(f"{abstract_data['future_work']}\n")
        
        return sections
    
    def generate_filename(self, pdf_data: Dict[str, Any], pdf_path: Path) -> str:
        """
        Generate a filename for the note.
        
        Args:
            pdf_data: Extracted PDF data
            pdf_path: Path to the original PDF file
            
        Returns:
            Generated filename (without extension)
        """
        metadata = pdf_data.get('metadata', {})
        
        # Extract components
        year = metadata.get('year', datetime.now().year)
        
        # Extract first author
        authors = self._extract_authors(metadata.get('author', ''))
        first_author = authors[0].split()[-1] if authors else 'Unknown'  # Last name
        
        # Create short title
        title = metadata.get('title', pdf_path.stem)
        title_short = self._create_short_title(title)
        
        # Format filename using pattern
        filename = self.file_pattern.format(
            year=year,
            first_author=first_author,
            title_short=title_short,
            title=title,
        )
        
        # Clean filename
        filename = self._clean_filename(filename)
        
        return filename
    
    def _extract_authors(self, author_string: str) -> List[str]:
        """Extract individual authors from author string."""
        if not author_string:
            return []
        
        # Common separators
        if ' and ' in author_string:
            authors = author_string.split(' and ')
        elif ';' in author_string:
            authors = author_string.split(';')
        elif ',' in author_string and not re.search(r'\b\w+,\s*\w+\b', author_string):
            # Comma separated (but not "LastName, FirstName" format)
            authors = author_string.split(',')
        else:
            authors = [author_string]
        
        # Clean and normalize
        authors = [a.strip() for a in authors if a.strip()]
        
        return authors
    
    def _generate_tags(self, keywords: List[str], pdf_data: Dict[str, Any]) -> List[str]:
        """Generate tags for the note."""
        tags = []
        
        # Add keywords as tags
        tags.extend(keywords)
        
        # Add default tags
        tags.append('research-paper')
        tags.append('academic')
        
        # Add language tag
        if self.language == 'ja':
            tags.append('japanese')
        
        # Add year tag
        year = pdf_data.get('metadata', {}).get('year')
        if year:
            tags.append(f'year-{year}')
        
        # Clean and deduplicate
        tags = [self._clean_tag(tag) for tag in tags]
        tags = list(dict.fromkeys(tags))  # Remove duplicates while preserving order
        
        return tags[:20]  # Limit to 20 tags
    
    def _extract_doi(self, pdf_data: Dict[str, Any]) -> Optional[str]:
        """Extract DOI from PDF data."""
        text = pdf_data.get('text', '')
        
        # DOI pattern
        doi_pattern = r'10\.\d{4,}/[-._;()/:\w]+'
        match = re.search(doi_pattern, text[:5000])  # Search in first part
        
        if match:
            return match.group(0)
        
        return None
    
    def _create_short_title(self, title: str, max_length: int = 30) -> str:
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
    
    def _clean_filename(self, filename: str) -> str:
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
    
    def _clean_tag(self, tag: str) -> str:
        """Clean tag for Obsidian."""
        # Remove special characters
        tag = re.sub(r'[^a-zA-Z0-9\-_]', '-', tag)
        tag = re.sub(r'-+', '-', tag)
        tag = tag.strip('-').lower()
        
        return tag