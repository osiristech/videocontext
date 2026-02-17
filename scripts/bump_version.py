#!/usr/bin/env python3
"""Bump VideoContext version in package files and update changelog scaffold."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
INIT_FILE = ROOT / "src" / "videocontext" / "__init__.py"
CHANGELOG = ROOT / "CHANGELOG.md"

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _replace_once(text: str, pattern: str, replacement: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"Could not find pattern: {pattern}")
    return updated


def bump_version(new_version: str) -> None:
    if not VERSION_RE.match(new_version):
        raise ValueError("Version must follow semantic version format: X.Y.Z")

    pyproject_text = PYPROJECT.read_text(encoding="utf-8")
    init_text = INIT_FILE.read_text(encoding="utf-8")

    pyproject_text = _replace_once(
        pyproject_text,
        r'^version = "[^"]+"$',
        f'version = "{new_version}"',
    )
    init_text = _replace_once(
        init_text,
        r'^__version__ = "[^"]+"$',
        f'__version__ = "{new_version}"',
    )

    PYPROJECT.write_text(pyproject_text, encoding="utf-8")
    INIT_FILE.write_text(init_text, encoding="utf-8")

    _update_changelog(new_version)


def _update_changelog(new_version: str) -> None:
    if not CHANGELOG.exists():
        CHANGELOG.write_text(
            "# Changelog\n\nAll notable changes to this project are documented in this file.\n\n## [Unreleased]\n\n",
            encoding="utf-8",
        )

    changelog_text = CHANGELOG.read_text(encoding="utf-8")
    if f"## [{new_version}] - " in changelog_text:
        return

    today = date.today().isoformat()
    marker = "## [Unreleased]\n\n"
    new_block = (
        f"{marker}"
        f"## [{new_version}] - {today}\n\n"
        "- Released.\n\n"
    )
    if marker in changelog_text:
        changelog_text = changelog_text.replace(marker, new_block, 1)
    else:
        changelog_text = f"# Changelog\n\n## [Unreleased]\n\n## [{new_version}] - {today}\n\n- Released.\n\n{changelog_text}"

    CHANGELOG.write_text(changelog_text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bump VideoContext package version.")
    parser.add_argument("version", help="New semantic version, e.g. 0.2.0")
    args = parser.parse_args()
    bump_version(args.version)
    print(f"Bumped version to {args.version}")


if __name__ == "__main__":
    main()
