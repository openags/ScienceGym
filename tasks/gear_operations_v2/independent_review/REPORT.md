# Independent review: gear metamaterial task design

DOI: 10.1038/s41563-022-01269-3

## Decision

**Pass for the declared source-grounded, gated task-design scope.** All findings raised in this review were remediated and independently retested. The final snapshot passes 85 independent static/source assertions, 40 targeted adversarial probes, 1,178 generated record mutations and the 65-test author suite. This does not certify execution readiness, trusted hardware verification or scientific replication.

## What was reviewed

The review used the existing lawful source audit and manifest, all authored JSON contracts, physical recipes, evaluator/actor boundaries and Python verifier. Focused checks against already-acquired local text confirmed the micro-Taiji steel-shaft connection, planetary dimensions and module conflicts, and integrated printing/support-removal distinctions. The reviewer did not reacquire publisher content, conduct a new correction search, independently reread every source page or watch the videos. The inherited evidence covers complete written material and eight sampled frames for each of five videos, without full-motion or audio inspection.

An independently authored static checker passes 85 assertions. These include the 18 physical branches, distinct specimen sizes and family IDs, all required fixture types, explicit interstation movement, post-load handling, open dimensional gates, source/unknown reference integrity, first-cycle and uncertainty semantics, and source/model/illustrative separation. The author suite was independently rerun after remediation and passed all 65 tests, including positive subcases for every physical branch and a whole-paper synthetic campaign.

## Source fidelity and physical completeness

The package preserves 5×5 quantitative macro-Taiji specimens separately from the 4×4 illustrative video specimen. It keeps the 5×6 micro-Taiji fabrication, 4×4 compression and 5×5 motorized specimens distinct, and retains the six different planetary material/scale/loading specimen sizes. The soft 4×4 designation is explicitly a metacell count rather than an inferred gear count. Impact has its own 3×3 polymer family and approximately 2.0-GPa declaration rather than inheriting the general 2.5-GPa macro-polymer card.

Preparation is represented by material acceptance, qualified fabrication, supported release, boxing, support removal, assembly, shaft capture, metrology and phase checks. Transport has explicit destinations; imaging and analysis remain logical operations at the specimen's current location. Mechanical routes include fixture selection, calibration, seating/clamping/pinning/grooves, zeroing, acquisition, bounded loading, raw closure, unloading, release, post-inspection and cleanup/storage. Actuation now explicitly arms and seals capture, isolates drives and releases couplers. Impact assigns loading, guarding, release and safe retrieval to a qualified enclosed service, followed by terminal quarantine.

Three early design concerns were corrected: geometric conflicts now require geometry-specific evidence; Taiji steel frames have explicit component-material bindings; and actuation has explicit acquisition/sealing/release boundaries. No author-certified CAD, material grade, operating envelope, calibration, robot embodiment or execution card has been invented. Those remain mandatory open gates.

The micro-planetary sun-radius disagreement, suspect planet-radius entry and tooth-module row conflict remain unresolved. Certified dimensional evidence is required before fabrication. Fit-window variability is not treated as independent-specimen standard deviation. The measured steel planetary range remains separate from the plotted theoretical ratio. Measured damping is a required analysis with measured parents, while finite versus periodic shear, FEA friction studies and illustrative applications keep their distinct meanings.

## Findings and remediation

1. **High: operation order and replay.** The verifier accepted analysis before acquisition, phase setting after loading and mount inspection after acquisition. It also accepted an additional impact execution event with a unique occurrence ID while the declared impact count remained one. Required-operation presence plus selected pairwise order checks were insufficient.
2. **High: lineage.** An event could use another attempt ID. A whole-paper campaign could assign the same specimen ID to incompatible macro-metal and micro-polymer families. Missing attempt IDs were accepted.
3. **Medium: type and evidence validation.** Accepted mutations included Boolean impact count, string-valued raw immutability, missing raw/calibration references, Boolean qualification/certificate identifiers, incorrect evidence type on a nongeometry gate, duplicate fitted cycle IDs and reused receipt identity.

All five impact guard fields correctly rejected false, missing and string-valued variants. Existing first-cycle, nonfinite phase/window, geometry-evidence, material and specimen-family checks also rejected their tested malformed cases. Guard booleans nevertheless remain toy record checks, not authenticated hardware interlocks.

The first run accepted 16 invalid records among 34 targeted probes. A second review identified three additional causal/lifetime gaps: impact loading could appear after release, gear insertion could appear after frame closure, and selected-scope campaigns could reuse a terminal impact specimen. The author added strict identifier/type checks, complete gate-evidence types, same-attempt and unique-receipt binding, declared handling-recipe ordering, causal acquisition/analysis dependencies, duplicate-execution checks, cross-family specimen consistency and campaign-wide impact single-use. These changes were inspected and all affected cases were independently rerun.

The final targeted suite contains 40 probes and rejects every invalid mutation. Its impact guard checks cover false, missing and string-valued alternatives independently for all five toy guard fields. The generated structural suite accepts all 18 baseline branch records, then rejects all 615 single-event deletions and all 563 adjacent handling-step swaps. These tests establish the tested canonical-record properties, not unrestricted alternate-route correctness or formal proof.

The executable reproductions and initial results are retained in `probe_adversarial.py` and `adversarial_initial_results.json`. Only synthetic bookkeeping records are generated; no physical force traces or physics model is simulated.

## Final verification

All commands ran locally in the package directory, with no hardware or network execution:

- `python -B -m unittest discover -s tests -v`: 65 tests passed; zero failures or skips
- `python -B independent_review/check_static.py`: 85 passed, zero failed
- `python -B independent_review/probe_adversarial.py`: 40 invalid mutations rejected, zero unexpected acceptances
- `python -B independent_review/probe_structural_mutations.py`: 18 positive baselines accepted; 1,178 invalid deletions/order swaps rejected

The accompanying `audit.json` records final contract/test hashes, review counts, resolved findings and limitations. Final release metadata and allowlist hashes must be refreshed by the package author after incorporating this review.

## Actor and execution boundary

The actor contract excludes reference outcomes, evaluator material, tests and this independent review. It also states that no projection loader or runtime sandbox exists. Therefore this review verifies a coherent declared boundary, not an implemented confidentiality guarantee. A future actor must receive an allowlisted projection, never the whole author package. A future trusted logger must authenticate evidence and establish fresh hardware state; local JSON acceptance cannot establish that a physical action occurred.

The appropriate eventual claim is a source-grounded, gated task design with scoped static and synthetic verification. No physical feasibility, robot execution, scientific replication, numerical reproduction, publication or source-media export was performed by this review.
