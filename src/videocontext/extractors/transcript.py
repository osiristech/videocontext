"""Transcript extraction from YouTube videos."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError

from youtube_transcript_api import RequestBlocked


class RateLimitedError(RuntimeError):
    """YouTube rejected transcript requests because of request volume."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


def _retry_after_seconds(error: Exception) -> float | None:
    pending: list[BaseException] = [error]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        if isinstance(current, HTTPError) and current.code == 429:
            value = current.headers.get("Retry-After") if current.headers else None
            if value:
                try:
                    return max(0, float(value))
                except ValueError:
                    try:
                        retry_at = parsedate_to_datetime(value)
                        if retry_at.tzinfo is None:
                            retry_at = retry_at.replace(tzinfo=timezone.utc)
                        return max(0, (retry_at - datetime.now(timezone.utc)).total_seconds())
                    except (TypeError, ValueError, OverflowError):
                        pass
        if current.__cause__ is not None:
            pending.append(current.__cause__)
        if current.__context__ is not None:
            pending.append(current.__context__)
    return None


def _is_rate_limited(error: Exception) -> bool:
    """Recognize blocks from either transcript backend and chained HTTP errors."""
    seen: set[int] = set()
    pending: list[BaseException] = [error]
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        if isinstance(current, RequestBlocked):
            return True
        if isinstance(current, HTTPError) and current.code == 429:
            return True
        if re.search(r"\bHTTP(?: Error)?\s*429\b", str(current), re.IGNORECASE):
            return True
        if current.__cause__ is not None:
            pending.append(current.__cause__)
        if current.__context__ is not None:
            pending.append(current.__context__)
    return False


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
    # A block applies to both backends; immediately trying the fallback adds traffic.
    try:
        segments = _fetch_via_api(video_id, lang)
        if not segments:
            raise RuntimeError("Primary transcript source returned no text")
        return segments
    except Exception as error:
        if _is_rate_limited(error):
            raise RateLimitedError(
                f"YouTube transcript rate limit reached for video {video_id}. Retry later.",
                retry_after=_retry_after_seconds(error),
            ) from error

    # Fallback to yt-dlp subtitle extraction
    try:
        segments = _fetch_via_ytdlp(video_id, lang)
        if not segments:
            raise RuntimeError("Fallback transcript source returned no text")
        return segments
    except Exception as error:
        if _is_rate_limited(error):
            raise RateLimitedError(
                f"YouTube transcript rate limit reached for video {video_id}. Retry later.",
                retry_after=_retry_after_seconds(error),
            ) from error
        raise RuntimeError(
            f"Could not retrieve transcript for video {video_id} in '{lang}'."
        ) from error


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
