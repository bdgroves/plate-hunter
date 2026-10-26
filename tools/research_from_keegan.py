"""
First-draft research lists straight from Jon Keegan's 2023 dataset, for states nobody
has curated by hand yet.

    python tools/research_from_keegan.py path/to/us-license-plates TX OH ...   # or ALL

For each state it writes research/<STATE>.json in the shape add_state.py reads:
  - drops plates a passer-by won't see on a car (dealer, government, motorcycle-only,
    trailer, taxi, temporary, and similar),
  - folds variants of one design together ("- Personalized", "(vehicle)", "Truck", …)
    and rows that share the same picture,
  - guesses a category from the title (military, colleges, nature, …).
Every entry is marked "status": "keegan-2023": unchecked against the state's current
page. Curated states (those whose research file has no such marker) are left alone.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP = re.compile(r"""\b(motorcycles?|moped|autocycle|trailers?|semi|dealers?|manufacturers?|transporters?|
    exempt|government|official|state[- ]owned|county|municipal|city[- ]owned|legislat\w*|senate|senator|
    representative|house of delegates|congress(?!ional medal)|judge|judicial|consul\w*|diplomat\w*|governor|
    temporary|temp\b|in[- ]transit|non[- ]?resident|\d+[- ]day|permit|taxi|for hire|limo\w*|hearse|livery|
    bus\b|school bus|fleet|apportioned|commercial|tractor|wrecker|tow\b|repossess\w*|rental|lease|
    low[- ]speed|off[- ]?highway|atv|utv|snowmobile|boat|vessel|moped|sample\s*$|placeholder|
    special equipment|construction|implement|mobile home|logging|for sale|test\b|demo)\b""", re.I | re.X)
STANDARD = re.compile(r"^(standard|regular|passenger|general issue|base)\b|\b(standard|regular) (issue|plate|passenger)\b", re.I)
VARIANT = re.compile(r"""\s*[-–(,:]*\s*\b(personali[sz]ed|vanity|sequential|vehicle|passenger|auto(mobile)?|truck|pickup|
    van|car|pwd|handicap\w*|new\s*\d{4}|\d{4}\s*design|version\s*\d|v\d|design\s*\d|plates?|tags?|
    license)\b\s*[)]*""", re.I | re.X)

CATS = [
    ("tribal", r"\btrib(e|al)\b|\bnation\b(?!al)|band of|pueblo|reservation|indian community|rancheria"),
    ("veterans", r"veteran|purple heart|\bp\.?o\.?w\b|prisoner of war|gold star|medal|silver star|bronze star|"
                 r"distinguished (flying )?cross|pearl harbor|vietnam|korea|world war|\bwwii?\b|legion|\bvfw\b|amvets|"
                 r"combat|wounded|disabled vet|\bdav\b|retired military|war on terror|gwot|desert storm|iraq|afghan|"
                 r"merit|valor|navy cross|service cross|air medal|survivor"),
    ("military", r"\barmy\b|\bnavy\b|air force|marines?\b|marine corps|coast guard|national guard|military|armed forces|"
                 r"reserves?\b|airborne|ranger|seabee|submarine|special forces|space force|\busmc\b|\busaf\b|\bnavy\b"),
    ("firstresponder", r"fire\s?fight|fire (dept|department|company|fighter)|\bfire\b|police|sheriff|law enforcement|"
                       r"trooper|\bems\b|emergency|first responder|\bk-?9\b|rescue|paramedic|fallen officer|peace officer|"
                       r"dispatcher|corrections"),
    ("colleges", r"universit|college|alumni|\bstate u\b|institute of technology|\bu of\b|collegiate|community college|"
                 r"\bhbcu\b|polytechnic|seminary"),
    ("sports", r"football|baseball|basketball|hockey|soccer|golf|tennis|racing|nascar|speedway|motorsport|olympic|"
               r"\b(nfl|mlb|nba|nhl|mls|wnba)\b|cowboys|packers|steelers|bears\b|lions\b|vikings|chiefs|broncos|"
               r"patriots|giants|jets\b|eagles\b(?! (scout|nest))|ravens|bengals|browns|colts|titans|jaguars|texans|"
               r"saints|falcons|panthers|buccaneers|dolphins|bills\b|commanders|redskins|cardinals|rams\b|chargers|"
               r"raiders|seahawks|49ers|yankees|mets\b|red sox|cubs\b|white sox|tigers\b|twins\b|royals|astros|"
               r"rangers\b|braves|marlins|phillies|pirates|reds\b|brewers|rockies|diamondbacks|padres|dodgers|"
               r"orioles|nationals|capitals|blackhawks|bruins|penguins|predators|lightning|hurricanes|avalanche|"
               r"wild\b|thunder|spurs|mavericks|rockets|celtics|knicks|lakers|bulls|pistons|pacers|hawks\b|heat\b|"
               r"magic\b|jazz|blazers|grizzlies|pelicans|cavaliers|bucks\b|timberwolves|nuggets|suns\b|kings\b|"
               r"wrestling|bowling|lacrosse|pickleball|softball|volleyball|rodeo|ski\b|skiing"),
    ("nature", r"wildlife|conserv|state parks?|national parks?|\bparks?\b|bird|fish|trout|bass\b|salmon|deer|elk|"
               r"bear\b|eagle(?! scout)|wolf|wolves|turkey|ducks?\b|quail|pheasant|grouse|forest|trees?\b|lake|river|"
               r"ocean|coast|beach|bay\b|environment|\bwild\b|nature|pollinat|butterfl|monarch|whale|turtle|scenic|"
               r"trails?|mountain|desert|prairie|bison|buffalo|habitat|wetland|watershed|zoo|aquarium|garden|"
               r"bluebird|cardinal bird|hummingbird|owl|hawk\b|falcon\b|panther\b|manatee|dolphin\b|reef|"
               r"sea turtle|clean water|recycl|keep .* beautiful|smokey|outdoor|hunting|sportsm[ae]n|audubon|"
               r"ducks unlimited|national forest|canyon|island|lighthouse|wildflower|state flower"),
    ("vehicle", r"antique|classic|collector|vintage|street rod|hot rod|historic(al)? vehicle|horseless|"
                r"year of (manufacture|issue)|\byom\b|farm|motor ?home|\brv\b|recreational vehicle|electric|"
                r"\bev\b|custom vehicle|kit car|replica|restored|old timer|camper|tractor|show car"),
    ("hobby", r"amateur radio|\bham\b|radio|horse|equine|music|arts?\b|masonic|mason|shrin|\belks\b|lions club|"
              r"rotary|kiwanis|fraternal|knights|odd fellows|moose|eastern star|harley|corvette|mustang|car club|"
              r"aviation|pilot|flying|space|aerospace|astronom|railroad|cycling|bicycl|share the road|jeep|"
              r"photograph|press\b|square danc|nascar"),
    ("charity", r"cancer|autism|child|kids|foundation|awareness|hospital|donor|donate|humane|animal|pets?\b|spay|"
                r"neuter|literacy|educat|teacher|school|heart|diabetes|alzheimer|habitat for|ymca|scouts?\b|4-h|"
                r"\bffa\b|agricultur|farm bureau|hunger|food bank|adopt|foster|orphan|disabilit|special olympics|"
                r"down syndrome|mental health|suicide|domestic violence|safe|prevent|memorial|in god we trust|"
                r"church|faith|ministr|chamber of commerce|historical society|museum|library|centennial|"
                r"bicentennial|anniversary|heritage|history|support|association|society|club|league|fund"),
]
CATS = [(c, re.compile(p, re.I)) for c, p in CATS]


def category(title: str) -> str:
    for c, rx in CATS:
        if rx.search(title):
            return c
    return "other"


def base_title(t: str) -> str:
    t = re.sub(r"\s+", " ", t.replace("​", "")).strip(" -–")
    prev = None
    while prev != t:
        prev, t = t, VARIANT.sub("", t).strip(" -–,:()")
    return t or prev


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    keegan = Path(sys.argv[1])
    rows = list(csv.DictReader(open(keegan / "us-license-plates.csv", encoding="utf-8", errors="replace")))
    wanted = sorted({r["state"] for r in rows}) if sys.argv[2].upper() == "ALL" else [s.upper() for s in sys.argv[2:]]
    (ROOT / "research").mkdir(exist_ok=True)
    for st in wanted:
        out = ROOT / "research" / f"{st}.json"
        if out.exists():
            old = json.loads(out.read_text())
            if old and any(r.get("status") != "keegan-2023" for r in old):
                print(f"{st}: curated by hand, left alone")
                continue
        plates, titles, hashes = [], {}, set()
        for r in (x for x in rows if x["state"] == st):
            title = re.sub(r"\s+", " ", r["plate_title"].replace("​", "")).strip()
            img = keegan / "plates" / st / r["plate_img"]
            if not title or SKIP.search(title) or STANDARD.search(title) or not img.exists():
                continue
            h = hashlib.md5(img.read_bytes()).hexdigest()
            key = base_title(title).lower()
            if h in hashes or key in titles:
                continue
            hashes.add(h)
            name = base_title(title)
            name = re.sub(r"\s+license plates?$", "", name, flags=re.I)
            if not re.search(r"[A-Za-z0-9]", name):   # nothing left but "Personalized" etc.: an everyday plate
                continue
            titles[key] = True
            plates.append({"title": name, "keegan_img": r["plate_img"], "cat": category(title),
                           "status": "keegan-2023", "source": r["source"]})
        out.write_text(json.dumps(plates, indent=1, ensure_ascii=False) + "\n")
        print(f"{st}: {len(plates)} plates (from {sum(1 for x in rows if x['state'] == st)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
