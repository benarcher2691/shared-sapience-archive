# SharedSapience channel report

Tracking and summarizing every video on
[youtube.com/@SharedSapience](https://www.youtube.com/@SharedSapience).

## Files

| File | What it is |
|---|---|
| `REPORT.md` | The report: channel overview, topic index, one summary per video (newest first). |
| `update.py` | Incremental updater — finds new videos, caches their metadata, writes summary stubs to `PENDING.md`. Never touches `REPORT.md`. |
| `data/meta/*.json` | Metadata cache, one JSON per video (title, date, duration, description, tags). This is what "already summarized" is diffed against. |
| `PENDING.md` | Created by `update.py` when new videos exist; holds raw material for summaries. Delete after folding into `REPORT.md`. |
| `refresh_report.py` | Recomputes `REPORT.md`'s header stats and topic index from its entries. Run after adding/editing entries. |
| `build_site.py` | Regenerates the website from `REPORT.md`. Run after updating the report. |
| `site/index.html` | The website — a single self-contained file (searchable, topic filters, light/dark). Open it in any browser or host it anywhere. |
| `site_template.html` | The site's design/markup; `build_site.py` injects the episode data into it. |

## Updating when new videos arrive

```sh
python3 update.py            # needs yt-dlp on PATH (brew install yt-dlp)
```

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
