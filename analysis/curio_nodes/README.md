# Chicago feature-construction dataflow in Curio

This directory holds the Python code installed in the saved Curio project
`b4a2907d-bf08-469f-a4d5-761f59c9f531` and the script that arranges its
canvas. The canvas contains feature construction and a separate Chicago-only
candidate model path. The map and chart nodes are parked for a later stage.

## Visual layout

Each lane has its own small source loaders, one source merge, feature nodes,
and one result merge. The final collector receives only three results:
morphology, built form, and urban function. No node has more than five outgoing
edges. All source loaders return catalog **paths**, not loaded GeoDataFrames.

| Lane | Source merge output (`arg`) | Direct consumers | Dependent consumers |
|---|---|---|---|
| Morphology | `[community areas, Overture roads/connectors, municipal streets]` | M1, M2, M3 | M1 → M6; M3 → M4 |
| Built form | `[community areas, hydrography, footprints/GHSL, Cook records]` | M7, B1, B2, B3, BV | — |
| Urban function | `[community areas, Census support, CMAP land use, CTA GTFS]` | U1, U2, U3, U4 | — |

Node prompts should address **one feature node at a time** and begin by
confirming the listed input slots. The result merges and final collector only
organize outputs; they do not fit or evaluate a model.
Copy-ready prompts for the next feature work are in [NEXT_CURIO_PROMPTS.md](README.md).

M1, M6, B1, BV, U1, U2, U3, and U4 construct 77 Community Area values. M2 is
connector-density diagnostic only. M3 and M4 are experimental mapped-street
enclosures, not accepted physical blocks. M7, B2, and B3 return explicit
unavailable states until the underlying parcel, reported-floor, and floor-area
entities are resolved. A constructed value is not a scientific acceptance
decision.

## Chicago-only candidate model

The model branch selects only M1/M6, B1/BV and U1/U2/U3/U4 from the existing
feature nodes. Three small selection merges feed a three-domain merge. Then
`model_matrix.py` joins the eight families, `model_fit.py` fits seven scalar
transforms and the M6 composition on Chicago, and `model_distances.py` computes
all 2,926 unordered area pairs. The three domains have equal budgets; their
families divide those budgets equally. This is
`chicago_only_8_family_candidate_v0`, a provisional descriptive model. It
excludes M2/M3/M4/M7/B2/B3 and makes no scientific acceptance claim.

`run_model_local.py` executes the selected features and three model stages
using installed Curio catalog files. `install_chicago_model.py` adds the model
branch under Curio's spec lock, with a backup and a concurrent-edit check.

`reorganize_graph.py --dry-run` reports the graph shape without changing the
saved project. The write mode acquires Curio's spec lock and backs up the prior
spec. `run_local.py FEATURE` constructs a named feature from the same installed
catalog files without performing model evaluation.

The local Curio server was launched with `--exec-parallelism 1` so the large
B1 and U1 geometry nodes do not run simultaneously. Preserve that setting
when restarting Curio for a full construction run.

## Next Curio prompts

## Next Curio agent prompts: Chicago feature construction

Use the saved dataflow `b4a2907d-bf08-469f-a4d5-761f59c9f531`. Send one prompt at a time to the agent inside the named **Feature** node. Each source bundle returns a list of dictionaries whose values are file paths, not loaded GeoDataFrames. Work only in that feature node. Preserve 77 `CHI:01`–`CHI:77` rows and explicit `status` and `reason` columns. These prompts construct or diagnose features; they do not accept features, fit a model, or perform a scientific evaluation.

### 1. Feature B2: construct the reported-stories subset diagnostic

> Work only in Feature B2. Its input is the built-form source bundle: `arg[0]['community_areas']` is the Community Area GeoJSON path, `arg[2]['city_building_footprints']` is the official Chicago building-footprint path, and `arg[3]` contains Cook assessor file paths. Build the *reported building stories* diagnostic from the official footprints, following `docs/chicago/CHICAGO_ATTRIBUTE_DOCUMENTATION.md`, section B2. Read the paths with GeoPandas, project to EPSG:26916, keep unique ACTIVE `bldg_id` buildings, dissolve duplicate geometry for an ID, and withhold any ID whose duplicated rows have conflicting `stories` reports. Assign each whole building to the Community Area with the largest polygon overlap. Only numeric `stories > 0` is an eligible report; zero, blank, nonnumeric and conflicting reports remain missing. Do not read `no_stories` as total floors: it records below-ground stories. Do not use `z_coord`, height in metres, `bldg_sq_fo`, or an imputed one story. Return exactly 77 rows with `unit_id`, eligible report count, all assigned ACTIVE building count, positive-report coverage, reported-subset median and P90, `status='reported_subset_diagnostic'`, and a reason stating that coverage and the building/entity population do not yet support an all-stock B2 feature. Keep the model-facing `value` null. First inspect and report the actual field names and value types; then write code in this node only. If a required field is absent, keep B2 unavailable and report the exact missing field instead of guessing.

### 2. Feature M7: inspect cadastral identity before counting

> Work only in Feature M7. Its built-form input has `arg[0]['community_areas']` and Cook parcel, universe, residential, condo, commercial and building paths in `arg[3]`. Inspect the actual schemas and source documentation for parcel geometry, PIN, parent/tieback and condominium relationships. Trace a few Loop condominium or multi-building parcels and a peripheral parcel through the available keys. Report the key cardinalities: parcel geometry to PIN, PIN to parent, parent to condominium unit, and parcel to building. State where a tax interest would multiply a physical parcel if rows were counted naively. Identify what portion of Chicago lacks DuPage coverage in this node. Then, only if a unique physical cadastral entity rule is supported by these files, implement a 77-row entity count per gross km² using whole-entity largest-overlap assignment and preserve unmatched/ambiguous counts. Otherwise keep `value` null for all 77 rows with `status='not_constructed_source_or_entity_gate'`, and return a compact diagnostic summary of the exact unresolved relationships. A count of PINs, parcel rows, footprints or condo units is not M7. Do not turn a Cook-only result into a citywide value.

### 3. Feature B3: inspect constructed-area meaning and duplicates

> Work only in Feature B3. Its built-form input has `arg[0]['community_areas']` and Cook residential, condominium, commercial, commercial-details, parcel and building file paths in `arg[3]`. Inventory the actual candidate area columns, their reported units, observation year, population covered, and keys. Show whether each candidate is living area, exterior area, rentable area, whole-building area or unit area, and whether a parent total repeats across condo rows. Inspect a small set of matched residential, condo and commercial records and identify duplicate paths before writing any sum. B3 means unique constructed floor area divided by Community Area land area; footprint coverage and GHSL height/volume are different features. If the supplied files do not establish one nonduplicated citywide area quantity covering residential, condo, commercial, exempt and DuPage stock, retain 77 rows with null `value`, `status='not_constructed_source_or_entity_gate'`, and a precise missing-source reason. Report any defensible subset calculation in separate diagnostic columns, never as B3. Do not sum incompatible area fields or fill missing stock with zero.

### 4. Feature M3: use the physical-face inventory when it is attached

Before this prompt, attach `analysis/results/Chicago/chicago_m3_provisional_faces_2026_09_27/global_provisional_faces.parquet` and `global_review_queue.csv` from the same directory as Curio datasets, then connect both **paths** through the Morphology source bundle. Preserve the current M3 and M4 nodes and their M3→M4 edge. The existing M3 centerline enclosures are experimental; the provisional-face file is also not an accepted block layer.

> Work only in Feature M3. Confirm the two attached paths and inspect their actual schemas. The 23,204 stitched polygons are provisional land faces, including motorway islands, airport land, tiny artifacts, possible street-gap merges and city-edge fragments. Preserve each `candidate_id` and join review flags only by that ID. Measure `outer_area_m2` on the whole polygon before assigning it to Community Areas; never clip first and call the clip a block. Compute a separate *provisional-face diagnostic* of log whole outer area, unweighted median and IQR with each face assigned once by largest Community Area overlap; also report an overlap-weighted sensitivity, candidate count and flagged/unresolved share. Keep the model-facing M3 `value` null and status `provisional_not_accepted`; do not silently remove flagged, tiny, large, rail or airport polygons, do not infer accepted block labels from the fact that a face is closed, and do not replace the accepted physical-block contract. Return the provisional face geometry with assignment and review fields as the second output so Feature M4 can use precisely the same candidate set. If either Curio dataset is not attached, leave current M3 unchanged and report the missing path.

### 5. Feature M4: derive provisional shape from M3's identical faces

> Work only in Feature M4 after Feature M3 returns its 77-row diagnostic and whole-face geometry as two outputs. Use *exactly* M3's global candidate IDs and whole-face outer rings. Calculate outer-ring compactness `4πA_outer/P_exterior²` and minimum-rotated-rectangle elongation, with any holes reported separately and not added to the exterior perimeter. Use M3's one-face largest-overlap assignment for the unweighted median and IQR; report overlap-weighted sensitivity separately. Retain the same candidate/flag population. Return 77 rows of provisional shape diagnostics, coverage and unresolved share, with model-facing `value` null and `status='provisional_not_accepted'`. Do not interpret a clipped district fragment as the shape of a whole block. If M3 still returns experimental centerline enclosures, keep M4 explicitly experimental and do not present it as physical block shape.

### Current scope and next stage

M1, M6, B1, BV, U1, U2, U3 and U4 already construct 77 Chicago rows; their scientific acceptance remains separate. M2 is excluded by the current project decision and needs no construction prompt. The M3/M4 physical-face layer still requires source review and adjudication before model use. M7 and B3 may remain null after honest source inspection. Do not send a model fitting or ranking prompt at this construction stage.
