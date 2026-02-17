"""Unit tests for YouTube URL parsing."""

import unittest

from videocontext.url import extract_video_id, normalize_url


class TestUrlParsing(unittest.TestCase):
    def test_extract_video_id_valid_inputs(self):
        video_id = "dQw4w9WgXcQ"
        cases = [
            f"https://www.youtube.com/watch?v={video_id}",
            f"https://youtu.be/{video_id}",
            f"youtube.com/shorts/{video_id}",
            f"https://youtube.com/embed/{video_id}",
            f"https://youtube.com/v/{video_id}",
            video_id,
        ]
        for item in cases:
            with self.subTest(item=item):
                self.assertEqual(extract_video_id(item), video_id)

    def test_extract_video_id_invalid_inputs(self):
        cases = [
            "https://vimeo.com/123",
            "https://youtube.com/playlist?list=PL123",
            "not-a-url",
            "abc",
        ]
        for item in cases:
            with self.subTest(item=item):
                with self.assertRaises(ValueError):
                    extract_video_id(item)

    def test_normalize_url(self):
        self.assertEqual(
            normalize_url("dQw4w9WgXcQ"),
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        )


if __name__ == "__main__":
    unittest.main()
