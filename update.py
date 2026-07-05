#!/usr/bin/env python3
"""Incremental updater for the SharedSapience channel report.

Usage:
    python3 update.py [--yt-dlp /path/to/yt-dlp]

What it does:
 1. Fetches the current video list for https://www.youtube.com/@SharedSapience/videos
 2. Diffs against data/meta/*.json (the local metadata cache)
 3. Downloads metadata for any NEW videos into data/meta/
 4. Appends stub entries for the new videos to PENDING.md

After running it, ask Claude (or write by hand) to turn the PENDING.md stubs
into summaries in REPORT.md, then delete PENDING.md. Nothing in REPORT.md is
ever touched by this script, so manual edits are safe.

Only stdlib is used; the single external tool is yt-dlp.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

CHANNEL_URL = "https://www.youtube.com/@SharedSapience/videos"
ROOT = Path(__file__).resolve().parent
META_DIR = ROOT / "data" / "meta"
PENDING = ROOT / "PENDING.md"
FIELDS = ["id", "title", "upload_date", "duration", "description", "tags", "view_count"]
# YouTube blocks anonymous web-client metadata requests; the android client works.
EXTRACTOR_ARGS = "youtube:player_client=android"


def find_yt_dlp(explicit: str | None) -> str:
    candidates = [explicit] if explicit else []
    candidates += ["yt-dlp", str(ROOT / "venv" / "bin" / "yt-dlp")]
    for c in candidates:
        if c and shutil.which(c):
            return c
    sys.exit("yt-dlp not found. Install it (e.g. `brew install yt-dlp` or "
             "`python3 -m venv venv && venv/bin/pip install yt-dlp`) or pass --yt-dlp PATH.")


def list_channel_ids(yt_dlp: str) -> list[str]:
    out = subprocess.run(
        [yt_dlp, "--flat-playlist", "--print", "%(id)s", CHANNEL_URL],
        capture_output=True, text=True, check=True,
    ).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


def fetch_meta(yt_dlp: str, video_id: str) -> dict:
    out = subprocess.run(
        [yt_dlp, "--skip-download", "--no-warnings",
         "--extractor-args", EXTRACTOR_ARGS,
         "-J", f"https://www.youtube.com/watch?v={video_id}"],
        capture_output=True, text=True, check=True,
    ).stdout
    full = json.loads(out)
    return {k: full.get(k) for k in FIELDS}


def stub(meta: dict) -> str:
    date = meta.get("upload_date") or "????????"
    date_fmt = f"{date[:4]}-{date[4:6]}-{date[6:]}" if len(date) == 8 else date
    mins = round((meta.get("duration") or 0) / 60)
    desc = (meta.get("description") or "").strip()
    return (
        f"### {meta['title']}\n"
        f"- **Video:** https://www.youtube.com/watch?v={meta['id']}\n"
        f"- **Uploaded:** {date_fmt} · {mins} min\n\n"
        f"**Description (raw, summarize me):**\n\n{desc}\n\n---\n\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--yt-dlp", dest="yt_dlp", default=None)
    args = ap.parse_args()
    yt_dlp = find_yt_dlp(args.yt_dlp)

    META_DIR.mkdir(parents=True, exist_ok=True)
    known = {p.stem for p in META_DIR.glob("*.json")}
    current = list_channel_ids(yt_dlp)
    new_ids = [v for v in current if v not in known]

    print(f"Channel has {len(current)} videos; {len(known)} cached; {len(new_ids)} new.")
    if not new_ids:
        print("Report is up to date.")
        return

    stubs = []
    for vid in new_ids:
        print(f"  fetching {vid} ...")
        try:
            meta = fetch_meta(yt_dlp, vid)
        except subprocess.CalledProcessError as e:
            print(f"  FAILED {vid}: {e.stderr.strip().splitlines()[-1] if e.stderr else e}")
            continue
        (META_DIR / f"{vid}.json").write_text(json.dumps(meta, indent=1))
        stubs.append(stub(meta))

    if stubs:
        header = "" if PENDING.exists() else (
            "# Pending summaries\n\n"
            "New videos found by update.py. Summarize each into REPORT.md\n"
            "(newest first, matching the existing entry format and topic tags),\n"
            "update the topic index, then delete this file.\n\n---\n\n")
        with PENDING.open("a") as f:
            f.write(header + "".join(stubs))
        print(f"\nWrote {len(stubs)} stub(s) to {PENDING.name}.")
        print('Next: ask Claude to "summarize PENDING.md into REPORT.md".')


if __name__ == "__main__":
    main()
