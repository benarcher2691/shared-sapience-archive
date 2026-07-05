#!/usr/bin/env python3
"""Recompute REPORT.md's header stats and topic index from its own entries.

Run after adding or editing entries so the counts, date range, and topic index
at the top of REPORT.md stay consistent:

    python3 refresh_report.py [--date YYYY-MM-DD]

--date sets the "Last updated" line (defaults to leaving it unchanged).
Only the header block above "## Video summaries" is rewritten; entries below
are left untouched. Stdlib only.
"""
import argparse
import re
from pathlib import Path

REPORT = Path(__file__).resolve().parent / "REPORT.md"
MARKER = "## Video summaries"

TOPIC_LABELS = {
    "#anthropic": "Anthropic", "#openai": "OpenAI", "#google-deepmind": "Google / DeepMind",
    "#meta": "Meta", "#xai-musk": "xAI / Musk", "#open-models": "Open models",
    "#compute-infrastructure": "Compute infrastructure", "#chips": "Chips / semiconductors",
    "#robotics": "Robotics", "#biotech-medicine": "Biotech & medicine", "#cybersecurity": "Cybersecurity",
    "#energy-climate": "Energy & climate", "#labor-economy": "Labor & economy",
    "#markets-finance": "Markets & finance", "#space": "Space", "#safety-alignment": "Safety & alignment",
    "#legal-courts": "Legal & courts", "#agents": "AI agents", "#science": "Science",
    "#society-culture": "Society & culture", "#policy-regulation": "Policy & regulation",
    "#export-controls": "Export controls", "#essay": "Essays (non-news)",
}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fmt_date(s):
    y, m, d = s.split("-")
    return f"{MONTHS[int(m) - 1]} {int(d)}, {y}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="value for 'Last updated'")
    args = ap.parse_args()

    text = REPORT.read_text()
    body = text[text.index(MARKER):]

    entries = re.findall(r"^### (\d{4}-\d{2}-\d{2}) — .+?\n(`#.*?)\n", body, re.M)
    dates = sorted(d for d, _ in entries)
    n = len(entries)

    counts = {}
    for _, meta in entries:
        for t in re.findall(r"`(#[a-z0-9-]+)`", meta):
            counts[t] = counts.get(t, 0) + 1
    index = "\n".join(
        f"| `{t}` | {TOPIC_LABELS.get(t, t.lstrip('#'))} | {c} |"
        for t, c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    )

    # keep existing "Last updated" unless overridden
    m = re.search(r"\*\*Last updated:\*\* (\S+)", text)
    last_updated = args.date or (m.group(1) if m else "unknown")

    header = f"""# The Century Report — SharedSapience channel summary

Summaries of every video on the [SharedSapience YouTube channel](https://www.youtube.com/@SharedSapience).
The channel publishes **The Century Report (TCR)**, a near-daily ~15-minute podcast covering
frontier-AI news — labs, policy, compute, and the science/biotech/energy stories AI is accelerating —
plus occasional stand-alone essay videos.

- **Videos summarized:** {n}
- **Date range:** {fmt_date(dates[0])} → {fmt_date(dates[-1])}
- **Last updated:** {last_updated}
- **How to update / search:** see [README.md](README.md)

> Entries are newest-first. Each is tagged with topics from the index below.
> To find every episode on a topic, grep the tag, e.g. `grep -n '#export-controls' REPORT.md`.

## Topic index

| Tag | Topic | Episodes |
|---|---|---:|
{index}

> Counts sum to more than {n} because most episodes carry several tags.

---

"""
    REPORT.write_text(header + body)
    print(f"Refreshed header: {n} episodes, {len(counts)} topics, "
          f"{fmt_date(dates[0])} → {fmt_date(dates[-1])}, updated {last_updated}.")


if __name__ == "__main__":
    main()
