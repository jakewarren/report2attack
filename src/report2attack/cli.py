"""Command-line interface for report2attack."""

import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import __version__
from .mapping import create_mapper
from .output import format_results
from .parsers import parse_input
from .preprocessing import chunk_text, preprocess_text
from .rag import setup_retrieval_system

console = Console()


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("input_source", type=str)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default=".",
    help="Output directory for results",
)
@click.option(
    "--formats",
    "-f",
    multiple=True,
    default=["json", "markdown"],
    help="Output formats (json, csv, markdown, navigator)",
)
@click.option(
    "--llm-provider",
    type=click.Choice(["openai", "anthropic", "ollama"]),
    default="openai",
    help="LLM provider to use",
)
@click.option(
    "--llm-model",
    type=str,
    default=None,
    help="LLM model name (provider-specific)",
)
@click.option(
    "--embedding-provider",
    type=click.Choice(["openai", "sentence-transformers"]),
    default="openai",
    help="Embedding provider to use",
)
@click.option(
    "--chunk-size",
    type=int,
    default=500,
    help="Maximum tokens per chunk",
)
@click.option(
    "--chunk-overlap",
    type=int,
    default=50,
    help="Token overlap between chunks",
)
@click.option(
    "--top-k",
    type=int,
    default=10,
    help="Number of techniques to retrieve per chunk",
)
@click.option(
    "--min-confidence",
    type=float,
    default=0.5,
    help="Minimum confidence threshold (0.0-1.0)",
)
@click.option(
    "--force-reload",
    is_flag=True,
    help="Force reload of ATT&CK data",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Verbose output",
)
@click.version_option(version=__version__)
def main(
    input_source: str,
    output_dir: str,
    formats: tuple,
    llm_provider: str,
    llm_model: str | None,
    embedding_provider: str,
    chunk_size: int,
    chunk_overlap: int,
    top_k: int,
    min_confidence: float,
    force_reload: bool,
    verbose: bool,
) -> None:
    """
    report2attack: Automated threat intelligence to MITRE ATT&CK mapping.

    INPUT_SOURCE can be:
    - A web URL (http:// or https://)
    - A PDF URL (ending in .pdf)
    - A local PDF file path

    Example usage:

        report2attack https://example.com/threat-report.html

        report2attack https://example.com/report.pdf

        report2attack report.pdf --formats json csv --output-dir ./results
    """
    try:
        # Support comma-separated formats (e.g., -f markdown,navigator)
        processed_formats = []
        for fmt in formats:
            if "," in fmt:
                processed_formats.extend([f.strip() for f in fmt.split(",") if f.strip()])
            else:
                processed_formats.append(fmt)
        formats = tuple(processed_formats)

        # Validate arguments before processing
        valid_formats = {"json", "csv", "markdown", "navigator"}
        invalid_formats = [fmt for fmt in formats if fmt not in valid_formats]
        if invalid_formats:
            console.print(
                f"[red]Error:[/red] Invalid format(s): {', '.join(invalid_formats)}\n"
                f"Valid formats are: {', '.join(sorted(valid_formats))}\n"
                f"Hint: You can use commas (-f json,csv) or multiple flags (-f json -f csv)"
            )
            sys.exit(1)

        if not formats:
            console.print(
                "[yellow]Warning:[/yellow] No formats specified, using defaults: json, markdown"
            )
            formats = ("json", "markdown")

        console.print(
            Panel.fit(
                f"[bold cyan]report2attack v{__version__}[/bold cyan]\n"
                "Automated ATT&CK Mapping Tool",
                border_style="cyan",
            )
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Step 1: Parse input
            task = progress.add_task("[cyan]Parsing input...", total=None)
            try:
                parsed = parse_input(input_source)
                source = parsed["source"]
                title = parsed["title"]
                text = parsed["text"]
                console.print(f"[green]✓[/green] Parsed: {title or source}")
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to parse input: {e}")
                sys.exit(1)
            progress.remove_task(task)

            # Step 2: Preprocess and chunk
            task = progress.add_task("[cyan]Preprocessing text...", total=None)
            try:
                cleaned_text = preprocess_text(text)
                chunks = chunk_text(
                    cleaned_text,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    source_document=source,
                )
                console.print(f"[green]✓[/green] Created {len(chunks)} chunks")
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to preprocess text: {e}")
                sys.exit(1)
            progress.remove_task(task)

            # Step 3: Setup retrieval system
            task = progress.add_task("[cyan]Setting up ATT&CK retrieval...", total=None)
            try:
                retriever = setup_retrieval_system(
                    embedding_provider=embedding_provider,
                    force_reload=force_reload,
                )
                console.print("[green]✓[/green] Retrieval system ready")
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to setup retrieval: {e}")
                sys.exit(1)
            progress.remove_task(task)

            # Step 4: Retrieve relevant techniques for each chunk
            task = progress.add_task("[cyan]Retrieving techniques...", total=None)
            all_retrieved = []
            try:
                # Batch retrieval for better performance
                chunk_texts = [chunk.text for chunk in chunks]
                all_retrieved = retriever.batch_retrieve(chunk_texts, tactic_filter=None)
                console.print(f"[green]✓[/green] Retrieved techniques for {len(chunks)} chunks")
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to retrieve techniques: {e}")
                sys.exit(1)
            progress.remove_task(task)

            # Step 5: Map to ATT&CK techniques using LLM
            task = progress.add_task(
                "[cyan]Mapping techniques with LLM...", total=len(chunks) if verbose else None
            )
            try:
                mapper = create_mapper(
                    llm_provider=llm_provider,
                    model_name=llm_model,
                    min_confidence=min_confidence,
                )

                if verbose:
                    actual_model = mapper.llm_name
                    console.print(f"[dim]Using {actual_model}[/dim]")

                # Prepare chunks for mapper
                chunk_dicts = [
                    {
                        "text": chunk.text,
                        "chunk_index": chunk.chunk_index,
                        "source_document": chunk.source_document,
                    }
                    for chunk in chunks
                ]

                # Define progress callback without tuple unpacking overhead
                def update_progress(i, total, found):
                    if verbose:
                        progress.update(task, completed=i)
                        console.print(f"[dim]  Chunk {i}/{total}: found {found} techniques[/dim]")

                mappings = mapper.map_document(
                    chunk_dicts,
                    all_retrieved,
                    verbose=verbose,
                    progress_callback=update_progress if verbose else None,
                )
                console.print(f"[green]✓[/green] Mapped {len(mappings)} techniques")
                if verbose:
                    console.print(f"[dim]  Total LLM requests: {mapper.request_count}[/dim]")
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to map techniques: {e}")
                if verbose:
                    console.print_exception()
                sys.exit(1)
            progress.remove_task(task)

            # Step 6: Format results
            task = progress.add_task("[cyan]Generating output...", total=None)
            try:
                # Prepare results
                results = {
                    "source": source,
                    "title": title,
                    "llm_provider": mapper.llm_name,
                    "min_confidence": min_confidence,
                    "attack_version": "18.1",
                    "techniques": [
                        {
                            "technique_id": m.technique_id,
                            "technique_name": m.technique_name,
                            "confidence": m.confidence,
                            "evidence": m.evidence,
                            "tactics": m.tactics,
                        }
                        for m in mappings
                    ],
                }

                output_files = format_results(results, list(formats), output_dir)

                console.print("[green]✓[/green] Generated output files:")
                for fmt, path in output_files.items():
                    console.print(f"  • {fmt}: {path}")

            except Exception as e:
                console.print(f"[red]✗[/red] Failed to generate output: {e}")
                sys.exit(1)
            progress.remove_task(task)

        # Final summary
        console.print("\n[bold green]Analysis complete![/bold green]")
        console.print(
            Panel.fit(
                f"[bold]Summary[/bold]\n"
                f"Techniques: {len(mappings)}\n"
                f"High confidence (≥0.8): {len([m for m in mappings if m.confidence >= 0.8])}\n"
                f"Medium confidence (0.5-0.8): {len([m for m in mappings if 0.5 <= m.confidence < 0.8])}",
                border_style="green",
            )
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
