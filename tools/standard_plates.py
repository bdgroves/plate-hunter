"""
Pictures for the States game: each state's everyday passenger plate.

    python tools/standard_plates.py research/standard_plates.json --keegan ../us-license-plates

research/standard_plates.json is a list like
    {"state": "OR", "keegan_img": "OR-op_image-000.jpg", "new_img": null, "note": "..."}
"new_img" (a URL) wins over the 2023 picture when a state has redesigned its plate since.
Writes plates/standard/<STATE>.webp and fills in "img" and "note" in data/states.json.
A state with no picture keeps the drawn stand-in plate.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
TRUSTED = (".gov", ".us")


def trusted(url):
    host = urlparse(url or "").netloc.lower()
    return bool(host) and host.endswith(TRUSTED)


UA = {"User-Agent": "Mozilla/5.0 (plate-hunter importer; +https://github.com/bdgroves/plate-hunter)"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("research")
    ap.add_argument("--keegan", type=Path)
    a = ap.parse_args()
    picks = {r["state"]: r for r in json.loads(Path(a.research).read_text())}
    out = ROOT / "plates" / "standard"
    out.mkdir(parents=True, exist_ok=True)
    states_file = ROOT / "data" / "states.json"
    states = json.loads(states_file.read_text())
    for s in states:
        r = picks.get(s["code"])
        if not r:
            continue
        im = None
        new = r.get("new_img") if trusted(r.get("new_img")) else None
        if new:
            s["img_url"] = new   # the current design; fetch_pictures.py swaps it in on GitHub's runners
            try:
                raw = urllib.request.urlopen(urllib.request.Request(new, headers=UA), timeout=30).read()
                im = Image.open(io.BytesIO(raw))
                s.pop("img_url")
            except Exception:  # noqa: BLE001
                pass
        k = r.get("keegan_img") or ""
        if im is None and k and "placeholder" not in k and a.keegan and (a.keegan / "plates" / s["code"] / k).exists():
            im = Image.open(a.keegan / "plates" / s["code"] / k)
        if r.get("note"):
            s["note"] = r["note"]
        if im is None:
            print(f"  {s['code']}: no picture yet" + (" (URL saved)" if s.get("img_url") else ""), file=sys.stderr)
            continue
        im = im.convert("RGBA") if im.mode in ("P", "LA", "RGBA") else im.convert("RGB")
        if im.width > 400:
            im = im.resize((400, round(im.height * 400 / im.width)), Image.LANCZOS)
        im.save(out / f"{s['code']}.webp", "WEBP", quality=82, method=6)
        s["img"] = f"plates/standard/{s['code']}.webp"
    states_file.write_text(json.dumps(states, indent=1, ensure_ascii=False) + "\n")
    print(f"{sum(1 for s in states if s.get('img'))} of {len(states)} states have a plate picture")
    return 0


if __name__ == "__main__":
    sys.exit(main())
