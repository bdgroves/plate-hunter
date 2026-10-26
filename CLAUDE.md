# plate-hunter — notes for Claude

Read `HANDOFF.md` before starting: current state, open items and what bit us before. `README.md` is the
public write-up of the game, data layout and tools.

## Rules for this repo

- `git pull --rebase` first: the robot and the picture workflow commit often.
- Run `python tools/validate.py` before every commit. It must print OK.
- Commit as `git -c user.name=Claude -c user.email=noreply@anthropic.com` with the session trailers.
- Edit files in place; replace text only after confirming it appears exactly once.
- Plate ids never change once published (finds are saved by id). Rename a plate by changing `name`.
- Pictures: official only (agency or sponsor). Look at every new picture (contact sheet) before calling
  it done; take out photos of cars, watermarked or news photos, placeholders and multi-plate sheets.
- Plates no longer sold stay in the game with `"retired": true`. Missing from a catalog is not proof.
- Codes: US and Canada are 2 letters, Mexico 3 (ISO 3166-2). Never assume `code[:2]`.
- New collections: `tools/add_canada.py` (Canada and Mexico) or `tools/apply_since.py` (US changes),
  then `tools/index.py`. Never hand-edit counts in `data/collections.json`.
- Counts in commit messages and replies: compute them.

## Working with Brooks

- Windows PowerShell; no local clone and no new Python packages on his PC. Anything that needs to run,
  runs on GitHub Actions or here.
- Robot decisions: issue #1 (`/add`, `/skip`), or he asks Claude to sort the waiting list.
- Pictures from sites that refuse GitHub: `tools/grab_in_browser.js` in his Chrome, upload to `incoming/`.
- Friendly, warm tone for anything on the blog. Say plainly when something was wrong.
