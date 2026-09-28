# Manual acquisition: remaining Chicago building data

Updated September 21, 2026. Validation and modeling are paused at the user's request. The following are acquisition instructions; no requests have been sent and no subscription purchased.

Save received files in `analysis/data/Chicago/manual_acquisition_2026_09_21/incoming/`, retaining their original names. The available public baseline datasets are already downloaded; there is no need to download them again.

## 1. Addison / DuPage — first priority

Open [Addison Property Search](https://www.addisontownship.com/property-search/), follow its database link, and search **0301100003** (industrial) first, then **0301200006** (leasehold). The [direct lookup](https://search.addisontownship.com/webdb/sd/addison/assessordb/search.aspx) accepts parcel numbers with or without dashes. Our earlier browser attempt stalled without a record result; this does not mean the parcel is absent.

On each matching record, download any available property record card, building/improvement details and sketch. If only a displayed detail page is available, use the browser's Print → Save as PDF. Include all pages/tabs that show stories, building area and area units/definition. Save as `<PIN>_record.pdf` (and `<PIN>_sketch.pdf` if separate). Do not save only a tax-bill/value summary; it lacks the physical attributes needed.

Start with those two records rather than manually repeating all 81 searches immediately. The exact [81-PIN list](../../analysis/data/Chicago/manual_acquisition_2026_09_21/addison_chicago_81_parcels.csv) is prepared for a batch export or later lookups. Most are exempt/airport parcels, so a residential-only dataset is insufficient.

If the lookup lacks cards or export, use the [Assessor's Office page](https://www.addisontownship.com/assessors-office/) or [county township directory](https://www.dupagecounty.gov/government/departments/supervisor_of_assessments/township_assessor_directory.php) to contact the responsible office. Ready-to-copy [Addison request text](../../analysis/data/Chicago/manual_acquisition_2026_09_21/addison_request.txt) specifies the exact records/fields and accepts an available vintage if 2024 is unavailable. Attach the 81-PIN CSV. Requested formats are preferences, not claims that those exports already exist.

**Addresses:** missing DuPage building stories, constructed area and improvement relationships (B2/B3/M7), with use information supporting U1.

## 2. Cook County — missing physical building characteristics

Use the official [data-subscription page](https://www.cookcountyassessoril.gov/data-subscription), which offers subscription inquiry, subscriber access and an official records-request route. The page does not publish a freely downloadable file that resolves the missing fields. Availability of exact stories and GFA in the subscription service is **not confirmed**; ask before purchasing anything.

Use [Cook request text](../../analysis/data/Chicago/manual_acquisition_2026_09_21/cook_request.txt) and attach [Chicago PIN scope ZIP](../../analysis/data/Chicago/manual_acquisition_2026_09_21/cook_chicago_pin_scope.zip). The ZIP contains the already acquired Chicago-linked tax PINs and PIN10 grouping keys; preserve leading zeros. This avoids requesting the whole county.

Needed: exact stories/floors; defined gross/constructed area; condo unit/building areas; physical building/card/parent keys; multi-parcel relations; and exempt/institutional stock coverage. Ask for the existing data dictionary and effective date. A new copy of the public commercial valuation table will not resolve its empty stories/GFA fields.

Official routes: [subscription inquiry/contact](https://www.cookcountyassessoril.gov/contact) and [FOIA information](https://www.cookcountyassessoril.gov/foia-freedom-information). Submit only if you choose; nothing has been sent on your behalf.

**Addresses:** remaining Cook B2/B3 gaps and M7 physical-parent relationships; use fields support U1.

## 3. Original commercial workbooks — optional, lower priority

Direct downloads returned HTTP 403 from the publisher's CloudFront file server. Firecrawl already extracted their visible table content, so retrieving the original XLSX files would recover originals/formulas but is **not known to fill the missing stories/GFA fields**. Prioritize items 1–2 above.

If your browser can download them, open the official [2024 Chicago valuation reports](https://www.cookcountyassessoril.gov/valuation-reports) and use each township's Commercial → Methodology Worksheets link. Exact links:

| Original filename | Direct XLSX | Publisher page |
|---|---|---|
| 2024.T75.PublicModel TJS_RPSC.xlsx | [Download](https://prodassets.cookcountyassessoril.gov/s3fs-public/reports/2024/2024.T75.PublicModel%20TJS_RPSC.xlsx) | [Report](https://www.cookcountyassessor.com/rogers-park-2024-commercial) |
| 2024.T77.PublicModel_2.xlsx | [Download](https://prodassets.cookcountyassessoril.gov/s3fs-public/reports/2024/2024.T77.PublicModel_2.xlsx) | [Report](https://www.cookcountyassessor.com/west-chicago-commercial-valuations) |
| 2024.T71.PublicModel.xlsx | [Download](https://prodassets.cookcountyassessoril.gov/s3fs-public/reports/2024/2024.T71.PublicModel.xlsx) | [Report](https://www.cookcountyassessor.com/jefferson-commercial-valuations) |
| 2024.T74.PublicModel.xlsx | [Download](https://prodassets.cookcountyassessoril.gov/s3fs-public/reports/2024/2024.T74.PublicModel.xlsx) | [Report](https://www.cookcountyassessor.com/north-chicago-commercial-valuations) |
| 2024.T76.PublicModel.xlsx | [Download](https://prodassets.cookcountyassessoril.gov/s3fs-public/reports/2024/2024.T76.PublicModel.xlsx) | [Report](https://www.cookcountyassessor.com/south-chicago-commercial-valuations) |
| 2024.T72.PublicModel.xlsx | [Download](https://prodassets.cookcountyassessoril.gov/s3fs-public/reports/2024/2024.T72.PublicModel.xlsx) | [Report](https://www.cookcountyassessor.com/lake-commercial-valuations) |
| 2024.T73.PublicModel_LV.xlsx | [Download](https://prodassets.cookcountyassessoril.gov/s3fs-public/reports/2024/2024.T73.PublicModel_LV.xlsx) | [Report](https://www.cookcountyassessor.com/lake-view-commercial-valuations) |
| 2024.T70.PublicModel 12-09-2025.xlsx | [Download](https://prodassets.cookcountyassessoril.gov/s3fs-public/reports/2024.T70.PublicModel%2012-09-2025.xlsx) | [Report](https://www.cookcountyassessor.com/hyde-park-commercial-valuations) |

## What to return

Place downloaded records/exports and any supplied dictionary in the `incoming/` directory. For a manual property lookup, two initial record cards are enough to establish what the site provides before doing all 81. For an office response, keep its dataset description, effective date and usage terms alongside the files. Do not send account passwords or subscription credentials.

## Acquisition status

This pass searched official acquisition routes and prepared scoped lists/request text. It did **not** acquire new building-characteristic records, rerun data validation, or resume modeling. Actual failures are distinguished above: Addison browser lookup stalled; workbook binaries returned 403; Cook's additional-data route requires inquiry/subscriber access rather than offering a known public file.
