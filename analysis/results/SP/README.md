# São Paulo — completed district attributes

**Start with [attributes_primary.csv](tables/attributes_primary.csv)** and the [construction report](reports/ATTRIBUTE_REPORT.md).

| Location | Contents and use |
|---|---|
| [tables/attributes_primary.csv](tables/attributes_primary.csv) | 96 districts × 23 raw primary candidates, plus ID/name; use for initial exploration |
| [tables/attributes_wide.csv](tables/attributes_wide.csv) | All 77 numeric attribute, diagnostic and sensitivity columns; Parquet equivalent alongside it |
| [tables/attributes_long.parquet](tables/attributes_long.parquet) | 7,392 district/feature records with units, numerator/denominator, coverage, quality, period and method; CSV equivalent alongside it |
| [tables/attribute_dictionary.csv](tables/attribute_dictionary.csv) | Feature definitions, units and primary flags |
| [spatial/sao_paulo_district_attributes.gpkg](spatial/sao_paulo_district_attributes.gpkg) | 96 district polygons with all attributes; EPSG:31983 |
| [reports/ATTRIBUTE_REPORT.md](reports/ATTRIBUTE_REPORT.md) | What was built, purpose, methods, issues/fixes, validation and remaining work |
| [figures/pilot_attribute_qa.png](figures/pilot_attribute_qa.png) | Brás, Itaim Bibi and Grajaú pilot comparison |
| [validation/tables](validation/tables) | Outlier review, feature ranges, quality summaries and population-support checks |
| [validation/checks](validation/checks) | JSON validation evidence; generally read the report instead |

Read IDs with `dtype={"district_id": str}` to preserve leading zeros. Brás is `10`. These attribute tables remain unscaled. A separate primary similarity model now exists, with the original validation issues corrected in v2. M5/U5 are excluded. U2 retains 508,844 unlocated jobs outside primary totals; the six M6 class shares are dependent. Review source/proxy metadata before modeling.

Release: `sp_attributes_2026_09_11_v1`. Final files have one physical copy; original pipeline paths link to them. The readable report is a small copy of the frozen report with links adjusted to this layout. Full execution provenance and intermediate calculations are under [work/runs](../../work/runs/README.md). To resume research, use the [handoff](../../notes/SP_DATA_RESOLUTION_HANDOFF.md) and [implementation plan](../../notes/SP_ATTRIBUTE_IMPLEMENTATION_PLAN.md).

[Attribute documentation](../../ATTRIBUTE_DOCUMENTATION.md) — definitions, input processing, formulas, all 77 columns, and limitations.

[Urban model implementation plan](../../URBAN_MODEL_IMPLEMENTATION_PLAN.md) — proposed N11 preprocessing, family distances, Brás comparisons, robustness tests and deliverables; the primary implementation now exists; see the v2 corrections report for completed modeling and robustness work.

[SP model validation](../../SP_MODEL_VALIDATION.md) — reproduced baseline ranking, identified defects and remaining acceptance work.

[Corrected SP model](../../SP_MODEL_FIXES.md) · [Chicago harmonization plan](../../CHICAGO_HARMONIZATION_PLAN.md).
