"""
Bring a state's 2023 list up to date from a "what changed since 2023" research file.

    python tools/apply_since.py research/since2023/TX.json [more files...]

Each file (see research/since2023/README.md) lists plates the state added, redesigned or
retired since Jon Keegan's mid-2023 snapshot. This:
  - adds each new plate (NEW badge for 60 days), with its picture address as "img_url";
    fetch-pictures.yml downloads it on GitHub, and the game draws a stand-in until then,
  - points a redesigned plate at its new picture the same way (same id, so finds survive),
  - marks retired plates "retired" (they stay in the game; old plates stay on the road),
  - adds the state's best plate page to data/watch.json for the robot, and
  - marks the state as checked against its current list.
Running it twice is harmless: plates already added are recognized by name.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from research_from_keegan import category  # noqa: E402
from plate_robot import slug, words  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TODAY = dt.date.today().isoformat()
CATS = {"military", "veterans", "nature", "sports", "colleges", "firstresponder", "charity", "hobby",
        "vehicle", "tribal", "other"}


# Research files are checked by hand, so only drop plates that aren't for everyday cars.
# (The importer's broader SKIP also drops "county" and "boat", which would lose real plates
# like "Rankin County School District" or "Chesapeake Bay Power Boat Association".)
NOT_A_CAR = re.compile(r"""\b(motorcycles?(?!\s+club)|moped|autocycle|trailers?|dealers?|manufacturers?|transporters?|
    exempt|temporary|in[- ]transit|permit|taxi|for\shire|apportioned|commercial|tractor|wrecker|
    off[- ]?highway|snowmobile)\b""", re.I | re.X)


def squash(name: str) -> str:
    return re.sub(r"[^a-z0-9&]", "", name.lower())


def same_name(a: str, b: str, state: str) -> bool:
    wa, wb = words(a, state), words(b, state)
    return bool(wa) and bool(wb) and (wa == wb or len(wa & wb) / len(wa | wb) >= 0.67)


def apply(path: Path) -> str:
    r = json.loads(path.read_text(encoding="utf-8"))
    code = r["state"].upper()
    f = ROOT / "data" / f"{code}.json"
    doc = json.loads(f.read_text(encoding="utf-8"))
    plates, state_name = doc["plates"], doc["name"]
    ids = {p["id"] for p in plates}
    added = redesigned = retired = 0

    for n in r.get("new", []):
        title = (n.get("title") or "").strip()
        # a plate counts as already in the game only under the same name: the researcher compared
        # names by hand, and a loose match takes "Southern University" for "Georgia Southern" and
        # "Florida A&M" for "University of Florida"
        if (not title or n.get("matches_existing") or NOT_A_CAR.search(title)
                or any(squash(p["name"]) == squash(title) for p in plates)):
            continue
        pid = slug(title)
        while pid in ids:
            pid += "-2"
        ids.add(pid)
        cat = n.get("cat") if n.get("cat") in CATS else category(title)
        p = {"id": pid, "name": title, "cat": cat, "img": None, "added": TODAY, "source": n.get("source")}
        if n.get("source_img"):
            p["img_url"] = n["source_img"]
        if n.get("year"):
            p["year"] = str(n["year"])
        if doc.get("rated"):
            p["rar"], p["pts"] = "rare", 50
        plates.append(p)
        added += 1

    def find(name: str):
        # an exact name first: "Houston Texans" must not stand in for "Houston Texans - State"
        return next((p for p in plates if p["name"] == name), None) or \
               next((p for p in plates if same_name(name, p["name"], state_name)), None)

    for d in r.get("redesigned", []):
        hit = find(d.get("name_in_game", ""))
        if hit and d.get("source_img") and hit.get("img_url") != d["source_img"]:
            hit["img_url"], hit["redesigned"] = d["source_img"], TODAY
            redesigned += 1

    pictured = 0
    for d in r.get("pictures", []):
        hit = find(d.get("name_in_game", ""))
        if hit and not hit.get("img") and d.get("source_img"):
            hit["img_url"] = d["source_img"]
            pictured += 1

    for d in r.get("retired", []):
        hit = find(d.get("name_in_game", ""))
        if hit and not hit.get("retired"):
            hit["retired"] = True
            retired += 1

    # a follow-up pass on a partly checked state only counts as a full check when it says so
    doc["checked"] = bool(r.get("complete", True)) or bool(doc.get("checked"))
    doc["checked_on"] = TODAY
    doc["about"] = re.sub(r" From the 2023 snapshot, not yet checked against the state's current list\.", "",
                          doc.get("about", "")) + f" Checked for plates added since 2023 on {TODAY}."
    f.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    if r.get("robot_url"):
        wf = ROOT / "data" / "watch.json"
        watch = json.loads(wf.read_text())
        if not any(p["url"] == r["robot_url"] for p in watch):
            taken = {p["code"] for p in watch}
            c = code if code not in taken else next(f"{code}-{i}" for i in range(2, 9) if f"{code}-{i}" not in taken)
            watch.append({"code": c, "name": state_name, "url": r["robot_url"]})
            wf.write_text(json.dumps(watch, indent=1) + "\n")
    return f"{code}: +{added} new, {pictured} pictures found, {redesigned} redesigned, {retired} marked retired"


def main() -> int:
    for a in sys.argv[1:]:
        print(apply(Path(a)))
    cols_file = ROOT / "data" / "collections.json"
    cols = json.loads(cols_file.read_text())
    for c in cols:
        d = json.loads((ROOT / c["file"]).read_text())
        c["count"], c["checked"] = len(d["plates"]), d.get("checked", True)
    cols_file.write_text(json.dumps(cols, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
