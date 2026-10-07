# The five Chicago Community Areas whose index is closest to Brás (SP:10): gap(u) = |I(u) − I(Brás)|, smallest first.
# Profile rank (diagnostic): rank among the 77 areas by Euclidean distance between the six scaled factors and Brás's.
import numpy as np
import pandas as pd

F = ['scaled_' + f for f in 'CRHVNL']
bras = arg.set_index('unit_id').loc['SP:10']
chi = arg[arg.city == 'Chicago'].copy()
chi['gap'] = (chi['index'] - bras['index']).abs()
chi['profile_distance'] = np.sqrt(((chi[F] - bras[F].astype(float)) ** 2).sum(axis=1))
chi['profile_rank'] = chi.profile_distance.rank(method='min').astype(int)
top = chi.sort_values(['gap', 'unit_id']).head(5)
m = arg['method'].iloc[0]
return pd.DataFrame({'Rank': range(1, 6), 'Area': top['name'].values, f'Index {m}': top['index'].round(3).values,
                     f'Brás index {m}': round(float(bras['index']), 3), 'Gap': top['gap'].round(3).values,
                     'Profile rank (of 77)': top['profile_rank'].values})
