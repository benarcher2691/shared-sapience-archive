#!/usr/bin/env python3
"""Generate site/index.html from REPORT.md.

Parses the episode entries out of REPORT.md, embeds them as JSON into
site_template.html (replacing the /*__DATA__*/ token), and writes the
self-contained single-file site to site/index.html.

Re-run after update.py + folding new episodes into REPORT.md:

    python3 build_site.py

Only stdlib is used.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "REPORT.md"
TEMPLATE = ROOT / "site_template.html"
OUT = ROOT / "site" / "index.html"

TOPIC_LABELS = {
    "#anthropic": "Anthropic", "#openai": "OpenAI", "#google-deepmind": "Google / DeepMind",
    "#meta": "Meta", "#xai-musk": "xAI / Musk", "#open-models": "Open models",
    "#compute-infrastructure": "Compute", "#chips": "Chips", "#robotics": "Robotics",
    "#biotech-medicine": "Biotech & medicine", "#cybersecurity": "Cybersecurity",
    "#energy-climate": "Energy & climate", "#labor-economy": "Labor & economy",
    "#markets-finance": "Markets", "#space": "Space", "#safety-alignment": "Safety & alignment",
    "#legal-courts": "Legal & courts", "#agents": "AI agents", "#science": "Science",
    "#society-culture": "Society & culture", "#policy-regulation": "Policy",
    "#export-controls": "Export controls", "#essay": "Essays",
}

ENTRY_RE = re.compile(
    r"^### (?P<date>\d{4}-\d{2}-\d{2}) — (?P<title>.+?)\n"
    r"(?P<meta>`#.*?)\n\n"
    r"(?P<summary>.+?)(?=\n### |\Z)",
    re.S | re.M,
)


def split_body(body: str):
    """Split an entry body into a lede paragraph and a list of story points.

    New format: a lede paragraph, then markdown bullets (`- **X** — ...`).
    Old format (no bullets): the whole body is treated as the lede.
    """
    lede_lines, points = [], []
    for line in body.strip().splitlines():
        s = line.strip()
        if s.startswith("- "):
            points.append(s[2:].strip())
        elif not points:  # lede text only before the first bullet
            lede_lines.append(s)
    lede = " ".join(" ".join(lede_lines).split())
    return lede, points


def parse_report(text: str):
    episodes = []
    for m in ENTRY_RE.finditer(text):
        meta = m.group("meta")
        tags = re.findall(r"`(#[a-z0-9-]+)`", meta)
        url_m = re.search(r"\(https?://[^)]*watch\?v=([\w-]+)\)", meta)
        vid = url_m.group(1) if url_m else ""
        min_m = re.search(r"·\s*(\d+)\s*min", meta)
        minutes = int(min_m.group(1)) if min_m else 0
        lede, points = split_body(m.group("summary"))
        episodes.append({
            "date": m.group("date"),
            "title": m.group("title").strip(),
            "tags": tags,
            "id": vid,
            "url": f"https://www.youtube.com/watch?v={vid}" if vid else "",
            "minutes": minutes,
            "lede": lede,
            "points": points,
            "format": "essay" if "#essay" in tags else "daily",
        })
    return episodes


def main():
    text = REPORT.read_text()
    episodes = parse_report(text)
    if not episodes:
        raise SystemExit("No episodes parsed — check REPORT.md format.")
    episodes.sort(key=lambda e: e["date"], reverse=True)

    # topic counts, ordered by frequency
    # #essay is handled by the format control, so it is not a topic chip.
    counts = {}
    for e in episodes:
        for t in e["tags"]:
            if t == "#essay":
                continue
            counts[t] = counts.get(t, 0) + 1
    topics = [
        {"tag": t, "label": TOPIC_LABELS.get(t, t.lstrip("#")), "count": c}
        for t, c in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    ]

    payload = {
        "episodes": episodes,
        "topics": topics,
        "channel": "https://www.youtube.com/@SharedSapience",
        "generated": "2026-07-04",
        "total_minutes": sum(e["minutes"] for e in episodes),
        "date_min": min(e["date"] for e in episodes),
        "date_max": max(e["date"] for e in episodes),
    }

    template = TEMPLATE.read_text()
    html = template.replace("/*__DATA__*/", json.dumps(payload, ensure_ascii=False))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html)
    print(f"Wrote {OUT} — {len(episodes)} episodes, {len(topics)} topics.")


if __name__ == "__main__":
    main()
