"""Step 3: U2 registered workplace-job density (jobs per km² of land), Chicago (LODES 2023) and São Paulo (RAIS 2022)."""
import hashlib, json
from pathlib import Path
import geopandas as gpd, numpy as np, pandas as pd, pyogrio, shapely
from harmonization.geometry import polygonal

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
D = A / "data"
OUT = A / "results/SP_CHI/u2_jobs_step3_2026_10_05"
TAB = OUT / "tables"
PREP = A / "work/prepared/Chicago/chi_functional_2026_09_16_v2"
EVID = A / "work/evidence/job_allocation_experiments"
OD = D / "SP/od2023_metro/Site_190225"
# Rules fixed before this run (MODEL_PLAN.md Step 3: S3-0..S3-7 and user decisions of 5 October 2026).
MAX_PCT, MAX_RANKS, CONC_FLAG, TOP_N, Z = 5.0, 5, 10.0, 10, 1.96
RAIS_LIKE = {1, 3}                  # OD VINC: employee with signed card, public servant
checks = {}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(2**20), b""):
            h.update(chunk)
    return h.hexdigest()


def check(name, ok, **detail):
    checks[name] = {"pass": bool(ok), **detail}


def compare(t, a, b, label):
    """Immateriality rule: every area within 5% and fewer than 5 ranks (within its city)."""
    pct = (t[b] / t[a] - 1) * 100
    move = t.groupby("city")[b].rank(ascending=False) - t.groupby("city")[a].rank(ascending=False)
    t[f"{label}_pct"], t[f"{label}_rank_move"] = pct, move
    over = t[(pct.abs() > MAX_PCT) | (move.abs() >= MAX_RANKS)]
    return over


# ---------------------------------------------------------------- Chicago

def chicago():
    pieces = gpd.read_parquet(PREP / "block_district_pieces.parquet")
    blocks = gpd.read_parquet(PREP / "blocks.parquet")
    hydro = pyogrio.read_dataframe(D / "Chicago/Hydro_20260916.geojson").to_crs(26916)
    water = shapely.union_all(hydro.geometry.map(polygonal).values)
    shapely.prepare(water)
    # Same block -> area land-share rule as U3 (S1-3, S3-3).
    block_land = pd.Series(shapely.area(shapely.difference(blocks.geometry.values, water)), index=blocks.GEOID20)
    pieces["w"] = shapely.area(shapely.difference(pieces.geometry.values, water)) / block_land.reindex(pieces.GEOID20).to_numpy()
    pieces["w"] = pieces.w.fillna(0)
    out = {}
    for year, f in [(2023, D / "Chicago/lodes_2023/il_wac_S000_JT00_2023.csv.gz"), (2022, D / "Chicago/il_wac_S000_JT00_2022.csv")]:
        wac = pd.read_csv(f, dtype={"w_geocode": str}, usecols=["w_geocode", "C000"])
        assert wac.w_geocode.is_unique
        jobs = blocks[["GEOID20"]].merge(wac, left_on="GEOID20", right_on="w_geocode", how="left").set_index("GEOID20").C000.fillna(0)
        p = pieces.assign(jobs=pieces.w * jobs.reindex(pieces.GEOID20).to_numpy())
        inside = p.groupby("unit_id").jobs.sum()
        wsum = p.groupby("GEOID20").w.sum().reindex(jobs.index, fill_value=0)
        outside = float((jobs * (1 - wsum)).sum())
        check(f"CHI_{year}_mass", np.isclose(inside.sum() + outside, jobs.sum()) and (wsum <= 1 + 1e-8).all(),
              inside=float(inside.sum()), outside=outside, block_total=float(jobs.sum()))
        out[year] = inside
        if year == 2023:
            top = jobs.nlargest(TOP_N).index
            out["2023_no_top"] = p[~p.GEOID20.isin(top)].groupby("unit_id").jobs.sum()
            missing = sorted(set(wac.loc[wac.C000 > 0, "w_geocode"]) & set(blocks.GEOID20) - set(pieces.GEOID20))
            check("CHI_2023_all_positive_city_blocks_have_pieces", not missing, missing=len(missing))
    u3 = pd.read_parquet(A / "results/Chicago/chicago_u3_step1_2026_10_02/tables/u3_step1.parquet").set_index("unit_id")
    biz = pd.read_csv(A / "results/Chicago/chi_employment_sensitivity_2026_09_22_v2/tables/district_job_sensitivity.csv")
    biz = biz[biz.scenario == "business_core"].set_index("unit_id").jobs_allocated
    t = pd.DataFrame({"unit_id": u3.index, "city": "CHI", "name": u3.district_name.to_numpy(), "land_m2": u3.land_m2.to_numpy()})
    t["jobs"] = t.unit_id.map(out[2023])
    t["jobs_2022_land_share"] = t.unit_id.map(out[2022])
    t["jobs_2022_business_land"] = t.unit_id.map(biz)
    t["jobs_without_top10"] = t.unit_id.map(out["2023_no_top"]).fillna(0)
    return t


# ---------------------------------------------------------------- São Paulo

def sao_paulo():
    units = gpd.read_parquet(A / "work/prepared/SP/sp_prep_2026_09_10_v3/N02/districts.parquet")
    r = pd.read_csv(EVID / "district_sensitivity.csv", dtype={"district_id": str}).set_index("district_id")
    rais = pd.read_csv(D / "SP/Socioeconomico/rais_empregos_sp_2022.csv", dtype={"cep": str})
    total = float(rais.empregos.sum())
    located = r.area_first.sum()
    check("SP_unplaced_jobs", np.isclose(total - located, 508844), file_total=total, placed=float(located), unplaced=float(total - located))
    alloc = pd.read_parquet(EVID / "area_first_allocations.parquet")
    by = alloc.groupby("district_id").allocated_jobs.sum()
    check("SP_cep_allocation_matches_district_table", np.allclose(by.reindex(r.index), r.area_first), max_abs_diff=float((by.reindex(r.index) - r.area_first).abs().max()))
    scale = total / located                       # S3-5: unplaced jobs spread like the placed ones
    top = rais[rais.cep != "99999999"].nlargest(TOP_N, "empregos").cep
    no_top = alloc[~alloc.cep.isin(top)].groupby("district_id").allocated_jobs.sum()
    t = pd.DataFrame({"unit_id": "SP:" + units.district_id, "city": "SP", "name": units.nm_distrito_municipal,
                      "land_m2": units.land_area_m2.to_numpy()})
    did = units.district_id.to_numpy()
    t["jobs"] = r.area_first.reindex(did).to_numpy() * scale
    t["jobs_placed_only"] = r.area_first.reindex(did).to_numpy()
    t["jobs_address_first"] = r.address_first.reindex(did).to_numpy() * scale
    t["jobs_without_top10"] = no_top.reindex(did).fillna(0).to_numpy() * scale
    check("SP_mass", np.isclose(t.jobs.sum(), total), jobs=float(t.jobs.sum()))
    return t.reset_index(drop=True), units


def od_agreement(t, units):
    """OD 2023 RAIS-comparable fixed-workplace jobs per district with an approximate sampling interval."""
    zones = gpd.read_file(OD / "002_Site Metro Mapas_190225/Shape/Zonas_2023.shp")
    zd = zones.loc[zones.NumeroMuni == 36].set_index("NumeroZona").NomeDistri
    p = pyogrio.read_dataframe(OD / "Banco2023_divulgacao_190225.dbf", read_geometry=False,
                               columns=["F_PESS", "FE_PESS", "ZONATRA1", "TRAB1_RE", "VINC1", "ZONATRA2", "TRAB2_RE", "VINC2"])
    p = p[p.F_PESS == 1]
    j = pd.concat([p[["FE_PESS", f"ZONATRA{k}", f"TRAB{k}_RE", f"VINC{k}"]].set_axis(["w", "zone", "where", "vinc"], axis=1) for k in (1, 2)])
    j = j[j.zone.isin(zd.index) & (j["where"] == 2) & j.vinc.isin(RAIS_LIKE)]
    import unicodedata
    norm = lambda s: unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper().strip()
    j["key"] = j.zone.map(zd).map(norm)
    g = j.groupby("key").agg(od=("w", "sum"), od_w2=("w", lambda w: (w ** 2).sum()), od_n=("w", "size"))
    t["key"] = t.name.map(norm)
    t = t.merge(g, left_on="key", right_index=True, how="left")
    assert t.od.notna().all()
    tot = t.od.sum()
    # ponytail: SE from sum of squared weights ignores household clustering and design effects, so it understates.
    t["od_share"], t["od_share_se"] = t.od / tot, np.sqrt(t.od_w2) / tot
    t["rais_share"] = t.jobs / t.jobs.sum()
    t["od_flag"] = (t.rais_share - t.od_share).abs() > Z * t.od_share_se
    t["rais_over_od"] = t.rais_share / t.od_share
    return t.drop(columns=["key", "od_w2"])


def main():
    TAB.mkdir(parents=True, exist_ok=True)
    c = chicago()
    s, units = sao_paulo()
    s = od_agreement(s, units)
    t = pd.concat([c, s], ignore_index=True)
    km2 = t.land_m2 / 1e6
    t["u2_jobs_land_km2"] = t.jobs / km2
    city_density = t.groupby("city").jobs.transform("sum") / t.groupby("city").land_m2.transform("sum") * 1e6
    t["u2_relative_centrality"] = t.u2_jobs_land_km2 / city_density
    for col in ("jobs_2022_land_share", "jobs_2022_business_land", "jobs_address_first", "jobs_without_top10", "jobs_placed_only"):
        t[col.replace("jobs", "u2")] = t[col] / km2
    t["rank_in_city"] = t.groupby("city").u2_jobs_land_km2.rank(ascending=False)
    check("no_missing_values", t.u2_jobs_land_km2.notna().all() and (t.u2_jobs_land_km2 >= 0).all())
    # S3-3 Chicago: land-share vs CMAP business-land allocation (2022 jobs, the year the business allocation exists).
    chi = t.city == "CHI"
    tc = t.loc[chi].copy(); over = compare(tc, "u2_2022_land_share", "u2_2022_business_land", "chi_alloc")
    t.loc[chi, ["chi_alloc_pct", "chi_alloc_rank_move"]] = tc[["chi_alloc_pct", "chi_alloc_rank_move"]].to_numpy()
    check("S3-3_CHI_allocation_immaterial", over.empty, cases=over.unit_id.tolist(),
          max_abs_pct=float(tc.chi_alloc_pct.abs().max()), max_abs_rank_move=float(tc.chi_alloc_rank_move.abs().max()))
    # S3-4 São Paulo: area_first vs address_first.
    ts = t.loc[~chi].copy(); over = compare(ts, "u2_jobs_land_km2", "u2_address_first", "sp_alloc")
    t.loc[~chi, ["sp_alloc_pct", "sp_alloc_rank_move"]] = ts[["sp_alloc_pct", "sp_alloc_rank_move"]].to_numpy()
    check("S3-4_SP_allocation_immaterial", over.empty, cases=over.unit_id.tolist(),
          max_abs_pct=float(ts.sp_alloc_pct.abs().max()), max_abs_rank_move=float(ts.sp_alloc_rank_move.abs().max()))
    # S3-6 concentration (descriptive): without the 10 largest blocks / CEPs.
    t["no_top10_pct"] = (t.u2_without_top10 / t.u2_jobs_land_km2 - 1) * 100
    checks["S3-6_concentration"] = {city: g.loc[g.no_top10_pct.abs() > CONC_FLAG, "unit_id"].tolist() for city, g in t.groupby("city")}
    # S3-5 exclusion sensitivity (SP): uniform rescaling, ranks unchanged by construction.
    checks["S3-5_SP_exclusion"] = {"level_change_pct": float((t.loc[~chi, "u2_placed_only"] / t.loc[~chi, "u2_jobs_land_km2"] - 1).mean() * 100)}
    # OD agreement test (flagged districts accepted with stated limits by user decision).
    sp = t.loc[~chi]
    checks["SP_od_agreement"] = {"flagged": sp.loc[sp.od_flag == True, "unit_id"].tolist(), "n_flagged": int(sp.od_flag.sum()),
                                 "spearman_jobs": float(sp.jobs.corr(sp.od, method="spearman")),
                                 "note": "approximate SE ignores clustering; flagged districts accepted with stated limits (user, 5 Oct 2026)"}
    checks["summary"] = {city: {"median": float(g.u2_jobs_land_km2.median()), "max": [g.loc[g.u2_jobs_land_km2.idxmax(), "name"], float(g.u2_jobs_land_km2.max())],
                                "min": [g.loc[g.u2_jobs_land_km2.idxmin(), "name"], float(g.u2_jobs_land_km2.min())], "jobs": float(g.jobs.sum())}
                         for city, g in t.groupby("city")}
    t.to_csv(TAB / "u2_jobs.csv", index=False)
    t.to_parquet(TAB / "u2_jobs.parquet", index=False)
    reg = {p.relative_to(ROOT).as_posix(): sha(p) for p in [
        D / "Chicago/lodes_2023/il_wac_S000_JT00_2023.csv.gz", D / "Chicago/il_wac_S000_JT00_2022.csv", D / "SP/Socioeconomico/rais_empregos_sp_2022.csv",
        EVID / "district_sensitivity.csv", EVID / "area_first_allocations.parquet", D / "SP/od2023_metro/Site_190225_PesquisaOD2023.zip",
        A / "results/Chicago/chi_employment_sensitivity_2026_09_22_v2/tables/district_job_sensitivity.csv",
        A / "results/Chicago/chicago_u3_step1_2026_10_02/tables/u3_step1.parquet", A / "work/prepared/SP/sp_prep_2026_09_10_v3/N02/districts.parquet"]}
    (OUT / "source_register.json").write_text(json.dumps({"inputs": reg, "documentation": "analysis/results/SP_CHI/u2_source_audit_2026_10_05/README.md"}, indent=2) + "\n")
    (OUT / "checks.json").write_text(json.dumps(checks, indent=2, default=float, ensure_ascii=False) + "\n")
    for k, v in checks.items():
        print(k, json.dumps(v, default=float, ensure_ascii=False)[:500])
    print("FAILED:", [k for k, v in checks.items() if "pass" in v and not v["pass"]] or "none")


if __name__ == "__main__":
    main()
