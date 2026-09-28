# Eight paired block fixtures against local references

`analysis/scripts/review_block_reference_fixtures_v2.py` rebuilds all four boundary modes in the five Chicago and three São Paulo pilots, verifies every candidate count against `../paired_boundary_sensitivity.csv`, and compares **whole owned polygons** by best intersection-over-union (IoU) in both directions. Candidate-to-reference agreement reveals spurious subdivisions; reference-to-candidate agreement reveals missing or merged reference blocks. The threshold reported below is IoU ≥ 0.50. All polygons, best matches, plots for Loop and Brás, and [six structured fixture annotations](fixture_annotations.json) are saved here. Two independent synthetic IoU fixtures pass in `analysis/tests/test_block_reference_fixtures_v2.py`.

Chicago's reference is 2020 Census blocks, which may use boundaries besides physical streets and can differ from a street block. São Paulo's reference is the eligible municipal Quadra layer, with its own source vintages and type rule. Both references are **city-specific diagnostics**, never common model inputs or ground truth for every polygon. The same largest-overlap whole-object district ownership rule is used for references and candidates; geometry is not clipped to the district.

| Unit | Reference objects | All-street candidate / reference match | No-link candidate / reference match | Whole-grade-filter candidate / reference match | Interval-aware candidate / reference match |
|---|---:|---:|---:|---:|---:|
| CHI:24 | 1,125 | .453 / .290 | .492 / .291 | .481 / .261 | .479 / .258 |
| CHI:28 | 908 | .508 / .525 | .634 / .534 | .628 / .420 | .626 / .417 |
| CHI:30 | 663 | .323 / .151 | .337 / .149 | .336 / .143 | .332 / .140 |
| CHI:32 | 343 | .287 / .379 | .372 / .397 | .471 / .327 | .571 / .306 |
| CHI:76 | 244 | .234 / .209 | .316 / .197 | .377 / .176 | .377 / .176 |
| SP:10 | 153 | .605 / .961 | .690 / .915 | .778 / .895 | .778 / .895 |
| SP:30 | 1,481 | .782 / .820 | .795 / .820 | .803 / .810 | .804 / .810 |
| SP:35 | 564 | .590 / .965 | .690 / .945 | .739 / .941 | .739 / .941 |

Every filtered mode raises the candidate match share over all streets in all eight units. Yet **neither grade-filtered mode raises reference match share in any unit**; filtering merges or loses reference blocks. No-link filtering raises reference match in only three units and lowers it in four (SP:30 is effectively unchanged). Thus candidate precision alone would choose an overly aggressive rule. Loop illustrates the failure: the interval-aware mode yields no owned enclosure within 140 m of the stacked-road fixture center, even though 13 owned Census blocks intersect that circle. It improves the median *surviving* candidate's IoU while losing coverage. The [Loop comparison figure](CHI_32_reference_comparison.png) and [Brás figure](SP_10_reference_comparison.png) show this directly. At O'Hare (CHI:76), low overlap persists in every mode, consistent with a difficult edge/airport case that needs separate inspection.

The six annotations distinguish source-verified topology from reference-only interpretation. The Loop 2.49 m connector pair is a **definite false distance merge** because its streets are on different source levels. The Brás 8.28 m pair is source-linked but still has no certified physical-arm count. A 3.01 m² Loop line enclosure has negligible Census overlap; a 51.79 m² Brás wedge has no eligible Quadra overlap. These are selected diagnostic fixtures, not a calibrated error rate. No polygon was deleted by size to improve agreement.

**Decision:** reject both grade-filtered modes as complete M3/M4 boundary networks at this stage. Keep all-streets and no-links as diagnostic baselines. Do not accept either as a shared physical-block definition: rail/water barriers, campuses, islands, reference vintage and Chicago Census versus SP Quadra semantics remain unresolved. The source-linked M2 complex also needs local physical-arm annotation. Continue with an explicit barrier/ground-road construction and matched imagery review before rebuilding 96/77 family measurements.
