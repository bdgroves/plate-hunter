# 🔍 PLATE HUNTER

### *The road-trip license plate game*

**[▶ Play it → brooksgroves.com/plate-hunter](https://brooksgroves.com/plate-hunter/)** · [The story behind it](https://brooksgroves.com/blog/plate-hunter-post.html)

> "The least popular special-design plate last year was the square dancer design, on only five vehicles, despite being one of the least expensive." — Seattle Times, April 20, 2026

Two games in one page:

- **🗺 States**: the classic. Spot a plate from every state (and DC) on this trip. Tap a state on the map or in the list, and watch the country fill in yellow. Start a new trip when you set off again; the states you've *ever* seen are kept.
- **✨ Specialty**: the deep cut. Washington has 72 special-design plates, from pickleball to the Muckleshoot Tribe to a plate only for cars built before 1916. Tap one when you spot it. The rarer it is on real roads, the more it's worth. Oregon, Idaho, California and Nevada are here too.

No server. No login. No ads. It installs to a phone's home screen and works with no signal.

---

## How it works

- **Tap to find.** A tap marks a plate or state found, with confetti. Tapping something you've already found opens its card instead, so a bump in the car can't erase a find. Every find has **Undo** for a few seconds.
- **Saved on the phone.** Progress lives in the browser (localStorage). The **?** sheet can save a backup file and restore it on another device.
- **Offline.** A service worker keeps the app, the plate lists and the map. In a specialty collection, **Save for offline** downloads every plate picture before you lose signal.
- **Install it.** "Add to Home Screen" on iPhone or Android and it opens like an app.

## The rarity system (Washington)

Points come from **Washington DOL 2025 registration figures**, as reported by Gene Balk (FYI Guy) in the Seattle Times on April 20, 2026.

| Tier | Vehicles on WA roads | Points |
|---|---|---|
| 🟦 Common | 8,000+ | 10 |
| 🟩 Uncommon | 3,000 – 8,000 | 25 |
| 🟧 Rare | 500 – 3,000 | 50 |
| 🟨 **Legendary** | Under 500 | 150 – 300 |

| Rank | Plate | Vehicles | Annual fees |
|---|---|---|---|
| 1 | WSU Cougars | 24,100 | $734,000 |
| 2 | Collector Vehicle | 20,300 | $710,400 |
| 3 | Washington National Parks | 12,700 | $404,000 |
| 4 | Law Enforcement Memorial | 11,300 | $351,100 |
| 5 | Seattle Seahawks | 11,100 | $336,000 |
| 6 | University of Washington | 10,300 | $313,000 |
| 7 | US Army | 7,700 | $240,300 |
| — | Seattle Mariners | 1,100 | $35,300 |
| — | Seattle University | ~200 | $6,600 |
| — | Horseless Carriage | ~140 | — |
| Last | **Square Dancer** | **5** | — |

Plates without a published count have an estimated tier. Other states' collections use the same tiers when real counts exist; otherwise they're marked *not rated yet* and every plate is worth 20.

---

## Repo layout

```
plate-hunter/
├── index.html              the page
├── app.js · app.css        the game
├── sw.js                   offline support
├── manifest.webmanifest    home-screen install
├── data/
│   ├── states.json         50 states + DC, with each one's everyday plate
│   ├── us-map.json         state outlines (us-atlas, Albers USA)
│   ├── collections.json    the specialty collections and how many plates each has
│   ├── WA.json …           one file per state: every specialty plate
│   ├── watch.json          the agency pages the weekly watcher checks
│   └── watch/              what those pages showed last time
├── plates/
│   ├── WA/ OR/ …           specialty plate pictures (WebP, 480 px)
│   └── standard/           one everyday plate per state
├── research/               the curated source lists the tools build from
└── tools/
    ├── validate.py         checks every data file (runs on every push)
    ├── add_state.py        builds a state's collection from a research list
    ├── standard_plates.py  builds the States game's plate pictures
    └── watch_plates.py     the weekly new-plate check
```

No build step and no dependencies for the app itself. To run it locally, serve the folder (the service worker and data files need http, not `file://`):

```powershell
git clone https://github.com/bdgroves/plate-hunter
cd plate-hunter
python -m http.server 8000
# then open http://localhost:8000
```

## Keeping it current

**New plates find you.** Every Monday, [`watch-plates.yml`](.github/workflows/watch-plates.yml) loads each agency's plate page listed in `data/watch.json` and compares the plate pictures with last week's. If any appeared or disappeared, it opens an issue labeled `new-plates` with links to them. People can also report one from the game (**?** → *Tell us on GitHub*).

### Adding a plate

1. Save the picture from the agency's page as WebP, about 480 px wide, in `plates/<STATE>/` (any image editor, or `python tools/add_state.py` for a whole state).
2. Add an entry to `data/<STATE>.json`:
   ```json
   {"id": "orca-2", "name": "Orca (new design)", "cat": "nature", "rar": "rare", "pts": 50,
    "img": "orca-2.webp", "year": "2026", "supports": "…", "vehicles": "New in 2026",
    "fact": "One or two friendly sentences, every claim checked."}
   ```
3. Bump that state's `count` in `data/collections.json`.
4. `python tools/validate.py`, then push. GitHub Pages publishes it; the app picks up new lists the next time it's opened with a signal.

Categories: military, veterans, nature, sports, colleges, firstresponder, charity, hobby, vehicle, tribal, other. Ids are lowercase with dashes and never change once published (finds are saved by id).

### Adding a state

1. Make `research/<STATE>.json`: the state's current plates, each with a title, category, and a picture (a file in Jon Keegan's dataset or a URL on the agency site). Mark plates the agency no longer sells as `"status": "discontinued"`.
2. `python tools/add_state.py <STATE> research/<STATE>.json --keegan path/to/us-license-plates`
3. Add the agency's plate page to `data/watch.json` and the new `data/<STATE>.json` to `FILES` in `sw.js` if it should load offline before it's opened once.
4. Validate and push.

---

## Credits

Plate pictures are from the states' licensing agencies, most by way of **[jonkeegan/us-license-plates](https://github.com/jonkeegan/us-license-plates)**: every US plate as of mid-2023, collected by Jon Keegan for [Beautiful Public Data](https://www.beautifulpublicdata.com/). Newer Washington plates (Pickleball, Keep WA Evergreen, Honeybees, LeMay, Throwback, Smokey Bear, Mount St. Helens) come from the [Washington State Department of Licensing](https://dol.wa.gov/vehicles-and-boats/vehicles/license-plates/get-custom-plates/special-design-plates).

Washington counts: WA DOL 2025 registration figures, via [Gene Balk, Seattle Times, April 20, 2026](https://www.seattletimes.com). State outlines: [us-atlas](https://github.com/topojson/us-atlas) (US Census Bureau cartographic boundaries).

Part of [brooksgroves.com](https://brooksgroves.com) · [GitHub](https://github.com/bdgroves) · [Bluesky](https://bsky.app/profile/bdgroves.bsky.social)
