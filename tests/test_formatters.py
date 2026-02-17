"""Unit tests for output formatters."""

import json
import unittest

from videocontext.extractors.metadata import Chapter, VideoMetadata
from videocontext.extractors.transcript import TranscriptSegment
from videocontext.formatters import json_fmt, markdown, text


def _sample_meta() -> VideoMetadata:
    return VideoMetadata(
        video_id="dQw4w9WgXcQ",
        title="Sample Title",
        channel="Sample Channel",
        duration=65,
        upload_date="2024-01-01",
        description=" Sample description ",
        chapters=[Chapter(start_time=0, title="Intro")],
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    )


def _sample_segments() -> list[TranscriptSegment]:
    return [TranscriptSegment(start=1.2, duration=2.0, text="hello world")]


class TestMarkdownFormatter(unittest.TestCase):
    def test_format_timestamp(self):
        self.assertEqual(markdown.format_timestamp(65), "1:05")
        self.assertEqual(markdown.format_timestamp(3665), "1:01:05")

    def test_format_full_contains_sections(self):
        output = markdown.format_full(_sample_meta(), _sample_segments())
        self.assertIn("# Video: Sample Title", output)
        self.assertIn("## Chapters", output)
        self.assertIn("## Description", output)
        self.assertIn("## Transcript", output)


class TestJsonFormatter(unittest.TestCase):
    def test_format_full_without_chapters(self):
        output = json_fmt.format_full(_sample_meta(), _sample_segments(), include_chapters=False)
        parsed = json.loads(output)
        self.assertNotIn("chapters", parsed)
        self.assertIn("transcript", parsed)
        self.assertEqual(parsed["transcript"][0]["text"], "hello world")


class TestTextFormatter(unittest.TestCase):
    def test_format_transcript_non_timestamped(self):
        output = text.format_transcript(_sample_segments())
        self.assertEqual(output, "hello world")

    def test_format_transcript_timestamped(self):
        output = text.format_transcript(_sample_segments(), timestamped=True)
        self.assertEqual(output, "[0:01] hello world")

    def test_format_full_without_chapters(self):
        output = text.format_full(_sample_meta(), _sample_segments(), include_chapters=False)
        self.assertNotIn("Chapters:", output)
        self.assertIn("Transcript:", output)


if __name__ == "__main__":
    unittest.main()
