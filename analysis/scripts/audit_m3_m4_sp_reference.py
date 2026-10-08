"""Post-hoc diagnostic for S8-4 (written after São Paulo failed the like-for-like check): which reference disagrees with the
official blocks, and M4 of Overture faces vs official quadras (M4 had no official check). A gap-closing rebuild was tried and abandoned (too slow)."""
import json
import geopandas as gpd, numpy as np, pandas as pd, pyogrio, shapely
import evaluate_b1_step4 as b1
import evaluate_m3_m4_m7_step8 as s8

def main():
    res = {}
    t = pd.read_csv(s8.OUT / "m3_m4_m7_by_unit.csv").set_index("unit_id")
    for city, c in t.groupby("city"):                   # which reference disagrees with the official blocks?
        sp = lambda a, b: round(float(c[a].corr(c[b], method="spearman")), 4)
        res[f"{city}_M3_spearman"] = {"overture_vs_official": sp("ov_m3_wmedian_ln_m2", "official_m3_wmedian_ln_m2"),
                                      "municipal_vs_official": sp("muni_m3_wmedian_ln_m2", "official_m3_wmedian_ln_m2"),
                                      "overture_vs_municipal": sp("ov_m3_wmedian_ln_m2", "muni_m3_wmedian_ln_m2")}
        res[f"{city}_land_in_municipal_faces_p10"] = round(float((c.muni_land_in_faces_m2 / (c.land_km2 * 1e6)).quantile(.1)), 3)
    t = t.query("city == 'SP'")
    q = pyogrio.read_dataframe(s8.D / "SP/Cadastro e Vias/quadra_viaria_editada.gpkg", columns=["tx_tipo_quadra_viaria"]).to_crs(31983)
    g = shapely.make_valid(q[q.tx_tipo_quadra_viaria.eq("Quadra")].geometry.values)
    ext = shapely.polygons(shapely.get_exterior_ring(g))
    rect = shapely.get_coordinates(shapely.oriented_envelope(g)).reshape(-1, 5, 2)[:, :3]
    s1, s2 = np.hypot(*(rect[:, 1] - rect[:, 0]).T), np.hypot(*(rect[:, 2] - rect[:, 1]).T)
    off = gpd.GeoDataFrame({"land_m2": shapely.area(g), "compactness": 4 * np.pi * shapely.area(ext) / shapely.length(shapely.get_exterior_ring(g)) ** 2,
                            "elongation": np.maximum(s1, s2) / np.minimum(s1, s2)}, geometry=g)
    o = s8.summarise(off, b1.land_units("SP"), "q").join(t)
    res["SP_M4_vs_official_quadras"] = {"compactness": round(float(o.ov_m4_wmedian_compactness.corr(o.q_m4_wmedian_compactness, method="spearman")), 4),
                                        "elongation": round(float(o.ov_m4_wmedian_elongation.corr(o.q_m4_wmedian_elongation, method="spearman")), 4)}
    (s8.OUT / "posthoc_reference_diagnostic.json").write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
