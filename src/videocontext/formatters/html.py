"""HTML formatter for AI consumption."""

from __future__ import annotations

from videocontext.extractors.metadata import VideoMetadata
from videocontext.extractors.transcript import TranscriptSegment
from videocontext.formatters.markdown import format_timestamp


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _wrap(body: str, title: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{_escape(title)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 860px; margin: 2rem auto; padding: 0 1.5rem; line-height: 1.7; color: #1a1a1a; }}
    h1 {{ font-size: 1.8rem; border-bottom: 2px solid #e0e0e0; padding-bottom: .5rem; }}
    h2 {{ font-size: 1.3rem; margin-top: 2rem; color: #333; }}
    .meta {{ color: #555; margin: .25rem 0; }}
    .meta a {{ color: #0066cc; }}
    ul {{ padding-left: 1.4rem; }}
    li {{ margin: .2rem 0; }}
    .timestamp {{ color: #888; font-size: .85em; margin-right: .4rem; }}
    p {{ margin: .4rem 0; }}
  </style>
</head>
<body>
{body}
</body>
</html>"""


def format_metadata(meta: VideoMetadata) -> str:
    """Format video metadata as an HTML document."""
    lines = [
        f"<h1>{_escape(meta.title)}</h1>",
        f'<p class="meta"><strong>Channel:</strong> {_escape(meta.channel)} &nbsp;|&nbsp; '
        f"<strong>Duration:</strong> {format_timestamp(meta.duration)} &nbsp;|&nbsp; "
        f"<strong>Published:</strong> {_escape(meta.upload_date)}</p>",
        f'<p class="meta"><strong>URL:</strong> <a href="{_escape(meta.url)}">{_escape(meta.url)}</a></p>',
    ]

    if meta.chapters:
        lines.append("<h2>Chapters</h2><ul>")
        for ch in meta.chapters:
            lines.append(f"  <li><span class=\"timestamp\">[{format_timestamp(ch.start_time)}]</span>{_escape(ch.title)}</li>")
        lines.append("</ul>")

    if meta.description:
        desc_html = "".join(f"<p>{_escape(line)}</p>" if line.strip() else "<br>" for line in meta.description.strip().splitlines())
        lines.append(f"<h2>Description</h2>{desc_html}")

    return _wrap("\n".join(lines), meta.title)


def format_transcript(segments: list[TranscriptSegment], timestamped: bool = True) -> str:
    """Format transcript segments as an HTML document."""
    lines = ["<h2>Transcript</h2>"]
    for seg in segments:
        if timestamped:
            lines.append(f'<p><span class="timestamp">[{format_timestamp(seg.start)}]</span>{_escape(seg.text)}</p>')
        else:
            lines.append(f"<p>{_escape(seg.text)}</p>")
    return _wrap("\n".join(lines), "Transcript")


def format_full(
    meta: VideoMetadata,
    segments: list[TranscriptSegment] | None = None,
    include_chapters: bool = True,
) -> str:
    """Format full video context as an HTML document."""
    lines = [
        f"<h1>{_escape(meta.title)}</h1>",
        f'<p class="meta"><strong>Channel:</strong> {_escape(meta.channel)} &nbsp;|&nbsp; '
        f"<strong>Duration:</strong> {format_timestamp(meta.duration)} &nbsp;|&nbsp; "
        f"<strong>Published:</strong> {_escape(meta.upload_date)}</p>",
        f'<p class="meta"><strong>URL:</strong> <a href="{_escape(meta.url)}">{_escape(meta.url)}</a></p>',
    ]

    if include_chapters and meta.chapters:
        lines.append("<h2>Chapters</h2><ul>")
        for ch in meta.chapters:
            lines.append(f"  <li><span class=\"timestamp\">[{format_timestamp(ch.start_time)}]</span>{_escape(ch.title)}</li>")
        lines.append("</ul>")

    if meta.description:
        desc_html = "".join(f"<p>{_escape(line)}</p>" if line.strip() else "<br>" for line in meta.description.strip().splitlines())
        lines.append(f"<h2>Description</h2>{desc_html}")

    if segments:
        lines.append("<h2>Transcript</h2>")
        for seg in segments:
            lines.append(f'<p><span class="timestamp">[{format_timestamp(seg.start)}]</span>{_escape(seg.text)}</p>')

    return _wrap("\n".join(lines), meta.title)
