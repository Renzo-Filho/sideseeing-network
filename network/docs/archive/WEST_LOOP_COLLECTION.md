# West Loop collection: route plan

Draft, 19 October 2026. West Loop is a second candidate area for the full collection, next to [River North](RIVER_NORTH_COLLECTION.md). This document plans its routes with the same method and the same field rules, so the two areas can be compared on equal terms. It only writes down what West Loop adds. Team size, hours per day and the schedule are still open.

## 1. Boundary (proposed 19 October 2026)

| Item | Choice |
|---|---|
| Boundary | The limits drawn on the map supplied on 19 October 2026: the **Ashland Ave centreline** (west), the **Grand Ave centreline** (north), the **Chicago River** (east: North and South Branch) and the **north rim of the I-290 trench** (south). The core is 4.01 km². |
| South edge | The I-290 rim is Van Buren St west of Racine and Tilden St east of it, where the trench swings about 100 m further south. The plan uses the Tilden centreline as the edge line. West of Racine, the only things south of Van Buren are the bridges over I-290, and those lead out of the area. |
| Boundary streets | **Both sides** of Grand, Ashland and Tilden are collected, with their crosswalks, as for River North. With these outer sidewalks the collection area is 4.21 km². |
| Crossings | **Every legal crosswalk** is traversed once, as for River North. |
| Levels | West Loop has a single street level. Sidewalks on bridges over the Kennedy Expressway and over rail are collected. So are Randolph and Washington where they pass under the Ogilvie train shed. Only river bridges and bridges over I-290 lead out of the area. |
| Team and daily hours | Open. |

**This boundary is not the City's West Loop.** The cross-city model scored the City neighborhood polygon (`Boundaries_-_Neighborhoods_20261013.geojson`, 4.92 km²). The two share 3.30 km².
- The City polygon stops at Kinzie St. It also reaches south of I-290 along the river, below Roosevelt Rd: 1.61 km² that this plan leaves out.
- This boundary takes in 0.56 km² that the City assigns to West Town (Kinzie to Grand) and 0.14 km² of Greektown.

Any comparison with the model must state this difference.

**Proposed, not yet confirmed** (the same as for River North): do not collect river bridges, the Riverwalk, private plazas (Riverside Plaza, the Union Station and Ogilvie forecourts), or paths inside Union Park and Skinner Park.

## 2. What carries over

Field rules F1–F8 and settings S1–S4 are those of [River North §3](RIVER_NORTH_COLLECTION.md). The voice protocol is that of [Pilot 2 §3](PILOT2_PROTOCOL.md). The Pilot 2 test session ([`pilot2_test.ipynb`](../../notebooks/pilot2_test.ipynb), 16 October 2026) has since answered several open settings:

| Item | Pilot 2 result | For West Loop |
|---|---|---|
| S1 video | `camera_resolution` 4 records 1920×1080 at 30 fps: the phone falls back to FHD | FHD (3). UHD is not available on the moto g. |
| S2 sensors | Game (`sensors_delay` 1) raised the calibrated gyroscope, gravity and linear acceleration streams from 5 to 49.6 Hz. No stream had a gap over 0.03 s. Storage rose by about 2%. | Game, as the notebook recommends |
| S3 mounting | Pitch is steady within a session. Between sessions the walking median ranged over 18.7–22.8°, and the phone was not always mounted the same way round. | Same lens side every session; check the on-screen angle before starting |
| F1 start | GPS stayed within 6 m from 13 s onward | The 30 s still start is enough |
| Signal stops | Four stops at signals: 28, 6, 57 and 48 s | Too few to plan with. Section 5 keeps a 30–60 s range. |

## 3. West Loop additions to the field rules

**W1. Dead ends.** Some legs end where no crosswalk continues: at a river bridge (the east end of most east–west streets), at a rail line, or at the Kennedy. Walk to the end of the sidewalk and say "end". Walk back to the last crosswalk saying "repeat", then make the U-turn there. The walk back is a logged repeat, not new coverage.

**W2. Halsted split.** East–west streets are split at Halsted into `_WEST` and `_EAST` modules. A `_WEST` module makes its U-turn at Halsted's west corners. The crosswalk over Halsted belongs to the `_EAST` module.

**W3. Runs.** A street that is cut for more than 60 m becomes one module per piece, lettered west to east or south to north (`LOOMIS_A` … `LOOMIS_E`). The cut can be an at-grade rail line, the Kennedy, a park or a jog. Walk from one run to the next without recording.

**W4. Diagonal streets.** Ogden and Milwaukee cross the grid diagonally, which creates six-way intersections where "straight ahead" can mean two crosswalks. Take the one that continues the sidewalk line of the module you are walking, as drawn on its route card. Never cross diagonally through the intersection.

## 4. Route plan

The rule is River North's ([§4](RIVER_NORTH_COLLECTION.md)): out on the north or east side, back on the south or west side, crossing straight ahead at every intersection. The U-turn crosswalk is the planned overlap with the perpendicular module.

`network/scripts/routes.py west_loop` builds the plan from OpenStreetMap (snapshot of 19 October 2026). The same script builds River North with `routes.py river_north`. The outputs are in `data/west_loop/` (not versioned):
- `sessions.csv`: one row per leg. The `gap_m` column gives the length of the leg with no mapped sidewalk or crosswalk, counting stretches of 40 m or more.
- `cards/<MODULE>.png`: one route card per module.
- `overview.png`, `unassigned.csv` and `routes.gpkg`, as for River North.
- `routing/`: the GIS layers, the field map and the GPX tracks of section 8.

**Coverage of the OSM inventory:** 101.2 of 102.2 km of sidewalk (99%) and 14.1 of 14.6 km of crosswalk (96%) are assigned. The plan has 78 modules and 154 legs, with 937 crosswalks, 385 of them signalised.
- **50 main modules:** 100 legs, 94.7 km, 21.4 h of walking. The longest leg is `CANAL-E` at 1,673 m (21 min); River North's longest is 1,463 m.
- **28 short modules:** under 400 m on both sides together. They have 54 legs, 6.4 km and 88 min of walking. They are short streets and the runs of streets that are cut. Each still costs the 40 s start and end rituals per leg, so walk each one straight after a neighbouring main module.

"From" and "to" name the nearest cross street to each end, as OSM gives it. On short and diagonal streets this can name the same street twice, or a street one block off. The route card is the reference. Walking minutes assume 1.4 m/s and **exclude signal waits, rituals and repositioning**.

**Main modules** (north–south streets from east to west, then east–west streets from south to north):

| Module | Out leg | Back leg | Sidewalk (m, both sides) | Crosswalks (with signals) | Walking min |
|---|---|---|---:|---:|---:|
| CANAL | `CANAL-E` Tilden → Clinton | `CANAL-W` Clinton → Tilden | 3,148 | 20 (19) | 41 |
| CLINTON | `CLINTON-E` Tilden → Grand | `CLINTON-W` Canal → Tilden | 3,008 | 24 (16) | 40 |
| JEFFERSON | `JEFFERSON-E` Tilden → Kinzie | `JEFFERSON-W` Kinzie → Tilden | 2,525 | 24 (18) | 34 |
| DESPLAINES | `DESPLAINES-E` Tilden → Grand | `DESPLAINES-W` Grand → Tilden | 2,934 | 32 (21) | 41 |
| HALSTED | `HALSTED-E` Van Buren → Milwaukee | `HALSTED-W` Grand → Van Buren | 2,817 | 26 (20) | 39 |
| GREEN | `GREEN-E` Van Buren → Grand | `GREEN-W` Grand → Van Buren | 2,956 | 26 (2) | 40 |
| PEORIA_A | `PEORIA_A-E` Van Buren → Hubbard | `PEORIA_A-W` Hubbard → Van Buren | 2,660 | 23 (0) | 36 |
| SANGAMON_A | `SANGAMON_A-E` Van Buren → Wayman | `SANGAMON_A-W` Wayman → Van Buren | 2,198 | 18 (4) | 30 |
| MORGAN | `MORGAN-E` Tilden → Grand | `MORGAN-W` Grand → Tilden | 2,987 | 27 (18) | 41 |
| CARPENTER | `CARPENTER-E` Madison → Grand | `CARPENTER-W` Grand → Madison | 1,808 | 18 (0) | 25 |
| ABERDEEN | `ABERDEEN-E` Van Buren → Grand | `ABERDEEN-W` Grand → Van Buren | 2,881 | 24 (4) | 38 |
| MAY | `MAY-E` Madison → Grand | `MAY-W` Grand → Madison | 1,791 | 18 (0) | 25 |
| RACINE | `RACINE-E` Van Buren → Grand | `RACINE-W` Grand → Van Buren | 2,878 | 26 (14) | 40 |
| ELIZABETH_A | `ELIZABETH_A-E` Madison → Carroll | `ELIZABETH_A-W` Carroll → Madison | 1,115 | 12 (0) | 16 |
| THROOP_A | `THROOP_A-E` Van Buren → Adams | `THROOP_A-W` Adams → Van Buren | 553 | 4 (0) | 7 |
| THROOP_B | `THROOP_B-E` Monroe → Elizabeth | `THROOP_B-W` Washington → Monroe | 528 | 4 (0) | 7 |
| ADA_A | `ADA_A-E` Madison → Ogden | `ADA_A-W` Ogden → Madison | 1,216 | 13 (0) | 17 |
| LOOMIS_A | `LOOMIS_A-E` Van Buren → Adams | `LOOMIS_A-W` Adams → Van Buren | 532 | 6 (6) | 7 |
| OGDEN | `OGDEN-E` Ashland → Grand | `OGDEN-W` Grand → Ashland | 1,781 | 24 (16) | 26 |
| LAFLIN_B | `LAFLIN_B-E` Lake → Arbour Place | `LAFLIN_B-W` Arbour Place → Lake | 561 | 5 (0) | 8 |
| LAFLIN_A | `LAFLIN_A-E` Van Buren → Madison | `LAFLIN_A-W` Madison → Van Buren | 1,028 | 8 (0) | 14 |
| ARMOUR | `ARMOUR-E` Kinzie → Grand | `ARMOUR-W` Grand → Kinzie | 420 | 4 (0) | 6 |
| JUSTINE | `JUSTINE-E` Lake → Arbour Place | `JUSTINE-W` Arbour Place → Lake | 569 | 5 (0) | 8 |
| ASHLAND | `ASHLAND-E` Van Buren → Grand | `ASHLAND-W` Grand → Van Buren | 2,852 | 33 (22) | 40 |
| VAN_BUREN_WEST | `VAN_BUREN_WEST-N` Ashland → Halsted | `VAN_BUREN_WEST-S` Halsted → Ashland | 3,002 | 16 (7) | 38 |
| VAN_BUREN_EAST | `VAN_BUREN_EAST-N` Halsted → Jackson | `VAN_BUREN_EAST-S` Canal → Halsted | 1,477 | 11 (11) | 20 |
| JACKSON_WEST | `JACKSON_WEST-N` Ashland → Green | `JACKSON_WEST-S` Halsted → Ashland | 2,936 | 21 (11) | 38 |
| JACKSON_EAST | `JACKSON_EAST-N` Halsted → Canal | `JACKSON_EAST-S` Canal → Halsted | 1,360 | 12 (10) | 18 |
| ADAMS_WEST | `ADAMS_WEST-N` Ashland → Halsted | `ADAMS_WEST-S` Halsted → Ashland | 2,966 | 18 (7) | 39 |
| ADAMS_EAST | `ADAMS_EAST-N` Halsted → Canal | `ADAMS_EAST-S` Canal → Halsted | 1,293 | 13 (11) | 18 |
| MONROE_WEST | `MONROE_WEST-N` Ashland → Halsted | `MONROE_WEST-S` Halsted → Ashland | 2,968 | 18 (6) | 38 |
| MONROE_EAST | `MONROE_EAST-N` Halsted → Canal | `MONROE_EAST-S` Canal → Halsted | 1,254 | 11 (10) | 17 |
| MADISON_WEST | `MADISON_WEST-N` Ashland → Halsted | `MADISON_WEST-S` Halsted → Ashland | 2,815 | 25 (13) | 38 |
| MADISON_EAST | `MADISON_EAST-N` Halsted → Canal | `MADISON_EAST-S` Canal → Halsted | 1,229 | 14 (10) | 18 |
| WASHINGTON_EAST | `WASHINGTON_EAST-N` Halsted → Canal | `WASHINGTON_EAST-S` Canal → Halsted | 1,318 | 12 (10) | 18 |
| WASHINGTON_WEST | `WASHINGTON_WEST-N` Ashland → Halsted | `WASHINGTON_WEST-S` Halsted → Ashland | 3,011 | 29 (12) | 40 |
| RANDOLPH_EAST | `RANDOLPH_EAST-N` Halsted → Canal | `RANDOLPH_EAST-S` Canal → Halsted | 1,323 | 17 (10) | 18 |
| RANDOLPH_WEST | `RANDOLPH_WEST-N` Lake → Green | `RANDOLPH_WEST-S` Green → Lake | 2,658 | 23 (6) | 35 |
| LAKE_WEST | `LAKE_WEST-N` Ashland → Halsted | `LAKE_WEST-S` Halsted → Ashland | 2,820 | 35 (12) | 39 |
| LAKE_EAST | `LAKE_EAST-N` Halsted → Canal | `LAKE_EAST-S` Randolph → Halsted | 1,482 | 12 (9) | 20 |
| FULTON_EAST | `FULTON_EAST-N` Halsted → Canal | `FULTON_EAST-S` Canal → Halsted | 1,077 | 9 (4) | 14 |
| FULTON_WEST | `FULTON_WEST-N` Ashland → Halsted | `FULTON_WEST-S` Halsted → Ashland | 2,826 | 33 (7) | 39 |
| WAYMAN_WEST | `WAYMAN_WEST-N` Peoria → Halsted | `WAYMAN_WEST-S` Green → Sangamon | 412 | 5 (0) | 6 |
| CARROLL | `CARROLL-N` Justine → Morgan | `CARROLL-S` Morgan → Justine | 1,424 | 24 (0) | 20 |
| KINZIE_WEST | `KINZIE_WEST-N` Ogden → Halsted | `KINZIE_WEST-S` Green → Elizabeth | 1,658 | 17 (0) | 23 |
| KINZIE_EAST | `KINZIE_EAST-N` Halsted → Canal | `KINZIE_EAST-S` Canal → Halsted | 1,265 | 7 (3) | 16 |
| HUBBARD_WEST | `HUBBARD_WEST-N` Ashland → Halsted | `HUBBARD_WEST-S` Halsted → Ashland | 2,068 | 29 (4) | 30 |
| MILWAUKEE_A | `MILWAUKEE_A-N` Halsted → Desplaines | `MILWAUKEE_A-S` Kinzie → Grand | 565 | 11 (11) | 9 |
| GRAND_WEST | `GRAND_WEST-N` Ashland → Halsted | `GRAND_WEST-S` Milwaukee → Ashland | 2,913 | 22 (7) | 39 |
| GRAND_EAST | `GRAND_EAST-N` Milwaukee → Canal | `GRAND_EAST-S` Canal → Milwaukee | 874 | 8 (1) | 12 |
| **Total** | 100 legs | | **94,740** | **876 (372)** | **1,285** |

**Short modules:**

| Module | Out leg | Back leg | Sidewalk (m, both sides) | Crosswalks (with signals) | Walking min |
|---|---|---|---:|---:|---:|
| UNION_A | `UNION_A-E` Walnut → Wayman | `UNION_A-W` Wayman → Fulton | 212 | 5 (0) | 3 |
| UNION_B | `UNION_B-E` Kinzie → Kinzie | `UNION_B-W` Kinzie → Kinzie | 145 | 2 (0) | 2 |
| UNION_C | `UNION_C-E` Hubbard → Grand | `UNION_C-W` Grand → Milwaukee | 204 | 2 (0) | 3 |
| SANGAMON_B | `SANGAMON_B-E` Kinzie → Hubbard | `SANGAMON_B-W` Hubbard → Kinzie | 322 | 4 (0) | 4 |
| WILLARD | `WILLARD-E` Washington → Randolph | `WILLARD-W` Randolph → Washington | 235 | 3 (0) | 4 |
| ELIZABETH_B | `ELIZABETH_B-E` Kinzie → Grand | `ELIZABETH_B-W` Ogden → Kinzie | 385 | 3 (0) | 5 |
| ADA_B | `ADA_B-E` Ogden → Hubbard | `ADA_B-W` Hubbard → Ogden | 196 | 3 (0) | 3 |
| LOOMIS_B | `LOOMIS_B-E` Monroe → Madison | `LOOMIS_B-W` Madison → Monroe | 249 | 2 (0) | 3 |
| NOBLE | `NOBLE-E` Hubbard → Grand | `NOBLE-W` Grand → Hubbard | 362 | 4 (2) | 5 |
| LOOMIS_C | `LOOMIS_C-E` Madison → Washington | `LOOMIS_C-W` Washington → Madison | 299 | 4 (2) | 4 |
| LOOMIS_D | `LOOMIS_D-E` Ogden → Ogden | `LOOMIS_D-W` Lake → Ogden | 168 | 1 (1) | 2 |
| LOOMIS_E | `LOOMIS_E-E` Ogden → Carroll | `LOOMIS_E-W` Carroll → Ogden | 364 | 6 (0) | 5 |
| BISHOP_B | — | `BISHOP_B-W` Hubbard → Hubbard | 58 | 0 (0) | 1 |
| BISHOP_A | `BISHOP_A-E` Madison → Washington | `BISHOP_A-W` Washington → Madison | 275 | 2 (0) | 4 |
| TILDEN_EAST | `TILDEN_EAST-N` Desplaines → Canal | `TILDEN_EAST-S` Clinton → Clinton | 314 | 3 (0) | 4 |
| TILDEN_WEST | `TILDEN_WEST-N` Van Buren → Van Buren | `TILDEN_WEST-S` Morgan → Van Buren | 392 | 1 (1) | 5 |
| GLADYS | `GLADYS-N` Halsted → Halsted | `GLADYS-S` Halsted → Halsted | 89 | 0 (0) | 1 |
| QUINCY_A | `QUINCY_A-N` Halsted → Adams | `QUINCY_A-S` Halsted → Halsted | 121 | 0 (0) | 2 |
| QUINCY_B | `QUINCY_B-N` Adams → Desplaines | `QUINCY_B-S` Desplaines → Jackson | 181 | 0 (0) | 2 |
| QUINCY_C | `QUINCY_C-N` Clinton → Clinton | `QUINCY_C-S` Clinton → Clinton | 205 | 1 (0) | 3 |
| WARREN | `WARREN-N` Ashland → Washington | `WARREN-S` Ogden → Ashland | 236 | 4 (3) | 4 |
| COURT_PLACE | `COURT_PLACE-N` Halsted → Halsted | `COURT_PLACE-S` Washington → Halsted | 103 | 0 (0) | 1 |
| COUCH_PLACE | `COUCH_PLACE-N` Halsted → Halsted | `COUCH_PLACE-S` Halsted → Halsted | 126 | 0 (0) | 2 |
| WALNUT | `WALNUT-N` Union → Union | `WALNUT-S` Union → Union | 171 | 0 (0) | 2 |
| MILWAUKEE_B | `MILWAUKEE_B-N` Fulton → Canal | `MILWAUKEE_B-S` Lake → Clinton | 130 | 4 (2) | 2 |
| WAYMAN_EAST | `WAYMAN_EAST-N` Union → Jefferson | `WAYMAN_EAST-S` Union → Union | 383 | 2 (0) | 5 |
| ARBOUR_PLACE | — | `ARBOUR_PLACE-S` Laflin → Ashland | 188 | 1 (0) | 2 |
| HUBBARD_EAST | `HUBBARD_EAST-N` Halsted → Desplaines | `HUBBARD_EAST-S` Desplaines → Desplaines | 320 | 4 (2) | 5 |
| **Total** | 54 legs | | **6,433** | **61 (13)** | **88** |

### Places that need a site check before their module is walked

- **Ogilvie train shed.** Randolph and Washington pass under it between Canal and Clinton, about 100 m per side, mapped as building passages. Expect no GPS fix there. Canal and Clinton run beside the elevated tracks into Ogilvie for 430–540 m of each module.
- **Metra lines between Kinzie and Hubbard.** The UP Geneva and Harvard lines cross the north–south streets on viaducts. Desplaines, May, Halsted, Aberdeen, Green, Carpenter, Peoria, Racine and Morgan each have 130–370 m of their module directly under rail. Expect dark video and poor GPS.
  - **Hubbard's south side** runs along the embankment. OSM maps only its corner pieces: `HUBBARD_WEST-S` has 636 m mapped and 767 m with nothing. Check whether a sidewalk exists.
- **The C&M line at grade.** It cuts Ada, Elizabeth, Peoria, Sangamon and Union near Kinzie. OSM maps no street across it, so these streets are split into runs. Check whether a crossing exists (Union has a footbridge). Carroll runs beside the line, and 425 m of its north-side leg and 303 m of its south-side leg have nothing mapped.
- **Lake St under the 'L'.** The Green and Pink Lines run above Lake St across the whole area. `LAKE_WEST` and `LAKE_EAST` walk beside the structure's columns, and every north–south module crosses Lake beneath it. This is West Loop's counterpart to River North's Franklin St.
- **The Kennedy Expressway.** East–west streets cross it on bridges. 24 crosswalks cross its ramps, only 5 of them signalised, mostly on the `_EAST` modules (Randolph and Madison have 4 each). Apply F4 strictly at these. Quincy and Wayman stop at the expressway, so they are split into runs.
- **Diagonal streets** (W4).
  - Ogden's west side is mapped in pieces along Union Park: `OGDEN-W` has 702 m mapped against 1,079 m on `OGDEN-E`, with 309 m unmapped.
  - Milwaukee's last block, from Fulton to Lake at Canal, shows partly on the `LAKE_EAST` card, because OSM pieces near Lake are assigned to Lake. Walk the whole block with `MILWAUKEE_B` and skip it on `LAKE_EAST-N`.
- **River ends** (W1). Between Canal and the river lie Union Station, Riverside Plaza and the Ogilvie frontages. Check which sidewalks there are public.
- **Short named streets** (Gladys, Court Place, Couch Place, Walnut, Willard). These may be private drives. Check access.
- **Unassigned pieces:** 59 pieces, 1.4 km in all (906 m of sidewalk and 513 m of crosswalk), in `unassigned.csv`. The largest are sidewalks by the Kennedy (Desplaines, Union and Jefferson, between Madison and Kinzie), sidewalks by Skinner Park (Adams and Throop), and two 33 m crossings on Jackson at Canal.
- **Short unmapped stretches** (42–66 m, `gap_m` in `sessions.csv`) on Clinton, Jefferson, Carpenter, May, Elizabeth, Ada, Loomis and Grand are usually a missing crosswalk or corner in OSM. Walk on and record what exists.

## 5. Workload, compared with River North

Both areas are measured with the same script and the same assumptions.

| Component | West Loop | River North | Basis |
|---|---|---|---|
| Sidewalk / crosswalks | 101.2 km / 937 (385 signalised) | 42.4 km / 447 (342) | Assigned OSM inventory |
| Modules / legs | 78 / 154 | 26 / 52 | |
| Walking | 22.9 h | 9.7 h | Pilot's 1.4 m/s |
| Start and end rituals (F1, F2) | 1.7 h | 35 min | Legs × 40 s |
| Curb pauses at unsignalised crosswalks (F3) | 28 min | 5 min | × 3 s |
| Signal waits | 3.2–6.4 h | 2.9–5.7 h | Signalised crosswalks × a 30–60 s mean. Pilot 2's four stops average 35 s, which gives 3.7 h and 3.3 h. |
| **Recording time** | **28.3–31.5 h** | **13.3–16.1 h** | Sum of the rows above |
| Storage | 257–286 GB | 121–147 GB | 9.1 GB per recording hour |
| Battery | about 28–32 Ah | about 13–16 Ah | About 1 Ah per recording hour |
| Voice transcription | about 160 CPU-hours | about 70 | 7× real time over the walking time (Pilot 2), before speech detection cuts it |
| Repositioning | Larger | Small | West Loop's 28 short modules sit between rail lines, parks and the Kennedy |
| Revisits | To be set | To be set | [Collection protocol §3](COLLECTION_PROTOCOL.md) |

**West Loop is about twice River North's workload:**
- 2.4× the sidewalk, 2.1× the crosswalks and 3× the legs, for 2.0–2.1× the recording time.
- Its signalised crosswalks are only 1.1× River North's: the extra crossings are mostly on residential streets without signals.

## 6. First West Loop day, if West Loop is chosen

Pilot 2 and River North's first day leave three West Loop conditions untested: passages under a train shed, the Metra viaducts, and an 'L' over a whole street. One day can test all three:
- **`WASHINGTON_EAST`** (18 min walking): the Kennedy bridge and its ramps, the Ogilvie passage, and towers by the river.
- **`LAKE_EAST`** (20 min): under the 'L' and beside the tracks into Ogilvie.
- **`HALSTED`** (39 min): under the Metra viaducts, across Lake beneath the 'L', and the six-way intersection at Grand and Milwaukee.

Its measured signal waits complete section 5.

## 7. Open items for the next discussion

1. Choose between River North and West Loop using section 5 and the team's confirmed hours. West Loop needs about twice the field time.
2. Confirm the boundary: the I-290 rim as the south edge (Tilden east of Racine), both sides of the boundary streets, and the exclusions in section 1.
3. Confirm rules W1–W4, the split at Halsted, and the 60 m threshold for runs.
4. Carry out the site checks in section 4. The most important are Hubbard's south side and the crossings of the C&M line.
5. Team, hours per day, and module order. Modules are independent, so the short modules can be given to whoever walks the neighbouring main module.
6. Confirm the routing method (section 8). The recommendation is the module plan by day.

## 8. GIS layers and route optimisation

`network/scripts/route_methods.py west_loop`, run after `routes.py`, builds the sidewalk network as a graph and divides it into routes in four ways: the module plan of section 4, and the three standard arc-routing methods. [ROUTING_WORKFLOW.md](ROUTING_WORKFLOW.md) explains the whole process, from the OSM download to these files, for readers new to route optimisation. The outputs are in `data/west_loop/routing/` (not versioned):

| File | Contents | Use |
|---|---|---|
| `map.html` | Each plan by day. Each session is a coloured line with ► arrows and a dot at its start; dotted grey lines are transfers, walked with the recording stopped. Street and satellite basemaps, and a button that shows your position. | Open it on a second phone in the field and switch on the day's layer, e.g. "modules: day 3". |
| `gpx/<plan>/D03_<session>.gpx` | One track per session (376 files) | Load into a phone map app (OsmAnd, Organic Maps) or Google My Maps |
| `routing.gpkg` | Several layers (details below this table) | QGIS |
| `plans.png`, `compare.csv` | The four plans side by side, and the results table below | |

The layers in `routing.gpkg`:
- `edges`: the walkable graph, 48,106 OSM segments. Its `req` flag marks the 6,126 survey targets.
- `zones`: the CARP zones.
- `plan_modules`, `plan_cpp`, `plan_rpp` and `plan_carp`: every traversal in walking order (`seq`), with `day`, `session`, `name` and `status` (first pass, repeat or transfer).

The survey targets total 115.1 km: section 4's 101.2 km of sidewalk and 14.1 km of crosswalk, less 0.2 km on ways that OSM tags as private. The recording phone is in the vest, so the map and tracks are for a second phone or for planning.

**The four plans** cover the same targets with the same cost model:
- walking at 1.4 m/s;
- 35 s per traversal of a signalised crosswalk (Pilot 2's mean) and 3 s per other crosswalk;
- 40 s of start and end rituals per session.

Sessions hold at most 30 min of recording, and days at most 3 h in the field. A stretch of more than 200 m that covers nothing new is a transfer, walked with the recording stopped.

- **Modules** (section 4). Each leg is a session: the out leg with its U-turn, then the back leg. The modules follow a short path through all of them (a travelling-salesman heuristic on transfer times), cut into days.
- **CPP (Chinese Postman).** One closed walk that may only use the survey network itself. That network is in 29 pieces, so it covers only the largest one.
- **RPP (Rural Postman).** One closed walk over every target. It may join the pieces through any walkable way: other footways, and street centrelines at 3× cost as a last resort. The walk is then cut into sessions and days along its length ("route first, cluster second").
- **CARP (hierarchical, as proposed).** 13 compact zones, each sized to fill one day: k-means clusters weighted by field time. Then one RPP walk per zone, cut into sessions.

The solvers are the standard heuristics: a minimum spanning tree to join the pieces, minimum-weight matching of odd nodes, and an Euler circuit. They give good routes, not proven optima.

| | Modules | CPP | RPP | CARP |
|---|---:|---:|---:|---:|
| Targets covered | 100% | 99.2% | 100% | 100% |
| Recorded, km (of which repeats) | 119.7 (4.6) | 130.1 (16.0) | 124.6 (9.5) | 135.0 (19.9) |
| Walked with the recording stopped, km | 15.1 | 4.4 | 1.6 | 4.1 |
| Total walked, km | 134.8 | 134.5 | 126.2 | 139.1 |
| Field time, h | 34.0 | 32.5 | 30.4 | 33.9 |
| Days of at most 3 h | 13 | 11 | 11 | 13 |
| Sessions (longest, min) | 154 (34) | 74 (31) | 66 (31) | 82 (31) |
| Signalised crossings traversed | 440 | 458 | 412 | 439 |
| Turns onto another street per recorded km | 1.4 | 9.8 | 11.8 | 12.6 |

These field times are higher than section 5's recording time because they add the transfers and the repeated crossings.

**What the comparison shows:**
1. **RPP is the shortest.** It takes 3.6 h (11%) and 2 days less than the modules, with 66 sessions instead of 154.
2. **Its price is being able to follow it.**
   - It turns onto another street every 85 m on average. The modules turn every 700 m, and only at their U-turns.
   - With the recording phone in the vest, a tour must be read off a second screen at nearly every corner. A module is one side of one street, straight ahead, and fits on a route card.
   - Tours also give up rule F4's straight-ahead crossing: they often cross a street and then turn.
3. **Sessions mean different things.** A module session is one street side (`HUBBARD_WEST-S`), so the field log, a revisit and the later analysis all use the same unit. A tour session is a 30-minute slice of a walk that mixes streets and sides.
4. **CPP cannot do West Loop alone.** The network is in 29 pieces, so CPP leaves 0.8% (1.0 km) uncovered. Because it may only repeat survey edges, it also repeats 16 km.
5. **The hierarchical CARP gives compact days.** Each day stays within one area (see `plans.png`). But each zone's walk has to close inside the zone, so it repeats 19.9 km. It ends up as long as the modules (33.9 h) while turning as often as the tours. Zones sized for 1.2–1.3× the required time overran into extra short days; 1.4× gives exactly one zone per day.
6. **The modules' cost is transfers:** 15.1 km walked with the recording stopped. This comes from the design, because each module ends at the corner where it started. It does not come from the order, which is already a short path through all modules.

**Recommendation: walk the modules.** Over 13 days they cost about 3.6 h more than the best tour, roughly 17 min a day. In return:
- every session is a straight line that needs no screen;
- the plan matches River North's;
- the dataset keeps one session per sidewalk side.

RPP remains the efficiency benchmark. CARP's zones are the alternative if the team prefers to keep each day within one area.

**Module plan by day** (`plan_modules`; tracks in `gpx/modules/`; transfers are walked with the recording stopped):

| Day | Modules, in walking order | Sessions | Transfers, km | Field h |
|---:|---|---:|---:|---:|
| 1 | CANAL, CLINTON, JEFFERSON | 6 | 0.2 | 2.7 |
| 2 | DESPLAINES, TILDEN_EAST, QUINCY_C, QUINCY_B, QUINCY_A, JACKSON_EAST, GLADYS, VAN_BUREN_EAST | 16 | 1.5 | 2.6 |
| 3 | GREEN, PEORIA_A, SANGAMON_A, MORGAN | 8 | 0.4 | 2.9 |
| 4 | TILDEN_WEST, RACINE, THROOP_A, LOOMIS_A, LAFLIN_A, ASHLAND | 12 | 1.1 | 2.8 |
| 5 | VAN_BUREN_WEST, JACKSON_WEST, ADAMS_WEST | 6 | 0.3 | 2.4 |
| 6 | MONROE_WEST, OGDEN, MADISON_WEST, WARREN | 8 | 0.3 | 2.5 |
| 7 | WASHINGTON_WEST, LAKE_WEST, JUSTINE, RANDOLPH_WEST, LAFLIN_B | 10 | 0.6 | 2.9 |
| 8 | LOOMIS_E, LOOMIS_D, ADA_A, LOOMIS_C, BISHOP_A, LOOMIS_B, THROOP_B, ELIZABETH_A, WILLARD, MAY, CARPENTER | 22 | 2.5 | 2.9 |
| 9 | MADISON_EAST, MONROE_EAST, ADAMS_EAST, HALSTED | 8 | 0.5 | 2.3 |
| 10 | ABERDEEN, WASHINGTON_EAST, COURT_PLACE, RANDOLPH_EAST, COUCH_PLACE, LAKE_EAST, UNION_A, WALNUT | 16 | 2.0 | 2.8 |
| 11 | WAYMAN_EAST, FULTON_EAST, WAYMAN_WEST, SANGAMON_B, KINZIE_EAST, HUBBARD_EAST, UNION_C, GRAND_EAST, MILWAUKEE_A, UNION_B, MILWAUKEE_B | 22 | 3.4 | 2.8 |
| 12 | ELIZABETH_B, KINZIE_WEST, ADA_B, NOBLE, BISHOP_B, ARMOUR, HUBBARD_WEST, GRAND_WEST | 15 | 1.7 | 2.7 |
| 13 | FULTON_WEST, CARROLL, ARBOUR_PLACE | 5 | 0.5 | 1.3 |

The day plan assumes one collector. With two, give each a run of consecutive days. Section 6's test day (`WASHINGTON_EAST`, `LAKE_EAST` and `HALSTED`) comes before day 1, and its legs are then skipped on days 9 and 10.

Related documents: [River North plan](RIVER_NORTH_COLLECTION.md), [Pilot 2 protocol](PILOT2_PROTOCOL.md), [collection protocol](COLLECTION_PROTOCOL.md), [research plan](PLAN.md).
