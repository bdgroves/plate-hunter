# 🔍 PLATE HUNTER

### *The road-trip license plate game*

**[▶ Play it → brooksgroves.com/plate-hunter](https://brooksgroves.com/plate-hunter/)** · [The story behind it](https://brooksgroves.com/blog/plate-hunter-post.html)

> "The least popular special-design plate last year was the square dancer design, on only five vehicles, despite being one of the least expensive." — Seattle Times, April 20, 2026

Two games in one page:

- **🗺 States**: the classic. Spot a plate from every state (and DC) on this trip. Tap a state on the map or in the list, and watch the country fill in gold. A switch above the map flips to **🇨🇦 Canada** (10 provinces, 3 territories) and **🇲🇽 Mexico** (31 states and Mexico City); each country keeps its own count, and one trip spans all three. Start a new trip when you set off again; the places you've *ever* seen are kept.
- **✨ Specialty**: the deep cut. **8,099 special-design plates** from every US state, Canadian province and territory, and Mexican state, from Washington's square dancer (five on the road) to Nunavut's polar-bear plate. Tap one when you spot it. In Washington the rarer it is on real roads, the more it's worth. Every list has been checked against the licensing agency's current one (October 2026), and plates a state no longer sells stay in the game marked *No longer sold, still on the road*. Mexico's lists are the designs a road-tripper can still spot: the current plate, earlier designs still legal, World Cup 2026, eco and antique plates.

No server. No login. No ads. It installs to a phone's home screen and works with no signal.

---

## How it works

- **Tap to find.** A tap marks a plate or state found, with confetti. Tapping something you've already found opens its card instead, so a bump in the car can't erase a find. Every find has **Undo** for a few seconds.
- **Saved on the phone.** Progress lives in the browser (localStorage). The **?** sheet can save a backup file and restore it on another device.
- **Offline.** A service worker keeps the app, the plate lists and the map. In a specialty collection, **Save for offline** downloads every plate picture before you lose signal.
- **Install it.** "Add to Home Screen" on iPhone or Android and it opens like an app.

## The rarity system (Washington)

Points come from real registration counts: the **WA DOL Special License Plate Annual Report** to the Legislature ([2024 report, 2023 data](https://dol.wa.gov/media/pdf/3700/2024-special-license-plate-annual-reportpdf)) and the 2025 figures Gene Balk (FYI Guy) reported in the Seattle Times on April 20, 2026. Each plate's card says which.

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

Plates too new to have a count yet have an estimated tier. Other states' collections use the same tiers when real counts exist; otherwise they're marked *not rated yet* and every plate is worth 20.

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
│   ├── provinces.json      Canada's 13 provinces and territories (same shape)
│   ├── mexico.json         Mexico's 32 states (ISO 3166-2 codes: JAL, CMX …)
│   ├── us-map.json         state outlines (us-atlas, Albers USA)
│   ├── ca-map.json         province outlines (Natural Earth 1:50m, Statistics Canada Lambert)
│   ├── mx-map.json         Mexican state outlines (Natural Earth 1:10m, EPSG:6372)
│   ├── collections.json    the specialty collections and how many plates each has
│   ├── WA.json ON.json JAL.json …  one file per state/province: every specialty plate
│   ├── watch.json          the agency pages the plate robot visits
│   ├── watch/              what it decided about each picture on each page (+ _status.json)
│   ├── known/              fingerprints of every 2023 US plate picture
│   └── pending.json        pictures waiting for a person to say yes or no
├── plates/
│   ├── WA/ OR/ …           specialty plate pictures (WebP, 480 px)
│   └── standard/           one everyday plate per state, province and Mexican state
├── incoming/               pictures a person fetched by hand (see "Sites that refuse GitHub")
├── research/               the curated source lists the tools build from
│   ├── since2023/          what changed since the 2023 snapshot, five passes (Oct 2026)
│   ├── canada/ · mexico/   the Canadian and Mexican research, with the briefs used
└── tools/
    ├── validate.py         checks every data file (runs on every push)
    ├── research_from_keegan.py  first-draft research lists from the 2023 dataset
    ├── add_state.py        builds a state's collection from a research list
    ├── apply_since.py      applies a "what changed since 2023" research file
    ├── add_canada.py       builds a Canadian or Mexican collection from a research file
    ├── fetch_pictures.py   downloads pictures known only by address (fetch-pictures.yml)
    ├── grab_pictures.ps1   PowerShell: downloads waiting pictures at home
    ├── grab_in_browser.js  Chrome console: the same, for sites that only answer a browser
    ├── index.py            rebuilds data/collections.json
    ├── standard_plates.py  builds the States game's plate pictures
    ├── plate_robot.py      the plate robot (see below)
    └── known_hashes.py     builds data/known/ from the 2023 dataset
```

No build step and no dependencies for the app itself. To run it locally, serve the folder (the service worker and data files need http, not `file://`):

```powershell
git clone https://github.com/bdgroves/plate-hunter
cd plate-hunter
python -m http.server 8000
# then open http://localhost:8000
```

## Keeping it current

### 🤖 The plate robot

Every Monday and Thursday, [`plate-robot.yml`](.github/workflows/plate-robot.yml) runs `tools/plate_robot.py`, which visits each licensing agency page in `data/watch.json` and looks at every picture on it once:

1. **Not plate-shaped** (logos, banners, photos): ignored.
2. **A plate the game already has**: recognized by a 256-bit picture fingerprint (the same picture scores 0–6, different plates 10 and up), by a colour thumbnail that forgives a different crop, border or render, or by its name. So a re-hosted, resized or re-rendered picture of a plate we have isn't mistaken for a new one.
3. **A plate the game leaves out on purpose** (motorcycle, dealer, variants), recognized from `data/known/`: ignored.
4. **New, and clearly a plate** (its fingerprint is close to some known US plate, the page gives it a name, and the robot has looked at that page before): **added to the game by itself**, with the picture, a name from the page, a guessed category and a **NEW** badge for 60 days. Players find them under the 🆕 filter.
5. **New, but the robot isn't sure**: saved to `data/pending.json` and shown on the robot's GitHub issue with its picture. Reply on the issue with `/add KEY`, `/add KEY as Better Name`, `/skip KEY`, or `/add all` / `/skip all`, and [`robot-decide.yml`](.github/workflows/robot-decide.yml) does it within a minute or two. Only the repo owner's replies count.

It never removes a plate (retired plates stay on the road for years); it only notes pictures that left a page. A page that suddenly shows more than 25 unknown pictures adds nothing by itself. Pages it can't read are listed in `data/watch/_status.json` and on the issue. To run it now: Actions → *Plate robot* → *Run workflow* (optionally for a few states).

People can also report a plate from the game (**?** → *Tell us on GitHub*).

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

### Sites that refuse GitHub

Some agency sites refuse GitHub's servers (Illinois, Nunavut, many Mexican states), so their pictures can't be downloaded by `fetch-pictures.yml`. Open the agency's site in Chrome, press F12, open the Console and paste [`tools/grab_in_browser.js`](tools/grab_in_browser.js): it saves every picture still waiting on that site as `STATE--plate-id.ext` (or `standard--CODE.ext` for an everyday plate). Drag the files into [`incoming/`](incoming/) on GitHub and commit; `fetch-pictures.yml` converts them, checks they're plate-shaped, points the plates at them and removes the used files. A plate entry may carry `"img_crop": [x0, y0, x1, y1]` to cut the plate out of a press photo.

### Checking a state

Every state starts as a first draft made by `tools/research_from_keegan.py` from Jon Keegan's 2023 dataset: plates nobody sees on a car (dealer, government, motorcycle, trailer, taxi…) dropped, variants of one design folded together, a category guessed from the title, and every entry marked `"status": "keegan-2023"`. The game labels those states *2023 list*.

Every state has now been checked (October 2026; see `research/since2023/`). To check one again:

1. Open `research/<STATE>.json` beside the state's current plate page. Fix names and categories, set plates the state no longer sells to `"status": "discontinued"`, add new plates (a picture file in Keegan's dataset, or `"source_img"` with the agency's picture address), and change every `"keegan-2023"` to `"current"`. Add `"vehicles"` wherever the state publishes counts; with enough of them the state gets real rarity tiers.
2. `python tools/add_state.py <STATE> research/<STATE>.json --keegan path/to/us-license-plates`
3. Add the state's plate page to `data/watch.json` if it isn't there, and `data/<STATE>.json` to `FILES` in `sw.js` so it loads offline before it's opened once.
4. Validate and push. Pictures known only by address download on GitHub (`fetch-pictures.yml`).

Plate ids come from the names, and finds are saved by id, so rename with care once people have played a state.

---

## Credits

Plate pictures are from the licensing agencies of the US states, Canadian provinces and territories and Mexican states, and from the plates' sponsors; most US ones by way of **[jonkeegan/us-license-plates](https://github.com/jonkeegan/us-license-plates)**: every US plate as of mid-2023, collected by Jon Keegan for [Beautiful Public Data](https://www.beautifulpublicdata.com/). Newer Washington plates (Pickleball, Keep WA Evergreen, Honeybees, LeMay, Throwback, Smokey Bear, Mount St. Helens) come from the [Washington State Department of Licensing](https://dol.wa.gov/vehicles-and-boats/vehicles/license-plates/get-custom-plates/special-design-plates).

Washington counts: WA DOL 2025 registration figures, via [Gene Balk, Seattle Times, April 20, 2026](https://www.seattletimes.com). State outlines: [us-atlas](https://github.com/topojson/us-atlas) (US Census Bureau cartographic boundaries). Canada and Mexico: [Natural Earth](https://www.naturalearthdata.com/) admin-1 boundaries (public domain).

Part of [brooksgroves.com](https://brooksgroves.com) · [GitHub](https://github.com/bdgroves) · [Bluesky](https://bsky.app/profile/bdgroves.bsky.social)
