Chicago-only Model

Why Chicago can be easier, and why it is not automatic
For a Chicago-only model, we can ask whether each number describes Chicago well without first matching a São Paulo tax field or map class. That is a real simplification. We still have to decide what the feature counts and whether its Chicago data cover the whole city fairly. The existing local tables are starting evidence, not a finished Chicago score. A new contract would choose the features, years, missing-data rules, weights, and Chicago-based scales before ranking the 77 Community Areas. M2 is excluded; B1 and BV are retained for review. The descriptions below keep the same interpretation as above and focus on what Chicago alone still needs.

M1: Street-network density
What it would say: Which Community Areas have more mapped street length for their size. A tight grid and a knot of highway ramps can both produce a high number.
Why it is still unfinished: The city and Overture maps include different roads. At O’Hare, some city class-99 lines are airport circulation, not ordinary neighborhood streets. We need one rule for streets, ramps, divided roads, and map edges, followed by local checks. Status: plausible citywide candidate, not yet accepted.

M2: Intersection density
What it would say: How frequently streets meet and offer a possible change of direction.
Why it is still unfinished: Nearby map points can be parts of one divided-road crossing or different upper and lower roads. Chicago endpoint and connector counts are useful experiments, but they are not confirmed real junctions. Status: deliberately excluded; no M2 value or weight belongs in the new Chicago score.

M3: Block size
What it would say: Whether Chicago’s street-bounded land is divided into small, fine-grained blocks or large, coarse-grained ones.
Why it is still unfinished: The 23,204 newly generated land faces include true blocks, but also motorway islands, airport land, uncertain railway edges, and faces merged across a missing street. The West Veterans Place split is proposed, not independently verified. A full set of independently traced blocks—including ones the computer misses—must test the repair method across very different neighborhoods. Status: not accepted.

M4: Block shape
What it would say: Whether those blocks are compact or long and narrow, a clue to possible detours.
Why it is still unfinished: A false sliver or a merged block can dominate the shape statistics. We must first settle M3, then measure the whole outline without letting a Community Area border create a fake edge. Status: not accepted.

M6: Street-class composition
What it would say: How much of each area’s mapped street length is local street, major road, motorway, and other classes.
Why it is still unfinished: Chicago can choose a local classification without matching São Paulo, but it must choose one consistent street map, check O’Hare and peripheral coverage, and leave truly unknown roads visible. Status: calculated candidate, not yet accepted.

M7: Physical parcel density
What it would say: Whether land is split into many small property units or a few large ones.
Why it is still unfinished: A Cook PIN might identify a condo unit rather than a ground parcel, and DuPage has its own records. A simple row count could make one apartment tower look like dozens of separate land pieces. The parent relationships still need verification. Status: not accepted.

B1: Building-footprint coverage
What it would say: How much ground in a Community Area is covered by mapped buildings, regardless of their height.
Why it is still unfinished: Full citywide Overture and older municipal candidates exist, but we need to check where each map misses or adds buildings and whether the land denominator follows a reasonable water boundary. Status: retained, not yet accepted as a score input.

B2: Reported floor counts
What it would say: The middle and taller end of Chicago buildings that actually report stories.
Why it is still unfinished: Only 52.16% of assigned active municipal buildings have a positive story report, and coverage varies greatly by area. Zero often means no report. Broad labels, split levels, condos, commercial properties, and DuPage gaps may bias the reported subset. Status: a useful subset diagnostic, not an accepted whole-stock feature.

B3: Constructed floor-area intensity
What it would say: How much indoor built area is recorded relative to the land underneath it.
Why it is still unfinished: Chicago has several partial area fields, not one verified all-building total. They define space differently and can repeat a parent building’s area for many condo records. If a complete, nonduplicated source cannot be established, original B3 should be omitted explicitly rather than replaced by footprint or estimated volume. Status: not accepted.

Supplemental BV: Estimated vertical form
What it would say: Whether a Community Area appears taller on average in a broad GHSL grid, even if B1’s ground coverage is similar.
Why it is still unfinished: Compare selected cells with local building evidence and inspect zeros, missing cells, water, and district edges. Keep height and volume under one family weight and test what changes if BV is left out. Status: retained, not yet accepted; it is not a replacement for B2 or B3.

U1: Land-use diversity
What it would say: Whether mapped Chicago land is mostly one use or spread among homes, commerce, industry, institutions, and other uses.
Why it is still unfinished: The CMAP eight-group calculation exists, but roads and other nonparcel land marked 6000 cover meaningful area. Mixed, vacant, secondary, and unknown uses need a declared rule; otherwise a diversity score can change just because one area’s map classifies more land. Status: candidate, not yet accepted.

U2: Workplace-job density
What it would say: Where LODES reports concentrations of jobs within Chicago.
Why it is still unfinished: Jobs are reported by Census block, while Community Area boundaries sometimes cut blocks. Moving jobs according to block area or likely business land changes estimates, especially around boundaries and downtown. We must state which jobs the source includes and preserve source-file lineage. Status: candidate, not yet accepted; matching Brazil’s RAIS is not required for the local model.

U3: Resident-population density
What it would say: Where Chicago Census residents live per square kilometre, distinct from daytime crowds.
Why it is still unfinished: The 2020 block counts and area allocation are already well documented, making this one of the clearer local candidates. Yet the contract must state how boundary-crossing blocks and small uncovered gaps were handled. An older supplied ACS Community Area total has uncertain period and should remain separate. Status: close to a defined local measure, but not formally accepted for the new score.

U4: Reachable bus supply
What it would say: How much scheduled CTA bus service is near residents during a chosen morning or weekend window.
Why it is still unfinished: Several radii and days have been calculated, but one main window and rule must be chosen before fitting. The CTA feed excludes Pace, schedules are not observed reliability, and a straight-line distance can cross barriers. Status: candidate, not yet accepted.

How the Chicago-only work can help the cross-city comparison
Validating Chicago first can give us trusted examples of real versus false blocks, missing roads, mapping gaps, and incomplete building records. Those examples reveal what a future common definition must survive. But a locally useful Chicago number does not automatically become a comparable São Paulo–Chicago number. The later model must define the same idea in both cities, rebuild changed measurements in both, learn its numerical scales from São Paulo, and apply those saved scales to Chicago without silently changing the meaning of a feature.

Status basis
This account follows the current project status and the Chicago-only reassessment, 13-family completion ledger, B1/BV decision, six-family reassessment, physical-block protocol, and dated result reports in the repository. Passing arithmetic checks means the calculations are reproducible; it does not by itself prove that the maps represent the real world or authorize a model fit.
