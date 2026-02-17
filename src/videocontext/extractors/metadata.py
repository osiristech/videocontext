"""Video metadata extraction using yt-dlp."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Chapter:
    """A chapter marker in a video."""
    start_time: float
    title: str


@dataclass
class VideoMetadata:
    """Metadata for a YouTube video."""
    video_id: str
    title: str
    channel: str
    duration: int  # seconds
    upload_date: str  # YYYY-MM-DD
    description: str
    view_count: int | None = None
    like_count: int | None = None
    tags: list[str] = field(default_factory=list)
    chapters: list[Chapter] = field(default_factory=list)
    url: str = ""


def fetch_metadata(video_id: str) -> VideoMetadata:
    """Fetch video metadata using yt-dlp without downloading the video.

    Args:
        video_id: The 11-character YouTube video ID.

    Returns:
        VideoMetadata object.

    Raises:
        RuntimeError: If metadata cannot be retrieved.
    """
    import yt_dlp

    url = f"https://www.youtube.com/watch?v={video_id}"

    opts = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        raise RuntimeError(f"Could not retrieve metadata for video {video_id}: {e}") from e

    if info is None:
        raise RuntimeError(f"No metadata returned for video {video_id}")

    return _metadata_from_info(video_id, info)


def _format_upload_date(raw_date: str) -> str:
    if len(raw_date) == 8:
        return f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
    return raw_date


def _metadata_from_info(video_id: str, info: dict) -> VideoMetadata:
    url = f"https://www.youtube.com/watch?v={video_id}"

    # Parse chapters
    chapters = [
        Chapter(
            start_time=ch.get("start_time", 0),
            title=ch.get("title", ""),
        )
        for ch in info.get("chapters", None) or []
    ]

    return VideoMetadata(
        video_id=video_id,
        title=info.get("title", "Unknown"),
        channel=info.get("channel", info.get("uploader", "Unknown")),
        duration=int(info.get("duration", 0)),
        upload_date=_format_upload_date(info.get("upload_date", "")),
        description=info.get("description", ""),
        view_count=info.get("view_count"),
        like_count=info.get("like_count"),
        tags=info.get("tags", None) or [],
        chapters=chapters,
        url=url,
    )
