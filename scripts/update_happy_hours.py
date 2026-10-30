#!/usr/bin/env python3
"""Source change monitor for Lamplight happy hours.

No speculative deal extraction: this script never replaces prices or hours based
on keyword guesses. It records observable source changes for editorial review.
"""
import csv
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "shared/src/commonMain/composeResources/files/happy_hours_tinyfish_2026_10_22.csv"
DIR = ROOT / "data/happy-hours"
STATE = DIR / "source_state.json"
REPORT = DIR / "review.md"
REPORT_JSON = DIR / "review.json"
UA = "Mozilla/5.0 (compatible; LamplightSourceMonitor/1.0; +https://github.com/nhenia/lamplight)"
MAX_BYTES = 900_000

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.ignore = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg"):
            self.ignore += 1
    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg") and self.ignore:
            self.ignore -= 1
    def handle_data(self, data):
        if not self.ignore:
            self.parts.append(data)

def fetch(url):
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,text/plain"})
    with urlopen(req, timeout=12) as response:
        content_type = response.headers.get("Content-Type", "")
        if not any(t in content_type for t in ("text/html", "text/plain", "application/xhtml+xml")):
            raise ValueError("Unsupported content type: " + content_type)
        body = response.read(MAX_BYTES).decode("utf-8", errors="replace")
    if "html" in content_type:
        parser = TextExtractor()
        parser.feed(body)
        body = " ".join(parser.parts)
    normalized = re.sub(r"\s+", " ", html.unescape(body)).strip()
    if len(normalized) < 40:
        raise ValueError("Page lacks readable text")
    return normalized

def main():
    DIR.mkdir(parents=True, exist_ok=True)
    previous = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    with CSV.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    today = datetime.now(timezone.utc).date().isoformat()
    current = dict(previous)
    findings = []
    for row in rows:
        url = row["source_url"].strip()
        if not url.startswith(("https://", "http://")):
            continue
        key = (row["venue_id"] or row["venue"]) + "|" + url
        status = {"venue": row["venue"], "neighborhood": row["neighborhood"], "url": url}
        try:
            text = fetch(url)
            # Track a stable digest of happy-hour-relevant excerpts rather than
            # noisy whole-page content such as reservation widgets or dates.
            snippets = []
            for match in list(re.finditer(r"happy\s*hour|aperitif\s*hour|industry\s*night", text, re.I))[:20]:
                start, end = max(0, match.start() - 100), min(len(text), match.end() + 360)
                snippets.append(text[start:end])
            excerpt = " | ".join(snippets)
            if not excerpt:
                status["status"] = "needs_review"
                status["reason"] = "No happy-hour text detected on source page"
            else:
                digest = hashlib.sha256(excerpt.encode("utf-8")).hexdigest()
                earlier = previous.get(key, {})
                if earlier.get("digest") and earlier["digest"] != digest:
                    status["status"] = "source_changed"
                    status["reason"] = "Happy-hour-related text changed; verify offer against source"
                else:
                    status["status"] = "monitored"
                current[key] = {"digest": digest, "last_success": today}
            status["excerpt"] = excerpt[:650]
        except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
            status["status"] = "needs_review"
            status["reason"] = f"Source unavailable: {type(exc).__name__}"
        if status["status"] != "monitored":
            findings.append(status)
        time.sleep(0.15)
    # State changes only after a successful fetch; failures never erase a known
    # good digest. Does not change the CSV's verification or research_date fields.
    STATE.write_text(json.dumps(current, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_JSON.write_text(json.dumps({"date": today, "total_records": len(rows), "findings": findings}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [f"# Lamplight happy hour source review — {today}", "",
        f"Catalog records: {len(rows)}. Source flags: {len(findings)}.", "",
        "This monitor flags possible changes. It does **not** assert prices or schedules changed,",
        "and does not automatically rewrite the curated happy-hour CSV.", ""]
    for item in findings:
        lines.extend([f"## {item['venue']} ({item['neighborhood']})",
                      f"- Status: {item['status']}",
                      f"- Source: {item['url']}",
                      f"- Reason: {item.get('reason', 'See source')}",
                      f"- Excerpt: {item.get('excerpt', '')}", ""])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Checked {len(rows)} records; {len(findings)} need review")

if __name__ == "__main__":
    main()
