# São Paulo documentation

Start with [SP_MODEL_FIXES.md](SP_MODEL_FIXES.md) for the current corrected model status and [SP_DATA_RESOLUTION_HANDOFF.md](SP_DATA_RESOLUTION_HANDOFF.md) for preparation lineage, artifact locations and source limitations.

- [SP_ATTRIBUTE_IMPLEMENTATION_PLAN.md](../archive/plans/SP_ATTRIBUTE_IMPLEMENTATION_PLAN.md) — v3 definitions and ordered N01–N11 next tasks; integration and attribute stages clearly distinguished.
- [SP_METHOD_DECISIONS.md](SP_METHOD_DECISIONS.md) — issue/cause/action/validation report, approved M6/M2 rules, and results of ten U2 allocation experiments.
- [BUILDING_PIPELINE.md](BUILDING_PIPELINE.md) — retained technical reference for the completed Overture GeoPackage.
- [Research protocol](../../plan.md) — SP-first research scope, later Chicago comparison and separate accessibility study.

The active model has 13 families; M5 and U5 are removed. B2 targets cadastral floor counts, U2 formal employment and U4 service-weighted bus access. M2 uses the approved 5 m structure-exclusion proxy; M6 uses the approved all-unclassified-as-Local overlay. N10 attribute construction is complete for all 96 districts. The corrected SP similarity model v2 is also complete, independently revalidated and supported by 577 robustness scenarios.

Four superseded status reports were removed after consolidation into the current handoff. Historical evidence and prepared data remain unchanged. Use `analysis/scripts/prepare_sp_v3.py`; do not run the old hard-coded v2 pipeline on the expanded raw folder.

Current [attribute construction report](../../analysis/outputs/sp_attributes/sp_attributes_2026_09_11_v1/REPORT.md) and [primary table](../../analysis/outputs/sp_attributes/sp_attributes_2026_09_11_v1/attributes_primary.csv). The long table contains the required source/quality metadata.

[Urban model implementation plan](../archive/plans/URBAN_MODEL_IMPLEMENTATION_PLAN.md) — archived N11 design specification retained for implementation history.
