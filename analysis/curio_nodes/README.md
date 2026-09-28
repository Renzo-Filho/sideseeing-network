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
Copy-ready prompts for the next feature work are in [NEXT_CURIO_PROMPTS.md](NEXT_CURIO_PROMPTS.md).

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
