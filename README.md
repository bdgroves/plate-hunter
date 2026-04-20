# 🔍 PLATE HUNTER

### *Washington State · Road Trip Edition*

> "The least popular special-design plate last year was the square dancer design, on only five vehicles, despite being one of the least expensive." — Seattle Times, April 20, 2026

---

Washington has 72 specialty license plates — and most people have never noticed most of them. There's a plate for pickleball. A plate for honeybees. A plate for the Muckleshoot Tribe. A plate that's only legal on cars built before 1916. And somewhere on the roads of the Evergreen State, five vehicles are rolling around with a square dancer on the back bumper, 300 points just waiting to be claimed.

**PLATE HUNTER** is a road trip game built around that premise. You see a plate in real life, you tap it in the app. It unlocks in full color. You earn points. The rarer the plate, the more it's worth — and the rarity tiers are pulled directly from the Washington DOL's annual vehicle registration data. This isn't made up.

In 2025, nearly **184,000 Washington vehicles** carried a special-design plate, generating **$5.8 million in fees**. Add personalized plates and the number climbs to **$9.8 million**. Washingtonians take their plates seriously. PLATE HUNTER takes them seriously too.

No server. No login. No ads. Just a phone, an open road, and 72 plates to find.

**[▶ Play it now → bdgroves.github.io/plate-hunter](https://bdgroves.github.io/plate-hunter)**

---

## How It Works

Open the app on your phone before you get in the car. Browse the grid — 72 plates, all grayed out, all waiting. When you spot one in real life, tap it. It flips to full color, confetti fires, your point total climbs. Finds persist in localStorage so your collection survives across sessions. Filter by category — military, nature, sports, tribal, colleges — or flip to **✅ Found** to review your haul.

That's it. No account required.

---

## The Rarity System

Point values are grounded in real data from the **Washington DOL 2025 registration figures**, as reported by the Seattle Times. Every number below is an actual vehicle count from actual Washington roads.

| Tier | Vehicles on WA Roads | Points |
|---|---|---|
| 🟦 Common | 8,000+ | 10 pts |
| 🟩 Uncommon | 3,000 – 8,000 | 25 pts |
| 🟧 Rare | 500 – 3,000 | 50 pts |
| 🟨 **Legendary** | Under 500 | 150 – 300 pts |

### By the Numbers — 2025 DOL Data

The top of the leaderboard isn't surprising. The bottom is where it gets interesting.

| Rank | Plate | Vehicles | Annual Fees |
|---|---|---|---|
| 🥇 1 | WSU Cougars | 24,100 | $734,000 |
| 🥈 2 | Collector Vehicle | 20,300 | $710,400 |
| 🥉 3 | Washington National Parks | 12,700 | $404,000 |
| 4 | Law Enforcement Memorial | 11,300 | $351,100 |
| 5 | Seattle Seahawks | 11,100 | $336,000 |
| 6 | University of Washington | 10,300 | $313,000 |
| 7 | US Army | 7,700 | $240,300 |
| — | Seattle Mariners | 1,100 | $35,300 |
| — | Seattle University | ~200 | $6,600 |
| — | Horseless Carriage | ~140 | — |
| 💀 Last | **Square Dancer** | **5** | — |

### Legendary Tier — The White Whales

Spotting any one of these on a road trip is genuinely remarkable.

| Plate | Why It's Legendary | Points |
|---|---|---|
| 🕺 **Square Dancer** | 5 registered statewide. *Five.* | 300 |
| 🏎 **Horseless Carriage** | ~140 statewide. Pre-1916 vehicles only — operational antiques | 300 |
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

Rarity data and vehicle counts from the WA DOL 2025 registration figures, as reported by [Gene Balk / FYI Guy, Seattle Times, April 20, 2026](https://www.seattletimes.com).

---

## Part of the brooksgroves.com ecosystem

This project lives alongside [AFTERSHOCK](https://bdgroves.github.io/aftershock), [PELE](https://bdgroves.github.io/PELE), [Rainier Snowpack](https://bdgroves.github.io/rainier-snowpack), and the rest of the [bdgroves GitHub universe](https://github.com/bdgroves). Built in the Pacific Northwest. Born in Tuolumne County.

[brooksgroves.com](https://brooksgroves.com) · [GitHub](https://github.com/bdgroves) · [Bluesky](https://bsky.app/profile/bdgroves.bsky.social)
