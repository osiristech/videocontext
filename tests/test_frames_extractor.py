"""Unit tests for frames extractor orchestration and helpers."""

import unittest
from pathlib import Path
from unittest.mock import patch

from videocontext.extractors import frames


class TestFrameTimestamps(unittest.TestCase):
    def test_interval_timestamps_with_duration(self):
        got = frames._build_interval_timestamps(duration=10.0, interval=3.0, max_frames=10)
        self.assertEqual(got, [0.0, 3.0, 6.0, 9.0])

    def test_interval_timestamps_caps_by_max_frames(self):
        got = frames._build_interval_timestamps(duration=20.0, interval=2.0, max_frames=3)
        self.assertEqual(got, [0.0, 2.0, 4.0])

    def test_interval_timestamps_without_duration(self):
        got = frames._build_interval_timestamps(duration=0.0, interval=5.0, max_frames=3)
        self.assertEqual(got, [0.0, 5.0, 10.0])


class TestExtractFrames(unittest.TestCase):
    @patch("videocontext.extractors.frames._extract_frames_at_timestamps")
    @patch("videocontext.extractors.frames._build_scene_timestamps")
    @patch("videocontext.extractors.frames._build_interval_timestamps")
    @patch("videocontext.extractors.frames._download_video")
    @patch("videocontext.extractors.frames._ensure_vision_dependencies")
    def test_extract_frames_uses_interval_mode(
        self,
        mock_deps,
        mock_download,
        mock_build_interval,
        mock_build_scene,
        mock_extract,
    ):
        mock_download.return_value = (Path("/tmp/video.mp4"), 20.0)
        mock_build_interval.return_value = [0.0, 5.0]
        mock_extract.return_value = ["frames/a.jpg", "frames/b.jpg"]

        got = frames.extract_frames("dQw4w9WgXcQ", "./frames", interval=5.0, max_frames=2)

        self.assertEqual(got, ["frames/a.jpg", "frames/b.jpg"])
        mock_build_interval.assert_called_once_with(20.0, 5.0, 2)
        mock_build_scene.assert_not_called()

    @patch("videocontext.extractors.frames._extract_frames_at_timestamps")
    @patch("videocontext.extractors.frames._build_scene_timestamps")
    @patch("videocontext.extractors.frames._download_video")
    @patch("videocontext.extractors.frames._ensure_vision_dependencies")
    def test_extract_frames_uses_scene_mode(
        self,
        mock_deps,
        mock_download,
        mock_build_scene,
        mock_extract,
    ):
        mock_download.return_value = (Path("/tmp/video.mp4"), 20.0)
        mock_build_scene.return_value = [1.2, 9.9]
        mock_extract.return_value = ["frames/a.jpg"]

        got = frames.extract_frames("dQw4w9WgXcQ", "./frames", interval=None, max_frames=5)

        self.assertEqual(got, ["frames/a.jpg"])
        mock_build_scene.assert_called_once()

    @patch("videocontext.extractors.frames._extract_frames_at_timestamps")
    @patch("videocontext.extractors.frames._build_interval_timestamps")
    @patch("videocontext.extractors.frames._download_video")
    @patch("videocontext.extractors.frames._ensure_vision_dependencies")
    def test_extract_frames_raises_if_no_frames_saved(
        self,
        mock_deps,
        mock_download,
        mock_build_interval,
        mock_extract,
    ):
        mock_download.return_value = (Path("/tmp/video.mp4"), 20.0)
        mock_build_interval.return_value = [0.0]
        mock_extract.return_value = []

        with self.assertRaises(RuntimeError):
            frames.extract_frames("dQw4w9WgXcQ", "./frames", interval=2.0, max_frames=1)

    def test_extract_frames_rejects_invalid_interval(self):
        with self.assertRaises(RuntimeError):
            frames.extract_frames("dQw4w9WgXcQ", "./frames", interval=0.0, max_frames=1)

    def test_extract_frames_rejects_invalid_max_frames(self):
        with self.assertRaises(RuntimeError):
            frames.extract_frames("dQw4w9WgXcQ", "./frames", interval=1.0, max_frames=0)


if __name__ == "__main__":
    unittest.main()
