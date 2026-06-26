"""Tests for saved VideoContext artifact bundles."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from videocontext.bundle import BundleExistsError, save_bundle
from videocontext.extractors.metadata import VideoMetadata
from videocontext.extractors.transcript import TranscriptSegment


def _sample_meta() -> VideoMetadata:
    return VideoMetadata(
        video_id="dQw4w9WgXcQ",
        title="Sample Title",
        channel="Sample Channel",
        duration=65,
        upload_date="2024-01-01",
        description="Sample description",
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    )


def _sample_segments() -> list[TranscriptSegment]:
    return [TranscriptSegment(start=1.0, duration=2.0, text="hello world")]


class TestSaveBundle(unittest.TestCase):
    @patch("videocontext.bundle.fetch_transcript")
    @patch("videocontext.bundle.fetch_metadata")
    def test_save_bundle_writes_expected_artifacts(self, mock_fetch_metadata, mock_fetch_transcript):
        mock_fetch_metadata.return_value = _sample_meta()
        mock_fetch_transcript.return_value = _sample_segments()

        with self.subTest("bundle files"):
            with tempfile.TemporaryDirectory() as tmpdir:
                output_root = Path(tmpdir)
                manifest = save_bundle("dQw4w9WgXcQ", output_dir=str(output_root))
                bundle_dir = output_root / "dQw4w9WgXcQ"

                expected = {
                    "metadata.json",
                    "metadata.md",
                    "transcript.txt",
                    "transcript.md",
                    "transcript.json",
                    "context.md",
                    "context.html",
                    "manifest.json",
                }
                self.assertTrue(bundle_dir.exists())
                self.assertEqual(set(manifest["files"]), expected)
                self.assertTrue((bundle_dir / "context.html").read_text(encoding="utf-8").startswith("<!DOCTYPE html>"))

                parsed_manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(parsed_manifest["video_id"], "dQw4w9WgXcQ")
                self.assertTrue(parsed_manifest["transcript"]["available"])
                self.assertEqual(parsed_manifest["warnings"], [])

    @patch("videocontext.bundle.fetch_transcript")
    @patch("videocontext.bundle.fetch_metadata")
    def test_save_bundle_preserves_metadata_when_transcript_fails(
        self,
        mock_fetch_metadata,
        mock_fetch_transcript,
    ):
        mock_fetch_metadata.return_value = _sample_meta()
        mock_fetch_transcript.side_effect = RuntimeError("transcript unavailable")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir)
            manifest = save_bundle("dQw4w9WgXcQ", output_dir=str(output_root))
            bundle_dir = output_root / "dQw4w9WgXcQ"

            self.assertFalse(manifest["transcript"]["available"])
            self.assertIn("transcript unavailable", manifest["warnings"][0])
            self.assertTrue((bundle_dir / "metadata.json").exists())
            self.assertTrue((bundle_dir / "context.md").exists())
            self.assertFalse((bundle_dir / "transcript.txt").exists())

    @patch("videocontext.bundle.fetch_transcript")
    @patch("videocontext.bundle.fetch_metadata")
    def test_save_bundle_requires_overwrite_for_existing_folder(
        self,
        mock_fetch_metadata,
        mock_fetch_transcript,
    ):
        mock_fetch_metadata.return_value = _sample_meta()
        mock_fetch_transcript.return_value = _sample_segments()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir)
            save_bundle("dQw4w9WgXcQ", output_dir=str(output_root))
            with self.assertRaises(BundleExistsError):
                save_bundle("dQw4w9WgXcQ", output_dir=str(output_root))

            manifest = save_bundle("dQw4w9WgXcQ", output_dir=str(output_root), overwrite=True)
            self.assertEqual(manifest["video_id"], "dQw4w9WgXcQ")

    @patch("videocontext.bundle.fetch_metadata")
    def test_overwrite_keeps_existing_bundle_when_metadata_fails(self, mock_fetch_metadata):
        mock_fetch_metadata.side_effect = RuntimeError("metadata unavailable")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir)
            bundle_dir = output_root / "dQw4w9WgXcQ"
            bundle_dir.mkdir(parents=True)
            sentinel = bundle_dir / "context.md"
            sentinel.write_text("existing bundle", encoding="utf-8")

            with self.assertRaises(RuntimeError):
                save_bundle("dQw4w9WgXcQ", output_dir=str(output_root), overwrite=True)

            self.assertEqual(sentinel.read_text(encoding="utf-8"), "existing bundle")


if __name__ == "__main__":
    unittest.main()
