# Handoff: Plate Hunter (as of Oct 26, 2026)

For a new Claude chat to pick this work back up. Read this file and `CLAUDE.md`, then `git pull`.
`README.md` is the public description of the game, the data and the tools; this file is the state of the work.

## Where it stands

**Live:** https://brooksgroves.com/plate-hunter/ (GitHub Pages from this repo). Listed on
brooksgroves.com/games.html; the story is `blog/plate-hunter-post.html` in `bdgroves/bdgroves.github.io`
(April post plus a "Six Months Later" section covering everything below).

| | |
|---|---|
| Classic game | US 50 + DC, Canada 13, Mexico 32, behind a USA / Canada / Mexico switch; one trip spans all three |
| Specialty plates | **8,145** in 96 collections (51 US, 13 Canada, 32 Mexico) |
| Official pictures | 7,970 (98%); the rest show a drawn stand-in with the plate's name. Mexico's stand-ins (Oct 27) are our own plate drawing: state-color band (`MX_BAND` in `app.js`), the state code as the letters in Mexico's AAA-000-A pattern, plate name along the bottom |
| Checked | every US state against its agency's current catalog (five passes, Oct 2026: `research/since2023/`); Canada and Mexico researched from scratch (`research/canada/`, `research/mexico/`) |
| Retired plates | stay in the game, marked "No longer sold, still on the road" |
| Rarity | real tiers only in Washington (DOL counts); everywhere else every plate is 20 pts |
| Robot | `plate-robot.yml`, Mon + Thu, 102 pages in `data/watch.json`; its GitHub issue (#1) waiting list was cleared Oct 26 |

## How Brooks works (important)

- Windows PowerShell. Python on his PC is blocked by Windows Application Control for new packages, so the
  robot and picture downloads run **on GitHub only**. He has no local clone of this repo.
- He decides robot finds by replying on issue #1: `/add KEY`, `/add KEY as Better Name`, `/skip KEY`, `/add all`.
  He can also just ask Claude to sort the list (done Oct 26: view `plates/_pending/`, rewrite `kind`/`target`
  in `data/pending.json` where the robot matched the wrong plate, then
  `python tools/plate_robot.py --decide "<lines>"` locally and push).
- Sites that refuse GitHub (Illinois, Nunavut, many Mexican states): Brooks opens the site in Chrome, F12 →
  Console, pastes `tools/grab_in_browser.js`, then drags the saved files into
  https://github.com/bdgroves/plate-hunter/upload/main/incoming . `fetch-pictures.yml` does the rest.
  (He pasted an old copy from chat once; point him at the file on GitHub.) A PDF or odd file in `incoming/`
  is for Claude to process by hand (PEI's plate PDF was cropped that way).
- The Claude in Chrome extension refuses to return image data (base64), so Claude can't carry pictures out
  of Chrome itself; Chrome is good for reading catalogs that only render in a browser.
- Blog brand is friendly and warm. Official pictures only (agency or sponsor; for Mexico a government press
  photo where the plate fills the frame is OK). Never collector sites (papl8s, plateshack), car photos,
  news photos, placeholders, or sheets of several plates. Look at every new picture before calling it done.

## Open items

### Small, any time
- [ ] **Mexico pictures:** 50 of 63 Mexican designs and 26 of 32 everyday plates still have no picture.
  Oct 26 (second pass, three agents + Claude checking each photo): added Coahuila and Yucatán (everyday +
  current), Jalisco 'Collage', Nuevo León World Cup. Looked at and **rejected** (don't re-propose):
  Puebla (the only clean picture is a fake-plate warning poster), Veracruz (square-ish banner art),
  Chiapas (tilted, cut off), BCS (ends cut off, string across), Zacatecas (paper covers the plate),
  Michoacán (the small "car" plate in `unnamed-1-3.jpg` is the windshield sticker; the big ones are trucks).
  Puebla's current everyday plate is the newer guinda "Gobierno de Puebla" design, not 2022 "Hacer historia";
  the `current-design-2022` entry may need a new sibling entry. Oaxaca's `canjedeplacas.oaxaca.gob.mx` no
  longer resolves (DNS gone), so its `img_url` will never download. Sites that refused (browser or GitHub):
  Sonora, Tlaxcala, Tabasco, Edomex, Guerrero, Hidalgo, Nayarit, CDMX SEMOVI, Campeche. Several Mexican start
  years are inferred from re-plating news (notes in `research/mexico/<CODE>.json`).
- [ ] **Mexico designs vs. a collector's list** (`research/mexico/moini-check-2026-10.md`, Oct 27): Guanajuato
  (2025), Nayarit (2026) and Puebla (2025) have newer everyday designs than the game; CHH, CMX and MEX may too;
  a few start years differ; 34 disability/eco/antique plates in 20 states aren't in the game. Waiting on
  Brooks's call. Moini's site forbids reuse: facts only, never his pictures or text; confirm officially first.
- [ ] **Canada everyday plates** still drawn: MB, NB, NL, NT, YT; 14 Canadian specialty plates too (veteran,
  firefighter, amateur radio, bilingual MB, NS search and rescue, PEI Retired Volunteer Firefighter). Oct 26:
  MB, NB, NL, NWT, Yukon and AB/NWT Legion pages publish no plate pictures; Nova Scotia only shows the
  retired versions. Likely needs a direct ask to the agencies.
- [ ] **US leftovers:** Maryland's 21 "Tag Coming Soon" plates (MVA's list re-read in full Oct 26; DC United's
  only image is Photobucket-watermarked, Bruce HS Alumni's shows the Brandywine plate) and Texas's Legion of
  Valor Medal (My Plates shows a blank template; not in TxDMV's guides under that name). Colorado's 4, Maryland's
  Gold Star pair and Texas's 3 Medal of Honor plates were done Oct 26 (TxDMV `Military-Plate-Guide.pdf` pages
  14-15 have clean plate images: `pdfimages -j`).
- [ ] Brooks's judgment (Oct 26): plates missing from a catalog but not proven retired **stay unretired**
  (TX Choose Life/Grambling/Panoramic/Lone Star, NC NASCAR drivers, KY Friends of Hemp/Cardinal, MS
  military qualification plates, PA possible duplicates). Listed under `retired_unsure` in the research files.

### Bigger, when Brooks is ready
- [ ] **App Store / Play Store** version for road trips (Capacitor wrapper, icons, screenshots, listings,
  privacy note; Apple developer account $99/yr). It already installs as a PWA and works offline.
- [ ] **Family play:** several phones on one trip with a scoreboard (needs some sync; pairs with the app).
- [ ] **Rarity beyond Washington:** states that publish per-plate registration counts (Nevada has some
  `vehicles` figures already) could get real tiers.

## Things that bit us (don't repeat)

- The robot took a page's state from `code[:2]`; Mexico's 3-letter codes would have been misread (MEX as
  Maine). Fixed to `code.split("-")[0]`. Any new code that assumes 2-letter codes is a bug.
- `apply_since.py` loose name matching took "Southern University" for "Georgia Southern"; new plates now
  dedupe on exact (squashed) names only, and retire/redesign look up the exact name first.
- The importer's `SKIP` regex drops "county", "boat", "governor"…; research files use the narrower
  `NOT_A_CAR` instead.
- A robot run's first visit to a page sends every unrecognized picture to the waiting list (by design), so
  adding many pages at once floods issue #1. Expect that after adding pages; sort it for Brooks.
- Counts in commit messages were wrong twice; compute them, don't estimate.
- Claude's workspace can't reach agency sites. To look at originals before cropping (Oct 26), Claude used a
  temporary branch `pic-staging` whose workflow downloads `staging/urls.json` and commits the files; then it
  cropped locally and committed finished WebPs to main. The branch is still on GitHub (the proxy won't let
  Claude delete it): delete it, or reuse it the same way.
- `fetch_pictures.py` once hung for 30+ min; it now has a 25-min budget, 30 s timeouts and skips a host
  after 3 failures (so a blocked host's later pictures are simply tried next run).

## Other threads from the same chat (not Plate Hunter)

- **#30DayMapChallenge:** 29 of 30 days done; Day 30 waits on Brooks's napkin scan. See
  `bdgroves/30DayMapChallenge/HANDOFF.md`.
- **Lower Rainbow Pools story** (`bdgroves/brooks-memoir`, `STORY-IDEAS.md`): waiting on Brooks's interview answers.
- **op-dedupe** (his local 1Password cleanup tool, on his PC only): `pixi run report` / `reused` work; next is
  `pixi run fix --tier 1` (email and master accounts, which share passwords with bank logins), then `--tier 2`.
- Done this chat and live: SIERRA-FLOW handoff post image, Myles story cover (`brooks-journal`), Blinn cover
  (`brooks-memoir`), Plate Hunter hero image (`images/features/game-plate-hunter-2.jpg`).
