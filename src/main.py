#!/usr/bin/env python3
"""
Obsidian Abstractor - Main entry point.

AI-powered academic paper summarizer for Obsidian.
"""

import sys
import asyncio
import logging
import click
import uuid
import yaml
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from .config_loader import ConfigLoader
from .pdf_monitor import PDFMonitor
from .pdf_extractor import PDFExtractor
from .paper_abstractor import PaperAbstractor
from .note_formatter import NoteFormatter
from .pdf_filter import PDFFilter
from .utils.path_resolver import PathResolver, create_resolver
from .utils.note_utils import extract_yaml_frontmatter, generate_filename_from_yaml, handle_rename
from .paperpile_sync import sync_paperpile

console = Console()


def setup_logging(verbose: bool):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create logs directory
    log_dir = Path("./logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create file handler with date-based filename
    log_filename = f"abstractor_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(
        log_dir / log_filename,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    # File formatter with more detail
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler with rich formatting
    console_handler = RichHandler(console=console, rich_tracebacks=True)
    console_handler.setLevel(level)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,  # Set root to DEBUG, handlers control their own levels
        format="%(message)s",
        datefmt="[%X]",
        handlers=[console_handler, file_handler]
    )
    
    # Reduce noise from some libraries
    logging.getLogger("watchdog").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Obsidian Abstractor - AI-powered academic paper summarizer."""
    pass


@cli.command()
@click.argument('folders', nargs=-1, type=click.Path(exists=False), required=False)
@click.option('--output', '-o', type=click.Path(exists=False), required=False, help='Output folder in Obsidian vault')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--daemon', '-d', is_flag=True, help='Run as daemon in background')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--show-config', is_flag=True, help='Show current configuration and exit')
def watch(folders, output, config, daemon, verbose, show_config):
    """Watch folders for new PDF files and process them."""
    setup_logging(verbose)
    
    # Load configuration
    try:
        config_loader = ConfigLoader(config)
        console.print("[green]✓[/green] Configuration loaded")
    except Exception as e:
        console.print(f"[red]Failed to load configuration: {e}[/red]")
        sys.exit(1)
    
    # Create path resolver
    resolver = create_resolver(config_loader.config)
    
    # Determine folders to watch
    watch_folders = []
    if folders:
        # Use command-line folders
        watch_folders = list(folders)
    else:
        # 新しい場所から読み込む（後方互換性なし）
        folder_settings = config_loader.config.get('folder_settings', {})
        config_folders = folder_settings.get('watch_folders', [])
        
        if not config_folders:
            console.print("[red]監視フォルダが設定されていません。[/red]")
            console.print("[yellow]config.yamlの'folder_settings.watch_folders'を設定するか、")
            console.print("コマンドラインでフォルダを指定してください。[/yellow]")
            sys.exit(1)
        watch_folders = config_folders
    
    # Determine output path
    output_path = None
    if output:
        # Use command-line output
        output_path = output
    else:
        # 新しい場所から読み込む（後方互換性なし）
        folder_settings = config_loader.config.get('folder_settings', {})
        output_path = folder_settings.get('watch_output') or folder_settings.get('default_output')
        
        if not output_path:
            console.print("[red]出力先が設定されていません。[/red]")
            console.print("[yellow]config.yamlの'folder_settings.default_output'を設定してください。[/yellow]")
            sys.exit(1)
    
    # Show configuration and exit if requested
    if show_config:
        console.print("\n[bold cyan]Current Configuration:[/bold cyan]")
        console.print("=" * 50)
        
        # Vault path
        folder_settings = config_loader.config.get('folder_settings', {})
        vault_path = folder_settings.get('vault_path', 'Not set')
        console.print(f"[cyan]Vault Path:[/cyan] {vault_path}")
        
        # Watch folders (resolve paths)
        console.print("\n[cyan]Watch Folders:[/cyan]")
        for folder in watch_folders:
            try:
                resolved = resolver.resolve_path(folder)
                console.print(f"  • {folder} → {resolved}")
            except Exception as e:
                console.print(f"  • {folder} → [red]Error: {e}[/red]")
        
        # Output path
        console.print(f"\n[cyan]Output Path:[/cyan] {output_path}")
        try:
            resolved_output = resolver.resolve_with_placeholders(output_path)
            console.print(f"  → {resolved_output}")
        except Exception as e:
            console.print(f"  → [red]Error: {e}[/red]")
        
        # PDF Filter status
        pdf_filter_enabled = config_loader.config.get('pdf_filter', {}).get('enabled', False)
        if pdf_filter_enabled:
            threshold = config_loader.config.get('pdf_filter', {}).get('academic_threshold', 50)
            console.print(f"\n[cyan]PDF Filter:[/cyan] Enabled (threshold: {threshold})")
        else:
            console.print(f"\n[cyan]PDF Filter:[/cyan] Disabled")
        
        console.print("\n" + "=" * 50)
        return
    
    console.print("[bold blue]Starting Obsidian Abstractor...[/bold blue]")
    console.print(f"[cyan]Watching folders:[/cyan] {', '.join(watch_folders)}")
    console.print(f"[cyan]Output path:[/cyan] {output_path}")
    
    # Update config with resolved values
    # watchセクションがない場合は作成
    if 'watch' not in config_loader.config:
        config_loader.config['watch'] = {}
    config_loader.config['watch']['folders'] = watch_folders
    if output_path:
        config_loader.config['watch']['output_path'] = output_path
    
    # Create and start monitor
    async def run_monitor():
        monitor = PDFMonitor(config_loader.config, output_path)
        try:
            await monitor.start(daemon=daemon)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping monitor...[/yellow]")
            await monitor.stop()
            console.print("[green]Monitor stopped[/green]")
    
    try:
        asyncio.run(run_monitor())
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('folder', type=click.Path(exists=True), required=True)
@click.option('--output', '-o', type=click.Path(), required=False, help='Output folder in Obsidian vault')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--recursive', '-r', is_flag=True, help='Process folders recursively')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def batch(folder, output, config, recursive, verbose):
    """Process all PDF files in a folder."""
    setup_logging(verbose)
    
    console.print(f"[bold blue]Batch processing: {folder}[/bold blue]")
    console.print(f"[cyan]Recursive:[/cyan] {'Yes' if recursive else 'No'}")
    
    # Load configuration
    try:
        config_loader = ConfigLoader(config)
        console.print("[green]✓[/green] Configuration loaded")
    except Exception as e:
        console.print(f"[red]Failed to load configuration: {e}[/red]")
        sys.exit(1)
    
    # Create path resolver
    resolver = create_resolver(config_loader.config)
    
    # Determine output path
    if output:
        # Use command-line output
        output_path = output
    else:
        # Use default output from config
        folder_settings = config_loader.config.get('folder_settings', {})
        default_output = folder_settings.get('default_output')
        
        if not default_output:
            console.print("[red]出力先が設定されていません。[/red]")
            console.print("[yellow]config.yamlの'folder_settings.default_output'を設定するか、")
            console.print("--outputオプションで出力先を指定してください。[/yellow]")
            sys.exit(1)
        
        # Use the default output path
        output_path = default_output
    
    console.print(f"[cyan]Output folder:[/cyan] {output_path}")
    
    # Process batch
    async def run_batch():
        monitor = PDFMonitor(config_loader.config, output_path)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("Processing PDFs...", total=None)
            
            results = await monitor.batch_process(Path(folder), recursive=recursive)
            
            progress.update(task, completed=len(results))
        
        # Display results
        table = Table(title="Processing Results")
        table.add_column("Status", style="green")
        table.add_column("Files")
        
        table.add_row("✓ Processed", str(len(results)))
        
        console.print(table)
        
        if results:
            console.print("\n[green]Generated notes:[/green]")
            for note_path in results[:5]:  # Show first 5
                console.print(f"  • {note_path.name}")
            if len(results) > 5:
                console.print(f"  ... and {len(results) - 5} more")
    
    try:
        asyncio.run(run_batch())
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('pdf_file', type=click.Path(exists=True), required=True)
@click.option('--output', '-o', type=click.Path(), required=False, help='Output folder in Obsidian vault')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--force', '-f', is_flag=True, help='Force processing even if filtered out')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def process(pdf_file, output, config, force, verbose):
    """Process a single PDF file."""
    setup_logging(verbose)
    
    pdf_path = Path(pdf_file)
    
    console.print(f"[bold blue]Processing: {pdf_path.name}[/bold blue]")
    
    # Load configuration
    try:
        config_loader = ConfigLoader(config)
        console.print("[green]✓[/green] Configuration loaded")
    except Exception as e:
        console.print(f"[red]Failed to load configuration: {e}[/red]")
        sys.exit(1)
    
    # Create path resolver
    resolver = create_resolver(config_loader.config)
    
    # Determine output path
    if output:
        # Use command-line output
        output_path = Path(output)
    else:
        # Use default output from config
        folder_settings = config_loader.config.get('folder_settings', {})
        default_output = folder_settings.get('default_output')
        
        if not default_output:
            console.print("[red]出力先が設定されていません。[/red]")
            console.print("[yellow]config.yamlの'folder_settings.default_output'を設定するか、")
            console.print("--outputオプションで出力先を指定してください。[/yellow]")
            sys.exit(1)
        
        # Resolve the default output path
        output_path = resolver.resolve_path(default_output)
    
    console.print(f"[cyan]Output folder:[/cyan] {output_path}")
    
    # Process single file
    async def run_process():
        logger = logging.getLogger(__name__)
        
        # Initialize components
        pdf_extractor = PDFExtractor(config_loader.config)
        paper_abstractor = PaperAbstractor(config_loader.config)
        note_formatter = NoteFormatter(config_loader.config)
        pdf_filter = PDFFilter(config_loader.config)
        
        # Ensure output directory exists
        output_path.mkdir(parents=True, exist_ok=True)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Apply PDF filter unless forced
            if not force and pdf_filter.enabled:
                task = progress.add_task("[cyan]Checking if PDF is academic paper...", total=None)
                filter_result = pdf_filter.filter_pdf(pdf_path)
                
                if not filter_result.accepted:
                    progress.update(task, description=f"[yellow]✗ Not an academic paper (score: {filter_result.score})")
                    console.print("\n[yellow]This PDF was filtered out:[/yellow]")
                    for reason in filter_result.reasons[:3]:  # Show top 3 reasons
                        console.print(f"  • {reason}")
                    console.print(f"\n[cyan]Tip:[/cyan] Use --force to process anyway")
                    return
                else:
                    progress.update(task, description=f"[green]✓ Academic paper detected (score: {filter_result.score})")
            
            # Extract PDF
            task = progress.add_task("[cyan]Extracting PDF content...", total=None)
            try:
                pdf_data = pdf_extractor.extract(pdf_path)
                progress.update(task, description="[green]✓ PDF extracted")
            except Exception as e:
                progress.update(task, description=f"[red]✗ PDF extraction failed: {e}")
                raise
            
            # Generate abstract
            task = progress.add_task("[cyan]Generating AI abstract...", total=None)
            try:
                abstract_data = await paper_abstractor.generate_abstract(pdf_data)
                progress.update(task, description="[green]✓ Abstract generated")
            except Exception as e:
                progress.update(task, description=f"[red]✗ Abstract generation failed: {e}")
                raise
            
            # Format note
            task = progress.add_task("[cyan]Creating Obsidian note...", total=None)
            temp_path = None
            try:
                note_content = note_formatter.format_note(pdf_data, abstract_data, pdf_path)
                
                # Step 1: Save with temporary filename
                temp_filename = f"temp_{uuid.uuid4()}.md"
                temp_path = output_path / temp_filename
                temp_path.write_text(note_content, encoding='utf-8')
                
                # Step 2: Extract YAML frontmatter
                yaml_data = extract_yaml_frontmatter(note_content)
                
                # Step 3: Generate final filename from YAML
                final_filename = generate_filename_from_yaml(yaml_data, config_loader.config)
                final_path = output_path / f"{final_filename}.md"
                
                # Step 4: Rename with conflict handling
                final_path = handle_rename(temp_path, final_path)
                temp_path = None  # Mark as successfully renamed
                
                progress.update(task, description=f"[green]✓ Note created: {final_path.name}")
            except Exception as e:
                progress.update(task, description=f"[red]✗ Note creation failed: {e}")
                # Clean up temp file if it exists
                if temp_path and temp_path.exists():
                    try:
                        temp_path.unlink()
                    except:
                        pass
                raise
        
        # Display summary
        console.print("\n[bold green]Success![/bold green]")
        
        # Show metadata
        metadata = pdf_data.get('metadata', {})
        if metadata.get('title'):
            console.print(f"[cyan]Title:[/cyan] {metadata['title']}")
        if metadata.get('author'):
            console.print(f"[cyan]Authors:[/cyan] {metadata['author']}")
        if metadata.get('year'):
            console.print(f"[cyan]Year:[/cyan] {metadata['year']}")
        
        console.print(f"\n[cyan]Note saved to:[/cyan] {final_path}")
    
    try:
        asyncio.run(run_process())
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command(name='paperpile-sync')
@click.option('--dry-run', is_flag=True, help='Perform a dry run without copying files')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def paperpile_sync_cmd(dry_run, config, verbose):
    """Sync PDFs from Paperpile to Obsidian vault using rclone."""
    setup_logging(verbose)
    
    # Load configuration
    try:
        config_loader = ConfigLoader(config)
        console.print("[green]✓[/green] Configuration loaded")
    except Exception as e:
        console.print(f"[red]Failed to load configuration: {e}[/red]")
        sys.exit(1)
    
    # Create path resolver
    resolver = create_resolver(config_loader.config)
    
    # Check if paperpile sync is enabled
    sync_config = config_loader.config.get('paperpile_sync', {})
    if not sync_config.get('enabled', False):
        console.print("\n[yellow]Paperpile sync is disabled in configuration.[/yellow]")
        console.print("To enable, add the following to your config.yaml:")
        console.print("\n[cyan]paperpile_sync:")
        console.print("  enabled: true")
        console.print("  rclone_remote: 'paperpile:'")
        console.print("  source_dirs: ['Papers', 'Unsorted']")
        console.print("  max_age: '7d'[/cyan]\n")
        sys.exit(1)
    
    async def run_sync():
        """Run the synchronization process."""
        console.print("\n[bold cyan]Paperpile PDF Sync[/bold cyan]")
        console.print("=" * 50)
        
        if dry_run:
            console.print("[yellow]DRY RUN MODE - No files will be copied[/yellow]\n")
        
        # Run sync
        success = await sync_paperpile(config_loader.config, resolver, dry_run)
        
        if success:
            console.print("\n[bold green]Sync completed successfully![/bold green]")
        else:
            console.print("\n[bold red]Sync failed. Check the logs for details.[/bold red]")
            sys.exit(1)
    
    try:
        asyncio.run(run_sync())
    except KeyboardInterrupt:
        console.print("\n[yellow]Sync cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)


def main():
    """Main entry point."""
    try:
        cli()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()