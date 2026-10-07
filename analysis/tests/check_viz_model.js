/* Runnable check: the explorer's in-browser computations reproduce the published model results.
   Usage (from the repository root): node analysis/tests/check_viz_model.js */
const fs = require('fs'), path = require('path'), vm = require('vm');
const M = require('../../viz/model.js');

const here = __dirname, res = path.join(here, '../results/SP_CHI');
const ctx = { window: {} };
vm.runInNewContext(fs.readFileSync(path.join(here, '../../viz/data.js'), 'utf8'), ctx);
const V = ctx.window.VIZ_DATA, n = V.units.length, ids = V.units.map((u) => u.id);
const csv = (f) => fs.readFileSync(f, 'utf8').trim().split('\n').map((l) => l.split(','));
let failed = 0;
const check = (name, ok, detail) => { console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${detail ? ': ' + detail : ''}`); failed += !ok; };

function matrix(file) {                     // published n x n distance table, reordered to the page's unit order
  const rows = csv(file), head = rows[0].slice(1), D = new Float64Array(n * n);
  const col = ids.map((u) => head.indexOf(u)), row = new Map(rows.slice(1).map((r) => [r[0], r.slice(1).map(Number)]));
  ids.forEach((u, i) => col.forEach((c, j) => { D[i * n + j] = row.get(u)[c]; }));
  return D;
}
const maxDiff = (a, b) => a.reduce((m, v, p) => Math.max(m, Math.abs(v - b[p])), 0);
const equal = (fams) => Object.fromEntries(V.h.families.map((f) => [f.id, fams.includes(f.id) ? 0 : 1]));
const tab = (s) => path.join(res, 'sp_chicago_model_v1_2026_10_06/tables', s);

/* Harmonized model: R1, R2, R3 under the three C6 scalings. */
let hybrid;
for (const s of ['hybrid', 'all_absolute', 'all_relative']) {
  const sc = V.h.scalings[s], mats = M.blockMatrices(sc.blocks, n);
  const r1 = M.harmonizedDistance(mats, sc.blocks, equal([]), n);
  check(`${s} R1 distance`, maxDiff(r1.D, matrix(tab(`distance_${s}_R1.csv`))) < 1e-9, `max |diff| ${maxDiff(r1.D, matrix(tab(`distance_${s}_R1.csv`))).toExponential(1)}`);
  const P = M.pcoa(r1.D, n), r2 = M.euclidean(P.scores, n, P.k90);
  check(`${s} R2 distance (${P.k90} components)`, maxDiff(r2, matrix(tab(`distance_${s}_R2.csv`))) < 1e-7, `max |diff| ${maxDiff(r2, matrix(tab(`distance_${s}_R2.csv`))).toExponential(1)}`);
  const r3 = M.harmonizedDistance(mats, sc.blocks, equal(V.h.r3_dropped[s]), n);
  check(`${s} R3 distance (without ${V.h.r3_dropped[s].join(', ')})`, maxDiff(r3.D, matrix(tab(`distance_${s}_R3.csv`))) < 1e-9);
  if (s === 'hybrid') hybrid = { mats, sc, r1, P };
}

const { mats, sc, r1, P } = hybrid;
const pv = csv(tab('pca_variance.csv')).slice(1, 9).map((r) => +r[1]);
check('hybrid PCA explained variance, PC1-PC8', pv.every((v, c) => Math.abs(v - P.explained[c]) < 1e-9));

const lofo = M.compare(M.harmonizedDistance(mats, sc.blocks, equal(['M1']), n).D, r1.D, n);
const sens = csv(tab('sensitivities_hybrid.csv')).find((r) => r[0] === 'without M1');
check('sensitivity "without M1" (Spearman, shared top-5)', lofo.spearmanPairs.toFixed(3) === (+sens[1]).toFixed(3) && lofo.meanTopkOverlap.toFixed(3) === (+sens[2]).toFixed(3),
  `${lofo.spearmanPairs.toFixed(3)}, ${lofo.meanTopkOverlap.toFixed(3)}`);

const C = M.clusters(P.scores, n);
const pub = new Map(csv(tab('ward_clusters.csv')).slice(1).map((r) => [r[0], +r[r.length - 2]]));
const pairs = new Set(ids.map((u, i) => `${C.labels[i]}-${pub.get(u)}`));
check(`Ward clusters: best k ${C.k}, silhouette ${C.silhouette[C.k].toFixed(3)}, same partition as published`,
  C.k === 4 && C.silhouette[4].toFixed(3) === '0.262' && pairs.size === 4);

/* Cross-City Urban Index A and B. */
const F = V.ab.factors.map((f) => f.id), ones = Object.fromEntries(F.map((f) => [f, 1]));
const bras = ids.indexOf('SP:10'), chi = ids.map((u, i) => i).filter((i) => V.units[i].city === 'CHI');
const match = csv(path.join(res, 'simple_index_ab_2026_10_01/tables/bras_chicago_match.csv'));
for (const m of ['A', 'B']) {
  const r = M.indexModel(V.ab[m].scaled, F, ones, n);
  check(`index ${m} equals published`, maxDiff(r.index, V.ab[m].index) < 1e-12);
  const rank = Array.from(r.index, (v) => 1 + Array.from(r.index).filter((w) => w > v).length);
  check(`index ${m} ranks equal published`, rank.every((v, i) => v === V.ab[m].rank[i]));
  const rows = match.filter((x) => x[0] === m), gapOrder = M.order(r.gap, n, bras, chi);
  const okGap = rows.every((x) => { const i = ids.indexOf(x[1]); return 1 + gapOrder.filter((j) => r.gap[bras * n + j] < r.gap[bras * n + i]).length === +x[7]; });
  const okProf = rows.every((x) => Math.abs(r.profile[bras * n + ids.indexOf(x[1])] - +x[8]) < 6e-5);
  check(`index ${m}: Brás's Chicago gap ranks and profile distances equal published`, okGap && okProf, `pick ${V.units[gapOrder[0]].name}`);
}

console.log(failed ? `\n${failed} check(s) failed` : '\nall checks passed');
process.exit(failed ? 1 : 0);
