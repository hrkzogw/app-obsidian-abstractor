#!/usr/bin/env python3
"""
Obsidian Abstractor - Main entry point.

AI-powered academic paper summarizer for Obsidian.
"""

import sys
import asyncio
import logging
import click
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from .config_loader import ConfigLoader
from .pdf_monitor import PDFMonitor
from .pdf_extractor import PDFExtractor
from .paper_abstractor import PaperAbstractor
from .note_formatter import NoteFormatter

console = Console()


def setup_logging(verbose: bool):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configure rich handler
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )
    
    # Reduce noise from some libraries
    logging.getLogger("watchdog").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Obsidian Abstractor - AI-powered academic paper summarizer."""
    pass


@cli.command()
@click.argument('folders', nargs=-1, type=click.Path(exists=True), required=True)
@click.option('--output', '-o', type=click.Path(), required=True, help='Output folder in Obsidian vault')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--daemon', '-d', is_flag=True, help='Run as daemon in background')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def watch(folders, output, config, daemon, verbose):
    """Watch folders for new PDF files and process them."""
    setup_logging(verbose)
    
    console.print("[bold blue]Starting Obsidian Abstractor...[/bold blue]")
    console.print(f"[cyan]Watching folders:[/cyan] {', '.join(folders)}")
    console.print(f"[cyan]Output folder:[/cyan] {output}")
    
    # Load configuration
    try:
        config_loader = ConfigLoader(config)
        console.print("[green]✓[/green] Configuration loaded")
    except Exception as e:
        console.print(f"[red]Failed to load configuration: {e}[/red]")
        sys.exit(1)
    
    # Update watch folders in config
    if folders:
        config_loader.config['watch']['folders'] = list(folders)
    
    # Create and start monitor
    async def run_monitor():
        monitor = PDFMonitor(config_loader.config, output)
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
@click.option('--output', '-o', type=click.Path(), required=True, help='Output folder in Obsidian vault')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--recursive', '-r', is_flag=True, help='Process folders recursively')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def batch(folder, output, config, recursive, verbose):
    """Process all PDF files in a folder."""
    setup_logging(verbose)
    
    console.print(f"[bold blue]Batch processing: {folder}[/bold blue]")
    console.print(f"[cyan]Output folder:[/cyan] {output}")
    console.print(f"[cyan]Recursive:[/cyan] {'Yes' if recursive else 'No'}")
    
    # Load configuration
    try:
        config_loader = ConfigLoader(config)
        console.print("[green]✓[/green] Configuration loaded")
    except Exception as e:
        console.print(f"[red]Failed to load configuration: {e}[/red]")
        sys.exit(1)
    
    # Process batch
    async def run_batch():
        monitor = PDFMonitor(config_loader.config, output)
        
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
@click.option('--output', '-o', type=click.Path(), required=True, help='Output folder in Obsidian vault')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def process(pdf_file, output, config, verbose):
    """Process a single PDF file."""
    setup_logging(verbose)
    
    pdf_path = Path(pdf_file)
    output_path = Path(output)
    
    console.print(f"[bold blue]Processing: {pdf_path.name}[/bold blue]")
    console.print(f"[cyan]Output folder:[/cyan] {output}")
    
    # Load configuration
    try:
        config_loader = ConfigLoader(config)
        console.print("[green]✓[/green] Configuration loaded")
    except Exception as e:
        console.print(f"[red]Failed to load configuration: {e}[/red]")
        sys.exit(1)
    
    # Process single file
    async def run_process():
        # Initialize components
        pdf_extractor = PDFExtractor(config_loader.config)
        paper_abstractor = PaperAbstractor(config_loader.config)
        note_formatter = NoteFormatter(config_loader.config)
        
        # Ensure output directory exists
        output_path.mkdir(parents=True, exist_ok=True)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
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
            try:
                note_content = note_formatter.format_note(pdf_data, abstract_data, pdf_path)
                filename = note_formatter.generate_filename(pdf_data, pdf_path)
                note_path = output_path / f"{filename}.md"
                
                # Ensure unique filename
                counter = 1
                while note_path.exists():
                    note_path = output_path / f"{filename}_{counter}.md"
                    counter += 1
                
                # Write note
                note_path.write_text(note_content, encoding='utf-8')
                progress.update(task, description=f"[green]✓ Note created: {note_path.name}")
            except Exception as e:
                progress.update(task, description=f"[red]✗ Note creation failed: {e}")
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
        
        console.print(f"\n[cyan]Note saved to:[/cyan] {note_path}")
    
    try:
        asyncio.run(run_process())
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