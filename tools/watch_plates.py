"""
Watch the licensing agencies' plate pages for new (or retired) plates.

    python tools/watch_plates.py            # check every page in data/watch.json
    python tools/watch_plates.py --report report.md

Each agency page is mostly a gallery of plate pictures, so the check is simple: list
every picture on the page (its address and alt text), compare with the list saved last
time in data/watch/<STATE>.json, and write down what appeared or disappeared. The
GitHub workflow opens an issue with the report when anything changed; a person then
adds the plate to data/<STATE>.json (see README, "Adding a plate").

The first run for a page only saves its list. Pages that can't be fetched are reported,
never treated as "every plate was retired".
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parent.parent
SNAP = ROOT / "data" / "watch"
UA = "Mozilla/5.0 (compatible; plate-hunter-watch/1.0; +https://github.com/bdgroves/plate-hunter)"
SKIP = ("logo", "icon", "sprite", "banner", "header", "footer", "social", "seal", "flag", "translate", "spinner")


class Pictures(HTMLParser):
    def __init__(self, base: str):
        super().__init__()
        self.base, self.found = base, {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "img":
            src = a.get("src") or a.get("data-src") or ""
        elif tag == "a" and (a.get("href") or "").lower().split("?")[0].endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
            src = a["href"]
        else:
            return
        if not src or src.startswith("data:"):
            return
        url = urljoin(self.base, src.strip())
        path = urlparse(url).path.lower()
        if path.endswith(".svg") or any(s in path for s in SKIP):
            return
        alt = " ".join((a.get("alt") or a.get("title") or "").split())
        self.found.setdefault(path, {"src": url, "alt": alt})
        if alt and not self.found[path]["alt"]:
            self.found[path]["alt"] = alt


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode(r.headers.get_content_charset() or "utf-8", "replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", help="write a Markdown report here when something changed")
    args = ap.parse_args()
    pages = json.loads((ROOT / "data" / "watch.json").read_text(encoding="utf-8"))
    SNAP.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    sections, failures = [], []

    for page in pages:
        code, url = page["code"], page["url"]
        snap_file = SNAP / f"{code}.json"
        old = json.loads(snap_file.read_text(encoding="utf-8")) if snap_file.exists() else None
        try:
            p = Pictures(url)
            p.feed(fetch(url))
        except Exception as e:  # noqa: BLE001
            failures.append(f"- **{code}** {url}: {e}")
            continue
        if len(p.found) < 5:
            failures.append(f"- **{code}** {url}: only {len(p.found)} pictures on the page; the layout may have changed")
            continue
        new = {"code": code, "url": url, "checked": today, "pictures": dict(sorted(p.found.items()))}
        if old:
            added = [v for k, v in new["pictures"].items() if k not in old["pictures"]]
            gone = [v for k, v in old["pictures"].items() if k not in new["pictures"]]
            if added or gone:
                lines = [f"### {page.get('name', code)} ({len(added)} new, {len(gone)} gone)", f"Page: {url}", ""]
                lines += [f"- 🆕 [{v['alt'] or v['src'].rsplit('/', 1)[-1]}]({v['src']})" for v in added]
                lines += [f"- ➖ {v['alt'] or v['src'].rsplit('/', 1)[-1]}" for v in gone]
                sections.append("\n".join(lines))
        else:
            print(f"{code}: first check, saved {len(p.found)} pictures")
        # Keep the old 'checked' date when nothing changed, so the file (and the repo) stays the same.
        if old and old["pictures"] == new["pictures"]:
            continue
        snap_file.write_text(json.dumps(new, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    for s in sections:
        print(s, "\n")
    for f in failures:
        print(f)
    if args.report and sections:
        body = ["Pictures changed on these licensing-agency plate pages since the last check. "
                "A new picture is often a new plate (or a redesign). Check it, then add it to `data/<STATE>.json` "
                "and its picture to `plates/<STATE>/` (README: *Adding a plate*).", ""] + sections
        if failures:
            body += ["", "Pages that couldn't be checked this time:", *failures]
        Path(args.report).write_text("\n\n".join(body) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
