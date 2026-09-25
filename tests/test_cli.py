"""CLI behavior tests with mocked extractors."""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from videocontext.cli import cli
from videocontext.extractors.metadata import VideoMetadata
from videocontext.extractors.transcript import TranscriptSegment
from videocontext.extractors.transcript import RateLimitedError


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

    def test_save_invalid_url_returns_error(self):
        result = self.runner.invoke(cli, ["save", "not-a-youtube-url"])
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

    @patch("videocontext.batch.fetch_transcript")
    def test_batch_transcripts_saves_and_resumes_without_refetching(self, mock_fetch):
        mock_fetch.return_value = [TranscriptSegment(start=0.0, duration=1.0, text="hello")]
        with tempfile.TemporaryDirectory() as tmp:
            ids = Path(tmp) / "ids.txt"
            ids.write_text("00000000001\n00000000002\n", encoding="utf-8")
            titles = Path(tmp) / "titles.tsv"
            titles.write_text("00000000001\tFirst video\n00000000002\tSecond video\n", encoding="utf-8")
            out = Path(tmp) / "out"
            args = ["batch-transcripts", str(ids), "--titles-file", str(titles),
                    "--output-dir", str(out), "--interval", "0"]

            first = self.runner.invoke(cli, args)
            self.assertEqual(first.exit_code, 0, first.output)
            self.assertEqual((out / "transcripts" / "First video [00000000001].txt").read_text(), "hello\n")
            self.assertEqual((out / "transcripts" / "Second video [00000000002].txt").read_text(), "hello\n")

            mock_fetch.reset_mock(side_effect=True)
            mock_fetch.side_effect = AssertionError("completed transcript fetched again")
            second = self.runner.invoke(cli, args)
            self.assertEqual(second.exit_code, 0, second.output)
            self.assertIn("2 skipped", second.output)
            status = self.runner.invoke(cli, ["batch-transcripts", str(ids), "--output-dir", str(out), "--status"])
            self.assertEqual(status.exit_code, 0, status.output)
            self.assertIn("2 saved", status.output)
            self.assertIn("0 pending", status.output)

    @patch("videocontext.batch.fetch_transcript")
    def test_batch_rate_limit_pause_uses_distinct_exit_status(self, mock_fetch):
        mock_fetch.side_effect = RateLimitedError("rate limit")
        with tempfile.TemporaryDirectory() as tmp:
            ids = Path(tmp) / "ids.txt"
            ids.write_text("00000000001\n", encoding="utf-8")
            titles = Path(tmp) / "titles.tsv"
            titles.write_text("00000000001\tFirst video\n", encoding="utf-8")
            result = self.runner.invoke(cli, [
                "batch-transcripts", str(ids), "--output-dir", str(Path(tmp) / "out"),
                "--titles-file", str(titles),
                "--max-rate-retries", "0",
            ])
            self.assertEqual(result.exit_code, 75, result.output)
            self.assertIn("resume later", result.output)

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

    @patch("videocontext.extractors.frames.extract_frames")
    def test_frames_runtime_error(self, mock_extract_frames):
        mock_extract_frames.side_effect = RuntimeError("decode failed")

        result = self.runner.invoke(cli, ["frames", self.video_url])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Error:", result.output)
        self.assertIn("decode failed", result.output)

    @patch("videocontext.bundle.save_bundle")
    def test_save_success_prints_bundle_files(self, mock_save_bundle):
        mock_save_bundle.return_value = {
            "output_dir": "out/dQw4w9WgXcQ",
            "files": ["context.md", "manifest.json"],
            "warnings": [],
        }

        result = self.runner.invoke(cli, ["save", self.video_url, "--output-dir", "out"])

        self.assertEqual(result.exit_code, 0)
        mock_save_bundle.assert_called_once_with(
            "dQw4w9WgXcQ",
            output_dir="out",
            lang="en",
            overwrite=False,
        )
        self.assertIn("Saved bundle to out/dQw4w9WgXcQ", result.output)
        self.assertIn("out/dQw4w9WgXcQ/context.md", result.output)

    @patch("videocontext.bundle.save_bundle")
    def test_save_prints_transcript_warning(self, mock_save_bundle):
        mock_save_bundle.return_value = {
            "output_dir": "out/dQw4w9WgXcQ",
            "files": ["context.md"],
            "warnings": ["transcript unavailable"],
        }

        result = self.runner.invoke(cli, ["save", self.video_url])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Warning:", result.output)
        self.assertIn("transcript unavailable", result.output)

    @patch("videocontext.bundle.save_bundle")
    def test_save_existing_bundle_returns_error(self, mock_save_bundle):
        from videocontext.bundle import BundleExistsError

        mock_save_bundle.side_effect = BundleExistsError("Output folder already exists")

        result = self.runner.invoke(cli, ["save", self.video_url])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Output folder already exists", result.output)

    @patch("videocontext.bundle.open_folder")
    @patch("videocontext.bundle.save_bundle")
    def test_save_open_opens_bundle_folder(self, mock_save_bundle, mock_open_folder):
        mock_save_bundle.return_value = {
            "output_dir": "out/dQw4w9WgXcQ",
            "files": [],
            "warnings": [],
        }

        result = self.runner.invoke(cli, ["save", self.video_url, "--open"])

        self.assertEqual(result.exit_code, 0)
        mock_open_folder.assert_called_once_with("out/dQw4w9WgXcQ")


if __name__ == "__main__":
    unittest.main()
