"""Tests for packaging/release metadata consistency."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestReleaseMetadata(unittest.TestCase):
    def test_version_is_synced_between_pyproject_and_package(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        init_file = (ROOT / "src" / "videocontext" / "__init__.py").read_text(encoding="utf-8")

        pyproject_match = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)
        init_match = re.search(r'^__version__ = "([^"]+)"$', init_file, re.MULTILINE)

        self.assertIsNotNone(pyproject_match)
        self.assertIsNotNone(init_match)
        self.assertEqual(pyproject_match.group(1), init_match.group(1))


if __name__ == "__main__":
    unittest.main()
