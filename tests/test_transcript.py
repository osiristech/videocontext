"""Transcript extraction failures exposed to callers."""

import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from youtube_transcript_api import RequestBlocked

from videocontext.extractors.transcript import RateLimitedError, TranscriptSegment, fetch_transcript


class TestTranscriptFailures(unittest.TestCase):
    @patch("videocontext.extractors.transcript._fetch_via_ytdlp")
    @patch("videocontext.extractors.transcript._fetch_via_api")
    def test_empty_primary_uses_fallback_instead_of_saving_blank_transcript(self, api, ytdlp):
        api.return_value = []
        ytdlp.return_value = [TranscriptSegment(start=0, duration=1, text="fallback text")]

        result = fetch_transcript("dQw4w9WgXcQ")

        self.assertEqual(result[0].text, "fallback text")

    @patch("videocontext.extractors.transcript._fetch_via_ytdlp")
    @patch("videocontext.extractors.transcript._fetch_via_api")
    def test_http_retry_after_is_carried_to_batch_scheduler(self, api, ytdlp):
        api.side_effect = HTTPError(
            "https://example.test", 429, "Too Many Requests", {"Retry-After": "90"}, None,
        )

        with self.assertRaises(RateLimitedError) as caught:
            fetch_transcript("dQw4w9WgXcQ")

        self.assertEqual(caught.exception.retry_after, 90)
        ytdlp.assert_not_called()

    @patch("videocontext.extractors.transcript._fetch_via_ytdlp")
    @patch("videocontext.extractors.transcript._fetch_via_api")
    def test_blocked_primary_does_not_make_fallback_request(self, api, ytdlp):
        api.side_effect = RequestBlocked("dQw4w9WgXcQ")

        with self.assertRaisesRegex(RuntimeError, "rate limit"):
            fetch_transcript("dQw4w9WgXcQ")

        ytdlp.assert_not_called()

    @patch("videocontext.extractors.transcript._fetch_via_ytdlp")
    @patch("videocontext.extractors.transcript._fetch_via_api")
    def test_fallback_http_429_is_reported_as_rate_limit(self, api, ytdlp):
        api.side_effect = RuntimeError("primary failed")
        ytdlp.side_effect = RuntimeError("HTTP Error 429: Too Many Requests")

        with self.assertRaisesRegex(RuntimeError, "rate limit"):
            fetch_transcript("dQw4w9WgXcQ")


if __name__ == "__main__":
    unittest.main()
