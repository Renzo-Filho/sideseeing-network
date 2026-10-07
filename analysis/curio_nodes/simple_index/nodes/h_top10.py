# The ten units most similar to Brás (SP:10) in the harmonized model, both cities pooled: smallest distance first.
import pandas as pd

t = arg[arg.unit_id == 'SP:10'].sort_values(['distance', 'other_id']).head(10)
return pd.DataFrame({'Rank': t['rank'].values, 'Unit': t.other_name.values, 'City': t.other_city.values,
                     'Rank in its city': t.rank_in_city.values, 'Distance': t.distance.round(3).values})
