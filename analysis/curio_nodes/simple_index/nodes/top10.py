# Top ten units by index (both cities pooled).
import pandas as pd

t = arg.sort_values('rank').head(10)
area = 'land_km2' if 'land_km2' in t else 'gross_area_km2'
label = 'Land km²' if area == 'land_km2' else 'Area km² (gross)'
return pd.DataFrame({'Rank': t['rank'].values, 'Unit': t['name'].values, 'City': t['city'].values,
                     label: t[area].round(1).values, f"Index {t['method'].iloc[0]}": t['index'].round(3).values})
