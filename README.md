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

# A file with one video ID or YouTube URL per line, with no list-size limit
videocontext batch-transcripts ids.txt --output-dir ~/Transcripts/my-channel

# Check progress without contacting YouTube; rerun the download command to resume
videocontext batch-transcripts ids.txt --output-dir ~/Transcripts/my-channel --status

# Use a local ID-and-title inventory to avoid extra YouTube title requests
videocontext batch-transcripts ids.txt --titles-file titles.tsv --output-dir ~/Transcripts/my-channel

# Rename previously saved ID-named files offline, preserving their contents
videocontext batch-transcripts ids.txt --titles-file titles.tsv --output-dir ~/Transcripts/my-channel --migrate-only

# Organize an existing collection and build its searchable catalog without network access
videocontext batch-transcripts ids.txt --titles-file titles.tsv --output-dir ~/Transcripts/my-channel --organize-only

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
| `batch-transcripts` | Paced, resumable transcripts from a list of video IDs or URLs |
| `metadata` | Metadata only (title, description, chapters) |
| `frames` | Key frame extraction (scene-detect or fixed-interval, requires `[vision]` extra) |

## No API Keys Required

VideoContext uses `youtube-transcript-api` and `yt-dlp` — no Google API key needed.

## Bulk Transcript Downloads

`batch-transcripts` accepts a text file with one bare video ID or YouTube URL per line. Blank lines, lines beginning with `#`, and duplicate IDs are ignored. It saves each transcript as `transcripts/<original video title> [<YouTube ID>].txt`, replacing only characters unsafe in filenames. `metadata/batch_index.json` records the ID-to-filename mapping so reruns skip completed videos. There is no application limit on the number of videos in the list.

Each output directory is a browsable collection: `CATALOG.md` lists every video alphabetically, links saved transcripts, and shows pending videos. `metadata/video_ids.txt` and `metadata/video_titles.tsv` keep the source lists available for later runs. `logs/` holds batch failures and download logs. Existing flat collections can be moved into this layout with `--organize-only` (or its older alias `--migrate-only`); organization uses local data and makes no YouTube requests. The command refuses to overwrite an unrelated file or a user-authored `CATALOG.md`.

By default, VideoContext fetches the title before the transcript. To avoid these extra requests, pass `--titles-file` with one `video-id<TAB>title` per line; extra tab-separated columns are ignored. Once supplied, the inventory is stored in the collection and reused on subsequent runs. `--organize-only` uses it to rename existing transcripts without contacting YouTube. The original transcript text is preserved.

Requests run one at a time. By default, VideoContext waits 120 seconds between videos; this is a conservative starting interval, not a guaranteed safe rate. If YouTube returns a rate limit, it stops making new requests, waits 30 minutes initially, and retries the same video with increasing cooldowns up to two hours. A server `Retry-After` value is honored when available. After six unsuccessful rate-limit retries, the command exits with status 75; run it again later to resume. Use `--retry-forever` to keep waiting until the block clears or you interrupt the command. Delays can be tuned with `--interval`, `--initial-cooldown`, and `--max-cooldown`.

Other transcript failures are recorded in `logs/batch_failures.jsonl` and the command continues with the next video. Rate limits are reported separately from unavailable captions. YouTube may still block requests or have videos without captions; an unlimited queue does not imply unlimited simultaneous requests or guaranteed transcript availability.

### Optional proxy route

Set `VIDEOCONTEXT_PROXY_FILE` to a text file containing one HTTP, HTTPS, SOCKS4, or SOCKS5 proxy URL. VideoContext uses that route for transcripts, metadata, and frame downloads. Keep the file private if its URL contains credentials (for example, `chmod 600 /path/to/proxy-url.txt`). `VIDEOCONTEXT_PROXY` can hold the URL directly when a file is inconvenient; the file takes precedence if both are set. Install `videocontext[proxy]` for SOCKS support.

A proxy is optional and is not bundled with VideoContext. It may also be rate limited by YouTube. Existing batch collections remain resumable when changing network routes; do not run two downloaders against the same collection at once.
