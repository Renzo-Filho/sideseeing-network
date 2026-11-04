# network/data (local only)

Field captures and everything derived from them. Git ignores this folder except this page. Nothing here is published: the videos show people, the audio is raw voice, and the Cook County parcels may not be redistributed.

```text
data/
  sources/            public downloads, read-only
    chicago_planimetrics/   City of Chicago curbs (5gv8-ktcg) and sidewalks (77cn-6x4c), zips + metadata
    imagery/                Cook County 2025 orthophoto crops (UTM 16N) cached by the notebooks
  west_loop/          the collection area
    plan/             routes.py and route_methods.py output: osm_<date>.json, routes.gpkg, sessions.csv, cards/, routing/, status/
    raw/              MultiSensor capture folders kept locally (day 2, 2026-10-20). Day 1 is read from Drive
    derived/          per-session tables from the notebooks and transcribe.py (<session>/), and day<N>_*.csv/gpkg
    workspace/        copy of the desktop-01 sideseeing-tools workspace: frames, preds (SAM3), motion, transcripts
    reference/        Morgan reference (curbs, back of sidewalk, parcels); Cook terms: local only
    graph/            graph phase outputs (phase0, phase2a*, phase2b*) and map.html
    review/           review prototypes (dataviz, Whisper)
  pilots/
    pilot1_2026-10-14/      raw/ (3 sessions, Near West Side), workspace/ (sideseeing-tools; data/ links into raw/)
    test_shapes_2026-10-15/ raw/ (3 GPS test shapes)
    pilot2_2026-10-16/      raw/ (1 session, voice protocol), derived/
  _archive/river_north/     the dropped area's route plan
  _transfers/               rclone run records: bras/ (state, lock, logs), west_loop/ (logs, exit codes)
```

Rules:
- A capture folder (`<yyyy-mm-dd-hh-mm-ss-ms>/` with `video.mp4`, `gps.csv`, sensor CSVs, `metadata.json`) is never edited. Anything computed from it goes to the area's `derived/`, `workspace/` or `graph/`.
- Do not keep a zip next to its unpacked folder: check the zip against the folder, then delete it.
- The disk is nearly full. Read large captures from Drive (`network/scripts/drive.sh mount`) instead of copying them here.
