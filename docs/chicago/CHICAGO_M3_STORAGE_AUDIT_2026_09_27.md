# Chicago M3/M4 storage audit — 27 September 2026

## Decision before a citywide run

The proposed **2D candidate generation and manual repair ledger can be designed to fit the current disk**, but it must stream small geographic batches and enforce a storage budget. Do not download citywide LiDAR or retain full-resolution imagery for every block. The current filesystem has **13,908,897,792 bytes free (12.95 GiB)** and is 95% used. `/tmp`, Curio, and this repository are on the **same filesystem**; moving files among them does not create free space. No files were deleted in this audit.

| Directory | Measured disk use | Interpretation |
|---|---:|---|
| `/home/renzo/Documents/GitHub/curio` | ~50 GiB | Includes ~17.3 GiB of registered application artifacts, ~16 GiB of scratch data, ~6.8 GiB of Git history, and ~1.9 GiB of webpack cache. |
| This `sideseeing-network` repository | ~32 GiB | Includes ~16 GiB `analysis/data`, ~7.6 GiB `analysis/work`, ~6 GiB Git history, and ~1.7 GiB Python environment. |
| Current M3 classified-LAS working directory | ~2.2 GiB | Two downloaded LAS files; small analytical outputs and receipts are elsewhere. |
| Current M3 results directories | Generally <70 MiB each | Maps dominate these pilot outputs; vector/CSV result files are small. |

### Size of the proposed operation

The six locally cached Cook ROW and Road Edge extracts total **38.9 MiB of GeoJSON** across Community Areas covering **68.2 of 597.7 km²** (11.4% of Chicago's Community Area area). A simple area extrapolation gives **~341 MiB** of raw 2D source GeoJSON citywide. This is an order-of-magnitude estimate, not a peak-space guarantee: road density, halo overlap, exceptional districts, temporary geometry files, and repeated renderings can raise it. A compressed GeoParquet or GeoPackage candidate/repair table should be much smaller than a full-city orthophoto or point cloud; measure actual bytes and face counts after the first tenth of the city before setting a final budget.

The expensive scenario is **retaining 3D and imagery everywhere**. The two targeted Cook LAS tiles already occupy ~2.2 GiB, and the LiDAR pilot used only two tiles. The next citywide stage should therefore use 2D generation, an audit queue, and imagery viewed or cached only for selected cases. For flagged 3D cases, extract one LAS tile at a time, keep derived class/profile metrics and a small evidence image, then remove the raw tile after its receipt and hash have been recorded if it is no longer needed. Do not turn the entire point cloud or all orthophotos into a local citywide cache.

**Execution budget:** run one geographic batch at a time, retain a single canonical compressed block table plus repair ledger, and cap new persistent M3 files at **3 GiB** during the pilot. Keep **at least 8 GiB free**; stop and inspect before crossing that floor. The 3 GiB cap is a design constraint, not a measured citywide requirement. Start with about one tenth of the city and record source, temporary, candidate, image, and evidence sizes separately; revise the cap only from observed growth. Ensure global block IDs and seam stitching work without keeping every tile's intermediate polygon copy.

## Cleanup proposals, ranked

These are **proposals only**. Curio is outside this task's writable workspace, and its application data must be cleaned with its references intact.

| Priority | Candidate | Potential recovery | Condition / cost |
|---|---|---:|---|
| 1 | Curio frontend webpack cache: `/home/renzo/Documents/GitHub/curio/utk_curio/frontend/urban-workflows/node_modules/.cache/webpack` | ~1.9 GiB | Generated build cache; will rebuild when Curio frontend runs. No Curio/webpack process was seen during this audit. |
| 2 | This repository's two raw LAS files in `analysis/work/chicago_m3_lidar_point_pilot_2026_09_26/` | ~2.14 GiB | Keep the small results, receipts, hashes, scripts and figures. Reproducing point-level tests later requires re-downloading the two 633.7/764.9 MB compressed ZIP members and extracting them. Preserve if the immediate next run needs point-level checks. |
| 3 | This repository's old `.git/objects/pack/tmp_pack_*` files | ~1.10 GiB | Five temporary pack files date from 10–14 September; no Git packing process was observed. Verify Git is idle and repository integrity before removal. **Do not delete normal `pack-*.pack` files.** Curio has a further ~0.09 GiB old temporary pack. |
| 4 | Curio's `.curio/data/artifacts` repeated large Parquet payloads | Up to **16.09 GiB** without losing distinct bytes | 27 files of 417.6 MiB have one identical SHA-256; 37 files of 156.0 MiB have another identical SHA-256. All but two tiny artifact files are registered in Curio's DuckDB catalog. Do **not** unlink them wholesale. First determine whether old sessions can be pruned through Curio. If all paths must remain, consider a separately reviewed byte-identical deduplication preserving every filename and database reference, with Curio stopped and a rollback plan; hard links are unsafe if any payload is edited in place. |
| 5 | Curio `scratch_data` copies of source files already in this repository | At least **8.16 GiB** among three verified examples | SHA-256 confirms identical independent copies of SP building morphology (4.37 GiB), Chicago building permits (2.76 GiB), and Chicago building footprints (1.03 GiB). The footprint file also appears in Curio's catalog and installed user dataset copies. Map Curio path dependencies before replacing a scratch copy with a reference to the canonical source; do not remove catalog-installed data solely because its bytes match. Other scratch copies may add savings after checksums. |
| 6 | Curio's `.curio/test-large-df-data` | ~0.11 GiB | Test output, likely regenerable; inspect test needs before removal. |

Large directories **not recommended for direct deletion**: either repository's normal `.git/objects/pack/pack-*.pack` files; Curio's entire `.curio/data/artifacts` directory or DuckDB catalog; either repository's active virtual environment; source data referenced by model scripts; and reference annotations, adjudication ledgers, receipts or compact QA reports. The `sideseeing-network` SP morphology file is referenced by several scripts, so its presence should be preserved unless those paths are intentionally migrated.

## Evidence and measurement notes

- `df -B1` on the repository returned 13,908,897,792 available bytes; both projects share the same device.
- `du -x` found Curio ~50 GiB and this repository ~32 GiB. `du` totals are rounded and nested directories must not be added to their parents.
- Curio's artifact directory has 1,293 files totaling 17.32 GiB; the DuckDB `artifacts` table has 1,396 rows. Of filesystem files, only two small files totaling 356,602 bytes lacked a matching artifact ID. The large repeated payloads are registered outputs of `curio.builtin/data-loading` and `data-loading@1`, not orphaned scratch files.
- SHA-256 was calculated for all 64 large repeated Curio artifacts. It found two exact-content groups, with 26 + 36 redundant physical copies; their combined deduplication opportunity is 16.09 GiB.
- SHA-256 was also checked for the three named Curio/`sideseeing-network` duplicate source examples; filenames, lengths and digests match. They are separate inodes with link count 1, so they currently consume separate space.
- This audit is read-only. A future cleanup should record before/after `df`, preserve path and content manifests, and perform application-level smoke checks.
