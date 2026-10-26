"""
Check the game's data before it ships. Run from the repo root:

    python tools/validate.py

Fails (exit 1) if a plate list is broken: a duplicate id, a missing picture, an unknown
category or rarity, a collection count that doesn't match its file, a state missing from
the map, or a file the offline cache expects that isn't there.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATS = {"military", "veterans", "nature", "sports", "colleges", "firstresponder",
        "charity", "hobby", "vehicle", "tribal", "other"}
RARITIES = {"common", "uncommon", "rare", "legendary", "unrated"}
problems: list[str] = []


def bad(msg: str) -> None:
    problems.append(msg)


def load(rel: str):
    try:
        return json.loads((ROOT / rel).read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        bad(f"{rel}: can't read ({e})")
        return None


states = load("data/states.json") or []
umap = load("data/us-map.json") or {"states": {}}
cols = load("data/collections.json") or []

codes = [s["code"] for s in states]
if len(codes) != 51 or len(set(codes)) != 51:
    bad(f"data/states.json: expected 51 unique states (50 + DC), found {len(set(codes))}")
for s in states:
    if s["code"] not in umap["states"]:
        bad(f"data/us-map.json: no shape for {s['code']}")
    if s.get("img") and not (ROOT / s["img"]).exists():
        bad(f"data/states.json: {s['code']} picture {s['img']} is missing")

provinces = load("data/provinces.json") or []
camap = load("data/ca-map.json") or {"states": {}}
pcodes = [s["code"] for s in provinces]
if len(set(pcodes)) != 13:
    bad(f"data/provinces.json: expected 13 provinces and territories, found {len(set(pcodes))}")
if set(pcodes) & set(codes):
    bad(f"a province shares a code with a state: {sorted(set(pcodes) & set(codes))}")
for s in provinces:
    if s["code"] not in camap["states"]:
        bad(f"data/ca-map.json: no shape for {s['code']}")
    if s.get("img") and not (ROOT / s["img"]).exists():
        bad(f"data/provinces.json: {s['code']} picture {s['img']} is missing")
for c in cols:
    if (c.get("country") == "CA") != (c["code"] in pcodes):
        bad(f"data/collections.json: {c['code']} should{'' if c['code'] in pcodes else ' not'} have country CA")

total_plates = 0
for c in cols:
    doc = load(c["file"])
    if not doc:
        continue
    plates = doc.get("plates", [])
    total_plates += len(plates)
    if doc.get("code") != c["code"]:
        bad(f"{c['file']}: code {doc.get('code')} doesn't match collections.json ({c['code']})")
    if len(plates) != c.get("count"):
        bad(f"data/collections.json: {c['code']} says {c.get('count')} plates, {c['file']} has {len(plates)}")
    ids = [p.get("id") for p in plates]
    for dup in {i for i in ids if ids.count(i) > 1}:
        bad(f"{c['file']}: duplicate id {dup}")
    for p in plates:
        where = f"{c['file']} [{p.get('id')}]"
        for field in ("id", "name", "cat"):
            if not p.get(field):
                bad(f"{where}: missing {field}")
        if not re.fullmatch(r"[a-z0-9-]+", str(p.get("id", ""))):
            bad(f"{where}: id should be lowercase letters, digits and dashes")
        if p.get("cat") not in CATS:
            bad(f"{where}: unknown category {p.get('cat')!r}")
        if doc.get("rated"):
            if p.get("rar") not in RARITIES:
                bad(f"{where}: unknown rarity {p.get('rar')!r}")
            if not isinstance(p.get("pts"), int):
                bad(f"{where}: pts should be a whole number")
        img = ROOT / "plates" / c["code"] / str(p.get("img"))
        if p.get("img") and not img.exists():
            bad(f"{where}: picture plates/{c['code']}/{p.get('img')} is missing")

# Everything the service worker precaches has to exist, or installing it fails.
sw = (ROOT / "sw.js").read_text(encoding="utf-8")
files = re.search(r"const FILES = \[(.*?)\];", sw, re.S)
for f in re.findall(r"'([^']+)'", files.group(1) if files else ""):
    if f != "./" and not (ROOT / f).exists():
        bad(f"sw.js precaches {f}, which doesn't exist")

if problems:
    print(f"{len(problems)} problem(s):")
    for p in problems:
        print("  -", p)
    sys.exit(1)
print(f"OK: {len(states)} states, {len(provinces)} provinces and territories, {len(cols)} specialty collections, {total_plates} plates")
