"""São Paulo height references for BV (S5-6): GeoSampa on two known towers, and IPTU 2026 floors weighted by occupied area."""
import glob
import geopandas as gpd, numpy as np, pandas as pd, pyogrio
import evaluate_b1_step4 as B

OUT = B.A / "results/SP_CHI/bv_step5_2026_10_05"


def main():
    tw = gpd.GeoDataFrame({"name": ["Edificio Italia (commonly cited 165 m, not verified)", "Copan (commonly cited 115 m, not verified)"]},
                          geometry=gpd.points_from_xy([-46.6437, -46.6446], [-23.5453, -23.5465]), crs=4326).to_crs(31983)
    g = pd.concat([gpd.read_file(f"zip://{f}", columns=["qt_altura_"]) for f in sorted(glob.glob(str(B.D / "SP/geosampa_edificacao_2026_10_05/page_*.zip")))], ignore_index=True)
    g = g.set_crs(31983, allow_override=True) if g.crs is None else g.to_crs(31983)
    for r in tw.itertuples():
        print(r.name, "-> GeoSampa heights within 25 m:", g[g.intersects(r.geometry.buffer(25))].qt_altura_.nlargest(2).round(1).tolist())
    cols = ["NUMERO DO CONTRIBUINTE", "NUMERO DO CONDOMINIO", "AREA OCUPADA", "QUANTIDADE DE PAVIMENTOS"]
    d = pd.read_csv(B.D / "SP/Cadastro e Vias/IPTU_2026.csv", sep=";", usecols=cols, dtype=str, encoding="latin-1")
    d["occ"] = pd.to_numeric(d["AREA OCUPADA"].str.replace(",", "."), errors="coerce").fillna(0)
    d["fl"] = pd.to_numeric(d["QUANTIDADE DE PAVIMENTOS"], errors="coerce")
    c, condo = d["NUMERO DO CONTRIBUINTE"], d["NUMERO DO CONDOMINIO"].fillna("00-0").str.strip()
    d["block"], d["lot"] = c.str[:6], np.where(condo.eq("00-0"), c.str[:10], c.str[:6] + "C" + condo)
    lots = d.groupby("lot").agg(occ=("occ", "median"), fl=("fl", "median"), block=("block", "first")).reset_index()
    lots = lots[(lots.occ > 0) & (lots.fl > 0)]
    q = pyogrio.read_dataframe(B.D / "SP/Cadastro e Vias/geoportal_quadra_fiscal_gsc.gpkg")
    q["block"] = q.cd_setor_fiscal + q.cd_quadra_fiscal
    q = q.dissolve("block").reset_index()
    u = B.land_units("SP")
    pts = gpd.GeoDataFrame(q[["block"]], geometry=q.geometry.representative_point(), crs=q.crs)
    lots["unit_id"] = lots.block.map(gpd.sjoin(pts, u, predicate="within").set_index("block").unit_id)
    fw = lots.dropna(subset=["unit_id"]).groupby("unit_id").apply(lambda x: (x.fl * x.occ).sum() / x.occ.sum(), include_groups=False).rename("iptu_floors_occ_weighted")
    t = pd.read_csv(OUT / "bv_step5_by_unit.csv").set_index("unit_id")
    t = t[t.city == "SP"].join(fw)
    for col in ("bv_height_built_m", "geosampa_height_m", "overture_osm_height_m"):
        print(f"{col}: Spearman with IPTU floors {t[col].corr(t.iptu_floors_occ_weighted, method='spearman'):.3f}; "
              f"median metres per floor {(t[col] / t.iptu_floors_occ_weighted).median():.2f}")
    t[["iptu_floors_occ_weighted"]].to_csv(OUT / "sp_iptu_floors.csv")


if __name__ == "__main__":
    main()
