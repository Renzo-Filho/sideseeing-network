"""Passage graph construction, as planned in docs/GRAPH_GPS_PLAN_2026-10-24.md.

Everything reads a sideseeing-tools workspace (SideSeeingWorkspace), where every table shares one time base: t,
seconds from the start of the session's video. Phase 0 checks the data contract before any graph is built:
contract (sessions and clocks), runs (the walk cut into runs), side_cue (which side the road is on) and zones
(whether the masks separate a sidewalk's zones). `python -m graph.phase0` runs them.
"""
