# Architecture

VideoContext is a Python CLI that extracts YouTube content for AI workflows.

## High-Level Flow

1. CLI command parses arguments (`src/videocontext/cli.py`).
2. URL is validated and normalized to a video id (`src/videocontext/url.py`).
3. Data is extracted from upstream sources:
   - Transcript: `youtube-transcript-api` with `yt-dlp` fallback (`src/videocontext/extractors/transcript.py`)
   - Metadata: `yt-dlp` (`src/videocontext/extractors/metadata.py`)
   - Frames: `yt-dlp` + `OpenCV` + `scenedetect` (`src/videocontext/extractors/frames.py`)
4. Output is formatted (`src/videocontext/formatters/*`).
5. Result is printed to stdout or written to file.
6. Bundle output is coordinated by `src/videocontext/bundle.py`.
7. Bulk transcript output is coordinated by `src/videocontext/batch.py`; it validates a complete input list, resolves video titles, tracks relative filenames in `metadata/batch_index.json`, skips saved results, writes each new transcript atomically, and refreshes `CATALOG.md`.

## Commands and Modules

- `vc transcript`:
  - Extract transcript segments
  - Formats: `text`, `timestamped`, `json`
- `vc batch-transcripts`:
  - Accept an arbitrary-length file of video IDs or URLs
  - Process requests sequentially, pause and retry the current video after rate limits, and resume from saved text files
  - Name transcript files `transcripts/<title> [<video-id>].txt`; `--titles-file` supplies local titles and `--organize-only` migrates earlier files offline
  - Keep video lists and the resume index in `metadata/`, with batch failures in `logs/batch_failures.jsonl`
  - Generate an alphabetical `CATALOG.md` with links to saved transcripts
- `vc save`:
  - Saves metadata, transcript, context, HTML, and a manifest
  - Uses `<output-dir>/<video-id>/` bundle folders
- `vc metadata`:
  - Extract title/channel/date/description/chapters/tags
  - Formats: `markdown`, `json`, `html`
- `vc context`:
  - Merges metadata + transcript
  - Formats: `markdown`, `text`, `json`, `html`
- `vc frames`:
  - Extracts frame images by interval or scene-detect mode
  - Requires `.[vision]` extras

## Error Handling

- User-facing errors are emitted through rich-safe helpers in CLI.
- Invalid URLs and extraction failures return non-zero exit codes.
- Transcript rate limits are preserved as a distinct error and do not trigger the fallback extractor. Persistent rate limits pause a batch with exit status 75.
- `context` can continue without transcript when metadata succeeds.

## Testing Strategy

- Unit tests for parsing/formatting/URL extraction.
- CLI behavior tests with mocks for deterministic output.
- Fixture-driven parsing tests for metadata/transcript transforms.
- Frame extractor orchestration tests without network calls.
