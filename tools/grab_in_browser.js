// Plate Hunter: download waiting plate pictures from a site that only answers real browsers.
// Open the agency's site in Chrome (e.g. https://www.ilsos.gov/), press F12, Console tab, paste this
// and press Enter (Chrome may ask you to type "allow pasting" first). Allow "multiple downloads" if asked.
// Files land in Downloads as STATE--plate-id.ext; upload them to
// https://github.com/bdgroves/plate-hunter/upload/main/incoming and fetch-pictures does the rest.
(async () => {
  const raw = 'https://raw.githubusercontent.com/bdgroves/plate-hunter/main/';
  let n = 0;
  for (const c of await (await fetch(raw + 'data/collections.json')).json()) {
    const doc = await (await fetch(raw + c.file)).json();
    for (const p of doc.plates) {
      if (!p.img_url || new URL(p.img_url).hostname !== location.hostname) continue;
      try {
        const blob = await (await fetch(p.img_url)).blob();
        const ext = (new URL(p.img_url).pathname.match(/\.(gif|png|jpe?g|webp)$/i) || ['.img'])[0];
        const a = Object.assign(document.createElement('a'),
          { href: URL.createObjectURL(blob), download: `${c.code}--${p.id}${ext}` });
        document.body.append(a); a.click(); a.remove();
        n++; await new Promise(r => setTimeout(r, 300));
      } catch (e) { console.warn('couldn\'t get', p.name, e); }
    }
  }
  // everyday plates waiting for a picture, saved as standard--CODE.ext
  for (const list of ['data/states.json', 'data/provinces.json', 'data/mexico.json']) {
    for (const s of await (await fetch(raw + list)).json()) {
      if (!s.img_url || new URL(s.img_url).hostname !== location.hostname) continue;
      try {
        const blob = await (await fetch(s.img_url)).blob();
        const ext = (new URL(s.img_url).pathname.match(/\.(gif|png|jpe?g|webp)$/i) || ['.img'])[0];
        const a = Object.assign(document.createElement('a'),
          { href: URL.createObjectURL(blob), download: `standard--${s.code}${ext}` });
        document.body.append(a); a.click(); a.remove();
        n++; await new Promise(r => setTimeout(r, 300));
      } catch (e) { console.warn('couldn\'t get', s.name, e); }
    }
  }
  console.log(`${n} picture(s) downloaded. Upload them at https://github.com/bdgroves/plate-hunter/upload/main/incoming`);
})();
