# Plate Hunter: what's new since mid-2023, state by state

Plate Hunter (brooksgroves.com/plate-hunter) is a road-trip game listing each state's specialty
license plates. For most states the list came from Jon Keegan's snapshot of every US plate taken
June–July 2023. Your job, for each state you're given: find the specialty plates that state has
ADDED since mid-2023 (and the ones it has RETIRED), using the state's official licensing agency
first, then news/sponsor sources. Do not re-verify the whole list; focus on changes.

What the game already has for a state: /home/claude/plate-hunter/data/<STATE>.json, "plates" list,
each with "name". Read it before searching so you can tell new from existing (names may be worded
differently: "Ducks Unlimited" vs "DU Conservation"; judge by meaning).

Only passenger plates a passer-by could see on an ordinary car count. Skip dealer, government,
legislator, motorcycle-only, trailer, commercial, taxi, temporary, and parking placards.

For each NEW plate give a picture address, best first:
  1. the licensing agency's own image of the plate (.gov or .us site),
  2. the sponsoring organization's own image,
  3. otherwise leave "source_img" null (never a news photo of a car).
Use WebSearch/WebFetch. Shell curl to websites is blocked. Don't edit anything under /home/claude/plate-hunter.

Write one file per state: /tmp/claude-0/-home-claude/16f6cead-b56d-53eb-a438-df28d8133ddc/scratchpad/since2023/<STATE>.json
{
 "state": "TX",
 "checked": ["urls you used"],
 "robot_url": "the agency page that shows the most plate pictures as plain <img> images (a gallery or list page), or null",
 "new": [{"title": "Plate name as the agency writes it", "cat": "one of military, veterans, nature, sports, colleges, firstresponder, charity, hobby, vehicle, tribal, other",
          "source_img": "https://... or null", "source": "page that confirms it", "year": "2024 (first issued) or null",
          "matches_existing": null}],
 "redesigned": [{"name_in_game": "...", "source_img": "https://...", "note": "new design issued 2025"}],
 "retired": [{"name_in_game": "...", "source": "..."}],
 "notes": "anything uncertain, in one or two sentences"
}
If a state has nothing new you can confirm, write the file with empty lists and say so in notes.
Final reply: one line per state (counts of new / redesigned / retired, and whether robot_url was found), plus anything surprising. Under 250 words.
