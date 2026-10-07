"""U6 activity composition (Step 7b). Phase B: classify São Paulo CNEFE 2022 establishments and draw the V1 audit sample.
Usage: build_u6_activity.py classify | places CITY | v2 | bridge | features [overture|cnefe] | untyped | vertical | rais_test"""
import json, re, sys, unicodedata
from pathlib import Path
import geopandas as gpd, numpy as np, pandas as pd
import evaluate_b1_step4 as b1

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "analysis"
D = A / "data"
CFG = A / "config/u6"
OUT = A / "results/SP_CHI/u6_activity_2026_10_06"
CLASSES = ["food_drink", "retail", "services_offices", "making_storing", "institutions"]
SEED, N_AUDIT = 20261006, 400
SPECIES_INSTITUTION = {"4": "institutions", "5": "institutions", "8": "institutions", "3": "making_storing"}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", s)).strip()


def cnefe_rules():
    k = pd.read_csv(CFG / "cnefe_keywords.csv").sort_values("priority")
    return [(r["class"], re.compile(r["pattern"])) for _, r in k.iterrows()]


def classify_text(text, rules):
    for cls, rx in rules:
        if rx.search(text):
            return cls
    return "unclassifiable"


def cnefe():
    xw = pd.read_csv(A / "results/SP_CHI/simple_index_source_audit_2026_10_01/tables/cnefe_district_crosswalk.csv", dtype=str)
    cn = pd.read_csv(D / "SP/Socioeconomico/CNEFE_2022/3550308_SAO_PAULO.csv", sep=";",
                     usecols=["COD_UNICO_ENDERECO", "COD_DISTRITO", "COD_ESPECIE", "DSC_ESTABELECIMENTO"], dtype=str)
    cn["unit_id"] = cn.COD_DISTRITO.map(dict(zip(xw.cod, xw.modal_unit_id)))
    return cn


def classify():
    OUT.mkdir(parents=True, exist_ok=True)
    rules = cnefe_rules()
    cn = cnefe()
    est = cn[cn.COD_ESPECIE.isin(["3", "4", "5", "6", "8"])].copy()
    est["text"] = est.DSC_ESTABELECIMENTO.fillna("").map(norm)
    est["class"] = est.COD_ESPECIE.map(SPECIES_INSTITUTION)
    six = est.COD_ESPECIE.eq("6")
    cache = {}
    est.loc[six, "class"] = [cache.setdefault(t, classify_text(t, rules)) for t in est.loc[six, "text"]]
    est[["COD_UNICO_ENDERECO", "unit_id", "COD_ESPECIE", "text", "class"]].to_parquet(OUT / "cnefe_establishments_classified.parquet", index=False)
    share = est["class"].value_counts(normalize=True).round(4).to_dict()
    res = {"establishment_records": len(est), "class_share_all_establishments": share,
           "V1_unclassifiable_share": float((est["class"] == "unclassifiable").mean()),
           "distinct_descriptions_species6": int(est.loc[six, "text"].nunique())}
    sample = est[six].sample(N_AUDIT, random_state=SEED)[["COD_UNICO_ENDERECO", "unit_id", "text", "class"]]
    sample.assign(audit_correct="", audit_note="").to_csv(OUT / "v1_audit_sample.csv", index=False)
    (OUT / "phase_b.json").write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=1))


def overture_class(tax, xw):
    """Most specific matching key (top/second level) in the Overture taxonomy crosswalk."""
    if tax is None or tax.get("hierarchy") is None or len(tax["hierarchy"]) == 0:
        return "unclassifiable"
    h = list(tax["hierarchy"])
    return xw.get("/".join(h[:2]), xw.get(h[0], "unclassifiable"))


def places(city):
    """Classify Overture places inside each unit's land (known-closed places excluded)."""
    OUT.mkdir(parents=True, exist_ok=True)
    folder, crs = ("Chicago", 26916) if city == "CHI" else ("SP", 31983)
    xw = dict(pd.read_csv(CFG / "overture_taxonomy.csv")[["key", "class"]].values)
    p = pd.concat([gpd.read_parquet(f, columns=["id", "taxonomy", "operating_status", "geometry"])
                   for f in sorted((D / f"{folder}/overture_2026_08_19/place").glob("*.parquet"))], ignore_index=True)
    closed = p.operating_status.isin(["permanently_closed", "temporarily_closed"])
    p = p[~closed].to_crs(crs)
    p["class"] = [overture_class(x, xw) for x in p.taxonomy]
    j = gpd.sjoin(p[["id", "class", "geometry"]], b1.land_units(city), predicate="within")
    j[["id", "unit_id", "class"]].to_parquet(OUT / f"overture_places_classified_{city}.parquet", index=False)
    res = {"places_in_units": len(j), "closed_excluded": int(closed.sum()), "class_share": j["class"].value_counts(normalize=True).round(4).to_dict()}
    (OUT / f"places_{city}.json").write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=1))


def v2():
    """V2: Overture food & drink and making & storing counts vs licensed sites of the same classes, per Chicago Community Area."""
    lic = pd.read_csv(D / "Chicago/business_licenses_2026_10_06/license_site_activities.csv", dtype=str).dropna(subset=["community_area"])
    lic = lic[lic.community_area.str.fullmatch(r"\d+")]
    rules = pd.read_csv(CFG / "licence_activity.csv").sort_values("priority")
    text = (lic.license_description.fillna("") + " | " + lic.business_activity.fillna(""))
    lic["class"] = "other"
    for _, r in rules[::-1].iterrows():                      # highest priority applied last, so it wins
        lic.loc[text.str.contains(r["pattern"], regex=True), "class"] = r["class"]
    lic["unit_id"] = "CHI:" + lic.community_area.astype(int).astype(str).str.zfill(2)
    lic["site"] = lic.account_number + "_" + lic.site_number
    rank = {"excluded": 0, "other": 1, "making_storing": 2, "food_drink": 3}  # a site with any food licence is food
    site = lic.assign(r=lic["class"].map(rank)).sort_values("r").drop_duplicates("site", keep="last")
    pl = pd.read_parquet(OUT / "overture_places_classified_CHI.parquet")
    res = {}
    for cls in ("food_drink", "making_storing"):
        a = pl[pl["class"] == cls].groupby("unit_id").size().rename("overture")
        b = site[site["class"] == cls].groupby("unit_id").size().rename("licence_sites")
        m = pd.concat([a, b], axis=1).fillna(0)
        rho = m.overture.corr(m.licence_sites, method="spearman")
        res[cls] = {"areas": len(m), "spearman": float(rho), "pass": bool(rho >= 0.80),
                    "overture_total": int(m.overture.sum()), "licence_sites_total": int(m.licence_sites.sum())}
    (OUT / "v2_chicago.json").write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=1))


def bridge():
    """V3 (descriptive): the Chicago instrument (Overture places) applied to São Paulo vs CNEFE, class composition by city and district."""
    c = pd.read_parquet(OUT / "cnefe_establishments_classified.parquet")
    o = pd.read_parquet(OUT / "overture_places_classified_SP.parquet")
    share = lambda d: d[d["class"].isin(CLASSES)].groupby("unit_id")["class"].value_counts(normalize=True).unstack(fill_value=0).reindex(columns=CLASSES, fill_value=0)
    sc, so = share(c), share(o)
    city = lambda d: d[d["class"].isin(CLASSES)]["class"].value_counts(normalize=True).reindex(CLASSES)
    res = {"city_share_cnefe": city(c).round(4).to_dict(), "city_share_overture": city(o).round(4).to_dict(),
           "city_ratio_overture_over_cnefe": (city(o) / city(c)).round(3).to_dict(),
           "district_spearman_by_class": {k: float(sc[k].corr(so[k].reindex(sc.index), method="spearman")) for k in CLASSES},
           "district_median_ratio_by_class": {k: float((so[k].reindex(sc.index) / sc[k]).median()) for k in CLASSES}}
    pd.concat([sc.add_prefix("cnefe_"), so.add_prefix("overture_")], axis=1).to_csv(OUT / "bridge_sp_class_shares.csv")
    (OUT / "v3_bridge.json").write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=1))


def chicago_housing_units():
    """ACS 2020-2024 housing units (B25001) by block group -> 2020 blocks by HOUSING20 share -> areas by block land share (as U3)."""
    import pyogrio, shapely
    from harmonization.geometry import polygonal
    prep = A / "work/prepared/Chicago/chi_functional_2026_09_16_v2"
    pieces = gpd.read_parquet(prep / "block_district_pieces.parquet")
    blocks = gpd.read_parquet(prep / "blocks.parquet")
    hydro = pyogrio.read_dataframe(D / "Chicago/Hydro_20260916.geojson").to_crs(26916)
    water = shapely.union_all(hydro.geometry.map(polygonal).values)
    block_land = pd.Series(shapely.area(shapely.difference(blocks.geometry.values, water)), index=blocks.GEOID20)
    w = shapely.area(shapely.difference(pieces.geometry.values, water)) / block_land.reindex(pieces.GEOID20).to_numpy()
    acs = pd.read_csv(D / "Chicago/acs_2020_2024_5yr/acsdt5y2024-b25001.dat", sep="|", dtype=str)
    acs = acs[acs.GEO_ID.str.startswith("1500000US")]
    acs = pd.Series(pd.to_numeric(acs.B25001_E001).to_numpy(), index=acs.GEO_ID.str[9:].to_numpy())
    dbf = pyogrio.read_dataframe(D / "Chicago/tl_2022_17_tabblock20/tl_2022_17_tabblock20.shp", read_geometry=False, columns=["GEOID20", "HOUSING20"])
    bg_h = dbf.groupby(dbf.GEOID20.str[:12]).HOUSING20.sum()
    hu20 = dbf.set_index("GEOID20").HOUSING20
    bg = pieces.GEOID20.str[:12]
    share = (hu20.reindex(pieces.GEOID20).to_numpy() / bg_h.reindex(bg).replace(0, np.nan).to_numpy())
    units = acs.reindex(bg).to_numpy() * np.nan_to_num(share) * np.nan_to_num(w)
    return pd.Series(units, index=pieces.unit_id.values).groupby(level=0).sum()


def features(sp_source="overture"):
    """Phase E: intensity, class shares, centred log-ratios, entropy, flags, face validity and overlaps (V4, V5).
    São Paulo establishments from Overture (D7b-3 RAIS test, 6 Oct 2026); `cnefe` rebuilds the superseded version under a suffix."""
    c = pd.read_parquet(OUT / ("cnefe_establishments_classified.parquet" if sp_source == "cnefe" else "overture_places_classified_SP.parquet"))
    sfx = "_sp_cnefe" if sp_source == "cnefe" else ""
    o = pd.read_parquet(OUT / "overture_places_classified_CHI.parquet")
    est = pd.concat([c[["unit_id", "class"]].assign(city="SP"), o[["unit_id", "class"]].assign(city="CHI")])
    n = est[est["class"].isin(CLASSES)].groupby(["unit_id", "class"]).size().unstack(fill_value=0).reindex(columns=CLASSES, fill_value=0)
    xw = pd.read_csv(A / "results/SP_CHI/simple_index_source_audit_2026_10_01/tables/cnefe_district_crosswalk.csv", dtype=str)
    cn = pd.read_csv(D / "SP/Socioeconomico/CNEFE_2022/3550308_SAO_PAULO.csv", sep=";", usecols=["COD_DISTRITO", "COD_ESPECIE"], dtype=str)
    cn["unit_id"] = cn.COD_DISTRITO.map(dict(zip(xw.cod, xw.modal_unit_id)))
    dw = pd.concat([cn[cn.COD_ESPECIE.isin(["1", "2"])].groupby("unit_id").size(), chicago_housing_units()])
    t = n.add_prefix("n_")
    t["city"] = np.where(t.index.str.startswith("CHI"), "CHI", "SP")
    t["n_classified"] = n.sum(axis=1)
    t["dwellings"] = dw.reindex(t.index)
    t["u6_intensity_per_100_dwellings"] = 100 * t.n_classified / t.dwellings
    t["u6_log_intensity"] = np.log(t.u6_intensity_per_100_dwellings)
    s = n.div(n.sum(axis=1), axis=0)
    for k in CLASSES:
        t[f"share_{k}"] = s[k]
    lg = np.log(n + 0.5)                                         # S7b-6 pseudo-count
    clr = lg.sub(lg.mean(axis=1), axis=0)
    for k in CLASSES:
        t[f"clr_{k}"] = clr[k]
        t[f"u6_clr_city_{k}"] = clr[k] - clr[k].groupby(t.city).transform("mean")   # C6: relative to own city's mean composition
    t["u6_entropy5"] = -(s * np.log(s.where(s > 0))).sum(axis=1) / np.log(5)
    t["flag_under_100_establishments"] = t.n_classified < 100
    t["dominant_relative_class"] = t[[f"u6_clr_city_{k}" for k in CLASSES]].idxmax(axis=1).str.replace("u6_clr_city_", "")
    others = {"u1": pd.read_csv(A / "results/SP_CHI/u1_step7_2026_10_06/u1_by_unit.csv").set_index("unit_id").u1_entropy4,
              "u2": pd.read_parquet(A / "results/SP_CHI/u2_jobs_step3_2026_10_05/tables/u2_jobs.parquet").set_index("unit_id").u2_jobs_land_km2,
              "u3": pd.concat([pd.read_parquet(A / "results/Chicago/chicago_u3_step1_2026_10_02/tables/u3_step1.parquet").set_index("unit_id").u3_acs_land_km2,
                               pd.read_parquet(A / "results/SP_CHI/u3_sp_catchup_2026_10_05/tables/u3_sp.parquet").set_index("unit_id").u3_land_km2])}
    res = {}
    for city, g in t.groupby("city"):
        res[city] = {"units": len(g), "flagged_under_100": g.index[g.flag_under_100_establishments].tolist(),
                     "median_intensity": float(g.u6_intensity_per_100_dwellings.median()), "median_entropy5": float(g.u6_entropy5.median()),
                     "top5_intensity": g.u6_intensity_per_100_dwellings.nlargest(5).round(1).to_dict(),
                     "bottom5_intensity": g.u6_intensity_per_100_dwellings.nsmallest(5).round(1).to_dict(),
                     "dominant_relative_class_counts": g.dominant_relative_class.value_counts().to_dict(),
                     "V5_spearman": {f"{a}_vs_{b}": float(g[a].corr(v.reindex(g.index), method="spearman"))
                                     for a in ("u6_log_intensity", "u6_entropy5") for b, v in others.items()}}
    anchors = ["SP:78", "SP:66", "SP:10", "SP:56", "SP:02", "CHI:32", "CHI:28", "CHI:72", "CHI:57"]
    res["V4_anchors"] = t.loc[anchors, ["u6_intensity_per_100_dwellings", "u6_entropy5", "dominant_relative_class"] + [f"share_{k}" for k in CLASSES]].round(3).to_dict(orient="index")
    t.to_csv(OUT / f"u6_by_unit{sfx}.csv")
    (OUT / f"phase_e{sfx}.json").write_text(json.dumps(res, indent=2, default=float) + "\n")
    print(json.dumps(res, indent=1, default=float))


def untyped():
    """Unclassifiable share by unit (both instruments) and Overture confidence of Chicago places with vs without a taxonomy."""
    c = pd.read_parquet(OUT / "cnefe_establishments_classified.parquet")
    o = pd.read_parquet(OUT / "overture_places_classified_CHI.parquet")
    conf = pd.concat([pd.read_parquet(f, columns=["id", "confidence", "sources"]) for f in sorted((D / "Chicago/overture_2026_08_19/place").glob("*.parquet"))])
    conf["provider"] = [x[0]["dataset"] if x is not None and len(x) else "none" for x in conf.sources]
    o = o.merge(conf.drop(columns="sources"), on="id")
    t = pd.read_csv(OUT / "u6_by_unit_sp_cnefe.csv").set_index("unit_id")
    res = {}
    for k, d in (("SP_cnefe", c), ("CHI_overture", o)):
        u = d["class"].eq("unclassifiable").groupby(d.unit_id).mean()
        res[k] = {"median": round(float(u.median()), 4), "p10": round(float(u.quantile(.1)), 4), "p90": round(float(u.quantile(.9)), 4),
                  "top8": u.nlargest(8).round(3).to_dict()}
        if k == "SP_cnefe":
            res["SP_spearman_unclassified_share_vs_intensity"] = round(float(u.corr(t.u6_intensity_per_100_dwellings, method="spearman")), 3)
    typed, untyped_ = o[o["class"].isin(CLASSES)], o[o["class"].eq("unclassifiable")]
    res["CHI_confidence"] = {"median_typed": round(float(typed.confidence.median()), 3), "median_untyped": round(float(untyped_.confidence.median()), 3),
                             "share_below_0.3_typed": round(float((typed.confidence < 0.3).mean()), 4),
                             "share_below_0.3_untyped": round(float((untyped_.confidence < 0.3).mean()), 4),
                             "provider_share_typed": typed.provider.value_counts(normalize=True).round(3).to_dict(),
                             "provider_share_untyped": untyped_.provider.value_counts(normalize=True).round(3).to_dict(),
                             "typed_share_below_0.3_top6_units": typed.confidence.lt(0.3).groupby(typed.unit_id).mean().nlargest(6).round(3).to_dict()}
    # Sensitivity: drop typed places with confidence < 0.3 and recompute intensity and city-centred CLR (final U6 table).
    final = pd.read_csv(OUT / "u6_by_unit.csv").set_index("unit_id")
    for city, folder in (("CHI", "Chicago"), ("SP", "SP")):
        pl = pd.read_parquet(OUT / f"overture_places_classified_{city}.parquet").merge(
            pd.concat([pd.read_parquet(f, columns=["id", "confidence"]) for f in sorted((D / f"{folder}/overture_2026_08_19/place").glob("*.parquet"))]), on="id")
        ty = pl[pl["class"].isin(CLASSES)]
        n = ty[ty.confidence >= 0.3].groupby(["unit_id", "class"]).size().unstack(fill_value=0).reindex(columns=CLASSES, fill_value=0)
        b = final[final.city == city]
        lg = np.log(n.reindex(b.index, fill_value=0) + 0.5)
        clr = lg.sub(lg.mean(axis=1), axis=0)
        clr = clr - clr.mean()
        res[f"{city}_sensitivity_confidence_0.3"] = {"spearman_intensity": round(float((n.sum(axis=1) / b.dwellings).corr(b.u6_intensity_per_100_dwellings, method="spearman")), 4),
                                                     **{f"spearman_clr_{k}": round(float(clr[k].corr(b[f"u6_clr_city_{k}"], method="spearman")), 4) for k in CLASSES},
                                                     "classified_kept": round(float(n.values.sum() / len(ty)), 4), "median_confidence": round(float(ty.confidence.median()), 3)}
    res["CHI_kenwood_untyped_name_sample"] = "inspected by hand 6 Oct 2026: mostly non-words or codes (e.g. 'Rmlhv1', 'Tqwh0727 71'); see README"
    (OUT / "unclassified_by_unit.json").write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(res, indent=1, ensure_ascii=False))


def vertical():
    """Does CNEFE list office suites or whole buildings? Records per building address (dwellings vs establishments),
    Overture-to-CNEFE count ratio and RAIS jobs per CNEFE establishment, by São Paulo district."""
    xw = pd.read_csv(A / "results/SP_CHI/simple_index_source_audit_2026_10_01/tables/cnefe_district_crosswalk.csv", dtype=str)
    cn = pd.read_csv(D / "SP/Socioeconomico/CNEFE_2022/3550308_SAO_PAULO.csv", sep=";", dtype=str,
                     usecols=["COD_DISTRITO", "COD_ESPECIE", "NOM_SEGLOGR", "NUM_ENDERECO"])
    cn["unit_id"] = cn.COD_DISTRITO.map(dict(zip(xw.cod, xw.modal_unit_id)))
    cn["bldg"] = cn.NOM_SEGLOGR + "|" + cn.NUM_ENDERECO
    per_bldg = lambda d: d.groupby("unit_id").size() / d.groupby("unit_id").bldg.nunique()
    dw, es = cn[cn.COD_ESPECIE.isin(["1", "2"])], cn[cn.COD_ESPECIE.eq("6")]
    c = pd.read_parquet(OUT / "cnefe_establishments_classified.parquet")
    o = pd.read_parquet(OUT / "overture_places_classified_SP.parquet")
    nc, no = (d[d["class"].isin(CLASSES)].groupby("unit_id").size() for d in (c, o))
    u2 = pd.read_parquet(A / "results/SP_CHI/u2_jobs_step3_2026_10_05/tables/u2_jobs.parquet").set_index("unit_id")
    t = pd.DataFrame({"name": u2.name, "dwellings_per_building": per_bldg(dw), "species6_per_building": per_bldg(es),
                      "overture_over_cnefe": no / nc, "rais_jobs_per_cnefe_establishment": u2.jobs / nc}).dropna(subset=["overture_over_cnefe"])
    t.round(3).to_csv(OUT / "cnefe_vertical_listing.csv")
    res = {"median": t.drop(columns="name").median().round(3).to_dict(),
           "spearman_overture_over_cnefe_vs_rais_jobs_per_establishment": round(float(t.overture_over_cnefe.corr(t.rais_jobs_per_cnefe_establishment, method="spearman")), 3),
           "spearman_overture_over_cnefe_vs_dwellings_per_building": round(float(t.overture_over_cnefe.corr(t.dwellings_per_building, method="spearman")), 3),
           "top8_overture_over_cnefe": t.nlargest(8, "overture_over_cnefe").round(2).to_dict(orient="index")}
    (OUT / "cnefe_vertical_listing.json").write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(res, indent=1, ensure_ascii=False))


def rais_class(code, xw):
    """Longest CNAE 2.0 prefix in the crosswalk wins."""
    for n in range(len(code), 1, -1):
        if code[:n] in xw:
            return xw[code[:n]]
    return "unclassifiable"


def rais_test():
    """D7b-3 (RT-1 to RT-5, approved 6 Oct 2026): CNEFE vs Overture model coordinates against RAIS 2022 establishments, by São Paulo district."""
    r = pd.read_parquet(D / "SP/rais_2022_estab/rais_estab_sp_2022.parquet", columns=["cnae_2", "cep", "quantidade_vinculos_ativos", "indicador_rais_negativa"])
    checks = {"non_negativa_establishments": int(r.indicador_rais_negativa.eq(0).sum()),
              "non_negativa_jobs": int(r.loc[r.indicador_rais_negativa.eq(0), "quantidade_vinculos_ativos"].sum())}
    assert checks == {"non_negativa_establishments": 314022, "non_negativa_jobs": 5390446}, checks   # city table msp_estabelec_empregos_2022.pdf
    r = r[r.quantidade_vinculos_ativos > 0].copy()                                                     # RT-1
    xw = dict(pd.read_csv(CFG / "rais_cnae.csv", dtype=str)[["prefix", "class"]].values)
    r["class"] = [rais_class(c, xw) for c in r.cnae_2.astype(str)]                                     # RT-2
    r["cep"] = r.cep.astype(str).str.zfill(8)
    al = pd.read_parquet(A / "work/evidence/job_allocation_experiments/area_first_allocations.parquet", columns=["cep", "district_id", "weight"])
    al = al[al.district_id.ne("UNLOCATED")]
    j = r.merge(al, on="cep")
    j["unit_id"] = "SP:" + j.district_id
    rais = j[j["class"].isin(CLASSES)].groupby(["unit_id", "class"]).weight.sum().unstack(fill_value=0).reindex(columns=CLASSES, fill_value=0)
    jobs = (j.weight * j.quantidade_vinculos_ativos).groupby(j.unit_id).sum()
    checks |= {"rt1_establishments": len(r), "rt1_placed_share": round(float(j.weight.sum() / len(r)), 4),
               "rt2_class_share": r["class"].value_counts(normalize=True).round(4).to_dict()}
    count = lambda d: d[d["class"].isin(CLASSES)].groupby(["unit_id", "class"]).size().unstack(fill_value=0).reindex(columns=CLASSES, fill_value=0)
    inst = {"cnefe": count(pd.read_parquet(OUT / "cnefe_establishments_classified.parquet")),
            "overture": count(pd.read_parquet(OUT / "overture_places_classified_SP.parquet")), "rais": rais}
    dw = pd.read_csv(OUT / "u6_by_unit.csv").set_index("unit_id").query("city == 'SP'").dwellings

    def coords(n):                                                                                     # RT-3: the model coordinates
        n = n.reindex(dw.index, fill_value=0)
        lg = np.log(n + 0.5)
        return pd.concat([np.log(100 * n.sum(axis=1) / dw).rename("log_intensity"), lg.sub(lg.mean(axis=1), axis=0).add_prefix("clr_")], axis=1)

    c = {k: coords(v) for k, v in inst.items()}
    rho = {k: {col: round(float(c[k][col].corr(c["rais"][col], method="spearman")), 4) for col in c["rais"]} for k in ("cnefe", "overture")}
    mean = {k: round(float(np.mean(list(v.values()))), 4) for k, v in rho.items()}
    choice = "overture" if mean["overture"] - mean["cnefe"] >= 0.05 else "cnefe"                       # RT-4
    gap = ["SP:26", "SP:45", "SP:07", "SP:35", "SP:06", "SP:62"]                                     # RT-5: where the office gap was found
    rk = {k: c[k].log_intensity.rank(ascending=False) for k in c}
    res = {"checks": checks, "RT3_spearman_with_rais": rho, "RT4_mean": mean, "RT4_difference_overture_minus_cnefe": round(mean["overture"] - mean["cnefe"], 4),
           "RT4_choice": choice,
           "RT5_raw_count_spearman_with_rais": {k: {cl: round(float(inst[k][cl].reindex(dw.index, fill_value=0).corr(rais[cl].reindex(dw.index, fill_value=0), method="spearman")), 4)
                                                   for cl in CLASSES + ["total"] if cl != "total"} | {"total": round(float(inst[k].sum(axis=1).reindex(dw.index, fill_value=0).corr(rais.sum(axis=1).reindex(dw.index, fill_value=0), method="spearman")), 4)}
                                               for k in ("cnefe", "overture")},
           "RT5_office_gap_districts_intensity_rank": {u: {k: int(rk[k][u]) for k in rk} for u in gap + ["SP:66", "SP:78", "SP:10", "SP:56"]},
           "RT5_rais_jobs_per_rais_establishment": {"median": round(float((jobs / rais.sum(axis=1)).median()), 2),
                                                    "top5": (jobs / rais.sum(axis=1)).nlargest(5).round(1).to_dict()}}
    out = pd.concat({k: v for k, v in c.items()}, axis=1)
    out.columns = [f"{a}_{b}" for a, b in out.columns]
    out.round(4).to_csv(OUT / "rais_test_by_unit.csv")
    (OUT / "rais_test.json").write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    {"classify": classify, "places": lambda: places(sys.argv[2]), "v2": v2, "bridge": bridge, "features": lambda: features(*sys.argv[2:3]), "untyped": untyped, "vertical": vertical, "rais_test": rais_test}[sys.argv[1]]()
