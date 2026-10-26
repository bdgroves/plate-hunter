# Plate Hunter: third pass on partly checked states

Read /tmp/claude-0/-home-claude/16f6cead-b56d-53eb-a438-df28d8133ddc/scratchpad/since2023/BRIEF.md first: same game, same rules
(official agency or sponsor pictures only, passenger plates only, don't edit the repo, no shell curl).
Your earlier colleagues already researched these states and the game has their results. Their
notes are in /home/claude/plate-hunter/research/since2023/<STATE>.json ("notes" says what they couldn't reach).
The game's current list is /home/claude/plate-hunter/data/<STATE>.json.

This pass has two jobs per state, in this order:
1. PICTURES. /tmp/claude-0/-home-claude/16f6cead-b56d-53eb-a438-df28d8133ddc/scratchpad/since2023/pass3/<STATE>-nopic.json lists plates in the game
   with no picture. Find official plate images for as many as you can (agency site, or the sponsor's own
   page). Agency plate images often share one folder; once you find the pattern, you can fill many at once
   by fetching the agency's list page and reading the image addresses from it.
2. GAPS. Plates added since mid-2023 that the earlier pass missed (its notes say where it got stuck).

Write /tmp/claude-0/-home-claude/16f6cead-b56d-53eb-a438-df28d8133ddc/scratchpad/since2023/pass3/<STATE>.json with the same fields as BRIEF.md's file
("state", "checked", "robot_url", "new", "redesigned", "retired", "notes") plus
  "pictures": [{"name_in_game": "exact name from the nopic list", "source_img": "https://..."}]
Set "complete": true only if you believe the state's list is now fully checked against its current catalog.

All agents share 200 web searches this round; stay within the budget you're given. Search to find a page,
then WebFetch it and what it links to rather than searching again.
Final reply under 200 words: per state, pictures found / new / complete?, and anything surprising.
