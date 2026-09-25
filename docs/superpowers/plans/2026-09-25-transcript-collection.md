# Transcript Collection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Organize VideoContext batch output into a durable, searchable collection and migrate the IndyDevDan directory without changing transcript content.

**Architecture:** Keep the collection root as the CLI output path. Store transcript text, metadata, and logs in separate directories; use a relative-path index for resume and generate an alphabetical catalog from the ID and title inventories.

**Tech Stack:** Python standard library, Click CLI, existing VideoContext extractors.

**Spec:** `docs/superpowers/specs/2026-09-25-transcript-collection-design.md`

## Global Constraints

- Preserve every existing transcript byte for byte.
- Do not overwrite unrelated user files during migration.
- Keep `--status` read-only and organization offline.
- Preserve `--migrate-only` as an alias.
- Keep the source checkout separate from downloaded content.

## Review Focus

- Interrupted migration: rerunning must discover the moved file and repair the index.
- Duplicate or unsafe titles: the video ID must keep filenames unique and paths contained in the collection.
- Existing catalog written by a user: generation must refuse to overwrite it.
- Old flat collections: saved transcripts must remain recognized while being migrated.
- Rate-limited download: the catalog and saved files must remain usable while the job waits.

### Task 1: Collection storage and migration

**Files:** `src/videocontext/batch.py`

**Interfaces:** `organize_collection(ids_file, output_dir, titles_file=None) -> int` migrates known files and returns the number of transcripts moved. `_load_index`, `_save_index`, `_saved`, and `_write_transcript` use collection-relative paths.

- [x] Read the current index and flat layout, then resolve each saved video by its ID and recorded filename.
- [x] Create `transcripts/`, `metadata/`, and `logs/`; move only known collection files and refuse destination collisions.
- [x] Store the IDs and available titles under `metadata/`; update the relative-path index after each safe move.
- [x] Make a second organization pass leave the same files and content in place.

### Task 2: Catalog and CLI

**Files:** `src/videocontext/batch.py`, `src/videocontext/cli.py`

**Interfaces:** `CATALOG.md` lists all IDs and titles, with links for saved transcripts. `--organize-only` performs offline migration; `--migrate-only` is an alias.

- [x] Generate a marked catalog sorted case-insensitively by title and containing saved/pending counts.
- [x] Refresh it after migration and each successful download; preserve a user-authored catalog.
- [x] Route failure records to `logs/` and keep read-only status working across both layouts.

### Task 3: Local data, documentation, and publication

**Files:** `README.md`, `docs/ARCHITECTURE.md`, `/home/soloarch/Transcripts/indydevdan/`

- [x] Stop the current batch process and record transcript hashes before migration.
- [x] Install the updated local build, organize IndyDevDan offline, and compare every transcript hash.
- [x] Restart the batch against durable metadata paths and inspect its first output.
- [x] Inspect the Git diff, syntax, package install, collection counts, and generated catalog; commit only this branch's work.
- [x] Push the branch to `origin` and update `main` only if repository access and branch policy allow it.
