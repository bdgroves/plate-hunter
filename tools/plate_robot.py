"""
The plate robot: keeps every state's plate list fresh by itself.

    python tools/plate_robot.py                    # visit every page in data/watch.json
    python tools/plate_robot.py --only WA OR       # just these states
    python tools/plate_robot.py --report report.md # write what it did, for the GitHub issue

For each licensing agency page it:
  1. lists the pictures on the page and remembers, per picture, what it decided last time
     (data/watch/<page>.json), so each picture is only ever looked at once;
  2. downloads each picture it hasn't seen, and skips anything that isn't plate-shaped
     (logos, photos, banners);
  3. compares the picture with every plate the game already has for that state, using a
     256-bit difference hash. The same plate scores 0–6, different plates 10 and up, so
     anything within 8 is "a plate we already have";
  4. adds the rest to data/<STATE>.json as new plates: the picture shrunk to 480 px WebP,
     a name from the page (alt text, caption, or the nearby text), a guessed category, and
     "added": today's date. The game shows those with a NEW badge.
Pictures that disappear are only reported (old plates stay on the road for years).

Pictures it isn't sure are plates (not close enough to any known US plate, or no usable
name) aren't added: they go to data/pending.json and the GitHub issue, where a reply of
"/add KEY", "/add KEY as Better Name" or "/skip KEY" settles them (robot-decide.yml).

Safety valves: a page that suddenly offers more than --max-new unknown pictures in one run
adds nothing by itself (up to 40 go to review), and a page that can't be fetched is
reported, never read as "every plate is gone".
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

import numpy as np
from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
from research_from_keegan import SKIP, category  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SNAP = ROOT / "data" / "watch"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36 plate-hunter-robot (+https://github.com/bdgroves/plate-hunter)")
CHROME = re.compile(r"logo|icon|sprite|banner|header|footer|social|seal|flag|translate|spinner|avatar|"
                    r"facebook|twitter|instagram|youtube|linkedin|arrow|button|bg[-_]|background", re.I)
GENERIC = re.compile(r"^(sample|image|img|photo|picture|plate|license plate|licence plate|special plate|"
                     r"specialty plate|click here|view|enlarge|new|thumbnail|\d+)$", re.I)
SAME = 8          # difference-hash distance that still counts as the same plate
PLATELIKE = 55    # a picture this close to *some* known US plate is almost surely a plate itself
PENDING = ROOT / "data" / "pending.json"
_corpus = None
NEW_PENDING: list[str] = []


def corpus() -> np.ndarray:
    """Fingerprints of every 2023 US plate: the yardstick for 'does this look like a plate?'."""
    global _corpus
    if _corpus is None:
        rows = [x for f in sorted((ROOT / "data" / "known").glob("*.txt")) for x in f.read_text().split()]
        _corpus = np.array([np.unpackbits(np.frombuffer(bytes.fromhex(x), dtype=np.uint8)).astype(bool) for x in rows])
    return _corpus


def platelike(h: np.ndarray) -> int:
    return int((corpus() != h).sum(1).min())
TODAY = dt.date.today().isoformat()


# ---------- reading a page ----------
class Page(HTMLParser):
    """Pictures on the page, each with the text people would read beside it."""

    def __init__(self, base: str):
        super().__init__(convert_charrefs=True)
        self.base, self.pics, self.recent, self.link_text, self.waiting = base, {}, [], None, []
        self.in_skip = 0

    def _add(self, src: str, alt: str, title: str):
        url = urljoin(self.base, src.strip())
        path = urlparse(url).path
        low = path.lower()
        if not low.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")) and "image" not in low:
            return
        if low.endswith(".svg") or CHROME.search(low):
            return
        before = " ".join(self.recent[-2:])[-120:]
        pic = self.pics.setdefault(path, {"src": url, "alt": alt or title, "before": before, "after": ""})
        if not pic["alt"] and (alt or title):
            pic["alt"] = alt or title
        self.waiting.append(pic)

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        if tag in ("script", "style", "noscript"):
            self.in_skip += 1
        if tag == "img":
            src = a.get("data-src") or a.get("data-lazy-src") or a.get("src") or ""
            if a.get("srcset") and not src:
                src = a["srcset"].split(",")[0].split()[0]
            if src and not src.startswith("data:"):
                self._add(src, a.get("alt", "").strip(), a.get("title", "").strip())
        elif tag == "a" and re.search(r"\.(jpe?g|png|webp|gif)(\?|$)", a.get("href", ""), re.I):
            self._add(a["href"], "", a.get("title", "").strip())

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self.in_skip:
            self.in_skip -= 1

    def handle_data(self, data):
        if self.in_skip:
            return
        text = " ".join(data.split())
        if len(text) < 2:
            return
        self.recent.append(text)
        self.recent = self.recent[-4:]
        for pic in self.waiting:          # the first words after a picture are usually its caption
            if not pic["after"]:
                pic["after"] = text[:120]
        self.waiting = []


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()


def clean_name(s: str) -> str:
    s = re.sub(r"\.(jpe?g|png|webp|gif)$", "", s or "", flags=re.I)
    s = re.sub(r"[_]+|%20|(?<=[a-z])-(?=[a-z])", " ", s)
    s = re.sub(r"\b(special(ty)?|license|licence|sample|plates?|image|thumb(nail)?|large|small|lg|sm|web|final|new)\b",
               " ", s, flags=re.I)
    s = " ".join(s.split()).strip(" -–:|,.")
    return s[:60]


def plate_name(pic: dict) -> str:
    for cand in (pic.get("alt"), pic.get("after"), pic.get("before")):
        n = clean_name(cand or "")
        if n and not GENERIC.match(n) and 3 <= len(n) <= 60 and re.search(r"[A-Za-z]{3}", n):
            return n
    n = clean_name(urlparse(pic["src"]).path.rsplit("/", 1)[-1])
    return n.title() if re.search(r"[A-Za-z]{3}", n) else f"New plate {TODAY}"


# ---------- comparing pictures ----------
def dhash(im: Image.Image, n: int = 16) -> np.ndarray:
    a = np.asarray(im.convert("L").resize((n + 1, n), Image.LANCZOS), dtype=np.int16)
    return (a[:, 1:] > a[:, :-1]).flatten()


STOP = {"plate", "plates", "license", "licence", "tag", "tags", "the", "of", "and", "a", "dmv", "special",
        "specialty", "sample", "state", "vehicle", "new", "design", "for", "in", "&"}


def words(name: str, state_name: str = "") -> set[str]:
    drop = STOP | set(state_name.lower().split())
    return {w for w in re.findall(r"[a-z0-9]+", name.lower()) if w not in drop and len(w) > 1}


def tiny(im: Image.Image) -> np.ndarray:
    """A 24x12 colour thumbnail of the plate (border trimmed), normalized for correlation.
    It forgives what trips up the difference hash: a different crop, border, size or render."""
    rgb = im.convert("RGB")
    box = ImageOps.invert(rgb.convert("L")).point(lambda x: 255 if x > 18 else 0).getbbox()
    a = np.asarray((rgb.crop(box) if box else rgb).resize((24, 12)), dtype=float).flatten()
    a -= a.mean()
    return a / (np.linalg.norm(a) + 1e-9)


LOOKALIKE = 0.90  # thumbnail correlation at which two pictures are the same plate


def plate_shaped(im: Image.Image) -> bool:
    w, h = im.size
    return w >= 110 and 1.45 <= w / max(h, 1) <= 2.9


def slug(s: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-")[:40] or "plate"


# ---------- one state ----------
class State:
    def __init__(self, code: str):
        self.code, self.file = code, ROOT / "data" / f"{code}.json"
        self.doc = json.loads(self.file.read_text(encoding="utf-8"))
        self.hashes, self.tinies = {}, {}
        for p in self.doc["plates"]:
            if p.get("img") and (ROOT / "plates" / code / p["img"]).exists():
                im = Image.open(ROOT / "plates" / code / p["img"])
                self.hashes[p["id"]], self.tinies[p["id"]] = dhash(im), tiny(im)
        self.added: list[dict] = []
        # plates from the 2023 dataset the game skips on purpose (motorcycle, dealer, variants…)
        known = ROOT / "data" / "known" / f"{code}.txt"
        self.skipped = [np.unpackbits(np.frombuffer(bytes.fromhex(x), dtype=np.uint8)).astype(bool)
                        for x in known.read_text().split()] if known.exists() else []

    def known_elsewhere(self, h: np.ndarray) -> bool:
        return any(int((h != k).sum()) <= SAME for k in self.skipped)

    def by_name(self, name: str) -> str | None:
        """The plate already in the game that this name means, if any ('Endangered Wildlife Orca' -> orca)."""
        want = words(name, self.doc["name"])
        if not want:
            return None
        best, score = None, 0.0
        for p in self.doc["plates"]:
            have = words(p["name"], self.doc["name"])
            if not have:
                continue
            j = len(want & have) / len(want | have)
            if want == have or j > score:
                best, score = p["id"], (1.0 if want == have else j)
        return best if score >= 0.67 else None

    def replace_picture(self, pid: str, im: Image.Image) -> None:
        """A redesign: same plate (same id, so players keep their finds), current picture."""
        p = next(x for x in self.doc["plates"] if x["id"] == pid)
        im = im.convert("RGBA") if im.mode in ("P", "LA", "RGBA") else im.convert("RGB")
        if im.width > 480:
            im = im.resize((480, round(im.height * 480 / im.width)), Image.LANCZOS)
        name = f"{pid}-{TODAY}.webp"            # a new file name, so phones don't keep the old picture
        im.save(ROOT / "plates" / self.code / name, "WEBP", quality=82, method=6)
        p["img"], p["redesigned"] = name, TODAY
        self.hashes[pid], self.tinies[pid] = dhash(im), tiny(im)
        self.added.append({**p, "redesign": True})

    def lookalike(self, im: Image.Image) -> str | None:
        t = tiny(im)
        best = max(self.tinies.items(), key=lambda kv: float(kv[1] @ t), default=None)
        return best[0] if best and float(best[1] @ t) >= LOOKALIKE else None

    def match(self, h: np.ndarray) -> tuple[str | None, int]:
        best, dist = None, 999
        for pid, hh in self.hashes.items():
            d = int((h != hh).sum())
            if d < dist:
                best, dist = pid, d
        return (best if dist <= SAME else None), dist

    def add(self, im: Image.Image, name: str, page_url: str) -> str:
        ids = {p["id"] for p in self.doc["plates"]}
        pid = slug(name)
        while pid in ids:
            pid = re.sub(r"(-\d+)?$", lambda m: f"-{int(m.group()[1:] or 1) + 1}", pid, count=1)
        im = im.convert("RGBA") if im.mode in ("P", "LA", "RGBA") else im.convert("RGB")
        if im.width > 480:
            im = im.resize((480, round(im.height * 480 / im.width)), Image.LANCZOS)
        (ROOT / "plates" / self.code).mkdir(parents=True, exist_ok=True)
        im.save(ROOT / "plates" / self.code / f"{pid}.webp", "WEBP", quality=82, method=6)
        plate = {"id": pid, "name": name, "cat": category(name), "img": f"{pid}.webp",
                 "added": TODAY, "auto": True, "source": page_url}
        if self.doc.get("rated"):
            plate["rar"], plate["pts"] = "rare", 50     # new plates are scarce until counts come in
        self.doc["plates"].append(plate)
        self.hashes[pid], self.tinies[pid] = dhash(im), tiny(im)
        self.added.append(plate)
        return pid

    def save(self):
        if self.added:
            self.doc["updated"] = TODAY
            self.file.write_text(json.dumps(self.doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


# ---------- pictures waiting for a person ----------
def load_pending() -> dict:
    return json.loads(PENDING.read_text()) if PENDING.exists() else {}


def save_pending(p: dict) -> None:
    if p or PENDING.exists():
        PENDING.write_text(json.dumps(dict(sorted(p.items())), indent=1, ensure_ascii=False) + "\n")


def decide(text: str) -> list[str]:
    """Act on '/add KEY', '/add KEY as Better Name', '/add all', '/skip KEY', '/skip all' lines."""
    pending, done, states = load_pending(), [], {}
    for line in text.splitlines():
        m = re.match(r"\s*/(add|skip)\s+(\S+)(?:\s+as\s+(.+))?", line, re.I)
        if not m:
            continue
        verb, key, rename = m.group(1).lower(), m.group(2), (m.group(3) or "").strip()
        keys = list(pending) if key.lower() == "all" else [key]
        for k in keys:
            item = pending.pop(k, None)
            if not item:
                done.append(f"`{k}`: not waiting (already decided?)")
                continue
            img = ROOT / "plates" / "_pending" / item["img"]
            snap_file = SNAP / f"{item['page']}.json"
            snap = json.loads(snap_file.read_text()) if snap_file.exists() else {"pictures": {}}
            if verb == "add" and item.get("kind") == "redesign":
                st = states.setdefault(item["state"], State(item["state"]))
                st.replace_picture(item["target"], Image.open(img))
                verdict, msg = f"plate:{item['target']}", f"🎨 new picture for `{item['target']}` in {item['state']}"
            elif verb == "add":
                st = states.setdefault(item["state"], State(item["state"]))
                pid = st.add(Image.open(img), rename or item["name"], item["source"])
                verdict, msg = f"new:{pid}", f"✅ added **{rename or item['name']}** to {item['state']}"
            else:
                verdict, msg = "rejected", f"🗑 skipped `{k}`"
            if item["picture"] in snap.get("pictures", {}):
                snap["pictures"][item["picture"]]["verdict"] = verdict
                snap_file.write_text(json.dumps(snap, indent=1, ensure_ascii=False) + "\n")
            img.unlink(missing_ok=True)
            done.append(msg)
    for s in states.values():
        s.save()
    if states:
        cols_file = ROOT / "data" / "collections.json"
        cols = json.loads(cols_file.read_text())
        for c in cols:
            if c["code"] in states:
                c["count"] = len(states[c["code"]].doc["plates"])
        cols_file.write_text(json.dumps(cols, indent=1) + "\n")
    save_pending(pending)
    return done


# ---------- the run ----------
def visit(page: dict, state: State, max_new: int, status: dict, report: list[str]) -> None:
    code, url = page["code"], page["url"]
    snap_file = SNAP / f"{code}.json"
    snap = json.loads(snap_file.read_text(encoding="utf-8")) if snap_file.exists() else {}
    try:
        raw = fetch(url)
    except Exception as e:  # noqa: BLE001
        status[code] = {"url": url, "ok": False, "error": str(e)[:200], "checked": TODAY}
        return

    if raw[:5] == b"%PDF-":                    # a plate list published as a PDF: note changes only
        digest = hashlib.sha256(raw).hexdigest()
        if snap.get("sha256") and snap["sha256"] != digest:
            report.append(f"### {page['name']}\nThe plate list PDF changed: {url}")
        if snap.get("sha256") != digest:
            snap_file.write_text(json.dumps({"code": code, "url": url, "checked": TODAY, "sha256": digest}, indent=1) + "\n")
        status[code] = {"url": url, "ok": True, "kind": "pdf", "checked": TODAY}
        return

    p = Page(url)
    p.feed(raw.decode("utf-8", "replace"))
    old = snap.get("pictures", {})
    pics, todo = {}, []
    for path, pic in p.pics.items():
        prev = old.get(path) or {}
        if prev.get("verdict"):
            pics[path] = {**pic, "verdict": prev["verdict"]}
        else:
            todo.append((path, pic))

    # On the first look at a page, everything unmatched goes to a person: that's when old
    # picture differences pile up. After that, a picture that appears is almost always a new plate.
    first_scan = not any("verdict" in v for v in old.values())
    candidates = []
    for path, pic in todo:
        try:
            im = Image.open(io.BytesIO(fetch(pic["src"])))
            im.load()
        except Exception:  # noqa: BLE001
            pics[path] = {**pic, "verdict": "unreadable"}
            continue
        if not plate_shaped(im):
            pics[path] = {**pic, "verdict": "not-a-plate"}
            continue
        h = dhash(im)
        hit, dist = state.match(h)
        hit = hit or state.lookalike(im)
        if hit:
            pics[path] = {**pic, "verdict": f"plate:{hit}"}
        elif state.known_elsewhere(h):
            pics[path] = {**pic, "verdict": "skipped-2023"}
        elif SKIP.search(plate_name(pic)) or SKIP.search(pic["src"]):
            pics[path] = {**pic, "verdict": "not-for-cars"}
        else:
            candidates.append((path, pic, im))

    added_here, pending = [], load_pending()
    flood = len(candidates) > max_new
    if flood:
        report.append(f"### {page['name']}: {len(candidates)} pictures didn't match any plate\n"
                      f"That's a lot at once, so none were added by themselves; up to 40 are listed for review "
                      f"below and the rest wait for the next run. {url}")
        for path, pic, _ in candidates[40:]:  # look again next time
            pics.pop(path, None)
        candidates = candidates[:40]
    for path, pic, im in candidates:
        name, near = plate_name(pic), platelike(dhash(im))
        same = state.by_name(name)
        if same and im.width < 240:
            # the plate we have, shown small or in a slightly different picture: nothing to do
            pics[path] = {**pic, "verdict": f"plate:{same}"}
            continue
        sure = (not flood and not first_scan and not same and near <= PLATELIKE
                and im.width >= 200 and not name.startswith("New plate"))
        if sure:
            pid = state.add(im, name, url)
            pics[path] = {**pic, "verdict": f"new:{pid}"}
            added_here.append(pid)
        else:                              # a first look at this page, a redesign, or not sure: ask a person
            key = f"{state.code}-{slug(name)}"
            while key in pending:
                key += "-x"
            img = ROOT / "plates" / "_pending" / f"{key}.webp"
            img.parent.mkdir(parents=True, exist_ok=True)
            small = im.convert("RGB")
            small.thumbnail((480, 480))
            small.save(img, "WEBP", quality=80)
            pending[key] = {"state": state.code, "name": name, "cat": category(name), "img": img.name,
                            "kind": "redesign" if same else "new", "target": same,
                            "source": url, "page": page["code"], "picture": path, "likeness": near, "found": TODAY}
            pics[path] = {**pic, "verdict": f"pending:{key}"}
            NEW_PENDING.append(key)
    save_pending(pending)

    gone = [v for k, v in old.items() if k not in p.pics and str(v.get("verdict", "")).startswith(("plate:", "new:"))]
    if gone:
        report.append(f"### {page['name']}: {len(gone)} plate picture(s) no longer on the page\n"
                      + "\n".join(f"- {g['verdict'].split(':', 1)[1]}" for g in gone)
                      + f"\nOld plates stay on the road for years, so these stay in the game. {url}")
    for v in pics.values():
        v.pop("before", None)
        v.pop("after", None)
    new_snap = {"code": code, "url": url, "pictures": dict(sorted(pics.items()))}
    old_cmp = {"code": snap.get("code"), "url": snap.get("url"), "pictures": snap.get("pictures")}
    if new_snap != old_cmp:
        snap_file.write_text(json.dumps({**new_snap, "checked": TODAY}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    plates_seen = sum(1 for v in pics.values() if v["verdict"].startswith(("plate:", "new:")))
    status[code] = {"url": url, "ok": True, "pictures": len(p.pics), "plates": plates_seen,
                    "added": added_here, "checked": TODAY}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", help="state codes to visit (default: all)")
    ap.add_argument("--report", help="write a Markdown report here when something happened")
    ap.add_argument("--max-new", type=int, default=25)
    ap.add_argument("--decide", help="a comment with /add and /skip lines (from the GitHub issue)")
    a = ap.parse_args()
    if a.decide is not None:
        for line in decide(a.decide):
            print(line)
        return 0
    pages = json.loads((ROOT / "data" / "watch.json").read_text(encoding="utf-8"))
    if a.only:
        pages = [p for p in pages if p["code"][:2] in {c.upper() for c in a.only}]
    SNAP.mkdir(parents=True, exist_ok=True)
    status_file = SNAP / "_status.json"
    status = json.loads(status_file.read_text()) if status_file.exists() else {}
    states: dict[str, State] = {}
    report: list[str] = []
    for page in pages:
        st = page["code"][:2]
        if not (ROOT / "data" / f"{st}.json").exists():
            continue
        states.setdefault(st, State(st))
        visit(page, states[st], a.max_new, status, report)
        s = status[page["code"]]
        print(f"{page['code']:8} {'ok ' if s['ok'] else 'ERR'} "
              + (f"{s.get('pictures', '')} pictures, {s.get('plates', '')} plates, {len(s.get('added', []))} new" if s['ok'] and s.get('kind') != 'pdf'
                 else s.get('kind', '') or s.get('error', '')))

    added = [(st, p) for st, s in states.items() for p in s.added]
    for s in states.values():
        s.save()
    if added:
        cols_file = ROOT / "data" / "collections.json"
        cols = json.loads(cols_file.read_text())
        for c in cols:
            if c["code"] in states:
                c["count"] = len(states[c["code"]].doc["plates"])
        cols_file.write_text(json.dumps(cols, indent=1) + "\n")
    status_file.write_text(json.dumps(dict(sorted(status.items())), indent=1) + "\n")

    if a.report and (added or report or NEW_PENDING):
        repo = "https://raw.githubusercontent.com/bdgroves/plate-hunter/main"
        lines = []
        if added:
            lines += [f"## 🆕 {len(added)} new plate(s) added to the game", "",
                      "The robot found these on the agencies' pages and added them with a NEW badge. "
                      "Names and categories are its best guess: fix anything off in `data/<STATE>.json` "
                      "(or delete a plate that isn't one).", ""]
            lines += [f"- **{st}** · {p['name']} · {p['cat']}" + (" (new picture)" if p.get("redesign") else "")
                      + f"  \n  <img src=\"{repo}/plates/{st}/{p['img']}\" width=\"180\"> [page]({p.get('source', '')})"
                      for st, p in added]
        waiting = load_pending()
        if waiting:
            lines += ["", f"## 🤔 {len(waiting)} picture(s) the robot isn't sure about", "",
                      "Reply to this issue with one line per decision: `/add KEY`, `/add KEY as Better Name`, "
                      "`/skip KEY`, or `/add all` / `/skip all`.", ""]
            shown = list(waiting.items())[:80]
            lines += [f"- `{k}` · " + (f"🎨 redesign of `{v['target']}`?" if v.get("kind") == "redesign" else f"🆕 {v['name']}")
                      + f"  \n  <img src=\"{repo}/plates/_pending/{v['img']}\" width=\"180\"> [page]({v['source']})"
                      for k, v in shown]
            if len(waiting) > len(shown):
                lines.append(f"\n…and {len(waiting) - len(shown)} more in `data/pending.json`.")
        if report:
            lines += ["", "## Notes", "", *report]
        broken = [f"- {k}: {v.get('error')}" for k, v in status.items() if not v.get("ok") and k in {p['code'] for p in pages}]
        if broken:
            lines += ["", f"<details><summary>{len(broken)} page(s) couldn't be read this time</summary>", "", *broken, "</details>"]
        Path(a.report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"done: {len(added)} new plate(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
