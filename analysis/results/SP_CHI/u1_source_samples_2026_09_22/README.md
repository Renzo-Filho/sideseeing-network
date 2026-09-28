# U1 bounded source and destination samples — 22 September 2026

**Status: diagnostic only. U1 remains unaccepted; no common model was fitted.** This checkpoint compares three possible meanings for a recovered U1 feature: developed-use area mix, all-land use mix, and destination diversity. It follows the [12-unit summary screen](../u1_summary_pilot_2026_09_22/README.md) and uses only six of those units for source inspection.

## Scope and reproducibility

Fixed seed `20260922`; three selected units per city: Brás (SP:10), Alto de Pinheiros (SP:02), São Domingos (SP:95), Loop (CHI:32), Albany Park (CHI:14), and Humboldt Park (CHI:23). The earlier summary screen selected them as central, residential and industrial contrasts. This is a purposive/stratified diagnostic sample, **not a citywide prevalence estimate**.

`analysis/scripts/pilot_u1_source_samples.py` reads three São Paulo parcel partitions and accepted-use fields, three spatially bounded Chicago CMAP LUI 2023 reads, small district land geometries, and the São Paulo mapped-parks layer. It draws **20 uniform land points and 20 uniform source polygons per unit** (120 of each overall), records raw codes and positions, and never overlays all 173 units. The land points approximate area support; the polygons expose label variety. The parks layer is only a partial open-space cue. These source labels were not verified against independent ground truth.

`analysis/scripts/pilot_u1_poi_samples.py` reads the [Overture Places 2026-08-19.0 release](https://stac.overturemaps.org/2026-08-19.0/places/place/collection.json), matched to the release already used for roads/buildings. It queries two geographic Parquet partitions using one bounding box around the three selected districts in each city; DuckDB uses one thread and a 512 MB memory cap. The boxes return 129,373 SP and 85,155 Chicago records, of which exact district point-in-polygon tests retain **10,479 SP and 19,503 Chicago** records. The remaining bbox records are discarded. Only aggregate results and **20 fixed-seed POIs per unit** are saved, not a citywide Places extract. Parquet metadata indicated 15/256 relevant SP and 9/256 relevant Chicago row groups for the combined boxes. Source URLs and boxes are in [poi_checks.json](poi_checks.json). The query is reproducible with local DuckDB `httpfs` and internet access.

## Land-source findings

| Unit | Source-coded land points / 20 | Ambiguous or unmatched points | Implication |
|---|---:|---|---|
| Brás | 14 cadastral-covered | 6 no cadastral use; 2 mixed/other and 1 unknown among covered | A six-class developed-use entropy would discard 9 of 20 sampled land locations. |
| Alto de Pinheiros | 14 cadastral-covered | 5 no cadastral use, 1 mapped park outside cadastral use; 1 mixed/other and 2 unknown among covered | Open space cannot be inferred from fiscal use alone. |
| São Domingos | 16 cadastral-covered | 4 no cadastral use; 2 mixed/other and 1 unknown among covered | Unmatched land and mixed use remain material in this small sample. |
| Loop | 20 CMAP-covered | 4 open-space and 4 raw `6000` generic/nonparcel code | A developed-only denominator discards substantial sampled land. |
| Albany Park | 20 CMAP-covered | 7 raw `6000` points | Treating every mapped polygon as a comparable use class would be misleading. |
| Humboldt Park | 20 CMAP-covered | 2 raw `6000` points | Some land has no specific use class despite polygon coverage. |

The 20-point counts are **not area percentages with useful precision**. Chicago `6000` is kept as source-unclassified here; it is not silently reinterpreted as open space, transport, or residential. No conflicting overlapping source categories occurred at the sampled points. The 20 uniformly selected polygons per unit are in [sampled_source_polygons.csv](sampled_source_polygons.csv); they have a different sampling weight and must not be pooled with land points.

## POI findings

Overture Places uses point destinations and a [hierarchical taxonomy](https://docs.overturemaps.org/guides/places/taxonomy/). We tested a **fixed 12-category destination ontology**, excluding unmapped taxonomy and `geographic_entities` from entropy while retaining their counts. The denominator is the number of classified destination records, not land area. Entropy uses Shannon H / ln(12). Thresholds 0.5 and 0.75 are sensitivities, **not calibrated accuracy cutoffs**.

| Unit | POIs / classified destinations | Unclassified or geographic | Fixed-12 entropy, all / confidence ≥0.75 |
|---|---:|---:|---:|
| Brás | 5,443 / 5,183 | 260 (4.8%) | 0.538 / 0.597 |
| Alto de Pinheiros | 2,306 / 2,219 | 87 (3.8%) | 0.857 / 0.880 |
| São Domingos | 2,730 / 2,622 | 108 (4.0%) | 0.839 / 0.866 |
| Loop | 16,569 / 12,762 | 3,807 (23.0%) | 0.780 / 0.760 |
| Albany Park | 1,426 / 1,375 | 51 (3.6%) | 0.835 / 0.828 |
| Humboldt Park | 1,508 / 1,447 | 61 (4.0%) | 0.859 / 0.842 |

Brás has 3,230 shopping POIs (62% of its classified destinations); Loop has 5,412 services/business POIs (42%). These profiles capture a recognizable **destination** contrast, but are not observations of residential share, parcel area, industrial land or jobs. Median record confidence is 0.564 in Brás versus 0.888 in the Loop; thresholding shifts the Brás entropy by about +0.059 and the Loop by −0.021. The fixed-seed 20-record Loop inspection includes multiple unclassified, implausible-looking names; their actual existence/location was not independently checked. A same-name/approximately 10 m diagnostic flags 0–4 candidate duplicate records per unit, but does not estimate total duplication or completeness. [POI category counts](poi_category_counts.csv), [summaries](poi_summary.csv) and [sampled records](sampled_pois.csv) preserve the evidence.

## Assessment of the three meanings

| Option | What the sample supports | Why it is not ready |
|---|---|---|
| **Developed-use area mix** | Both cities have usable broad residential/commercial/industrial/institutional codes on parts of sampled land. A common classified-land denominator is technically possible. | SP fiscal primary use versus Chicago observed primary land use remains a semantic mismatch; SP uncovered/mixed/unknown and Chicago `6000` residuals are too visible to renormalize away. Accepted-entity area and district land still use different supports. |
| **All-land use mix** | Chicago distinguishes some open-space polygons; the SP parks layer locates at least one sampled park outside cadastral coverage. | The SP layer is partial, while Chicago `6000` combines unspecified nonparcel support. No paired comprehensive observed open-land inventory has been validated. This option is weaker with current inputs. |
| **Destination diversity** | A same-release, paired POI source can be queried cheaply for selected neighborhoods; a shared 12-category taxonomy yields interpretable profiles. | The Loop has 23% records without a destination category; confidence distributions differ; some labels appear suspect; mapping completeness and source selection remain untested. It measures destinations rather than U1 land-use area. |

**Working recommendation for discussion:** carry developed-use area mix as the closest U1 repair, with explicit classified, mixed, unknown, nonparcel and unmapped land mass on one district-land denominator. Carry destination diversity as a separately named candidate to test for added information and source quality. Defer an all-land entropy until a comprehensive, comparable SP open-land source and Chicago nonparcel allocation rule are demonstrated. None of the three passes U1 acceptance yet.

## Next bounded validation

1. Independently inspect the existing point and polygon positions in Brás/Loop and the paired residential/industrial units using local imagery or authoritative reference maps. Label whether each source category matches visible use, and keep uncertain cases; select additional points only for a stated ambiguity.
2. For developed-use mix, compute exact **district-clipped, unioned** classified/mixed/unknown/unmapped areas in these six units only, with a land denominator shared in concept. Test dominant-use assignments for SP `mixed/other` and Chicago mixed-use codes on raw labels; never infer a use solely from zoning.
3. For POIs, independently check the 20 fixed-seed records per unit for existence, location and broad category. Probe the Loop unclassified names and compare confidence thresholds and source/provider composition. Test whether destination diversity adds information beyond U2 jobs, U3 population, B1 footprints and the repaired area-use mix before assigning a family weight.

Reproduce with `.venv/bin/python analysis/scripts/pilot_u1_source_samples.py` and `.venv/bin/python analysis/scripts/pilot_u1_poi_samples.py`. The first requires local prepared sources; the second requires the same plus network access and DuckDB `httpfs`. See [source checks](checks.json) and [POI checks](poi_checks.json). No citywide U1 construction or model fit followed.


**Further bounded follow-up:** [Exact six-unit land coverage and two-anchor POI provider audit](../u1_developed_area_2026_09_22/README.md) now split SP no-use land into no raw lot versus raw lot without accepted use, test explicit mixed-label dominance, and diagnose unequal POI provider composition. The source-level sample above remains the baseline; its 20-point fractions were never exact area estimates.
