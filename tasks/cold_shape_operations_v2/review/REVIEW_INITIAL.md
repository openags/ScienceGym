# Independent review: cold-shape operation contracts

Review time: 2026-10-03 16:47–16:53 UTC
Package: `cold_shape_operations_v2` (actively authored; initial review snapshot)
Review artifacts are original analysis and synthetic code only, outside the package. No publisher figures/text, new physical recipe, actual simulation, or device commands were created.

## Initial verdict

**Changes requested before claiming independent verification.** The source mapping and execution limits are strong, but two source-coverage details and several synthetic-verifier false acceptances need correction. Live evidence is refused by design; no accepted synthetic probe represents physical validation or a device-access vulnerability.

The initial authored inventory is internally consistent: 76 shared operation definitions, 31 physical branch contracts, 6 numerical/analytical dispositions, 19 unresolved gates, 18 transport routes and 7 loop types. These are authored design subdivisions, not independent experiments or executed trials.

## Evidence reviewed

- Source packet README, coverage map, reading log and relevant source-manifest/provenance fields
- Main text covering all experiment families, Methods, numerical boundary, discussion, data availability and source conflicts
- SI characterization methods, captions and parameter-identification passages; direct visual inspection of main Fig. 2 and SI pages 5, 6 and 14 to verify geometric labels, alternative-resin ambiguity, repeat scope and measured/simulated curves
- All package JSON files, branch conditions, operation interfaces/actions, closure/lineage/state contracts and initial verifier/tests

The review does not independently claim all ancillary movies, source XLSX, author implementation code or every source pixel were read. Source-packet full-read claims are attributed to that audit.

## Strengths verified

- Physical tests are separated from fitting, FEA and analytical derivations. Numerical dispositions are explicitly unexecuted and cannot count as measured raw evidence
- Every source physical family P00–P18 has an explicit mapping, including micro-pipe and alternative-resin work
- Geometry, fixtures, sample allocations, measurement settings and qualified safety programs remain unresolved rather than receiving convenient defaults
- Robot roles cover supported custody, loading interfaces, registration, safe unloading and record preservation. Chemical processing, UV, active loading/heating and liquid-metal filling remain closed-service responsibilities
- Main B1 onset discrepancy, lattice label error, SI hot-tensile printed units and alternative-resin identity ambiguity are preserved
- No automatic post-cure is inserted; the organogel's UV sensitivity is retained
- Five-result hinge-angle error bars, ten material cycles and forty hinge cycles are not represented as interchangeable independent sample counts
- Printed hand is correctly treated as a polymer demonstrator. LED observations remain qualitative; flow and antenna suggestions are not promoted to quantitative demonstrated experiments
- Actor-visible allowlist is separated from hidden outcomes/reference routes; loader and live runtime are explicitly unimplemented

## Source coverage findings

### S1. Homogeneous B1 fixity series needs an explicit physical allocation

Main Fig. 2C and its accompanying text include measured B1 shape fixity as a function of imposed strain, used to fit the relation feeding the hinge theory. The initial HINGE_ANGLE_FORCE branch names only hinge families and does not explicitly allocate homogeneous B1 coupons or bind their fixed-strain records. A hinge-only campaign could therefore appear complete without the measured B1 subseries. Add an explicit subseries or branch and preserve its separation from fitted/theoretical values. Do not generalize the hinge-angle error-bar replication statement.

### S2. Preserve source-known specimen rate/hold context

The initial MEMORY_HOT/COLD conditions preserve reported strain and temperatures but omit the rates/holds already present in SI Note 1. Retain those facts as source-scoped scientific context, still requiring qualified device cards. This does not authorize transferring the specimen schedule to ten-cycle tests or geometric demonstrations.

## Executed checks

- Independent static cross-reference harness: 81 passed, 0 failed
- Author verifier: passed with initial inventory above
- Author unit tests: 45 passed
- Independent adversarial probes: 9 unexpected acceptances (see JSON artifact and exact executable harness)

## Synthetic verifier findings

1. **Whole-paper coverage/lineage (high):** all physical branches with one arbitrary string condition and summary booleans pass without actual phase, material/layout/temperature cell, control, ancestor, raw-record or specimen evidence
2. **Replication enforcement (high):** a declared seven-replicate condition passes with one summary and no sample IDs
3. **Cycle receipt replay (high):** forty cycle indices pass while reusing the same four receipt strings for all cycles
4. **Program substitution (high):** completed service event may carry a different program hash from verified event
5. **Unsafe unload contradiction (high):** an earlier safe-release event suffices despite explicit unsafe state on the unloaded event
6. **Gate-card content (medium):** status/revision/receipt text substitutes for the required geometry, scene, schedule, calibration and qualified-scope fields
7. **Timestamp validation (low):** impossible date/time passes a shape-only regex
8. **Card inventory (medium):** duplicating one gate card hides a missing different gate while count remains correct
9. **Route inventory (low):** removing a route leaves declared count inconsistent yet package validation passes

These severities describe the declared synthetic validation contract, not live execution. There is no authenticated backend, physical scene, controller or scientific replication.

## Integration notes

The author was notified directly of every finding and is revising the package. Source counts are provisional and must be refreshed if the B1 fixity family becomes a new branch. The initial hashes in `initial_static_results.json` and adversarial contract hash identify the reviewed baseline. Retest revised code and preserve this original report as a record of what was actually tested.

Additional integration caution: service-precondition strings alone do not bind specimen location/state, scoped calibration, selected hinge/axis, condition, or attempt. The verifier must bind those identities. Electrical transport must require isolation and disconnection; per-configuration LED snapshots cannot establish uninterrupted conductivity while deforming.
