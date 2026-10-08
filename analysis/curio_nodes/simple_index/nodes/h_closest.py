# The five Chicago Community Areas closest to Brás (SP:10) in the harmonized model, and what drives each distance:
# the two families with the largest share of D² (each family's part of the squared distance; parts sum to D²).
import pandas as pd

t = arg[(arg.unit_id == 'SP:10') & (arg.other_city == 'Chicago')].sort_values(['distance', 'other_id']).head(5)
parts = t[[c for c in t if c.startswith('d2_')]]
share = parts.div(parts.sum(axis=1), axis=0)


def drivers(row):
    top = row.sort_values(ascending=False).head(2)
    return ', '.join(f'{k[3:]} {v:.0%}' for k, v in top.items())


return pd.DataFrame({'Rank': t.rank_in_city.values, 'Area': t.other_name.values, 'Distance': t.distance.round(3).values,
                     'Rank of all 172': t['rank'].values, 'Largest parts of D²': share.apply(drivers, axis=1).values})
