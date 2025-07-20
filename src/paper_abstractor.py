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
from google import genai
from google.genai import types

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
        
        # Initialize Gemini client
        self.client = genai.Client(api_key=self.api_key)
        
        # Model settings - check both api and ai sections for compatibility
        self.model_name = (config.get('ai', {}).get('model') or 
                          config.get('api', {}).get('model', 'gemini-2.0-flash-001'))
        self.max_tokens = (config.get('ai', {}).get('max_tokens') or 
                          config.get('api', {}).get('max_tokens', 2048))
        
        # Abstractor settings
        self.language = config.get('abstractor', {}).get('language', 'en')
        self.max_length = config.get('abstractor', {}).get('max_length', 1000)
        self.include_citations = config.get('abstractor', {}).get('include_citations', True)
        self.include_figures = config.get('abstractor', {}).get('include_figures', True)
        self.extract_keywords = config.get('abstractor', {}).get('extract_keywords', True)
        
        # Visual extraction settings
        self.enable_visual_extraction = config.get('abstractor', {}).get('enable_visual_extraction', False)
        self.max_image_pages = config.get('abstractor', {}).get('max_image_pages', 3)
        self.image_dpi = config.get('abstractor', {}).get('image_dpi', 150)
        
        # Rate limiting
        self.rate_limit = config.get('rate_limit', {})
        self.requests_per_minute = self.rate_limit.get('requests_per_minute', 60)
        self.request_delay = self.rate_limit.get('request_delay', 1)
        self.retry_attempts = config.get('advanced', {}).get('retry_attempts', 3)
        
        # Load prompt templates
        self.prompt_templates = self._load_prompt_templates()
        
        # Request tracking for rate limiting
        self._request_times: List[float] = []
    
    
    def _load_prompt_templates(self) -> Dict[str, str]:
        """Load prompt templates from files."""
        templates = {}
        prompt_dir = Path(__file__).parent.parent / 'config' / 'prompts'
        
        # Load the unified prompt template
        template_file = prompt_dir / 'academic_abstract.txt'
        if template_file.exists():
            template_content = template_file.read_text(encoding='utf-8')
            # Use the same template for all languages/modes
            templates['markdown_ja'] = template_content
            templates['ja'] = template_content
            templates['en'] = template_content
        else:
            # Fallback to default templates if file doesn't exist
            templates['markdown_ja'] = self._get_default_japanese_prompt()
            templates['ja'] = self._get_default_japanese_prompt()
            templates['en'] = self._get_default_english_prompt()
        
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
        
        # Extract page images if visual extraction is enabled
        page_images = None
        if self.enable_visual_extraction and pdf_data.get('pdf_path'):
            try:
                from .pdf_extractor import PDFExtractor
                extractor = PDFExtractor(self.config)
                page_images = extractor.extract_page_images(
                    Path(pdf_data['pdf_path']),
                    dpi=self.image_dpi
                )
                logger.info(f"Extracted {len(page_images)} page images for visual processing")
            except Exception as e:
                logger.warning(f"Failed to extract page images: {e}")
                # Continue without images
        
        # Check if we should use markdown template
        use_markdown = 'markdown_ja' in self.prompt_templates and self.language == 'ja'
        
        # Generate abstract with retries
        for attempt in range(self.retry_attempts):
            try:
                if use_markdown:
                    abstract_data = await self._generate_markdown_with_gemini(input_text, pdf_data, page_images)
                else:
                    abstract_data = await self._generate_with_gemini(input_text, pdf_data, page_images)
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
        max_chars = 60000  # Approximately 15000 tokens
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
    
    async def _generate_with_gemini(self, input_text: str, pdf_data: Dict[str, Any], 
                                    page_images: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Generate abstract using Gemini API."""
        # Get appropriate prompt template
        prompt_template = self.prompt_templates.get(self.language, self.prompt_templates['en'])
        
        # Format the prompt
        prompt = prompt_template.format(
            pdf_text=input_text,
            max_length=self.max_length,
            language="日本語" if self.language == 'ja' else "English",
        )
        
        # Create generation config
        generation_config = types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=self.max_tokens,
        )
        
        # Build contents for multimodal request
        contents = self._build_multimodal_contents(prompt, page_images)
        
        # Generate response using new SDK
        def _generate_sync():
            return self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=generation_config
            )
        
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            _generate_sync
        )
        
        # Parse the response
        abstract_text = response.text
        
        # Debug: Log the raw response
        if self.config.get('advanced', {}).get('log_level') == 'DEBUG':
            logger.debug(f"Raw Gemini response:\n{abstract_text}")
            
            # Also save to file for inspection
            debug_dir = Path("debug_output")
            debug_dir.mkdir(exist_ok=True)
            debug_file = debug_dir / f"gemini_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(f"Prompt used:\n{prompt}\n\n")
                f.write(f"Response:\n{abstract_text}")
            logger.debug(f"Gemini output saved to: {debug_file}")
        
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
        section_content = []
        in_target_section = False
        section_level = 0
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check if this is a section header
            is_header = False
            current_level = 0
            
            # Determine header level
            if line_stripped.startswith('#####'):
                current_level = 5
            elif line_stripped.startswith('####'):
                current_level = 4
            elif line_stripped.startswith('###'):
                current_level = 3
            elif line_stripped.startswith('##'):
                current_level = 2
            elif line_stripped.startswith('#'):
                current_level = 1
            
            # Check if this line matches our target section
            for name in section_names:
                if (line_stripped.startswith(f"{'#' * current_level} {name}") or 
                    line_stripped.startswith(f"{'#' * current_level}{name}") or
                    line_stripped.startswith(f"**{name}") or
                    line_stripped.startswith(f"{name}:") or
                    (line_stripped == name and current_level > 0)):
                    is_header = True
                    in_target_section = True
                    section_level = current_level
                    # Extract any content after the header on the same line
                    content_after_header = line_stripped.split(name, 1)
                    if len(content_after_header) > 1:
                        content = content_after_header[1].strip().lstrip(':*').strip()
                        if content:
                            section_content.append(content)
                    break
            
            if is_header:
                # If we found our target section, we already handled it above
                if not in_target_section:
                    continue
            elif in_target_section:
                # Check if we've reached another section at the same or higher level
                if current_level > 0 and current_level <= section_level:
                    # Check if this is a different section (not our target)
                    if not any(name in line_stripped for name in section_names):
                        break
                
                # Add content if we're in the target section
                if line_stripped:
                    # Clean up formatting
                    content = line_stripped
                    # Remove bullet points if they're at the start
                    if content.startswith(('- ', '* ', '• ')):
                        content = content[2:].strip()
                    elif content.startswith(('1. ', '2. ', '3. ', '4. ', '5. ')):
                        content = content[3:].strip()
                    
                    if content:
                        section_content.append(content)
        
        result = ' '.join(section_content).strip()
        
        # Post-process to clean up common formatting issues
        result = result.replace('**', '').replace('*', '')
        result = ' '.join(result.split())  # Normalize whitespace
        
        return result
    
    async def _generate_markdown_with_gemini(self, input_text: str, pdf_data: Dict[str, Any],
                                            page_images: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Generate complete markdown using Gemini API."""
        # Get markdown prompt template
        prompt_template = self.prompt_templates.get('markdown_ja')
        
        # Extract metadata
        metadata = pdf_data.get('metadata', {})
        title = metadata.get('title', 'Untitled')
        authors = metadata.get('author', 'Unknown')
        year = metadata.get('year', datetime.now().year)
        page_count = pdf_data.get('page_count', 0)
        file_size_mb = pdf_data.get('file_size_mb', 0)
        pdf_filename = pdf_data.get('pdf_path', 'unknown.pdf')
        if isinstance(pdf_filename, Path):
            pdf_filename = pdf_filename.name
        
        # Format the prompt
        prompt = prompt_template.format(
            pdf_text=input_text,
            max_length=self.max_length,
            title=title,
            authors=authors,
            year=year,
            pdf_filename=pdf_filename,
            current_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # Create generation config
        generation_config = types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=self.max_tokens,
        )
        
        # Build contents for multimodal request
        contents = self._build_multimodal_contents(prompt, page_images)
        
        # Generate response using new SDK
        def _generate_sync():
            return self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=generation_config
            )
        
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            _generate_sync
        )
        
        # Get the markdown response
        markdown_text = response.text
        
        # Remove markdown code block wrapper if present
        if markdown_text.startswith('```markdown'):
            markdown_text = markdown_text[11:]  # Remove ```markdown
            if markdown_text.endswith('```'):
                markdown_text = markdown_text[:-3]  # Remove closing ```
        elif markdown_text.startswith('```'):
            markdown_text = markdown_text[3:]  # Remove opening ```
            if markdown_text.endswith('```'):
                markdown_text = markdown_text[:-3]  # Remove closing ```
        
        # Strip any leading/trailing whitespace
        markdown_text = markdown_text.strip()
        
        # Debug: Log the raw response
        if self.config.get('advanced', {}).get('log_level') == 'DEBUG':
            logger.debug(f"Raw Gemini markdown response length: {len(markdown_text)} chars")
            
            # Also save to file for inspection
            debug_dir = Path("debug_output")
            debug_dir.mkdir(exist_ok=True)
            debug_file = debug_dir / f"gemini_markdown_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(markdown_text)
            logger.debug(f"Gemini markdown output saved to: {debug_file}")
        
        # Return the complete markdown as the main content
        abstract_data = {
            'markdown_content': markdown_text,
            'abstract_language': self.language,
            'model_used': self.model_name,
            'generation_date': datetime.now().isoformat(),
            'use_markdown_format': True
        }
        logger.debug(f"Final abstract_data to be returned: {abstract_data}")
        return abstract_data
    
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
        
        # Find all experiment sections
        experiment_sections = []
        current_exp_lines = []
        experiment_number = None
        in_experiment_section = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check for experiment headers (more robust patterns)
            exp_patterns = [
                r'実験\s*(\d+)',
                r'Experiment\s*(\d+)',
                r'### 実験\s*(\d+)',
                r'## 実験\s*(\d+)',
                r'A-2.*実験\s*(\d+)',
            ]
            
            found_exp = False
            for pattern in exp_patterns:
                import re
                match = re.search(pattern, line_stripped)
                if match:
                    # Save previous experiment if exists
                    if in_experiment_section and current_exp_lines and experiment_number:
                        experiment_sections.append({
                            'number': experiment_number,
                            'lines': current_exp_lines.copy()
                        })
                    
                    # Start new experiment
                    experiment_number = match.group(1)
                    current_exp_lines = [line]
                    in_experiment_section = True
                    found_exp = True
                    break
            
            if not found_exp:
                # Check if we've hit a major section that ends experiments
                if line_stripped.startswith('## ') and any(section in line_stripped for section in [
                    '総合考察', '結論', 'General Discussion', 'Discussion', 'Conclusion'
                ]):
                    if in_experiment_section and current_exp_lines and experiment_number:
                        experiment_sections.append({
                            'number': experiment_number,
                            'lines': current_exp_lines.copy()
                        })
                    in_experiment_section = False
                elif in_experiment_section:
                    current_exp_lines.append(line)
        
        # Save last experiment if exists
        if in_experiment_section and current_exp_lines and experiment_number:
            experiment_sections.append({
                'number': experiment_number,
                'lines': current_exp_lines.copy()
            })
        
        # Parse each experiment section
        for exp_section in experiment_sections:
            exp_text = '\n'.join(exp_section['lines'])
            experiment = {
                'number': exp_section['number'],
                'objectives': self._extract_experiment_field(exp_text, ['目的と仮説', 'Objectives', 'Hypothesis']),
                'participants': self._extract_experiment_field(exp_text, ['実験参加者', 'Participants', '参加者']),
                'tasks': self._extract_experiment_field(exp_text, ['課題と刺激', 'Tasks', 'Stimuli', '課題']),
                'procedure': self._extract_experiment_field(exp_text, ['手続き', 'Procedure', 'プロシージャ']),
                'analysis': self._extract_experiment_field(exp_text, ['分析方法', 'Analysis', 'Statistical Analysis', '統計分析']),
                'results': self._extract_experiment_field(exp_text, ['結果と小括', 'Results', '結果'])
            }
            
            # Remove empty experiments
            if any(experiment[key].strip() for key in experiment.keys() if key != 'number'):
                experiments.append(experiment)
        
        return experiments
    
    def _extract_experiment_field(self, exp_text: str, field_names: List[str]) -> str:
        """Extract a specific field from experiment text."""
        lines = exp_text.split('\n')
        field_content = []
        in_field = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check if this line is a field header
            is_field_header = False
            for field_name in field_names:
                if (field_name in line_stripped and 
                    ('**' in line_stripped or ':' in line_stripped or line_stripped.startswith('* '))):
                    is_field_header = True
                    in_field = True
                    # Extract content after the field name
                    content_part = line_stripped.split(field_name, 1)
                    if len(content_part) > 1:
                        content = content_part[1].strip().lstrip('*:').strip()
                        if content:
                            field_content.append(content)
                    break
            
            if not is_field_header and in_field:
                # Check if we've hit another field or major section
                if (('**' in line_stripped and any(other_field in line_stripped for other_field in [
                    '目的', '参加者', '課題', '手続き', '分析', '結果', 'Objectives', 'Participants', 'Tasks', 'Procedure', 'Analysis', 'Results'
                ])) or line_stripped.startswith('### ') or line_stripped.startswith('## ')):
                    break
                elif line_stripped:
                    field_content.append(line_stripped)
        
        return ' '.join(field_content).strip()
    
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
    
    def _build_multimodal_contents(self, prompt: str, 
                                 page_images: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Build contents array for multimodal Gemini request.
        
        Args:
            prompt: Text prompt
            page_images: Optional list of page images
            
        Returns:
            Contents array formatted for Gemini API
        """
        contents = []
        
        # Add text prompt
        text_parts = [{"text": prompt}]
        
        # Add images if available
        if page_images:
            image_parts = []
            total_size_kb = 0
            
            for img in page_images[:self.max_image_pages]:  # Limit number of images
                total_size_kb += img.get('file_size_kb', 0)
                
                # Check total size limit (12MB)
                if total_size_kb > 12 * 1024:
                    logger.warning(f"Total image size exceeds 12MB, stopping at page {img['page_number']}")
                    break
                
                image_parts.append({
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": img['image_data']
                    }
                })
                
                # Add page reference text
                text_parts.append({
                    "text": f"\n[Page {img['page_number']} image above]\n"
                })
            
            if image_parts:
                logger.info(f"Added {len(image_parts)} images to multimodal request")
                # Combine text and images
                all_parts = text_parts[:1]  # Initial prompt
                for i, img_part in enumerate(image_parts):
                    all_parts.append(img_part)
                    if i + 1 < len(text_parts):
                        all_parts.append(text_parts[i + 1])  # Page reference
                
                contents.append({
                    "role": "user",
                    "parts": all_parts
                })
            else:
                # Text only
                contents.append({
                    "role": "user", 
                    "parts": text_parts
                })
        else:
            # Text only (for SDK v1.26.0 format)
            contents = prompt
        
        return contents