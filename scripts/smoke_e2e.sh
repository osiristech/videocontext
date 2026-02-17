#!/usr/bin/env bash
set -euo pipefail

# Optional live-network smoke tests for the videocontext CLI.
# Requires internet connectivity and youtube access.

URL="${1:-https://www.youtube.com/watch?v=dQw4w9WgXcQ}"
OUT_DIR="${2:-./smoke_out}"

mkdir -p "${OUT_DIR}"

echo "[smoke] URL: ${URL}"
echo "[smoke] Output dir: ${OUT_DIR}"

echo "[smoke] metadata -> ${OUT_DIR}/metadata.md"
vc metadata "${URL}" -o "${OUT_DIR}/metadata.md"

echo "[smoke] transcript(json) -> ${OUT_DIR}/transcript.json"
vc transcript "${URL}" -f json -o "${OUT_DIR}/transcript.json"

echo "[smoke] context(text, no chapters) -> ${OUT_DIR}/context.txt"
vc context "${URL}" -f text --no-chapters -o "${OUT_DIR}/context.txt"

echo "[smoke] frames(interval=30, max=3) -> ${OUT_DIR}/frames/"
vc frames "${URL}" --interval 30 --max-frames 3 --output-dir "${OUT_DIR}/frames"

echo "[smoke] complete"
echo "[smoke] generated files:"
find "${OUT_DIR}" -type f | sort
