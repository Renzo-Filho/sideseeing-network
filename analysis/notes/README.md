# São Paulo documentation

Start with [SP_DATA_RESOLUTION_HANDOFF.md](SP_DATA_RESOLUTION_HANDOFF.md): current source status, completed work, remaining decisions, artifact locations and agent-resumption instructions.

- [SP_ATTRIBUTE_IMPLEMENTATION_PLAN.md](SP_ATTRIBUTE_IMPLEMENTATION_PLAN.md) — v3 definitions and ordered N01–N11 next tasks; integration and attribute stages clearly distinguished.
- [SP_METHOD_DECISIONS.md](SP_METHOD_DECISIONS.md) — issue/cause/action/validation report, approved M6/M2 rules, and results of ten U2 allocation experiments.
- [BUILDING_PIPELINE.md](BUILDING_PIPELINE.md) — retained technical reference for the completed Overture GeoPackage.
- [Research protocol](../../plan.md) — SP-first research scope, later Chicago comparison and separate accessibility study.

The active model has 13 families; M5 and U5 are removed. B2 now targets cadastral floor counts, U2 formal employment and U4 service-weighted bus access. New data are integrated in the isolated v3 preparation run; acceptance is family-specific. M2 is approved as the 5 m structure-exclusion proxy; M6 uses the approved all-unclassified-as-Local overlay. Ten U2 experiments are complete; area-first U2 is selected. N10 attribute construction is complete for all 96 districts; no similarity model has been fitted.

Four superseded status reports were removed after consolidation into the current handoff. Historical evidence and prepared data remain unchanged. Use `analysis/scripts/prepare_sp_v3.py`; do not run the old hard-coded v2 pipeline on the expanded raw folder.

Current [attribute construction report](../outputs/sp_attributes/sp_attributes_2026_09_11_v1/REPORT.md) and [primary table](../outputs/sp_attributes/sp_attributes_2026_09_11_v1/attributes_primary.csv). The long table contains the required source/quality metadata.

[Urban model implementation plan](../URBAN_MODEL_IMPLEMENTATION_PLAN.md) — detailed proposed N11 design and execution stages; no model fitted.
