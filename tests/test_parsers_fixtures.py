"""Fixture-driven tests for metadata/transcript parsing."""

import json
import unittest
from pathlib import Path

from videocontext.extractors.metadata import _format_upload_date, _metadata_from_info
from videocontext.extractors.transcript import _parse_json3_transcript

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestMetadataParsing(unittest.TestCase):
    def test_format_upload_date(self):
        self.assertEqual(_format_upload_date("20260115"), "2026-01-15")
        self.assertEqual(_format_upload_date("2026-01-15"), "2026-01-15")
        self.assertEqual(_format_upload_date(""), "")

    def test_metadata_from_fixture(self):
        info = json.loads((FIXTURES_DIR / "metadata_info.json").read_text(encoding="utf-8"))
        meta = _metadata_from_info("dQw4w9WgXcQ", info)

        self.assertEqual(meta.video_id, "dQw4w9WgXcQ")
        self.assertEqual(meta.title, "Fixture Video")
        self.assertEqual(meta.channel, "Fixture Channel")
        self.assertEqual(meta.duration, 372)
        self.assertEqual(meta.upload_date, "2026-01-15")
        self.assertEqual(meta.description, "A fixture description.")
        self.assertEqual(meta.tags, ["python", "cli", "testing"])
        self.assertEqual(len(meta.chapters), 2)
        self.assertEqual(meta.chapters[1].title, "Implementation")


class TestTranscriptParsing(unittest.TestCase):
    def test_parse_json3_fixture(self):
        data = json.loads((FIXTURES_DIR / "transcript.json3").read_text(encoding="utf-8"))
        segments = _parse_json3_transcript(data)

        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0].start, 0.0)
        self.assertEqual(segments[0].duration, 1.5)
        self.assertEqual(segments[0].text, "Hello world")
        self.assertEqual(segments[1].start, 4.5)
        self.assertEqual(segments[1].duration, 2.5)
        self.assertEqual(segments[1].text, "Second line")


if __name__ == "__main__":
    unittest.main()
