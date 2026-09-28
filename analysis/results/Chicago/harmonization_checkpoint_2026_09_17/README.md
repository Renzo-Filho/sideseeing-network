# Harmonization checkpoint — 17 September 2026

**50 audit checks passed, zero failed; 41 repository tests passed.** This independently audits the existing paired road candidates and Chicago footprint pilots. It does not accept a common model or generate rankings. Existing numerical releases were read, not rewritten.

## What was checked

Both cities' complete qualified-ID universes, road-density numerators/denominators, nine nonnegative unit-sum class shares, city totals, separate class inventories and connector accounting reconcile. All acceptance flags remain false.

All five Chicago pilots were independently reconstructed for **both** Overture and municipal footprints: union whole intersecting objects without tiles, then clip to gross and hydro-land support. All 20 area comparisons passed; maximum difference from the tiled construction was below 0.0000001 m². Numerators, denominator reconstruction and bounds also passed.

The functional release's registered numeric artifacts retain their hashes. One historical checksum differs: its `README.md`, whose links were updated during the documentation reorganization. This is recorded as document drift, not silently re-signed or treated as changed measurements. The historical checksum manifest remains intact.

## Substantive findings and limits

| Chicago pilot | Overture minus municipal hydro-land coverage, percentage points |
|---|---:|
| West Town (24) | +1.5522 |
| Near West Side (28) | +1.8878 |
| South Lawndale (30) | −0.5088 |
| Loop (32) | +1.9898 |
| O'Hare (76) | +0.3909 |

The arithmetic is reproducible, but these differences do not establish which source is complete or current. Review omissions, additions, ancillary structures and hydrography before accepting B1.

Unknown road class represents 1.4627% of selected Chicago length and 2.0065% in SP. Unclassified represents a further 1.6992% and 2.0555%, respectively. Do not merge these into Local without an explicit shared policy. Access-rule fields occur on 26,732/53,687 selected Chicago records and 60,600/190,090 SP records. Field presence does **not** mean a road is private or impassable; conditional rules still need interpretation. Connector counts remain unvalidated physical-intersection candidates.

## Reproduce

From repository root:

```bash
.venv/bin/python analysis/scripts/audit_harmonization_checkpoint.py
.venv/bin/python -m unittest discover -s analysis/tests -v
```

The audit takes existing releases and prepared data as input and writes only this separate checkpoint. It does not rerun acquisitions, road construction, or functional publication. `input_code_checksums.json` binds audit inputs/code; `checks.json` records every result; CSVs expose the reconstruction and policy diagnostics. `repository_tests.log` records the current test run.

## Exact next task

Start the **U2 CMAP business-area sensitivity** in a new release/config. Inspect the full raw CMAP schema/classification and freeze employment-support categories. Read land-use records over the **whole intersecting Census blocks**, including outside-city pieces; do not rely only on the city-selected cache. Union support, expose ambiguous area, allocate whole-block C000 over district/outside business support, and use flagged gross-area fallback for zero support. Conserve every block's jobs, preserve all outside/unmatched/fallback mass, compare against the frozen area baseline, and test synthetic border/overlap/zero-support cases. Keep it extended-only pending LODES/RAIS universe equivalence.

Afterward: shared road access/service/pedestrian/ramp policy and topology fixtures; physical blocks; full-city B1 and matched SP companions; cadastral/use semantics; finally a frozen common-feature contract before rankings.

The user asked for an early quota stop. No large next pipeline was started and no background work remains. Last usage snapshot before documentation wrap-up: 36% five-hour and 29% weekly remaining (account-wide, subject to change).
