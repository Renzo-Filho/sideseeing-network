# Full-scope paired morphology pilot flags

The [pilot CSV](paired_m2_m3_m4_pilot_flags.csv) reuses the sealed H1–H3 source candidates without changing them. Its eight units are the original five Chicago and three SP processing fixtures. A connector pair within 10 m is **only a flag for inspection**: it can represent one divided-road junction, two distinct nearby junctions or mapping segmentation. Enclosures under 6 m width and over 1 km² are likewise flags, not automatic deletions.

Loop (`CHI:32`) has 71 near connector pairs involving 84 of 389 candidates and 125 narrow enclosures among 455; Brás (`SP:10`) has 13 near pairs involving 26 of 399 and 2 narrow among 244. This reveals materially different artifact pressure in the dense pilots. O'Hare (`CHI:76`) has six enclosures over 1 km²; the SP Grajaú fixture (`SP:30`) also has six. Neither metric establishes true intersection/block counts. The existing [Chicago Loop map](../harmonization_2026_09_22_h1_h3/roads/Chicago_32_pilot.png) and [SP Brás map](../harmonization_2026_09_22_h1_h3/roads/SP_10_pilot.png) show candidate geometry but need manual labeling of physical junctions, barriers and true block edges.

Reproduce with `.venv/bin/python analysis/scripts/review_paired_junction_block_pilots.py`. The next method step is to label paired examples, implement physical-arm consolidation and a separate block boundary network, then check those definitions before a full-city rebuild. M2/M3/M4 remain unavailable for fitting.

## Source-rule candidate continuation (22 September)

The [M2 source-topology review](junctions_v2/README.md) rejects distance-only merging: Loop has a 2.49 m close pair on different Overture levels, while the Brás fixture has a short same-street link. The [M3/M4 boundary sensitivity](blocks_v2/README.md) compares four common line-selection modes, including scoped road-rule intervals, in all eight pilots. Loop changes substantially and requires physical block annotation. These are diagnostic artifacts; **M2/M3/M4 remain unaccepted**, and the 13-family fit remains prohibited.

## Barrier continuation

The [paired rail/water barrier pilot](blocks_v3_barriers/README.md) rejects rail centerlines and arbitrary rail corridors as universal M3/M4 boundaries. A land-only shoreline sensitivity improves Loop reference coverage but is not yet an accepted physical-block rule.

## Local rail and matched-road continuation

[City-local rail envelopes](blocks_v4_local_rail/README.md) did not provide an equivalent shared M3/M4 boundary. The [173-unit M1/M6 scope review](m1_m6_review/README.md) locks the ten-class mapped-road method for review, documents O’Hare/Marsilac coverage outliers and the pedestrian-street mismatch in older block pilots, and keeps strict fitting closed.
