"""Post-hoc diagnostic for S7-5 (Chicago): residential share of Cook 2024 ground-parcel LAND AREA (not PIN counts) vs CMAP residential share."""
import glob
import geopandas as gpd, pandas as pd
import evaluate_b1_step4 as b1

A = b1.A
OUT = A / "results/SP_CHI/u1_step7_2026_10_06"


def main():
    u = b1.land_units("CHI")
    parts = []
    for f in sorted(glob.glob(str(b1.D / "Chicago/chicago_cadastral_2026_09_18/cook_parcels_2024/*.parquet"))):
        g = gpd.read_parquet(f, columns=["geometry", "PARCELTYPE", "AssessorBLDGclass"]).to_crs(26916)
        g = g[g.PARCELTYPE.eq("BaseParcel") & g.AssessorBLDGclass.notna()]          # ground parcels; condo units are separate layers
        parts.append(gpd.GeoDataFrame({"res": g.AssessorBLDGclass.astype(str).str[0].isin(["2", "3"]), "a": g.geometry.area},
                                      geometry=g.geometry.representative_point(), crs=26916))
    p = gpd.sjoin(pd.concat(parts, ignore_index=True).pipe(gpd.GeoDataFrame, crs=26916), u, predicate="within")
    ref = (p.a * p.res).groupby(p.unit_id).sum() / p.a.groupby(p.unit_id).sum()
    t = pd.read_csv(OUT / "u1_by_unit.csv").set_index("unit_id")
    c = t[t.city == "CHI"].join(ref.rename("ref_residential_parcel_area_share"))
    rho = c.p_residential.corr(c.ref_residential_parcel_area_share, method="spearman")
    rho_cnt = c.p_residential.corr(c.ref_residential_pin_share, method="spearman")
    print(f"CMAP residential share vs Cook ground-parcel residential AREA share: Spearman {rho:.3f} (pre-registered PIN-count reference {rho_cnt:.3f})")
    c[["p_residential", "ref_residential_pin_share", "ref_residential_parcel_area_share"]].to_csv(OUT / "chicago_reference_diagnostic.csv")


if __name__ == "__main__":
    main()
