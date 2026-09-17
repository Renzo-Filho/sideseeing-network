# sideseeing-network

## Chicago analysis update

Chicago local-source attributes, updated data requirements and the execution handoff are documented in [docs/chicago/CHICAGO_EXECUTION_REPORT.md](docs/chicago/CHICAGO_EXECUTION_REPORT.md). Strict SP–Chicago harmonization remains a separate acceptance gate.


São Paulo district morphology and Brás similarity research.

- [Analysis workspace guide](analysis/README.md) — folder architecture and file roles.
- [Documentation map](docs/README.md) — current methods, status, handoff and historical material.
- [Completed São Paulo attributes](analysis/results/SP/README.md) — tables, map, report and validation.
- [Research plan](plan.md) — scope and methodology.

Attribute construction is complete; a primary SP similarity model has been implemented and independently reproduced, with the reported defects corrected and the v2 release validated.

[Attribute documentation](docs/sp/ATTRIBUTE_DOCUMENTATION.md) — definitions, input processing, formulas, all 77 columns, and limitations.

[Urban model implementation plan](docs/archive/plans/URBAN_MODEL_IMPLEMENTATION_PLAN.md) — proposed N11 preprocessing, family distances, Brás comparisons, robustness tests and deliverables; the primary implementation now exists; see the v2 corrections report for completed modeling and robustness work.

[SP model validation](docs/archive/audits/SP_MODEL_VALIDATION.md) — reproduced baseline ranking, identified defects and remaining acceptance work.

[Corrected SP model](docs/sp/SP_MODEL_FIXES.md) · [Chicago harmonization plan](docs/chicago/CHICAGO_HARMONIZATION_PLAN.md).

## Development

Use Python 3.12. `pyproject.toml` declares the project dependencies; `analysis/requirements.txt` records the exact tested environment used by the published releases. Run the repository tests with:

```bash
.venv/bin/python -m unittest discover -s analysis/tests -v
```
