# SharedSapience channel report

Tracking and summarizing every video on
[youtube.com/@SharedSapience](https://www.youtube.com/@SharedSapience).

## Files

| File | What it is |
|---|---|
| `REPORT.md` | The report: channel overview, topic index, one summary per video (newest first). |
| `update.py` | Incremental updater — finds new videos, caches their metadata, writes summary stubs to `PENDING.md`. Never touches `REPORT.md`. `--refetch` re-pulls metadata for videos already cached. |
| `data/meta/*.json` | Metadata cache, one JSON per video (title, date, duration, description, tags). Reused when a video was fetched but never summarized, so no refetch is needed. |
| `PENDING.md` | Created by `update.py` when new videos exist; holds raw material for summaries. Delete after folding into `REPORT.md`. |
| `refresh_report.py` | Recomputes `REPORT.md`'s header stats and topic index from its entries. Run after adding/editing entries. |
| `build_site.py` | Regenerates the website from `REPORT.md`. Run after updating the report. |
| `site/index.html` | The website — a single self-contained file (searchable, topic filters, light/dark). Open it in any browser or host it anywhere. |
| `site_template.html` | The site's design/markup; `build_site.py` injects the episode data into it. |

## Updating when new videos arrive

```sh
python3 update.py            # needs yt-dlp on PATH (brew install yt-dlp)
```

`update.py` decides what's new by diffing the channel listing against the video
IDs already written up in `REPORT.md` — not against the metadata cache. That
matters: a video whose metadata was fetched but never summarized still counts
as new and gets re-stubbed, instead of the script reporting "up to date" while
the report sits a video behind. Re-running is safe — cached metadata is reused
rather than refetched, and a video already stubbed in `PENDING.md` isn't
stubbed twice.

Then ask Claude:

> summarize PENDING.md into REPORT.md, matching the existing format and tags

or write the entries by hand. Each entry is a one-line lede followed by the
day's distinct stories as bullets — each bullet led by its **bolded subject** so
the topics in a given episode are scannable:

```markdown
### YYYY-MM-DD — Video Title
`#tag1` `#tag2` `#tag3` · [watch](https://www.youtube.com/watch?v=ID) · NN min

One-sentence lede naming the day's biggest story.

- **Subject** — one distinct story, concrete (names/numbers).
- **Subject** — the next story.
- **Subject** — etc. (typically 3–6; fewer for essays).
```

`build_site.py` parses this exact shape: the paragraph before the first `-`
bullet becomes the lede, and each `- **X** — …` line becomes a story point the
site renders as a list and includes in search.

Keep entries newest-first and reuse existing tags where possible (see the topic
index in `REPORT.md`). You don't need to hand-edit the header or topic index —
`refresh_report.py` recomputes them.

Then refresh the header and rebuild the website:

```sh
python3 refresh_report.py --date $(date +%F)   # recompute stats + topic index
python3 build_site.py                          # reads REPORT.md, writes site/index.html
open site/index.html                           # (macOS) preview in a browser
```

`refresh_report.py` rewrites only the header block above "## Video summaries"
(episode count, date range, "Last updated", and the topic index table) from the
entries themselves; it never touches the entries. `--date` sets "Last updated"
(omit it to leave that line unchanged).

In full, the update loop is: **`update.py`** → summarize `PENDING.md` into
`REPORT.md` → delete `PENDING.md` → **`refresh_report.py`** → **`build_site.py`**.

## When yt-dlp is bot-blocked

YouTube periodically refuses per-video metadata with "Sign in to confirm you're
not a bot" — every player client and Safari cookies fail, but the channel
*flat-playlist* listing keeps working, so `update.py` still detects new videos.
When that happens, reconstruct the cache file by hand:

- title and duration from `yt-dlp --flat-playlist --print '%(id)s|%(title)s|%(duration)s'`
- title confirmed via `https://www.youtube.com/oembed?url=…&format=json`
- episode content from the companion post linked in every description,
  `https://sharedsapience.com/the-century-report-<month>-<day>-<year>/`

Write `data/meta/<id>.json` with the same fields as the others and start the
description with `NOTE: metadata reconstructed …` — that marker both flags the
file and makes it findable later. Once written, `update.py` stops re-flagging
the video as new.

The block usually lifts on its own after a day or two. To swap a reconstructed
file for the real thing:

```sh
python3 update.py --refetch reconstructed   # retry every hand-written file
python3 update.py --refetch VIDEO_ID …      # or just these
```

`--refetch` skips the channel diff, never writes `PENDING.md`, and keeps the
existing file if the fetch fails or comes back empty — so it is safe to run
against videos already summarized in `REPORT.md`. It only replaces the cached
metadata; if a summary was written from reconstructed material, re-check that
entry against the real description afterwards.

## The website

`site/index.html` is a single self-contained file — no server, no build step,
no external requests. Open it directly or drop it on any static host (GitHub
Pages, Netlify, S3). It offers:

- full-text search over titles and summaries (with match highlighting),
- a **format** filter (all / daily reports / essays),
- topic filters (click chips to narrow; multiple chips AND together),
- episodes grouped by month, newest-first, with a sort toggle,
- a live count, a stats strip, and a light/dark theme toggle.

It reads the same data as `REPORT.md`, so `python3 build_site.py` after every
report update keeps them in sync.

## Searching

- **By topic:** use the Topic index at the top of `REPORT.md`, or grep a tag:
  `grep -n '#export-controls' REPORT.md`
- **By keyword:** `grep -in 'kras' REPORT.md` (summaries), or search the full
  descriptions: `grep -il 'kras' data/meta/*.json`
- **By date:** entries are headed `### YYYY-MM-DD — …`, so
  `grep -n '### 2026-05' REPORT.md` lists all May 2026 episodes.
