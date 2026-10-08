/* Cross-City Urban Explorer: UI. Data comes from data.js (window.VIZ_DATA), computation from model.js (window.VizModel).
   One reference unit and one comparison set are shared by every view; each method keeps its own settings and baseline. */
(() => {
  'use strict';
  const V = window.VIZ_DATA, M = window.VizModel, N = V.units.length, U = V.units;
  const IDX = Object.fromEntries(U.map((u, i) => [u.id, i]));
  const CITY = { SP: 'São Paulo', CHI: 'Chicago' };
  const OTHER = { SP: 'CHI', CHI: 'SP' };
  const POOL = { SP: [], CHI: [] };
  U.forEach((u, i) => POOL[u.city].push(i));
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const clone = (o) => JSON.parse(JSON.stringify(o));
  const nf = (d) => new Intl.NumberFormat('en-US', { maximumFractionDigits: d, minimumFractionDigits: d });
  const fmt = (x, d = 3) => (x === null || x === undefined || x !== x ? '—' : nf(d).format(x));
  const pct = (x, d = 0) => (x === null || x !== x ? '—' : nf(d).format(100 * x) + '%');
  const label = (i) => `${U[i].name} (${U[i].city === 'SP' ? 'SP' : 'CHI'})`;
  const cityTag = (i) => `<span class="citytag ${U[i].city}">${U[i].city === 'SP' ? 'SP' : 'CHI'}</span>`;

  /* ---------------------------------------------------------------- methods and state */
  const AB_F = V.ab.factors.map((f) => f.id);
  const H_F = V.h.families.map((f) => f.id);
  const COLS = Object.fromEntries(V.h.columns.map((c) => [c.id, c]));
  const FAM = Object.fromEntries(V.h.families.map((f) => [f.id, f]));
  const ones = (ids) => Object.fromEntries(ids.map((f) => [f, 1]));
  const METHODS = {
    A: { tab: 'index-a', doc: 'doc-a', name: 'Cross-City Urban Index A', short: 'Index A', feats: AB_F,
      def: 'Six factors counted per unit (commerce, dwellings, transit stops, building height, street segments, street length), min–max scaled over the 173 units and summed. The agreed rule calls two units alike when their index values are close.',
      defaults: { weights: ones(AB_F), off: {}, rule: 'gap', k: 0 } },
    B: { tab: 'index-b', doc: 'doc-b', name: 'Cross-City Urban Index B', short: 'Index B', feats: AB_F,
      def: 'The Index A sketch with counts divided by land area and GHSL height for both cities. Same scaling and weights, so differences from Index A come from those two corrections.',
      defaults: { weights: ones(AB_F), off: {}, rule: 'gap', k: 0 } },
    H: { tab: 'harmonized', doc: 'doc-h', name: 'Harmonized cross-city similarity model', short: 'Harmonized', feats: H_F,
      def: `${V.h.columns.length} measurements in ${H_F.length} feature families, standardized on a common scale (C6) and combined into a calibrated distance with equal family budgets. Two units are alike when their whole profile is close.`,
      defaults: { weights: ones(H_F), off: {}, cols: {}, scaling: 'hybrid', geometry: 'full', k: 0 } },
  };
  const TAB_METHOD = { 'index-a': 'A', 'index-b': 'B', harmonized: 'H' };
  const TABS = ['overview', 'doc-a', 'doc-b', 'doc-h', 'index-a', 'index-b', 'harmonized'];
  const state = {
    tab: 'overview', ref: IDX[V.meta.reference], compare: [],
    cfg: { A: clone(METHODS.A.defaults), B: clone(METHODS.B.defaults), H: clone(METHODS.H.defaults) },
    base: { A: null, B: null, H: null },                  // null = the published settings
    ui: Object.fromEntries(['A', 'B', 'H'].map((m) => [m, { breakdown: true, mapBy: 'distance', heat: 'nbhd', pcx: 0, pcy: 1, pcColor: 'city' }])),
  };
  /* Families with several scalar columns in one block (M4, U1) can be reweighted inside (column weights, cfg.cols). */
  const MIX = Object.fromEntries(V.h.scalings.hybrid.blocks.filter((b) => b.block !== 'composition' && b.columns.length > 1).map((b) => [b.family, b.columns]));
  const colW = (cfg, c) => (cfg.cols && c in cfg.cols ? +cfg.cols[c] : 1);
  const mixEmpty = (cfg, f) => !!MIX[f] && MIX[f].every((c) => !(colW(cfg, c) > 0));
  const weightsOf = (cfg, m) => Object.fromEntries(METHODS[m].feats.map((f) => [f, cfg.off[f] || (m === 'H' && mixEmpty(cfg, f)) ? 0 : +cfg.weights[f]]));
  const baseCfg = (m) => state.base[m] || METHODS[m].defaults;
  /* Canonical form of a settings object: switched-off features as a sorted list, so the order of clicks does not matter. */
  const canon = (m, cfg) => JSON.stringify({ ...cfg, off: Object.keys(cfg.off).filter((f) => cfg.off[f]).sort(), weights: METHODS[m].feats.map((f) => +cfg.weights[f]),
    cols: Object.entries(cfg.cols || {}).filter(([, v]) => +v !== 1).map(([c, v]) => [c, +v]).sort() });
  /* Published runs as settings: R1 and R2 equal weights; R3 drops the pruned columns (a one-column family is switched off). */
  function presetCfg(name, c) {
    const out = { ...clone(c), weights: ones(H_F), off: {}, cols: {}, geometry: name === 'R2' ? 'pca' : 'full' };
    if (name === 'R3') V.h.r3_dropped_columns[c.scaling].forEach((col) => { const f = COLS[col].family; if (MIX[f]) out.cols[col] = 0; else out.off[f] = true; });
    return out;
  }

  /* ---------------------------------------------------------------- computation (memoized) */
  const blocksCache = new Map();
  function blocksFor(cfg) {
    const key = cfg.scaling + JSON.stringify(Object.entries(cfg.cols || {}).sort());
    if (!blocksCache.has(key)) {
      if (blocksCache.size > 30) blocksCache.delete(blocksCache.keys().next().value);
      blocksCache.set(key, M.blockMatrices(V.h.scalings[cfg.scaling].blocks, N, cfg.cols || {}));
    }
    return blocksCache.get(key);
  }
  const memo = new Map();

  function run(m, cfg, base) {
    const key = m + canon(m, cfg) + '|' + (base ? canon(m, base.cfg) : 'self');
    if (memo.has(key)) return memo.get(key);
    const w = weightsOf(cfg, m);
    let D, Dfull, contrib = null, index = null;
    if (!Object.values(w).some((v) => v > 0)) return { error: 'Every feature is switched off. Turn at least one back on.' };
    if (m === 'H') {
      const r = M.harmonizedDistance(blocksFor(cfg), w, N);
      D = Dfull = r.D; contrib = r.contrib;
    } else {
      const r = M.indexModel(V.ab[m].scaled, AB_F, w, N);
      index = r.index; Dfull = r.profile; D = cfg.rule === 'gap' ? r.gap : r.profile;
    }
    if (Dfull.some((v) => v !== v)) {
      return { error: 'Some pairs share no active feature: O\'Hare, Marsilac and Parelheiros have no U1 land shares. Turn on another family.' };
    }
    const P = M.pcoa(Dfull, N, base && !base.error ? base.P.scores : null);
    let E = P.scores;
    if (m === 'H' && cfg.geometry === 'pca') { D = M.euclidean(P.scores, N, P.k90); E = P.scores.map((r) => r.slice(0, P.k90)); }
    const C = M.clusters(E, N, +cfg.k || 0, base && !base.error ? base.C.labels : null);
    const axes = axesFor(m, cfg);
    const load = M.loadings(P.scores, Object.fromEntries(loadingCols(m, cfg).map((c) => [c.name, c.values])), N, Math.min(6, P.scores[0].length));
    const res = { m, cfg: clone(cfg), w, D, Dfull, contrib, index, P, C, axes, load };
    if (memo.size > 40) memo.delete(memo.keys().next().value);
    memo.set(key, res);
    return res;
  }
  const baseline = (m) => run(m, baseCfg(m), null);
  const current = (m) => run(m, state.cfg[m], baseline(m));
  const sameAsBase = (m) => canon(m, state.cfg[m]) === canon(m, baseCfg(m));

  /* Standardized axes (radar, maps, cluster profiles) and loading columns. */
  function axesFor(m, cfg) {
    if (m !== 'H') {
      const meth = m;
      return V.ab.factors.map((f) => ({
        id: f.id, code: f.id, label: f.name, short: { C: 'Commerce', R: 'Dwellings', H: 'Transit hubs', V: 'Height', N: 'Street segments', L: 'Segment length' }[f.id], family: f.id, values: V.ab[meth].scaled[f.id], raw: V.ab[meth].raw[f.id],
        unit: meth === 'A' ? f.unitA : f.unitB, desc: meth === 'A' || f.defB === 'same as A' ? f.defA : f.defB.startsWith(f.id + ' ') ? `${f.defB}, where ${f.id} = ${f.defA}` : f.defB,
        high: 'scaled 0–1 over the 173 units: 0 is the lowest unit, 1 the highest', level: 'pooled min–max', off: !!cfg.off[f.id],
      }));
    }
    const out = [];
    for (const b of V.h.scalings[cfg.scaling].blocks) {
      if (b.block === 'composition') continue;
      b.columns.forEach((c, k) => {
        const col = COLS[c];
        out.push({ id: c, code: b.family + (b.columns.length > 1 ? String.fromCharCode(97 + k) : ''), label: col.label, family: b.family,
          values: b.X.map((r) => r[k]), raw: col.raw, unit: col.unit, desc: col.desc, high: col.high,
          level: V.h.scalings[cfg.scaling].levels[c], off: !!cfg.off[b.family] || colW(cfg, c) === 0 });
      });
    }
    return out;
  }
  function loadingCols(m, cfg) {
    if (m !== 'H') return AB_F.map((f) => ({ name: `${f} ${V.ab.factors.find((x) => x.id === f).name}`, values: V.ab[m].scaled[f] }));
    const out = [];
    for (const b of V.h.scalings[cfg.scaling].blocks) b.columns.forEach((c, k) => out.push({ name: `${b.family} ${COLS[c].label}`, values: b.X.map((r) => r[k]) }));
    return out;
  }

  /* ---------------------------------------------------------------- colour */
  let T = {};
  function readTokens() {
    const cs = getComputedStyle(document.documentElement), g = (v) => cs.getPropertyValue(v).trim();
    T = { ink: g('--ink'), ink2: g('--ink-2'), muted: g('--muted'), rule: g('--rule'), ruleStrong: g('--rule-strong'), surface: g('--surface'),
      paper: g('--paper'), sans: g('--font-sans'), mono: g('--font-mono'), acc: g('--acc-' + ({ A: 'a', B: 'b', H: 'h' }[TAB_METHOD[state.tab]] || 'h')),
      cat: [1, 2, 3, 4, 5, 6, 7, 8].map((k) => g('--c' + k)), seq: [0, 1, 2, 3, 4, 5, 6].map((k) => g('--seq-' + k)),
      div: [g('--div-neg'), g('--div-mid'), g('--div-pos')] };
    T.city = { CHI: T.cat[0], SP: T.cat[1] };
  }
  const hex = (h) => [1, 3, 5].map((k) => parseInt(h.slice(k, k + 2), 16));
  function ramp(stops, t) {
    if (t !== t || t === null) return T.rule;
    t = Math.max(0, Math.min(1, t));
    const x = t * (stops.length - 1), k = Math.min(stops.length - 2, Math.floor(x)), f = x - k, a = hex(stops[k]), b = hex(stops[k + 1]);
    return `rgb(${a.map((v, j) => Math.round(v + f * (b[j] - v))).join(',')})`;
  }
  const seqScale = () => T.seq.map((c, k) => [k / (T.seq.length - 1), c]);
  const seqScaleRev = () => T.seq.slice().reverse().map((c, k) => [k / (T.seq.length - 1), c]);
  const divScale = () => [[0, T.div[0]], [0.5, T.div[1]], [1, T.div[2]]];
  const quantile = (arr, q) => { const s = arr.filter((v) => v === v).sort((a, b) => a - b); return s[Math.min(s.length - 1, Math.floor(q * (s.length - 1)))]; };

  /* ---------------------------------------------------------------- Plotly helpers */
  const PCONF = { displaylogo: false, responsive: false, modeBarButtonsToRemove: ['select2d', 'lasso2d', 'autoScale2d', 'toggleSpikelines', 'hoverCompareCartesian'] };
  function layout(extra) {
    const ax = { gridcolor: T.rule, zerolinecolor: T.ruleStrong, linecolor: T.ruleStrong, tickfont: { size: 11, color: T.ink2 }, title: { font: { size: 12, color: T.ink2 } } };
    const base = { paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', font: { family: T.sans, size: 12, color: T.ink2 },
      margin: { l: 48, r: 12, t: 12, b: 40 }, hoverlabel: { bgcolor: T.surface, bordercolor: T.ruleStrong, font: { color: T.ink, family: T.sans } },
      xaxis: { ...ax }, yaxis: { ...ax }, showlegend: false, legend: { font: { size: 11, color: T.ink2 }, orientation: 'h', y: -0.18 } };
    for (const [k, v] of Object.entries(extra || {})) base[k] = v && typeof v === 'object' && !Array.isArray(v) && base[k] ? { ...base[k], ...v } : v;
    return base;
  }
  function plot(el, data, lay, onClick) {
    if (!el) return;
    // Explicit size from the container on every render: Plotly's own `responsive` mode resized figures in hidden tabs
    // to the wrong size and later renders kept it (collapsed PCA, matrix spilling out of its panel).
    lay.autosize = false;
    lay.width = el.clientWidth || el.parentElement.clientWidth;
    Plotly.react(el, data, lay, PCONF);
    el._click = onClick;
    if (!el._bound) {
      el._bound = true;
      el.on('plotly_click', (ev) => { const p = ev.points && ev.points[0]; if (p && el._click) el._click(p); });
    }
  }

  /* ---------------------------------------------------------------- tooltip */
  const tip = $('#tip');
  function showTip(html, ev) {
    tip.innerHTML = html; tip.hidden = false;
    const w = tip.offsetWidth, h = tip.offsetHeight;
    tip.style.left = Math.min(window.innerWidth - w - 8, ev.clientX + 14) + 'px';
    tip.style.top = Math.min(window.innerHeight - h - 8, ev.clientY + 14) + 'px';
  }
  const hideTip = () => { tip.hidden = true; };

  /* ---------------------------------------------------------------- SVG maps (projected polygons, decametres) */
  function makeMap(el, city) {
    const ids = POOL[city];
    let W = 0, H = 0;
    ids.forEach((i) => V.polygons[i].forEach((r) => { for (let k = 0; k < r.length; k += 2) { W = Math.max(W, r[k]); H = Math.max(H, r[k + 1]); } }));
    const pad = 40, path = {}, centre = {};
    ids.forEach((i) => {
      let best = 0;
      path[i] = V.polygons[i].map((r) => {
        let a = 0, cx = 0, cy = 0;
        const pts = [];
        for (let k = 0; k < r.length; k += 2) {
          const x = r[k], y = H - r[k + 1];
          pts.push(x + ',' + y);
          if (k + 2 < r.length) { const x2 = r[k + 2], y2 = H - r[k + 3], c = x * y2 - x2 * y; a += c; cx += (x + x2) * c; cy += (y + y2) * c; }
        }
        if (Math.abs(a) > best) { best = Math.abs(a); centre[i] = [cx / (3 * a), cy / (3 * a)]; }
        return 'M' + pts.join('L') + 'Z';
      }).join('');
    });
    el.innerHTML = `<svg viewBox="${-pad} ${-pad} ${W + 2 * pad} ${H + 2 * pad}" role="img" aria-label="Map of ${CITY[city]} units">
      <g class="units">${ids.map((i) => `<path class="u" data-i="${i}" fill-rule="evenodd" d="${path[i]}"></path>`).join('')}</g><g class="rings"></g><g class="labels"></g></svg>
      <div class="mapctl"><button type="button" data-z="in" aria-label="Zoom in">+</button><button type="button" data-z="out" aria-label="Zoom out">−</button><button type="button" data-z="reset" aria-label="Reset zoom">⟲</button></div>
      <div class="note" style="margin-top:4px"><b class="ink2">${CITY[city]}</b> · ${ids.length} ${city === 'SP' ? 'districts' : 'Community Areas'} <span class="muted">· Ctrl/⌘ + scroll or +/− to zoom, drag to pan</span></div>`;
    const svg = $('svg', el), units = Object.fromEntries($$('path.u', el).map((p) => [p.dataset.i, p]));
    const map = { el, city, tipFor: null, onClick: null };
    const fs = (W + H) / 70;                    // label size in map units (~13px at typical widths)

    /* Zoom and pan by moving the viewBox inside the full extent; labels keep their screen size. */
    const full = { x: -pad, y: -pad, w: W + 2 * pad, h: H + 2 * pad };
    let vb = { ...full }, drag = null, dragged = false;
    const setVB = () => {
      vb.w = Math.min(full.w, vb.w); vb.h = Math.min(full.h, vb.h);
      vb.x = Math.max(full.x, Math.min(full.x + full.w - vb.w, vb.x));
      vb.y = Math.max(full.y, Math.min(full.y + full.h - vb.h, vb.y));
      svg.setAttribute('viewBox', `${vb.x} ${vb.y} ${vb.w} ${vb.h}`);
      const k = vb.w / full.w;
      $$('text', svg).forEach((t) => { t.setAttribute('font-size', fs * k); t.setAttribute('stroke-width', fs * k / 4); t.setAttribute('y', t.dataset.cy - fs * k * 0.9); });
      svg.classList.toggle('zoomed', k < 0.999);
    };
    const toMap = (ev) => { const m = svg.getScreenCTM(); return [(ev.clientX - m.e) / m.a, (ev.clientY - m.f) / m.d]; };
    const zoom = (f, cx = vb.x + vb.w / 2, cy = vb.y + vb.h / 2) => {
      const r = Math.max(1 / 25, Math.min(1, vb.w * f / full.w)) * full.w / vb.w;      // at most 25x
      vb = { x: cx - (cx - vb.x) * r, y: cy - (cy - vb.y) * r, w: vb.w * r, h: vb.h * r };
      setVB();
    };
    $('.mapctl', el).addEventListener('click', (ev) => {
      const z = ev.target.closest('[data-z]'); if (!z) return;
      if (z.dataset.z === 'reset') { vb = { ...full }; setVB(); } else zoom(z.dataset.z === 'in' ? 0.6 : 1 / 0.6);
    });
    svg.addEventListener('wheel', (ev) => {
      if (!(ev.ctrlKey || ev.metaKey)) return;                // plain scrolling keeps scrolling the page
      ev.preventDefault();
      const [x, y] = toMap(ev);
      zoom(ev.deltaY < 0 ? 0.8 : 1.25, x, y);
    }, { passive: false });
    svg.addEventListener('pointerdown', (ev) => { if (ev.button === 0) { drag = { x: ev.clientX, y: ev.clientY, vb: { ...vb }, id: ev.pointerId }; dragged = false; } });
    svg.addEventListener('pointermove', (ev) => {
      if (!drag || vb.w >= full.w) return;
      const dx = ev.clientX - drag.x, dy = ev.clientY - drag.y;
      if (!dragged && Math.hypot(dx, dy) < 4) return;
      if (!dragged) { dragged = true; svg.setPointerCapture(drag.id); svg.classList.add('panning'); hideTip(); }
      const a = svg.getScreenCTM().a;
      vb = { ...drag.vb, x: drag.vb.x - dx / a, y: drag.vb.y - dy / a };
      setVB();
    });
    const endDrag = () => { drag = null; svg.classList.remove('panning'); };
    svg.addEventListener('pointerup', endDrag);
    svg.addEventListener('pointercancel', endDrag);

    svg.addEventListener('mousemove', (ev) => { if (dragged && drag) return; const i = ev.target.dataset && ev.target.dataset.i; if (i !== undefined && map.tipFor) showTip(map.tipFor(+i), ev); else hideTip(); });
    svg.addEventListener('mouseleave', hideTip);
    svg.addEventListener('click', (ev) => { if (dragged) { dragged = false; return; } const i = ev.target.dataset && ev.target.dataset.i; if (i !== undefined && map.onClick) map.onClick(+i, ev); });
    map.update = ({ fill, rings = [], labels = [], tipFor, onClick }) => {
      map.tipFor = tipFor; map.onClick = onClick;
      ids.forEach((i) => units[i].setAttribute('fill', fill(i)));
      const mine = rings.filter((r) => U[r.i].city === city);   // each ring gets a surface halo so it reads on dark fills
      $('.rings', svg).innerHTML = mine.map((r) => `<path class="ring" d="${path[r.i]}" stroke="${T.surface}" stroke-width="${(r.width || 2) + 2}"></path>`).join('')
        + mine.map((r) => `<path class="ring" d="${path[r.i]}" stroke="${r.color}" stroke-width="${r.width || 2}"></path>`).join('');
      $('.labels', svg).innerHTML = labels.filter((l) => U[l.i].city === city)
        .map((l) => { const [x, y] = centre[l.i]; return `<text x="${x}" data-cy="${y}" text-anchor="middle">${esc(l.text)}</text>`; }).join('');
      setVB();
    };
    return map;
  }

  /* ---------------------------------------------------------------- reference and comparison */
  function setRef(i) {
    if (i === undefined || i === null || i === state.ref) return;
    state.ref = i;
    state.compare = state.compare.filter((j) => j !== i);
    syncRefInputs();
    schedule();
  }
  function toggleCompare(i) {
    if (i === state.ref) return;
    const k = state.compare.indexOf(i);
    if (k >= 0) state.compare.splice(k, 1);
    else { state.compare.push(i); if (state.compare.length > 3) state.compare.shift(); }
    schedule();
  }
  const compareColor = (k) => T.cat[k];
  function unitFromText(v) {
    const t = v.trim().toLowerCase();
    if (!t) return null;
    let i = U.findIndex((u, j) => label(j).toLowerCase() === t || u.id.toLowerCase() === t);
    if (i < 0) i = U.findIndex((u) => u.name.toLowerCase() === t);
    if (i < 0) i = U.findIndex((u) => u.name.toLowerCase().startsWith(t));
    return i < 0 ? null : i;
  }
  function bindRefInput(input) {
    const go = () => { const i = unitFromText(input.value); if (i !== null) setRef(i); else input.value = label(state.ref); };
    input.addEventListener('change', go);
    input.addEventListener('keydown', (e) => { if (e.key === 'Enter') go(); });
    input.addEventListener('focus', () => input.select());
  }
  function syncRefInputs() { $$('input[data-ref]').forEach((inp) => { if (document.activeElement !== inp) inp.value = label(state.ref); }); }

  /* ---------------------------------------------------------------- routing and theme */
  const typeset = new Set();
  function typesetView(tab) {            // MathJax loads deferred; it calls window.onMathJaxReady once it can typeset
    if (typeset.has(tab) || !(window.MathJax && MathJax.typesetPromise)) return;
    typeset.add(tab);
    MathJax.typesetPromise([$(`[data-view="${tab}"]`)]).catch(() => typeset.delete(tab));
  }
  window.onMathJaxReady = () => typesetView(state.tab);
  function show(tab) {
    state.tab = tab;
    $$('section.view').forEach((s) => { s.hidden = s.dataset.view !== tab; });
    $$('.tab').forEach((b) => b.setAttribute('aria-current', b.dataset.tab === tab ? 'page' : 'false'));
    typesetView(tab);
    render();
  }
  function route() {
    const h = decodeURIComponent(location.hash.slice(1));
    if (!h || TABS.includes(h)) { show(h || 'overview'); window.scrollTo(0, 0); return; }
    const el = document.getElementById(h), v = el && el.closest('[data-view]');
    if (v) { if (state.tab !== v.dataset.view) show(v.dataset.view); requestAnimationFrame(() => el.scrollIntoView()); }
  }
  function toggleTheme() {
    const root = document.documentElement, dark = root.dataset.theme ? root.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    root.dataset.theme = dark ? 'light' : 'dark';
    schedule();
  }

  let pending = false;
  function schedule() { if (pending) return; pending = true; requestAnimationFrame(() => { pending = false; render(); }); }
  function render() {
    readTokens();
    if (state.tab === 'overview') renderOverview();
    const m = TAB_METHOD[state.tab];
    if (m) renderExplorer(m);
  }

  /* ---------------------------------------------------------------- shared ranking helpers */
  const closest = (R, city, k) => M.order(R.D, N, state.ref, POOL[city]).slice(0, k);
  function rankAll(R) { const o = M.order(R.D, N, state.ref), r = new Int32Array(N); o.forEach((j, k) => { r[j] = k + 1; }); return r; }

  /* ---------------------------------------------------------------- overview */
  let ovMaps = null;
  function renderOverview() {
    if (!ovMaps) ovMaps = { SP: makeMap($('#ov-map-SP'), 'SP'), CHI: makeMap($('#ov-map-CHI'), 'CHI') };
    const R = current('H'), ref = state.ref;
    const others = R.error ? [] : Array.from({ length: N }, (_, j) => R.D[ref * N + j]).filter((_, j) => j !== ref);
    const lo = Math.min(...others), hi = quantile(others, 0.95);
    for (const map of Object.values(ovMaps)) {
      map.update({
        fill: (i) => (i === ref ? T.surface : R.error ? T.rule : ramp(T.seq, 1 - (R.D[ref * N + i] - lo) / (hi - lo))),
        rings: [{ i: ref, color: T.ink, width: 2.5 }], labels: [{ i: ref, text: '★ ' + U[ref].name }],
        tipFor: (i) => `<b>${esc(U[i].name)}</b> ${cityTag(i)}<br>${i === ref ? 'Reference' : R.error ? '' : 'Harmonized distance ' + fmt(R.D[ref * N + i])}<br><span class="muted">Click to make it the reference</span>`,
        onClick: (i) => setRef(i),
      });
    }
    const oc = OTHER[U[ref].city];
    $('#ov-answer-title').textContent = `Closest to ${U[ref].name} in ${CITY[oc]}`;
    const rows = ['H', 'B', 'A'].map((m) => {
      const r = current(m);
      if (r.error) return `<tr><td>${METHODS[m].short}</td><td colspan="3" class="muted">${esc(r.error)}</td></tr>`;
      const top = closest(r, oc, 3);
      return `<tr><td><button class="btn small" data-go="${METHODS[m].tab}">${METHODS[m].short}</button></td>${top.map((j) => `<td>${esc(U[j].name)} <span class="muted num">${fmt(r.D[ref * N + j])}</span></td>`).join('')}</tr>`;
    }).join('');
    $('#ov-answer').innerHTML = `<div class="tablewrap"><table class="tbl"><thead><tr><th>Method</th><th>1st</th><th>2nd</th><th>3rd</th></tr></thead><tbody>${rows}</tbody></table></div>
      <p class="note" style="margin-top:8px">Numbers are each method's dissimilarity (smaller = more alike); they are not comparable across methods. Index A and B use the index-gap rule unless you switch them to the factor profile.</p>`;
  }

  function fillStatic() {
    const S = V.summary, nAll = N;
    const bind = { 'n-sp': S.SP.units, 'n-chi': S.CHI.units, 'n-all': nAll, 'n-cols': V.h.columns.length, 'n-fams': H_F.length,
      'r3-hybrid': V.h.r3_dropped_columns.hybrid.map((c) => `${COLS[c].family} (${COLS[c].label.toLowerCase()})`).join(', ') };
    $$('[data-bind]').forEach((el) => { el.textContent = bind[el.dataset.bind]; });
    $('#unit-list').innerHTML = U.map((u, i) => `<option value="${esc(label(i))}"></option>`).join('');
    const n = (x) => nf(0).format(x);
    $('#hero-facts').innerHTML = [
      [S.SP.units, 'São Paulo districts'], [S.CHI.units, 'Chicago Community Areas'], [nf(0).format(nAll * (nAll - 1) / 2), 'pairs compared'],
      [n(S.SP.land_km2) + ' km²', 'São Paulo land'], [n(S.CHI.land_km2) + ' km²', 'Chicago land'], [`${V.h.columns.length} · ${H_F.length}`, 'model columns · families'],
    ].map(([b, s]) => `<div><b>${b}</b><span>${s}</span></div>`).join('');
    const rows = [['Units', 'units'], ['Land area (km²)', 'land_km2'], ['Median unit land (km²)', 'land_median_km2'], ['Commercial places (Overture, five categories)', 'commercial_places'],
      ['Dwellings (CNEFE 2022 · Census 2020)', 'dwellings'], ['Metro / \'L\' stations', 'stations'], ['Bus stops (GTFS)', 'bus_stops'],
      ['Buildings with a height (Overture)', 'buildings_with_height'], ['Road segments (ten classes)', 'road_segments']];
    $('#ov-data').innerHTML = `<table class="tbl"><thead><tr><th>Item</th><th class="r">São Paulo</th><th class="r">Chicago</th></tr></thead><tbody>${rows.map(([t, k]) =>
      `<tr><td>${t}</td><td class="r">${nf(k.includes('median') ? 2 : k === 'land_km2' ? 1 : 0).format(S.SP[k])}</td><td class="r">${nf(k.includes('median') ? 2 : k === 'land_km2' ? 1 : 0).format(S.CHI[k])}</td></tr>`).join('')}</tbody></table>`;
    const famTable = `<table class="tbl"><thead><tr><th>Family</th><th>What it measures</th><th>Chicago source</th><th>São Paulo source</th><th>Same instrument</th><th>Hybrid C6</th></tr></thead><tbody>${V.h.families.map((f) =>
      `<tr><td><b class="mono">${f.id}</b> ${esc(f.name)}<div class="muted">${f.domain}</div></td><td>${esc(f.desc)}</td><td>${esc(f.chicago)}</td><td>${esc(f.sao_paulo)}</td><td>${f.same_instrument ? 'yes' : '<b>no</b>'}</td><td><span class="pill ${f.hybrid_level === 'absolute' ? 'abs' : 'rel'}">${f.hybrid_level}</span></td></tr>`).join('')}</tbody></table>`;
    $('#ov-sources').innerHTML = famTable;
    fillDocs(famTable);
  }

  /* ---------------------------------------------------------------- documentation tables (from the published results) */
  function table(head, rows, right = []) {
    return `<table class="tbl"><thead><tr>${head.map((h, k) => `<th class="${right.includes(k) ? 'r' : ''}">${h}</th>`).join('')}</tr></thead><tbody>${rows.map((r) =>
      `<tr class="${r.hl ? 'hl' : ''}">${r.map((c, k) => `<td class="${right.includes(k) ? 'r' : ''}">${c}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  }
  function fillDocs(famTable) {
    const t = V.ab.tests, fill = (k, html) => { const el = $(`[data-fill="${k}"]`); if (el) el.innerHTML = html; };
    const S = V.summary;
    const totals = { C: 'commercial_places', R: 'dwellings', H: null, N: 'road_segments', V: 'buildings_with_height' };
    fill('ab-factors-A', table(['Code', 'Factor', 'Group', 'Definition (Index A)', 'São Paulo', 'Chicago'], V.ab.factors.map((f) => [
      `<b class="mono">${f.id}</b>`, f.name, f.group, esc(f.defA),
      f.id === 'H' ? `${nf(0).format(S.SP.stations)} + ${nf(0).format(S.SP.bus_stops)}` : totals[f.id] ? nf(0).format(S.SP[totals[f.id]]) : '—',
      f.id === 'H' ? `${nf(0).format(S.CHI.stations)} + ${nf(0).format(S.CHI.bus_stops)}` : totals[f.id] ? nf(0).format(S.CHI[totals[f.id]]) : '—']), [4, 5]));
    const t1 = (m) => t.t1.filter((r) => r.method === m);
    fill('ab-t1', table(['Factor', 'A: within parts', 'A: merged ÷ largest part (median)', 'B: within parts', 'Verdict A', 'Verdict B'], t1('A').map((a) => {
      const b = t1('B').find((x) => x.factor === a.factor);
      const row = [a.factor === 'index' ? '<b>Index</b>' : a.factor, `${a.within_parts} of ${a.subprefeituras_tested}`, a.within_parts < a.subprefeituras_tested ? fmt(a.merged_over_max_part_median, 2) : '—',
        `${b.within_parts} of ${b.subprefeituras_tested}`, a.verdict, b.verdict];
      row.hl = a.factor === 'index';
      return row;
    }), [1, 2, 3]));
    const t2 = t.t2.filter((r) => r.factor === 'index');
    const ci = (r) => `${r.spearman > 0 ? '+' : ''}${fmt(r.spearman)} [${fmt(r.ci_low)}, ${fmt(r.ci_high)}]`;
    fill('ab-t2', table(['Index', 'Pooled (173)', 'São Paulo (96)', 'Chicago (77)'], ['A', 'B'].map((m) => {
      const g = (s) => t2.find((r) => r.method === m && r.scope === s);
      return [m, ci(g('pooled')) + `<div class="muted">${g('pooled').verdict}</div>`, ci(g('SP')) + `<div class="muted">${g('SP').verdict}</div>`, ci(g('Chicago')) + `<div class="muted">${g('Chicago').verdict}</div>`];
    })));
    const t3 = t.t3[0];
    fill('ab-t3', table(['T3 measure', 'Value'], [['Spearman, A vs B (pooled / São Paulo / Chicago)', `${fmt(t3.spearman_pooled)} / ${fmt(t3.spearman_SP)} / ${fmt(t3.spearman_Chicago)}`],
      ['Shared top 10', t3.top10_overlap], ["Brás's rank, A → B", `${t3.bras_rank_A} → ${t3.bras_rank_B}`],
      ['Largest rank shift', `${esc(U[IDX[t3.unit_with_max_shift]].name)}: ${t3.max_rank_shift} places`], ['Verdict', `<b>${t3.verdict}</b>`]]));
    fill('ab-t4', table(['T4 group', 'Chicago units, A', 'Chicago units, B', 'Expected at Chicago\'s share'], ['top20', 'bottom20'].map((g) => {
      const r = (m) => t.t4.find((x) => x.method === m && x.group === g);
      return [g === 'top20' ? 'Top 20' : 'Bottom 20', r('A').chicago, r('B').chicago, fmt(r('A').expected_chicago_at_unit_share, 1)];
    }), [1, 2, 3]));
    fill('ab-s1', table(['S1 method', 'Spearman with primary', 'Top-10 kept', "Brás's rank"], t.s1.map((r) => [r.method, fmt(r.spearman_with_primary), r.top10_overlap, `${r.bras_rank_primary} → ${r.bras_rank_merged}`]), [1, 2]));
    fill('ab-summary-A', table(['Test', 'Index A result'], [
      ['T1 boundary invariance', `${t1('A').filter((r) => r.verdict !== 'boundary-invariant').map((r) => r.factor).join(', ')} <b>depend on boundaries</b> (index: ${t1('A').find((r) => r.factor === 'index').within_parts} of 29 merged units within their parts)`],
      ['T2 size dependence', `index vs land area ${ci(t2.find((r) => r.method === 'A' && r.scope === 'pooled'))}: <b>size-dependent</b>`],
      ['T3 agreement with B', `Spearman ${fmt(t3.spearman_pooled)}, shared top 10: ${t3.top10_overlap}: <b>${t3.verdict}</b>`],
      ['T4 Chicago units in top / bottom 20', `${t.t4.find((x) => x.method === 'A' && x.group === 'top20').chicago} / ${t.t4.find((x) => x.method === 'A' && x.group === 'bottom20').chicago} (8.9 expected)`]]));
    const bras = IDX['SP:10'], chi = POOL.CHI;
    fill('ab-bras', table(['Method', 'Rank', 'Chicago area', 'Index', 'Gap to Brás', 'Profile rank'], ['A', 'B'].flatMap((m) => {
      const r = M.indexModel(V.ab[m].scaled, AB_F, ones(AB_F), N), byGap = M.order(r.gap, N, bras, chi), byProf = M.order(r.profile, N, bras, chi);
      return byGap.slice(0, 3).map((j, k) => [k ? '' : `Index ${m} (Brás ${fmt(r.index[bras])})`, k + 1, esc(U[j].name), fmt(r.index[j]), fmt(r.gap[bras * N + j]), byProf.indexOf(j) + 1]);
    }), [1, 3, 4, 5]));
    fill('h-families', famTable);
    fill('h-columns', table(['Column', 'Family', 'Unit', 'Transform', 'Hybrid level', 'A high value means'], V.h.columns.map((c) => [
      `<code>${c.id}</code>`, c.family, esc(c.unit), c.transform, `<span class="pill ${V.h.scalings.hybrid.levels[c.id] === 'absolute' ? 'abs' : 'rel'}">${V.h.scalings.hybrid.levels[c.id]}</span>`, esc(c.high)])));
    fill('h-shares', table(['Family', 'Mean share of D² (all pairs)', 'Median share', 'Pairs where it is over half of D²'], V.h.published.family_shares.map((r) => {
      const row = [`${r.family} ${FAM[r.family].name}`, pct(r.mean_share, 1), pct(r.median_share, 1), nf(0).format(r.pairs_over_half)];
      row.hl = r.mean_share > 0.15;
      return row;
    }), [1, 2, 3]));
    fill('h-pca', table(['Component', 'Variance explained', 'Cumulative'], V.h.published.pca_variance.map((r) => [r.pc, pct(r.explained, 1), pct(r.cumulative, 1)]), [1, 2]));
    fill('h-stability', table(['Rank', 'Chicago area', 'Share of draws in the top 5', 'Stable (≥ 80%)'], V.h.published.stability_bras.map((r) => [r.rank, esc(r.name), pct(r.share_of_draws, 1), r.stable ? 'yes' : '<b>no</b>']), [0, 2]));
    fill('h-scale', table(['Scaling', 'Run', 'Spearman, all pairs', 'Shared top 5', "Brás's Chicago distances (Spearman)", "Brás's Chicago top 10 kept", 'Other-city share of nearest 5'],
      V.h.published.scale_comparison.map((r) => [r.scaling.replace('_', '-'), r.run, fmt(r.spearman_pairs), fmt(r.mean_topk_overlap), fmt(r.bras_chicago_spearman), r.bras_chicago_top10_kept, fmt(r.mean_other_city_neighbours)]), [2, 3, 4, 5, 6]));
    fill('h-sens', table(['Scenario', 'Spearman, all pairs', 'Shared top 5', "Brás's Chicago top 5 kept"], V.h.published.sensitivities.map((r) => [esc(r.scenario), fmt(r.spearman_pairs), fmt(r.mean_topk_overlap), r.bras_top5_chicago_kept]), [1, 2, 3]));
    const bi = IDX['SP:10'], loop = IDX['CHI:32'], u3 = COLS.u3_acs_land_km2.raw;
    const med = (city) => { const v = POOL[city].map((i) => u3[i]).sort((a, b) => a - b); return (v[(v.length - 1) >> 1] + v[v.length >> 1]) / 2; };
    const pos = (i) => 1 + POOL[U[i].city].filter((j) => u3[j] > u3[i]).length;
    $('#h-c6-example').innerHTML = `An example from the data: Brás has ${nf(0).format(u3[bi])} residents per km² of land, ${pos(bi)}th of ${POOL.SP.length} in São Paulo (city median ${nf(0).format(med('SP'))}); the Loop has ${nf(0).format(u3[loop])}, ${pos(loop)}th of ${POOL.CHI.length} in Chicago (median ${nf(0).format(med('CHI'))}). Compared on absolute levels they are alike; compared by position within their city, Brás is ordinary and the Loop is dense. Absolute comparison is right when a number means the same thing in both cities; relative comparison is the safe choice when the measuring instrument differs.`;
  }

  /* ---------------------------------------------------------------- explorer skeleton and control rail */
  function explorerHTML(m) {
    const meth = METHODS[m], isH = m === 'H';
    const featRows = (ids) => ids.map((f) => {
      const meta = isH ? FAM[f] : V.ab.factors.find((x) => x.id === f);
      const tipText = isH ? `${meta.desc} Chicago: ${meta.chicago}. São Paulo: ${meta.sao_paulo}.` : `A: ${meta.defA}. B: ${meta.defB}.`;
      return `<div class="frow" data-f="${f}"><input type="checkbox" id="on-${m}-${f}" aria-label="Use ${esc(meta.name)}" checked>
        <label class="fname" for="on-${m}-${f}" title="${esc(tipText)}"><b>${f}</b>${esc(meta.name)}</label><span class="share num"></span>
        <input type="range" id="w-${m}-${f}" min="0" max="3" step="0.1" value="1" aria-label="Weight of ${esc(meta.name)}">${isH && MIX[f] ? `
        <details class="mix"${f === 'U1' ? ' open' : ''}><summary>Inside ${f}: ${MIX[f].length} columns</summary>${MIX[f].map((c) => `
          <div class="mrow" data-c="${c}"><label for="cw-${c}">${esc(COLS[c].label)}</label><span class="share num"></span>
          <input type="range" id="cw-${c}" min="0" max="3" step="0.1" value="1" aria-label="Weight of ${esc(COLS[c].label)} inside ${f}"></div>`).join('')}
        </details>` : ''}</div>`;
    }).join('');
    const feats = isH
      ? ['Street morphology', 'Built form', 'Use and activity'].map((d) => `<div class="domain">${d}</div>${featRows(H_F.filter((f) => FAM[f].domain === d))}`).join('')
      : `<div class="domain">Built environment</div>${featRows(['C', 'R', 'H', 'V'])}<div class="domain">Network</div>${featRows(['N', 'L'])}`;
    const settings = isH ? `
        <div class="ctl"><span class="lbl help" title="How São Paulo and Chicago values are put on one scale. Every column is standardized, z = (value − mean) / SD, capped at ±3; the scaling decides whose mean and SD are used. Hover an option for its rule.">Cross-city scaling (C6)</span><div class="seg" data-set="scaling"><button data-v="hybrid" title="Published primary. Families measured with the same instrument in both cities (M1, M3, M4, M6, M7, B1, U3) are compared on absolute levels: mean and SD over all 173 units. Families whose instruments differ (BV, U2, U4, U6, U1) are compared by position within their own city: mean and SD per city.">Hybrid</button><button data-v="all_absolute" title="Every column standardized over all 173 units: values compared as measured. Keeps city-wide differences, including those caused by different instruments, so the nearest neighbours mix the two cities less (about 7% from the other city).">All absolute</button><button data-v="all_relative" title="Every column standardized within its own city: a unit is compared by its position in its city. Removes city-wide shifts and stretches, so the nearest neighbours mix the two cities more (about 24% from the other city). It does not fix an instrument that mis-ranks units inside a city.">All relative</button></div></div>
        <div class="ctl"><span class="lbl help" title="How the dissimilarity between two units is measured. Hover an option for its rule.">Distance</span><div class="seg" data-set="geometry"><button data-v="full" title="Run R1: D = √( Σ family budget × calibrated block dissimilarity ), each block divided by its median pair so families count alike. Uses every direction of variation. Published primary.">Full model</button><button data-v="pca" title="Run R2: Euclidean distance on the principal components that together explain at least 90% of the variance (five components in the published fit). Drops the minor directions, about 10% of the variance; PCA and clusters then follow this geometry.">PCA (≥ 90%)</button></div></div>
        <div class="ctl"><span class="lbl">Published runs</span><div class="seg" data-preset><button data-v="R1" title="Equal weights, full distance">R1</button><button data-v="R2" title="Equal weights, distance on the components reaching 90% of variance">R2</button><button data-v="R3" title="Without correlated features (|ρ| ≥ 0.70 pruned)">R3</button></div><span class="note" data-preset-note></span></div>`
      : `
        <div class="ctl"><span class="lbl">Similarity rule</span><div class="seg" data-set="rule"><button data-v="gap">Index gap</button><button data-v="profile">Factor profile</button></div>
        <span class="note">Index gap is the agreed rule; factor profile is the protocol's diagnostic. PCA and clusters always use the factor profile.</span></div>`;
    return `<div class="explore">
      <aside class="rail" aria-label="${meth.short} settings">
        <details open><summary>Reference</summary><div class="body">
          <input type="search" list="unit-list" data-ref id="ref-${m}" autocomplete="off" aria-label="Reference unit">
          <span class="note">Shared by all methods. Click units in any view to compare them.</span></div></details>
        <details open><summary>Model settings</summary><div class="body">${settings}
          <div class="ctl"><label for="k-${m}">Clusters</label><select id="k-${m}"><option value="0">Best silhouette (k = 3–8)</option>${[2, 3, 4, 5, 6, 7, 8].map((k) => `<option value="${k}">k = ${k}</option>`).join('')}</select></div></div></details>
        <details open><summary>Features and weights</summary><div class="body">
          <span class="note">${isH ? 'Family budgets; shares are renormalized over active families.' : 'Factor weights in the index sum.'} Hover a name for its definition.</span>
          <div>${feats}</div>
          <div class="btnrow"><button class="btn small" data-act="equal">Equal weights</button><button class="btn small" data-act="allon">All on</button></div></div></details>
        <details open><summary>Baseline</summary><div class="body"><div class="basebox" data-basebox></div>
          <div class="btnrow"><button class="btn small" data-act="pin">Pin current settings</button><button class="btn small" data-act="unpin">Use published</button></div></div></details>
      </aside>
      <div class="xmain">
        <div class="xhead">
          <div class="eyebrow">Explore · ${meth.name}</div>
          <h1 data-title></h1>
          <p class="def">${esc(meth.def)} <button class="btn small" data-go="${meth.doc}">Read the method</button></p>
          <div class="refbar" data-refbar></div>
          <div class="tiles" data-tiles></div>
          <p class="note" data-cross></p>
          <nav class="subnav" aria-label="Sections">${[['rank', 'Closest units'], ['maps', 'Distance maps'], ['profile', 'Profile'], ['matrix', 'Distance matrix'], ['pca', 'Principal components'], ['clusters', 'Clusters']]
            .map(([k, t]) => `<button data-jump="${k}-${m}">${t}</button>`).join('')}</nav>
        </div>
        <div data-error></div>
        <section class="xsection" id="rank-${m}"><header><h2>Closest units in each city</h2>
          <label class="inline-ctl"><input type="checkbox" data-ui="breakdown" checked> Show what drives each match</label>
          <p data-rank-note></p></header>
          <div class="grid2">${['SP', 'CHI'].map((c) => `<div class="panel"><div class="plot" data-plot="rank-${c}"></div>
            <details class="tview"><summary>Table view</summary><div class="tablewrap" data-ranktable="${c}"></div></details></div>`).join('')}</div></section>
        <section class="xsection" id="maps-${m}"><header><h2>Distance maps</h2>
          <label class="inline-ctl">Colour by <select data-ui="mapBy"></select></label>
          <p>Both cities on one colour scale. ★ marks the reference; outlines mark its 10 closest units in each city and the units you compare.</p></header>
          <div class="panel"><div class="grid2"><div class="mapbox" data-map="SP"></div><div class="mapbox" data-map="CHI"></div></div><div class="legend" data-maplegend></div></div></section>
        <section class="xsection" id="profile-${m}"><header><h2>Standardized profile</h2><p data-profile-note></p></header>
          <div class="grid2"><div class="panel"><div class="plot" data-plot="radar"></div></div><div class="panel"><div class="panel-head"><h3>What each axis means</h3><span class="note">raw value and standardized value</span></div><div class="tablewrap scrollbox" data-featguide></div></div></div></section>
        <section class="xsection" id="matrix-${m}"><header><h2>Distance matrix</h2>
          <label class="inline-ctl">Show <select data-ui="heat"><option value="nbhd">Reference and its 10 closest per city</option><option value="all">All ${N} units, ordered by cluster</option></select></label>
          <p>Every pairwise dissimilarity among the units shown. Darker cells are more alike. Click a cell to compare its column unit.</p></header>
          <div class="panel"><div class="plot" data-plot="heat"></div></div></section>
        <section class="xsection" id="pca-${m}"><header><h2>Principal components</h2>
          <span class="inline-ctl">Axes <select data-ui="pcx" aria-label="Horizontal component"></select><select data-ui="pcy" aria-label="Vertical component"></select>
          Colour <select data-ui="pcColor"><option value="city">by city</option><option value="cluster">by cluster</option></select></span>
          <p data-pca-note></p></header>
          <div class="grid-3-2"><div class="panel"><div class="plot" data-plot="pca"></div></div>
            <div style="display:grid;gap:16px;min-width:0"><div class="panel"><div class="panel-head"><h3>Variance explained</h3></div><div class="plot" data-plot="scree"></div></div>
            <div class="panel"><div class="panel-head"><h3>Loadings</h3><span class="note">correlation of each column with each component</span></div><div class="plot" data-plot="load"></div></div></div></div></section>
        <section class="xsection" id="clusters-${m}"><header><h2>Clusters</h2><p data-cl-note></p></header>
          <div class="grid-3-2"><div class="panel"><div class="plot" data-plot="clscatter"></div></div>
            <div class="panel"><div class="panel-head"><h3>Silhouette by number of clusters</h3></div><div class="plot" data-plot="sil"></div></div></div>
          <div class="panel"><div class="grid2"><div class="mapbox" data-clmap="SP"></div><div class="mapbox" data-clmap="CHI"></div></div><div class="cats" data-cllegend></div></div>
          <div class="grid2"><div class="panel"><div class="panel-head"><h3>Clusters by city</h3></div><div class="tablewrap" data-cltable></div></div>
            <div class="panel"><div class="panel-head"><h3>Mean standardized value by cluster</h3></div><div class="plot" data-plot="clprof"></div></div></div>
          <div class="panel"><div class="panel-head"><h3 data-members-title></h3><span class="note">Click a name to compare it</span></div><div data-members></div></div></section>
      </div></div>`;
  }

  const X = {};   // per-method DOM handles
  function buildExplorer(m) {
    const root = $(`[data-view="${METHODS[m].tab}"]`);
    root.innerHTML = explorerHTML(m);
    const h = X[m] = { root, maps: { SP: makeMap($('[data-map="SP"]', root), 'SP'), CHI: makeMap($('[data-map="CHI"]', root), 'CHI') },
      clmaps: { SP: makeMap($('[data-clmap="SP"]', root), 'SP'), CHI: makeMap($('[data-clmap="CHI"]', root), 'CHI') },
      p: (k) => $(`[data-plot="${k}"]`, root) };
    bindRefInput($(`#ref-${m}`));
    if (matchMedia('(max-width: 980px)').matches) $$('.rail details', root).slice(1).forEach((d) => { d.open = false; });   // phones: settings folded
    const cfg = () => state.cfg[m];
    $$('.frow', root).forEach((row) => {
      const f = row.dataset.f, cb = $('input[type="checkbox"]', row), sl = $('input[type="range"]', row);
      cb.addEventListener('change', () => { if (cb.checked) delete cfg().off[f]; else cfg().off[f] = true; schedule(); });
      // A full recompute and redraw takes ~0.4 s, so while dragging only the shares update; views follow when the slider pauses.
      sl.addEventListener('input', () => { cfg().weights[f] = +sl.value; if (+sl.value > 0) delete cfg().off[f]; syncRail(m); clearTimeout(h.drag); h.drag = setTimeout(schedule, 180); });
      sl.addEventListener('change', () => { clearTimeout(h.drag); schedule(); });
    });
    $$('.mrow', root).forEach((row) => {            // column weights inside a family (same pause-then-recompute rule)
      const c = row.dataset.c, sl = $('input', row);
      sl.addEventListener('input', () => { cfg().cols = { ...cfg().cols, [c]: +sl.value }; syncRail(m); clearTimeout(h.drag); h.drag = setTimeout(schedule, 180); });
      sl.addEventListener('change', () => { clearTimeout(h.drag); schedule(); });
    });
    $$('[data-set]', root).forEach((seg) => seg.addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) { cfg()[seg.dataset.set] = b.dataset.v; schedule(); } }));
    const preset = $('[data-preset]', root);
    if (preset) preset.addEventListener('click', (e) => {
      const b = e.target.closest('button'); if (!b) return;
      state.cfg[m] = presetCfg(b.dataset.v, cfg());
      schedule();
    });
    $(`#k-${m}`).addEventListener('change', (e) => { cfg().k = +e.target.value; schedule(); });
    root.addEventListener('click', (e) => {
      const act = e.target.closest('[data-act]'), jump = e.target.closest('[data-jump]');
      if (jump) document.getElementById(jump.dataset.jump).scrollIntoView({ behavior: 'smooth' });
      if (!act) return;
      const c = cfg();
      if (act.dataset.act === 'equal') { c.weights = ones(METHODS[m].feats); c.cols = {}; }
      if (act.dataset.act === 'allon') c.off = {};
      if (act.dataset.act === 'pin') state.base[m] = clone(c);
      if (act.dataset.act === 'unpin') state.base[m] = null;
      schedule();
    });
    $$('[data-ui]', root).forEach((el) => el.addEventListener('change', () => {
      state.ui[m][el.dataset.ui] = el.type === 'checkbox' ? el.checked : (el.dataset.ui === 'pcx' || el.dataset.ui === 'pcy' ? +el.value : el.value);
      schedule();
    }));
    syncRefInputs();
  }

  function syncRail(m) {
    const root = X[m].root, c = state.cfg[m], w = weightsOf(c, m), tot = Object.values(w).reduce((a, b) => a + b, 0);
    $$('.frow', root).forEach((row) => {
      const f = row.dataset.f, on = !c.off[f], sl = $('input[type="range"]', row);
      $('input[type="checkbox"]', row).checked = on;
      if (document.activeElement !== sl) sl.value = c.weights[f];
      row.classList.toggle('off', !(w[f] > 0));
      $('.share', row).textContent = w[f] > 0 && tot > 0 ? pct(w[f] / tot) : 'off';
      if (MIX[f]) {
        const vs = MIX[f].reduce((a, col) => a + colW(c, col), 0);
        $$('.mrow', row).forEach((mr) => {
          const v = colW(c, mr.dataset.c), msl = $('input', mr);
          if (document.activeElement !== msl) msl.value = v;
          $('.share', mr).textContent = v > 0 && vs > 0 ? `${pct(v / vs)} of ${f}` : 'off';
          mr.classList.toggle('off', !(v > 0) || !(w[f] > 0));
        });
      }
    });
    $$('[data-set]', root).forEach((seg) => $$('button', seg).forEach((b) => b.setAttribute('aria-pressed', String(c[seg.dataset.set] === b.dataset.v))));
    const preset = $('[data-preset]', root);
    if (preset) {
      const which = ['R1', 'R2', 'R3'].find((r) => canon(m, presetCfg(r, c)) === canon(m, c)) || null;
      $$('button', preset).forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.v === which)));
      $('[data-preset-note]', root).textContent = which ? `Current: ${which} under ${c.scaling.replace('_', '-')} scaling`
        + (which === 'R3' ? ` (without ${V.h.r3_dropped_columns[c.scaling].map((col) => `${COLS[col].family} ${COLS[col].label.toLowerCase()}`).join(', ')})` : '') : 'Custom settings';
    }
    $(`#k-${m}`).value = String(c.k || 0);
    const b = baseCfg(m);
    const desc = m === 'H' ? `${b.scaling.replace('_', '-')} scaling, ${b.geometry === 'pca' ? 'PCA distance' : 'full distance'}` : `${b.rule === 'gap' ? 'index gap' : 'factor profile'} rule`;
    const changed = METHODS[m].feats.filter((f) => !!b.off[f] !== !!c.off[f] || +b.weights[f] !== +c.weights[f])
      .concat(Object.keys(MIX).filter((f) => m === 'H' && MIX[f].some((col) => colW(b, col) !== colW(c, col))).map((f) => `${f} inner mix`));
    $('[data-basebox]', root).innerHTML = `<b>${state.base[m] ? 'Pinned snapshot' : 'Published settings'}</b>: ${desc}${Object.keys(b.off).length ? `, without ${Object.keys(b.off).join(', ')}` : ''}${METHODS[m].feats.some((f) => +b.weights[f] !== 1) || Object.values(b.cols || {}).some((v) => +v !== 1) ? ', custom weights' : ', equal weights'}.<br>${sameAsBase(m) ? 'Current settings match it.' : `Changed from it: ${changed.length ? changed.join(', ') : 'model settings'}.`}`;
  }

  /* ---------------------------------------------------------------- explorer rendering */
  function renderExplorer(m) {
    if (!X[m]) buildExplorer(m);
    const h = X[m], root = h.root, ref = state.ref;
    const R = current(m), Rb = baseline(m);
    syncRail(m);
    $('[data-title]', root).textContent = `${U[ref].name}, ${CITY[U[ref].city]}`;
    renderRefbar(m);
    const err = $('[data-error]', root);
    err.innerHTML = R.error ? `<div class="error">${esc(R.error)}</div>` : '';
    $$('.xsection', root).forEach((s) => { s.style.opacity = R.error ? 0.35 : 1; });
    if (R.error) return;
    renderTiles(m, R, Rb);
    renderRanking(m, R, Rb);
    renderMaps(m, R);
    renderProfile(m, R);
    renderMatrix(m, R);
    renderPCA(m, R);
    renderClusters(m, R);
  }

  function renderRefbar(m) {
    const bar = $('[data-refbar]', X[m].root);
    bar.innerHTML = `<span class="chip ref">★ ${esc(U[state.ref].name)} ${cityTag(state.ref)}</span>` +
      state.compare.map((j, k) => `<span class="chip"><span class="dot" style="background:${compareColor(k)}"></span>${esc(U[j].name)} ${cityTag(j)}
        <button data-mkref="${j}" title="Make ${esc(U[j].name)} the reference">make reference</button><button data-rm="${j}" aria-label="Remove ${esc(U[j].name)}">×</button></span>`).join('') +
      (state.compare.length ? '' : '<span class="note">Click units in the charts or maps to compare up to three with the reference.</span>');
    bar.onclick = (e) => {
      const a = e.target.closest('[data-mkref]'), r = e.target.closest('[data-rm]');
      if (a) setRef(+a.dataset.mkref);
      if (r) toggleCompare(+r.dataset.rm);
    };
  }

  function renderTiles(m, R, Rb) {
    const root = X[m].root, ref = state.ref, rc = U[ref].city, oc = OTHER[rc], all = rankAll(R);
    const best = (city) => closest(R, city, 1)[0];
    const tile = (k, v, s) => `<div class="tile"><span class="k">${k}</span><span class="v">${v}</span><span class="s">${s}</span></div>`;
    const bo = best(oc), bs = best(rc);
    let agree, kept;
    if (sameAsBase(m)) {
      agree = tile('Against the baseline', 'Same settings', 'Change features, weights or settings to compare');
      kept = tile('Top 10 kept', '10 / 10 · 10 / 10', 'São Paulo · Chicago');
    } else {
      const c = M.compare(R.D, Rb.D, N);
      agree = tile('Against the baseline', `ρ = ${fmt(c.spearmanPairs)}`, `Spearman over all pairs; ${pct(c.meanTopkOverlap)} of top-5 neighbours shared`);
      const k = (city) => { const a = new Set(closest(R, city, 10)); return closest(Rb, city, 10).filter((j) => a.has(j)).length; };
      kept = tile("Reference's top 10 kept", `${k('SP')} / 10 · ${k('CHI')} / 10`, 'São Paulo · Chicago, against the baseline');
    }
    $('[data-tiles]', root).innerHTML = tile(`Closest in ${CITY[oc]}`, esc(U[bo].name), `distance ${fmt(R.D[ref * N + bo])} · rank ${all[bo]} of ${N - 1} overall`)
      + tile(`Closest in ${CITY[rc]}`, esc(U[bs].name), `distance ${fmt(R.D[ref * N + bs])}`) + agree + kept;
    const others = ['A', 'B', 'H'].filter((x) => x !== m).map((x) => {
      const r = current(x);
      return r.error ? `${METHODS[x].short}: n/a` : `${METHODS[x].short} → <b>${esc(U[closest(r, oc, 1)[0]].name)}</b>`;
    });
    $('[data-cross]', root).innerHTML = `Closest in ${CITY[oc]} by the other methods (their current settings): ${others.join(' · ')}.`;
  }

  /* Contribution matrix: what drives each match (rows = units, columns = features). */
  function contribution(m, R, units) {
    const ref = state.ref;
    if (m === 'H') {
      const fams = H_F.filter((f) => R.w[f] > 0);
      return { cols: fams, kind: 'share', z: units.map((j) => fams.map((f) => (R.contrib[f] ? R.contrib[f][ref * N + j] : 0) / (R.Dfull[ref * N + j] ** 2 || 1))), names: fams.map((f) => `${f} ${FAM[f].name}`) };
    }
    const F = AB_F.filter((f) => R.w[f] > 0), S = V.ab[m].scaled;
    if (R.cfg.rule === 'gap') return { cols: F, kind: 'signed', z: units.map((j) => F.map((f) => R.w[f] * (S[f][j] - S[f][ref]))), names: F.map((f) => V.ab.factors.find((x) => x.id === f).name) };
    return { cols: F, kind: 'share', z: units.map((j) => F.map((f) => R.w[f] * (S[f][j] - S[f][ref]) ** 2 / (R.D[ref * N + j] ** 2 || 1))), names: F.map((f) => V.ab.factors.find((x) => x.id === f).name) };
  }

  function renderRanking(m, R, Rb) {
    const root = X[m].root, ref = state.ref, ui = state.ui[m], all = rankAll(R), same = sameAsBase(m);
    const ruleName = m === 'H' ? (R.cfg.geometry === 'pca' ? 'PCA-truncated distance (R2)' : 'model distance D') : (R.cfg.rule === 'gap' ? 'index gap |I(u) − I(ref)|' : 'factor profile distance');
    $('[data-rank-note]', root).textContent = `Bars: ${ruleName}, shorter = more alike.` + (ui.breakdown ? (m === 'H'
      ? ' Matrix: each family\'s share of the squared distance' + (R.cfg.geometry === 'pca' ? ' (from the full model, which R2 approximates).' : '.')
      : R.cfg.rule === 'gap' ? ' Matrix: each factor\'s signed part of the index difference (blue = the unit is lower, red = higher); parts can cancel.' : ' Matrix: each factor\'s share of the squared profile distance.') : '')
      + (same ? '' : ' Labels show the rank change against the baseline.');
    for (const city of ['SP', 'CHI']) {
      const el = X[m].p('rank-' + city), top = closest(R, city, 10);
      const bOrder = M.order(Rb.D, N, ref, POOL[city]);
      const names = top.map((j, k) => `${k + 1}. ${U[j].name}`);
      const shift = top.map((j, k) => { if (same) return ''; const b = bOrder.indexOf(j); return b >= 10 ? ' new' : b === k ? ' =' : b > k ? ` ▲${b - k}` : ` ▼${k - b}`; });
      const dist = top.map((j) => R.D[ref * N + j]);
      const data = [{ type: 'bar', orientation: 'h', x: dist, y: names, customdata: top, xaxis: 'x', yaxis: 'y',
        marker: { color: top.map((j) => (state.compare.includes(j) ? compareColor(state.compare.indexOf(j)) : T.city[city])), line: { width: 0 } },
        text: dist.map((d, k) => fmt(d) + shift[k]), textposition: 'outside', cliponaxis: false, textfont: { size: 11, color: T.ink2 },
        hovertemplate: top.map((j, k) => `<b>${esc(U[j].name)}</b><br>distance %{x:.3f}<br>rank ${k + 1} in ${CITY[city]}, ${all[j]} of ${N - 1} overall` + (same ? '' : `<br>baseline rank in ${CITY[city]}: ${bOrder.indexOf(j) + 1}`) + '<extra></extra>') }];
      const lay = layout({ height: 390, margin: { l: 150, r: 16, t: 34, b: ui.breakdown ? 56 : 34 }, bargap: 0.45,
        title: { text: `Closest in ${CITY[city]}`, font: { size: 14, color: T.ink, family: T.sans }, x: 0, xanchor: 'left', y: 0.98 },
        yaxis: { autorange: 'reversed', automargin: true, tickfont: { size: 11, color: T.ink }, gridcolor: 'rgba(0,0,0,0)' },
        xaxis: { domain: ui.breakdown ? [0, 0.5] : [0, 0.92], range: [0, Math.max(...dist) * 1.35], title: { text: 'distance' } } });
      if (ui.breakdown) {
        const C = contribution(m, R, top), amax = Math.max(1e-9, ...C.z.flat().map(Math.abs)), signed = C.kind === 'signed';
        data.push({ type: 'heatmap', z: C.z, x: C.cols, y: names, xaxis: 'x2', yaxis: 'y', xgap: 2, ygap: 2,
          colorscale: signed ? divScale() : seqScale(), zmin: signed ? -amax : 0, zmax: amax, customdata: C.z.map(() => C.names),
          colorbar: { orientation: 'h', x: 0.78, xanchor: 'center', y: -0.04, yanchor: 'top', len: 0.42, thickness: 7, outlinewidth: 0,
            tickformat: signed ? '+.2f' : '.0%', tickfont: { size: 9, color: T.ink2 }, nticks: 4 },
          hovertemplate: signed ? '%{y}<br>%{customdata}: %{z:+.3f} of the index gap<extra></extra>' : '%{y}<br>%{customdata}: %{z:.0%} of the squared distance<extra></extra>' });
        lay.xaxis2 = { domain: [0.56, 1], anchor: 'y', side: 'top', tickmode: 'array', tickvals: C.cols, tickfont: { size: 9.5, color: T.ink2, family: T.mono }, tickangle: 0, gridcolor: 'rgba(0,0,0,0)', linecolor: 'rgba(0,0,0,0)' };
      }
      plot(el, data, lay, (p) => toggleCompare(p.customdata !== undefined && typeof p.customdata === 'number' ? p.customdata : top[names.indexOf(p.y)]));
      const allTop = M.order(R.D, N, ref, POOL[city]).slice(0, 20);
      $(`[data-ranktable="${city}"]`, root).innerHTML = table(['Rank', `${CITY[city]} unit`, 'Distance', 'Rank of all', 'Baseline rank'], allTop.map((j, k) =>
        [k + 1, esc(U[j].name), fmt(R.D[ref * N + j]), all[j], bOrder.indexOf(j) + 1]), [0, 2, 3, 4]);
    }
  }

  function mapOptions(m, R) {
    const sel = $('[data-ui="mapBy"]', X[m].root);
    const opts = [['distance', 'Distance to the reference']].concat(m === 'H' ? [] : [['index', `Index ${m} value`]]).concat(R.axes.map((a) => ['ax:' + a.id, `${a.code} ${a.label}`]));
    const key = opts.map((o) => o[0]).join();
    if (sel.dataset.key !== key) { sel.innerHTML = opts.map(([v, t]) => `<option value="${v}">${esc(t)}</option>`).join(''); sel.dataset.key = key; }
    if (!opts.some((o) => o[0] === state.ui[m].mapBy)) state.ui[m].mapBy = 'distance';
    sel.value = state.ui[m].mapBy;
  }

  function renderMaps(m, R) {
    mapOptions(m, R);
    const ref = state.ref, by = state.ui[m].mapBy, root = X[m].root, all = rankAll(R);
    const top = [...closest(R, 'SP', 10), ...closest(R, 'CHI', 10)];
    let fill, legend, valueText;
    if (by === 'distance') {
      const others = Array.from({ length: N }, (_, j) => R.D[ref * N + j]).filter((_, j) => j !== ref), lo = Math.min(...others), hi = quantile(others, 0.95);
      fill = (i) => (i === ref ? T.surface : ramp(T.seq, 1 - (R.D[ref * N + i] - lo) / (hi - lo)));
      legend = `<span>more alike ${fmt(lo)}</span><span class="bar" style="background:linear-gradient(90deg,${T.seq.slice().reverse().join(',')})"></span><span>≥ ${fmt(hi)} less alike</span>`;
      valueText = (i) => `distance ${fmt(R.D[ref * N + i])} · rank ${all[i]} of ${N - 1}`;
    } else if (by === 'index') {
      const v = R.index, lo = Math.min(...v), hi = Math.max(...v);
      fill = (i) => ramp(T.seq, (v[i] - lo) / (hi - lo));
      legend = `<span>Index ${m} ${fmt(lo, 2)}</span><span class="bar" style="background:linear-gradient(90deg,${T.seq.join(',')})"></span><span>${fmt(hi, 2)}</span>`;
      valueText = (i) => `index ${fmt(v[i])} · gap to reference ${fmt(Math.abs(v[i] - v[ref]))}`;
    } else {
      const a = R.axes.find((x) => 'ax:' + x.id === by);
      if (m === 'H') {
        fill = (i) => (a.values[i] === null ? T.rule : ramp(T.div, (a.values[i] + 3) / 6));
        legend = `<span>${esc(a.code)} ${esc(a.label)}: −3 SD</span><span class="bar" style="background:linear-gradient(90deg,${T.div.join(',')})"></span><span>+3 SD (${a.level} scaling)</span><span class="muted">grey = missing</span>`;
      } else {
        fill = (i) => ramp(T.seq, a.values[i]);
        legend = `<span>${esc(a.label)}: 0 (lowest unit)</span><span class="bar" style="background:linear-gradient(90deg,${T.seq.join(',')})"></span><span>1 (highest)</span>`;
      }
      valueText = (i) => `${esc(a.label)}: ${rawText(a, i)} · standardized ${fmt(a.values[i], 2)}`;
    }
    const rings = top.map((i) => ({ i, color: T.ink, width: 1.6 })).concat(state.compare.map((i, k) => ({ i, color: compareColor(k), width: 3 }))).concat([{ i: ref, color: T.ink, width: 3 }]);
    for (const map of Object.values(X[m].maps)) {
      map.update({ fill, rings, labels: [{ i: ref, text: '★ ' + U[ref].name }],
        tipFor: (i) => `<b>${esc(U[i].name)}</b> ${cityTag(i)}<br>${i === ref ? 'Reference' : valueText(i)}<br><span class="muted">Click to ${state.compare.includes(i) ? 'remove from' : 'add to'} the comparison</span>`,
        onClick: (i) => toggleCompare(i) });
    }
    $('[data-maplegend]', root).innerHTML = legend;
  }

  /* Raw values, formatted by unit. */
  function rawText(a, i) {
    const v = a.raw[i];
    if (v === null || v === undefined) return 'missing';
    switch (a.unit) {
      case 'share': return pct(v, 1);
      case 'ln m²': return `≈ ${nf(0).format(Math.exp(v))} m²`;
      case 'ln per 100 dwellings': return `${fmt(Math.exp(v), 1)} per 100 dwellings`;
      case '4πA/P²': return fmt(v, 3);
      case 'ratio': case 'clr': return fmt(v, 2);
      case 'km/km²': case 'm': case 'PTAL AI': return fmt(v, 1) + (a.unit === 'm' ? ' m' : a.unit === 'km/km²' ? ' km/km²' : '');
      default: return `${nf(Math.abs(v) < 100 ? 1 : 0).format(v)} ${a.unit}`;
    }
  }

  function renderProfile(m, R) {
    const root = X[m].root, ref = state.ref, axes = R.axes.filter((a) => !a.off), units = [ref, ...state.compare];
    if (!state.compare.length) { const best = closest(R, OTHER[U[ref].city], 1)[0]; units.push(best); }
    const color = (k) => (k === 0 ? T.ink : compareColor(state.compare.length ? k - 1 : 0));
    const theta = axes.map((a) => `${a.code} ${a.short || a.label}`);
    const isH = m === 'H';
    const data = units.map((i, k) => ({ type: 'scatterpolar', r: [...axes.map((a) => a.values[i]), axes[0].values[i]], theta: [...theta, theta[0]], name: label(i),
      mode: 'lines+markers', line: { color: color(k), width: k ? 2 : 2.5 }, marker: { size: 5, color: color(k) }, fill: k ? 'none' : 'toself', fillcolor: k ? undefined : 'rgba(127,127,127,0.10)',
      connectgaps: false, hovertemplate: `<b>${esc(U[i].name)}</b><br>%{theta}: %{r:.2f}<extra></extra>` }));
    plot(X[m].p('radar'), data, layout({ height: 520, margin: { l: 110, r: 110, t: 40, b: 64 }, showlegend: true, legend: { orientation: 'h', y: -0.08, x: 0.5, xanchor: 'center' },
      polar: { bgcolor: 'rgba(0,0,0,0)', radialaxis: { range: isH ? [-3.3, 3.3] : [0, 1], gridcolor: T.rule, linecolor: T.ruleStrong, tickfont: { size: 10, color: T.muted }, angle: 90, tickangle: 90 },
        angularaxis: { direction: 'clockwise', rotation: 90, gridcolor: T.rule, linecolor: T.ruleStrong, tickfont: { size: 10, color: T.ink } } } }));
    $('[data-profile-note]', root).innerHTML = (isH
      ? 'Each axis is a model column as the distance sees it: a z-score capped at ±3. Zero is the mean of the comparison group (all 173 units for <span class="pill abs">absolute</span> columns, the unit\'s own city for <span class="pill rel">relative</span> ones under the current scaling). U6 composition enters the distance through its log-ratios and is not drawn.'
      : `Each axis is a factor min–max scaled over the 173 units (0 = lowest unit, 1 = highest), exactly as it enters Index ${m}.`)
      + (state.compare.length ? '' : ' With no unit selected, the closest unit in the other city is drawn.');
    const head = ['Axis', 'What it measures'].concat(units.map((i, k) => `<span class="swatch" style="background:${color(k)}"></span>${esc(U[i].name)}`));
    $('[data-featguide]', root).innerHTML = table(head, axes.map((a) => [
      `<b class="mono">${a.code}</b> ${esc(a.label)}${isH ? `<div><span class="pill ${a.level === 'absolute' ? 'abs' : 'rel'}">${a.level}</span></div>` : ''}`,
      `<span class="ink2">${esc(a.desc)}</span><div class="muted">High: ${esc(a.high)}.</div>`,
      ...units.map((i) => `<span class="num">${rawText(a, i)}</span><div class="muted num">${isH ? 'z' : 'scaled'} ${fmt(a.values[i], 2)}</div>`)]));
  }

  function renderMatrix(m, R) {
    const ref = state.ref, mode = state.ui[m].heat;
    $('[data-ui="heat"]', X[m].root).value = mode;
    let units;
    if (mode === 'nbhd') units = [ref, ...closest(R, 'SP', 10), ...closest(R, 'CHI', 10)];
    else {
      const L = R.C.labels, s = R.P.scores;
      units = Array.from({ length: N }, (_, i) => i).sort((a, b) => L[a] - L[b] || s[a][0] - s[b][0]);
    }
    const names = units.map((i) => (i === ref ? '★ ' : '') + label(i));
    const z = units.map((i) => units.map((j) => (i === j ? null : R.D[i * N + j])));
    const vals = z.flat().filter((v) => v !== null), hi = quantile(vals, 0.95);
    const shapes = [];
    if (mode === 'all') {
      const L = R.C.labels;
      units.forEach((u, k) => { if (k && L[u] !== L[units[k - 1]]) { shapes.push({ type: 'line', x0: k - 0.5, x1: k - 0.5, y0: -0.5, y1: N - 0.5, line: { color: T.ink, width: 1 } }, { type: 'line', y0: k - 0.5, y1: k - 0.5, x0: -0.5, x1: N - 0.5, line: { color: T.ink, width: 1 } }); } });
      const r = units.indexOf(ref);
      shapes.push({ type: 'rect', x0: -0.5, x1: N - 0.5, y0: r - 0.5, y1: r + 0.5, line: { color: T.ink, width: 1.5 } });
    } else {
      shapes.push({ type: 'line', x0: 10.5, x1: 10.5, y0: -0.5, y1: units.length - 0.5, line: { color: T.ink, width: 1 } }, { type: 'line', y0: 10.5, y1: 10.5, x0: -0.5, x1: units.length - 0.5, line: { color: T.ink, width: 1 } });
    }
    const big = mode === 'all', el = X[m].p('heat');
    const ml = big ? 20 : 190, mb = big ? 20 : 150, side = Math.max(240, Math.min(el.clientWidth - ml - 90, big ? 680 : 520));
    plot(el, [{ type: 'heatmap', z, x: names, y: names, colorscale: seqScaleRev(), zmin: 0, zmax: hi, xgap: big ? 0 : 1, ygap: big ? 0 : 1,
      colorbar: { thickness: 10, len: 0.6, title: { text: 'distance', side: 'right', font: { size: 11, color: T.ink2 } }, tickfont: { size: 10, color: T.ink2 }, outlinewidth: 0 },
      hoverongaps: false, hovertemplate: '%{y}<br>↔ %{x}<br>distance %{z:.3f}<extra></extra>' }],
    layout({ height: side + 10 + mb, margin: { l: ml, r: 10, t: 10, b: mb }, shapes,
      xaxis: { showticklabels: !big, tickangle: -50, tickfont: { size: 10 }, gridcolor: 'rgba(0,0,0,0)', constrain: 'domain' },
      yaxis: { showticklabels: !big, autorange: 'reversed', tickfont: { size: 10 }, gridcolor: 'rgba(0,0,0,0)', scaleanchor: 'x' } }),
    (p) => { const j = units[names.indexOf(p.x)]; if (j !== undefined) toggleCompare(j); });
  }

  function pcSelects(m, R) {
    const n = Math.min(6, R.P.scores[0].length), root = X[m].root;
    for (const k of ['pcx', 'pcy']) {
      const sel = $(`[data-ui="${k}"]`, root);
      if (+sel.dataset.n !== n) { sel.innerHTML = Array.from({ length: n }, (_, c) => `<option value="${c}">PC${c + 1}</option>`).join(''); sel.dataset.n = n; }
      if (state.ui[m][k] >= n) state.ui[m][k] = k === 'pcx' ? 0 : Math.min(1, n - 1);
      sel.value = state.ui[m][k];
    }
    $('[data-ui="pcColor"]', root).value = state.ui[m].pcColor;
  }

  function scatterTraces(m, R, colorBy, cx, cy) {
    const s = R.P.scores, ref = state.ref, L = R.C.labels, all = rankAll(R);
    const hover = (i) => `<b>${esc(U[i].name)}</b> (${CITY[U[i].city]})<br>cluster ${L[i] + 1}` + (i === ref ? '<br>reference' : `<br>distance ${fmt(R.D[ref * N + i])} · rank ${all[i]}`);
    const sym = (i) => (U[i].city === 'SP' ? 'circle' : 'diamond');
    const groups = colorBy === 'city' ? ['SP', 'CHI'].map((c) => ({ name: CITY[c], ids: POOL[c], color: T.city[c] }))
      : Array.from({ length: R.C.k }, (_, c) => ({ name: `Cluster ${c + 1}`, ids: Array.from({ length: N }, (_, i) => i).filter((i) => L[i] === c), color: T.cat[c] }));
    const tr = groups.map((g) => ({ type: 'scatter', mode: 'markers', name: g.name, x: g.ids.map((i) => s[i][cx]), y: g.ids.map((i) => s[i][cy]), customdata: g.ids,
      marker: { color: g.color, size: 9, symbol: g.ids.map(sym), line: { color: T.surface, width: 1 } }, hovertext: g.ids.map(hover), hoverinfo: 'text' }));
    const top = [...closest(R, 'SP', 10), ...closest(R, 'CHI', 10)];
    tr.push({ type: 'scatter', mode: 'markers', name: '10 closest per city', x: top.map((i) => s[i][cx]), y: top.map((i) => s[i][cy]), customdata: top, hoverinfo: 'skip',
      marker: { size: 16, color: 'rgba(0,0,0,0)', symbol: 'circle-open', line: { color: T.ink, width: 1.5 } } });
    tr.push({ type: 'scatter', mode: 'markers', name: 'Reference', x: [s[ref][cx]], y: [s[ref][cy]], customdata: [ref], hovertext: [hover(ref)], hoverinfo: 'text',
      marker: { size: 20, color: T.ink, symbol: 'star', line: { color: T.surface, width: 1.5 } } });
    const ann = [ref, ...state.compare].map((i, k) => ({ x: s[i][cx], y: s[i][cy], text: (k ? '' : '★ ') + esc(U[i].name), showarrow: true, arrowhead: 0, arrowwidth: 1, arrowcolor: T.ink2, ax: 24, ay: -22,
      font: { size: 11, color: T.ink }, bgcolor: T.surface, bordercolor: k ? compareColor(k - 1) : T.ink, borderwidth: 1, borderpad: 2 }));
    return { tr, ann };
  }

  function renderPCA(m, R) {
    pcSelects(m, R);
    const root = X[m].root, ui = state.ui[m], P = R.P, cx = ui.pcx, cy = ui.pcy;
    const { tr, ann } = scatterTraces(m, R, ui.pcColor, cx, cy);
    const ex = (c) => `PC${c + 1} (${pct(P.explained[c], 1)})`;
    plot(X[m].p('pca'), tr, layout({ height: 560, showlegend: true, legend: { orientation: 'h', y: -0.12 }, annotations: ann, margin: { l: 56, r: 12, t: 12, b: 70 },
      xaxis: { title: { text: ex(cx) }, zeroline: true }, yaxis: { title: { text: ex(cy) }, zeroline: true } }), (p) => { if (typeof p.customdata === 'number') toggleCompare(p.customdata); });
    const k = Math.min(10, P.explained.length), xs = Array.from({ length: k }, (_, c) => `PC${c + 1}`);
    plot(X[m].p('scree'), [
      { type: 'bar', x: xs, y: P.explained.slice(0, k), name: 'each component', marker: { color: xs.map((_, c) => (c < P.k90 ? T.acc : T.ruleStrong)) }, hovertemplate: '%{x}: %{y:.1%}<extra></extra>' },
      { type: 'scatter', mode: 'lines+markers', x: xs, y: P.cumulative.slice(0, k), name: 'cumulative', line: { color: T.ink, width: 2 }, marker: { size: 6, color: T.ink }, hovertemplate: 'up to %{x}: %{y:.1%}<extra></extra>' }],
    layout({ height: 230, showlegend: true, legend: { orientation: 'h', y: -0.3 }, margin: { l: 44, r: 10, t: 8, b: 56 }, yaxis: { tickformat: '.0%', range: [0, 1.02] },
      shapes: [{ type: 'line', xref: 'paper', x0: 0, x1: 1, y0: 0.9, y1: 0.9, line: { color: T.muted, width: 1 } }],
      annotations: [{ xref: 'paper', x: 1, y: 0.86, yanchor: 'top', xanchor: 'right', showarrow: false, text: `90% reached with ${P.k90} components`, font: { size: 10, color: T.ink2 }, bgcolor: T.surface }] }));
    const names = Object.keys(R.load), npc = R.load[names[0]].length;
    plot(X[m].p('load'), [{ type: 'heatmap', z: names.map((n) => R.load[n]), x: Array.from({ length: npc }, (_, c) => `PC${c + 1}`), y: names, colorscale: divScale(), zmin: -1, zmax: 1, xgap: 2, ygap: 2,
      colorbar: { thickness: 8, len: 0.8, tickfont: { size: 9, color: T.ink2 }, outlinewidth: 0 }, hovertemplate: '%{y}<br>%{x}: r = %{z:.2f}<extra></extra>' }],
    layout({ height: Math.max(220, 20 * names.length + 50), margin: { l: 170, r: 10, t: 8, b: 30 }, yaxis: { autorange: 'reversed', tickfont: { size: 10, color: T.ink }, gridcolor: 'rgba(0,0,0,0)' }, xaxis: { side: 'bottom', tickangle: 0, tickfont: { size: 10 }, gridcolor: 'rgba(0,0,0,0)' } }));
    const top = (c) => names.map((n) => [n, R.load[n][c]]).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).slice(0, 3).map(([n, v]) => `${n} ${v > 0 ? '+' : '−'}${fmt(Math.abs(v), 2)}`).join(', ');
    $('[data-pca-note]', root).innerHTML = `${m === 'H' ? 'Principal coordinates of the full-model distance' : 'PCA of the weighted factor profile'} over all ${N} units. ${P.k90} components reach 90% of the variance. PC1 is led by ${top(0)}; PC2 by ${top(1)}. Circles: São Paulo; diamonds: Chicago. Ringed: the reference's 10 closest per city.`;
  }

  function renderClusters(m, R) {
    const root = X[m].root, C = R.C, L = C.labels, ref = state.ref, ui = state.ui[m];
    const { tr, ann } = scatterTraces(m, R, 'cluster', ui.pcx, ui.pcy);
    const P = R.P;
    plot(X[m].p('clscatter'), tr, layout({ height: 460, showlegend: true, legend: { orientation: 'h', y: -0.14 }, annotations: ann.slice(0, 1), margin: { l: 56, r: 12, t: 12, b: 70 },
      xaxis: { title: { text: `PC${ui.pcx + 1} (${pct(P.explained[ui.pcx], 1)})` } }, yaxis: { title: { text: `PC${ui.pcy + 1} (${pct(P.explained[ui.pcy], 1)})` } } }), (p) => { if (typeof p.customdata === 'number') toggleCompare(p.customdata); });
    const ks = [2, 3, 4, 5, 6, 7, 8];
    plot(X[m].p('sil'), [{ type: 'scatter', mode: 'lines+markers', x: ks, y: ks.map((k) => C.silhouette[k]), line: { color: T.ink2, width: 2 },
      marker: { size: ks.map((k) => (k === C.k ? 14 : 7)), color: ks.map((k) => (k === C.k ? T.acc : T.ink2)) }, hovertemplate: 'k = %{x}: silhouette %{y:.3f}<extra></extra>' }],
    layout({ height: 250, margin: { l: 50, r: 10, t: 10, b: 40 }, xaxis: { title: { text: 'k' }, dtick: 1 }, yaxis: { title: { text: 'mean silhouette' } } }));
    const cnote = m === 'H' && R.cfg.geometry === 'pca' ? 'the components of the PCA distance' : 'all positive principal components';
    $('[data-cl-note]', root).textContent = `Ward clustering on ${cnote} (k = ${C.k}, silhouette ${fmt(C.silhouette[C.k])}${R.cfg.k ? ', fixed' : ', best of 3–8'}). Colours follow the baseline's clusters where groups match. A descriptive check, not a validated typology. Circles: São Paulo; diamonds: Chicago.`;
    for (const map of Object.values(X[m].clmaps)) {
      map.update({ fill: (i) => T.cat[L[i]], rings: [{ i: ref, color: T.ink, width: 3 }], labels: [{ i: ref, text: '★ ' + U[ref].name }],
        tipFor: (i) => `<b>${esc(U[i].name)}</b> ${cityTag(i)}<br>Cluster ${L[i] + 1}`, onClick: (i) => toggleCompare(i) });
    }
    $('[data-cllegend]', root).innerHTML = Array.from({ length: C.k }, (_, c) => `<span><span class="swatch" style="background:${T.cat[c]}"></span>Cluster ${c + 1}</span>`).join('');
    // profiles: mean standardized value of each axis by cluster (A/B factors re-standardized over the 173 units)
    const axes = R.axes.filter((a) => !a.off);
    const zOf = (a) => {
      if (m === 'H') return a.values;
      const v = a.values, mu = v.reduce((s, x) => s + x, 0) / N, sd = Math.sqrt(v.reduce((s, x) => s + (x - mu) ** 2, 0) / N) || 1;
      return v.map((x) => (x - mu) / sd);
    };
    const Z = axes.map(zOf);
    const prof = Array.from({ length: C.k }, (_, c) => axes.map((a, q) => { const v = Z[q].filter((x, i) => L[i] === c && x !== null); return v.reduce((s, x) => s + x, 0) / v.length; }));
    plot(X[m].p('clprof'), [{ type: 'heatmap', z: prof, x: axes.map((a) => a.code), y: prof.map((_, c) => `Cluster ${c + 1}`), customdata: prof.map(() => axes.map((a) => a.label)),
      colorscale: divScale(), zmin: -2, zmax: 2, xgap: 2, ygap: 2, colorbar: { thickness: 8, len: 0.9, tickfont: { size: 9, color: T.ink2 }, outlinewidth: 0 },
      hovertemplate: '%{y}<br>%{customdata}: %{z:+.2f} SD<extra></extra>' }],
    layout({ height: 70 + 34 * C.k, margin: { l: 80, r: 10, t: 8, b: 40 }, yaxis: { autorange: 'reversed', gridcolor: 'rgba(0,0,0,0)' }, xaxis: { tickfont: { family: T.mono, size: 10 }, gridcolor: 'rgba(0,0,0,0)' } }));
    const E = R.P.scores, rows = Array.from({ length: C.k }, (_, c) => {
      const ids = Array.from({ length: N }, (_, i) => i).filter((i) => L[i] === c), d = E[0].length;
      const cen = Array.from({ length: d }, (_, q) => ids.reduce((s, i) => s + E[i][q], 0) / ids.length);
      const rep = ids.slice().sort((a, b) => E[a].reduce((s, v, q) => s + (v - cen[q]) ** 2, 0) - E[b].reduce((s, v, q) => s + (v - cen[q]) ** 2, 0)).slice(0, 3);
      const ord = axes.map((a, q) => [a.code, prof[c][q]]).sort((a, b) => b[1] - a[1]);
      const row = [`<span style="white-space:nowrap"><span class="swatch" style="background:${T.cat[c]}"></span>Cluster ${c + 1}</span>`, ids.filter((i) => U[i].city === 'SP').length, ids.filter((i) => U[i].city === 'CHI').length,
        `high ${ord.slice(0, 2).map((x) => x[0]).join(', ')}; low ${ord.slice(-2).map((x) => x[0]).join(', ')}`, rep.map((i) => esc(U[i].name)).join(', ')];
      row.hl = L[ref] === c;
      return row;
    });
    $('[data-cltable]', root).innerHTML = table(['Cluster', 'São Paulo', 'Chicago', 'Character (mean SD)', 'Most typical members'], rows, [1, 2]);
    const mem = Array.from({ length: N }, (_, i) => i).filter((i) => L[i] === L[ref] && i !== ref);
    $('[data-members-title]', root).textContent = `${U[ref].name} is in cluster ${L[ref] + 1}, with ${mem.length} other units`;
    $('[data-members]', root).innerHTML = ['SP', 'CHI'].map((c) => `<div style="margin-top:6px"><h4>${CITY[c]} (${mem.filter((i) => U[i].city === c).length})</h4><div class="members" style="margin-top:6px">${mem.filter((i) => U[i].city === c)
      .sort((a, b) => R.D[ref * N + a] - R.D[ref * N + b]).map((i) => `<button data-cmp="${i}">${esc(U[i].name)}</button>`).join('') || '<span class="note">none</span>'}</div></div>`).join('');
    $('[data-members]', root).onclick = (e) => { const b = e.target.closest('[data-cmp]'); if (b) toggleCompare(+b.dataset.cmp); };
  }

  /* ---------------------------------------------------------------- init */
  function init() {
    readTokens();
    fillStatic();
    bindRefInput($('#ov-ref'));
    $('#ov-ref').dataset.ref = '';
    syncRefInputs();
    document.addEventListener('click', (e) => { const g = e.target.closest('[data-go]'); if (g) { e.preventDefault(); location.hash = g.dataset.go; } });
    $$('.tab').forEach((b) => b.addEventListener('click', () => { location.hash = b.dataset.tab; }));
    $('#theme').addEventListener('click', toggleTheme);
    matchMedia('(prefers-color-scheme: dark)').addEventListener('change', schedule);
    let resizing;
    window.addEventListener('resize', () => { clearTimeout(resizing); resizing = setTimeout(schedule, 150); });
    window.addEventListener('hashchange', route);
    route();
  }
  init();
})();
