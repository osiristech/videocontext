"""JSON formatter for machine-readable output."""

from __future__ import annotations

import json
from dataclasses import asdict

from videocontext.extractors.metadata import VideoMetadata
from videocontext.extractors.transcript import TranscriptSegment


def format_metadata(meta: VideoMetadata) -> str:
    """Format video metadata as JSON."""
    data = asdict(meta)
    return json.dumps(data, indent=2, ensure_ascii=False)


def format_transcript(segments: list[TranscriptSegment]) -> str:
    """Format transcript segments as JSON."""
    data = [asdict(seg) for seg in segments]
    return json.dumps(data, indent=2, ensure_ascii=False)


def format_full(
    meta: VideoMetadata,
    segments: list[TranscriptSegment] | None = None,
    include_chapters: bool = True,
) -> str:
    """Format full video context as JSON."""
    data = asdict(meta)
    if not include_chapters:
        data.pop("chapters", None)
    if segments:
        data["transcript"] = [asdict(seg) for seg in segments]
    return json.dumps(data, indent=2, ensure_ascii=False)
