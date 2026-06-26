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

## Commands and Modules

- `vc transcript`:
  - Extract transcript segments
  - Formats: `text`, `timestamped`, `json`
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
- `context` can continue without transcript when metadata succeeds.

## Testing Strategy

- Unit tests for parsing/formatting/URL extraction.
- CLI behavior tests with mocks for deterministic output.
- Fixture-driven parsing tests for metadata/transcript transforms.
- Frame extractor orchestration tests without network calls.
