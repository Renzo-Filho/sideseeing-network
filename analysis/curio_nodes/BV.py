# BV: GHSL native 100 m ANBH 2018 on municipal hydrographic land.
# Valid zero-height cells are included; nodata is excluded and reported.
import geopandas as gpd
import pandas as pd
import numpy as np
import shapely
import rasterio
from rasterio.windows import from_bounds
areas=gpd.read_file(arg[0]['community_areas'])
areas['unit_id']='CHI:'+areas.area_numbe.astype(int).astype(str).str.zfill(2)
areas=areas[['unit_id','geometry']].sort_values('unit_id').reset_index(drop=True)
assert len(areas)==areas.unit_id.nunique()==77
hydro=gpd.read_file(arg[1]['hydrography'])
rows=[]
with rasterio.open(arg[2]['ghsl_anbh_2018']) as raster:
    assert raster.res==(100.,100.) and raster.crs.to_string()=='ESRI:54009'
    areas=areas.to_crs(raster.crs)
    water=hydro.to_crs(raster.crs).geometry.union_all()
    for area in areas.itertuples():
        land=area.geometry.difference(water)
        raw=from_bounds(*land.bounds,transform=raster.transform)
        left=int(np.floor(raw.col_off)); top=int(np.floor(raw.row_off))
        right=int(np.ceil(raw.col_off+raw.width)); bottom=int(np.ceil(raw.row_off+raw.height))
        window=rasterio.windows.Window(left,top,right-left,bottom-top)
        window=window.intersection(rasterio.windows.Window(0,0,raster.width,raster.height))
        data=raster.read(1,window=window,masked=True)
        valid=~np.ma.getmaskarray(data)
        transform=raster.window_transform(window)
        numerator=valid_area=0.0
        for rr,cc in np.argwhere(valid):
            x0,y0=transform*(int(cc),int(rr)); x1,y1=transform*(int(cc)+1,int(rr)+1)
            cell=shapely.box(min(x0,x1),min(y0,y1),max(x0,x1),max(y0,y1))
            overlap=cell.intersection(land).area
            if overlap>0: numerator+=float(data[rr,cc])*overlap; valid_area+=overlap
        if valid_area<=0: raise ValueError(area.unit_id+' has no raster support')
        coverage=valid_area/land.area
        rows.append({'unit_id':area.unit_id,'BV_net_grid_height_land_m':numerator/valid_area,
                     'valid_area_m2':valid_area,'land_area_m2':land.area,'raster_support_fraction':coverage,
                     'status':'constructed_chicago' if coverage>1-1e-8 else 'incomplete_raster_support'})
return pd.DataFrame(rows)
