"""
Build (or rebuild) a state's specialty collection from a curated plate list.

    python tools/add_state.py OR research/OR.json --keegan ../us-license-plates

research/<STATE>.json is a list of plates, one object each:

    {"title": "Crater Lake", "cat": "nature", "status": "current",
     "keegan_img": "OR-op_image-012.jpg",          # a picture in Jon Keegan's dataset, or
     "source_img": "https://.../crater-lake.png",  # a picture on the agency's site
     "supports": "...", "year": "1997", "vehicles": "12,345", "fact": "..."}

Discontinued plates are skipped. Pictures are shrunk to 480 px WebP in plates/<STATE>/.
If enough plates have real vehicle counts, rarity and points follow the same tiers as
Washington; otherwise the collection is "unrated" and every plate is worth the same.
Hand edits in data/<STATE>.json (facts, names) are kept for plates whose id still exists.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
NAMES = {s["code"]: s["name"] for s in json.loads((ROOT / "data/states.json").read_text())}
TIERS = [(8000, "common", 10), (3000, "uncommon", 25), (500, "rare", 50), (0, "legendary", 150)]
UA = {"User-Agent": "Mozilla/5.0 (plate-hunter importer; +https://github.com/bdgroves/plate-hunter)"}


def slug(s: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")[:40]


def count(v) -> int | None:
    m = re.search(r"[\d,]+", str(v or ""))
    return int(m.group().replace(",", "")) if m else None


# Pictures are only taken from the agencies themselves or the plate's own sponsor,
# never from news photos.
TRUSTED = (".gov", ".us", "oregonstate.edu", "oregonzoo.org", "nfl.com")


def trusted(url: str | None) -> bool:
    host = urlparse(url or "").netloc.lower()
    return bool(host) and any(host.endswith(t) for t in TRUSTED)


def picture(p: dict, keegan: Path | None, code: str) -> Image.Image | None:
    """The plate's picture, or None when it can't be had here (fetch_pictures.py gets it later)."""
    if p.get("keegan_img") and keegan and (keegan / "plates" / code / p["keegan_img"]).exists():
        return Image.open(keegan / "plates" / code / p["keegan_img"])
    if trusted(p.get("source_img")):
        try:
            req = urllib.request.Request(p["source_img"], headers=UA)
            return Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=60).read()))
        except Exception:  # noqa: BLE001
            return None
    return None


def vehicles_text(r: dict) -> str | None:
    n = count(r.get("vehicles"))
    if n is None:
        return None
    year = re.search(r"(19|20)\d\d", str(r.get("vehicles_asof") or ""))
    return f"{n:,}" + (f" ({year.group()})" if year else "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("code")
    ap.add_argument("research")
    ap.add_argument("--keegan", type=Path, help="local clone of github.com/jonkeegan/us-license-plates")
    ap.add_argument("--min-counted", type=float, default=0.6,
                    help="share of plates that need a vehicle count before the state is rated")
    a = ap.parse_args()
    code = a.code.upper()
    rows = [r for r in json.loads(Path(a.research).read_text()) if r.get("status") != "discontinued"
            and r.get("cat") != "standard"]
    out_dir = ROOT / "plates" / code
    out_dir.mkdir(parents=True, exist_ok=True)
    data_file = ROOT / "data" / f"{code}.json"
    old = {p["id"]: p for p in json.loads(data_file.read_text())["plates"]} if data_file.exists() else {}

    counted = [r for r in rows if count(r.get("vehicles"))]
    rated = len(counted) >= a.min_counted * len(rows)
    plates, seen = [], set()
    for r in rows:
        pid = slug(r["title"])
        while pid in seen:
            pid += "-2"
        seen.add(pid)
        im = picture(r, a.keegan, code)
        p = {"id": pid, "name": r["title"], "cat": r.get("cat") or "other", "img": None}
        if im is not None:
            im = im.convert("RGBA") if im.mode in ("P", "LA", "RGBA") else im.convert("RGB")
            if im.width > 480:
                im = im.resize((480, round(im.height * 480 / im.width)), Image.LANCZOS)
            im.save(out_dir / f"{pid}.webp", "WEBP", quality=82, method=6)
            p["img"] = f"{pid}.webp"
        elif trusted(r.get("source_img")):
            p["img_url"] = r["source_img"]   # fetch_pictures.py downloads it on GitHub's runners
        if p["img"] is None:
            print(f"  {r['title']}: no picture yet" + (" (URL saved)" if p.get("img_url") else ""), file=sys.stderr)
        for k in ("year", "supports", "fact"):
            if r.get(k):
                p[k] = str(r[k])
        if vehicles_text(r):
            p["vehicles"] = vehicles_text(r)
        if r.get("status") == "new_since_2023" and not r.get("year"):
            p["year"] = "New"
        if rated:
            n = count(r.get("vehicles"))
            if n is None:
                p["rar"], p["pts"] = "rare", 50   # no count: assume uncommon enough to be worth looking for
            else:
                _, p["rar"], p["pts"] = next(t for t in TIERS if n >= t[0])
        keep = old.get(pid, {})
        for k in ("name", "fact", "cat"):
            if keep.get(k):
                p[k] = keep[k]
        if keep.get("rar_by_hand"):   # a rarity someone set by hand survives a rebuild
            p["rar"], p["pts"], p["rar_by_hand"] = keep["rar"], keep["pts"], True
        plates.append(p)

    doc = {"code": code, "name": NAMES[code], "rated": rated,
           "updated": __import__("datetime").date.today().isoformat(),
           "about": f"{NAMES[code]} special-design plates." + ("" if rated else " Not rated yet: every plate is worth the same."),
           "sources": [{"title": "Jon Keegan, us-license-plates (2023)", "url": "https://github.com/jonkeegan/us-license-plates"}],
           "plates": plates}
    data_file.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    cols_file = ROOT / "data/collections.json"
    cols = [c for c in json.loads(cols_file.read_text()) if c["code"] != code]
    cols.append({"code": code, "name": NAMES[code], "file": f"data/{code}.json", "count": len(plates), "rated": rated})
    cols.sort(key=lambda c: (c["code"] != "WA", c["name"]))
    cols_file.write_text(json.dumps(cols, indent=1) + "\n")
    print(f"{code}: {len(plates)} plates written ({'rated' if rated else 'unrated'}), pictures in plates/{code}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
