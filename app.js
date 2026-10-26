/* Plate Hunter — a road-trip license plate game.
   Two games share one page:
     States     the classic: spot a plate from every state (and DC) on this trip,
                and every Canadian province and territory too
     Specialty  spot a state's special-design plates; rarer plates score more
   Everything is saved in this browser (localStorage). No server, no account. */
'use strict';

const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const store = {
  get(k, d) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* private mode: play without saving */ } },
};
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const fmtDate = ts => new Date(ts).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });

const CATS = [
  ['military', '🎖', 'Military'], ['veterans', '🎗', 'Veterans'], ['nature', '🌲', 'Nature'],
  ['sports', '🏆', 'Sports'], ['colleges', '🎓', 'Colleges'], ['firstresponder', '🚒', 'First responders'],
  ['charity', '💙', 'Charity'], ['hobby', '🎨', 'Hobby'], ['vehicle', '🚗', 'Vehicle'],
  ['tribal', '🦅', 'Tribal'], ['other', '✨', 'Other'],
];
// Points when a collection has no registration counts behind it.
const UNRATED_PTS = 20;
// Tiny states get a labeled box beside the map so they're easy to tap.
const CALLOUTS = ['VT', 'NH', 'MA', 'RI', 'CT', 'NJ', 'DE', 'MD', 'DC'];
const CALLOUTS_CA = ['PE', 'NS', 'NB'];
const CALLOUTS_MX = ['CMX', 'MOR', 'TLA', 'AGU', 'QUE'];
// The two countries in the classic game. Each keeps its own count; a trip spans both.
const COUNTRY = {
  us: { list: () => S.states, map: () => S.map, callouts: CALLOUTS, cx: 982, cy: 150, noun: 'state', label: 'USA', flag: '🇺🇸', ms: 'ms', w: 1050 },
  ca: { list: () => S.provinces, map: () => S.caMap, callouts: CALLOUTS_CA, cx: 880, cy: 700, noun: 'province', label: 'Canada', flag: '🇨🇦', ms: 'msCA', w: 960 },
  mx: { list: () => S.mexico, map: () => S.mxMap, callouts: CALLOUTS_MX, cx: 40, cy: 440, noun: 'Mexican state', label: 'Mexico', flag: '🇲🇽', ms: 'msMX', w: 960 },
};

const S = {
  view: 'states',            // 'states' | 'specialty'
  states: [], map: null, provinces: [], caMap: null, mexico: [], mxMap: null, collections: [],
  country: store.get('ph_country', 'us'),   // which map the States tab shows
  col: null,                 // the loaded specialty collection
  colCode: store.get('ph_col', 'WA'),
  filter: 'all',
  trip: store.get('ph_trip', null),        // {started, seen:{CA:ts}}
  ever: store.get('ph_states_ever', {}),   // {CA:firstSeenTs}
  trips: store.get('ph_trips', []),        // finished trips [{started, ended, count}]
  drawer: null,              // {kind:'plate'|'state', id}
};
if (!S.trip) { S.trip = { started: Date.now(), seen: {} }; store.set('ph_trip', S.trip); }

/* ---------- loading ---------- */
async function getJSON(url) { const r = await fetch(url); if (!r.ok) throw new Error(url + ' ' + r.status); return r.json(); }

async function boot() {
  [S.states, S.map, S.collections, S.provinces, S.caMap, S.mexico, S.mxMap] = await Promise.all([
    getJSON('data/states.json'), getJSON('data/us-map.json'), getJSON('data/collections.json'),
    getJSON('data/provinces.json'), getJSON('data/ca-map.json'), getJSON('data/mexico.json'), getJSON('data/mx-map.json')]);
  if (!COUNTRY[S.country]) S.country = 'us';
  if (!S.collections.find(c => c.code === S.colCode)) S.colCode = S.collections[0].code;
  const h = location.hash.replace('#', '').split('/');
  if (h[0] === 'specialty') { S.view = 'specialty'; if (h[1] && S.collections.find(c => c.code === h[1].toUpperCase())) S.colCode = h[1].toUpperCase(); }
  else if (h[0] === 'states') { S.view = 'states'; if (COUNTRY[h[1]]) S.country = h[1]; }
  else S.view = store.get('ph_view', Object.keys(store.get('ph_wa', {})).length ? 'specialty' : 'states');
  await show(S.view);
}

async function loadCollection(code) {
  const meta = S.collections.find(c => c.code === code);
  const col = await getJSON(meta.file);
  col.key = col.storageKey || 'ph_' + code.toLowerCase();
  col.found = store.get(col.key, {});
  col.msShown = store.get(col.key + '_ms', []);
  for (const p of col.plates) if (!col.rated || !p.pts) { p.rar = p.rar || 'unrated'; p.pts = p.pts || UNRATED_PTS; }
  S.col = col; S.colCode = code; S.filter = 'all'; S.q = '';
  store.set('ph_col', code);
}

/* ---------- views ---------- */
async function show(view) {
  S.view = view; store.set('ph_view', view);
  document.querySelectorAll('.tab').forEach(t => t.setAttribute('aria-selected', t.dataset.view === view));
  if (view === 'specialty' && (!S.col || S.col.code !== S.colCode)) await loadCollection(S.colCode);
  const hash = view === 'states' ? (S.country === 'us' ? '#states' : '#states/' + S.country) : '#specialty/' + S.colCode.toLowerCase();
  if (location.hash !== hash) history.replaceState(null, '', hash);
  view === 'states' ? renderStates() : renderSpecialty();
}

// Codes never clash: no province shares a postal code with a state, and Mexico's are three letters.
const region = code => S.states.find(s => s.code === code) || S.provinces.find(s => s.code === code) || S.mexico.find(s => s.code === code);
const countryOf = code => S.provinces.some(s => s.code === code) ? 'ca' : S.mexico.some(s => s.code === code) ? 'mx' : 'us';
const seenIn = (k, seen = S.trip.seen) => COUNTRY[k].list().filter(s => seen[s.code]).length;

function renderStates() {
  const k = S.country, C = COUNTRY[k], list = C.list();
  const n = seenIn(k), total = list.length, ever = seenIn(k, S.ever);
  const seg = Object.entries(COUNTRY).map(([key, c]) =>
    `<button class="ch" data-country="${key}" aria-pressed="${key === k}">${c.flag} ${c.label}<span class="n">${seenIn(key)}/${c.list().length}</span></button>`).join('');
  $('#main').innerHTML = `
  <div class="fb country" role="group" aria-label="Country">${seg}</div>
  <section class="pw" aria-label="This trip">
    <div class="pr"><span class="pl">${k === 'ca' ? 'Provinces and territories' : k === 'mx' ? 'Mexican states' : 'States'} this trip</span><span class="pn" id="pCt">${n} / ${total}</span></div>
    <div class="pt"><div class="pf" id="pFill" style="width:${n / total * 100}%"></div></div>
    <div class="st">
      <span class="pill">🗓 <span>started</span> ${esc(fmtDate(S.trip.started))}</span>
      <span class="pill">🗺 <strong id="everCt">${ever}</strong><span>ever</span></span>
      <span class="spacer"></span>
      <button class="link-btn" id="shareBtn">Share</button>
      <button class="link-btn" id="newTrip">New trip</button>
    </div>
  </section>
  <div class="map-wrap">${mapSVG()}
    <div class="map-key"><span><i style="background:var(--gold)"></i>This trip</span><span><i style="background:var(--map-ever)"></i>An earlier trip</span><span><i style="background:var(--map-off)"></i>Not yet</span></div>
  </div>
  <div class="grid sgrid" id="grid">${list.map(stateCard).join('')}</div>`;
  refreshStatus();
  $('#main').querySelector('.country').onclick = e => {
    const b = e.target.closest('[data-country]'); if (!b || b.dataset.country === S.country) return;
    S.country = b.dataset.country; store.set('ph_country', S.country);
    history.replaceState(null, '', S.country === 'us' ? '#states' : '#states/' + S.country);
    renderStates();
  };
  $('#newTrip').onclick = confirmNewTrip;
  $('#shareBtn').onclick = shareTrip;
  $('#main').querySelector('.map').addEventListener('click', e => {
    const el = e.target.closest('[data-st]'); if (el) tapState(el.dataset.st, el);
  });
  $('#main').querySelector('.map').addEventListener('keydown', e => {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    const el = e.target.closest('[data-st]'); if (el) { e.preventDefault(); tapState(el.dataset.st, el); }
  });
  $('#grid').addEventListener('click', e => {
    const b = e.target.closest('[data-st]'); if (b) tapState(b.dataset.st, b.closest('.card'));
  });
}

function mapSVG() {
  const C = COUNTRY[S.country], seen = S.trip.seen, ever = S.ever, M = C.map().states;
  const name = c => (region(c) || {}).name || c;
  const cls = c => (seen[c] ? 'found' : '') + (ever[c] ? ' ever' : '');
  let paths = '', labels = '', call = '';
  for (const s of C.list()) {
    const m = M[s.code]; if (!m) continue;
    paths += `<path d="${m.d}" class="${cls(s.code)}" data-st="${s.code}" tabindex="0" role="button" aria-pressed="${!!seen[s.code]}" aria-label="${esc(name(s.code))}"><title>${esc(name(s.code))}</title></path>`;
    if (!C.callouts.includes(s.code)) {
      const [x, y] = s.code === 'FL' ? [m.c[0] + 12, m.c[1] + 4] : s.code === 'MI' ? [m.c[0] + 10, m.c[1] + 16] : s.code === 'LA' ? [m.c[0] - 8, m.c[1]] : m.c;
      labels += `<text x="${x}" y="${y}" class="${seen[s.code] ? 'found' : ''}">${s.code}</text>`;
    }
  }
  C.callouts.forEach((c, i) => {
    const m = M[c]; if (!m) return;
    const x = C.cx, y = C.cy + i * 36;
    call += `<g class="callout ${seen[c] ? 'found' : ''}" data-st="${c}" tabindex="-1">
      <line x1="${m.c[0]}" y1="${m.c[1]}" x2="${x}" y2="${y + 15}" stroke="rgba(255,255,255,.18)" stroke-width="1"/>
      <rect x="${x}" y="${y}" width="62" height="30" rx="7"/><text x="${x + 31}" y="${y + 15.5}" class="${seen[c] ? 'found' : ''}">${c}</text></g>`;
  });
  const [, , , h] = C.map().viewBox.split(' ');
  return `<svg class="map map-${S.country}" viewBox="0 0 ${C.w} ${h}" role="group" aria-label="Map of ${{ us: 'states', ca: 'provinces and territories', mx: 'Mexican states' }[S.country]} found this trip">${paths}${call}${labels}</svg>`;
}

function plateVisual(img, code, cls = 'plate-img') {
  return img ? `<img class="${cls}" src="${esc(img)}" alt="" loading="lazy" decoding="async">`
             : `<span class="fake" aria-hidden="true"><small>${esc((region(code) || {}).name || '')}</small><b>${esc(code)}</b></span>`;
}

// A specialty plate's picture, or a drawn stand-in with its name until we have one.
function platePic(c, p, cls = 'plate-img') {
  return p.img ? `<img class="${cls}" src="plates/${c.code}/${esc(p.img)}" alt="" loading="lazy" decoding="async">`
               : `<span class="fake named" aria-hidden="true"><small>${esc(c.name)}</small><em>${esc(p.name)}</em><i>picture coming</i></span>`;
}

function stateCard(s) {
  const f = S.trip.seen[s.code];
  return `<div class="card${f ? ' found' : ''}" data-card="${s.code}">
    <button class="hit" data-st="${s.code}" aria-pressed="${!!f}" aria-label="${esc(s.name)}${f ? ', found' : ''}">
      <div class="iw">${plateVisual(s.img, s.code)}<div class="chk">✓</div></div>
      <div class="ci"><span class="cn">${esc(s.name)}</span>${f ? `<span class="seen-date">${esc(new Date(f).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }))}</span>` : ''}</div>
    </button></div>`;
}

// Plates the robot (or a person) added in the last 60 days get a NEW badge.
const isNew = p => p.added && (Date.now() - Date.parse(p.added + 'T12:00:00')) < 60 * 864e5;

const opt = k => `<option value="${k.code}"${S.colCode === k.code ? ' selected' : ''}>${esc(k.name)} (${k.count.toLocaleString()})</option>`;

function renderSpecialty() {
  const c = S.col;
  const counts = {}; c.plates.forEach(p => counts[p.cat] = (counts[p.cat] || 0) + 1);
  const fresh = c.plates.filter(isNew).length;
  const cats = CATS.filter(([k]) => counts[k]);
  $('#main').innerHTML = `
  <div class="picker">
    <label for="colPick" class="pl">State or province</label>
    <select id="colPick">
      <optgroup label="United States">${S.collections.filter(k => !k.country && k.checked !== false).map(opt).join('')}</optgroup>
      ${S.collections.some(k => !k.country && k.checked === false) ? `<optgroup label="United States, 2023 list (not checked yet)">${S.collections.filter(k => !k.country && k.checked === false).map(opt).join('')}</optgroup>` : ''}
      <optgroup label="Canada">${S.collections.filter(k => k.country === 'CA').map(opt).join('')}</optgroup>
      ${S.collections.some(k => k.country === 'MX') ? `<optgroup label="Mexico">${S.collections.filter(k => k.country === 'MX').map(opt).join('')}</optgroup>` : ''}
    </select>
  </div>
  <section class="pw" aria-label="${esc(c.name)} progress">
    <div class="pr"><span class="pl">${esc(c.name)} plates found</span><span class="pn" id="pCt"></span></div>
    <div class="pt"><div class="pf" id="pFill"></div></div>
    <div class="st">
      <span class="pill">⭐ <strong id="tPts">0</strong><span>pts</span></span>
      ${c.rated ? `<span class="pill">🏆 <strong id="lCt">0</strong><span>legendary</span></span><span class="pill">🔥 <strong id="rCt">0</strong><span>rare</span></span>` : `<span class="pill"><span>rarity not rated yet</span></span>`}
      ${c.checked === false ? `<span class="pill" title="These plates come from a 2023 snapshot of every US plate and haven't been checked against ${esc(c.name)}'s current list yet."><span>2023 list</span></span>` : ''}
      <span class="spacer"></span>
      <button class="link-btn" id="offBtn">Save for offline</button>
    </div>
  </section>
  <div class="search"><input id="q" type="search" placeholder="Search ${c.plates.length.toLocaleString()} ${esc(c.name)} plates" aria-label="Search plates by name" autocomplete="off"></div>
  <div class="fb" id="fb" role="group" aria-label="Filter plates">
    <button class="ch" data-cat="all" aria-pressed="true">All ${c.plates.length}</button>
    ${cats.map(([k, e, l]) => `<button class="ch" data-cat="${k}" aria-pressed="false">${e} ${l}<span class="n">${counts[k]}</span></button>`).join('')}
    ${fresh ? `<button class="ch" data-cat="new" aria-pressed="false">🆕 New<span class="n">${fresh}</span></button>` : ''}
    <button class="ch" data-cat="found" aria-pressed="false">✅ Found</button>
  </div>
  <div class="grid" id="grid"></div>`;
  $('#colPick').onchange = async e => { await loadCollection(e.target.value); show('specialty'); };
  $('#q').oninput = e => { S.q = e.target.value.trim().toLowerCase(); renderGrid(); };
  $('#fb').onclick = e => {
    const ch = e.target.closest('.ch'); if (!ch) return;
    S.filter = ch.dataset.cat;
    document.querySelectorAll('#fb .ch').forEach(x => x.setAttribute('aria-pressed', x === ch));
    renderGrid();
  };
  $('#grid').onclick = e => {
    const info = e.target.closest('[data-info]'); if (info) return openPlate(info.dataset.info);
    const hit = e.target.closest('[data-id]'); if (hit) tapPlate(hit.dataset.id);
  };
  $('#offBtn').onclick = saveOffline;
  checkOffline();
  renderGrid(); plateStats(); refreshStatus();
}

function renderGrid() {
  const c = S.col, f = S.filter;
  let list = f === 'all' ? c.plates : f === 'found' ? c.plates.filter(p => c.found[p.id])
    : f === 'new' ? c.plates.filter(isNew) : c.plates.filter(p => p.cat === f);
  if (S.q) list = list.filter(p => p.name.toLowerCase().includes(S.q));
  $('#grid').innerHTML = list.length ? list.map(p => {
    const fd = !!c.found[p.id];
    return `<div class="card${fd ? ' found' : ''}" data-card="${p.id}">
      <button class="hit" data-id="${p.id}" aria-pressed="${fd}" aria-label="${esc(p.name)}${fd ? ', found. Open details' : ', mark as found'}">
        <div class="iw">${platePic(c, p)}<div class="chk">✓</div></div>
      </button>
      <button class="hit ci" data-info="${p.id}" aria-label="About the ${esc(p.name)} plate">
        <div class="cn">${isNew(p) ? '<span class="newb">NEW</span> ' : ''}${esc(p.name)}</div>
        <div class="cm"><span class="rar r-${p.rar}">${p.rar}</span><span class="pts">+${p.pts} pts</span></div>
      </button></div>`;
  }).join('') : `<div class="empty"><b>🔍</b>${S.q ? `No plate matches “${esc(S.q)}”.` : f === 'found' ? 'No plates found yet.<br>Get out there and start hunting!' : 'Nothing here.'}</div>`;
}

function plateStats() {
  const c = S.col, fp = c.plates.filter(p => c.found[p.id]);
  $('#pCt').textContent = `${fp.length} / ${c.plates.length}`;
  $('#pFill').style.width = `${fp.length / c.plates.length * 100}%`;
  $('#tPts').textContent = fp.reduce((s, p) => s + p.pts, 0).toLocaleString();
  if ($('#lCt')) { $('#lCt').textContent = fp.filter(p => p.rar === 'legendary').length; $('#rCt').textContent = fp.filter(p => p.rar === 'rare').length; }
  return fp.length;
}

/* ---------- marking finds ---------- */
// A tap marks a plate found. Tapping a found plate opens its card, where it can be unmarked,
// so a bump in a moving car can't erase a find.
function tapPlate(id) {
  const c = S.col, p = c.plates.find(x => x.id === id); if (!p) return;
  if (c.found[id]) return openPlate(id);
  setPlate(id, true);
  const card = document.querySelector(`[data-card="${id}"]`);
  confetti(card);
  const m = { legendary: `🏆 LEGENDARY! ${p.name}`, rare: `🔥 Rare find! ${p.name}`, uncommon: `✨ Nice! ${p.name}`, common: `✓ Spotted! ${p.name}`, unrated: `✓ Spotted! ${p.name}` };
  toast(`${m[p.rar] || m.common} +${p.pts}`, p.rar === 'legendary' ? 'var(--y)' : p.rar === 'rare' ? 'var(--o)' : 'var(--g)', () => setPlate(id, false));
  milestone(plateStats(), c.plates.length, c.msShown, c.key + '_ms', `${c.name} plate`);
}

function setPlate(id, on) {
  const c = S.col;
  on ? (c.found[id] = Date.now()) : delete c.found[id];
  store.set(c.key, c.found);
  const card = document.querySelector(`[data-card="${id}"]`);
  if (card) {
    card.classList.toggle('found', on);
    const hit = card.querySelector('[data-id]'); if (hit) hit.setAttribute('aria-pressed', on);
    if (on) { card.classList.add('pop'); setTimeout(() => card.classList.remove('pop'), 350); }
  }
  if (S.filter === 'found') renderGrid();
  plateStats(); refreshStatus();
  if (S.drawer && S.drawer.id === id) openPlate(id);
}

function tapState(code, el) {
  if (S.trip.seen[code]) return openState(code);
  confetti(el);
  setState(code, true);
  const st = region(code), k = countryOf(code), C = COUNTRY[k];
  toast(`🚗 ${st.name}!  ${seenIn(k)} of ${C.list().length}`, 'var(--g)', () => setState(code, false));
  milestone(seenIn(k), C.list().length, S.trip[C.ms] || (S.trip[C.ms] = []), null, C.noun);
}

function setState(code, on) {
  if (on) { S.trip.seen[code] = Date.now(); if (!S.ever[code]) S.ever[code] = Date.now(); }
  else {
    const ts = S.trip.seen[code]; delete S.trip.seen[code];
    // Undoing a first-ever sighting removes it from the lifetime list too.
    if (S.ever[code] === ts) delete S.ever[code];
  }
  store.set('ph_trip', S.trip); store.set('ph_states_ever', S.ever);
  if (S.view === 'states') renderStates();
  if (S.drawer && S.drawer.id === code) openState(code);
}

function tripLine(us, ca, mx = seenIn('mx')) {
  const parts = [`${us} of ${S.states.length} states`];
  if (ca) parts.push(`${ca} of ${S.provinces.length} provinces and territories`);
  if (mx) parts.push(`${mx} of ${S.mexico.length} Mexican states`);
  return parts.length > 1 ? parts.slice(0, -1).join(', ') + ' and ' + parts.at(-1) : parts[0];
}

function confirmNewTrip() {
  const n = Object.keys(S.trip.seen).length, us = seenIn('us'), ca = seenIn('ca');
  openSheet(`<div class="drawer-body sheet-text">
    <div class="drawer-name">Start a new trip?</div>
    <p>This trip found <b>${tripLine(us, ca)}</b> since ${esc(fmtDate(S.trip.started))}. A new trip clears the maps. Your “ever seen” list and specialty finds stay.</p>
    <div class="row"><button class="btn" id="ntGo">Start new trip</button><button class="btn ghost" data-close>Keep this one</button></div></div>`);
  $('#ntGo').onclick = () => {
    if (n) { S.trips.unshift({ started: S.trip.started, ended: Date.now(), count: us, ca, mx: seenIn('mx') }); store.set('ph_trips', S.trips.slice(0, 50)); }
    S.trip = { started: Date.now(), seen: {} }; store.set('ph_trip', S.trip);
    closeDrawer(); renderStates(); toast('🛣 New trip started. Good hunting!', 'var(--y)');
  };
}

async function shareTrip() {
  const text = `I've spotted plates from ${tripLine(seenIn('us'), seenIn('ca'))} on this trip with Plate Hunter 🚗`;
  const url = location.origin + location.pathname;
  try {
    if (navigator.share) await navigator.share({ title: 'Plate Hunter', text, url });
    else { await navigator.clipboard.writeText(text + ' ' + url); toast('Copied to clipboard', 'var(--y)'); }
  } catch (e) { /* share sheet dismissed */ }
}

/* ---------- drawers ---------- */
function openSheet(html) {
  $('#toast').classList.remove('show');
  $('#drawerInner').innerHTML = html;
  $('#overlay').classList.add('show'); $('#drawer').classList.add('show');
  $('#drawer').querySelectorAll('[data-close]').forEach(b => b.onclick = closeDrawer);
  setTimeout(() => ($('#drawer').querySelector('button:not(.drawer-x)') || $('#drawerX')).focus({ preventScroll: true }), 50);
}
function closeDrawer() {
  $('#overlay').classList.remove('show'); $('#drawer').classList.remove('show');
  const back = S.drawer && document.querySelector(`[data-card="${S.drawer.id}"] button`);
  S.drawer = null; if (back) back.focus({ preventScroll: true });
}

function openPlate(id) {
  const c = S.col, p = c.plates.find(x => x.id === id), f = c.found[id];
  S.drawer = { kind: 'plate', id };
  openSheet(`<div class="drawer-img-wrap">${platePic(c, p, 'drawer-img')}</div>
  <div class="drawer-body">
    <h2 class="drawer-name" id="dTitle">${esc(p.name)}</h2>
    <div class="drawer-meta"><span class="rar r-${p.rar}">${p.rar}</span><span class="pts">+${p.pts} pts</span>
      ${p.year ? `<span>First issued ${esc(p.year)}</span>` : ''}${p.retired ? '<span>No longer sold, still on the road</span>' : ''}${p.vehicles ? `<span>🚗 ${esc(vehiclesLine(p.vehicles, c.name))}</span>` : ''}</div>
    ${p.fact ? `<div class="fact-box"><div class="fact-label">💡 Did you know?</div><div class="info-text">${esc(p.fact)}</div></div>` : ''}
    ${p.supports ? `<div class="info-section"><div class="info-label">Supports</div><div class="info-text">${esc(p.supports)}</div></div>` : ''}
    ${f ? `<div class="info-section"><div class="info-label">Found</div><div class="info-text">${esc(fmtDate(f))}</div></div>` : ''}
    <button class="collect${f ? ' found-btn' : ''}" id="dBtn">${f ? '✓ Found. Tap to unmark' : 'Mark as found'}</button>
  </div>`);
  $('#dBtn').onclick = () => f ? setPlate(id, false) : (closeDrawer(), tapPlate(id));
}

// "~100 (2023)" -> "~100 on Washington roads (2023 count)"; "New in 2026" stays as it is.
function vehiclesLine(v, state) {
  const m = String(v).match(/^(.*?)\s*\((\d{4})\)\s*$/);
  if (m) return `${m[1]} on ${state} roads (${m[2]} count)`;
  return /\d/.test(v) && !/^new/i.test(v) ? `${v} on ${state} roads` : v;
}

function openState(code) {
  const s = region(code), f = S.trip.seen[code], ev = S.ever[code];
  const col = S.collections.find(c => c.code === code);
  S.drawer = { kind: 'state', id: code };
  openSheet(`<div class="drawer-img-wrap">${plateVisual(s.img, code, 'drawer-img')}</div>
  <div class="drawer-body">
    <h2 class="drawer-name">${esc(s.name)}</h2>
    ${s.note ? `<div class="fact-box"><div class="info-text">${esc(s.note)}</div></div>` : ''}
    <div class="info-section"><div class="info-label">This trip</div><div class="info-text">${f ? 'Spotted ' + esc(fmtDate(f)) : 'Not yet'}</div></div>
    ${ev ? `<div class="info-section"><div class="info-label">First ever</div><div class="info-text">${esc(fmtDate(ev))}</div></div>` : ''}
    ${col ? `<div class="info-section"><div class="info-text"><a href="#specialty/${code.toLowerCase()}" id="goCol">Hunt ${esc(s.name)}’s ${col.count} specialty plates →</a></div></div>` : ''}
    <button class="collect${f ? ' found-btn' : ''}" id="dBtn">${f ? '✓ Spotted. Tap to unmark' : 'Mark as spotted'}</button>
  </div>`);
  $('#dBtn').onclick = () => f ? setState(code, false) : (closeDrawer(), tapState(code, document.querySelector(`[data-card="${code}"]`)));
  if ($('#goCol')) $('#goCol').onclick = async e => { e.preventDefault(); closeDrawer(); S.colCode = code; await loadCollection(code); show('specialty'); scrollTo(0, 0); };
}

function openAbout() {
  S.drawer = { kind: 'about', id: null };
  const total = S.collections.reduce((s, c) => s + c.count, 0).toLocaleString();
  const unchecked = S.collections.filter(c => c.checked === false).map(c => esc(c.name)).join(', ').replace(/, ([^,]*)$/, ' and $1');
  openSheet(`<div class="drawer-body sheet-text">
    <h2 class="drawer-name">How to play</h2>
    <p><b>States</b> is the classic road-trip game. Every time you see a plate from a new state, tap it on the map or in the list. Switch to <b>Canada</b> for the 10 provinces and 3 territories, or <b>Mexico</b> for its 32 states; each country keeps its own count. Start a new trip when you set off again; the places you've ever seen are kept.</p>
    <p><b>Specialty</b> is the deep cut: ${total} special-design plates from every US state, Canadian province and territory, and Mexican state. Tap a plate when you spot it. ${unchecked ? `Most lists are checked against the state's or province's current one; ${unchecked} still come from a 2023 snapshot, so a few plates there may be retired or missing.` : `Every list is checked against the state's or province's current one, and a robot looks for new plates twice a week.`} Plates no longer sold stay in the game, because they're still on the road. Rarer plates are worth more. In Washington the points come from how many vehicles really carry each plate, from the Department of Licensing's own counts. Everywhere else isn't rated yet, so every plate there is worth the same.</p>
    <p>Tapped the wrong one? Use <b>Undo</b>, or open the plate and unmark it.</p>
    <h3>Your progress</h3>
    <p>Everything is saved in this browser on this device, with no account. To move it to another phone, save a backup and open it there.</p>
    <div class="row"><button class="link-btn y" id="bkSave">Save a backup</button><label class="link-btn" for="bkLoad">Restore a backup</label><input type="file" id="bkLoad" accept="application/json" class="sr"></div>
    <h3>Install it</h3>
    <p>On a phone, use your browser's <b>Add to Home Screen</b>. Plate Hunter then opens like an app and works with no signal; tap <b>Save for offline</b> in a specialty collection first to keep all of its pictures.</p>
    <h3>Where the plates come from</h3>
    <p>Plate images: state and provincial licensing agencies and the plates' sponsors, many US ones via Jon Keegan's <a href="https://github.com/jonkeegan/us-license-plates" target="_blank" rel="noopener">US license plates dataset</a> (2023) for Beautiful Public Data. Washington counts: WA DOL's Special License Plate Annual Report to the Legislature, and 2025 figures reported by the Seattle Times. Spot a plate that's missing? <a href="https://github.com/bdgroves/plate-hunter/issues/new?title=New%20plate%3A%20" target="_blank" rel="noopener">Tell us on GitHub</a>.</p>
    ${S.trips.length ? `<h3>Past trips</h3><ul>${S.trips.slice(0, 8).map(t => `<li>${esc(fmtDate(t.started))} to ${esc(fmtDate(t.ended))}: ${t.count} states${t.ca ? `, ${t.ca} provinces` : ''}${t.mx ? `, ${t.mx} Mexican states` : ''}</li>`).join('')}</ul>` : ''}
    <button class="btn ghost" data-close>Close</button></div>`);
  $('#bkSave').onclick = backup;
  $('#bkLoad').onchange = restore;
}

/* ---------- backup ---------- */
function backup() {
  const data = { app: 'plate-hunter', version: 2, saved: new Date().toISOString(), keys: {} };
  try { for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); if (k.startsWith('ph_')) data.keys[k] = localStorage.getItem(k); } } catch (e) { }
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([JSON.stringify(data, null, 1)], { type: 'application/json' }));
  a.download = `plate-hunter-backup-${new Date().toISOString().slice(0, 10)}.json`;
  a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}
async function restore(e) {
  const file = e.target.files[0]; if (!file) return;
  try {
    const data = JSON.parse(await file.text());
    if (data.app !== 'plate-hunter' || !data.keys) throw new Error('not a backup');
    for (const [k, v] of Object.entries(data.keys)) if (k.startsWith('ph_')) localStorage.setItem(k, v);
    location.reload();
  } catch (err) { toast("That file isn't a Plate Hunter backup", 'var(--r)'); }
}

/* ---------- offline pictures ---------- */
function plateUrls(c) { return c.plates.filter(p => p.img).map(p => new URL(`plates/${c.code}/${p.img}`, location.href).href); }
async function checkOffline() {
  if (!('caches' in window)) return $('#offBtn').remove();
  const cache = await caches.open('ph-plates');
  const urls = plateUrls(S.col);
  const hits = await Promise.all(urls.map(u => cache.match(u)));
  if (hits.every(Boolean) && $('#offBtn')) { $('#offBtn').textContent = '✓ Saved offline'; $('#offBtn').disabled = true; }
}
async function saveOffline() {
  const b = $('#offBtn'); b.disabled = true; b.textContent = 'Saving…';
  try {
    const cache = await caches.open('ph-plates');
    const urls = plateUrls(S.col); let done = 0;
    await Promise.all(urls.map(async u => { if (!(await cache.match(u))) await cache.add(u); b.textContent = `Saving ${++done}/${urls.length}`; }));
    b.textContent = '✓ Saved offline';
  } catch (e) { b.disabled = false; b.textContent = 'Save for offline'; toast("Couldn't save every picture. Try again with a signal.", 'var(--r)'); }
}

/* ---------- celebrations ---------- */
const CC = ['#c8922a', '#4a5c45', '#8b3a2a', '#2a4a6b', '#d9a63f', '#83a077'];
function confetti(el) {
  if (!el || reduceMotion) return;
  const r = el.getBoundingClientRect(), b = document.createElement('div');
  b.className = 'burst'; b.style.cssText = `left:${r.left + r.width / 2}px;top:${r.top + r.height / 2}px`;
  for (let i = 0; i < 20; i++) {
    const bit = document.createElement('div'); bit.className = 'bit';
    const a = i / 20 * 2 * Math.PI, d = 45 + Math.random() * 60, s = 5 + Math.random() * 6;
    bit.style.cssText = `background:${CC[i % CC.length]};width:${s}px;height:${s}px;--tx:${Math.cos(a) * d}px;--ty:${Math.sin(a) * d}px;--tr:${Math.random() * 360}deg;left:-3px;top:-3px`;
    b.appendChild(bit);
  }
  document.body.appendChild(b); setTimeout(() => b.remove(), 850);
}

let tT;
function toast(msg, color, undo) {
  const t = $('#toast');
  t.innerHTML = `<span class="msg">${esc(msg)}</span>${undo ? '<button type="button">Undo</button>' : ''}`;
  t.style.borderColor = color || 'var(--g)';
  if (undo) t.querySelector('button').onclick = () => { undo(); t.classList.remove('show'); };
  t.classList.add('show'); clearTimeout(tT); tT = setTimeout(() => t.classList.remove('show'), undo ? 4500 : 2600);
}

function milestone(count, total, shown, key, noun) {
  const steps = [
    [1, '🚗', 'First one!', `Your very first ${noun}. The hunt is on.`],
    [5, '👀', 'Eyes open!', `5 down. You're on a roll.`],
    [10, '🔍', 'Plate detective', `10! Sharp eyes, hunter.`],
    [Math.round(total / 4), '⭐', 'A quarter there', `${Math.round(total / 4)} of ${total}.`],
    [Math.round(total / 2), '🔥', 'Halfway!', `${Math.round(total / 2)} of ${total}. Seriously impressive.`],
    [total - 1, '🫣', 'One to go', 'Just one left. Keep your eyes peeled.'],
    [total, '🏆', 'Complete!', `All ${total}. Legendary.`],
  ];
  const m = steps.find(s => s[0] === count && !shown.includes(count)); if (!m) return;
  shown.push(count); key ? store.set(key, shown) : store.set('ph_trip', S.trip);
  setTimeout(() => {
    $('#msEm').textContent = m[1]; $('#msTi').textContent = m[2]; $('#msSu').textContent = m[3];
    $('#ms').classList.add('show'); $('#msBtn').focus({ preventScroll: true });
  }, 600);
}

/* ---------- the status bar and badge (same strip as the other games) ---------- */
function refreshStatus() {
  const parts = [
    `Trip <b>${seenIn('us')}/${S.states.length || 51}</b>`,
    ...(S.provinces.length && (S.country === 'ca' || seenIn('ca')) ? [`Canada <b>${seenIn('ca')}/${S.provinces.length}</b>`] : []),
    ...(S.mexico.length && (S.country === 'mx' || seenIn('mx')) ? [`Mexico <b>${seenIn('mx')}/${S.mexico.length}</b>`] : []),
    `Since <b>${esc(new Date(S.trip.started).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }))}</b>`,
    `Ever <b>${Object.keys(S.ever).length}</b>`,
  ];
  if (S.col) {
    const fp = S.col.plates.filter(p => S.col.found[p.id]);
    parts.push(`${esc(S.col.code)} plates <b>${fp.length}/${S.col.plates.length}</b>`, `Points <b>${fp.reduce((s, p) => s + p.pts, 0).toLocaleString()}</b>`);
  }
  $('#statusbar').innerHTML = parts.map(x => `<span>${x}</span>`).join('');
  $('#badge').textContent = S.view === 'states' ? 'States' : (S.col ? S.col.name : 'Specialty');
}

/* ---------- wiring ---------- */
(() => {
  const root = document.documentElement, tb = $('#theme-toggle');
  const sync = () => { tb.textContent = root.getAttribute('data-theme') === 'dark' ? '\u25d0' : '\u25d1'; };
  sync();
  tb.onclick = () => {
    const dark = root.getAttribute('data-theme') === 'dark';
    dark ? root.removeAttribute('data-theme') : root.setAttribute('data-theme', 'dark');
    try { localStorage.setItem('bg_theme', dark ? 'light' : 'dark'); } catch (e) { }
    sync();
  };
})();
document.querySelectorAll('.tab').forEach(t => t.onclick = () => { show(t.dataset.view); });
$('#overlay').onclick = closeDrawer;
$('#drawerX').onclick = closeDrawer;
$('#aboutBtn').onclick = openAbout;
$('#msBtn').onclick = () => $('#ms').classList.remove('show');
addEventListener('keydown', e => { if (e.key === 'Escape') { closeDrawer(); $('#ms').classList.remove('show'); } });
addEventListener('hashchange', () => {
  const h = location.hash.replace('#', '').split('/');
  if (h[0] === 'states') { const k = COUNTRY[h[1]] ? h[1] : 'us'; if (S.view !== 'states' || k !== S.country) { S.country = k; show('states'); } }
  if (h[0] === 'specialty') { const c = (h[1] || S.colCode).toUpperCase(); if (S.view !== 'specialty' || c !== S.colCode) { S.colCode = c; show('specialty'); } }
});
if ('serviceWorker' in navigator && location.protocol !== 'file:') navigator.serviceWorker.register('sw.js').catch(() => { });
boot().catch(err => {
  console.error(err);
  $('#main').innerHTML = `<div class="empty"><b>🚧</b>Plate Hunter couldn't load its plate lists.<br>Check your connection and reload.</div>`;
});
