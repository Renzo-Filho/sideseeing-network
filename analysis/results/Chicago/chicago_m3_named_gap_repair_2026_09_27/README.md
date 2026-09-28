# Named-street gap repair screen, 27 September 2026

**Decision:** The West Veterans Place parcel-guided split does not generalize automatically to the other named-street gap alerts. Among 11 frozen alerts in four cached Community Areas, the tested 10 m nonparcel corridor creates one additional closed local land face only at West Veterans Place. Other alerts need grade, public-street status, source alignment and property-side review before a repair is proposed. This is a topology/source screen, not a complete block reference or accuracy estimate.

## Screen

The [previous named-street audit](../chicago_m3_complete_zone_pilot_v1_2026_09_26/README.md) flagged 11 municipal segments with at least 30 m outside Cook ROW plus ordinary Road Edge after a 5 m alignment allowance. Here each full municipal segment receives a 120 m local analysis envelope. We intersect its 10 m search buffer with land outside Cook BaseParcels and directly union the result with the existing ROW + ordinary Road Edge barrier after 3 m mapped-alley reopening. We compare the number of closed land faces in the envelope before and after. The [case table](named_gap_repair_screen.csv) retains added corridor area, parcel crossing fraction and closed-face areas.

| Alert group | Observation | Interpretation for next review |
|---|---|---|
| W Veterans Pl | 0% of line length inside BaseParcels; 1,379 m² added corridor; closed local faces rise from 1 to 2. | Reproduces the known merge repair candidate. Independent property-side edge and road-status checks remain. |
| E Congress Dr, longer segment | About 4% of line inside parcels and 2,318 m² added corridor, but no additional closed face. | Investigate endpoints, grade and surrounding barriers; added area alone does not repair a merge. |
| E Wacker Dr, one segment | No parcels in its local envelope; 2,234 m² corridor, no closed face. | Likely special downtown/river or grade context; inspect imagery and street level before any split. |
| Other eight alerts | New corridors are 0–46 m²; several municipal lines lie mostly or wholly inside BaseParcels. One is explicitly named `E WACKER LOWER DR`, class 7. | Potential centerline/cadastre alignment or stacked-street cases; no automatic parcel-gap repair. |

The four examined units are CHI:11, 32, 57 and 63. The screening inventory is **not** a citywide census of missing boundaries. A count of closed faces inside an artificial 120 m envelope is only a triage metric; a true block may extend outside it. The line-inside-parcels fraction is also a cadastral alignment signal, not a public-road-status test. A zero face delta does not prove that an alert is false.

## Implication for candidate method

Keep named municipal gaps as reason-coded alerts. Apply a nonparcel corridor only after local evidence shows an ordinary at-grade public street and a plausible property-side gap; preserve the original face and mark unverified repairs unresolved. The earlier [West Veterans topology test](../chicago_m3_veterans_repair_2026_09_27/README.md) identified the safe direct-union operation, but did not establish a universal 10 m search width. Review the two large-corridor/no-split downtown cases before claiming the gap procedure has general reach.

Reproduce from the cached sources with:

```bash
.venv/bin/python analysis/scripts/audit_chicago_m3_named_gap_repairs_2026_09_27.py
```

The [summary](summary.json) records the alert count, units and closed-face changes. No candidate here is promoted to an accepted M3/M4 block.
