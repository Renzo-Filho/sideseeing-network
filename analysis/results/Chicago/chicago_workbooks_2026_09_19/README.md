# Chicago commercial workbook checkpoint — extracted September 19, documented September 21, 2026

Firecrawl retrieved table contents from all eight official 2024 Chicago commercial valuation workbooks. Direct XLSX downloads returned HTTP 403, so **original workbook binaries were not acquired**. These are saved text extractions, not fully validated Excel files.

The [official report index](https://www.cookcountyassessoril.gov/valuation-reports) links each township page below. All sources concern first-pass 2024 valuation inputs, not necessarily current buildings or final post-appeal characteristics. The revised Hyde Park filename includes 12-09-2025; its filename is not proof of the actual observation date.

| Source page / workbook | Chicago detail rows | Unique key PINs | Key PINs absent from API extract |
|---|---:|---:|---:|
| [2024.T75.PublicModel TJS_RPSC.xlsx](https://www.cookcountyassessor.com/rogers-park-2024-commercial) | 1,153 | 1,129 | 0 |
| [2024.T77.PublicModel_2.xlsx](https://www.cookcountyassessor.com/west-chicago-commercial-valuations) | 7,166 | 7,082 | 2 |
| [2024.T71.PublicModel.xlsx](https://www.cookcountyassessor.com/jefferson-commercial-valuations) | 6,394 | 6,291 | 1 |
| [2024.T74.PublicModel.xlsx](https://www.cookcountyassessor.com/north-chicago-commercial-valuations) | 1,749 | 1,735 | 97 |
| [2024.T76.PublicModel.xlsx](https://www.cookcountyassessor.com/south-chicago-commercial-valuations) | 2,045 | 2,035 | 2 |
| [2024.T72.PublicModel.xlsx](https://www.cookcountyassessor.com/lake-commercial-valuations) | 5,300 | 5,247 | 0 |
| [2024.T73.PublicModel_LV.xlsx](https://www.cookcountyassessor.com/lake-view-commercial-valuations) | 4,229 | 4,146 | 0 |
| [2024.T70.PublicModel 12-09-2025.xlsx](https://www.cookcountyassessor.com/hyde-park-commercial-valuations) | 4,195 | 4,140 | 1 |

## Validation and usefulness

- Parsed 72 property tables across eight extracts; summary and split-class repeat tables were excluded from the detail output.
- Retained **32,231 Chicago-linked detail records**, representing **31,805 unique key PINs**. Every retained row has a normalized PIN10 matching the spatially validated Chicago Cook parcels.
- All **31,702 unique key PINs** in the prior commercial API extract appear in these detail records. There are **103 additional key PINs**, mostly in North Chicago (97). These are additional valuation keys, not proof of 103 newly identified physical buildings.
- `Bldg SF` is nonempty on **30,268 records**; `Net Rentable SF` on **5,987**. These are display-string presence counts, not positive numeric coverage or reconciled gross floor area.
- No stories or explicitly gross-floor-area column was found in the extracted property-table headers. These workbooks therefore do not close B2 exact floors or B3 gross-area semantics. Building/rentable area can help B3 reconciliation; use/classes and related PINs can help U1/M7.
- One Lake Township row has no PIN and contains repeated `E` values. It was excluded and its location retained in `validation.json`. No column-count mismatch was recorded.
- Original binary, hidden sheets, formulas, formatting and parser completeness cannot be independently verified. Coverage against API key PINs supports usefulness but does not establish complete workbook reproduction. Differences in row counts also reflect repeat-table exclusion and possible source revisions.

## Saved data and provenance

Chicago-only extracted detail records: `analysis/data/Chicago/chicago_workbooks_2026_09_19/chicago_detail_records.jsonl`. Each row retains the source URL, filename, sheet, source-text line, matched Chicago PINs and displayed fields. The adjacent manifest records its SHA-256 hash. Related commercial entities can cross the city boundary; their area values have not been allocated to Chicago.

Raw text extracts: `.firecrawl/chicago-commercial-workbooks-2026-09-19/` (Git-ignored). `workbook_register.json` contains all direct download URLs and extraction hashes; `downloads.json` preserves failed binary requests; `sheet_validation.json`, `file_summary.json` and `validation.json` provide table/field/count evidence. Reproduction entry point: `analysis/scripts/validate_chicago_workbook_extracts.py`.

Next: compare the additional/revised area records cautiously if needed; prioritize DuPage improvement records and other sources for missing exact stories/GFA. Do not substitute building SF for GFA or count duplicate valuation rows as buildings. Modeling remains paused.
