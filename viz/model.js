/* Model core of the Cross-City Urban Explorer: pure functions, no DOM. Loaded by index.html as the global `VizModel`
   and by check_model.js under Node, which asserts that these functions reproduce the published results.
   Distance matrices are flat Float64Array(n * n), row-major. */
(function (root) {
  'use strict';

  const sq = (x) => x * x;

  /* Harmonized model (sp_chicago_model_v1). Each block b holds X (n x c, null = missing), its share s_b of its family
     budget and its calibration beta_b. blockMatrices precomputes m_b / beta_b once per C6 scaling. */
  function blockMatrices(blocks, n) {
    return blocks.map((b) => {
      const m = new Float64Array(n * n), c = b.X[0].length;
      for (let i = 0; i < n; i++) {
        for (let j = i; j < n; j++) {
          let s = 0;
          for (let k = 0; k < c; k++) {
            const a = b.X[i][k], e = b.X[j][k];
            if (a === null || e === null) { s = NaN; break; }
            s += sq(a - e);
          }
          m[i * n + j] = m[j * n + i] = s / c / b.cal;
        }
      }
      return m;
    });
  }

  /* D^2(d,e) = sum_b w_f(b) s_b m_b / beta_b over the blocks both units have, divided by the budget of those blocks
     (J-7, J-8). Weights need not sum to 1: the denominator renormalizes. Returns D and each family's part of D^2. */
  function harmonizedDistance(mats, blocks, weights, n) {
    const N = n * n, num = new Float64Array(N), den = new Float64Array(N), contrib = {};
    blocks.forEach((b, bi) => {
      const w = (weights[b.family] || 0) * b.share;
      if (!(w > 0)) return;
      const m = mats[bi], c = contrib[b.family] || (contrib[b.family] = new Float64Array(N));
      for (let p = 0; p < N; p++) {
        const v = m[p];
        if (v === v) { num[p] += w * v; den[p] += w; c[p] += w * v; }
      }
    });
    const D = new Float64Array(N);
    for (let p = 0; p < N; p++) D[p] = Math.sqrt(num[p] / den[p]);
    for (const f in contrib) { const c = contrib[f]; for (let p = 0; p < N; p++) c[p] /= den[p]; }
    for (let i = 0; i < n; i++) D[i * n + i] = 0;
    return { D, contrib };
  }

  /* Cross-City Urban Index A/B (P-AB-1): I(u) = sum_f w_f f'(u) over the min-max scaled factors f'.
     Two dissimilarities: the agreed index gap |I(u) - I(v)| and the diagnostic factor profile
     sqrt(sum_f w_f (f'(u) - f'(v))^2). */
  function indexModel(scaled, factors, weights, n) {
    const act = factors.filter((f) => weights[f] > 0);
    const index = new Float64Array(n);
    for (const f of act) for (let i = 0; i < n; i++) index[i] += weights[f] * scaled[f][i];
    const gap = new Float64Array(n * n), profile = new Float64Array(n * n);
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        let s = 0;
        for (const f of act) s += weights[f] * sq(scaled[f][i] - scaled[f][j]);
        gap[i * n + j] = gap[j * n + i] = Math.abs(index[i] - index[j]);
        profile[i * n + j] = profile[j * n + i] = Math.sqrt(s);
      }
    }
    return { index, gap, profile };
  }

  /* Symmetric eigendecomposition: Householder tridiagonalization + implicit QL (JAMA tred2/tql2, public domain).
     V is n arrays of length n holding the matrix on entry and the eigenvectors (columns) on exit; d gets eigenvalues. */
  function tred2(n, V, d, e) {
    for (let j = 0; j < n; j++) d[j] = V[n - 1][j];
    for (let i = n - 1; i > 0; i--) {
      let scale = 0, h = 0;
      for (let k = 0; k < i; k++) scale += Math.abs(d[k]);
      if (scale === 0) {
        e[i] = d[i - 1];
        for (let j = 0; j < i; j++) { d[j] = V[i - 1][j]; V[i][j] = 0; V[j][i] = 0; }
      } else {
        for (let k = 0; k < i; k++) { d[k] /= scale; h += d[k] * d[k]; }
        let f = d[i - 1], g = Math.sqrt(h);
        if (f > 0) g = -g;
        e[i] = scale * g;
        h -= f * g;
        d[i - 1] = f - g;
        for (let j = 0; j < i; j++) e[j] = 0;
        for (let j = 0; j < i; j++) {
          f = d[j];
          V[j][i] = f;
          g = e[j] + V[j][j] * f;
          for (let k = j + 1; k <= i - 1; k++) { g += V[k][j] * d[k]; e[k] += V[k][j] * f; }
          e[j] = g;
        }
        f = 0;
        for (let j = 0; j < i; j++) { e[j] /= h; f += e[j] * d[j]; }
        const hh = f / (h + h);
        for (let j = 0; j < i; j++) e[j] -= hh * d[j];
        for (let j = 0; j < i; j++) {
          f = d[j]; g = e[j];
          for (let k = j; k <= i - 1; k++) V[k][j] -= f * e[k] + g * d[k];
          d[j] = V[i - 1][j];
          V[i][j] = 0;
        }
      }
      d[i] = h;
    }
    for (let i = 0; i < n - 1; i++) {
      V[n - 1][i] = V[i][i];
      V[i][i] = 1;
      const h = d[i + 1];
      if (h !== 0) {
        for (let k = 0; k <= i; k++) d[k] = V[k][i + 1] / h;
        for (let j = 0; j <= i; j++) {
          let g = 0;
          for (let k = 0; k <= i; k++) g += V[k][i + 1] * V[k][j];
          for (let k = 0; k <= i; k++) V[k][j] -= g * d[k];
        }
      }
      for (let k = 0; k <= i; k++) V[k][i + 1] = 0;
    }
    for (let j = 0; j < n; j++) { d[j] = V[n - 1][j]; V[n - 1][j] = 0; }
    V[n - 1][n - 1] = 1;
    e[0] = 0;
  }

  function tql2(n, V, d, e) {
    for (let i = 1; i < n; i++) e[i - 1] = e[i];
    e[n - 1] = 0;
    let f = 0, tst1 = 0;
    const eps = 2 ** -52;
    for (let l = 0; l < n; l++) {
      tst1 = Math.max(tst1, Math.abs(d[l]) + Math.abs(e[l]));
      let m = l;
      while (m < n && Math.abs(e[m]) > eps * tst1) m++;
      if (m > l) {
        do {
          let g = d[l], p = (d[l + 1] - g) / (2 * e[l]), r = Math.hypot(p, 1);
          if (p < 0) r = -r;
          d[l] = e[l] / (p + r);
          d[l + 1] = e[l] * (p + r);
          const dl1 = d[l + 1];
          let h = g - d[l];
          for (let i = l + 2; i < n; i++) d[i] -= h;
          f += h;
          p = d[m];
          let c = 1, c2 = 1, c3 = 1, s = 0, s2 = 0;
          const el1 = e[l + 1];
          for (let i = m - 1; i >= l; i--) {
            c3 = c2; c2 = c; s2 = s;
            g = c * e[i]; h = c * p; r = Math.hypot(p, e[i]);
            e[i + 1] = s * r; s = e[i] / r; c = p / r;
            p = c * d[i] - s * g;
            d[i + 1] = h + s * (c * g + s * d[i]);
            for (let k = 0; k < n; k++) {
              const vk = V[k];
              h = vk[i + 1];
              vk[i + 1] = s * vk[i] + c * h;
              vk[i] = c * vk[i] - s * h;
            }
          }
          p = -s * s2 * c3 * el1 * e[l] / dl1;
          e[l] = s * p;
          d[l] = c * p;
        } while (Math.abs(e[l]) > eps * tst1);
      }
      d[l] += f;
      e[l] = 0;
    }
  }

  /* Principal-coordinate analysis of D (= PCA of the embedding when D is Euclidean), as chicago_model.pca:
     B = -1/2 J D^2 J; scores = V sqrt(lambda) over positive eigenvalues; k90 = fewest components reaching 90%.
     Sign convention: each component points to its largest-magnitude unit, or agrees with `align` when given. */
  function pcoa(D, n, align) {
    const A = Array.from({ length: n }, (_, i) => Float64Array.from({ length: n }, (_, j) => -0.5 * sq(D[i * n + j])));
    const r = A.map((row) => row.reduce((s, v) => s + v, 0) / n), g = r.reduce((s, v) => s + v, 0) / n;
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) A[i][j] += g - r[i] - r[j];
    const d = new Float64Array(n), e = new Float64Array(n);
    tred2(n, A, d, e);
    tql2(n, A, d, e);
    const order = Array.from(d.keys()).sort((a, b) => d[b] - d[a]);
    const top = d[order[0]], keep = order.filter((k) => d[k] > 1e-10 * top);
    const posSum = keep.reduce((s, k) => s + d[k], 0);
    const negMass = -order.filter((k) => d[k] < 0).reduce((s, k) => s + d[k], 0) / posSum;
    const scores = Array.from({ length: n }, () => new Float64Array(keep.length));
    keep.forEach((k, c) => {
      const lam = Math.sqrt(d[k]);
      let sign = 1;
      if (align && c < align[0].length) {
        let dot = 0;
        for (let i = 0; i < n; i++) dot += A[i][k] * align[i][c];
        sign = dot < 0 ? -1 : 1;
      } else {
        let best = 0;
        for (let i = 0; i < n; i++) if (Math.abs(A[i][k]) > Math.abs(best)) best = A[i][k];
        sign = best < 0 ? -1 : 1;
      }
      for (let i = 0; i < n; i++) scores[i][c] = sign * A[i][k] * lam;
    });
    const explained = keep.map((k) => d[k] / posSum);
    const cumulative = [];
    explained.reduce((s, v) => (cumulative.push(s + v), s + v), 0);
    const k90 = cumulative.findIndex((c) => c >= 0.9) + 1;
    return { scores, explained, cumulative, k90, negativeMass: negMass };
  }

  function euclidean(E, n, k) {
    const D = new Float64Array(n * n), m = k || E[0].length;
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        let s = 0;
        for (let c = 0; c < m; c++) s += sq(E[i][c] - E[j][c]);
        D[i * n + j] = D[j * n + i] = Math.sqrt(s);
      }
    }
    return D;
  }

  /* Ward agglomeration (Lance-Williams on squared Euclidean distances), as sklearn AgglomerativeClustering(ward).
     ponytail: O(n^3) closest-pair scan, fine for 173 units; use a nearest-neighbour chain if n grows past ~1,000. */
  function ward(E, n) {
    const d2 = euclidean(E, n).map(sq), size = new Float64Array(n).fill(1), alive = new Uint8Array(n).fill(1), merges = [];
    for (let step = 0; step < n - 1; step++) {
      let bi = -1, bj = -1, best = Infinity;
      for (let i = 0; i < n; i++) {
        if (!alive[i]) continue;
        for (let j = i + 1; j < n; j++) if (alive[j] && d2[i * n + j] < best) { best = d2[i * n + j]; bi = i; bj = j; }
      }
      for (let k = 0; k < n; k++) {
        if (!alive[k] || k === bi || k === bj) continue;
        const v = ((size[bi] + size[k]) * d2[bi * n + k] + (size[bj] + size[k]) * d2[bj * n + k] - size[k] * best) / (size[bi] + size[bj] + size[k]);
        d2[bi * n + k] = d2[k * n + bi] = v;
      }
      size[bi] += size[bj];
      alive[bj] = 0;
      merges.push([bi, bj, Math.sqrt(best)]);
    }
    return merges;
  }

  /* Labels after the first n - k merges; clusters numbered by their smallest member index. */
  function cut(merges, n, k) {
    const parent = Int32Array.from({ length: n }, (_, i) => i);
    const find = (i) => { while (parent[i] !== i) i = parent[i] = parent[parent[i]]; return i; };
    for (let s = 0; s < n - k; s++) parent[find(merges[s][1])] = find(merges[s][0]);
    const id = new Map(), labels = new Int32Array(n);
    for (let i = 0; i < n; i++) { const r = find(i); if (!id.has(r)) id.set(r, id.size); labels[i] = id.get(r); }
    return labels;
  }

  function silhouette(DE, n, labels) {
    const k = Math.max(...labels) + 1, size = new Float64Array(k);
    for (const l of labels) size[l]++;
    let total = 0;
    for (let i = 0; i < n; i++) {
      const sums = new Float64Array(k);
      for (let j = 0; j < n; j++) if (j !== i) sums[labels[j]] += DE[i * n + j];
      const own = labels[i];
      if (size[own] < 2) continue;
      const a = sums[own] / (size[own] - 1);
      let b = Infinity;
      for (let c = 0; c < k; c++) if (c !== own && size[c] > 0) b = Math.min(b, sums[c] / size[c]);
      total += (b - a) / Math.max(a, b);
    }
    return total / n;
  }

  /* Relabel `labels` to best match `base` (greedy on overlap) so colours stay with the same groups when settings change. */
  function alignLabels(labels, base) {
    const k = Math.max(...labels) + 1, kb = Math.max(...base) + 1, overlap = [];
    for (let a = 0; a < k; a++) for (let b = 0; b < kb; b++) {
      let c = 0;
      for (let i = 0; i < labels.length; i++) c += labels[i] === a && base[i] === b;
      overlap.push([c, a, b]);
    }
    overlap.sort((x, y) => y[0] - x[0] || x[1] - y[1] || x[2] - y[2]);
    const map = new Map(), used = new Set();
    for (const [c, a, b] of overlap) if (c > 0 && !map.has(a) && !used.has(b)) { map.set(a, b); used.add(b); }
    let next = kb;
    for (let a = 0; a < k; a++) if (!map.has(a)) { while (used.has(next)) next++; map.set(a, next); used.add(next); }
    const out = Int32Array.from(labels, (l) => map.get(l));
    const ids = [...new Set(out)].sort((x, y) => x - y);              // compact to 0..k-1, keeping matched order
    return Int32Array.from(out, (l) => ids.indexOf(l));
  }

  function clusters(E, n, kFixed, base) {
    const merges = ward(E, n), DE = euclidean(E, n), sil = {};
    for (let k = 2; k <= 8; k++) sil[k] = silhouette(DE, n, cut(merges, n, k));
    const k = kFixed || [3, 4, 5, 6, 7, 8].reduce((a, b) => (sil[b] > sil[a] ? b : a));   // notebook rule: best of 3..8
    let labels = cut(merges, n, k);
    if (base) labels = alignLabels(labels, base);
    return { k, labels, silhouette: sil, merges };
  }

  function ranks(a) {      // average ranks for ties
    const idx = Array.from(a.keys()).sort((i, j) => a[i] - a[j]), r = new Float64Array(a.length);
    for (let s = 0; s < idx.length;) {
      let e = s;
      while (e + 1 < idx.length && a[idx[e + 1]] === a[idx[s]]) e++;
      for (let t = s; t <= e; t++) r[idx[t]] = (s + e) / 2;
      s = e + 1;
    }
    return r;
  }

  function spearman(a, b) {
    const ra = ranks(a), rb = ranks(b), n = a.length;
    let ma = 0, mb = 0;
    for (let i = 0; i < n; i++) { ma += ra[i]; mb += rb[i]; }
    ma /= n; mb /= n;
    let sab = 0, saa = 0, sbb = 0;
    for (let i = 0; i < n; i++) { const x = ra[i] - ma, y = rb[i] - mb; sab += x * y; saa += x * x; sbb += y * y; }
    return sab / Math.sqrt(saa * sbb);
  }

  /* Units ordered by distance from unit i (excluding i), ties broken by index; restricted to `pool` when given. */
  function order(D, n, i, pool) {
    const ids = (pool || Array.from({ length: n }, (_, j) => j)).filter((j) => j !== i);
    const v = (j) => (D[i * n + j] === D[i * n + j] ? D[i * n + j] : Infinity);   // missing distances last
    return ids.sort((a, b) => v(a) - v(b) || a - b);
  }

  function upper(D, n) {
    const out = new Float64Array(n * (n - 1) / 2);
    let p = 0;
    for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) out[p++] = D[i * n + j];
    return out;
  }

  /* chicago_model.compare: Spearman over all pairs and mean shared top-k across units. */
  function compare(D, base, n, k = 5) {
    let overlap = 0;
    for (let i = 0; i < n; i++) {
      const a = new Set(order(D, n, i).slice(0, k));
      overlap += order(base, n, i).slice(0, k).filter((j) => a.has(j)).length / k;
    }
    return { spearmanPairs: spearman(upper(D, n), upper(base, n)), meanTopkOverlap: overlap / n };
  }

  /* Correlation of each column with each component (the notebook's loadings). cols: {name: array}. */
  function loadings(scores, cols, n, npc) {
    const out = {};
    for (const [name, x] of Object.entries(cols)) {
      out[name] = [];
      for (let c = 0; c < npc; c++) {
        const ok = [];
        for (let i = 0; i < n; i++) if (x[i] !== null && x[i] === x[i]) ok.push(i);
        const mx = ok.reduce((s, i) => s + x[i], 0) / ok.length, my = ok.reduce((s, i) => s + scores[i][c], 0) / ok.length;
        let sxy = 0, sxx = 0, syy = 0;
        for (const i of ok) { const a = x[i] - mx, b = scores[i][c] - my; sxy += a * b; sxx += a * a; syy += b * b; }
        out[name].push(sxx > 0 && syy > 0 ? sxy / Math.sqrt(sxx * syy) : 0);
      }
    }
    return out;
  }

  const api = { blockMatrices, harmonizedDistance, indexModel, pcoa, euclidean, ward, cut, silhouette, alignLabels, clusters,
                spearman, order, compare, loadings };
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.VizModel = api;
})(this);
