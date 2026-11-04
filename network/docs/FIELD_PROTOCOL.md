# Field protocol: West Loop collection

4 November 2026. How a normal field day is done. **The one-page volunteer briefing is the protocol** (decision 32 in [RESEARCH_PLAN](RESEARCH_PLAN.md#5-decisions)): section 1 is its text, and the rest of this page is what the researcher adds around it. It replaces the October field rules, which are archived: the general [collection protocol](archive/COLLECTION_PROTOCOL.md), the [West Loop route plan](archive/WEST_LOOP_COLLECTION.md), the field rules F1–F8 of [River North](archive/RIVER_NORTH_COLLECTION.md) §3 and the voice protocol of [Pilot 2](archive/PILOT2_PROTOCOL.md) §3. Section 8 lists what changed, for reading the older sessions.

The **calibration day** is not part of this protocol. It is a separate plan, still under discussion: [CALIBRATION_DAY_PLAN_2026-11-03.md](CALIBRATION_DAY_PLAN_2026-11-03.md).

Briefings used so far (kept outside the repository, in Renzo's files): Green St, 4 November, and Jefferson St, 6 November.

## 1. The protocol

What every collector does, as the briefing says it. `<street>` is the day's street.

> We are mapping the sidewalks and crosswalks of Chicago's West Loop. You walk one street with a phone in a vest, and the phone records video, GPS and motion sensors. Software later builds the sidewalk map from those recordings, so what matters is that every walk is done the same way.

1. **Start the recording.** Stand at the start corner, facing your walking direction, with the phone already in the vest. Press record and stand still for **30 seconds**.
2. **Walk normally.** Ordinary pace, in the middle of the sidewalk, on the same line the whole way. Never touch the phone or the screen while walking.
3. **At every corner, cross `<street>` and come back, to record each crosswalk.**
   - Stop next to the curb and turn 270° so you face the other side of `<street>`.
   - When it is safe (or the signal shows WALK), cross on the marked crosswalk, straight ahead. Never diagonally, never mid-block.
   - On the far side, make a U-turn (180°) to face your own sidewalk again, and cross straight back when the signal allows.
   - Turn back to your walking direction, cross the side street straight ahead, and keep walking.
4. **Talk as you walk** (section 3).
5. **End the recording.** Walk past the last crossing, stand still for **10 seconds**, say **"end"**, stop recording and check that it was saved.
6. **Switch sides.** At the end, cross `<street>` to the other side and start a new recording for the walk back, from step 1.

**The app:** MultiSensor is the only app. The researcher sets it up before leaving; the collector only starts and stops it.

**Why the corner ritual matters:** each crosswalk over the walked street is crossed there and back, so every crossing is a repeated, timed measurement of the street's width and of which sidewalk the walker is on. This is the "rung" of the ladder ([METHOD §5](METHOD.md#5-the-walk-only-inference-the-ladder)).

## 2. Routes: one street per day

A field day walks **one whole street, both sides**, in two recordings (one per side). The road is always on the walker's left.

| Street runs | First recording | Second recording |
|---|---|---|
| **North–south** ("vertical": Green, Jefferson, Morgan…) | East side, **south to north** | West side, **north to south** |
| **East–west** ("horizontal": Madison, Randolph…) | South side, **west to east** | North side, **east to west** |

```
 north–south street                      east–west street

   W side │ ║ │ E side                    N side  ◄──────────── 2nd (east → west)
     2nd  │ ║ │  1st                      ═════════ street ═════════
      ▼   │ ║ │   ▲                       S side  ────────────► 1st (west → east)
          │ ║ │                                   W                       E
```

- **Start and end** are named in the day's briefing, e.g. Green St from Van Buren to Grand Ave (4 November: about 4.7 km of walking and about 1.5 hours of recording, 2 hours on site).
- **Plan for 2 hours on site** for a full street.
- **Which streets are done** is dated status: see [STATUS.md](STATUS.md).
- **Free test routes** (decision 26) are a different kind of walk: a route drawn at random before the walk and kept unchanged, walked as a person going somewhere would. How many and how they are drawn is still open ([RESEARCH_PLAN §6](RESEARCH_PLAN.md#6-open-questions)).

**The route plan's files and the new scheme.** `routes.gpkg` and `sessions.csv` (section 7) cut the area into modules and legs. A street-day may cover several modules (east–west streets are split at Halsted). The leg names still identify the side: `GREEN-E`, `GREEN-W` for a north–south street, `MADISON_WEST-N`, `MADISON_WEST-S` for an east–west one. The files on disk were made under the October rules: on **east–west streets their directions are reversed** (north side first, west to east). Re-running the planner with the briefing's protocol (section 7) gives the current directions; the side, not the direction, identifies a leg.

## 3. Spoken words

From the briefing:

| When | Say |
|---|---|
| At each curb or tactile strip | **curb ramp** or **no curb ramp** |
| In the middle of each crossing | **crosswalk** |
| Something on the sidewalk | **obstruction**, **damage**, **blocked**, or another interesting element |
| How it feels, if you like | Free remarks: "feels unsafe", "nice shade", "very noisy" |
| At the end | **end** |

- The words are an **evaluation reference only**: graph construction never reads them (decision 14). The free remarks are an exploratory measurement (decision 30).
- **Raw audio never leaves this machine.** Audio is released only as annotated transcripts (decision 23, AGENTS.md rule 8).
- **Older sessions used other words.** Sessions recorded under the October rules (at least D1–D3, 19–22 October) used Pilot 2's vocabulary: "ramp" / "no ramp", a spoken session ID, no talking while crossing, and remarks started by "note" ([Pilot 2](archive/PILOT2_PROTOCOL.md) §3). A transcript must be read with the vocabulary of its day.

## 4. Before and after each field day

What the researcher does; the collectors do not need it.

**Before leaving:**
- **Settings** (measured in Pilot 2, unchanged since):
  - Video: FHD, `camera_resolution` 3 (1920×1080 at 30 fps). Zoom at 1.0; do not touch the preview, since MultiSensor zooms on a pinch while recording.
  - Sensors: Game, `sensors_delay` 1.
  - GPS interval 1 s; Battery Saver off.
  - About 10 GB free per recording hour (Pilot 2 measured 9.1 GB); a charged power bank.
- **Mounting:** the lens on the same side in every session; check the on-screen angle before starting (Pilot 2 found the mount changed between sessions).
- **Camera height:** measure each new collector's lens height on the vest, standing in walking shoes (Renzo's is 1.30 m).
- **The briefing** for the day's street, with the Google Maps link.

**The field log**, one row per recording, in `network/data/<area>/field_log.csv` (local: it holds collectors' names). It is an **input** of the software: it names each session's protocol, so the code knows which side of the road to expect. `walk2net.fieldlog` reads it and refuses a misspelt column, a row without its required values, a session listed twice or a protocol with no definition in `network/protocols/`.

| Column | Required | Example |
|---|---|---|
| `session` | yes | `2026-11-04-14-05-12-345` (the capture folder) |
| `label` | yes | `D4 S1`: the day and the recording number |
| `protocol` | yes | `briefing-2026-11` (field days from 4 November); `oct-2026` for the earlier days; `free-route` for a free test route |
| `leg` | | `GREEN-E`: the street and side |
| `collector` | | Renzo |
| `phone` | | moto g 5G (2023) Android 34 |
| `camera_height_m` | | 1.30 |
| `start`, `end` | | Times, if noted |
| `deviations` | | Restarts (keep the failed folder), detours, closures, **crosswalks not crossed and why**, crowds, rain, dusk |

The West Loop log lists D1–D3 (19–22 October) under `oct-2026`, with the leg and phone where the documents give them; the collectors, camera heights and the later days are to be filled in.

**After the day:**
1. Copy the original capture folders intact, keeping their names. Check that video, GPS and sensor files open **before** deleting anything from the phone.
2. Upload to Google Drive and RustFS (`rclone copy`, never `sync` or `move`), write the file manifest in [datasets/](datasets/README.md) and the run log in `network/data/_transfers/west_loop/`.
3. Process on desktop-01, then the automatic checks (S1).
4. Assign the new passes to development or test by street, in `splits.csv` ([METHOD §4](METHOD.md#4-how-the-data-are-managed)).
5. Add a line to [STATUS.md](STATUS.md).

**Gaps in the briefing to consider for its next version.** The plan relies on two things the briefing does not yet say:
- **What to do at a closed or missing crosswalk.** A crosswalk the collector could not cross is a verified negative connection ([RESEARCH_PLAN §2.2](RESEARCH_PLAN.md#22-what-tile2net-does-and-where-the-walk-can-do-better)). Suggested: do not cross, continue to the next legal crosswalk, and say "closed".
- **Describe places, never people.** Never read out a plate or a name. The audio is reviewed and anonymised before any release, but less to remove is safer.

## 5. The area

West Loop, as proposed on 19 October 2026:

| Item | Choice |
|---|---|
| Boundary | **Ashland Ave** centreline (west), **Grand Ave** centreline (north), the **Chicago River** (east), the north rim of the **I-290** trench (south: Van Buren St west of Racine, Tilden St east of it). Core 4.01 km² |
| Boundary streets | **Both sides** of Grand, Ashland and Tilden, with their crosswalks (4.21 km² in all) |
| Levels | One street level. Sidewalks on bridges over the Kennedy and over rail are collected, and Randolph and Washington under the Ogilvie train shed |
| Proposed exclusions | River bridges, the Riverwalk, private plazas (Riverside Plaza, the Union Station and Ogilvie forecourts), paths inside Union Park and Skinner Park |

**This is not the City's West Loop.** The cross-city model scored the City's neighborhood polygon (4.92 km²); the two share 3.30 km². Any comparison with the model must say so.

The route plan's OSM inventory covers 101.2 km of sidewalk and 937 crosswalks (385 signalised) in 78 modules ([archived plan](archive/WEST_LOOP_COLLECTION.md) §4).

## 6. Places to check before walking a street

| Place | Streets | What to expect |
|---|---|---|
| Ogilvie train shed | Randolph and Washington between Canal and Clinton; Canal and Clinton beside the tracks | No GPS under the shed; dark video |
| Metra viaducts between Kinzie and Hubbard | Desplaines, May, Halsted, Aberdeen, Green, Carpenter, Peoria, Racine, Morgan (130–370 m under rail each) | Dark video, poor GPS. Check whether Hubbard's south side, along the embankment, has a sidewalk |
| The C&M line at grade near Kinzie | Ada, Elizabeth, Peoria, Sangamon, Union; Carroll beside it | Streets cut by the line; check whether a crossing exists (Union has a footbridge) |
| The 'L' over Lake St | Lake, and every north–south street where it crosses Lake | Columns beside the walk; poor GPS |
| The Kennedy Expressway | East–west streets on its bridges; 24 crosswalks over its ramps, 5 signalised | Cross only where it is safe and legal |
| Diagonal streets | Ogden, Milwaukee (six-way intersections) | Cross straight ahead along your sidewalk line, never diagonally. Ogden's west side is mapped only in pieces along Union Park |
| River ends | East–west streets east of Canal; Union Station, Riverside Plaza | Check which sidewalks are public |
| Short named streets | Gladys, Court Place, Couch Place, Walnut, Willard | May be private drives; check access |

## 7. Route files

`python -m walk2net.plan west_loop briefing-2026-11` (from `network/`) builds the plan for the area in `network/areas/west_loop.toml`, under the briefing's protocol, from an OpenStreetMap snapshot (19 October 2026), into `network/data/west_loop/plan/`, which git ignores:
- `routes.gpkg`: the modules and their legs (one leg per sidewalk side);
- `sessions.csv`: one row per leg, with its length and crosswalks;
- `cards/<MODULE>.png`: a route card per module; `overview.png`; `unassigned.csv`.

A second script, `route_methods.py`, compared the module plan with three tour-based plans (Chinese Postman, Rural Postman, capacitated arc routing). The protocol does not use tours, so it was dropped on 4 November ([ARCHITECTURE §6](ARCHITECTURE.md#6-where-each-piece-went)); the comparison is explained in the archived [routing workflow](archive/ROUTING_WORKFLOW.md) and [West Loop plan](archive/WEST_LOOP_COLLECTION.md) §8. The files it wrote (`plan/routing/`, with a field map and GPX tracks) are still on disk.

## 8. What changed from the October rules

For reading sessions recorded before the briefing.

| Topic | October rules (archived) | Now (the briefing) |
|---|---|---|
| Unit of work | A module, one leg per recording, about 30 min; a day of several modules | One whole street per day, one recording per side |
| East–west streets | North side first, west to east | South side first, west to east |
| Crossings | F4: cross straight ahead; a U-turn crosswalk at the module's end. D1–D3 already crossed the walked street there and back at every corner ([RESULTS](RESULTS.md#phase-2a-notes-the-ladder-on-morgan) 2a) | At every corner: turn 270°, cross the walked street, turn 180°, cross back, then cross the side street |
| Curb pause | F3: at least 3 s still at every curb | Stop next to the curb (no set time) |
| Signals | Cross only on a fresh WALK phase | Cross when safe, or on WALK |
| Start and end | 30 s still; sync taps and the spoken session ID; 10 s still | 30 s still; 10 s still and "end" |
| Voice | "ramp / no ramp" and other code words; never talk while crossing; "note …" remarks | "curb ramp / no curb ramp"; "crosswalk" in the middle of each crossing; obstruction, damage, blocked; free remarks |
| Closures | Log the crosswalk as not crossable and go on | Not covered yet (section 4) |
