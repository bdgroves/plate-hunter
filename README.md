# 🔍 PLATE HUNTER

### *Washington State · Road Trip Edition*

> "Only 5 square dancer plates registered in all of Washington. They're out there. Somewhere."

---

Washington has 72 specialty license plates — and most people have never noticed most of them. There's a plate for pickleball. A plate for honeybees. A plate for the Muckleshoot Tribe. A plate that's only legal on cars built before 1916. And somewhere on the roads of the Evergreen State, five vehicles are rolling around with a square dancer on the back bumper, 300 points just waiting to be claimed.

**PLATE HUNTER** is a road trip game built around that premise. You see a plate in real life, you tap it in the app. It unlocks in full color. You earn points. The rarer the plate, the more it's worth — and the rarity tiers are pulled directly from the Washington DOL's annual vehicle registration report. This isn't made up. The square dancer really does have only five registered vehicles. The Horseless Carriage plate really does require a pre-1916 automobile. The Medal of Honor plate requires, well, a Medal of Honor.

No server. No login. No ads. Just a phone, an open road, and 72 plates to find.

**[▶ Play it now → bdgroves.github.io/plate-hunter](https://bdgroves.github.io/plate-hunter)**

---

## How It Works

Open the app on your phone before you get in the car. Browse the grid — 72 plates, all grayed out, all waiting. When you spot one in real life, tap it. It flips to full color, confetti fires, your point total climbs. Finds persist in localStorage so your collection survives across sessions. Filter by category — military, nature, sports, tribal, colleges — or flip to **✅ Found** to review your haul.

That's it. No account required.

---

## The Rarity System

Point values are grounded in real data from the **Washington Department of Licensing 2024 Report to the Legislature**, which publishes vehicle counts per specialty plate design.

| Tier | Vehicles on WA Roads | Points |
|---|---|---|
| 🟦 Common | 8,000+ | 10 pts |
| 🟩 Uncommon | 3,000 – 8,000 | 25 pts |
| 🟧 Rare | 500 – 3,000 | 50 pts |
| 🟨 **Legendary** | Under 500 | 150 – 300 pts |

### Legendary Tier

These are the white whales. Spotting any one of these on a road trip is genuinely remarkable.

| Plate | Why It's Legendary | Points |
|---|---|---|
| 🕺 **Square Dancer** | ~5 registered statewide | 300 |
| 🏎 **Horseless Carriage** | Pre-1916 vehicles only — operational antiques | 300 |
| 🏅 **Medal of Honor** | Eligibility requires the nation's highest military honor | 300 |
| 🤡 **J.P. Patches Pal** | Seattle's beloved TV clown. The nostalgia is real but the plates are scarce | 200 |
| 🕊 **Former Prisoner of War** | Restricted to verified POW/MIA families | 200 |
| 🦅 **Chehalis / Muckleshoot / Puyallup Tribal** | Issued to enrolled tribal members only | 200 |
| 🎾 **Tennis** | Nobody buys these | 150 |
| 🤼 **Wrestling** | Somehow even fewer than tennis | 150 |
| 📡 **Military Affiliate Radio (MARS)** | You have to know what MARS is to want this plate | 150 |

---

## The Plates (72 Total)

**🎖 Military** — Air Force · Army · Coast Guard · Marine Corps · National Guard · Navy

**🎗 Veterans** — Disabled American Veteran · Former POW · Gold Star Family · Medal of Honor · MARS · Purple Heart · 988 Prevent Veteran Suicide

**🌲 Nature** — Orca · Honeybees & Pollinators · Lighthouses · San Juan Islands · State Flower · National Parks · State Parks · Wildlife Bear · Wildlife Deer · Wildlife Elk · Wildlife Steelhead · Wild on Washington Eagle · Keep WA Evergreen · Smokey Bear · Mount St. Helens

**🏆 Sports** — Seahawks · Mariners · Kraken · Sounders · Storm · Ski and Ride · Pickleball · Tennis · Wrestling

**🎓 Colleges** — WSU · UW · CWU · EWU · Evergreen State · Gonzaga · Seattle University · WWU

**🚒 First Responders** — Law Enforcement Memorial · Professional Firefighter · Volunteer Firefighter

**💙 Charity** — 4-H · Breast Cancer Awareness · FFA Foundation · Fred Hutchinson · Helping Kids Speak · J.P. Patches Pal · Keep Kids Safe · Washington Wine · We Love Our Pets

**🎨 Hobby** — Amateur Radio · Fly Washington Aviation · Music Matters · Share the Road · Square Dancer · Throwback Blackout · LeMay Car Museum

**🚗 Vehicle** — Collector · Horseless Carriage · Restored · Rideshare

**🦅 Tribal** — Chehalis · Muckleshoot · Puyallup

---

## Repo Structure

```
plate-hunter/
├── index.html            ← The entire app. Open this.
├── README.md
└── plates/
    └── WA/               ← 72 Washington plate images
        ├── seahawksPlate.png
        ├── squaredancePlate.png
        ├── NationalParksPlate.jpg
        └── ... (72 total)
```

No build step. No dependencies. No bundler. Open `index.html` in a browser and it runs.

---

## Running Locally

```bash
git clone https://github.com/bdgroves/plate-hunter
cd plate-hunter
open index.html   # macOS
# or just drag index.html into any browser
```

For GitHub Pages: **Settings → Pages → Deploy from branch `main` → `/ (root)`**

Live at: `bdgroves.github.io/plate-hunter`

---

## Roadmap

The Washington build is the foundation. Everything else stacks on top.

- [ ] All 50 US states (using [jonkeegan/us-license-plates](https://github.com/jonkeegan/us-license-plates) as the image source)
- [ ] Canadian provinces
- [ ] Mexican states — bonus tier
- [ ] React Native / Expo — iOS + Android
- [ ] Family / multiplayer mode
- [ ] Streak tracking and achievements
- [ ] Smokey Bear plate (WA DOL — coming soon)
- [ ] Mount St. Helens plate (WA DOL — pending redesign)

---

## Tech Stack

Vanilla HTML · CSS · JavaScript. localStorage for persistence. Zero frameworks, zero build tools, zero server. The whole app is one file and a folder of images. That's the point.

The pipeline that keeps it current: when new WA plates are legislated, grab the image from the DOL, add one entry to the plates array in `index.html`, push to main. Done.

---

## Image Credits

Base plate images from **[jonkeegan/us-license-plates](https://github.com/jonkeegan/us-license-plates)** — a dataset of all U.S. license plates as of July 2023, assembled by Jon Keegan for [Beautiful Public Data](https://www.beautifulpublicdata.com/).

2025 Washington additions (Pickleball, Keep WA Evergreen, Honeybees, LeMay, Throwback, Smokey Bear, Mt. St. Helens) sourced from the [Washington State Department of Licensing](https://dol.wa.gov/vehicles-and-boats/vehicles/license-plates/get-custom-plates/special-design-plates).

Rarity data from the WA DOL 2024 Report to the Legislature.

---

## Part of the brooksgroves.com ecosystem

This project lives alongside [AFTERSHOCK](https://bdgroves.github.io/aftershock), [PELE](https://bdgroves.github.io/PELE), [Rainier Snowpack](https://bdgroves.github.io/rainier-snowpack), and the rest of the [bdgroves GitHub universe](https://github.com/bdgroves). Built in the Pacific Northwest. Born in Tuolumne County.

[brooksgroves.com](https://brooksgroves.com) · [GitHub](https://github.com/bdgroves) · [Bluesky](https://bsky.app/profile/bdgroves.bsky.social)
