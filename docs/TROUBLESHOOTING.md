# Troubleshooting

## `ffmpeg is not installed` during `vc frames`

Symptom:
- yt-dlp fails with merge-format errors.

Fix:

```bash
sudo apt update
sudo apt install -y ffmpeg
ffmpeg -version
```

## AV1 decode errors from OpenCV

Symptom:
- Repeated logs similar to:
  - `Your platform doesn't support hardware accelerated AV1 decoding`
  - `Could not extract any frames from video`

What to try:
1. Use latest code (it prefers H.264-compatible formats first).
2. Retry with interval mode:
   ```bash
   vc frames "<url>" --interval 15 --max-frames 3 --output-dir ./frames_test
   ```
3. Try a different video to isolate source codec issues.
4. Ensure system FFmpeg/OpenCV packages are installed and up to date.

## `Video unavailable`

Symptom:
- yt-dlp returns video unavailable for a specific ID.

Fix:
- Confirm the URL is public and available in your region.
- Retry with another video ID.
- Update yt-dlp:
  ```bash
  pip install -U yt-dlp
  ```

## Pre-commit touches unrelated files

Symptom:
- Running pre-commit modifies files outside this project.

Fix:
- Run pre-commit via project Make target only:
  ```bash
  cd projects/videocontext
  make precommit-run
  ```
- This project target is scoped to tracked files under `projects/videocontext`.

## Lint says `ruff is not installed`

Fix:

```bash
cd projects/videocontext
make dev-install
make lint
```

## `vc save --open` does not open File Explorer

Symptom:
- The bundle is saved, but no file manager window appears.

Fix:
- Open the printed output folder manually.
- Confirm `xdg-open` is available:
  ```bash
  command -v xdg-open
  ```
