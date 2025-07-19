"""
Tests for PDF filtering functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.pdf_filter import PDFFilter, FilterResult, ScoringRule


class TestPDFFilter:
    """Test cases for PDFFilter class."""
    
    @pytest.fixture
    def config(self):
        """Sample configuration for testing."""
        return {
            'pdf_filter': {
                'enabled': True,
                'academic_only': True,
                'academic_threshold': 50,
                'min_pages': 5,
                'max_pages': 500,
                'min_size_mb': 0.1,
                'max_size_mb': 100,
            },
            'scoring_rules': {
                'positive': {
                    'doi_found': 50,
                    'abstract_found': 20,
                    'references_found': 20,
                },
                'negative': {
                    'invoice_in_filename': -100,
                    'presentation_in_filename': -50,
                }
            }
        }
    
    @pytest.fixture
    def pdf_filter(self, config):
        """Create PDFFilter instance."""
        return PDFFilter(config)
    
    def test_filter_disabled(self):
        """Test that filtering returns accepted when disabled."""
        config = {'pdf_filter': {'enabled': False}}
        filter = PDFFilter(config)
        
        result = filter.filter_pdf(Path('test.pdf'))
        
        assert result.accepted is True
        assert result.score == 0
        assert 'Filtering disabled' in result.reasons
    
    def test_filename_negative_patterns(self, pdf_filter):
        """Test negative filename patterns."""
        # Test invoice pattern
        result = pdf_filter._check_filename(Path('invoice_2024.pdf'))
        score, reasons = result
        
        assert score == -100
        assert any('Invoice pattern' in r for r in reasons)
        
        # Test presentation pattern
        result = pdf_filter._check_filename(Path('presentation_slides.pdf'))
        score, reasons = result
        
        assert score == -50
        assert any('Presentation pattern' in r for r in reasons)
    
    def test_filename_positive_patterns(self, pdf_filter):
        """Test positive filename patterns."""
        # Test academic keywords
        result = pdf_filter._check_filename(Path('research_paper_2024.pdf'))
        score, reasons = result
        
        assert score > 0
        assert any('paper' in r.lower() for r in reasons)
        assert any('year pattern' in r for r in reasons)
    
    def test_file_size_check(self, pdf_filter):
        """Test file size checking."""
        # Mock file size
        pdf_path = Mock(spec=Path)
        
        # Test too small
        pdf_path.stat.return_value.st_size = 50 * 1024  # 50KB
        score, reasons = pdf_filter._check_file_size(pdf_path)
        assert score == -50
        assert any('too small' in r.lower() for r in reasons)
        
        # Test optimal size
        pdf_path.stat.return_value.st_size = 2 * 1024 * 1024  # 2MB
        score, reasons = pdf_filter._check_file_size(pdf_path)
        assert score == 10
        assert any('optimal' in r.lower() for r in reasons)
        
        # Test too large
        pdf_path.stat.return_value.st_size = 200 * 1024 * 1024  # 200MB
        score, reasons = pdf_filter._check_file_size(pdf_path)
        assert score == -30
        assert any('too large' in r.lower() for r in reasons)
    
    @patch('src.pdf_filter.fitz.open')
    def test_metadata_check(self, mock_fitz_open, pdf_filter):
        """Test PDF metadata checking."""
        # Mock PDF document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 25  # 25 pages
        mock_doc.metadata = {
            'producer': 'LaTeX with hyperref',
            'creator': 'pdfTeX',
            'title': 'Research Paper',
            'author': 'John Doe'
        }
        mock_fitz_open.return_value.__enter__.return_value = mock_doc
        
        score, reasons = pdf_filter._check_metadata(Path('test.pdf'))
        
        assert score > 0
        assert any('typical' in r.lower() for r in reasons)
        assert any('latex' in r.lower() for r in reasons)
        assert any('title' in r.lower() for r in reasons)
        assert any('author' in r.lower() for r in reasons)
    
    @patch('src.pdf_filter.fitz.open')
    def test_content_scan(self, mock_fitz_open, pdf_filter):
        """Test content scanning."""
        # Mock PDF document with academic content
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 10
        
        # Mock pages with academic content
        mock_page = MagicMock()
        mock_page.get_text.return_value = """
        Abstract
        This paper presents a novel approach to machine learning.
        
        Introduction
        Machine learning has become increasingly important...
        
        References
        [1] Smith et al. (2023). Deep Learning. Nature.
        DOI: 10.1038/s41586-023-12345-6
        """
        
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz_open.return_value.__enter__.return_value = mock_doc
        
        score, reasons = pdf_filter._quick_content_scan(Path('test.pdf'))
        
        assert score > 0
        assert any('Abstract' in r for r in reasons)
        assert any('References' in r for r in reasons)
        assert any('DOI' in r for r in reasons)
    
    @patch('src.pdf_filter.fitz.open')
    def test_full_filter_academic_paper(self, mock_fitz_open, pdf_filter):
        """Test full filtering of an academic paper."""
        # Mock file stats
        pdf_path = Mock(spec=Path)
        pdf_path.name = 'deep_learning_survey_2024.pdf'
        pdf_path.stat.return_value.st_size = 3 * 1024 * 1024  # 3MB
        
        # Mock PDF document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 28
        mock_doc.metadata = {
            'producer': 'LaTeX',
            'title': 'Deep Learning Survey'
        }
        
        # Mock academic content
        mock_page = MagicMock()
        mock_page.get_text.return_value = """
        Abstract
        This survey reviews recent advances in deep learning...
        
        References
        DOI: 10.1109/TPAMI.2024.123456
        """
        
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz_open.return_value.__enter__.return_value = mock_doc
        
        result = pdf_filter.filter_pdf(pdf_path)
        
        assert result.accepted is True
        assert result.score >= 50
        assert 'meets threshold' in result.reasons[0]
    
    @patch('src.pdf_filter.fitz.open')
    def test_full_filter_non_academic(self, mock_fitz_open, pdf_filter):
        """Test full filtering of a non-academic PDF."""
        # Mock file stats
        pdf_path = Mock(spec=Path)
        pdf_path.name = 'invoice_2024_001.pdf'
        pdf_path.stat.return_value.st_size = 200 * 1024  # 200KB
        
        result = pdf_filter.filter_pdf(pdf_path)
        
        # Should be rejected based on filename alone
        assert result.accepted is False
        assert result.score < 0
        assert 'Invoice pattern' in str(result.reasons)
    
    def test_custom_scoring_rules(self):
        """Test custom scoring rules."""
        config = {
            'pdf_filter': {'enabled': True},
            'scoring_rules': {
                'positive': {
                    'custom_keyword': {
                        'pattern': 'blockchain',
                        'score': 30,
                        'description': 'Blockchain keyword found'
                    }
                },
                'negative': {
                    'report_pattern': -80
                }
            }
        }
        
        filter = PDFFilter(config)
        
        # Check that custom rules are loaded
        assert 'custom_keyword' in filter.positive_rules
        assert filter.positive_rules['custom_keyword'].score == 30
        assert 'report_pattern' in filter.negative_rules
        assert filter.negative_rules['report_pattern'].score == -80