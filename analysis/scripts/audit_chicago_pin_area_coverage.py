"""Count, by Cook property-class group, how many Chicago-linked 2024 PINs have a positive recorded building/unit area in any local assessor source; write CSVs to argv[1]."""
import glob, re, sys, pathlib
import pandas as pd, pyarrow.parquet as pq

D = "analysis/data/Chicago/chicago_cadastral_2026_09_18/"
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)


def rd(name, cols):
    return pd.concat(pq.read_table(f, columns=cols).to_pandas() for f in sorted(glob.glob(D + name + "/*.parquet")))


def pos(s):
    return pd.to_numeric(s, errors="coerce") > 0


dig = lambda s: re.sub(r"\D", "", s)
u = rd("cook_universe_2024", ["pin", "class", "chicago_community_area_num"])
u = u[u.chicago_community_area_num.notna()].copy()
u["pin"] = u.pin.astype(str).str.zfill(14); u["grp"] = u["class"].astype(str).str[:1]
res = rd("cook_residential_2024", ["pin", "char_bldg_sf"]); con = rd("cook_condo_2024", ["pin", "char_unit_sf", "char_building_sf"])
com = rd("cook_commercial_2024", ["keypin", "pins", "bldgsf"]); com = com[pos(com.bldgsf)]
comm = {dig(k) for k in com.keypin} | {dig(p) for s in com.pins.astype(str) for p in re.findall(r"\d{2}-\d{2}-\d{3}-\d{3}-\d{4}", s)}
u["residential_area"] = u.pin.isin(res.loc[pos(res.char_bldg_sf), "pin"].astype(str).str.zfill(14))
u["condo_unit_area"] = u.pin.isin(con.loc[pos(con.char_unit_sf), "pin"].astype(str).str.zfill(14))
u["condo_building_area"] = u.pin.isin(con.loc[pos(con.char_building_sf), "pin"].astype(str).str.zfill(14))
u["commercial_area"] = u.pin.isin(comm)
src = ["residential_area", "condo_unit_area", "condo_building_area", "commercial_area"]
u["any_area"] = u[src].any(axis=1)
t = u.groupby("grp").agg(pins=("pin", "size"), **{c: (c, "sum") for c in src}, any_area=("any_area", "sum"))
t["pct_any_area"] = (100 * t.any_area / t.pins).round(1)
t.to_csv(OUT / "pin_area_coverage_by_class_group.csv"); u["class"].value_counts().head(15).to_csv(OUT / "top_classes.csv")
u[~u.any_area & (u.grp == "2")]["class"].value_counts().head(10).to_csv(OUT / "class2_without_area_top.csv")
print(t.to_string()); print("TOTAL", len(u), int(u.any_area.sum()), round(100 * u.any_area.mean(), 1))
