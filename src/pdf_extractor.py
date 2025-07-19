"""
PDF extraction module for Obsidian Abstractor.

This module provides functionality to extract text, metadata, and structure
from academic PDF files using PyMuPDF (fitz).
"""

import re
import logging
import base64
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extract text, metadata, and structure from PDF files."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize PDF extractor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.max_size_mb = self.config.get('pdf', {}).get('max_size_mb', 100)
        self.extraction_mode = self.config.get('pdf', {}).get('extraction_mode', 'auto')
        self.handle_encrypted = self.config.get('pdf', {}).get('handle_encrypted', False)
    
    def extract(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Extract all information from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted text, metadata, and structure
            
        Raises:
            ValueError: If PDF is encrypted and handle_encrypted is False
            RuntimeError: If PDF extraction fails
        """
        # Check file size
        file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_size_mb:
            raise ValueError(f"PDF file too large: {file_size_mb:.1f}MB (max: {self.max_size_mb}MB)")
        
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            raise RuntimeError(f"Failed to open PDF: {e}")
        
        # Check if encrypted
        if doc.is_encrypted:
            if not self.handle_encrypted:
                doc.close()
                raise ValueError("PDF is encrypted and handle_encrypted is False")
            # Try to decrypt with empty password
            if not doc.authenticate(""):
                doc.close()
                raise ValueError("PDF is encrypted and cannot be opened without password")
        
        try:
            result = {
                'text': self.extract_text(doc),
                'metadata': self.extract_metadata(doc, pdf_path),
                'structure': self.extract_structure(doc),
                'figures': self.extract_figures(doc),
                'references': self.extract_references(doc),
                'page_count': len(doc),
                'file_size_mb': round(file_size_mb, 2),
                'extraction_date': datetime.now().isoformat(),
                'pdf_path': str(pdf_path),  # Store path for image extraction
            }
        finally:
            doc.close()
        
        return result
    
    def extract_text(self, doc: fitz.Document) -> str:
        """
        Extract text from all pages of the PDF.
        
        Args:
            doc: PyMuPDF document object
            
        Returns:
            Extracted text as a single string
        """
        text_parts = []
        
        for page_num, page in enumerate(doc):
            try:
                # Extract text with layout preservation if in auto mode
                if self.extraction_mode == 'layout':
                    text = page.get_text("text", flags=fitz.TEXTFLAGS_DICT)
                else:
                    text = page.get_text()
                
                if text.strip():
                    text_parts.append(f"[Page {page_num + 1}]\n{text}")
                    
            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                continue
        
        return "\n\n".join(text_parts)
    
    def extract_metadata(self, doc: fitz.Document, pdf_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from the PDF.
        
        Args:
            doc: PyMuPDF document object
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing metadata
        """
        metadata = doc.metadata or {}
        
        # Clean and normalize metadata
        cleaned_metadata = {
            'filename': pdf_path.name,
            'title': self._clean_string(metadata.get('title', '')),
            'author': self._clean_string(metadata.get('author', '')),
            'subject': self._clean_string(metadata.get('subject', '')),
            'keywords': self._clean_string(metadata.get('keywords', '')),
            'creator': self._clean_string(metadata.get('creator', '')),
            'producer': self._clean_string(metadata.get('producer', '')),
            'creation_date': self._parse_date(metadata.get('creationDate', '')),
            'modification_date': self._parse_date(metadata.get('modDate', '')),
        }
        
        # Try to extract additional metadata from the first page
        if not cleaned_metadata['title'] or not cleaned_metadata['author']:
            first_page_meta = self._extract_first_page_metadata(doc)
            if not cleaned_metadata['title'] and first_page_meta.get('title'):
                cleaned_metadata['title'] = first_page_meta['title']
            if not cleaned_metadata['author'] and first_page_meta.get('authors'):
                cleaned_metadata['author'] = ', '.join(first_page_meta['authors'])
        
        # Extract year from creation date or text
        if cleaned_metadata['creation_date']:
            cleaned_metadata['year'] = cleaned_metadata['creation_date'][:4]
        else:
            year_match = re.search(r'\b(19|20)\d{2}\b', str(doc.get_page_text(0)))
            if year_match:
                cleaned_metadata['year'] = year_match.group(0)
        
        return cleaned_metadata
    
    def extract_structure(self, doc: fitz.Document) -> List[Dict[str, Any]]:
        """
        Extract document structure (sections, subsections).
        
        Args:
            doc: PyMuPDF document object
            
        Returns:
            List of section dictionaries
        """
        structure = []
        toc = doc.get_toc()  # Table of contents
        
        if toc:
            for level, title, page in toc:
                structure.append({
                    'level': level,
                    'title': title,
                    'page': page,
                })
        else:
            # Try to extract structure from text patterns
            structure = self._extract_structure_from_text(doc)
        
        return structure
    
    def extract_figures(self, doc: fitz.Document) -> List[Dict[str, Any]]:
        """
        Extract figure and table captions.
        
        Args:
            doc: PyMuPDF document object
            
        Returns:
            List of figure/table information
        """
        figures = []
        
        # Common patterns for figure and table captions
        caption_patterns = [
            r'Fig(?:ure)?\.?\s*(\d+)[:\.]?\s*([^\n]+)',
            r'Table\s*(\d+)[:\.]?\s*([^\n]+)',
            r'図\s*(\d+)[:\.]?\s*([^\n]+)',  # Japanese
            r'表\s*(\d+)[:\.]?\s*([^\n]+)',  # Japanese
        ]
        
        for page_num, page in enumerate(doc):
            try:
                text = page.get_text()
                
                for pattern in caption_patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        fig_type = 'figure' if 'fig' in pattern.lower() or '図' in pattern else 'table'
                        figures.append({
                            'type': fig_type,
                            'number': match.group(1),
                            'caption': match.group(2).strip(),
                            'page': page_num + 1,
                        })
            except Exception as e:
                logger.warning(f"Failed to extract figures from page {page_num + 1}: {e}")
        
        return figures
    
    def extract_references(self, doc: fitz.Document) -> List[str]:
        """
        Extract references/bibliography section.
        
        Args:
            doc: PyMuPDF document object
            
        Returns:
            List of reference strings
        """
        references = []
        ref_section_found = False
        
        # Look for references section
        ref_patterns = [
            r'References\s*$',
            r'Bibliography\s*$',
            r'参考文献\s*$',  # Japanese
            r'引用文献\s*$',  # Japanese
        ]
        
        for page_num in range(len(doc) - 1, max(0, len(doc) - 10), -1):
            page = doc[page_num]
            text = page.get_text()
            
            if not ref_section_found:
                for pattern in ref_patterns:
                    if re.search(pattern, text, re.MULTILINE | re.IGNORECASE):
                        ref_section_found = True
                        break
            
            if ref_section_found:
                # Extract individual references (basic pattern)
                ref_lines = text.split('\n')
                current_ref = []
                
                for line in ref_lines:
                    line = line.strip()
                    if re.match(r'^\[\d+\]', line) or re.match(r'^\d+\.', line):
                        if current_ref:
                            references.append(' '.join(current_ref))
                        current_ref = [line]
                    elif line and current_ref:
                        current_ref.append(line)
                
                if current_ref:
                    references.append(' '.join(current_ref))
        
        return references[::-1]  # Reverse to get correct order
    
    def _extract_first_page_metadata(self, doc: fitz.Document) -> Dict[str, Any]:
        """Extract metadata from the first page text."""
        if len(doc) == 0:
            return {}
        
        first_page_text = doc[0].get_text()
        lines = first_page_text.split('\n')
        
        metadata = {}
        
        # Try to find title (usually the largest text on first page)
        # Simple heuristic: longest line in first 20 lines
        title_candidates = [line.strip() for line in lines[:20] if len(line.strip()) > 10]
        if title_candidates:
            metadata['title'] = max(title_candidates, key=len)
        
        # Try to find authors (often after title, before abstract)
        authors = []
        author_section = False
        for i, line in enumerate(lines[:50]):
            line = line.strip()
            
            # Check for author patterns
            if re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+', line):
                authors.append(line)
                author_section = True
            elif author_section and (line.lower().startswith('abstract') or len(line) > 100):
                break
        
        if authors:
            metadata['authors'] = authors
        
        return metadata
    
    def _extract_structure_from_text(self, doc: fitz.Document) -> List[Dict[str, Any]]:
        """Extract structure from text patterns when TOC is not available."""
        structure = []
        
        section_patterns = [
            (1, r'^\d+\.?\s+[A-Z][A-Za-z\s]+$'),  # 1. Introduction
            (2, r'^\d+\.\d+\.?\s+[A-Z][A-Za-z\s]+$'),  # 1.1 Subsection
            (1, r'^[IVX]+\.?\s+[A-Z][A-Za-z\s]+$'),  # I. Introduction
            (1, r'^(Abstract|Introduction|Methods?|Results?|Discussion|Conclusion|References)$'),
        ]
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                for level, pattern in section_patterns:
                    if re.match(pattern, line, re.IGNORECASE):
                        structure.append({
                            'level': level,
                            'title': line,
                            'page': page_num + 1,
                        })
                        break
        
        return structure
    
    def _clean_string(self, s: str) -> str:
        """Clean and normalize string."""
        if not s:
            return ''
        # Remove extra whitespace and control characters
        s = re.sub(r'\s+', ' ', s)
        s = ''.join(c for c in s if c.isprintable() or c.isspace())
        return s.strip()
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse PDF date string to ISO format."""
        if not date_str:
            return None
        
        # PDF date format: D:YYYYMMDDHHmmSSOHH'mm'
        match = re.match(r'D:(\d{4})(\d{2})(\d{2})', date_str)
        if match:
            year, month, day = match.groups()
            return f"{year}-{month}-{day}"
        
        return None
    
    def extract_page_images(self, pdf_path: Path, page_numbers: Optional[List[int]] = None, 
                          dpi: int = 150) -> List[Dict[str, Any]]:
        """
        Extract specified pages as images from PDF (memory-safe implementation).
        
        Args:
            pdf_path: Path to the PDF file
            page_numbers: List of page numbers to extract (0-indexed). If None, selects optimal pages
            dpi: DPI for image extraction (default 150)
            
        Returns:
            List of dictionaries containing page images and metadata
        """
        doc = None
        try:
            doc = fitz.open(pdf_path)
            images = []
            
            # If no page numbers specified, select optimal pages
            if page_numbers is None:
                page_numbers = self._select_optimal_pages(doc)
            
            for page_num in page_numbers:
                if page_num >= len(doc):
                    logger.warning(f"Page {page_num} exceeds document length {len(doc)}")
                    continue
                
                image_data = self._extract_single_page_image(doc, page_num, dpi)
                if image_data:
                    images.append(image_data)
            
            logger.info(f"Extracted {len(images)} page images from PDF")
            return images
            
        except Exception as e:
            logger.error(f"Failed to extract page images: {e}")
            return []
        finally:
            if doc:
                doc.close()
    
    def _extract_single_page_image(self, doc: fitz.Document, page_num: int, 
                                  dpi: int) -> Optional[Dict[str, Any]]:
        """
        Extract a single page as image with size limit handling.
        
        Args:
            doc: PyMuPDF document object
            page_num: Page number (0-indexed)
            dpi: DPI for image extraction
            
        Returns:
            Dictionary with image data or None if failed
        """
        try:
            page = doc[page_num]
            
            # Calculate zoom factor from DPI (PDF default is 72 DPI)
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            
            # First attempt with requested DPI
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img_data = pix.tobytes("png")
            
            # Check size limit (4MB)
            max_size = 4 * 1024 * 1024
            if len(img_data) > max_size:
                logger.warning(f"Page {page_num + 1} image too large ({len(img_data) // 1024}KB), reducing DPI")
                
                # Retry with lower DPI
                reduced_dpi = int(dpi * 0.7)
                zoom = reduced_dpi / 72.0
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img_data = pix.tobytes("png")
                
                # If still too large, reduce further
                if len(img_data) > max_size:
                    reduced_dpi = int(dpi * 0.5)
                    zoom = reduced_dpi / 72.0
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    img_data = pix.tobytes("png")
            
            return {
                'page_number': page_num + 1,
                'image_data': base64.b64encode(img_data).decode('utf-8'),
                'file_size_kb': len(img_data) // 1024,
                'dpi': dpi,
                'width': pix.width,
                'height': pix.height,
            }
            
        except Exception as e:
            logger.warning(f"Failed to extract image from page {page_num + 1}: {e}")
            return None
    
    def _select_optimal_pages(self, doc: fitz.Document, max_pages: int = 5) -> List[int]:
        """
        Select optimal pages for visual extraction.
        
        Args:
            doc: PyMuPDF document object
            max_pages: Maximum number of pages to select
            
        Returns:
            List of page numbers (0-indexed)
        """
        selected_pages = set()
        
        # Always include title/abstract page
        selected_pages.add(0)
        
        # Find figure/table pages
        figure_pages = self._detect_figure_pages_intelligent(doc)
        # Add up to 3 figure pages
        for page_num, score in figure_pages[:3]:
            selected_pages.add(page_num)
        
        # Add conclusion/results pages (last few pages)
        if len(doc) > 3:
            selected_pages.add(len(doc) - 1)  # Last page
            if len(doc) > 4:
                selected_pages.add(len(doc) - 2)  # Second to last
        
        # Add methodology page (typically in the middle third)
        if len(doc) > 6:
            method_page = len(doc) // 3
            selected_pages.add(method_page)
        
        # Convert to sorted list and limit to max_pages
        return sorted(list(selected_pages))[:max_pages]
    
    def _detect_figure_pages_intelligent(self, doc: fitz.Document) -> List[Tuple[int, int]]:
        """
        Intelligently detect pages containing figures and tables.
        
        Args:
            doc: PyMuPDF document object
            
        Returns:
            List of (page_number, score) tuples sorted by score
        """
        figure_pages = []
        
        # Keywords indicating figures/tables with weights
        indicators = {
            'figure': 3,
            'table': 3,
            'fig.': 3,
            'tab.': 3,
            '図': 3,
            '表': 3,
            'graph': 2,
            'chart': 2,
            'plot': 2,
            'diagram': 2,
            'グラフ': 2,
            'experiment': 1,
            '実験': 1,
            'result': 1,
            '結果': 1,
        }
        
        for page_num in range(len(doc)):
            try:
                page = doc[page_num]
                text = page.get_text().lower()
                
                # Calculate score based on indicators
                score = 0
                for indicator, weight in indicators.items():
                    count = text.count(indicator)
                    score += count * weight
                
                # Bonus for pages with less text (likely to have figures)
                text_density = len(text.strip()) / (page.rect.width * page.rect.height)
                if text_density < 0.5:  # Low text density
                    score += 2
                
                if score >= 2:  # Threshold for considering as figure page
                    figure_pages.append((page_num, score))
                    
            except Exception as e:
                logger.warning(f"Error analyzing page {page_num}: {e}")
                continue
        
        # Sort by score (descending)
        figure_pages.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"Detected {len(figure_pages)} figure pages")
        return figure_pages