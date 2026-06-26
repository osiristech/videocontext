# VideoContext

Extract video context (transcripts, metadata) for AI CLI consumption.

YouTube is the largest developer knowledge base — tutorials, talks, demos — but AI CLI tools can't access it. VideoContext bridges that gap: extract video content into structured text that any AI CLI can consume via piping.

## Documentation

- Architecture: `docs/ARCHITECTURE.md`
- Development workflow: `docs/DEVELOPMENT.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`
- Release setup: `docs/RELEASE_SETUP.md`

## Install

```bash
pip install -e .

# Optional: frame extraction support
pip install -e ".[vision]"
```

## Testing

```bash
# Use test extras (pytest available if preferred)
pip install -e ".[test]"

# Built-in test run (works without pytest or editable install)
PYTHONPATH=src python -m unittest discover -s tests -v

# Or use shortcuts
make test
```

## Linting & Pre-commit

```bash
# Install dev tooling (ruff, pre-commit, packaging helpers)
pip install -e ".[dev,test]"
make dev-install

# Run lint checks
make lint
make lint-fix

# Install git hooks, then run them across the repo
make precommit-install
make precommit-run
```

`make precommit-run` is scoped to tracked files under `projects/videocontext`.

## Release

```bash
# Bump version in pyproject + __init__ and seed changelog entry
python scripts/bump_version.py 0.2.0

# Or with Makefile
make bump V=0.2.0

# Validate tests before tagging
python -m unittest discover -s tests -v
make release-check

# Create release tag (triggers publish workflow)
git tag videocontext-v0.2.0
git push origin videocontext-v0.2.0
```

The release workflow uses trusted publishing (`.github/workflows/videocontext-release.yml`), so configure your PyPI project to trust this repository/workflow.
Detailed setup steps are in `docs/RELEASE_SETUP.md`.

## Live Smoke Test (Optional)

```bash
# Requires network + YouTube access
# Runs against the local source tree, no console-script install required
./scripts/smoke_e2e.sh
make smoke URL="https://www.youtube.com/watch?v=dQw4w9WgXcQ" OUT=./smoke_out

# Custom URL/output directory
./scripts/smoke_e2e.sh "https://www.youtube.com/watch?v=dQw4w9WgXcQ" ./smoke_out
```

## Usage

```bash
# Save a complete local bundle (recommended)
vc save "https://youtube.com/watch?v=abc123"

# Save and open the folder in File Explorer
vc save "https://youtube.com/watch?v=abc123" --open

# Full context — metadata + transcript (default: markdown)
videocontext context "https://youtube.com/watch?v=abc123"

# Pipe directly to Claude Code
videocontext context "https://youtube.com/watch?v=abc123" | claude

# Transcript only
videocontext transcript "https://youtube.com/watch?v=abc123"

# Metadata only
videocontext metadata "https://youtube.com/watch?v=abc123"

# Extract key frames (scene-detect default)
videocontext frames "https://youtube.com/watch?v=abc123" --output-dir ./frames

# Extract frames at fixed interval
videocontext frames "https://youtube.com/watch?v=abc123" --interval 15 --max-frames 12

# Short alias
vc context "https://youtube.com/watch?v=abc123"

# JSON output
vc context "https://youtube.com/watch?v=abc123" -f json

# Save to file
vc context "https://youtube.com/watch?v=abc123" -o notes.md
```

`vc save` creates a folder under `./videocontext-output/<video-id>/` with:

- `metadata.json`
- `metadata.md`
- `transcript.txt`
- `transcript.md`
- `transcript.json`
- `context.md`
- `context.html`
- `manifest.json`

## Commands

| Command | Description |
|---------|-------------|
| `save` | Save metadata, transcript, context, HTML, and manifest files |
| `context` | Full video context (metadata + transcript) |
| `transcript` | Transcript only |
| `metadata` | Metadata only (title, description, chapters) |
| `frames` | Key frame extraction (scene-detect or fixed-interval, requires `[vision]` extra) |

## No API Keys Required

VideoContext uses `youtube-transcript-api` and `yt-dlp` — no Google API key needed.
