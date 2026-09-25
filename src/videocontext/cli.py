"""VideoContext CLI — extract video content for AI consumption."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.markup import escape

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


def _print_error(message: str) -> None:
    err_console.print(f"[red]Error:[/red] {escape(message)}")


def _print_warning(message: str) -> None:
    err_console.print(f"[yellow]Warning:[/yellow] {escape(message)}")


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
        _print_error(str(e))
        sys.exit(1)

    with err_console.status("Fetching transcript..."):
        try:
            segments = fetch_transcript(video_id, lang=lang)
        except RuntimeError as e:
            _print_error(str(e))
            sys.exit(1)

    if fmt == "json":
        result = json_fmt.format_transcript(segments)
    elif fmt == "timestamped":
        result = markdown.format_transcript(segments, timestamped=True)
    else:
        result = "\n".join(seg.text for seg in segments)

    _write_output(result, output)


@cli.command("batch-transcripts")
@click.argument("ids_file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-o", "--output-dir", required=True, type=click.Path(path_type=Path), help="Directory for per-video text files.")
@click.option("-l", "--lang", default="en", show_default=True, help="Transcript language code.")
@click.option("--interval", type=click.FloatRange(min=0), default=120.0, show_default=True, help="Seconds between video requests.")
@click.option("--initial-cooldown", type=click.FloatRange(min=1), default=1800.0, show_default=True, help="First wait after a rate limit, in seconds.")
@click.option("--max-cooldown", type=click.FloatRange(min=1), default=7200.0, show_default=True, help="Maximum wait after repeated rate limits, in seconds.")
@click.option("--max-rate-retries", type=click.IntRange(min=0), default=6, show_default=True, help="Retries for one blocked video before pausing the batch.")
@click.option("--retry-forever", is_flag=True, help="Keep waiting and retrying rate limits until interrupted.")
@click.option("--status", is_flag=True, help="Show saved and pending counts without network requests.")
@click.option("--titles-file", type=click.Path(exists=True, dir_okay=False, path_type=Path),
              help="Local ID-and-title inventory (tab-separated), avoiding title lookup requests.")
@click.option("--organize-only", "--migrate-only", is_flag=True,
              help="Organize saved transcripts and generate the catalog without network requests.")
def batch_transcripts(
    ids_file: Path, output_dir: Path, lang: str, interval: float,
    initial_cooldown: float, max_cooldown: float, max_rate_retries: int,
    retry_forever: bool, status: bool, titles_file: Path | None, organize_only: bool,
):
    """Download any length list of YouTube IDs or URLs, resuming saved files."""
    from videocontext.batch import BatchPaused, download_transcripts, inspect_batch, organize_collection

    try:
        if status:
            counts = inspect_batch(ids_file, output_dir)
            click.echo(f"{counts.total} videos: {counts.saved} saved, {counts.pending} pending")
            return
        if organize_only:
            moved = organize_collection(ids_file, output_dir, titles_file)
            click.echo(f"Organized collection; moved {moved} transcripts.")
            return

        summary = download_transcripts(
            ids_file, output_dir, lang=lang, interval=interval,
            initial_cooldown=initial_cooldown, max_cooldown=max_cooldown,
            max_rate_retries=None if retry_forever else max_rate_retries,
            titles_file=titles_file,
            progress=lambda message: click.echo(message, err=True),
        )
    except BatchPaused as error:
        _print_error(str(error))
        click.echo(
            f"Paused: {error.summary.completed} saved, {error.summary.skipped} skipped, "
            f"{error.summary.failed} failed this run; rerun to resume.", err=True,
        )
        sys.exit(75)
    except (OSError, RuntimeError, ValueError) as error:
        _print_error(str(error))
        sys.exit(1)

    click.echo(
        f"Batch complete: {summary.completed} saved, {summary.skipped} skipped, "
        f"{summary.failed} failed, {summary.rate_limit_retries} rate-limit retries."
    )


@cli.command()
@click.argument("url")
@click.option("-f", "--format", "fmt", type=click.Choice(["markdown", "json", "html"]), default="markdown", help="Output format.")
@click.option("-o", "--output", default=None, help="Output file (default: stdout).")
def metadata(url: str, fmt: str, output: str | None):
    """Extract video metadata (title, description, chapters, tags, duration)."""
    from videocontext.extractors.metadata import fetch_metadata
    from videocontext.formatters import html, json_fmt, markdown

    try:
        video_id = extract_video_id(url)
    except ValueError as e:
        _print_error(str(e))
        sys.exit(1)

    with err_console.status("Fetching metadata..."):
        try:
            meta = fetch_metadata(video_id)
        except RuntimeError as e:
            _print_error(str(e))
            sys.exit(1)

    if fmt == "json":
        result = json_fmt.format_metadata(meta)
    elif fmt == "html":
        result = html.format_metadata(meta)
    else:
        result = markdown.format_metadata(meta)

    _write_output(result, output)


@cli.command()
@click.argument("url")
@click.option("-f", "--format", "fmt", type=click.Choice(["markdown", "json", "text", "html"]), default="markdown", help="Output format.")
@click.option("--no-transcript", is_flag=True, help="Metadata only, skip transcript.")
@click.option("--no-chapters", is_flag=True, help="Skip chapter markers.")
@click.option("-l", "--lang", default="en", help="Transcript language code.")
@click.option("-o", "--output", default=None, help="Output file (default: stdout).")
def context(url: str, fmt: str, no_transcript: bool, no_chapters: bool, lang: str, output: str | None):
    """Full video context — metadata + transcript, formatted for AI consumption."""
    from videocontext.extractors.metadata import fetch_metadata
    from videocontext.extractors.transcript import fetch_transcript
    from videocontext.formatters import html, json_fmt, markdown, text

    try:
        video_id = extract_video_id(url)
    except ValueError as e:
        _print_error(str(e))
        sys.exit(1)

    with err_console.status("Fetching metadata..."):
        try:
            meta = fetch_metadata(video_id)
        except RuntimeError as e:
            _print_error(str(e))
            sys.exit(1)

    segments = None
    if not no_transcript:
        with err_console.status("Fetching transcript..."):
            try:
                segments = fetch_transcript(video_id, lang=lang)
            except RuntimeError as e:
                _print_warning(str(e))
                err_console.print("[yellow]Continuing without transcript.[/yellow]")

    formatter = {"markdown": markdown, "json": json_fmt, "text": text, "html": html}[fmt]
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
        _print_error(str(e))
        sys.exit(1)

    try:
        paths = extract_frames(video_id, output_dir, interval=interval, max_frames=max_frames)
        for p in paths:
            click.echo(p)
    except ImportError as e:
        _print_error(str(e))
        sys.exit(1)
    except NotImplementedError as e:
        err_console.print(f"[yellow]{escape(str(e))}[/yellow]")
        sys.exit(0)
    except RuntimeError as e:
        _print_error(str(e))
        sys.exit(1)


@cli.command()
@click.argument("url")
@click.option("--output-dir", default="./videocontext-output", help="Root directory for saved bundles.")
@click.option("-l", "--lang", default="en", help="Transcript language code.")
@click.option("--open", "open_after", is_flag=True, help="Open the saved folder in File Explorer.")
@click.option("--overwrite", is_flag=True, help="Replace an existing bundle folder.")
def save(url: str, output_dir: str, lang: str, open_after: bool, overwrite: bool):
    """Save metadata, transcript, context, HTML, and a manifest."""
    from videocontext.bundle import BundleExistsError, open_folder, save_bundle

    try:
        video_id = extract_video_id(url)
    except ValueError as e:
        _print_error(str(e))
        sys.exit(1)

    with err_console.status("Saving video context bundle..."):
        try:
            manifest = save_bundle(video_id, output_dir=output_dir, lang=lang, overwrite=overwrite)
        except BundleExistsError as e:
            _print_error(str(e))
            sys.exit(1)
        except RuntimeError as e:
            _print_error(str(e))
            sys.exit(1)

    for warning in manifest["warnings"]:
        _print_warning(warning)

    bundle_dir = manifest["output_dir"]
    err_console.print(f"[green]Saved bundle to {escape(bundle_dir)}[/green]")
    for filename in manifest["files"]:
        click.echo(f"{bundle_dir}/{filename}")

    if open_after:
        open_folder(bundle_dir)
