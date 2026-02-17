"""YouTube URL parser and normalizer."""

import re
from urllib.parse import parse_qs, urlparse

# Matches bare 11-char YouTube video IDs
VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")


def extract_video_id(url_or_id: str) -> str:
    """Extract a YouTube video ID from various URL formats or a bare ID.

    Supports:
        - https://www.youtube.com/watch?v=ID
        - https://youtu.be/ID
        - https://youtube.com/shorts/ID
        - https://youtube.com/embed/ID
        - https://youtube.com/v/ID
        - https://www.youtube.com/playlist?list=PLID (raises ValueError)
        - Bare 11-character video IDs

    Returns:
        The 11-character video ID.

    Raises:
        ValueError: If the URL/ID cannot be parsed.
    """
    text = url_or_id.strip()

    # Bare video ID
    if VIDEO_ID_PATTERN.match(text):
        return text

    parsed = urlparse(text)

    # Add scheme if missing so urlparse works
    if not parsed.scheme:
        parsed = urlparse(f"https://{text}")

    hostname = (parsed.hostname or "").lower().replace("www.", "")

    if hostname not in ("youtube.com", "youtu.be", "m.youtube.com", "music.youtube.com"):
        raise ValueError(f"Not a YouTube URL: {url_or_id}")

    # youtu.be/ID
    if hostname == "youtu.be":
        video_id = parsed.path.lstrip("/").split("/")[0]
        if VIDEO_ID_PATTERN.match(video_id):
            return video_id
        raise ValueError(f"Could not extract video ID from: {url_or_id}")

    # /watch?v=ID
    if parsed.path == "/watch":
        params = parse_qs(parsed.query)
        if "v" in params:
            video_id = params["v"][0]
            if VIDEO_ID_PATTERN.match(video_id):
                return video_id
        raise ValueError(f"Could not extract video ID from: {url_or_id}")

    # /shorts/ID, /embed/ID, /v/ID
    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) >= 2 and path_parts[0] in ("shorts", "embed", "v", "live"):
        video_id = path_parts[1]
        if VIDEO_ID_PATTERN.match(video_id):
            return video_id

    raise ValueError(
        f"Could not extract video ID from: {url_or_id}\n"
        "Supported formats: YouTube URLs, youtu.be links, shorts, or 11-character video IDs."
    )


def normalize_url(video_id: str) -> str:
    """Return the canonical YouTube URL for a video ID."""
    return f"https://www.youtube.com/watch?v={video_id}"
