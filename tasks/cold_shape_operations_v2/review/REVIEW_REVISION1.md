# Independent review addendum: revision 1

Retested 2026-10-03 16:58–17:01 UTC. This addendum preserves rather than replaces the initial review.

## Verified repairs

- B1_FIXITY_SERIES explicitly reserves homogeneous B1 fixity coupons, does not inherit hinge-angle n=5 and keeps the missing strain schedule gated
- Known SI Note 1 specimen timing context is retained; the unspecified cold recovery hold remains null, and unrelated demonstrations do not inherit the specimen schedule
- Current inventory is 76 operations, 32 physical branch contracts, 6 numerical dispositions, 19 gates, 24 routes and 7 loop types
- Independent static consistency harness: 83 passed / 0 failed
- Author verifier and all 73 author unit tests: passed
- All 9 original adversarial inputs now reject. Several old inputs reject early due to the revised schema; targeted author tests separately cover their relevant upgraded checks
- Explicit tests now reject cycle receipt replay, program-hash drift, unsafe unload, incomplete/duplicate cards, impossible datetime, replicate deficits and inventory-count drift

## Remaining composition findings

The exact executable probes and JSON results are preserved in `adversarial_composition.py` and `adversarial_composition_results.json`. Five probes were accepted by revision 1:

1. Campaign service events explicitly carrying a wrong station, obsolete version, other condition, wrong material and missing calibration
2. Campaign MOVE occurrence carrying an invented route and connected tethers
3. A campaign containing no raw measurement records at all (the author's own positive campaign fixture)
4. Reversed operation-receipt ordering
5. Standalone bound service whose expected material is B1 but whose object context explicitly says B2

The first three expose noncomposition: the campaign checker calls `validate_service_trace`, but not the stronger `validate_service_binding`, `validate_transfer` or `validate_record` helpers. Individual helper unit tests are not evidence that campaign validation enforces those checks. Case 4 can remain a declared limitation if operation receipt membership is intentionally unordered and no execution-sequence claim is made.

The package still correctly refuses live evidence and returns `physical_execution_validated: false`. These are synthetic contract-check limitations, not physical or robot execution findings. A scoped alternative to implementing a runtime is to identify this function as a coverage-schema probe and explicitly declare these unvalidated dimensions; do not call it an end-to-end scientific validator.

## Remaining multistage representation issue

`condition_requirements.json` represents material/layout/axis comparisons but does not explicitly require both temperature states for THERMAL_HINGES or MICRO_PIPE; their generic phase lists do not provide the missing requirement. MEMORY_VISUAL and HYBRID_STRIPS also need explicit thermal-stage records if not enforced within qualified subphase schedules. The source branch context already preserves the reported temperatures, so this is a coverage-enforcement/representation issue, not a missing source fact.

The author has received exact findings and may fix them or explicitly narrow the verifier's claims. Final independent disposition remains pending this clarification/revision.
