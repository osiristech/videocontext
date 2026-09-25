# Transcript Collection Design

## Goal

Keep large channel transcript collections easy to browse and safe to resume. The existing IndyDevDan collection has 13 title-and-ID transcript files, a 215-video title inventory, a resume index, and four logs mixed in one directory.

## Layout

The directory passed to `batch-transcripts --output-dir` is a collection root:

```text
collection/
  CATALOG.md                 Generated alphabetical list with saved/pending status
  transcripts/               <video title> [<video id>].txt
  metadata/
    video_ids.txt             Durable input list
    video_titles.tsv          Local title inventory when available
    batch_index.json          Video ID to relative transcript path and title
    legacy_batch_index.json   Preserved previous index after migration
  logs/
    batch_failures.jsonl      Non-rate-limit failures from VideoContext
    ...                       Existing known download logs, preserved
```

The catalog links saved transcripts and lists pending videos by title and ID. It is generated only when the existing file is absent or already marked as generated. Video titles retain their wording; only filesystem-unsafe characters and excessive length are adjusted in filenames. The ID is always present in transcript filenames.

## Migration and resume

`--organize-only` runs entirely offline when a title inventory is supplied. It migrates known files from the flat layout, records relative transcript paths, and writes the catalog. `--migrate-only` remains an alias. A normal batch run organizes the collection before fetching and refreshes the catalog after each saved transcript. Status checks stay read-only. Migration may be rerun safely and must never overwrite an unrelated file. The input list and title inventory are copied into `metadata/` so the collection is usable after temporary source files disappear.

## Scope and limits

The layout applies to `batch-transcripts` collections. Single-video `transcript` output paths and `save` bundles retain their existing contracts. Existing text content must be preserved byte for byte. YouTube rate limits remain external; collection organization makes no network calls.
