# Pilot 2: settings, field rules and voice protocol, near UIC

Draft, 16 October 2026; collected the same day around UIC (public streets only, not the campus). Pilot 2 settles what the [River North plan](RIVER_NORTH_COLLECTION.md) leaves open before the main collection:
- the sensor speed and the video resolution;
- the field rules at signalised crossings;
- the voice protocol and its vocabulary;
- two sensor checks (barometer and magnetometer).

GPS among tall buildings cannot be tested near UIC; it stays for the first River North day. **MultiSensor is the only collection app.**

## Decisions this pilot implements

| Topic | Decision |
|---|---|
| Collection app | MultiSensor only (`rafaelpezzuto/multi-sensor-data-collection`). No second app runs alongside it. |
| Voice | **Role B.** A spoken log, element code words (section 3a), and free observations for future studies of semantic context (section 3b). The graph and the vision-language model are built **without** the voice, which serves only to evaluate them. A later **declared experiment** compares "automatic only" with "automatic + voice". |
| Vision-language model | Where it runs (on our own machine, or in the cloud on frames with faces and plates blurred) is decided **after** Pilot 2. |
| Extras tested | Barometer and magnetometer checks; one UHD (4K) block. |

## 1. Before leaving

- **App permissions:** precise location, microphone, camera, and high sampling rate sensors (Android asks for this one separately).
- **Phone:** Battery Saver off, power bank connected, at least 40 GB free.
- **Settings:** GPS interval 1 s, all sensor groups on, FHD (`camera_resolution` 3) except in `P2-UHD`.
- **Zoom 1.0.** Nobody touches the preview: MultiSensor supports pinch-to-zoom while recording and does not log it.
- **Mounting:** the same orientation as on 14 October. Note which side the lens is on.
- **Printed field card** (section 5), because the phone is in the vest during recording.

## 2. Sessions

Every session follows rules F1–F8 of the [River North plan](RIVER_NORTH_COLLECTION.md): 30 s still start, 3 s curb pause before every crosswalk, fresh WALK at signals, 10 s still end.

It also includes the **sync tap**: right after the 30 s still start, tap the vest mount three times while saying the session ID. The taps appear as accelerometer spikes, audible knocks and a movement in the video, which checks that the three streams line up.

Taylor St follows the River North out-and-back rule. Walk out on the north side eastbound, cross Taylor at the far end (the U-turn), come back on the south side westbound, and cross straight ahead at every intersection. **Route map:** [pilot2-routes.png](pilot2-routes.png).

| ID | Where (from OpenStreetMap, 16 October; verify on site) | Setting | What to do | What it settles |
|---|---|---|---|---|
| `P2-GAME` | A quiet residential corner near Taylor and Racine | `sensors_delay` Game (1) | 30 s still, sync tap, walk 60 s including one corner turn, stand 30 s | Stream rates, file size and battery at Game |
| `P2-FAST` | Same corner | Fastest (0) | Same as `P2-GAME` | The same at Fastest, plus whether video or GPS lose samples |
| `TAYLOR-N` | Taylor St, north side, Racine → Halsted (signals at Racine, Morgan and Halsted) | Fastest | Out leg with full voice protocol | Endurance at Fastest; signal waits; voice load on a busy commercial street; repeat of part of the 14 October red route (Miller–Morgan), so GPS on the same sidewalk can be compared across days |
| `TAYLOR-S` | Taylor St, south side, Halsted → Racine | Fastest (Game if `TAYLOR-N` showed trouble) | Back leg with full voice protocol | Same as `TAYLOR-N` |
| `P2-UHD` | Taylor St, north side, Racine → Aberdeen, **eastbound**: the same view direction as `TAYLOR-N` | UHD (`camera_resolution` 4) | Re-walk the two blocks that `TAYLOR-N` recorded in FHD | Storage per hour and visible detail, UHD against FHD on the same scene |
| `P2-BARO` | Stair at 41.86858, −87.64894 (OSM way 1382580753, 11 m long, no access restriction), about 110 m south-west of Taylor and Halsted. It sits in what looks like a UIC building complex, so check access. Any public stair of at least one storey will do. | Fastest | 30 s still at the bottom, climb, 30 s still at the top, come down, 30 s still. Then step down one ordinary curb and stand 10 s. | Whether the barometer registers a storey and a curb |
| `UNDER-N`, `UNDER-S` *(optional)* | Taylor St between Wood and Paulina. The Pink Line crosses above Taylor there on an elevated structure (OSM layer 2), between Paulina and Hermitage. North side Wood → Paulina, U-turn at Paulina, south side Paulina → Wood. | Fastest | Both legs with voice | GPS, video exposure and magnetometer when passing beneath elevated steel. The track does **not** run above any sidewalk here: near UIC, Paulina St is about 45 m east of it. River North's Franklin St is the real sustained test. |
| `P2-MAG` | Three metal sidewalk grates or vault covers found on site | Fastest | Walk straight over each at normal pace, saying "grate" as you step on it; then walk the same line beside it | Whether the magnetometer shows a mark at grates |

**Suggested order:** `P2-GAME`, `P2-FAST`, `TAYLOR-N`, `P2-BARO` (next to where `TAYLOR-N` ends), `TAYLOR-S`, `P2-UHD`, then the walk west on Taylor to Wood (about 1.2 km, not recorded), then `UNDER-N` and `UNDER-S`. Do `P2-MAG` wherever grates turn up. Between Morgan and Halsted, Taylor has a signalised mid-block crosswalk: say **mid-block** as you pass it, but don't cross it.

**Rough budget:** 2–2.5 h on the ground, about 1.5 h of it recording. At the pilot rate of 9.1 GB per hour for FHD that is about 15 GB, plus the UHD block. The phone drew about 1 Ah per recording hour.

## 3. Voice protocol

Speak **English**, in a normal voice, without stopping.
- **Never talk while crossing.** Say crossing calls at the curb pause, before stepping off, and right after arriving.
- **Describe places, never people.** Never read out a plate or a name.
- **Spoken log** (always):
  - "`<session ID>` start" during the sync tap, and "`<session ID>` end" during the 10 s still;
  - "closed" or "detour" at a closure;
  - "repeat" when walking a passage again;
  - "restart" when restarting a recording.

### 3a. Element code words

Each word is said **when you are alongside the element**, so its time matches the GPS position. A word refers to **your own sidewalk** unless it starts with **"across"**, which means the other side of the street or the street itself.

**Crossing calls.** Make one at each curb pause for the end you are leaving, and one right after stepping up for the end you arrived at. Always say the ramp state, then any extras.

| Say | When |
|---|---|
| **ramp** / **no ramp** | Curb ramp present or absent at this crossing end (always one of the two) |
| tactile | Tactile warning surface at this end |
| button | Pedestrian push button |
| audible | Signal that sounds or speaks |
| unmarked | No painted crosswalk |
| island | Refuge island or median in the crossing |

**Walking zone.** Say these as you pass.

| Say | Meaning |
|---|---|
| obstruction *(+ type)* | Fixed object in or touching the walking zone. Optional type: pole, hydrant, tree, sign, bench, bin, planter, rack, meter, box, café |
| blocked *(+ type)* | Temporary blockage: bins out, parked car or scooter, sign board, delivery |
| damage | Cracks, heaving, holes, missing pavement |
| grate | Metal grate or vault cover in the path |
| narrow | Walking zone clearly narrower than usual |
| slope | Noticeable slope, along or across |
| steps | Steps in the walking path |
| construction | Scaffolding, work zone, temporary walkway |

**Connections.** These matter most for the graph.

| Say | Meaning |
|---|---|
| driveway | Driveway crossing the sidewalk |
| alley | Alley crossing the sidewalk |
| path | A public path branching off the sidewalk |
| end | The sidewalk ends |
| gap | A missing piece: you walk on grass, gravel or the street |
| mid-block | A marked mid-block crosswalk (not crossed unless on the route) |

**Street side:** **bus stop**.

Downtown, ramps are nearly universal and the River North rule may become "say only **no ramp**". Near UIC both states are said, so Pilot 2 can measure how often each occurs.

### 3b. Observations for semantic-context studies

Free speech, always started by **"note"** plus one type word, so speech-to-text can find and sort the notes. Keep each note to one sentence, said while walking, about what is **in view now**.

| Start with | For | Example |
|---|---|---|
| note similar | Something that resembles a place seen before. Say what and where. | "note similar: brick three-flats like the ones on Miller" |
| note use | What the place is used for | "note use: row of restaurants with outdoor seating" |
| note feel | Your own perception: safe, pleasant, noisy, quiet, shaded, exposed, smelly | "note feel: quiet and shaded" |
| note busy | Level of activity, never individuals | "note busy: line at the bus stop" |
| note landmark | A distinctive or named place | "note landmark: church on the corner" |
| note change | Temporary or changing things | "note change: vacant storefront, for lease signs" |
| note access | Doubt about whether a space is public | "note access: gated plaza, looks private" |
| note other | Anything else | |

Notes are subjective by design. They record what a person noticed. That makes them a benchmark for later studies: can image models find the similarities a person recalls, or predict the perceptions a person reports? Notes are never used to build the graph.

**Processing, on our own machine:** speech-to-text with word timestamps. It produces three derived files, kept outside the raw folders:
- the spoken log, into the session manifest;
- `voice_tags.csv`: time, code word, side, nearest GPS fix;
- `voice_notes.csv`: time, type, text, nearest GPS fix.

Raw audio is never published, since it also contains passers-by.

## 4. What is measured afterwards

| Measurement | Decision |
|---|---|
| Rate of every stream at Game and Fastest; file size per hour; battery current; samples lost over the Taylor legs | `sensors_delay` for the main collection |
| GB per hour and visible detail, UHD against FHD on the same block | Video resolution |
| Still time at each signalised curb pause | Signal waits (River North's will differ; first River North day re-measures) |
| GPS on Taylor between Miller and Morgan, 14 against 16 October | Repeatability of GPS on the same sidewalk |
| GPS, video and magnetometer passing under the Pink Line on Taylor | A first look at elevated steel; the sustained test is Franklin St in River North |
| Sync taps in accelerometer, audio and video | Stream alignment and offsets |
| Code words and notes per km; words missed compared with a review of the video on one leg; whether talking interfered with crossings | Practical vocabulary size; whether River North uses "no ramp" only; final word list |
| Barometer change on the stair and at the curb; magnetometer change at grates and under the Pink Line | Whether these sensors join the evidence for steps, levels and grates |
| Vision-language model on one or two anonymised legs, run locally and in the cloud | Where the model runs |

## 5. Field card (print this)

```
START  30 s still · tap tap tap + "<ID> start"        END  10 s still + "<ID> end"
CURB   stop 3 s · fresh WALK only · never talk while crossing · straight ahead
LOG    closed · detour · repeat · restart

CROSSING CALL (leaving curb + arriving curb):  ramp / no ramp  [+ tactile button audible unmarked island]
WALKING ZONE:   obstruction (+pole hydrant tree sign bench bin planter rack meter box café)
                blocked (+type) · damage · grate · narrow · slope · steps · construction
CONNECTIONS:    driveway · alley · path · end · gap · mid-block
STREET SIDE:    bus stop          OTHER SIDE: say "across" first

NOTES  "note" + similar | use | feel | busy | landmark | change | access | other  + one sentence
       places, never people · say it while the thing is in view
```

Related documents: [River North plan](RIVER_NORTH_COLLECTION.md), [collection protocol](COLLECTION_PROTOCOL.md), [research plan](PLAN.md).
