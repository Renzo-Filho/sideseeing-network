"""Export the inputs of the Cross-City Urban Explorer to viz/data.js.

The page recomputes every model in the browser, so this script exports model *inputs*, never fitted results:
- Cross-City Urban Index A and B: the raw and min-max scaled factors of protocol P-AB-1 (index_A_B.csv).
- Harmonized cross-city similarity model (sp_chicago_model_v1): for each C6 scaling, every distance block as the
  model sees it (scaled columns or log-ratios) and its calibration, built by the model's own functions
  (sp_chicago_model.py / chicago_model.py), so no model rule is re-implemented here.
- Simplified unit polygons in each city's projected CRS (decametres), unit names, and the published test tables
  that the documentation pages quote.
analysis/tests/check_viz_model.js asserts that the page's computations reproduce the published results.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import sp_chicago_model as xm
import chicago_model as cm

A = xm.A
AB = A / "results/SP_CHI/simple_index_ab_2026_10_01/tables"
XR = xm.OUT / "tables"
OUT = A.parent / "viz/data.js"
SIMPLIFY_M = 20                                        # polygon simplification tolerance (metres)
NAME_FIX = {"Capao Redondo": "Capão Redondo", "Carrao": "Carrão", "Cidade Lider": "Cidade Líder", "Freguesia Do O": "Freguesia do Ó",
            "Jardim Angela": "Jardim Ângela", "Jose Bonifacio": "José Bonifácio", "Sacoma": "Sacomã", "Santa Cecilia": "Santa Cecília",
            "Tremembe": "Tremembé", "Vila Curuca": "Vila Curuçá", "Vila Jacui": "Vila Jacuí", "Alto De Pinheiros": "Alto de Pinheiros",
            "Parque Do Carmo": "Parque do Carmo"}

FAMILIES = {   # id: (name, domain, what it measures)
    "M1": ("Street density", "Street morphology", "Street length in ten road classes per km² of land."),
    "M3": ("Block size", "Street morphology", "Size of the street block in which a typical m² of land sits (area-weighted median of the faces enclosed by the streets)."),
    "M4": ("Block shape", "Street morphology", "Area-weighted median compactness (4πA/P²) and elongation (longest ÷ shortest side) of those blocks."),
    "M6": ("Street hierarchy", "Street morphology", "Share of street length in motorway, trunk, primary and secondary roads."),
    "M7": ("Parcel density", "Street morphology", "Ground parcels per km² of land; a condominium counts once in both cities."),
    "B1": ("Footprint coverage", "Built form", "Union of building footprints divided by land area."),
    "BV": ("Vertical form", "Built form", "Built-surface-weighted building height."),
    "U2": ("Job density", "Use and activity", "Registered jobs per km² of land."),
    "U3": ("Resident density", "Use and activity", "Residents per km² of land."),
    "U4": ("Transit access", "Use and activity", "PTAL Access Index (TfL method) for bus and rail, averaged over residents."),
    "U6": ("Activity composition", "Use and activity", "Establishments per 100 dwellings (intensity) and their mix across five activity classes (composition)."),
    "U1": ("Land-use shares", "Use and activity", "Residential, industrial and institutional shares of classified occupied land."),
}
SOURCES = {    # family: (Chicago source, São Paulo source, same instrument?)
    "M1": ("Overture streets 2026-08-19", "Overture streets 2026-08-19", True),
    "M3": ("Overture street faces", "Overture street faces", True),
    "M4": ("Overture street faces", "Overture street faces", True),
    "M6": ("Overture streets", "Overture streets", True),
    "M7": ("Cook County 2024 ground parcels", "GeoSampa fiscal lots", True),
    "B1": ("Overture buildings", "Overture buildings", True),
    "BV": ("GHSL R2023A (2018)", "GHSL R2023A (2018)", False),
    "U2": ("LODES 2023", "RAIS 2022", False),
    "U3": ("ACS 2020–2024", "Census 2022", True),
    "U4": ("PTAL: CTA bus, 'L', Metra", "PTAL: SPTrans bus, Metrô, CPTM", False),
    "U6": ("Overture places + ACS dwellings", "Overture places + CNEFE dwellings", False),
    "U1": ("CMAP Land Use Inventory 2023 (observed)", "IPTU 2026 (declared)", False),
}
COLUMNS = {    # column: (short label, unit, how to read a high value)
    "m1_km_per_km2": ("Street density", "km/km²", "more street length per km² of land: a finer, denser network"),
    "ov_m3_wmedian_ln_m2": ("Block size", "ln m²", "larger blocks: a coarser grain (industrial land, rail yards, airports read as huge blocks)"),
    "ov_m4_wmedian_compactness": ("Block compactness", "4πA/P²", "blocks closer to a square or circle"),
    "ov_m4_wmedian_elongation": ("Block elongation", "ratio", "longer, thinner blocks"),
    "m6_major_share": ("Major-road share", "share", "more of the network is arterial (motorway to secondary)"),
    "m7_parcels_per_km2": ("Parcel density", "parcels/km²", "more, smaller ground parcels: a finer property grain"),
    "B1_coverage_land": ("Footprint coverage", "share", "more of the land is covered by buildings"),
    "bv_height_built_m": ("Built height", "m", "taller buildings on the built surface"),
    "u2_jobs_land_km2": ("Job density", "jobs/km²", "more registered jobs per km² of land"),
    "u3_acs_land_km2": ("Resident density", "residents/km²", "more residents per km² of land"),
    "u4_ptai_avg_resident": ("Transit access", "PTAL AI", "more frequent, nearer bus and rail service for residents"),
    "u6_log_intensity": ("Activity intensity", "ln per 100 dwellings", "more establishments per dwelling: a busier, more commercial place"),
    "u6_clr_city_food_drink": ("Mix: food & drink", "clr", "relatively more food and drink places"),
    "u6_clr_city_retail": ("Mix: retail", "clr", "relatively more retail"),
    "u6_clr_city_services_offices": ("Mix: services & offices", "clr", "relatively more services and offices"),
    "u6_clr_city_making_storing": ("Mix: making & storing", "clr", "relatively more workshops, manufacturing and storage"),
    "u6_clr_city_institutions": ("Mix: institutions", "clr", "relatively more schools, health, religious and public institutions"),
    "p_residential": ("Residential land", "share", "more occupied land in residential use"),
    "p_industrial": ("Industrial land", "share", "more occupied land in industrial use"),
    "p_institutional": ("Institutional land", "share", "more occupied land in institutional use"),
}
COL_DESC = {   # columns of multi-column families; single-column families use the family text
    "ov_m4_wmedian_compactness": "Area-weighted median compactness of the street blocks, 4πA/P² (1 = a circle).",
    "ov_m4_wmedian_elongation": "Area-weighted median elongation of the street blocks, longest ÷ shortest side.",
    "u6_log_intensity": "Establishments (Overture places, five activity classes) per 100 dwellings, in logs.",
    "p_residential": "Share of classified occupied land in residential use.",
    "p_industrial": "Share of classified occupied land in industrial use.",
    "p_institutional": "Share of classified occupied land in institutional use.",
}
FACTORS = {    # P-AB-1 factor: (name, group, method A definition, method B definition, unit A, unit B)
    "C": ("Commercial establishments", "built environment", "Overture places in five commercial categories inside the unit",
          "C ÷ land km²", "places", "places/km²"),
    "R": ("Residential establishments", "built environment", "Dwellings: CNEFE 2022 private dwellings (SP); Census 2020 housing units (Chicago)",
          "R ÷ land km²", "dwellings", "dwellings/km²"),
    "H": ("Transportation hubs", "built environment", "Metro/'L' stations + bus stops (GTFS) inside the unit", "H ÷ land km²", "stops", "stops/km²"),
    "V": ("Building height", "built environment", "Mean Overture height of buildings with a height",
          "GHSL built volume ÷ built surface", "m", "m"),
    "N": ("Number of streets", "network", "Overture road segments (ten classes) whose midpoint is in the unit", "N ÷ land km²", "segments", "segments/km²"),
    "L": ("Average street length", "network", "Mean length of those segments", "same as A", "m", "m"),
}


def clean(a, nd=10):
    """JSON-ready list: floats rounded, NaN -> None."""
    return [None if (v is None or (isinstance(v, float) and np.isnan(v))) else (round(float(v), nd) if isinstance(v, (float, np.floating)) else v)
            for v in a]


def records(df):
    return json.loads(df.to_json(orient="records", double_precision=10))


def unit_name(n):
    return NAME_FIX.get(n, n)


def polygons(ids):
    """Simplified rings per unit in each city's projected CRS, integer decametres from the city's corner."""
    sp, ch = xm.geometry()
    out = {}
    for g, crs in ((sp, 31983), (ch, 26916)):
        g = g.to_crs(crs)
        g["geometry"] = g.geometry.simplify(SIMPLIFY_M, preserve_topology=True)
        x0, y0 = g.total_bounds[0], g.total_bounds[1]
        for uid, geom in zip(g.unit_id, g.geometry):
            parts = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
            rings = []
            for p in parts:
                for r in [p.exterior, *p.interiors]:
                    xy = np.round((np.asarray(r.coords)[:, :2] - [x0, y0]) / 10).astype(int)
                    rings.append(xy.ravel().tolist())
            out[uid] = rings
    missing = set(ids) - set(out)
    if missing:
        raise ValueError(f"no polygon for {sorted(missing)}")
    return [out[u] for u in ids]


def harmonized(df, subs, fams, ids):
    """Every block of the three C6 scalings, built by cm.blocks exactly as the published fit."""
    scalings = {}
    for s in ("hybrid", "all_absolute", "all_relative"):
        bl = cm.blocks(xm.frame_for(df, subs, s), fams, levels=xm.levels(s))
        scalings[s] = dict(levels={c: v for c, v in xm.levels(s).items() if c in df.columns},
                           blocks=[dict(family=b["family"], block=b["block"], columns=b["columns"], share=b["share"], cal=b["cal"],
                                        X=[clean(row) for row in b["X"]]) for b in bl])
    col_fam = {c: f for f, cs in fams.items() for c in cs}
    r3 = {s: sorted({col_fam[c] for c in pd.read_csv(XR / f"r3_pruning_log_{s}.csv").dropped}) for s in scalings}
    columns = [dict(id=c, family=col_fam[c], label=COLUMNS[c][0], unit=COLUMNS[c][1], high=COLUMNS[c][2],
                    desc=COL_DESC.get(c, FAMILIES[col_fam[c]][2]),
                    transform=cm.TRANSFORM.get(c, "identity (log-ratio)"), raw=clean(df.loc[ids, c].to_numpy(float)))
               for c in df.columns]
    families = [dict(id=f, name=FAMILIES[f][0], domain=FAMILIES[f][1], desc=FAMILIES[f][2], columns=cs,
                     chicago=SOURCES[f][0], sao_paulo=SOURCES[f][1], same_instrument=SOURCES[f][2],
                     hybrid_level="absolute" if xm.levels("hybrid")[next(c for c in cs if c not in cm.CLR)] == "absolute" else "relative")
                for f, cs in fams.items()]
    published = dict(
        pca_variance=records(pd.read_csv(XR / "pca_variance.csv").rename(columns={"Unnamed: 0": "pc"}).head(8)),
        family_shares=records(pd.read_csv(XR / "family_contribution_shares_hybrid_R1.csv").rename(columns={"Unnamed: 0": "family"})),
        sensitivities=records(pd.read_csv(XR / "sensitivities_hybrid.csv")),
        scale_comparison=records(pd.read_csv(XR / "scale_comparison.csv")),
        stability_bras=records(pd.read_csv(XR / "stability_bras_top5_chicago.csv")),
        r3_logs={s: records(pd.read_csv(XR / f"r3_pruning_log_{s}.csv")) for s in scalings},
    )
    return dict(families=families, columns=columns, scalings=scalings, r3_dropped=r3, published=published)


def index_ab(ids):
    t = pd.read_csv(AB / "index_A_B.csv").set_index("unit_id").loc[ids]
    comp = pd.read_csv(AB / "unit_components.csv").set_index("unit_id").loc[ids]
    out = dict(factors=[dict(id=f, name=v[0], group=v[1], defA=v[2], defB=v[3], unitA=v[4], unitB=v[5]) for f, v in FACTORS.items()])
    for m in ("A", "B"):
        out[m] = dict(raw={f: clean(t[f"{m}_raw_{f}"]) for f in FACTORS}, scaled={f: clean(t[f"{m}_scaled_{f}"], 15) for f in FACTORS},
                      index=clean(t[f"{m}_index"], 15), rank=t[f"{m}_rank"].astype(int).tolist())
    out["components"] = {c: clean(comp[c], 3) for c in ["C_count", "R_count", "H_stations", "H_bus", "V_A_n", "N_count"]}
    tests = dict(t1=pd.read_csv(AB / "t1_boundary_invariance.csv"), t2=pd.read_csv(AB / "t2_size_dependence.csv"),
                 t3=pd.read_csv(AB / "t3_agreement.csv"), t4=pd.read_csv(AB / "t4_city_composition.csv"),
                 s1=pd.read_csv(AB / "s1_bus_merged.csv"), summary=pd.read_csv(AB / "index_summary.csv"))
    out["tests"] = {k: records(v) for k, v in tests.items()}
    return out, comp


def summary(comp, city):
    """Overview figures, all computed from the project's tables."""
    c = comp.assign(city=city.values)
    g = c.groupby("city")
    return {k: dict(units=int(g.size()[k]), land_km2=round(float(g.land_km2.sum()[k]), 1), land_median_km2=round(float(g.land_km2.median()[k]), 2),
                    commercial_places=int(g.C_count.sum()[k]), dwellings=int(round(g.R_count.sum()[k])), stations=int(g.H_stations.sum()[k]),
                    bus_stops=int(g.H_bus.sum()[k]), buildings_with_height=int(g.V_A_n.sum()[k]), road_segments=int(g.N_count.sum()[k]))
            for k in ("SP", "CHI")}


def main():
    x, df, subs, names, city, fams = xm.load_inputs()
    ids = df.index.tolist()
    ab, comp = index_ab(ids)
    data = dict(
        meta=dict(contract=x["contract_version"], reference=xm.REFERENCE, simplify_m=SIMPLIFY_M,
                  generated_by="analysis/scripts/export_viz_data.py"),
        units=[dict(id=u, name=unit_name(names[u]), city=city[u], land_km2=round(float(comp.land_km2[u]), 3)) for u in ids],
        polygons=polygons(ids),
        ab=ab,
        h=harmonized(df, subs, fams, ids),
        summary=summary(comp, city),
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("// Generated by analysis/scripts/export_viz_data.py; do not edit.\nwindow.VIZ_DATA = "
                   + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(xm.ROOT)} ({OUT.stat().st_size / 1e6:.2f} MB): {len(ids)} units")


if __name__ == "__main__":
    main()
