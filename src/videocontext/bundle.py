"""Save complete VideoContext artifact bundles."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from videocontext.extractors.metadata import VideoMetadata, fetch_metadata
from videocontext.extractors.transcript import TranscriptSegment, fetch_transcript
from videocontext.formatters import html, json_fmt, markdown
from videocontext.url import normalize_url


class BundleExistsError(RuntimeError):
    """Raised when a bundle already exists and overwrite was not requested."""


def save_bundle(
    video_id: str,
    output_dir: str = "./videocontext-output",
    lang: str = "en",
    overwrite: bool = False,
) -> dict:
    """Save a complete artifact bundle for a YouTube video."""
    root = Path(output_dir)
    bundle_dir = root / video_id

    if bundle_dir.exists():
        if not overwrite:
            raise BundleExistsError(
                f"Output folder already exists: {bundle_dir}\n"
                "Use --overwrite to replace generated files."
            )

    meta = fetch_metadata(video_id)
    segments: list[TranscriptSegment] | None = None
    warnings: list[str] = []

    try:
        segments = fetch_transcript(video_id, lang=lang)
    except RuntimeError as e:
        warnings.append(str(e))

    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    files = _write_artifacts(bundle_dir, meta, segments)
    files = sorted([*files, "manifest.json"])
    manifest = _build_manifest(
        bundle_dir=bundle_dir,
        meta=meta,
        lang=lang,
        files=files,
        transcript_available=segments is not None,
        warnings=warnings,
    )

    manifest_path = bundle_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return manifest


def open_folder(path: str | Path) -> None:
    """Open a folder in the platform file manager."""
    subprocess.Popen(["xdg-open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _write_artifacts(
    bundle_dir: Path,
    meta: VideoMetadata,
    segments: list[TranscriptSegment] | None,
) -> list[str]:
    files: list[str] = []

    artifacts = {
        "metadata.json": json_fmt.format_metadata(meta),
        "metadata.md": markdown.format_metadata(meta),
        "context.md": markdown.format_full(meta, segments),
        "context.html": html.format_full(meta, segments),
    }

    if segments is not None:
        artifacts.update({
            "transcript.txt": "\n".join(seg.text for seg in segments),
            "transcript.md": markdown.format_transcript(segments, timestamped=True),
            "transcript.json": json_fmt.format_transcript(segments),
        })

    for filename, content in artifacts.items():
        (bundle_dir / filename).write_text(content + "\n", encoding="utf-8")
        files.append(filename)

    return sorted(files)


def _build_manifest(
    bundle_dir: Path,
    meta: VideoMetadata,
    lang: str,
    files: list[str],
    transcript_available: bool,
    warnings: list[str],
) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "video_id": meta.video_id,
        "source_url": meta.url or normalize_url(meta.video_id),
        "title": meta.title,
        "channel": meta.channel,
        "language": lang,
        "output_dir": str(bundle_dir),
        "files": files,
        "transcript": {
            "available": transcript_available,
        },
        "metadata": asdict(meta),
        "warnings": warnings,
    }
