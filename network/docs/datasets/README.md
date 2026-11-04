# Dataset organization plan: Brás and hospitals

Status: **proposal and source inventory, 21 October 2026**. No Drive or RustFS data was moved while preparing this plan; transfers subsequently started by the user are outside this document's verified state. The migration should be reviewed against the inventory and mapping below. This page is the handoff for another agent.

For expected duration, bottlenecks and a small measured pilot before copying, see [Brás transfer preflight](TRANSFER_PREFLIGHT.md).
For a read-only survey of the other collections in the shared `datasets` Drive folder, see [Other datasets](OTHER_DATASETS.md).

## Scope and existing conventions

The network collection protocol requires original MultiSensor folders and their contents to remain intact; derived outputs belong outside raw folders ([collection protocol](../COLLECTION_PROTOCOL.md), [pilot data plan](../archive/PILOT_DATA_PLAN.md)). `analysis/data/` has a separate register for model inputs, so this plan concerns field captures and their direct derivatives, not a reorganization of the model-input register.

RustFS bucket root at the initial 21 October check: `chicago/west-loop/` contained four 2026 capture folders directly; `sao-paulo/bras/` was empty then. These paths set the city and area spelling convention. Do not migrate the West Loop captures as part of this planning task.

Sources inspected:

| Source | Access used | Role |
|---|---|---|
| [Brás: `2025_Auditoria_Calcadas`](https://drive.google.com/drive/folders/1cIKFRLeKXzYAJ7VakP9dHFL1T3GKDzrV) | Connected Drive account and the local `gdrive:` rclone remote | **Only source for the proposed Brás copy** |
| [Shared `datasets` folder](https://drive.google.com/drive/folders/18BhEPZwIDCP44HoxkpXShardOaw2r3Tr) | Signed-in `renzo.filho@usp.br` browser session | Hospitals; its Brás branch is incomplete and excluded |
| [RustFS `sideseeing` bucket](https://data.urbantk.org/rustfs/console/browser/?bucket=sideseeing) | Local `rustfs:` rclone remote | Proposed destination |

The connected Drive tool and current `gdrive:` remote use `renzofilho2004z@gmail.com` and cannot list the shared `datasets` folder; the USP browser session can. Before a bulk hospital transfer, arrange a USP-authorized rclone remote or grant that Gmail account read access. Never place credentials or rclone config contents in this repository.

For a fresh Brás object inventory, use the existing read-only remote and store the large result outside the repository:

```bash
rclone lsjson gdrive: --drive-root-folder-id 1cIKFRLeKXzYAJ7VakP9dHFL1T3GKDzrV --recursive --files-only --fast-list --hash > /tmp/bras-drive-inventory.json
```

The current USP Drive browser tab can inspect the shared tree, but it is not a bulk file inventory or a substitute for an authorized transfer connection. Do not include the local rclone configuration file, tokens or access keys in any handoff.

## What is in Drive

### Brás

A recursive metadata-only `rclone lsjson --hash` inventory of the Brás link found **72,572 files, 396.30 decimal GB**. This is source storage across original, copied and derived branches, not 396 GB of unique captures. A capture-level index is in [bras-captures.csv](bras-captures.csv). The Drive folder ID above is the root for every relative path in that CSV.

| Existing branch | Observed contents | Approx. size |
|---|---|---:|
| `00_dados_originais/MultiSensor/D1P1..D4P4/` | 16 route groups, 216 distinct timestamped capture folders; each has the same nine MultiSensor files (`video.mp4`, `gps.csv`, three sensor CSVs, `cell.csv`, `wifi.csv`, `consumption.csv`, `metadata.json`). Capture dates: 9 Nov (49), 10 Nov (66), 11 Nov (34), 16 Nov (67) 2025. | 169.66 GB |
| `00_dados_originais/gps_todos.csv` | Combined GPS table; whether it is an original export or an aggregate needs confirmation. | 0.004 GB |
| `02_videos_e_acelerometros/D1P1..D4P4/` | 216 folders, each with `video.mp4` and `accelerometer_filtered.csv`. All 216 videos have the **same capture ID and MD5** as the video in the corresponding original MultiSensor folder. The filtered CSVs are distinct derivatives. | 165.27 GB |
| `01_dados_processados/01_image_sequences/` | 216 capture-keyed directories with 68,063 JPEG frames. | 30.73 GB |
| `01_dados_processados/02_videos_low_res/` | 216 low-resolution MP4s plus one `._` sidecar file. | 29.90 GB |
| `01_dados_processados/03_gpkg_shapefiles/` | 216 top-level GPKGs, 216 `BKP_GPKG` files, 216 `BKP_CSVs` files. The backup CSVs match raw `gps.csv` by MD5. Only **28 of 216** same-named GPKG/main-backup pairs match by MD5; retain both sets until their lineage is understood. | 0.086 GB |
| `03_analises/` | Notebooks, `predictions_probs.csv`, an audit CSV, a GPKG, `errors_surface/` images and `report_images/`. | 0.647 GB |
| Root files | `20260303_auditoria_calcadas_bras.gpkg.zip`, `Filtro.ipynb`. | 0.004 GB |

Across the Brás Drive tree, 1,761 additional files fall into 1,738 identical-MD5 groups, accounting for about **164.85 GB** of repeated bytes. The 216 copied full-resolution videos are the main contributor. This is a metadata-based duplicate finding; it does not mean every same-named file is identical or that any source should be deleted. The Brás timestamped capture names are unique across the 216 original folders, but the `D#P#` route labels should still be recorded as provenance.

The requested Brás copy selects only four source branches from `2025_Auditoria_Calcadas`: original MultiSensor captures for `raw/`, `01_image_sequences/`, `02_videos_low_res/`, and `03_analises/auditoria_calcadas_bras.gpkg`. The GPKG is **41,578,496 bytes** with Drive MD5 `6dec61fd9be96bb6dfc216c3eab146e1` in the source inventory and will be named `auditoria_calcada_bras.gpkg` at the destination, exactly as requested. The source image directories and low-resolution video stems use compact timestamps such as `20251110-093203969`; all 216 compact IDs match the 216 original raw capture IDs after date/time formatting. Use the original hyphenated capture ID for their destination folder/file names. Other source material, including `02_videos_e_acelerometros/`, per-capture GPKGs, notebooks and the root GPKG ZIP, remains in Drive and is not mapped into this selected layout.

The selected copy is **70,224 files, 230.335 decimal GB** in the 21 October metadata snapshot: 1,944 raw files, 68,063 JPEG frames, 216 low-resolution videos and one GPKG. Recheck source metadata before an actual transfer.

### Hospitals

The shared `datasets` folder contains `sideseeing-hospital-2025/`, `sideseeing-hospital-missing-data-2025/`, and `sideseeing-hospital-snippets-2025/`. The main folder has `raw/`, `samples/`, `routes/`, `tasks/`, `loader.ipynb`, and `metadata.csv`. A sampled raw route folder has `video.mp4`, `video.gif`, `video.wav`, `labels.txt`, `metadata.json`, GPS and sensor CSVs, and `consumption.csv`. A sampled `samples/` folder has the same filenames; byte-level overlap with raw was **not checked**. `routes/` has `html/` and `png/`; `tasks/` includes `labeling/` and notebooks. The missing-data folder has `BATON_OLLRMC/` and `BATON_BRGB/`. The separate snippets source has `runs/`, `snippets/`, `snippets.tar.gz`, `loader.ipynb` and `metadata.csv`. Its `snippets/` branch contains numbered route-segment folders; one inspected folder (`052_Santos_CHE_Route_04_TO`) has `video.mp4`, `metadata.json`, GPS and sensor CSVs, and `consumption.csv`. These are companion sources, not separate confirmed campaigns. The relationship between snippets and raw captures still needs file-level verification.

The main hospital [`raw/` branch](https://drive.google.com/drive/folders/1kVOacWti1oshvAfuGJN6zNF0UU3G_hVO) contains **12 source site folders** and **51 immediately visible route/block folders**. Their exact source folder URLs are in [hospital-sites.csv](hospital-sites.csv). These 51 are physical route/block capture folders, not a count of labeled direction segments or files. Neither total file count nor completeness has been established.

| City for target path | Source site folder | Immediate route/block folders |
|---|---|---:|
| `sao-paulo` | `SaoPaulo_HC`, `SaoPaulo_HUUSP` | 2, 2 |
| `jundiai` | `Jundiai_HU`, `Jundiai_HSV` | 2, 5 |
| `santos` | `Santos_HM`, `Santos_CHE` | 5, 6 |
| `chicago` | `Chicago_UIH`, `Chicago_NMH`, `Chicago_RUCM` | 9, 8, 8 |
| `baton-rouge` | `BATON_OLLRMC`, `BATON_0MCG`, `BATON_BRGB` | 2, 1, 1 |

The Chicago metadata distinguishes `TO` and `FROM` route legs; other sites mix `Route` and `Block` names. A Jundiaí HSV site has five physical folders (`Block01` and `Route01`–`Route04`) while the visible metadata has nine labeled rows for it: the four routes each have `TO` and `FROM` rows, and the block has one. A metadata row therefore must not be counted as a separate raw capture. The source folder and the metadata both spell `0MCG` with a zero; whether that code was intended needs confirmation before renaming it. Preserve all original route/block folder names and record normalized labels separately. Do not infer a missing capture solely from an asymmetric route name; inspect the companion missing-data branch and `metadata.csv` first.

The Drive preview of the main hospital `metadata.csv` shows columns `name`, `geolocation_center`, `media_start_time`, `media_stop_time`, `media_total_time`, `video_frames`, `video_fps`, `video_resolution`, `manufacturer`, `model`, and `so_version`. Its visible rows include capture dates in **2024** (February through August) despite the `-2025` dataset folder name; treat `2025` as a source collection label until the campaign dates are verified. The preview exposes only the first **49 data rows** through `Santos_CHE_Route_03_TO`, so it is not a complete metadata inventory. The timestamp strings do not state a time zone. The visible `BatonRouge_0MCG_Route_01_FROM` row corroborates the Baton Rouge city mapping and the zero character in that source code.

Companion folder entrypoints: [hospital `samples/`](https://drive.google.com/drive/folders/1RfWeeHbpLOJEQcR38fG_l1fmli4sAXyJ), [hospital `routes/`](https://drive.google.com/drive/folders/1p2YZ6rTFAmLiWQX2MuA_rJQZWMsTrkeJ), [hospital `tasks/`](https://drive.google.com/drive/folders/1SrzRd5K0oZOt2p3W8HHsLnWOQebi3yfT), [hospital missing-data](https://drive.google.com/drive/folders/1DoQzIQ-8G7pkzPln-hTAaVwL6GevX_O8), and [hospital snippets](https://drive.google.com/drive/folders/16TnkSTck0NR4Sl7Ap0bSrMBv3aclfgvN).

### Excluded Brás source

The shared [`datasets/citizen-audit-sidewalks-sp-2025/`](https://drive.google.com/drive/folders/1uLgOVmEagpPy1xXEoKxu4k0RbP8040eq) branch contains some folders with the same capture names, but the user identified it as incomplete. Do not use it to fill or replace files from `2025_Auditoria_Calcadas`; it is outside this copy plan.

## Proposed RustFS architecture

Use lowercase ASCII **kebab-case** for structural folder names. Keep `sao-paulo/bras/` under the city root, with `raw/` and `processed/` as its only branches and with the exact selected contents below. Keep **all hospital material together under one bucket-root `hospitals/` folder**, including the main hospital dataset and its companion sources. Hospital city names belong inside `hospitals/raw/`; no hospital data goes under city roots. Do not rename original capture folders or their files. Record original spelling, accents, dates, site aliases and route codes in the local handoff files.

```text
sideseeing/
  chicago/
    west-loop/                      # existing captures; unchanged by this plan
  sao-paulo/
    bras/
      raw/<D#P#>/<original-capture-folder>/
      processed/
        image-sequences/<capture-folder>/
        videos-low-res/<capture-folder>.mp4
        auditoria_calcada_bras.gpkg
  hospitals/
    raw/<city>/<site-code>/<original-route-or-block-folder>/
    samples/                        # main hospital source branch
    routes/                         # route plans and maps
    tasks/                          # labeling and notebooks
    metadata.csv                    # main hospital metadata
    loader.ipynb                    # main hospital loader
    missing-data/                   # separate companion source
    snippets/                       # separate companion source, with its own metadata
```

For Brás, copy `00_dados_originais/MultiSensor/D#P#/<original-capture-folder>/` to `raw/D#P#/<original-capture-folder>/`. Map each compact source ID under `01_dados_processados/01_image_sequences/` to `processed/image-sequences/<original-capture-folder>/`, and each compact MP4 stem under `01_dados_processados/02_videos_low_res/` to `processed/videos-low-res/<original-capture-folder>.mp4`. Copy `03_analises/auditoria_calcadas_bras.gpkg` to `processed/auditoria_calcada_bras.gpkg`. Preserve source file names **inside** raw capture and image-sequence folders. Exclude the `._` sidecar and all other source branches from this selected copy; keep them in Drive. The destination GPKG spelling follows the user's requested name, while the source spelling is recorded here for verification.

For hospitals, `<city>` uses the same lowercase city spelling (`chicago`, `sao-paulo`, `jundiai`, `santos`, `baton-rouge`); `<site-code>` is the lowercase source code (for example `hc`, `uih`, `nmh`) until site identities are documented. Retain full source names and URLs in the local hospital mapping. The hospital `samples/`, `routes/`, `tasks/`, `metadata.csv` and `loader.ipynb` come from the main source folder; `missing-data/` and `snippets/` retain the two companion sources as separate branches within `hospitals/`. Keep each hospital capture folder intact on initial import, including any GIF, WAV or label file whose generation status is unknown; classify those files after provenance review.

`snippets/` is a **real Drive source**, containing smaller numbered route segments and supporting files; it is not a new naming convention or a required raw-capture folder. `catalog` was a proposed index of source paths, hashes and transfer status, **not a folder found in Drive**. It is removed from the RustFS layout for now; tracking files stay in this handoff (`network/docs/datasets/`; run logs in `network/data/_transfers/`). The existing West Loop folders remain at their current keys.

## Local tracking files

The current [Brás capture inventory](bras-captures.csv) and [hospital site mapping](hospital-sites.csv) live beside this plan, not inside RustFS. Before any bulk copy, extend local tracking with:

1. `datasets.csv`: stable dataset ID, city, area/study/site, campaign, owner/contact, source root URL/ID, destination prefix, date range, access level, status.
2. `captures.csv`: stable physical capture ID, original folder and relative path, city/site, route or block label, date/time with **time zone verified separately**, device, source dataset, destination, status and quality notes. Do not equate filename time with a synchronized sensor clock.
3. `segments.csv`: hospital metadata `name`, parent physical capture ID, `TO`/`FROM`/block label, media start and stop times, geolocation center, video properties and device fields. One physical route folder can have more than one metadata row.
4. `objects.csv`: source file ID/path, intended role (`raw`, `processed`, `samples`, `routes`, `tasks`, `missing-data`, `snippets`, or `unclassified`), size, available Drive checksum, destination key, transfer and verification result. Record unavailable checksums explicitly.
5. `overlaps.csv`: hospital source paths/IDs that may repeat between raw, samples and snippets, match type (`name`, `size`, `hash`, or `content`), and the decision for each copy. The incomplete second Brás link is excluded.

## Migration sequence and gates

1. Freeze a read-only inventory of the four selected Brás branches in `2025_Auditoria_Calcadas`. Use that folder alone as the source; the other Brás link is incomplete and excluded. The capture CSV here is a starting snapshot, not an exhaustive object manifest.
2. Record the verified one-to-one compact-to-original ID mapping for all 216 image directories and 216 low-resolution videos in a local object manifest. Recheck the GPKG's source size and checksum before copying.
3. Copy a small representative capture first and verify file count, size, available checksums and readability. Then copy the selected Brás branches with resumable rclone jobs, preserving raw capture contents.
4. Compare the destination inventory with the frozen selected-source inventory. Full-resolution videos and other multipart objects may lack an S3 MD5; record the actual verification method and use a streamed content check for critical exceptions before declaring byte identity. Keep Drive originals intact.
5. Update project references to the new Brás locations after verified transfer. Hospital migration requires a separate USP-authorized inventory and remains a separate step; West Loop remains outside this migration.

Brás copy completion means every selected source object has the destination key shown above and passed verification, and no raw folder contents changed. The hospital totals and relationships among `raw/`, `samples/` and `snippets/` are still unverified.

## Factual questions before bulk copy

- Confirm the intended public-facing identity of hospital site `BATON_0MCG` and any desired hospital names. The source folder and metadata use a zero, so preserve `0mcg` as the storage code until a documented correction is approved.
- Read the complete hospital `metadata.csv` and labeling materials through a USP-authorized bulk-read path. The browser preview shows the schema and first 49 data rows only; reconcile every segment to its physical capture folder and determine the complete date range.
- Obtain a USP-authorized bulk-read path for the shared `datasets` tree. The current `gdrive:` remote reaches the Brás link but not the hospital link.
