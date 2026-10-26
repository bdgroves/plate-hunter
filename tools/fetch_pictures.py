"""
Download plate pictures that are known only by their web address ("img_url").

    python tools/fetch_pictures.py

Some new plates were added before their picture could be saved (the importer can't
always reach agency sites). They carry "img_url" in data/<STATE>.json or
data/states.json and show a drawn stand-in in the game. This downloads each one,
saves a 480 px WebP and points the plate at it. Runs on GitHub's runners
(fetch-pictures.yml); a picture that still can't be fetched is simply left for next time.
"""
from __future__ import annotations

import io
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 (plate-hunter; +https://github.com/bdgroves/plate-hunter)"}


DEADLINE = time.monotonic() + 25 * 60     # leave what's left for the next run
failed_hosts: dict[str, int] = {}


def grab(url: str, dest: Path, width: int) -> bool:
    host = urllib.parse.urlsplit(url).hostname or ""
    if time.monotonic() > DEADLINE or failed_hosts.get(host, 0) >= 3:
        return False   # out of time, or a site that keeps refusing: try again next run
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
            raw = r.read(8_000_000)
        im = Image.open(io.BytesIO(raw))
        if not 1.3 <= im.width / max(im.height, 1) <= 3.2:   # artwork or a flyer, not a plate
            print(f"  {url}: not plate-shaped ({im.width}x{im.height}); left for a person", file=sys.stderr)
            return False
        im = im.convert("RGBA") if im.mode in ("P", "LA", "RGBA") else im.convert("RGB")
        if im.width > width:
            im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        dest.parent.mkdir(parents=True, exist_ok=True)
        im.save(dest, "WEBP", quality=82, method=6)
        return True
    except Exception as e:  # noqa: BLE001
        failed_hosts[host] = failed_hosts.get(host, 0) + 1
        print(f"  couldn't get {url}: {e}", file=sys.stderr, flush=True)
        return False


def main() -> int:
    got = 0
    for c in json.loads((ROOT / "data/collections.json").read_text()):
        f = ROOT / c["file"]
        doc = json.loads(f.read_text())
        changed = False
        for p in doc["plates"]:
            # a redesign gets a new file name, so phones that saved the old picture fetch the new one
            name = f"{p['id']}-{p['redesigned']}.webp" if p.get("img") and p.get("redesigned") else f"{p['id']}.webp"
            if p.get("img_url") and grab(p["img_url"], ROOT / "plates" / c["code"] / name, 480):
                p["img"] = name
                del p["img_url"]
                changed = True
                got += 1
                print(f"{c['code']}: {p['name']}", flush=True)
        if changed:
            f.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    sf = ROOT / "data/states.json"
    states = json.loads(sf.read_text())
    changed = False
    for s in states:
        if s.get("img_url") and grab(s["img_url"], ROOT / "plates/standard" / f"{s['code']}.webp", 400):
            s["img"] = f"plates/standard/{s['code']}.webp"
            del s["img_url"]
            changed = True
            got += 1
            print(f"standard plate: {s['name']}")
    if changed:
        sf.write_text(json.dumps(states, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{got} picture(s) saved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
