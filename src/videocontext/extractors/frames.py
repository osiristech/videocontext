"""Frame extraction from YouTube videos (requires [vision] extras)."""

from __future__ import annotations

import tempfile
from pathlib import Path


def extract_frames(video_id: str, output_dir: str, interval: float | None = None, max_frames: int = 20) -> list[str]:
    """Extract key frames from a video.

    Requires the [vision] optional dependency: pip install videocontext[vision]

    Args:
        video_id: YouTube video ID.
        output_dir: Directory to save extracted frames.
        interval: Seconds between frames. If None, uses scene detection.
        max_frames: Maximum number of frames to extract.

    Returns:
        List of paths to extracted frame images.

    Raises:
        ImportError: If scenedetect is not installed.
        RuntimeError: If frame extraction fails.
    """
    if max_frames < 1:
        raise RuntimeError("max_frames must be at least 1")

    if interval is not None and interval <= 0:
        raise RuntimeError("interval must be greater than 0")

    _ensure_vision_dependencies()
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        video_path, duration = _download_video(video_id, Path(tmpdir))

        if interval is not None:
            timestamps = _build_interval_timestamps(duration, interval, max_frames)
        else:
            timestamps = _build_scene_timestamps(video_path, max_frames)

        if not timestamps:
            raise RuntimeError("No candidate timestamps generated for frame extraction")

        paths = _extract_frames_at_timestamps(video_path, out_dir, video_id, timestamps)
        if not paths:
            raise RuntimeError("Could not extract any frames from video")
        return paths


def _ensure_vision_dependencies() -> None:
    try:
        import cv2  # noqa: F401
        import scenedetect  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "Frame extraction requires the [vision] extra.\n"
            "Install it with: pip install videocontext[vision]"
        ) from e


def _download_video(video_id: str, tmpdir: Path) -> tuple[Path, float]:
    import yt_dlp

    from videocontext.network import yt_dlp_proxy_options

    url = f"https://www.youtube.com/watch?v={video_id}"
    opts = {
        # Prefer single-file H.264 variants first to avoid AV1 decode issues
        # in OpenCV environments without AV1 support.
        "format": "best[ext=mp4][vcodec*=avc1]/best[vcodec*=avc1]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "outtmpl": str(tmpdir / "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    opts.update(yt_dlp_proxy_options())
    proxy_active = "proxy" in opts

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = Path(ydl.prepare_filename(info))
    except Exception as e:
        if proxy_active:
            raise RuntimeError(f"Could not download video {video_id} for frame extraction") from e
        raise RuntimeError(f"Could not download video {video_id} for frame extraction: {e}") from e

    if not file_path.exists():
        matches = sorted(tmpdir.glob(f"{video_id}.*"))
        if not matches:
            raise RuntimeError("Video download completed but output file was not found")
        file_path = matches[0]

    duration = float(info.get("duration") or 0.0)
    return file_path, duration


def _build_interval_timestamps(duration: float, interval: float, max_frames: int) -> list[float]:
    timestamps: list[float] = []
    current = 0.0

    if duration <= 0:
        while len(timestamps) < max_frames:
            timestamps.append(current)
            current += interval
        return timestamps

    while current < duration and len(timestamps) < max_frames:
        timestamps.append(current)
        current += interval

    if not timestamps:
        timestamps.append(0.0)

    return timestamps


def _build_scene_timestamps(video_path: Path, max_frames: int) -> list[float]:
    from scenedetect import SceneManager, open_video
    from scenedetect.detectors import ContentDetector

    video = open_video(str(video_path))
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector())
    scene_manager.detect_scenes(video)
    scene_list = scene_manager.get_scene_list()

    timestamps: list[float] = []
    for start, end in scene_list:
        start_s = start.get_seconds()
        end_s = end.get_seconds()
        timestamps.append((start_s + end_s) / 2.0)
        if len(timestamps) >= max_frames:
            break

    if not timestamps:
        # Fallback to one frame from the beginning if no scenes are detected.
        return [0.0]

    return timestamps


def _extract_frames_at_timestamps(
    video_path: Path,
    output_dir: Path,
    video_id: str,
    timestamps: list[float],
) -> list[str]:
    import cv2

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open downloaded video file: {video_path}")

    fps = capture.get(cv2.CAP_PROP_FPS) or 0.0
    output_paths: list[str] = []

    try:
        for idx, ts in enumerate(timestamps, start=1):
            if fps > 0:
                frame_idx = int(ts * fps)
                capture.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            else:
                capture.set(cv2.CAP_PROP_POS_MSEC, ts * 1000.0)

            ok, frame = capture.read()
            if not ok or frame is None:
                continue

            out_path = output_dir / f"{video_id}_{idx:03d}_{int(ts * 1000)}ms.jpg"
            written = cv2.imwrite(str(out_path), frame)
            if written:
                output_paths.append(str(out_path))
    finally:
        capture.release()

    return output_paths
