# Independent review: graphene quantum Hall array operations v2

Decision: ACCEPTED_ORIGINAL_STATIC_TASK_DESIGN_ONLY

This review accepts one original, non-executable whole-paper design and its finite metadata tests. It accepts zero validated runnable whole-paper tasks. Physical execution, hardware operations, scientific reproduction, electrical/physical simulation, production receipt authentication and scientific analysis remain unimplemented. All actual qualification remains held.

## Evidence reviewed

The reviewer compared the task package directly with the accepted source-review packet, independently read the new design and contract files, examined the finite validator, wrote new adversarial and export tests, and ran both independent and primary suites. This review consumes the accepted source annotations; it does not claim a second acquisition or complete reread of the publisher article, access to raw scientific data, or numerical verification of published results.

All 17 retained JSON annotation files match the accepted packet byte for byte. They preserve 29 facts, 18 ambiguities, 14 outcome records, 20 unresolved input groups, all 15 R00–R14 route steps, eight stations and eleven scene groups. Main-table coverage remains nine rows. The shared scene contract matches the separately supplied contract exactly: SHA-256 d86dc8699ca1bf8fe2c552d318e5e5eac8a6b613a27ed87d4cab56b2f8d7b86d. All 15 operation bindings and all 32 distinct evidence-only anchors agree.

## Scientific and service design

- Array1 and Array2 remain regions of one chip, each containing 118 parallel Hall elements with nominal R_K/236, about 109 ohm. Their whole series object contains 236 elements with nominal R_K/118, about 219 ohm. The on-chip Hall bar is not another manufactured specimen
- The 100-ohm oil-bath and 12.9-kiloohm air-bath references retain separate identities and per-device current/power evidence
- The comparison graph retains five direct edge types, four nodes, three simple loops and two independent graph cycles. No direct HB–Array2 source edge is invented. Derived paths do not become independent acquisitions
- Source CCC readings remain within-run evidence, not independent chip, lot, cooldown, remount or laboratory repetitions. Prospective counts and conditions remain null
- Preparation release, carrier/custody, calibration lifetime and revisions, physical resource leases, immutable measurement lineage, controls, failures and independent closeout are explicit
- R09 preserves intentional nonquantizing-control semantics. R10 and R11 retain optional acquisition while remaining part of the whole-paper design. Short screening SD is separated from long-record Allan uncertainty
- Printed Allan input/error-equation ambiguities and the printed loop-expansion defect remain explicit holds. No equation has been silently repaired and no numerical Allan or loop implementation is supplied
- R14 is reachable from the started R03 session, independently of analysis success. Started jobs, individual safety channels, accepted support/custody/storage, lease acknowledgement and distinct partial/failed/held/unattempted branches remain required
- Source outcomes are not observations, runtime defaults, safety limits, rewards or pass targets. The actor view contains only operation/evidence identifiers and requirements

## Adversarial findings closed

1. Calibration initially failed to bind method, mount and terminal-map revisions. The validator now rejects missing or mismatched values
2. R04 initially accepted unrelated arbitrary comparison devices. It now has a distinct characterization-path and same-chip identity schema
3. Measurements initially accepted unbound lease identifiers. They now require a matching synthetic lease receipt, physical resources, job, custodian, chip and mount
4. One untyped observation identifier initially satisfied every safety channel. Distinct channel observation identifiers are now required
5. Export validation initially omitted the manifest's own bytes from secret/binary inspection. The manifest is now inspected before parsing and its schema identifier is exact
6. R03 initially accepted a lease for an unrelated chip or receiving custodian. Chip, custodian and explicit mount are now bound to custody evidence
7. R13 initially accepted invalid branch labels and conflated the declared source-edge inventory with acquired-edge inventory. Validated edge/branch labels and separate acquired-edge coverage now preserve held and partial states

8. A final packaging pass found literal dummy attack markers in the primary export-test source. Splitting those literals preserves the runtime attack tests while ensuring the exported test code contains no secret-shaped marker; both regression suites and the 51-member directory export passed again

Independent regression tests reproduce the relevant bad cases and now reject them. Positive baselines are retained to distinguish correct rejection from rejection of an unrelated malformed fixture.

## Verification

- Independent suites: 44 test methods passed, zero failures, zero errors and zero skips
  - 16 static source/design/binding tests
  - 16 finite-validator and adversarial tests
  - 12 export and archive-attack tests
- Primary suites: 32 test methods passed
- Submitted static package validator: 223 checks passed
- No test issues a hardware command, supplies measured scientific values, implements the disputed equations, connects to an instrument or simulates scientific physics

Run the independent tests from the package with:

    PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s review -p 'test_independent_*.py' -v

The refreshed task semantic core is cb8d06d71946eeacfdb9e5284c52eeff17d937fcdc7f37ed7a1f8311ba14a9f0. Its entry hashes and aggregate hash were independently recomputed. The exact substantive snapshot hashes are recorded in INDEPENDENT_REVIEW.json. Review files and administrative release metadata are outside that snapshot so the review and export can be sealed without recursive hashing.

## Acceptance limits and release gates

The finite validator checks selected synthetic metadata invariants, not a complete future service implementation. Synthetic provider/receipt trust is evaluator-owned fixture trust, not cryptographic authentication. R04 calibration/terminal references have schema-presence checks only; external calibration and lease qualification are not cross-validated there. Persistent atomic lease management, actual state sensing, complete external receipt resolution and real scientific validity are not implemented. Successful fixture review never clears actual qualification.

This review checks the shared scene contract and operation bindings, not scene geometry, visual appearance, load-bearing capacity, collision safety or physical kinematics. Separate asset review and exact final archive pairing remain required. A schematic scene is not a qualified robot workspace.

A 51-member finalized directory passed exact allowlist and byte-hygiene inspection. This report refresh requires one final allowlist regeneration. The final archive is assembled after this review. Validate exact final archive membership and hashes, absence of publisher originals and forbidden bytes, final scene/task pairing and detached receipt before delivery. Administrative status, manifest, release-pairing and delivery-receipt additions may follow; any substantive change to the hashed design, contract, binding or test code requires renewed review.
