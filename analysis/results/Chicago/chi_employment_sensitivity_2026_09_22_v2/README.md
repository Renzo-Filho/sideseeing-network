# Chicago workplace-allocation sensitivity v2 — September 22, 2026

Completed both scenarios for all 14,990 positive-job Census blocks. **138 independent audit checks passed, zero failed**, including 16 stratified independent geometry reconstructions. This is an extended diagnostic, not acceptance of RAIS–LODES equivalence.

The September 17 v1 partial run is preserved. Its resumed computation stopped at block `170310707001004` because a roughly 0.0001 m² polygon-overlay residual exceeded the prior tolerance. Version 2 records each partition-area residual and normalizes only inside a bound of 0.001 m² plus 1e-7 of support area. Larger discrepancies still fail. Observed maximum absolute correction is 0.001215 m²; maximum relative correction is 3.071e-8. Jobs are conserved exactly to floating precision, without relocating unresolved source employment into Chicago.

| Scenario | Inside Chicago jobs | Outside residual jobs | Gross-area fallback blocks |
|---|---:|---:|---:|
| Business core | 1,408,280.585 | 49,982.415 | 5,817 |
| Business + transport/communications/utilities | 1,409,711.999 | 48,551.001 | 5,125 |

Both reconcile to 1,458,263 jobs in whole intersecting positive-job blocks. Land-use support includes outside-city parts of those blocks. Fourteen blocks have under 99% CMAP coverage; very small positive supports and large fallback shares remain limitations. Primary use only; conflicting distinct use-code overlaps are excluded. Jobs are 2022, CMAP use is 2023, and geographic blocks are Census 2020 in TIGER 2022.

Files: `tables/district_job_sensitivity.csv`, `tables/mass_and_fallback_summary.csv`, `validation/independent_checks.json`, and `validation/source_code_manifest.json`. Detailed allocations and residuals remain in ignored `analysis/work/prepared/Chicago/chi_employment_sensitivity_2026_09_22_v2/`.

```bash
.venv/bin/python analysis/scripts/prepare_chicago_employment_sensitivity_v2.py
.venv/bin/python analysis/scripts/validate_chicago_employment_sensitivity_v2.py
```

Existing Chicago functional v2 and original SP releases remain unchanged. Paired-stage decisions are documented in `docs/chicago/SP_CHICAGO_HARMONIZATION_EXECUTION.md`.
