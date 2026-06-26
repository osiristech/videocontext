#!/usr/bin/env bash
set -euo pipefail

# Optional live-network smoke tests for the videocontext CLI.
# Requires internet connectivity and youtube access.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON:-python}"
URL="${1:-https://www.youtube.com/watch?v=dQw4w9WgXcQ}"
OUT_DIR="${2:-./smoke_out}"

run_vc() {
  PYTHONPATH="${PROJECT_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}" "${PYTHON_BIN}" -m videocontext "$@"
}

mkdir -p "${OUT_DIR}"

echo "[smoke] URL: ${URL}"
echo "[smoke] Output dir: ${OUT_DIR}"

echo "[smoke] metadata -> ${OUT_DIR}/metadata.md"
run_vc metadata "${URL}" -o "${OUT_DIR}/metadata.md"

echo "[smoke] transcript(json) -> ${OUT_DIR}/transcript.json"
run_vc transcript "${URL}" -f json -o "${OUT_DIR}/transcript.json"

echo "[smoke] context(text, no chapters) -> ${OUT_DIR}/context.txt"
run_vc context "${URL}" -f text --no-chapters -o "${OUT_DIR}/context.txt"

echo "[smoke] frames(interval=30, max=3) -> ${OUT_DIR}/frames/"
run_vc frames "${URL}" --interval 30 --max-frames 3 --output-dir "${OUT_DIR}/frames"

echo "[smoke] complete"
echo "[smoke] generated files:"
find "${OUT_DIR}" -type f | sort
