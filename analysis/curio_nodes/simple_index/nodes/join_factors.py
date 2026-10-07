# Join the factor tables (one row per unit) on unit_id, so the next merge carries one table plus land area.
comp = arg[0]
for part in arg[1:]:
    comp = comp.merge(part, on='unit_id', how='left', validate='one_to_one')
assert len(comp) == 173 and comp.unit_id.is_unique
return comp
