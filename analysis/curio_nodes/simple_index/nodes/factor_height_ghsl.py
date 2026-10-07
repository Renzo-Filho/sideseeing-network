# V (method B) · GHSL built volume ÷ built surface: V_B(u) = Σ_c w_c·AGBH_c / Σ_c w_c·(AGBH_c / ANBH_c), over the
# native 100 m cells c (ESRI:54009) valid in ANBH and AGBH 2018 and volume 2020, with w_c = area(c ∩ u).
# Unit outlines as in the GHSL evaluation: GeoSampa's district layer and the City of Chicago's Community Area GeoJSON,
# both downloaded through the Discovery Catalog.
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
from rasterio.windows import Window, from_bounds

sp = gpd.read_file(arg['sp_units_municipal'])
sp['unit_id'] = 'SP:' + sp.cd_distrito_municipal.astype(str).str.zfill(2)
chi = gpd.read_file(arg['chi_units_geojson'])
chi['unit_id'] = 'CHI:' + chi.area_numbe.astype(int).astype(str).str.zfill(2)

rows = []
for units, r in ((sp, arg['ghsl_sp']), (chi, arg['ghsl_chi'])):
    with rasterio.open(r['anbh']) as a, rasterio.open(r['agbh']) as g, rasterio.open(r['volume']) as v:
        units = units.to_crs(a.crs)
        for u in units.itertuples():
            raw = from_bounds(*u.geometry.bounds, transform=a.transform)
            win = Window(int(np.floor(raw.col_off)), int(np.floor(raw.row_off)), int(np.ceil(raw.width)) + 1,
                         int(np.ceil(raw.height)) + 1).intersection(Window(0, 0, a.width, a.height))
            A, G, V = (x.read(1, window=win, masked=True) for x in (a, g, v))
            tr = a.window_transform(win)
            ov = np.zeros(A.shape)
            for i, j in np.argwhere(~np.ma.getmaskarray(A)):
                x0, y0 = tr * (j, i + 1)
                x1, y1 = tr * (j + 1, i)
                ov[i, j] = shapely.box(x0, y0, x1, y1).intersection(u.geometry).area
            ok = ~np.ma.getmaskarray(A) & ~np.ma.getmaskarray(G) & ~np.ma.getmaskarray(V) & (ov > 0)
            w, an, ag = ov[ok], A.data[ok].astype(float), G.data[ok].astype(float)
            frac = np.where(an > 0, ag / np.where(an > 0, an, 1), 0.0)
            rows.append({'unit_id': u.unit_id, 'V_B_num': float((w * ag).sum()), 'V_B_den': float((w * frac).sum())})
return pd.DataFrame(rows)
