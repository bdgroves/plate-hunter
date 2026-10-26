"""
Build a Canadian province's or territory's plate list from a research file.

    python tools/add_canada.py research/canada/ON.json [more files...]

Each research file (see research/canada/README.md) names the everyday plate's picture and every
specialty plate the province sells, with picture addresses. This writes data/<CODE>.json (plates
start as drawn stand-ins with "img_url"; fetch-pictures.yml downloads the pictures on GitHub),
points data/provinces.json at the standard plate's picture, adds the province's plate page to
data/watch.json for the robot, and rebuilds data/collections.json.

Running it again keeps finds safe: plates already in the file keep their ids, and only new ones are added.
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_since import CATS, NOT_A_CAR, squash  # noqa: E402
from plate_robot import slug  # noqa: E402
from research_from_keegan import category  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TODAY = dt.date.today().isoformat()


def build(path: Path) -> str:
    r = json.loads(path.read_text(encoding="utf-8"))
    code = r["code"].upper()
    pf = ROOT / "data" / "provinces.json"
    provinces = json.loads(pf.read_text(encoding="utf-8"))
    prov = next(p for p in provinces if p["code"] == code)

    f = ROOT / "data" / f"{code}.json"
    doc = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {
        "code": code, "name": prov["name"], "rated": False, "plates": []}
    plates = doc["plates"]
    ids = {p["id"] for p in plates}
    added = 0
    for n in r.get("plates", []):
        title = (n.get("title") or "").strip()
        if not title or NOT_A_CAR.search(title) or any(squash(p["name"]) == squash(title) for p in plates):
            continue
        pid = slug(title)
        while pid in ids:
            pid += "-2"
        ids.add(pid)
        p = {"id": pid, "name": title, "cat": n.get("cat") if n.get("cat") in CATS else category(title), "img": None}
        if n.get("source_img"):
            p["img_url"] = n["source_img"]
        for k in ("year", "supports", "fact", "source"):
            if n.get(k):
                p[k] = str(n[k])
        if f.exists():               # a later run: these really are new to the game
            p["added"] = TODAY
        plates.append(p)
        added += 1

    doc.update({
        "updated": TODAY,
        "checked": bool(r.get("complete")),
        "checked_on": TODAY,
        "about": f"{prov['name']} special-design plates, from the province's own list on {TODAY}. "
                 "Not rated yet: every plate is worth the same."
                 if code not in ("YT", "NT", "NU") else
                 f"{prov['name']} special-design plates, from the territory's own list on {TODAY}. "
                 "Not rated yet: every plate is worth the same.",
        "sources": [{"title": "Provincial and territorial licensing agencies, and the plates' sponsors",
                     "url": r.get("robot_url") or ""}],
    })
    f.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    std = r.get("standard") or {}
    if std.get("source_img") and not prov.get("img"):
        prov["img_url"] = std["source_img"]
    if std.get("note"):
        prov["note"] = std["note"]
    pf.write_text(json.dumps(provinces, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    if r.get("robot_url"):
        wf = ROOT / "data" / "watch.json"
        watch = json.loads(wf.read_text())
        if not any(p["url"] == r["robot_url"] for p in watch):
            taken = {p["code"] for p in watch}
            c = code if code not in taken else next(f"{code}-{i}" for i in range(2, 9) if f"{code}-{i}" not in taken)
            watch.append({"code": c, "name": prov["name"], "url": r["robot_url"]})
            wf.write_text(json.dumps(watch, indent=1) + "\n")
    pics = sum(1 for p in plates if p.get("img") or p.get("img_url"))
    return f"{code}: {len(plates)} plates (+{added}), {pics} with a picture address"


def main() -> int:
    for a in sys.argv[1:]:
        print(build(Path(a)))
    subprocess.run([sys.executable, str(ROOT / "tools" / "index.py")], check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
