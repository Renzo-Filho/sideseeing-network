# Pilot data task list

This checklist implements [PILOT_DATA_PLAN.md](PILOT_DATA_PLAN.md). Work in order; each checkpoint is a decision before increasing graph complexity. No analysis or implementation task below is marked complete merely because the GPS overview notebook exists.

## Data readiness

- [ ] **T1 — Inventory sessions and clocks.** Build a manifest for the three raw folders using the researcher's confirmed route IDs; inventory streams/settings/units, inspect video, and test GPS–IMU–video alignment. Recover actual start/end and deviations without assuming a missing field log. **Accept:** every session has route-ID provenance, file/stream status, time base, and documented synchronization limits. **Verify:** spot-check a visible turn or stop against sensor timestamps in each session. **Depends on:** none.
- [ ] **T2 — Audit actual route coverage.** Compare the drawing to each recording; list sidewalk sides, crossings, park paths, overlaps, repositioning, and gaps with source intervals. **Accept:** every intended passage has an observed/partial/not-observed/inaccessible/uncertain outcome; no overlap is inferred from GPS proximity alone. **Verify:** review the critical intervals in video and inspect them on the raw GPS map. **Depends on:** T1.

### Checkpoint A — Evidence readiness

- [ ] Review the manifest and coverage/issue map. Decide whether missing video, clock uncertainty, or unresolved route details block any intended graph case; target only those cases for reacquisition.

## First graph

- [ ] **T3 — Define graph and evidence records.** Specify node roles, passage classes, edge endpoints, traversal eligibility, source/time references, and unknown/conflict states using pilot examples. **Accept:** opposite sidewalk sides, one crossing, a coverage endpoint, and a park path can be represented without implied connections. **Verify:** walk through the examples and their route-query consequences on paper. **Depends on:** T2.
- [ ] **T4 — Compare street-level baselines.** Produce GPS-only and GPS-plus-synchronized-evidence candidate graphs for the observed pilot footprint. **Accept:** both retain raw trajectory references, distinguish candidate from confirmed connectivity, and report unresolved side assignments. **Verify:** inspect element counts, duplicate/false joins, crossing continuity, and differences between the two variants. **Depends on:** T1–T3.

### Checkpoint B — Topology review

- [ ] Review failure cases before selecting matching tolerances or aerial reconciliation rules. Record any change to the graph contract.

## Fusion and pilot conclusion

- [ ] **T5 — Reconcile aerial hypotheses.** Add visible aerial candidates and explicit correspondences while retaining source-only and conflicting elements. **Accept:** every union element identifies which of GPS, IMU, video, and aerial imagery support it; absent support and unresolved matches stay visible. **Verify:** inspect cases with close parallel paths, crossings, occlusion, and 2D intersections. **Depends on:** T4.
- [ ] **T6 — Evaluate and decide.** Freeze criteria, create a small independent reference, report topology/association/coverage errors and acquisition costs, and select a targeted second-pilot question. **Accept:** a report states what this pilot supports, what remains unresolved, and a specific next collection or method experiment. **Verify:** independently inspect referenced cases and rerun basic route queries on eligible edges. **Depends on:** T2–T5.

### Checkpoint C — Pilot decision

- [ ] The graph variant, evidence trail, evaluation limits, and targeted next experiment are reviewable by the researcher. No general Chicago performance claim is made from these three sessions.
