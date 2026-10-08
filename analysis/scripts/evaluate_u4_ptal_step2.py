"""Step 2: U4 PTAL Access Index (TfL 2015 method) for Chicago Community Areas and São Paulo districts."""
import datetime as dt, hashlib, json, math
from pathlib import Path
import geopandas as gpd, numpy as np, pandas as pd, pyogrio, shapely
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree
from harmonization.functional import active_services, seconds
from harmonization.geometry import polygonal
from harmonization.ptal import MAX_WALK_M, edf, mode_ai

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
D = A / "data"
OUT = A / "results/SP_CHI/u4_ptal_step2_2026_10_05"
TAB = OUT / "tables"
# Decisions S2-7 to S2-13, fixed by the user on 5 October 2026 before this script ran (docs/chicago/MODEL_PLAN.md).
DATE = dt.date(2026, 10, 14)                       # a Wednesday inside the CTA, Metra and SPTrans calendars
WIN = (8 * 3600 + 15 * 60, 9 * 3600 + 15 * 60)    # 08:15-09:15, so departures in the window are per hour
GRID = 100
NO_WALK = {"motorway", "trunk"}
NOT_STREET = {"footway", "path", "steps", "cycleway"}   # removed in the U4-2 streets-only sensitivity
MODES = ("bus", "metro", "rail")
BANDS = [0, 2.5, 5, 10, 15, 20, 25, 40]           # PTAL 1a..6b lower edges; AI = 0 is PTAL 0
BAND_NAMES = ["1a", "1b", "2", "3", "4", "5", "6a", "6b"]
MAX_PCT, MAX_RANKS, ZERO_FLAG = 10.0, 5, 0.10
CITIES = {
    "CHI": dict(crs=26916, overture=D / "Chicago/overture_2026_08_19",
                feeds=[(D / "Chicago/google_transit", {"3": "bus", "1": "metro"}),
                       (D / "Chicago/metra_gtfs_2026_10_05", {"2": "rail"})]),
    "SP": dict(crs=31983, overture=D / "SP/overture_2026_08_19",
               feeds=[(D / "SP/Socioeconomico/f-6gy-sptrans-latest", {"3": "bus", "1": "metro", "2": "rail"})]),
}
checks = {}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(2**20), b""):
            h.update(chunk)
    return h.hexdigest()


def check(name, ok, **detail):
    checks[name] = {"pass": bool(ok), **detail}


def gtfs(path, name, **kw):
    f = path / f"{name}.txt"
    if not f.exists():
        return None
    return pd.read_csv(f, dtype=str, skipinitialspace=True, keep_default_na=False, **kw).rename(columns=str.strip)


# ---------------------------------------------------------------- units and residents

def chicago_units_and_people():
    """Block-piece land polygons carrying the U3 ACS 2020-2024 allocation (S1-3, S1-7a)."""
    prep = A / "work/prepared/Chicago/chi_functional_2026_09_16_v2"
    units = gpd.read_parquet(A / "work/prepared/Chicago/chi_local_2026_09_16_v1/districts.parquet")
    units = units.rename(columns={"district_name": "name"})[["unit_id", "name", "geometry"]]
    pieces = gpd.read_parquet(prep / "block_district_pieces.parquet")
    blocks = gpd.read_parquet(prep / "blocks.parquet")
    hydro = pyogrio.read_dataframe(D / "Chicago/Hydro_20260916.geojson").to_crs(26916)
    water = shapely.union_all(hydro.geometry.map(polygonal).values)
    shapely.prepare(water)
    pieces["geometry"] = shapely.difference(pieces.geometry.values, water)
    block_land = pd.Series(shapely.area(shapely.difference(blocks.geometry.values, water)), index=blocks.GEOID20)
    pieces["weight_b"] = pieces.geometry.area / block_land.reindex(pieces.GEOID20).to_numpy()
    acs = pd.read_csv(D / "Chicago/acs_2020_2024_5yr/acsdt5y2024-b01003.dat", sep="|", dtype=str)
    acs = acs[acs.GEO_ID.str.startswith("1500000US")]
    acs = pd.Series(pd.to_numeric(acs.B01003_E001).to_numpy(), index=acs.GEO_ID.str[9:].to_numpy())
    dbf = pyogrio.read_dataframe(D / "Chicago/tl_2022_17_tabblock20/tl_2022_17_tabblock20.shp", read_geometry=False, columns=["GEOID20", "POP20"])
    bg_pop20 = dbf.groupby(dbf.GEOID20.str[:12]).POP20.sum()
    bg = pieces.GEOID20.str[:12]
    share = (pieces.POP20 / bg_pop20.reindex(bg).replace(0, np.nan).to_numpy()).fillna(0)
    pieces["residents"] = acs.reindex(bg).to_numpy() * share * pieces.weight_b
    u3 = pd.read_parquet(A / "results/Chicago/chicago_u3_step1_2026_10_02/tables/u3_step1.parquet").set_index("unit_id")
    got = pieces.groupby("unit_id").residents.sum().reindex(u3.index)
    check("CHI_residents_equal_U3", np.allclose(got, u3.acs_residents_a, rtol=1e-9), max_abs_diff=float((got - u3.acs_residents_a).abs().max()))
    return units, pieces.loc[pieces.residents > 0, ["unit_id", "residents", "geometry"]]


def sp_units_and_people():
    """São Paulo districts and Census 2022 tract population (GeoSampa)."""
    units = gpd.read_parquet(A / "work/prepared/SP/sp_prep_2026_09_10_v3/N02/districts.parquet")
    units = units.assign(unit_id="SP:" + units.district_id, name=units.nm_distrito_municipal)[["unit_id", "name", "geometry"]]
    tracts = pyogrio.read_dataframe(D / "SP/Socioeconomico/densidade_demografica.gpkg", columns=["cd_original_setor_censitario", "qt_populacao"])
    tracts = tracts.to_crs(31983)
    tracts["geometry"] = tracts.geometry.map(polygonal)
    tracts["qt_populacao"] = tracts.qt_populacao.fillna(0)
    tracts["tract_area"] = tracts.area
    total = float(tracts.qt_populacao.sum())
    # Tracts nest in districts in principle; the overlay assigns any boundary sliver to the district it lies in.
    parts = gpd.overlay(tracts, units[["unit_id", "geometry"]], how="intersection", keep_geom_type=True)
    parts["residents"] = parts.qt_populacao * parts.area / parts.tract_area
    check("SP_residents_conserved", math.isclose(parts.residents.sum(), total, rel_tol=1e-4),
          census_2022_total=total, assigned=float(parts.residents.sum()))
    return units, parts.loc[parts.residents > 0, ["unit_id", "residents", "geometry"]]


def grid_points(polys):
    """100 m cells cut by population polygons; residents shared by area; one representative point per part."""
    x0, y0, x1, y1 = polys.total_bounds
    xs, ys = np.meshgrid(np.arange(math.floor(x0 / GRID) * GRID, x1, GRID), np.arange(math.floor(y0 / GRID) * GRID, y1, GRID))
    cells = shapely.box(xs.ravel(), ys.ravel(), xs.ravel() + GRID, ys.ravel() + GRID)
    c, p = polys.sindex.query(cells, predicate="intersects")
    parts = shapely.intersection(cells[c], polys.geometry.values[p])
    area = shapely.area(parts)
    keep = area > 0
    poly_area = polys.geometry.area.to_numpy()
    pts = gpd.GeoDataFrame({"unit_id": polys.unit_id.to_numpy()[p[keep]],
                            "weight": polys.residents.to_numpy()[p[keep]] * area[keep] / poly_area[p[keep]],
                            "part_area": area[keep]},
                           geometry=shapely.point_on_surface(parts[keep]), crs=polys.crs)
    ok = np.allclose(pts.groupby("unit_id").weight.sum().reindex(polys.unit_id.unique()),
                     polys.groupby("unit_id").residents.sum().reindex(polys.unit_id.unique()), rtol=1e-9)
    return pts.reset_index(drop=True), ok


# ---------------------------------------------------------------- service

def departures(path, modes, city):
    """Departures per route, direction and stop in 08:15-09:15 on DATE (exact timetables or headway records)."""
    cal, exc = gtfs(path, "calendar"), gtfs(path, "calendar_dates")
    if exc is None:
        exc = pd.DataFrame(columns=["service_id", "date", "exception_type"])
    active = active_services(cal, exc, DATE)
    routes = gtfs(path, "routes")
    routes = routes[routes.route_type.isin(modes)].assign(mode=lambda r: r.route_type.map(modes))
    trips = gtfs(path, "trips")
    trips = trips[trips.service_id.isin(active) & trips.route_id.isin(routes.route_id)].copy()
    trips["direction_id"] = trips.get("direction_id", pd.Series("0", index=trips.index)).replace("", "0")
    trips = trips.merge(routes[["route_id", "mode"]], on="route_id")
    stops = gtfs(path, "stops")
    stops = gpd.GeoDataFrame(stops[["stop_id"]], geometry=gpd.points_from_xy(pd.to_numeric(stops.stop_lon), pd.to_numeric(stops.stop_lat)), crs=4326)
    want = set(trips.trip_id)
    parts = []
    reader = pd.read_csv(path / "stop_times.txt", dtype=str, skipinitialspace=True, keep_default_na=False, chunksize=2_000_000,
                         usecols=lambda c: c.strip() in {"trip_id", "stop_id", "departure_time", "pickup_type"})
    for chunk in reader:
        chunk = chunk.rename(columns=str.strip)
        parts.append(chunk[chunk.trip_id.isin(want)])
    st = pd.concat(parts, ignore_index=True)
    st["sec"] = seconds(st.departure_time)
    st["off"] = st.sec - st.groupby("trip_id").sec.transform("min")   # used by headway feeds only
    if "pickup_type" not in st:
        st["pickup_type"] = ""
    st = st.merge(trips[["trip_id", "route_id", "direction_id", "mode"]], on="trip_id")
    # TfL: rail services count only if they stop at least twice in the city.
    stops_in_city = set(stops.loc[stops.to_crs(city.crs).within(city.union_all()), "stop_id"])
    in_city = st[st.stop_id.isin(stops_in_city)].groupby("trip_id").stop_id.nunique()
    rail_ok = ~(st["mode"].eq("rail") & ~st.trip_id.map(in_city).fillna(0).ge(2))
    st = st[rail_ok & st.pickup_type.ne("1")]
    fq = gtfs(path, "frequencies")
    if fq is None or fq.empty:
        assert st.sec.max() < 86400 + WIN[0], "previous-day trips could reach the window"
        hit = st[(st.sec >= WIN[0]) & (st.sec < WIN[1])]
        dep = hit.groupby(["mode", "route_id", "direction_id", "stop_id"]).size().rename("per_hour").reset_index()
        check(f"U4-1_timetable_count_{path.name}", duck_window_count(path, set(st.trip_id)) == len(hit), departures=len(hit))
    else:
        assert set(st.trip_id) <= set(fq.trip_id), "mixed timetable and headway trips are not handled"
        f = fq.assign(start=seconds(fq.start_time), end=seconds(fq.end_time), h=pd.to_numeric(fq.headway_secs))
        m = st.merge(f[["trip_id", "start", "end", "h"]], on="trip_id")
        # Vehicles leave the first stop at start + k*h for start + k*h < end; count k reaching this stop in the window.
        lo = np.maximum(0, np.ceil((WIN[0] - m.off - m.start) / m.h))
        hi = np.minimum(np.ceil((WIN[1] - m.off - m.start) / m.h) - 1, np.ceil((m.end - m.start) / m.h) - 1)
        m["n"] = np.maximum(0, hi - lo + 1)
        dep = m.groupby(["mode", "route_id", "direction_id", "stop_id"]).n.sum().rename("per_hour").reset_index()
        dep = dep[dep.per_hour > 0]
        sample = m.drop_duplicates("trip_id").trip_id.sample(min(25, m.trip_id.nunique()), random_state=20261005)
        slow = 0
        for t in sample:
            for r in m[m.trip_id.eq(t)].itertuples():
                k, n = 0, 0
                while r.start + k * r.h < r.end:
                    n += WIN[0] <= r.start + k * r.h + r.off < WIN[1]
                    k += 1
                slow += abs(n - r.n)
        check(f"headway_expansion_{path.name}", slow == 0, sampled_trips=len(sample), mismatches=int(slow))
    dep = dep.merge(stops, on="stop_id")
    return gpd.GeoDataFrame(dep, geometry="geometry", crs=4326).to_crs(city.crs), active


def duck_window_count(path, trip_ids):
    """Independent count of raw stop_times rows in the window for the given trips (pickup_type 1 excluded)."""
    import duckdb
    con = duckdb.connect()
    con.register("ok", pd.DataFrame({"trip_id": sorted(trip_ids)}))
    f = str(path / "stop_times.txt")
    cols = {c.strip(): c for c in con.read_csv(f, all_varchar=True).columns}
    q = lambda c: f'trim(s."{cols[c]}")'
    sec = " + ".join(f"cast(split_part({q('departure_time')}, ':', {i + 1}) AS BIGINT) * {m}" for i, m in enumerate((3600, 60, 1)))
    sql = (f"SELECT count(*) FROM read_csv('{f}', all_varchar=true) s JOIN ok ON {q('trip_id')} = ok.trip_id "
           f"WHERE coalesce({q('pickup_type')}, '') <> '1' AND ({sec}) >= {WIN[0]} AND ({sec}) < {WIN[1]}")
    return con.execute(sql).fetchone()[0]


# ---------------------------------------------------------------- walking network

def walk_graph(overture, crs, area, exclude):
    seg = gpd.read_parquet(next((overture / "segment").glob("*.parquet")), columns=["subtype", "class", "connectors", "geometry"])
    seg = seg[seg.subtype.eq("road") & ~seg["class"].isin(exclude)].to_crs(crs)
    seg = seg[seg.intersects(area)].reset_index(drop=True)
    e = seg[["connectors"]].assign(length=seg.length).explode("connectors").dropna()
    e = pd.DataFrame({"seg": e.index, "length": e.length.to_numpy(),
                      "cid": [c["connector_id"] for c in e.connectors], "at": [c["at"] for c in e.connectors]})
    # Node position from the segment itself: 0.5% of connectors lie outside the downloaded connector file's extent.
    e["geometry"] = shapely.line_interpolate_point(seg.geometry.values[e.seg.to_numpy()], e["at"].to_numpy(), normalized=True)
    e = e.sort_values(["seg", "at"])
    nxt = e.drop(columns="geometry").groupby("seg").shift(-1)
    edges = pd.DataFrame({"a": e.cid, "b": nxt.cid, "w": (nxt["at"] - e["at"]) * e.length}).dropna()
    con = e.drop_duplicates("cid").reset_index(drop=True)
    idx = pd.Series(con.index, index=con.cid)
    a, b = idx.reindex(edges.a).to_numpy(), idx.reindex(edges.b).to_numpy()
    w = np.maximum(edges.w.to_numpy(), 1e-3)                # zero-length links would vanish from a sparse matrix
    g = pd.DataFrame({"a": np.minimum(a, b).astype(int), "b": np.maximum(a, b).astype(int), "w": w}).query("a != b").groupby(["a", "b"]).w.min().reset_index()
    n = len(con)
    G = coo_matrix((g.w, (g.a, g.b)), shape=(n, n)).tocsr()
    _, comp = connected_components(G, directed=False)
    main = comp == np.bincount(comp).argmax()
    xy = np.c_[shapely.get_x(con.geometry.values), shapely.get_y(con.geometry.values)]
    return G, xy, np.flatnonzero(main), {"segments": len(seg), "nodes": n, "edges": len(g), "main_component_share": float(main.mean())}


# ---------------------------------------------------------------- access index

def access_index(points_xy, dep, net=None):
    """Point AI per mode. net=(G, xy, main) for network walking; None for straight-line distance."""
    n = len(points_xy)
    msum = {m: np.zeros(n) for m in MODES}
    mmax = {m: np.zeros(n) for m in MODES}
    if net:
        G, xy, main = net
        tree = cKDTree(xy[main])
        psnap, i = tree.query(points_xy)
        pnode = main[i]
        ssnap, j = tree.query(np.c_[dep.geometry.x, dep.geometry.y])
        dep = dep.assign(node=main[j], snap_m=ssnap)
    else:
        ptree = cKDTree(points_xy)
    for (mode, route), rdep in dep.groupby(["mode", "route_id"]):
        best = np.zeros(n)                                  # most frequent direction: max EDF over directions
        for _, d in rdep.groupby("direction_id"):
            if net:
                # Per node keep the stop with the highest frequency; walking starts at its snap distance.
                d = d.sort_values("per_hour", ascending=False).drop_duplicates("node")
                dist, _, src = dijkstra(G, directed=False, indices=d.node.to_numpy(), limit=MAX_WALK_M[mode], min_only=True, return_predecessors=True)
                f = np.zeros(len(xy)); f[d.node.to_numpy()] = d.per_hour.to_numpy()
                s = np.zeros(len(xy)); s[d.node.to_numpy()] = d.snap_m.to_numpy()
                reach = src[pnode] >= 0
                walk = np.full(n, np.inf)
                walk[reach] = dist[pnode[reach]] + psnap[reach] + s[src[pnode[reach]]]
                per_hour = np.where(reach, f[np.maximum(src[pnode], 0)], 0)
            else:
                walk, per_hour = np.full(n, np.inf), np.zeros(n)
                sxy = np.c_[d.geometry.x, d.geometry.y]
                for k, near in enumerate(ptree.query_ball_point(sxy, r=MAX_WALK_M[mode])):
                    near = np.asarray(near, dtype=int)
                    dd = np.hypot(*(points_xy[near] - sxy[k]).T)
                    better = dd < walk[near]                # nearest stop of the route-direction wins
                    walk[near[better]] = dd[better]
                    per_hour[near[better]] = d.per_hour.to_numpy()[k]
            ok = walk <= MAX_WALK_M[mode]
            e = np.zeros(n)
            e[ok] = edf(walk[ok], per_hour[ok], mode)
            best = np.maximum(best, e)
        msum[mode] += best
        mmax[mode] = np.maximum(mmax[mode], best)
    ai = {m: mmax[m] + 0.5 * (msum[m] - mmax[m]) for m in MODES}
    ai["total"] = sum(ai[m] for m in MODES)
    return ai


def summarise(pts, ai, units, prefix):
    w = pts.weight.to_numpy()
    df = pd.DataFrame({"unit_id": pts.unit_id, "w": w, "a": pts.part_area, **{k: v for k, v in ai.items()}})
    g = df.groupby("unit_id")
    out = pd.DataFrame(index=units.unit_id)
    wmean = lambda col: (df[col] * df.w).groupby(df.unit_id).sum() / g.w.sum()
    out[prefix] = wmean("total")
    if prefix == "u4_ptai_avg_resident":
        for m in MODES:
            out[f"ai_{m}"] = wmean(m)
        out["share_ai_zero"] = (df.w * (df.total == 0)).groupby(df.unit_id).sum() / g.w.sum()
        band = np.digitize(df.total, BANDS, right=True)     # 0 -> PTAL 0, then 1a..6b
        for k, name in enumerate(["0"] + BAND_NAMES):
            out[f"share_ptal_{name}"] = (df.w * (band == k)).groupby(df.unit_id).sum() / g.w.sum()
        out["ai_unweighted_populated"] = (df.total * df.a).groupby(df.unit_id).sum() / g.a.sum()
        out["residents"] = g.w.sum()
        out["points"] = g.size()
    return out


# ---------------------------------------------------------------- main

def main():
    TAB.mkdir(parents=True, exist_ok=True)
    rows = [("bus", 200, 3), ("bus", 200, 10), ("bus", 200, 7), ("bus", 400, 3), ("bus", 400, 4), ("bus", 400, 7),
            ("metro", 746, 8), ("metro", 746, 8), ("rail", 900, 3), ("rail", 900, 2)]
    tfl = sum(mode_ai([edf(d, f, m) for mm, d, f in rows if mm == m]) for m in MODES)
    check("U4-1_tfl_figure_2_15", round(tfl, 2) == 15.16, computed=tfl, published=15.16)
    results, register = [], {}
    for city, cfg in CITIES.items():
        print("==", city, flush=True)
        units, polys = chicago_units_and_people() if city == "CHI" else sp_units_and_people()
        units = units.to_crs(cfg["crs"])
        polys = polys.to_crs(cfg["crs"])
        pts, ok = grid_points(polys)
        check(f"U4-1_{city}_grid_conserves_residents", ok, points=len(pts), residents=float(pts.weight.sum()))
        area = units.union_all().buffer(2000)
        dep = []
        for path, modes in cfg["feeds"]:
            d, active = departures(path, modes, units)
            dep.append(d)
            register[f"{city}:{path.name}"] = {"active_services": sorted(active), "files": {
                p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(path.glob("*.txt")) + sorted(path.glob("*.zip"))}}
        dep = pd.concat(dep, ignore_index=True)
        dep = dep[dep.within(area)]
        checks[f"{city}_service"] = {m: {"routes": int(dep[dep["mode"] == m].route_id.nunique()),
                                         "stop_route_directions": int((dep["mode"] == m).sum()),
                                         "departures_per_hour": float(dep.loc[dep["mode"] == m, "per_hour"].sum())} for m in MODES}
        xy = np.c_[pts.geometry.x, pts.geometry.y]
        out = {}
        for label, exclude in [("u4_ptai_avg_resident", NO_WALK), ("u4_streets_only", NO_WALK | NOT_STREET)]:
            G, nxy, main, info = walk_graph(cfg["overture"], cfg["crs"], area, exclude)
            far = cKDTree(nxy[main]).query(np.c_[dep.geometry.x, dep.geometry.y])[0] > 100
            checks[f"{city}_{label}_network"] = {**info, "stop_rows_over_100m_from_network": float(far.mean())}
            ai = access_index(xy, dep, (G, nxy, main))
            assert np.allclose(ai["total"], sum(ai[m] for m in MODES)) and (ai["total"] >= 0).all()
            out[label] = summarise(pts, ai, units, label)
            print(city, label, flush=True)
        out["straight"] = summarise(pts, access_index(xy, dep), units, "u4_straight_line")
        t = pd.concat(out.values(), axis=1).reset_index()
        t.insert(1, "city", city)
        t.insert(2, "name", units.set_index("unit_id").name.reindex(t.unit_id).to_numpy())
        results.append(t)
    t = pd.concat(results, ignore_index=True)
    check("U4-1_no_missing_values", t.u4_ptai_avg_resident.notna().all(), missing=t.loc[t.u4_ptai_avg_resident.isna(), "unit_id"].tolist())

    rk = lambda c: t.groupby("city")[c].rank(ascending=False)
    t["rank_in_city"] = rk("u4_ptai_avg_resident")
    for alt in ("u4_streets_only", "u4_straight_line"):
        t[f"{alt}_pct"] = np.where(t.u4_ptai_avg_resident > 0, (t[alt] / t.u4_ptai_avg_resident - 1) * 100, 0.0)
        t[f"{alt}_rank_move"] = rk(alt) - t.rank_in_city
    for city, g in t.groupby("city"):
        over = g[(g.u4_streets_only_pct.abs() > MAX_PCT) | (g.u4_streets_only_rank_move.abs() >= MAX_RANKS)]
        check(f"U4-2_{city}_footways_immaterial", over.empty, max_abs_pct=float(g.u4_streets_only_pct.abs().max()),
              max_abs_rank_move=float(g.u4_streets_only_rank_move.abs().max()), cases=over.unit_id.tolist(),
              spearman=float(g.u4_ptai_avg_resident.corr(g.u4_streets_only, method="spearman")))
        checks[f"U4-3_{city}_straight_line"] = {"spearman": float(g.u4_ptai_avg_resident.corr(g.u4_straight_line, method="spearman")),
                                                "median_pct": float(g.u4_straight_line_pct.median()),
                                                "areas_moving_5_or_more_ranks": int((g.u4_straight_line_rank_move.abs() >= 5).sum())}
        mode_share = {m: float((g[f"ai_{m}"] * g.residents).sum() / (g.u4_ptai_avg_resident * g.residents).sum()) for m in MODES}
        checks[f"U4-4_{city}_descriptive"] = {"resident_weighted_mode_share_of_ai": mode_share,
                                              "areas_over_10pct_residents_ai_zero": g.loc[g.share_ai_zero > ZERO_FLAG, "unit_id"].tolist()}
    old = pd.read_parquet(A / "results/Chicago/chi_functional_2026_09_16_v2/tables/bus_service_access.parquet")
    old = old[(old.window == "weekday_am") & (old.radius_m == 400)].set_index("unit_id").expected_departures_per_resident
    t["chi_bus_only_u4_old"] = t.unit_id.map(old)
    c = t[t.city == "CHI"]
    checks["U4-4_CHI_descriptive"]["spearman_vs_bus_only_u4"] = float(c.u4_ptai_avg_resident.corr(c.chi_bus_only_u4_old, method="spearman"))

    t.to_csv(TAB / "u4_ptal.csv", index=False)
    t.to_parquet(TAB / "u4_ptal.parquet", index=False)
    register["method"] = {"source": "Transport for London, Connectivity Assessment Guide (2015), section 2, tables 2.1-2.2, figure 2.15",
                          "files": {p.relative_to(ROOT).as_posix(): sha(p) for p in [D / "shared/ptal_method/tfl_connectivity_assessment_guide_2015.pdf"]}}
    register["inputs"] = {p.relative_to(ROOT).as_posix(): sha(p) for p in [
        D / "SP/Socioeconomico/densidade_demografica.gpkg", A / "results/Chicago/chicago_u3_step1_2026_10_02/tables/u3_step1.parquet",
        next((D / "Chicago/overture_2026_08_19/segment").glob("*.parquet")), next((D / "SP/overture_2026_08_19/segment").glob("*.parquet"))]}
    (OUT / "source_register.json").write_text(json.dumps(register, indent=2) + "\n")
    (OUT / "checks.json").write_text(json.dumps(checks, indent=2, default=float) + "\n")
    for k, v in checks.items():
        print(k, json.dumps(v, default=float)[:400])
    print("FAILED:", [k for k, v in checks.items() if "pass" in v and not v["pass"]] or "none")


if __name__ == "__main__":
    main()
