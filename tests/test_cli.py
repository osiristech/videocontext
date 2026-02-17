"""CLI behavior tests with mocked extractors."""

import unittest
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from videocontext.cli import cli
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


class TestCli(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    def test_invalid_url_returns_error(self):
        result = self.runner.invoke(cli, ["metadata", "not-a-youtube-url"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Not a YouTube URL", result.output)

    @patch("videocontext.extractors.metadata.fetch_metadata")
    @patch("videocontext.extractors.transcript.fetch_transcript")
    def test_context_continues_without_transcript(self, mock_fetch_transcript, mock_fetch_metadata):
        mock_fetch_metadata.return_value = _sample_meta()
        mock_fetch_transcript.side_effect = RuntimeError("transcript unavailable")

        result = self.runner.invoke(cli, ["context", self.video_url, "-f", "text"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Warning:", result.output)
        self.assertIn("Continuing without transcript.", result.output)
        self.assertIn("Sample Title", result.output)

    @patch("videocontext.extractors.transcript.fetch_transcript")
    def test_transcript_json_output(self, mock_fetch_transcript):
        mock_fetch_transcript.return_value = [TranscriptSegment(start=1.0, duration=2.0, text="hello")]

        result = self.runner.invoke(cli, ["transcript", self.video_url, "-f", "json"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn('"text": "hello"', result.output)

    @patch("videocontext.extractors.metadata.fetch_metadata")
    def test_metadata_writes_output_file(self, mock_fetch_metadata):
        mock_fetch_metadata.return_value = _sample_meta()

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ["metadata", self.video_url, "-o", "metadata.md"])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Written to metadata.md", result.output)

            content = Path("metadata.md").read_text(encoding="utf-8")
            self.assertIn("# Video: Sample Title", content)
            self.assertTrue(content.endswith("\n"))

    @patch("videocontext.extractors.frames.extract_frames")
    def test_frames_success_prints_paths(self, mock_extract_frames):
        mock_extract_frames.return_value = ["frames/1.jpg", "frames/2.jpg"]

        result = self.runner.invoke(cli, ["frames", self.video_url, "--max-frames", "2"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("frames/1.jpg", result.output)
        self.assertIn("frames/2.jpg", result.output)

    @patch("videocontext.extractors.frames.extract_frames")
    def test_frames_import_error(self, mock_extract_frames):
        mock_extract_frames.side_effect = ImportError("missing extra")

        result = self.runner.invoke(cli, ["frames", self.video_url])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Error:", result.output)
        self.assertIn("missing extra", result.output)

    @patch("videocontext.extractors.frames.extract_frames")
    def test_frames_not_implemented_is_non_fatal(self, mock_extract_frames):
        mock_extract_frames.side_effect = NotImplementedError("not ready yet")

        result = self.runner.invoke(cli, ["frames", self.video_url])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("not ready yet", result.output)


if __name__ == "__main__":
    unittest.main()
