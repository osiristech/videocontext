"""Transcript extraction from YouTube videos."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TranscriptSegment:
    """A single segment of a transcript."""
    start: float
    duration: float
    text: str


def fetch_transcript(video_id: str, lang: str = "en") -> list[TranscriptSegment]:
    """Fetch transcript for a YouTube video.

    Uses youtube-transcript-api as the primary method, falls back to yt-dlp
    subtitle extraction if that fails.

    Args:
        video_id: The 11-character YouTube video ID.
        lang: Language code for the transcript.

    Returns:
        List of TranscriptSegment objects.

    Raises:
        RuntimeError: If no transcript could be retrieved.
    """
    # Try youtube-transcript-api first
    try:
        return _fetch_via_api(video_id, lang)
    except Exception:
        pass

    # Fallback to yt-dlp subtitle extraction
    try:
        return _fetch_via_ytdlp(video_id, lang)
    except Exception as e:
        raise RuntimeError(
            f"Could not retrieve transcript for video {video_id}.\n"
            f"The video may not have captions available in '{lang}'."
        ) from e


def _fetch_via_api(video_id: str, lang: str) -> list[TranscriptSegment]:
    """Fetch transcript using youtube-transcript-api."""
    from youtube_transcript_api import YouTubeTranscriptApi

    ytt_api = YouTubeTranscriptApi()
    transcript = ytt_api.fetch(video_id, languages=[lang, f"{lang}-auto", f"a.{lang}"])

    return [
        TranscriptSegment(
            start=snippet.start,
            duration=snippet.duration,
            text=snippet.text,
        )
        for snippet in transcript.snippets
    ]


def _fetch_via_ytdlp(video_id: str, lang: str) -> list[TranscriptSegment]:
    """Fetch transcript using yt-dlp subtitle extraction."""
    import json
    import tempfile
    from pathlib import Path

    import yt_dlp

    with tempfile.TemporaryDirectory() as tmpdir:
        opts = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": [lang],
            "subtitlesformat": "json3",
            "outtmpl": str(Path(tmpdir) / "%(id)s"),
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

        # Find the subtitle file
        sub_files = list(Path(tmpdir).glob("*.json3"))
        if not sub_files:
            raise RuntimeError("No subtitle file produced by yt-dlp")

        data = json.loads(sub_files[0].read_text())
        segments = _parse_json3_transcript(data)
        if not segments:
            raise RuntimeError("yt-dlp subtitles contained no text")

        return segments


def _parse_json3_transcript(data: dict) -> list[TranscriptSegment]:
    segments = []
    for event in data.get("events", []):
        start_ms = event.get("tStartMs", 0)
        duration_ms = event.get("dDurationMs", 0)
        segs = event.get("segs", [])
        text = "".join(s.get("utf8", "") for s in segs).strip()
        if text:
            segments.append(TranscriptSegment(
                start=start_ms / 1000.0,
                duration=duration_ms / 1000.0,
                text=text,
            ))
    return segments
