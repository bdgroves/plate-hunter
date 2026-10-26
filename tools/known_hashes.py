"""
Fingerprints of every plate picture in Jon Keegan's 2023 dataset, including the ones the
game leaves out on purpose (motorcycle, dealer, trailer, variants of one design).

    python tools/known_hashes.py path/to/us-license-plates

Writes data/known/<STATE>.txt, one 256-bit difference hash (64 hex digits) per line. The
plate robot reads these so a picture of a plate we skipped on purpose isn't mistaken for a
brand-new plate.
"""
import csv
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plate_robot import dhash  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    keegan = Path(sys.argv[1])
    rows = list(csv.DictReader(open(keegan / "us-license-plates.csv", encoding="utf-8", errors="replace")))
    out = ROOT / "data" / "known"
    out.mkdir(parents=True, exist_ok=True)
    by_state: dict[str, set[str]] = {}
    for r in rows:
        f = keegan / "plates" / r["state"] / r["plate_img"]
        try:
            h = dhash(Image.open(f))
        except Exception:  # noqa: BLE001
            continue
        by_state.setdefault(r["state"], set()).add(np.packbits(h).tobytes().hex())
    for st, hs in sorted(by_state.items()):
        (out / f"{st}.txt").write_text("\n".join(sorted(hs)) + "\n")
    print(f"{sum(len(v) for v in by_state.values())} fingerprints for {len(by_state)} states")
    return 0


if __name__ == "__main__":
    sys.exit(main())
