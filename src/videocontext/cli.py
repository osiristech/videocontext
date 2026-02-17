"""VideoContext CLI — extract video content for AI consumption."""

from __future__ import annotations

import sys

import click
from rich.console import Console

from videocontext.url import extract_video_id

err_console = Console(stderr=True)


def _write_output(text: str, output: str | None) -> None:
    """Write text to file or stdout."""
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(text)
            f.write("\n")
        err_console.print(f"[green]Written to {output}[/green]")
    else:
        click.echo(text)


@click.group()
@click.version_option(package_name="videocontext")
def cli():
    """VideoContext — Extract video content for AI CLI consumption."""
    pass


@cli.command()
@click.argument("url")
@click.option("-f", "--format", "fmt", type=click.Choice(["text", "timestamped", "json"]), default="text", help="Output format.")
@click.option("-l", "--lang", default="en", help="Transcript language code.")
@click.option("-o", "--output", default=None, help="Output file (default: stdout).")
def transcript(url: str, fmt: str, lang: str, output: str | None):
    """Extract transcript from a YouTube video."""
    from videocontext.extractors.transcript import fetch_transcript
    from videocontext.formatters import json_fmt, markdown

    try:
        video_id = extract_video_id(url)
    except ValueError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    with err_console.status("Fetching transcript..."):
        try:
            segments = fetch_transcript(video_id, lang=lang)
        except RuntimeError as e:
            err_console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)

    if fmt == "json":
        result = json_fmt.format_transcript(segments)
    elif fmt == "timestamped":
        result = markdown.format_transcript(segments, timestamped=True)
    else:
        result = "\n".join(seg.text for seg in segments)

    _write_output(result, output)


@cli.command()
@click.argument("url")
@click.option("-f", "--format", "fmt", type=click.Choice(["markdown", "json"]), default="markdown", help="Output format.")
@click.option("-o", "--output", default=None, help="Output file (default: stdout).")
def metadata(url: str, fmt: str, output: str | None):
    """Extract video metadata (title, description, chapters, tags, duration)."""
    from videocontext.extractors.metadata import fetch_metadata
    from videocontext.formatters import json_fmt, markdown

    try:
        video_id = extract_video_id(url)
    except ValueError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    with err_console.status("Fetching metadata..."):
        try:
            meta = fetch_metadata(video_id)
        except RuntimeError as e:
            err_console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)

    if fmt == "json":
        result = json_fmt.format_metadata(meta)
    else:
        result = markdown.format_metadata(meta)

    _write_output(result, output)


@cli.command()
@click.argument("url")
@click.option("-f", "--format", "fmt", type=click.Choice(["markdown", "json", "text"]), default="markdown", help="Output format.")
@click.option("--no-transcript", is_flag=True, help="Metadata only, skip transcript.")
@click.option("--no-chapters", is_flag=True, help="Skip chapter markers.")
@click.option("-l", "--lang", default="en", help="Transcript language code.")
@click.option("-o", "--output", default=None, help="Output file (default: stdout).")
def context(url: str, fmt: str, no_transcript: bool, no_chapters: bool, lang: str, output: str | None):
    """Full video context — metadata + transcript, formatted for AI consumption."""
    from videocontext.extractors.metadata import fetch_metadata
    from videocontext.extractors.transcript import fetch_transcript
    from videocontext.formatters import json_fmt, markdown, text

    try:
        video_id = extract_video_id(url)
    except ValueError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    with err_console.status("Fetching metadata..."):
        try:
            meta = fetch_metadata(video_id)
        except RuntimeError as e:
            err_console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)

    segments = None
    if not no_transcript:
        with err_console.status("Fetching transcript..."):
            try:
                segments = fetch_transcript(video_id, lang=lang)
            except RuntimeError as e:
                err_console.print(f"[yellow]Warning:[/yellow] {e}")
                err_console.print("[yellow]Continuing without transcript.[/yellow]")

    formatter = {"markdown": markdown, "json": json_fmt, "text": text}[fmt]
    result = formatter.format_full(meta, segments, include_chapters=not no_chapters)

    _write_output(result, output)


@cli.command()
@click.argument("url")
@click.option("--interval", type=float, default=None, help="Seconds between frames.")
@click.option("--output-dir", default="./frames", help="Directory for extracted frames.")
@click.option("--max-frames", type=int, default=20, help="Max number of frames.")
def frames(url: str, interval: float | None, output_dir: str, max_frames: int):
    """Extract key frames from a video (requires [vision] extra)."""
    from videocontext.extractors.frames import extract_frames

    try:
        video_id = extract_video_id(url)
    except ValueError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    try:
        paths = extract_frames(video_id, output_dir, interval=interval, max_frames=max_frames)
        for p in paths:
            click.echo(p)
    except ImportError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except NotImplementedError as e:
        err_console.print(f"[yellow]{e}[/yellow]")
        sys.exit(0)
