"""walk2net (working name): the pedestrian graph from phone walking recordings. Method: docs/METHOD.md;
architecture: docs/ARCHITECTURE.md.

Everything reads a sideseeing-tools workspace (SideSeeingWorkspace), where every table shares one time base: t,
seconds from the start of the session's video.

    stages/     the pipeline's steps: sync (S1, the data contract and clocks), walk (S2, steps and runs), side_cue and
                zones (phase 0 checks), ground (S3-S4, the camera and the ground), ladder (S5, the walking lines)
    baselines   raw GPS and the GPS + steps smoother, for comparison
    evaluate/   reference (building the scoring reference) and score (S11); never imported by stages/
    plan        field planning: streets and legs from OpenStreetMap
    resultmap   the local result map

The experiments that produced docs/RESULTS.md are in network/experiments/ (python -m experiments.<name>, from network/).
"""
