"""Markdown formatter for AI consumption."""

from __future__ import annotations

from videocontext.extractors.metadata import VideoMetadata
from videocontext.extractors.transcript import TranscriptSegment


def format_timestamp(seconds: float) -> str:
    """Format seconds as H:MM:SS or M:SS."""
    total = int(seconds)
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_metadata(meta: VideoMetadata) -> str:
    """Format video metadata as markdown."""
    lines = [
        f"# Video: {meta.title}",
        f"**Channel:** {meta.channel} | **Duration:** {format_timestamp(meta.duration)} | **Published:** {meta.upload_date}",
        f"**URL:** {meta.url}",
    ]

    if meta.chapters:
        lines.append("")
        lines.append("## Chapters")
        for ch in meta.chapters:
            lines.append(f"- [{format_timestamp(ch.start_time)}] {ch.title}")

    if meta.description:
        lines.append("")
        lines.append("## Description")
        lines.append(meta.description.strip())

    return "\n".join(lines)


def format_transcript(segments: list[TranscriptSegment], timestamped: bool = True) -> str:
    """Format transcript segments as markdown."""
    lines = ["## Transcript"]
    for seg in segments:
        if timestamped:
            lines.append(f"[{format_timestamp(seg.start)}] {seg.text}")
        else:
            lines.append(seg.text)
    return "\n".join(lines)


def format_full(
    meta: VideoMetadata,
    segments: list[TranscriptSegment] | None = None,
    include_chapters: bool = True,
) -> str:
    """Format full video context as markdown."""
    lines = [
        f"# Video: {meta.title}",
        f"**Channel:** {meta.channel} | **Duration:** {format_timestamp(meta.duration)} | **Published:** {meta.upload_date}",
        f"**URL:** {meta.url}",
    ]

    if include_chapters and meta.chapters:
        lines.append("")
        lines.append("## Chapters")
        for ch in meta.chapters:
            lines.append(f"- [{format_timestamp(ch.start_time)}] {ch.title}")

    if meta.description:
        lines.append("")
        lines.append("## Description")
        lines.append(meta.description.strip())

    if segments:
        lines.append("")
        lines.append(format_transcript(segments))

    return "\n".join(lines)
