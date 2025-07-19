"""
PDF filtering module for academic paper detection.

This module implements a funnel approach to efficiently filter PDF files,
identifying academic papers using a scoring system.
"""

import re
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional, NamedTuple
from dataclasses import dataclass

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class FilterResult(NamedTuple):
    """Result of PDF filtering."""
    accepted: bool
    score: float
    reasons: List[str]
    details: Dict[str, Any]


@dataclass
class ScoringRule:
    """Scoring rule for PDF filtering."""
    pattern: str
    score: float
    description: str
    is_regex: bool = False


class PDFFilter:
    """Filter PDFs to identify academic papers using a scoring system."""
    
    # Default scoring rules
    DEFAULT_POSITIVE_RULES = {
        'doi_found': ScoringRule(
            pattern=r'10\.\d{4,9}/[-._;()/:\w]+',
            score=50,
            description='DOI pattern found',
            is_regex=True
        ),
        'abstract_section': ScoringRule(
            pattern='abstract',
            score=20,
            description='Abstract section found'
        ),
        'references_section': ScoringRule(
            pattern='references',
            score=20,
            description='References section found'
        ),
        'introduction_section': ScoringRule(
            pattern='introduction',
            score=15,
            description='Introduction section found'
        ),
        'conclusion_section': ScoringRule(
            pattern='conclusion',
            score=10,
            description='Conclusion section found'
        ),
        'methodology_section': ScoringRule(
            pattern='methodology',
            score=10,
            description='Methodology section found'
        ),
    }
    
    DEFAULT_NEGATIVE_RULES = {
        'invoice_pattern': ScoringRule(
            pattern='invoice',
            score=-100,
            description='Invoice pattern in filename'
        ),
        'receipt_pattern': ScoringRule(
            pattern='receipt',
            score=-100,
            description='Receipt pattern in filename'
        ),
        'presentation_pattern': ScoringRule(
            pattern='presentation',
            score=-50,
            description='Presentation pattern in filename'
        ),
        'slides_pattern': ScoringRule(
            pattern='slides',
            score=-50,
            description='Slides pattern in filename'
        ),
        'manual_pattern': ScoringRule(
            pattern='manual',
            score=-70,
            description='Manual pattern in filename'
        ),
        'brochure_pattern': ScoringRule(
            pattern='brochure',
            score=-70,
            description='Brochure pattern in filename'
        ),
    }
    
    # Academic publishers
    ACADEMIC_PUBLISHERS = [
        'elsevier', 'springer', 'wiley', 'nature', 'science',
        'ieee', 'acm', 'taylor & francis', 'sage', 'oxford',
        'cambridge', 'plos', 'frontiers', 'mdpi', 'arxiv',
        'latex', 'pdflatex', 'xelatex', 'lualatex'
    ]
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize PDF filter.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        filter_config = config.get('pdf_filter', {})
        
        # Basic settings
        self.enabled = filter_config.get('enabled', True)
        self.academic_only = filter_config.get('academic_only', False)
        self.academic_threshold = filter_config.get('academic_threshold', 50)
        self.min_pages = filter_config.get('min_pages', 5)
        self.max_pages = filter_config.get('max_pages', 500)
        
        # File size limits (in MB)
        self.min_size_mb = filter_config.get('min_size_mb', 0.1)
        self.max_size_mb = filter_config.get('max_size_mb', 100)
        
        # Load custom scoring rules
        self.positive_rules = self._load_scoring_rules(
            config.get('scoring_rules', {}).get('positive', {}),
            self.DEFAULT_POSITIVE_RULES
        )
        self.negative_rules = self._load_scoring_rules(
            config.get('scoring_rules', {}).get('negative', {}),
            self.DEFAULT_NEGATIVE_RULES
        )
    
    def filter_pdf(self, pdf_path: Path) -> FilterResult:
        """
        Filter a PDF file using funnel approach.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            FilterResult with acceptance decision and details
        """
        if not self.enabled:
            return FilterResult(
                accepted=True,
                score=0,
                reasons=['Filtering disabled'],
                details={}
            )
        
        score = 0
        reasons = []
        details = {}
        
        # Level 1: Filename check (fastest)
        filename_score, filename_reasons = self._check_filename(pdf_path)
        score += filename_score
        reasons.extend(filename_reasons)
        details['filename_score'] = filename_score
        
        # Early rejection for very negative filename scores
        if filename_score <= -100:
            return FilterResult(
                accepted=False,
                score=score,
                reasons=reasons,
                details=details
            )
        
        # Level 2: File size check (fast)
        size_score, size_reasons = self._check_file_size(pdf_path)
        score += size_score
        reasons.extend(size_reasons)
        details['size_score'] = size_score
        
        # Early rejection for invalid file sizes
        if size_score <= -50:
            return FilterResult(
                accepted=False,
                score=score,
                reasons=reasons,
                details=details
            )
        
        try:
            # Level 3: PDF metadata check (medium speed)
            metadata_score, metadata_reasons = self._check_metadata(pdf_path)
            score += metadata_score
            reasons.extend(metadata_reasons)
            details['metadata_score'] = metadata_score
            
            # Level 4: Quick content scan (slower)
            content_score, content_reasons = self._quick_content_scan(pdf_path)
            score += content_score
            reasons.extend(content_reasons)
            details['content_score'] = content_score
            
        except Exception as e:
            logger.warning(f"Error analyzing PDF {pdf_path}: {e}")
            reasons.append(f"Analysis error: {str(e)}")
            details['error'] = str(e)
        
        # Final decision
        details['total_score'] = score
        accepted = not self.academic_only or score >= self.academic_threshold
        
        if not accepted:
            reasons.insert(0, f"Score {score} below threshold {self.academic_threshold}")
        else:
            reasons.insert(0, f"Score {score} meets threshold {self.academic_threshold}")
        
        return FilterResult(
            accepted=accepted,
            score=score,
            reasons=reasons,
            details=details
        )
    
    def _check_filename(self, pdf_path: Path) -> Tuple[float, List[str]]:
        """Check filename against patterns."""
        score = 0
        reasons = []
        filename_lower = pdf_path.name.lower()
        
        # Check negative patterns
        for rule_name, rule in self.negative_rules.items():
            if rule.pattern in filename_lower:
                score += rule.score
                reasons.append(f"Filename: {rule.description}")
        
        # Check positive patterns
        for keyword in ['paper', 'article', 'journal', 'conference', 'proceedings']:
            if keyword in filename_lower:
                score += 5
                reasons.append(f"Filename: Contains '{keyword}'")
        
        # Check for year patterns (common in academic papers)
        if re.search(r'(19|20)\d{2}', pdf_path.name):
            score += 5
            reasons.append("Filename: Contains year pattern")
        
        return score, reasons
    
    def _check_file_size(self, pdf_path: Path) -> Tuple[float, List[str]]:
        """Check file size."""
        score = 0
        reasons = []
        
        try:
            size_mb = pdf_path.stat().st_size / (1024 * 1024)
            
            if size_mb < self.min_size_mb:
                score -= 50
                reasons.append(f"File too small: {size_mb:.1f}MB < {self.min_size_mb}MB")
            elif size_mb > self.max_size_mb:
                score -= 30
                reasons.append(f"File too large: {size_mb:.1f}MB > {self.max_size_mb}MB")
            else:
                # Optimal size range for academic papers (0.5-10MB)
                if 0.5 <= size_mb <= 10:
                    score += 10
                    reasons.append(f"File size optimal: {size_mb:.1f}MB")
                else:
                    reasons.append(f"File size: {size_mb:.1f}MB")
                    
        except Exception as e:
            logger.warning(f"Error checking file size: {e}")
            reasons.append("Could not check file size")
        
        return score, reasons
    
    def _check_metadata(self, pdf_path: Path) -> Tuple[float, List[str]]:
        """Check PDF metadata."""
        score = 0
        reasons = []
        
        try:
            with fitz.open(pdf_path) as doc:
                metadata = doc.metadata
                
                # Check page count
                page_count = len(doc)
                if page_count < self.min_pages:
                    score -= 30
                    reasons.append(f"Too few pages: {page_count} < {self.min_pages}")
                elif page_count > self.max_pages:
                    score -= 20
                    reasons.append(f"Too many pages: {page_count} > {self.max_pages}")
                else:
                    # Typical academic paper range (8-40 pages)
                    if 8 <= page_count <= 40:
                        score += 15
                        reasons.append(f"Page count typical: {page_count}")
                    else:
                        score += 5
                        reasons.append(f"Page count: {page_count}")
                
                # Check producer/creator for academic tools
                producer = (metadata.get('producer', '') or '').lower()
                creator = (metadata.get('creator', '') or '').lower()
                
                for tool in self.ACADEMIC_PUBLISHERS:
                    if tool in producer or tool in creator:
                        score += 20
                        reasons.append(f"Academic tool detected: {tool}")
                        break
                
                # Check for title
                if metadata.get('title'):
                    score += 5
                    reasons.append("Has metadata title")
                
                # Check for author
                if metadata.get('author'):
                    score += 5
                    reasons.append("Has metadata author")
                    
        except Exception as e:
            logger.warning(f"Error checking metadata: {e}")
            reasons.append("Could not check metadata")
        
        return score, reasons
    
    def _quick_content_scan(self, pdf_path: Path) -> Tuple[float, List[str]]:
        """Quick scan of first and last few pages."""
        score = 0
        reasons = []
        
        try:
            with fitz.open(pdf_path) as doc:
                # Scan first 3 pages and last 2 pages
                pages_to_scan = []
                if len(doc) > 0:
                    pages_to_scan.extend(range(min(3, len(doc))))
                if len(doc) > 5:
                    pages_to_scan.extend(range(len(doc) - 2, len(doc)))
                
                text_sample = ""
                for page_num in pages_to_scan:
                    try:
                        page = doc[page_num]
                        text_sample += page.get_text().lower() + "\n"
                    except:
                        continue
                
                # Check positive patterns
                for rule_name, rule in self.positive_rules.items():
                    if rule.is_regex:
                        if re.search(rule.pattern, text_sample, re.IGNORECASE):
                            score += rule.score
                            reasons.append(f"Content: {rule.description}")
                    else:
                        if rule.pattern in text_sample:
                            score += rule.score
                            reasons.append(f"Content: {rule.description}")
                
                # Check for academic keywords
                academic_keywords = [
                    'abstract', 'introduction', 'methodology', 'results',
                    'discussion', 'conclusion', 'references', 'bibliography',
                    'keywords', 'corresponding author', 'doi:', 'issn',
                    'received:', 'accepted:', 'published:'
                ]
                
                found_keywords = []
                for keyword in academic_keywords:
                    if keyword in text_sample:
                        found_keywords.append(keyword)
                
                if len(found_keywords) >= 3:
                    score += 10 * len(found_keywords)
                    reasons.append(f"Multiple academic keywords: {', '.join(found_keywords[:5])}")
                    
        except Exception as e:
            logger.warning(f"Error scanning content: {e}")
            reasons.append("Could not scan content")
        
        return score, reasons
    
    def _load_scoring_rules(self, custom_rules: Dict[str, Any], 
                           default_rules: Dict[str, ScoringRule]) -> Dict[str, ScoringRule]:
        """Load and merge custom scoring rules with defaults."""
        rules = default_rules.copy()
        
        for rule_name, rule_config in custom_rules.items():
            if isinstance(rule_config, (int, float)):
                # Simple score override
                if rule_name in rules:
                    rules[rule_name].score = float(rule_config)
            elif isinstance(rule_config, dict):
                # Full rule definition
                rules[rule_name] = ScoringRule(
                    pattern=rule_config.get('pattern', ''),
                    score=float(rule_config.get('score', 0)),
                    description=rule_config.get('description', rule_name),
                    is_regex=rule_config.get('is_regex', False)
                )
        
        return rules