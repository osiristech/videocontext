"""Plain text formatter — minimal, no markup."""

from __future__ import annotations

from videocontext.extractors.metadata import VideoMetadata
from videocontext.extractors.transcript import TranscriptSegment
from videocontext.formatters.markdown import format_timestamp


def format_metadata(meta: VideoMetadata) -> str:
    """Format video metadata as plain text."""
    lines = [
        meta.title,
        f"Channel: {meta.channel}",
        f"Duration: {format_timestamp(meta.duration)}",
        f"Published: {meta.upload_date}",
        f"URL: {meta.url}",
    ]

    if meta.chapters:
        lines.append("")
        lines.append("Chapters:")
        for ch in meta.chapters:
            lines.append(f"  {format_timestamp(ch.start_time)} - {ch.title}")

    if meta.description:
        lines.append("")
        lines.append(meta.description.strip())

    return "\n".join(lines)


def format_transcript(segments: list[TranscriptSegment], timestamped: bool = False) -> str:
    """Format transcript as plain text (no timestamps by default)."""
    if timestamped:
        return "\n".join(f"[{format_timestamp(seg.start)}] {seg.text}" for seg in segments)
    return "\n".join(seg.text for seg in segments)


def format_full(
    meta: VideoMetadata,
    segments: list[TranscriptSegment] | None = None,
    include_chapters: bool = True,
) -> str:
    """Format full video context as plain text."""
    parts = [format_metadata(meta)]
    if not include_chapters:
        # Re-format without chapters
        m = VideoMetadata(**{**meta.__dict__, "chapters": []})
        parts = [format_metadata(m)]

    if segments:
        parts.append("")
        parts.append("Transcript:")
        parts.append(format_transcript(segments))

    return "\n".join(parts)
