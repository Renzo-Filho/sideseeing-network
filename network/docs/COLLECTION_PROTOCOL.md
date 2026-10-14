# Chicago sidewalk-network collection protocol

Working draft, 13 October 2026, updated through interview Q19. The immediate collection is a small Near West Side pilot near UIC, not the entire community area; see [PILOT_NEAR_WEST_SIDE.md](PILOT_NEAR_WEST_SIDE.md). The broader target remains full street-adjacent sidewalk coverage, on both sides of streets, in a community area selected for feasible collection within one to two weeks. Each collector will use MultiSensor on their own device, with the existing data-collection vest setup. One pass per sidewalk is the agreed baseline; planned overlaps are permitted and must be highlighted. Actual person-hours, device inventory, detailed boundary rules, and field-verified routes remain to be settled.

## Purpose and agreed constraints

Collect the observations needed to reconstruct a general-walking passage graph and associate its geometry and connectivity with GPS, inertial, street-video, and public aerial evidence. The team consists of Renzo with at most two volunteers; availability need not be simultaneous. A Chicago community area will be selected later.

**Collection decisions from Q13–Q15:** area size affects feasibility; the intended target is all sidewalks in the selected community area, with working hours arranged within a one-to-two-week collection period. Each person will record with MultiSensor on their own phone. Renzo will register devices once volunteers are confirmed. The earlier compact-core default and preference for one or two standardized phones are superseded. Neither volunteer availability nor daily recording throughput has yet been established.

**Collection decisions from Q16–Q19:** focus on street-adjacent sidewalks, collecting both physical sides of each street once. Internal park paths and other non-street passages are outside the initial systematic coverage target. Use the available data-collection vest setup; handheld capture is not the planned default. The researcher expects the represented passages to be bidirectional in most cases. Repeated sections are permitted for practical route continuity/efficiency and must be documented and highlighted; universal two-direction collection is not required.

**Immediate pilot:** Renzo alone will use a moto g 5G (2023) with MultiSensor and the collection vest. The three researcher-drawn routes run between Aberdeen and Morgan, Polk to Taylor; see the [route drawing](PILOT_NEAR_WEST_SIDE.md) and [solo field protocol](PILOT_PROTOCOL.md). UIC campus sidewalks are excluded. The drawn public mid-block paths are a pilot-only exploratory exception and will be reported separately from street-adjacent sidewalks. The broader campaign's team and street-adjacent scope are unchanged. This pilot does not commit to surveying the whole Near West Side or select it as the final comparative-study community area.

Construction will be automatic. Field administration and capture quality checks are permitted; a separate human-verified evaluation reference is agreed. Do not turn fieldwork into a manual barrier-labeling or GPS-correction exercise.

No diagonal road shortcuts are planned. A genuinely diagonal sidewalk/crosswalk can be captured along its actual alignment. Other crossing-selection details depend on the selected site and reconnaissance.

This draft adapts the Brás report as inspiration. It does not adopt that report's instructions as requirements, presume its app settings are current, or transfer its productivity estimates directly to Chicago.

## Lessons from Brás and proposed adaptations

Source: `RELATÓRIO DA AUDITORIA DE CALÇADAS - BRÁS.txt`, supplied by the researcher, local path `/home/renzo/Downloads/RELATÓRIO DA AUDITORIA DE CALÇADAS - BRÁS.txt`. Line references refer to this supplied text version.

| Reported practice or result | Implication for this research |
|---|---|
| Two preliminary field tests preceded the audit (lines 270–271). | Run a technical pilot before committing the main collection budget. |
| Route maps distinguished direction, recording start/stop locations, recorded passages, and repositioning travel (327–329). | Preserve these distinctions in route cards and the workload estimate. |
| Teams were described as pairs or trios (278). | Treat volunteers as additional capacity only when recording equipment and roles justify it; three people do not automatically mean three independent recording streams. |
| Planned travel totaled 126.7 km, including repositioning (329). | Keep total collector travel separate from unique sidewalk coverage. |
| Four visits typically lasted five to six hours; some had local support (336). | Do not assume this research team can reproduce the audit's organization or daily output. |
| Forgotten crossings, re-recordings, crowded passages, and a street market required revisits (343–344). | Maintain separate crossing coverage and a targeted revisit list. |
| The report recommends around 6 km per researcher/day; its reported mean was 7.9 km/day, and it estimates effective movement at 2–3 km/h (343–344). | These are historical context, not Chicago targets. Estimate capacity from the local pilot, including delays, equipment checks, and data handling. |
| Manual review corrected 64,700 GPS points, and the report identifies that review as a scaling bottleneck (350–359). | Preserve uncorrected observations. Localization errors belong to reconstruction experiments; manual edits belong only to an independent reference, if used. |
| The Annex used a displayed −75° mount angle, one-second location/network intervals, and five-second start/end waits (793–809, 835–845). | Test field of view, actual timestamps, signal acquisition, and sampling on the chosen devices. Do not assume this angle, interval, or waiting time meets our needs. |
| Its historical storage observation was about 10 GB per person/day for 6–9 km, at FullHD (footnote 11, line 1229). | Measure GB per recording hour and battery consumption in the pilot. |

## 1. Select a community area against the full-coverage workload

**Agreed target:** cover street-adjacent sidewalks on both sides of streets in the selected community area within one to two weeks. The selected area's size and pedestrian network determine whether this is feasible for the available collectors. A connected core with optional expansion is no longer the default collection scope. Connecting street crossings remain part of the planned network collection; their inventory and boundary-street treatment will be made explicit during route planning.

**Proposed selection procedure:** for candidate areas, estimate sidewalk-side length, crossing targets, repositioning, repeat/revisit burden, and practical access; check public imagery coverage and acquisition dates. Compare the estimated effort with confirmed person-hours and pilot-measured throughput before finalizing the area. Square kilometers alone do not define the collection workload. Retain the research criteria for neighborhood selection alongside operational feasibility, and document the resulting limits on cross-city or citywide comparisons.

The immediate pilot is a small sample of Near West Side near UIC; its routes and objectives are documented separately in [PILOT_NEAR_WEST_SIDE.md](PILOT_NEAR_WEST_SIDE.md). Its limited extent does not replace the later full-area collection target. If a candidate area for the later study cannot fit the available effort, revisit area selection or the resource/window commitment explicitly rather than silently changing the target to partial coverage. No full-study feasibility conclusion is possible until the area and available person-hours are known.

## 2. Define coverage before drawing itineraries

Use a provisional coverage inventory to organize fieldwork. It is not the reconstructed graph or its ground truth.

| Fieldwork unit | What to plan and track |
|---|---|
| Sidewalk-side segment | One physical side of a street between recognizable reference locations. The opposite side is a separate target. |
| Crossing | A specific connector with both approaches, the road traversal, and the arrival visible in a continuous recording where feasible. |
| Junction transition | The sidewalk movement around a corner or into a branch; merely observing nearby segments does not establish this transition. |
| Route join | Shared observed passage near the end/start of two collection modules, so their association can be studied. |
| Repeat | A deliberate additional traversal of selected passages, marked separately from unique coverage. |

Use map-based candidate targets to plan coverage, updating the inventory when field conditions differ. Candidate IDs and planned connectivity must not silently be supplied as verified answers to the reconstruction method. If a later experiment uses route plans as priors, declare that input explicitly.

Do not count a crossing as traversed merely because it appears in video from a nearby sidewalk. Distinguish observed-from-a-distance, traversed, and not recorded.

## 3. Build short, connected route modules

1. Inventory sidewalk sides and candidate crossing targets within the chosen perimeter.
2. Group adjacent targets into routes with clear start/end landmarks, direction arrows, and a practical return or rendezvous location.
3. Distinguish mandatory capture, transit/repositioning, deliberate repeat, and optional extension on each route card.
4. Review crossings individually. Walking the perimeter of a block does not automatically record every crossing joining that block to its neighbors.
5. Give neighboring modules a deliberate shared passage where practicable; do not depend on two noisy endpoint coordinates meeting exactly. Decide overlap length after the pilot.
6. Allocate routes by expected total field time, including waits and repeated travel, rather than sidewalk length alone.
7. Reserve capacity for fixing failed captures. Optional supplementary observations may be deprioritized, but required sidewalk coverage must not be silently dropped to fit the schedule.

**Agreed sidewalk collection depth:** one usable traversal of each physical sidewalk side. Overlap is allowed for efficient, continuous walking routes and must be explicit in the plan. Reacquisition of unusable captures remains possible and is recorded as a revisit, not new unique coverage. One usable traversal of each required crossing is the proposed crossing baseline. Repeated traversals are diagnostic observations, not automatically independent ground truth.

Each planned overlap must have an ID, street and sidewalk side, clear start/end references, participating route IDs, direction(s), reason, and an estimated repeated length when measured. Route cards must use both a visual style and a text label such as `OVERLAP O1`, rather than color alone. Distinguish first-pass capture, overlap capture, and repositioning. Count a physical passage only once in unique coverage, even when multiple recordings support it. Log unplanned repeats after collection using the same distinction.

**Direction distinction:** the two sidewalks on opposite sides of a street are separate physical passages. Each may permit movement in both directions. A capture has its own observed direction, which must be preserved without automatically imposing that direction on graph connectivity. The expectation of mostly bidirectional passages does not establish that reverse-direction video/sensor evidence was collected; one pass per sidewalk is the agreed baseline.

A field route is an ordered walk through planned targets. It is not a graph edge. One recording may support several graph elements, and several recordings may support one element.

## 4. Assign routes to collectors using their own phones

Each participating collector will use MultiSensor on their own device and the existing data-collection vest setup. Registration follows volunteer confirmation. The acquisition procedure should be consistent across devices; identical hardware is not required. Check how many complete vest/mount setups are available when assigning simultaneous routes; the number has not been established. Route allocation is still a proposal.

| Available team | Proposed main-collection arrangement |
|---|---|
| Renzo alone | One recording stream, collecting assigned modules in sequence. Check the full-area workload against actual capacity. |
| Renzo + one volunteer | Up to two recording streams, with explicit module and crossing assignments and planned overlap. Availability and device checks determine actual throughput. |
| Renzo + two volunteers | Up to three recording streams, with route ownership and a shared progress log. Coordination, quality review, and field delays still consume time. |

A joint onboarding/pilot session is proposed before splitting into assigned routes. Registration should include collector/device ID, model, OS/app version, exported sensor availability, camera configuration, and mounting arrangement. Use a short shared test passage to expose gross differences between acquisition setups; it is not a controlled estimate of device effects because collector and device may differ together. Record later changes. Do not assign different units or sample-rate assumptions to all phones merely because they use the same app.

Route assignments must accommodate non-simultaneous volunteer attendance. A route card should remain usable by another collector if reassigned, while preserving the actual collector/device provenance. An accompanying non-recording person adds support rather than unique coverage.

## 5. Technical pilot and settings record

Before the main survey:

- Inventory device model, OS/app version, camera orientation, mounting method, and the actual exported sensor streams.
- Check every participating device after registration. Select compatible acquisition settings where possible, and retain each device's actual export schema and sampling behavior. Numerical sampling/video settings are not yet fixed.
- Test phone fit, stability, and a repeatable camera view using the existing collection vest, with the actual phone and wearer. The view should show the walked passage and relevant crossing/junction context. The surface-oriented Brás view is a starting candidate, not a fixed angle requirement.
- Check a short stationary period, straight walk, turn, crossing, and recording restart. Inspect exported video, location and inertial records for continuity, timestamp conventions, gaps, and practical alignment.
- Verify that the recording state and location updates are established before leaving; determine a suitable start/end procedure empirically rather than assuming five seconds guarantees readiness.
- Measure recording-hour storage, battery consumption, usable-capture rate, field travel time, and time spent transferring/checking data.
- Record settings and keep them stable during the main collection. Document any necessary change rather than silently mixing acquisition configurations.

The report's “GPS calibration” instruction is not adopted as a verified remedy. The pilot must establish observed positioning behavior on the actual devices.

Audio is not yet a required research modality. A written session identifier is sufficient for the proposed administrative log; whether to capture audio or use spoken identifiers remains a settings decision.

## 6. Field sequence per module

**Before walking:** confirm route/session ID, collector/device, configuration, charged battery/storage, and the mounting view using a short test. Start from a recognizable location outside the critical transition being studied.

**During capture:** walk the actual sidewalk passage at an ordinary comfortable pace. Follow the intended crossing alignment; keep recording through approach, waiting, traversal, and arrival when feasible. Do not stop or restart recording in the middle of a crossing merely to match a route-card boundary. Avoid unnecessary camera handling or deliberate sideways pans during the main motion record; document adjustments or separate supplementary views.

If the intended passage cannot be completed, record the deviation when stopped and mark the target for review. Do not invent a connection from the planned itinerary or force completion for coverage. A detour is an observed trajectory with a reason; it must not silently substitute for the unrecorded target.

**At completion:** finish beyond the last critical transition, verify that the recording saved, and log interruptions, changed device/mount, obstruction, or skipped targets. Start a new session after a failed/restarted recording and retain the relationship to the intended module. Do not conceal failed sessions by reusing their identifiers.

Precise session length and overlap distance remain pilot outcomes. Long enough to preserve transitions and short enough for manageable recovery is the proposed tradeoff.

## 7. Minimal field records and end-of-session review

Maintain one lightweight manifest:

- Route/module ID, capture folder/session ID, date, collector, and device/configuration ID.
- Actual start/end times or timestamp references; distinguish planned direction from any deviations.
- Status of required targets: pending, recorded awaiting quality review, usable, partial, revisit needed, or not applicable with reason.
- Interruptions, occlusion, equipment changes, relevant weather/lighting or surface conditions, and intended repeats.

These are acquisition records, not manually assigned accessibility labels or corrected topology.

After each field session, copy the original capture folders intact, preserve their names and raw contents, and verify the copy and file readability before deleting anything from the device. Check that required streams exist, timestamps are plausible, recording durations overlap as intended, and critical transitions are visible. The exact completeness checks must follow the verified data contract, not the screenshot alone.

Plot raw GPS over imagery as the first diagnostic. Keep anomalous trajectories visible and investigate them; do not move points manually to make the map appear correct. Use the review to prioritize specific reacquisition needs rather than rewalking everything.

## 8. Capacity and coverage accounting

Estimate workload from the pilot using:

> Field effort = capture travel + repositioning travel + deliberate repeats + crossing waits + setup/checks + breaks and interruptions.

Budget data transfer and post-field review separately. Count time per person and concurrent recording setups explicitly: two people walking together for two hours use four person-hours but may produce only one recording stream.

The one-to-two-week window is agreed; hours per collector and actual attendance will be arranged later. Do not convert this calendar window into an assumed number of full working days. Before final area selection, compare total required effort with the sum of confirmed collector-hours, including coordination and quality-review responsibilities. Preserve a revisit allowance within the schedule; its size should follow the pilot. Whether onboarding precedes or occupies part of the collection window remains to be arranged.

Report at least four separate quantities:

1. Unique sidewalk-side coverage, with the method used to estimate length.
2. Unique crossing targets successfully traversed/recorded, plus unresolved or missed targets.
3. Total recorded travel, including repeated segments.
4. Total collector travel and field/post-field person-hours.

Report coverage relative to the selected community-area scope and the provisional inventory, including denominator revisions when new passages are discovered. Define boundary-street and non-street-path treatment before claiming full coverage. Do not call planned-target completion proof that every physical passage has been discovered. GPS sample length alone is not an established measure of unique sidewalk length.

## 9. Independent evaluation

Reserve a separate verification procedure for selected topology cases. An evaluator can use field inspection or recorded evidence to identify actual passages/connections, while keeping those reference labels out of construction and held-out tuning. When possible, establish the reference before exposing the evaluator to the model output.

The field team may later contribute to evaluation; a separate large labeling workforce is not assumed. Separate files and declared roles/timing matter more than pretending that routine capture logs constitute independent ground truth. Repeat recordings and aerial agreement are useful checks but are not substitutes for the agreed reference.

## Decisions to settle in the next interview round

1. **Pilot logistics:** Renzo is the sole pilot collector with a moto g 5G (2023). Mark actual starts/finishes and overlap landmarks on the working route map, verify current access and choose the field date; see the [solo field protocol](PILOT_PROTOCOL.md).
2. **Site-dependent coverage:** specify the pilot crossing inventory and coverage endpoints, then boundary-street treatment for the later full study. Street-adjacent scope and one pass per sidewalk with highlighted overlaps are already settled.
3. **Registration and pilot details:** record devices and available vest/mount setups after volunteer confirmation, then verify framing, export behavior, and feasible concurrent collection. Use of the collection vest is already settled.

Once these decisions are settled, define module size, repeat allocation, crew assignments, acquisition settings, and acceptance/revisit criteria. Exact routes require selecting the community area and inspecting its actual pedestrian layout. Device registration and detailed availability follow volunteer confirmation; they are not prerequisites for discussing these remaining policy choices.

## Proposed completion criteria for the collection stage

- The selected community-area boundary, coverage definition, candidate inventory, exclusions, and actual collection conditions are documented.
- Every required target has an explicit final coverage/quality status; gaps are retained and explained.
- Raw multimodal recordings, settings, and provenance are preserved and linked to the manifest.
- Main capture includes usable junction and crossing transitions, not just disjoint sidewalk fragments.
- A separate evaluation reference and its independence limits are documented.
- Pilot-measured effort, repeat/revisit costs, and remaining uncertainty are reported.

Companion research plan: [PLAN.md](PLAN.md).
