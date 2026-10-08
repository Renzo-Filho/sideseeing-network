# Chicago centerline CLASS versus Overture road class

Run `analysis/scripts/review_chicago_centerline_class_vs_overture.py`. For each Chicago Street Center Lines record with status `N` and CLASS in `1,2,3,4,7,9,99` (the local M1 filter), the midpoint is matched to the nearest raw Overture `road` segment within 15 m (release 2026-08-19.0, all road classes including `service`). Shares are weighted by centerline length. This is a cross-scheme consistency check, not ground truth: Overture classes are largely OpenStreetMap tags, one midpoint stands for each record, and the nearest segment can be a service road even when an eligible street is also within 15 m.

Outputs: `centerline_class_vs_overture_class.csv` (class × Overture class, km and share) and `class4_street_type.csv`.

| CLASS (city label) | km | Nearest Overture class (share of length) |
|---|---:|---|
| 1 expressway | 286 | motorway 95.1%, trunk 3.2% |
| 2 arterials | 680 | secondary 66.2%, primary 14.0%, tertiary 11.9% |
| 3 collectors | 762 | secondary 44.2%, tertiary 42.2%, primary 4.5% |
| **4 other streets** | **4,905** | **residential 79.8%, service 10.4%, tertiary 5.7%, secondary 1.7%, unclassified 1.3%, no road within 15 m 0.3%** |
| 9 ramps | 157 | motorway 92.9% |
| 99 unclassified (O'Hare) | 146 | no Overture road within 15 m 57.2%, service 23.2%, unclassified 10.0% |

Class 4 by `street_typ`: AVE 54.2%, ST 35.7%, PL 4.7%, DR 1.7%, BLVD 1.6%. The suffix does not separate local from arterial streets.

**Reading.** Classes 1–3 map sensibly onto Overture's motorway/primary/secondary/tertiary ladder, so the city and Overture agree on the upper hierarchy. Class 4 is dominantly residential-type streets but is a residual: about 7% falls on Overture tertiary/secondary (collector-like) and about 10% on `service`-type roads, which Overture M1 excludes. It should not be relabelled Local wholesale; a defensible working description is "residual class, ≈ 80% residential-type". No official definition of "other streets" beyond the city's dictionary label was found.
