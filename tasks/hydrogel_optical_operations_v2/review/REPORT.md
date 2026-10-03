# Independent review: hydrogel optical task design

## Verdict

Approved for the gated, source-grounded design scope. The final payload must still pass the exact-package export check after its manifest is regenerated. This verdict does not establish execution readiness, complete visual source coverage, robot feasibility, instrument safety, physical simulation or scientific replication.

Reviewed scope: 36 physical branch definitions, 107 operation definitions and 53 source-coverage records for Nature Materials DOI [10.1038/s41563-023-01649-3](https://doi.org/10.1038/s41563-023-01649-3). The full supplied source audit and the contributing paper-task, asset and review guides were read. Review compared the authored contracts against that audit; publisher media were not independently reopened or reinspected.

## Independent checks

- 211 static and source-scope checks passed
- 43 adversarial record probes passed: one valid baseline and 42 required rejections
- 158 required-field and structural mutations were rejected
- 17 export-logic probes passed: one valid original-sentinel baseline and 16 required rejections
- The author's static package verifier passed
- The author's 17 unittest methods were independently run before final manifest regeneration: 16 passed; only the exact-package baseline failed because author changes and new review files had not yet been rehashed. Export-logic mutation tests passed

Reproducible independent entry points are static_review.py, adversarial_review.py, structural_probe.py and export_probe.py in this directory. They write their own named receipts here. Re-running a receipt-generating review after export freeze changes that receipt and therefore requires a new manifest hash. Final frozen verification should run the read-only author checks.

## Findings resolved during review

1. Standalone hydrogel coupons could bypass curing. A distinct closed GEL_CURE service and prerequisite now precede coupon cutting
2. Required allocation and lineage maps were absent from acceptance. Condition-compatible parent sets, batch/material ancestry, complete lineage, job membership and carrier bindings are now checked
3. SEM and confocal initially shared an unqualified specimen. Separate reserved siblings are now mandatory, with the 3D branch explicitly restricted to its source IP-S material
4. The square-lattice route could claim its compatibility control without the incompatible-spacing branch. That branch is now a prerequisite
5. Removing required fixture, calibration, raw-record, hash, attempt or card fields from both authority and events could pass; stale cards also passed. Exact job/event fields, typed nonempty bindings and current registrations now reject those cases
6. Quarantine and added actor actuation fields could pass. They now reject. Optical release evidence must identify the same specimen, output version and raw record
7. Malformed nested inputs raised exceptions rather than returning rejection. They now fail closed
8. Export scanning ignored unlisted files under cache-named directories and an unlisted directory symlink; malformed manifests could raise exceptions. The export verifier now rejects those cases
9. Required lineage fields could contain empty identities, invalid initial versions, obsolete development cards, Boolean map hashes, malformed thermal histories or nonexistent extra jobs. Allocation provenance could be omitted or relabeled as source-derived, and reserved roles were not enforced. All 15 discovered structural cases now reject
10. Source-specific author refinements were rechecked: the scan-speed branch uses AFM without inventing a thermal scan-speed series, and spectral transmission retains the reported two-material comparison separately from the three-material thermal microscopy controls

The original first adversarial receipt is retained. Later successful receipts identify the exact verifier hashes tested. Author rerun files are labeled as author-generated; they are not substituted for the independent final runs.

## Source fidelity and visibility

The coverage inventory preserves material controls and formulation sweeps, beam characterization, inert resist comparison, lattice compatibility and cycling, geometry and scale extensions, power images, angle optics, combined encoding, and separate numerical/theoretical dispositions. The preparation route retains closed formulation, printing, material-specific development, capillary assembly, cure, cover removal, water chamber and optical release.

Four Extended Data image inspections remain missing. All four captions have explicit gap records. Video coverage remains eight sampled keyframes per clip, not full-motion inspection. Video 9 retains its 20-times acceleration and separate 27,000-unit specimen; neither playback duration nor frames become response-time measurements.

The 20/50 mW Fig. 4l conflict and Fig. 3j column disagreement remain unresolved source gates. Workbook unit/panel conflicts, malformed PVA specification, missing values, fitted-point separation and undefined pre-buckling quantities remain explicit. The 15/50 mW beam contexts, 25/27-cycle histories and 10,000/27,000-unit image specimens remain separate. Reported feature counts are not promoted to independent material batches.

Only agent_visible.json is designated actor-visible. It exposes no source answer targets, future observations or qualified instance defaults. Every processing station retains a closed qualified-service boundary; robot scope is carrier movement, loading, qualified handoff, readout and unloading. Synthetic authority, cards, raw-record identifiers and controls are labeled authored fixtures, not observations from this paper or new experiments.

## Remaining gates and limits

- Missing Extended Data images prohibit complete visual-source claims
- All qualified operating parameters, apparatus cards, geometry, grasps and physical assets remain unresolved or unimplemented
- Production authentication, a trusted physical event logger, measurement-analysis implementation and enforced runtime actor isolation are not implemented
- PLAN, INSPECT, ARCHIVE and CLEAN are represented by synthetic context/completion evidence; these tests do not demonstrate their physical execution
- This review performed no device actuation, numerical solver run, physical simulation, public write or publisher-asset export
- Exact final payload identity must be established by the regenerated allowlist and subsequent read-only export check
