"""Source audit for alternatives to U1 ('what is done in each neighbourhood'): building-use tags, CMAP secondary use,
place providers, places vs official registries, and establishments per 100 dwellings. Context only; no feature is built."""
import collections, glob, json
import geopandas as gpd, numpy as np, pandas as pd, pyogrio
import evaluate_b1_step4 as b1

A, D = b1.A, b1.D
OUT = A / "results/SP_CHI/u1_alternatives_2026_10_06"
res = {}


def cnefe():
    xw = pd.read_csv(A / "results/SP_CHI/simple_index_source_audit_2026_10_01/tables/cnefe_district_crosswalk.csv", dtype=str)
    cn = pd.read_csv(D / "SP/Socioeconomico/CNEFE_2022/3550308_SAO_PAULO.csv", sep=";", usecols=["COD_DISTRITO", "COD_ESPECIE", "DSC_ESTABELECIMENTO"], dtype=str)
    cn["unit_id"] = cn.COD_DISTRITO.map(dict(zip(xw.cod, xw.modal_unit_id)))
    return cn


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # 1. Building-use tags
    b = gpd.read_parquet(D / "Chicago/overture_2026_08_19/building/part_0000.parquet", columns=["subtype", "geometry"]).to_crs(26916)
    a = b.area
    res["chicago_overture_building_area_share_with_subtype"] = float(a[b.subtype.notna()].sum() / a.sum())
    res["chicago_overture_building_subtype_area_shares"] = (a.groupby(b.subtype).sum() / a.sum()).round(4).to_dict()
    land = gpd.read_parquet(A / "work/prepared/SP/sp_prep_2026_09_10_v3/N02/district_land.parquet")
    bras = tuple(land[land.district_id == "10"].to_crs(4326).total_bounds)
    o = pyogrio.read_dataframe(D / "shared/osm_geofabrik/sudeste-latest.osm.pbf", layer="multipolygons", bbox=bras, columns=["building"])
    o = o[o.building.notna()].to_crs(31983)
    res["bras_osm_building_tag_area_share_yes"] = float(o.area[o.building.eq("yes")].sum() / o.area.sum())
    # 2. CMAP secondary use
    u = b1.land_units("CHI")
    l = pyogrio.read_dataframe(D / "Chicago/LUI_2023_view_332920193481040239.gpkg", bbox=tuple(u.to_crs(3857).total_bounds),
                               columns=["LANDUSE2", "MODIFIER"]).to_crs(26916)
    l = l[l.intersects(u.union_all())]
    has2 = l.LANDUSE2.notna() & l.LANDUSE2.astype(str).str.strip().ne("")
    res["cmap_area_share_with_secondary_use"] = float(l.area[has2].sum() / l.area.sum())
    res["cmap_multi_use_modifier_polygons"] = int(l.MODIFIER.eq("M").sum())
    # 3. Place providers
    for c in ("Chicago", "SP"):
        p = pd.concat([pd.read_parquet(x, columns=["sources"]) for x in glob.glob(str(D / f"{c}/overture_2026_08_19/place/*.parquet"))])
        cnt = collections.Counter(d for s in p.sources for d in {x["dataset"] for x in s})
        res[f"{c}_place_provider_share"] = {k: round(v / len(p), 4) for k, v in cnt.most_common(6)}
    # 4. Places vs official registries, and establishments per 100 dwellings
    comp = pd.read_csv(A / "results/SP_CHI/simple_index_ab_2026_10_01/tables/unit_components.csv").set_index("unit_id")
    s = pd.read_csv(D / "Chicago/business_licenses_2026_10_06/license_sites_by_area.csv", dtype=str).dropna(subset=["community_area"])
    s = s[s.community_area.str.fullmatch(r"\d+")]
    lic = s.groupby("CHI:" + s.community_area.astype(int).astype(str).str.zfill(2)).size()
    cn = cnefe()
    est = cn[cn.COD_ESPECIE.isin(["4", "5", "6", "8"])].groupby("unit_id").size()
    dw = cn[cn.COD_ESPECIE.isin(["1", "2"])].groupby("unit_id").size()
    for city, ref in (("CHI_vs_licence_sites", lic), ("SP_vs_cnefe_establishments", est)):
        j = pd.concat([comp.C_count, ref.rename("ref"), comp.land_km2], axis=1, join="inner")
        r = j.C_count / j.ref
        res[f"overture_commercial_places_{city}"] = {"n": len(j), "spearman_counts": float(j.C_count.corr(j.ref, method="spearman")),
                                                     "spearman_densities": float((j.C_count / j.land_km2).corr(j.ref / j.land_km2, method="spearman")),
                                                     "median_ratio": float(r.median()), "p10_p90_ratio": r.quantile([.1, .9]).round(3).tolist()}
    pieces = pd.read_parquet(A / "work/prepared/Chicago/chi_functional_2026_09_16_v2/block_district_pieces.parquet", columns=["GEOID20", "unit_id", "weight"])
    hu = pyogrio.read_dataframe(D / "Chicago/tl_2022_17_tabblock20/tl_2022_17_tabblock20.shp", read_geometry=False, columns=["GEOID20", "HOUSING20"]).set_index("GEOID20").HOUSING20
    hu = (pieces.GEOID20.map(hu) * pieces.weight).groupby(pieces.unit_id).sum()
    t = pd.concat([(100 * est / dw).rename("est_per_100_dwellings"), (100 * lic / hu).rename("licence_sites_per_100_housing_units")], axis=1)
    t.to_csv(OUT / "establishments_per_100_dwellings.csv")
    res["sp_top5_est_per_100_dw"] = t.est_per_100_dwellings.dropna().nlargest(5).round(2).to_dict()
    res["sp_selected_ranks_est_per_100_dw"] = {k: int(t.est_per_100_dwellings.rank(ascending=False)[k]) for k in ("SP:66", "SP:78", "SP:10", "SP:02")}
    res["chi_top5_licence_sites_per_100_hu"] = t.licence_sites_per_100_housing_units.dropna().nlargest(5).round(2).to_dict()
    # 5. CNEFE establishment descriptions
    e = cn[cn.COD_ESPECIE.isin(["4", "5", "6", "8"])]
    res["cnefe_species_counts"] = cn.COD_ESPECIE.value_counts().sort_index().to_dict()
    res["cnefe_establishments_with_description"] = float(e.DSC_ESTABELECIMENTO.notna().mean())
    res["cnefe_other_purpose_top_first_words"] = e[e.COD_ESPECIE.eq("6")].DSC_ESTABELECIMENTO.dropna().str.upper().str.split().str[0].value_counts().head(25).to_dict()
    (OUT / "audit.json").write_text(json.dumps(res, indent=2, default=float, ensure_ascii=False) + "\n")
    print(json.dumps(res, indent=1, default=float, ensure_ascii=False))


if __name__ == "__main__":
    main()
