"""Bulk transcript downloads with resumable local results."""

import json
import tempfile
import unittest
from pathlib import Path

from videocontext.batch import BatchPaused, download_transcripts, inspect_batch
from videocontext.extractors.transcript import RateLimitedError, TranscriptSegment


def _segments(text: str) -> list[TranscriptSegment]:
    return [TranscriptSegment(start=0.0, duration=1.0, text=text)]


def _titles(ids: Path) -> Path:
    path = ids.with_suffix(".tsv")
    path.write_text(
        "".join(f"{video_id}\t{video_id}\n" for video_id in ids.read_text().splitlines()),
        encoding="utf-8",
    )
    return path


def _named(output_dir: Path, video_id: str) -> Path:
    return output_dir / "transcripts" / f"{video_id} [{video_id}].txt"


class TestBatchTranscripts(unittest.TestCase):
    def test_processes_more_than_215_ids_and_skips_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ids = root / "ids.txt"
            videos = [f"{number:011d}" for number in range(220)]
            ids.write_text("\n".join([*videos, videos[0]]) + "\n", encoding="utf-8")
            out = root / "transcripts"
            out.mkdir()
            (out / f"{videos[0]}.txt").write_text("existing\n", encoding="utf-8")
            fetched = []

            def fetch(video_id, lang):
                fetched.append(video_id)
                return _segments(video_id)

            summary = download_transcripts(
                ids, out, interval=0, fetcher=fetch, sleeper=lambda _: None,
                titles_file=_titles(ids),
            )

            self.assertEqual(summary.total, 220)
            self.assertEqual(summary.completed, 219)
            self.assertEqual(summary.skipped, 1)
            self.assertEqual(summary.failed, 0)
            self.assertEqual(len(fetched), 219)
            self.assertEqual(_named(out, videos[0]).read_text(), "existing\n")
            self.assertEqual(_named(out, videos[-1]).read_text(), f"{videos[-1]}\n")
            self.assertEqual(inspect_batch(ids, out).saved, 220)

    def test_blank_existing_output_is_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ids = root / "ids.txt"
            ids.write_text("00000000001\n", encoding="utf-8")
            out = root / "out"
            out.mkdir()
            (out / "00000000001.txt").write_text("\n", encoding="utf-8")

            self.assertEqual(inspect_batch(ids, out).pending, 1)

    def test_empty_fetch_is_failure_not_saved_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ids = root / "ids.txt"
            ids.write_text("00000000001\n", encoding="utf-8")
            out = root / "out"

            summary = download_transcripts(
                ids, out, interval=0, fetcher=lambda video_id, lang: [], sleeper=lambda _: None,
                titles_file=_titles(ids),
            )

            self.assertEqual(summary.failed, 1)
            self.assertEqual(inspect_batch(ids, out).pending, 1)
            self.assertFalse((out / "00000000001.txt").exists())

    def test_rate_limit_waits_and_retries_same_video_before_next(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ids = root / "ids.txt"
            ids.write_text("00000000001\n00000000002\n", encoding="utf-8")
            attempts = []
            waits = []

            def fetch(video_id, lang):
                attempts.append(video_id)
                if len(attempts) == 1:
                    raise RateLimitedError("rate limit")
                return _segments(video_id)

            summary = download_transcripts(
                ids, root / "out", interval=2, initial_cooldown=30,
                fetcher=fetch, sleeper=waits.append, titles_file=_titles(ids),
            )

            self.assertEqual(attempts, ["00000000001", "00000000001", "00000000002"])
            self.assertEqual(waits, [30, 2])
            self.assertEqual(summary.rate_limit_retries, 1)
            self.assertEqual(summary.completed, 2)

    def test_retry_after_longer_than_backoff_is_respected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ids = root / "ids.txt"
            ids.write_text("00000000001\n", encoding="utf-8")
            waits = []
            attempts = 0

            def fetch(video_id, lang):
                nonlocal attempts
                attempts += 1
                if attempts == 1:
                    raise RateLimitedError("rate limit", retry_after=90)
                return _segments("recovered")

            download_transcripts(
                ids, root / "out", interval=0, initial_cooldown=30,
                fetcher=fetch, sleeper=waits.append, titles_file=_titles(ids),
            )

            self.assertEqual(waits, [90])

    def test_repeated_rate_limit_pauses_without_advancing_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ids = root / "ids.txt"
            ids.write_text("00000000001\n00000000002\n", encoding="utf-8")
            attempts = []
            waits = []

            def fetch(video_id, lang):
                attempts.append(video_id)
                raise RateLimitedError("rate limit")

            with self.assertRaises(BatchPaused) as caught:
                download_transcripts(
                    ids, root / "out", interval=0, initial_cooldown=10,
                    max_rate_retries=2, fetcher=fetch, sleeper=waits.append,
                    titles_file=_titles(ids),
                )

            self.assertEqual(caught.exception.video_id, "00000000001")
            self.assertEqual(attempts, ["00000000001", "00000000001", "00000000001"])
            self.assertEqual(waits, [10, 20])
            self.assertFalse((root / "out" / "00000000002.txt").exists())

    def test_non_rate_failure_is_logged_and_next_video_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ids = root / "ids.txt"
            ids.write_text("00000000001\n00000000002\n", encoding="utf-8")
            out = root / "out"

            def fetch(video_id, lang):
                if video_id == "00000000001":
                    raise RuntimeError("No captions found")
                return _segments("second")

            summary = download_transcripts(
                ids, out, interval=0, fetcher=fetch, sleeper=lambda _: None,
                titles_file=_titles(ids),
            )

            self.assertEqual((summary.completed, summary.failed), (1, 1))
            self.assertFalse((out / "00000000001.txt").exists())
            self.assertEqual(_named(out, "00000000002").read_text(), "second\n")
            failures = [json.loads(line) for line in (out / "logs" / "batch_failures.jsonl").read_text().splitlines()]
            self.assertEqual(failures[0]["video_id"], "00000000001")
            self.assertIn("No captions found", failures[0]["error"])

    def test_invalid_id_fails_before_fetching_any_video(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ids = root / "ids.txt"
            ids.write_text("00000000001\nnot a video\n", encoding="utf-8")
            fetched = []

            with self.assertRaisesRegex(ValueError, "line 2"):
                download_transcripts(
                    ids, root / "out", interval=0,
                    fetcher=lambda video_id, lang: fetched.append(video_id),
                    titles_file=_titles(ids),
                )

            self.assertEqual(fetched, [])


if __name__ == "__main__":
    unittest.main()
