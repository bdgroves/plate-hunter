"""
Rebuild data/collections.json from the data/<STATE>.json files.

    python tools/index.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
names = {s["code"]: s["name"] for s in json.loads((ROOT / "data/states.json").read_text())}
cols = []
for code in names:
    f = ROOT / "data" / f"{code}.json"
    if f.exists():
        d = json.loads(f.read_text())
        cols.append({"code": code, "name": names[code], "file": f"data/{code}.json", "count": len(d["plates"]),
                     "rated": d.get("rated", False), "checked": d.get("checked", True)})
cols.sort(key=lambda c: (c["code"] != "WA", c["name"]))
(ROOT / "data/collections.json").write_text(json.dumps(cols, indent=1) + "\n")
print(f"{len(cols)} collections, {sum(c['count'] for c in cols)} plates")
