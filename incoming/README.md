# Pictures handed in by a person

Some agency sites refuse GitHub's servers (Illinois's does), so their plate pictures can't be
downloaded by `fetch-pictures.yml`. Fetch them at home instead:

1. In PowerShell:
   `& ([scriptblock]::Create((irm https://raw.githubusercontent.com/bdgroves/plate-hunter/main/tools/grab_pictures.ps1)))`
   (add `-State IL` at the end for one state). It saves them to `Downloads\plate-pictures\<STATE>\<plate id>.<ext>`.
2. Open https://github.com/bdgroves/plate-hunter/upload/main/incoming and drag the state folder(s) in.
   Commit straight to main.
3. `fetch-pictures.yml` runs, turns each into the game's 480 px WebP, points the plate at it, and
   removes the used files from here. Anything left over (not plate-shaped, unknown id) stays for a look.
