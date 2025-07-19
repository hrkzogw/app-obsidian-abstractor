"""
AI-powered paper abstraction module for Obsidian Abstractor.

This module provides functionality to generate comprehensive abstracts
from academic papers using Google Gemini AI.
"""

import asyncio
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
import json
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

logger = logging.getLogger(__name__)


class PaperAbstractor:
    """Generate AI-powered abstracts from academic papers."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the paper abstractor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.api_key = config.get('api', {}).get('google_ai_key', '')
        if not self.api_key:
            raise ValueError("Google AI API key not configured")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Model settings
        self.model_name = config.get('api', {}).get('model', 'gemini-pro')
        self.max_tokens = config.get('api', {}).get('max_tokens', 2048)
        
        # Abstractor settings
        self.language = config.get('abstractor', {}).get('language', 'en')
        self.max_length = config.get('abstractor', {}).get('max_length', 1000)
        self.include_citations = config.get('abstractor', {}).get('include_citations', True)
        self.include_figures = config.get('abstractor', {}).get('include_figures', True)
        self.extract_keywords = config.get('abstractor', {}).get('extract_keywords', True)
        
        # Rate limiting
        self.rate_limit = config.get('rate_limit', {})
        self.requests_per_minute = self.rate_limit.get('requests_per_minute', 60)
        self.request_delay = self.rate_limit.get('request_delay', 1)
        self.retry_attempts = config.get('advanced', {}).get('retry_attempts', 3)
        
        # Initialize model
        self._init_model()
        
        # Load prompt templates
        self.prompt_templates = self._load_prompt_templates()
        
        # Request tracking for rate limiting
        self._request_times: List[float] = []
    
    def _init_model(self):
        """Initialize the Gemini model."""
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": self.max_tokens,
        }
        
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=generation_config,
            safety_settings=safety_settings,
        )
    
    def _load_prompt_templates(self) -> Dict[str, str]:
        """Load prompt templates from files."""
        templates = {}
        prompt_dir = Path(__file__).parent.parent / 'config' / 'prompts'
        
        # Default templates if files don't exist
        default_templates = {
            'ja': self._get_default_japanese_prompt(),
            'en': self._get_default_english_prompt(),
        }
        
        for lang in ['ja', 'en']:
            template_file = prompt_dir / f'academic_abstract_{lang}.txt'
            if template_file.exists():
                templates[lang] = template_file.read_text(encoding='utf-8')
            else:
                templates[lang] = default_templates[lang]
        
        return templates
    
    async def generate_abstract(self, pdf_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an abstract from extracted PDF data.
        
        Args:
            pdf_data: Dictionary containing extracted PDF data
            
        Returns:
            Dictionary containing the generated abstract and metadata
        """
        # Rate limiting
        await self._apply_rate_limit()
        
        # Prepare input data
        input_text = self._prepare_input_text(pdf_data)
        
        # Generate abstract with retries
        for attempt in range(self.retry_attempts):
            try:
                abstract_data = await self._generate_with_gemini(input_text, pdf_data)
                return abstract_data
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.request_delay * (attempt + 1))
                else:
                    raise RuntimeError(f"Failed to generate abstract after {self.retry_attempts} attempts: {e}")
    
    def _prepare_input_text(self, pdf_data: Dict[str, Any]) -> str:
        """Prepare input text for the AI model."""
        parts = []
        
        # Add metadata if available
        metadata = pdf_data.get('metadata', {})
        if metadata.get('title'):
            parts.append(f"Title: {metadata['title']}")
        if metadata.get('author'):
            parts.append(f"Authors: {metadata['author']}")
        if metadata.get('year'):
            parts.append(f"Year: {metadata['year']}")
        
        parts.append("")  # Empty line
        
        # Add main text
        text = pdf_data.get('text', '')
        # Limit text length to avoid token limits
        max_chars = 30000  # Approximately 7500 tokens
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[Text truncated due to length...]"
        parts.append(text)
        
        # Add figures if configured
        if self.include_figures and pdf_data.get('figures'):
            parts.append("\n\nFigures and Tables:")
            for fig in pdf_data['figures'][:10]:  # Limit to 10 figures
                parts.append(f"- {fig['type'].capitalize()} {fig['number']}: {fig['caption']}")
        
        # Add references sample if configured
        if self.include_citations and pdf_data.get('references'):
            parts.append("\n\nSample References:")
            for ref in pdf_data['references'][:5]:  # Show first 5 references
                parts.append(f"- {ref}")
        
        return "\n".join(parts)
    
    async def _generate_with_gemini(self, input_text: str, pdf_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate abstract using Gemini API."""
        # Get appropriate prompt template
        prompt_template = self.prompt_templates.get(self.language, self.prompt_templates['en'])
        
        # Format the prompt
        prompt = prompt_template.format(
            pdf_text=input_text,
            max_length=self.max_length,
            language="日本語" if self.language == 'ja' else "English",
        )
        
        # Generate response
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            self.model.generate_content,
            prompt
        )
        
        # Parse the response
        abstract_text = response.text
        
        # Check if it's an experimental or review paper
        is_experimental = '実験論文' in abstract_text or 'Experimental Paper' in abstract_text
        is_review = 'レビュー論文' in abstract_text or 'Review Paper' in abstract_text
        
        # Structure the output based on paper type
        if is_experimental:
            # Extract experimental paper sections
            result = {
                'paper_type': 'experimental',
                'summary': self._extract_section(abstract_text, ['論文全体の背景と目的', 'A-1', '研究の背景']),
                'background': self._extract_section(abstract_text, ['研究の背景']),
                'prior_research': self._extract_section(abstract_text, ['先行研究と問題点']),
                'objectives': self._extract_section(abstract_text, ['本研究の目的と仮説']),
                'experiments': self._extract_experiment_details(abstract_text),
                'discussion': self._extract_section(abstract_text, ['総合考察と結論', 'General Discussion', 'A-3', '結果の統合']),
                'contributions': self._extract_section(abstract_text, ['学術的貢献']),
                'limitations': self._extract_section(abstract_text, ['研究の限界と今後の展望', '限界', 'Limitations']),
                'keywords': [],
                'abstract_language': self.language,
                'model_used': self.model_name,
                'generation_date': datetime.now().isoformat(),
            }
        elif is_review:
            # Extract review paper sections
            result = {
                'paper_type': 'review',
                'summary': self._extract_section(abstract_text, ['レビューの主題と目的', 'B-1', 'レビューの主題']),
                'review_theme': self._extract_section(abstract_text, ['レビューの主題']),
                'review_necessity': self._extract_section(abstract_text, ['レビューの必要性']),
                'main_theories': self._extract_section(abstract_text, ['主要な理論・モデル']),
                'discussion_classification': self._extract_section(abstract_text, ['議論の分類']),
                'landmark_studies': self._extract_section(abstract_text, ['画期的な研究']),
                'consensus': self._extract_section(abstract_text, ['コンセンサス', '学術的コンセンサス']),
                'controversies': self._extract_section(abstract_text, ['論争点']),
                'conclusions': self._extract_section(abstract_text, ['結論と総括', '著者らの結論']),
                'future_directions': self._extract_section(abstract_text, ['今後の課題', 'Future Directions']),
                'keywords': [],
                'abstract_language': self.language,
                'model_used': self.model_name,
                'generation_date': datetime.now().isoformat(),
            }
        else:
            # Fallback to original structure if paper type is not detected
            result = {
                'paper_type': 'unknown',
                'summary': self._extract_section(abstract_text, ['要約', 'Summary', '概要', '論文全体の背景と目的', 'レビューの主題と目的']),
                'key_contributions': self._extract_list_section(abstract_text, ['主要な貢献', 'Key Contributions', '主要貢献', '学術的貢献']),
                'methodology': self._extract_section(abstract_text, ['手法', 'Methodology', '方法', '実験手法']),
                'results': self._extract_section(abstract_text, ['結果', 'Results', '実験結果', '結果と小括']),
                'insights': self._extract_section(abstract_text, ['洞察', 'Insights', '考察', '総合考察']),
                'limitations': self._extract_section(abstract_text, ['限界', 'Limitations', '制限事項', '研究の限界']),
                'future_work': self._extract_section(abstract_text, ['今後の研究', 'Future Work', '将来の研究', '今後の展望']),
                'keywords': [],
                'abstract_language': self.language,
                'model_used': self.model_name,
                'generation_date': datetime.now().isoformat(),
            }
        
        # Extract keywords if configured
        if self.extract_keywords:
            result['keywords'] = self._extract_keywords(abstract_text, pdf_data)
        
        return result
    
    def _extract_section(self, text: str, section_names: List[str]) -> str:
        """Extract a specific section from the generated text."""
        lines = text.split('\n')
        current_section = None
        section_content = []
        
        for line in lines:
            line = line.strip()
            
            # Check if this is a section header
            is_header = False
            for name in section_names:
                if (line.startswith(f"## {name}") or 
                    line.startswith(f"# {name}") or 
                    line.startswith(f"### {name}") or
                    line.startswith(f"#### {name}") or
                    line.startswith(f"##### {name}") or
                    line.startswith(f"{name}:") or
                    line == name):
                    is_header = True
                    current_section = name
                    break
            
            if is_header:
                continue
            
            # Check if we've reached another section
            if current_section and line.startswith(('#', '##', '###', '####', '#####')) and not any(name in line for name in section_names):
                break
            
            # Add content if we're in the target section
            if current_section and line:
                section_content.append(line)
        
        return '\n'.join(section_content).strip()
    
    def _extract_list_section(self, text: str, section_names: List[str]) -> List[str]:
        """Extract a list section from the generated text."""
        content = self._extract_section(text, section_names)
        if not content:
            return []
        
        items = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith(('- ', '* ', '1.', '2.', '3.', '・')):
                # Remove bullet point or number
                item = line.lstrip('- *・').lstrip('0123456789.')
                items.append(item.strip())
        
        return items
    
    def _extract_experiment_details(self, text: str) -> List[Dict[str, Any]]:
        """Extract details of individual experiments from the text."""
        experiments = []
        lines = text.split('\n')
        current_experiment = None
        current_section = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Check for experiment headers
            if any(pattern in line for pattern in ['実験 ', 'Experiment ', 'A-2']):
                # Save previous experiment if exists
                if current_experiment:
                    experiments.append(current_experiment)
                
                # Start new experiment
                current_experiment = {
                    'number': self._extract_experiment_number(line),
                    'objectives': '',
                    'participants': '',
                    'tasks': '',
                    'procedure': '',
                    'analysis': '',
                    'results': '',
                }
                current_section = 'objectives'
            
            elif current_experiment:
                # Detect section changes
                if '実験参加者' in line or 'Participants' in line:
                    current_section = 'participants'
                elif '課題と刺激' in line or 'Tasks' in line:
                    current_section = 'tasks'
                elif '手続き' in line or 'Procedure' in line:
                    current_section = 'procedure'
                elif '分析方法' in line or 'Analysis' in line:
                    current_section = 'analysis'
                elif '結果と小括' in line or 'Results' in line:
                    current_section = 'results'
                elif line.startswith('#'):
                    # New major section, save current experiment
                    if current_experiment:
                        experiments.append(current_experiment)
                        current_experiment = None
                else:
                    # Add content to current section
                    if current_section and line:
                        current_experiment[current_section] += line + '\n'
        
        # Save last experiment
        if current_experiment:
            experiments.append(current_experiment)
        
        # Clean up experiment data
        for exp in experiments:
            for key in exp:
                if isinstance(exp[key], str):
                    exp[key] = exp[key].strip()
        
        return experiments
    
    def _extract_experiment_number(self, line: str) -> str:
        """Extract experiment number from line."""
        import re
        match = re.search(r'実験\s*(\d+)|Experiment\s*(\d+)', line)
        if match:
            return match.group(1) or match.group(2)
        return '1'
    
    def _extract_keywords(self, abstract_text: str, pdf_data: Dict[str, Any]) -> List[str]:
        """Extract keywords from the abstract and original metadata."""
        keywords = []
        
        # Get keywords from metadata
        metadata_keywords = pdf_data.get('metadata', {}).get('keywords', '')
        if metadata_keywords:
            keywords.extend([k.strip() for k in metadata_keywords.split(',')])
        
        # Look for keywords section in abstract
        keyword_section = self._extract_section(abstract_text, ['キーワード', 'Keywords', 'タグ'])
        if keyword_section:
            # Extract comma-separated or line-separated keywords
            if ',' in keyword_section:
                keywords.extend([k.strip() for k in keyword_section.split(',')])
            else:
                keywords.extend([k.strip() for k in keyword_section.split('\n') if k.strip()])
        
        # Remove duplicates and clean
        keywords = list(set(k.lower().replace('#', '') for k in keywords if k))
        
        # Add default tags
        keywords.extend(['research-paper', 'academic'])
        if self.language == 'ja':
            keywords.append('japanese')
        
        return sorted(list(set(keywords)))[:15]  # Limit to 15 keywords
    
    async def _apply_rate_limit(self):
        """Apply rate limiting to API requests."""
        current_time = time.time()
        
        # Remove old request times (older than 1 minute)
        self._request_times = [t for t in self._request_times if current_time - t < 60]
        
        # Check if we need to wait
        if len(self._request_times) >= self.requests_per_minute:
            oldest_request = self._request_times[0]
            wait_time = 60 - (current_time - oldest_request) + 0.1
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
        
        # Add current request time
        self._request_times.append(current_time)
        
        # Apply minimum delay between requests
        await asyncio.sleep(self.request_delay)
    
    def _get_default_japanese_prompt(self) -> str:
        """Get default Japanese prompt template."""
        return """以下の学術論文を分析し、構造化された要約を日本語で作成してください。

# 要約に含める内容：
1. 研究の背景と動機
2. 解決しようとする問題
3. 提案手法の概要
4. 実験設定と評価方法
5. 主要な結果と発見
6. 研究の貢献と限界
7. 今後の展望

# 形式：
- 各セクションは見出しを付ける（## を使用）
- 重要なポイントは箇条書き（- を使用）
- 技術用語には簡潔な説明を追加
- 定量的な結果は具体的な数値で示す
- 最大{max_length}文字以内

# 追加指示：
- 専門用語は日本語と英語を併記
- 図表への参照がある場合は言及
- キーワードをリストアップ

論文テキスト：
{pdf_text}"""
    
    def _get_default_english_prompt(self) -> str:
        """Get default English prompt template."""
        return """Analyze the following academic paper and create a structured abstract in English.

# Content to include:
1. Research background and motivation
2. Problem being addressed
3. Proposed methodology overview
4. Experimental setup and evaluation methods
5. Key results and findings
6. Research contributions and limitations
7. Future directions

# Format:
- Use headings for each section (use ##)
- Important points as bullet lists (use -)
- Add brief explanations for technical terms
- Show quantitative results with specific numbers
- Maximum {max_length} characters

# Additional instructions:
- List relevant keywords
- Mention references to figures/tables if present
- Focus on clarity and conciseness

Paper text:
{pdf_text}"""