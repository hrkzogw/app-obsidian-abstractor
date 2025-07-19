"""
PDF monitoring module for Obsidian Abstractor.

This module provides functionality to monitor folders for new PDF files
and process them automatically using watchdog.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import json
import aiofiles
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from .pdf_extractor import PDFExtractor
from .paper_abstractor import PaperAbstractor
from .note_formatter import NoteFormatter
from .pdf_filter import PDFFilter
from .utils.path_resolver import PathResolver, create_resolver

logger = logging.getLogger(__name__)


class PDFEventHandler(FileSystemEventHandler):
    """Handle file system events for PDF files."""
    
    def __init__(self, monitor: 'PDFMonitor'):
        """
        Initialize event handler.
        
        Args:
            monitor: PDFMonitor instance
        """
        self.monitor = monitor
        self.patterns = monitor.patterns
        self.ignore_patterns = monitor.ignore_patterns
    
    def on_created(self, event: FileCreatedEvent):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        path = Path(event.src_path)
        
        # Check if file matches patterns
        if not self._matches_patterns(path):
            return
        
        # Check if file should be ignored
        if self._matches_ignore_patterns(path):
            return
        
        logger.info(f"New PDF detected: {path}")
        
        # Add to processing queue
        asyncio.create_task(self.monitor.add_to_queue(path))
    
    def _matches_patterns(self, path: Path) -> bool:
        """Check if file matches watch patterns."""
        return any(path.match(pattern) for pattern in self.patterns)
    
    def _matches_ignore_patterns(self, path: Path) -> bool:
        """Check if file matches ignore patterns."""
        return any(path.match(pattern) for pattern in self.ignore_patterns)


class PDFMonitor:
    """Monitor folders for new PDF files and process them."""
    
    def __init__(self, config: Dict[str, Any], output_path: str):
        """
        Initialize PDF monitor.
        
        Args:
            config: Configuration dictionary
            output_path: Output path (can be vault-relative or absolute)
        """
        self.config = config
        self.path_resolver = create_resolver(config)
        
        # Resolve output path with placeholders
        self.output_path_template = output_path
        self.output_path = self.path_resolver.resolve_with_placeholders(output_path)
        
        # Watch settings
        watch_config = config.get('watch', {})
        
        # Resolve watch folders
        folder_paths = watch_config.get('folders', [])
        self.folders = []
        for folder_str in folder_paths:
            try:
                resolved_folder = self.path_resolver.resolve_path(folder_str)
                self.folders.append(resolved_folder)
                logger.info(f"Resolved watch folder: {folder_str} -> {resolved_folder}")
            except Exception as e:
                logger.warning(f"Failed to resolve folder '{folder_str}': {e}")
        
        self.patterns = watch_config.get('patterns', ['*.pdf', '*.PDF'])
        self.ignore_patterns = watch_config.get('ignore_patterns', ['*draft*', '*tmp*', '.*'])
        
        # Processing settings
        self.batch_size = config.get('rate_limit', {}).get('batch_size', 5)
        self.workers = config.get('advanced', {}).get('workers', 2)
        
        # Cache settings
        self.use_cache = config.get('advanced', {}).get('pdf_cache', True)
        self.cache_dir = Path(config.get('advanced', {}).get('cache_dir', '~/.cache/obsidian-abstractor')).expanduser()
        if self.use_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.cache_file = self.cache_dir / 'processed_files.json'
        
        # Initialize components
        self.pdf_extractor = PDFExtractor(config)
        self.paper_abstractor = PaperAbstractor(config)
        self.note_formatter = NoteFormatter(config)
        self.pdf_filter = PDFFilter(config)
        
        # Processing queue and state
        self.processing_queue: asyncio.Queue = asyncio.Queue()
        self.processed_files: Set[str] = self._load_processed_files()
        self.is_running = False
        self.observer: Optional[Observer] = None
        self.workers_tasks: List[asyncio.Task] = []
    
    async def start(self, daemon: bool = False):
        """
        Start monitoring folders.
        
        Args:
            daemon: Run as daemon in background
        """
        logger.info(f"Starting PDF monitor for folders: {self.folders}")
        
        try:
            # Validate folders
            for folder in self.folders:
                if not folder.exists():
                    logger.warning(f"Folder does not exist: {folder}")
                    folder.mkdir(parents=True, exist_ok=True)
            
            # Ensure output directory exists
            self.output_path.mkdir(parents=True, exist_ok=True)
            
            self.is_running = True
            
            # Start file system observer
            self.observer = Observer()
            handler = PDFEventHandler(self)
            
            for folder in self.folders:
                self.observer.schedule(handler, str(folder), recursive=True)
            
            self.observer.start()
            logger.info("File system observer started")
            
            # Start worker tasks
            for i in range(self.workers):
                task = asyncio.create_task(self._process_queue_worker(i))
                self.workers_tasks.append(task)
            
            logger.info(f"Started {self.workers} worker tasks")
            
            # Initial scan
            await self._initial_scan()
            
            if daemon:
                # Daemon mode: continuous monitoring
                logger.info("Monitor started in daemon mode")
                try:
                    while self.is_running:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal")
            else:
                # Non-daemon mode: process initial scan files only
                logger.info("Monitor started in non-daemon mode")
                
                # Record initial file count
                initial_file_count = self.processing_queue.qsize()
                
                if initial_file_count > 0:
                    logger.info(f"Processing {initial_file_count} files from initial scan...")
                    try:
                        # Wait for all items to be processed with timeout
                        await asyncio.wait_for(
                            self.processing_queue.join(),
                            timeout=1800.0  # 30 minutes timeout
                        )
                        logger.info("All files processed successfully")
                    except asyncio.TimeoutError:
                        logger.error("Processing timed out after 30 minutes")
                        raise
                else:
                    logger.info("No files found in initial scan")
        
        except KeyboardInterrupt:
            logger.info("Interrupt signal received, shutting down...")
        except Exception as e:
            logger.error(f"Error during monitoring: {e}", exc_info=True)
            raise
        finally:
            # Safe shutdown
            if self.is_running:
                await self.stop()
            logger.info("Monitor has been shut down")
    
    async def stop(self):
        """Stop monitoring."""
        logger.info("Stopping PDF monitor...")
        
        self.is_running = False
        
        # Stop observer
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        # Cancel worker tasks
        for task in self.workers_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.workers_tasks, return_exceptions=True)
        
        # Save processed files cache
        self._save_processed_files()
        
        logger.info("PDF monitor stopped")
    
    async def add_to_queue(self, pdf_path: Path):
        """Add a PDF file to the processing queue."""
        # Check if already processed
        if self.use_cache and str(pdf_path) in self.processed_files:
            logger.debug(f"Skipping already processed file: {pdf_path}")
            return
        
        # Wait a bit for file to be fully written
        await asyncio.sleep(2)
        
        # Check if file is readable
        if not pdf_path.exists() or not pdf_path.is_file():
            logger.warning(f"File not found or not readable: {pdf_path}")
            return
        
        await self.processing_queue.put(pdf_path)
        logger.info(f"Added to queue: {pdf_path}")
    
    async def process_file(self, pdf_path: Path, force: bool = False) -> Optional[Path]:
        """
        Process a single PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            force: Force processing even if filtered out
            
        Returns:
            Path to the generated note, or None if processing failed
        """
        try:
            # Apply PDF filter unless forced
            if not force and self.pdf_filter.enabled:
                filter_result = self.pdf_filter.filter_pdf(pdf_path)
                
                if not filter_result.accepted:
                    logger.info(f"Filtered out: {pdf_path}")
                    for reason in filter_result.reasons:
                        logger.info(f"  - {reason}")
                    logger.info(f"  Total score: {filter_result.score}")
                    
                    # Handle quarantine if enabled
                    if self.config.get('pdf_filter', {}).get('quarantine_enabled', False):
                        quarantine_folder = self.config.get('pdf_filter', {}).get('quarantine_folder')
                        if quarantine_folder:
                            await self._quarantine_file(pdf_path, Path(quarantine_folder).expanduser(), filter_result)
                    
                    return None
                else:
                    logger.info(f"Accepted: {pdf_path} (score: {filter_result.score})")
            
            logger.info(f"Processing: {pdf_path}")
            
            # Extract PDF data
            pdf_data = self.pdf_extractor.extract(pdf_path)
            
            # Generate abstract
            abstract_data = await self.paper_abstractor.generate_abstract(pdf_data)
            
            # Format note
            note_content = self.note_formatter.format_note(pdf_data, abstract_data, pdf_path)
            
            # Generate filename
            filename = self.note_formatter.generate_filename(pdf_data, pdf_path)
            
            # Resolve output path with current date and PDF metadata
            context = {
                'author': pdf_data.get('metadata', {}).get('author', 'Unknown').split(',')[0].strip(),
                'paper_year': pdf_data.get('metadata', {}).get('year', 'Unknown'),
                'title': pdf_data.get('metadata', {}).get('title', pdf_path.stem)[:30],
            }
            current_output_path = self.path_resolver.resolve_with_placeholders(
                self.output_path_template, context
            )
            
            # Ensure output directory exists
            current_output_path.mkdir(parents=True, exist_ok=True)
            
            note_path = current_output_path / f"{filename}.md"
            
            # Ensure unique filename
            counter = 1
            while note_path.exists():
                note_path = self.output_path / f"{filename}_{counter}.md"
                counter += 1
            
            # Write note
            async with aiofiles.open(note_path, 'w', encoding='utf-8') as f:
                await f.write(note_content)
            
            logger.info(f"Created note: {note_path}")
            
            # Mark as processed
            if self.use_cache:
                self.processed_files.add(str(pdf_path))
                self._save_processed_files()
            
            return note_path
            
        except Exception as e:
            logger.error(f"Failed to process {pdf_path}: {e}", exc_info=True)
            return None
    
    async def _quarantine_file(self, pdf_path: Path, quarantine_folder: Path, filter_result):
        """Move filtered file to quarantine folder."""
        try:
            quarantine_folder.mkdir(parents=True, exist_ok=True)
            
            # Create info file with filter details
            info_path = quarantine_folder / f"{pdf_path.stem}_filter_info.txt"
            info_content = f"File: {pdf_path.name}\n"
            info_content += f"Filtered at: {datetime.now().isoformat()}\n"
            info_content += f"Score: {filter_result.score}\n"
            info_content += f"Threshold: {self.pdf_filter.academic_threshold}\n"
            info_content += "\nReasons:\n"
            for reason in filter_result.reasons:
                info_content += f"  - {reason}\n"
            
            async with aiofiles.open(info_path, 'w', encoding='utf-8') as f:
                await f.write(info_content)
            
            logger.info(f"Quarantine info saved: {info_path}")
            
        except Exception as e:
            logger.warning(f"Failed to quarantine {pdf_path}: {e}")
    
    async def _process_queue_worker(self, worker_id: int):
        """Worker task to process PDFs from the queue."""
        logger.info(f"Worker {worker_id} started")
        
        while self.is_running:
            try:
                # Get item from queue with timeout
                pdf_path = await asyncio.wait_for(
                    self.processing_queue.get(),
                    timeout=1.0
                )
                
                logger.info(f"Worker {worker_id} processing: {pdf_path}")
                try:
                    await self.process_file(pdf_path)
                finally:
                    # Notify queue that task is done
                    self.processing_queue.task_done()
                    
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
                # Mark task as done even on error
                self.processing_queue.task_done()
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def _initial_scan(self):
        """Perform initial scan of folders for existing PDFs."""
        logger.info("Performing initial scan...")
        
        pdf_files = []
        for folder in self.folders:
            if not folder.exists():
                continue
            
            for pattern in self.patterns:
                pdf_files.extend(folder.rglob(pattern))
        
        # Filter out ignored patterns
        pdf_files = [
            f for f in pdf_files
            if not any(f.match(p) for p in self.ignore_patterns)
        ]
        
        # Filter out already processed files
        if self.use_cache:
            pdf_files = [
                f for f in pdf_files
                if str(f) not in self.processed_files
            ]
        
        logger.info(f"Found {len(pdf_files)} unprocessed PDF files")
        
        # Add to queue
        for pdf_file in pdf_files:
            await self.add_to_queue(pdf_file)
    
    def _load_processed_files(self) -> Set[str]:
        """Load processed files cache."""
        if not self.use_cache:
            return set()
        
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('processed_files', []))
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        
        return set()
    
    def _save_processed_files(self):
        """Save processed files cache."""
        if not self.use_cache:
            return
        
        try:
            data = {
                'processed_files': list(self.processed_files),
                'last_updated': datetime.now().isoformat(),
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    async def batch_process(self, folder: Path, recursive: bool = False) -> List[Path]:
        """
        Batch process all PDFs in a folder.
        
        Args:
            folder: Folder to process
            recursive: Process subfolders recursively
            
        Returns:
            List of generated note paths
        """
        logger.info(f"Batch processing folder: {folder}")
        
        # Find PDF files
        pdf_files = []
        for pattern in self.patterns:
            if recursive:
                pdf_files.extend(folder.rglob(pattern))
            else:
                pdf_files.extend(folder.glob(pattern))
        
        # Filter out ignored patterns
        pdf_files = [
            f for f in pdf_files
            if not any(f.match(p) for p in self.ignore_patterns)
        ]
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Process in batches
        results = []
        for i in range(0, len(pdf_files), self.batch_size):
            batch = pdf_files[i:i + self.batch_size]
            
            logger.info(f"Processing batch {i // self.batch_size + 1} ({len(batch)} files)")
            
            # Process batch concurrently
            tasks = [self.process_file(pdf) for pdf in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for pdf, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to process {pdf}: {result}")
                elif result:
                    results.append(result)
        
        logger.info(f"Batch processing complete. Generated {len(results)} notes")
        return results