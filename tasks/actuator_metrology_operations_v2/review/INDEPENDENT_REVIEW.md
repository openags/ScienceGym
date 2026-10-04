# Independent review: actuator metrology operations v2

## Decision

The source-grounded contract and offline synthetic verifier pass independent review after two findings were corrected. This is approval only for the bounded prepared-specimen record-verification task. The exact 41-member named export and all seven independent export tests also pass.

Whole-paper completion remains false. This package does not qualify for a full-paper replication target count. No fabrication, DEM, FEM, CNN training, physical actuation, image segmentation, mechanical simulation, or production safety validation was performed in this review.

## Source review

Source: Bonfanti et al., *Automatic design of mechanical metamaterial actuators*, DOI 10.1038/s41467-020-17947-2. The final main scientific text, equations 1–6, captions and seven main figures, four-page written supplement, one-page movie descriptions, and full-duration sampled contact sheets for the three movies were examined. References to outside papers and the peer-review file were not treated as evidence. Author source code was not inspected or executed; source pixels and source prose dumps are absent from the review artifacts.

The implemented boundary matches the source: prepared printed specimens have a fixed bottom holder, nominal 5 mm input imposed with a caliper, paired camera observations, and node-displacement analysis. The source does not supply a robot-ready fixture, camera calibration, uncertainty model, exact specimen CAD, force limits, or a safe unloading and custody procedure. Those remain explicit qualification gaps or authored fixture choices.

The four recorded source discrepancies are justified and remain unresolved:

- Main Results prose reverses the direction assignments of main Figure 2 and Supplementary Figure 3. Caption and arrow evidence identifies Figure 2 as anti-parallel and Supplementary Figure 3 as orthogonal
- Figure-to-movie pointers conflict with movie descriptions and actual title cards: Movie 2 is orthogonal; Movie 3 is anti-parallel
- Physical Methods refers to Supplementary Figure 1 for printed results, while that figure is an optimization trace; the printed orthogonal panels are in Supplementary Figure 3
- Force Results prose points both scans at Figure 5c, while the input-force scan is Figure 5d

A qualified specimen/node/world-frame card can authorize a chosen benchmark direction without purporting to resolve the publication. The default no-card route remains a direction hold. Figure 1's screen arrow is not adopted as a universal world coordinate.

Whole-paper design accounting preserves separate regular and jammed-disordered searches; default and size-scaling Monte Carlo schedules; six scaling sizes and independent runs; angular spring re-neighboring; FEM validation before printing; fabrication qualification; nonlinear amplitude comparisons; force-pliers evaluation versus visualization conditions; run-level CNN split and train-only resampling; CNN-generated structures requiring independent DEM evaluation; and separate add/remove, same-lattice and cross-lattice heatmap analyses. All those numerical and fabrication routes remain unimplemented design contracts. Prepared specimen intake never completes them.

## Corrected findings

### R1: actor projection was insufficiently explicit

Source efficiencies occur in evidence_map.json as well as source_outcomes.json. A file-level evaluator reference list initially omitted evidence_map.json. The author corrected this by defining the exact actor-visible allowlist as only agent_visible.json in evaluator_reference.json and EXPORT_ALLOWLIST.json, with every other member evaluator/audit-only. The public package remains an auditable developer artifact, not a secret actor benchmark.

### R2: fixture-instance IDs did not distinguish configurations

Initially, two fixtures with the same episode ID but different direction branches produced identical actor IDs and evidence IDs. The corresponding event trace could therefore be accepted against the alternate fixture. This did not let the actor submit a measured value, but it made the replay namespace ambiguous.

The author introduced fixture_instance_id derived from episode, branch, scenario and variant, namespaced actor/event/specimen/frame/calibration/receipt identities by that immutable instance, and added the instance to observation bindings. Independent regressions now reject cross-branch, cross-scenario and cross-variant trace replay even when the outer episode ID is reused.

## Independent adversarial verification

review/test_independent_adversarial.py contains 26 passing test methods, including 48 physical-branch synthetic configuration checks plus the default hold. It tests:

- Strict actor IDs only, extra-result and qualification injection rejection
- Every missing operation, adjacent reordering, duplicate events, receipt reuse, cross-episode and cross-configuration replay
- Specimen, attempt, topology, material lot, mount, camera, calibration, node-map and direction-card lineage; before/after freshness and content hashes
- Node identity and cardinality, malformed or non-finite values, calibrated planar mapping and pixel-y inversion
- Both matched human-design and machine-design specimen lifecycles under matching benchmark conditions
- Command acknowledgements separately from independent base, input and unloaded observations
- Signed n=2 mean-output projection divided by mean-input projection; off-axis motion is not norm gain, wrong-way output stays negative, and non-positive input denominators fail
- Rehashed false state claims, source-outcome substitution, stale calibration and unqualified cards
- Failed short input, base slip and occluded-image cases retaining no efficiency result and ending in observed quarantine/cleanup
- Post-measurement damage retaining historical measurement but prohibiting reuse
- Supported unloading, base release, retrieval, inspection, raw/failed-attempt archive, and observed cleanup
- Scope flags remaining false for physical validation, numerical execution and whole-paper completion

review/test_independent_export.py adds seven exact-export and actor-separation tests covering member inventory, SHA-256 and byte counts, unlisted/missing files, modified bytes, symlinks, ZIP extras/duplicates/traversal, and malformed allowlist records. All seven tests pass against the 41-member named freeze; the public ZIP was also checked for exact member names and identical bytes.

## Residual limits

The verifier intentionally compares the entire independently supplied bundle with a deterministic public fixture. It is a closed-world regression artifact, not a general instrument-data validator. Recomputed hashes cannot authorize an altered fixture; conversely, hashes and public fixture code provide no external authentication or secrecy.

Replay rejection applies within a trace and across bound fixture instances. Revalidating the identical immutable offline fixture is deterministic and accepted; there is no persistent production replay registry. The n=2 choice and numerical tolerances are authored benchmark choices. The printed source's generalized-efficiency exponent is not established. Qualification-hold metadata does not imply an implemented real recovery controller. Rendering and interface cards do not supply calibrated mechanics or physical authority.

## Reproduction

From the package root:

- PYTHONDONTWRITEBYTECODE=1 python review/test_independent_adversarial.py
- PYTHONDONTWRITEBYTECODE=1 python review/test_independent_export.py
- PYTHONDONTWRITEBYTECODE=1 python tests/verify_package.py
- PYTHONDONTWRITEBYTECODE=1 python tests/verify_export.py PATH_TO_RELEASE_ZIP

The review writes only its four explicitly named files under review/. Author implementation changes were made by the author in response to findings. Export must include only the exact final manifest members, excluding source media, datasets, author code, caches, symlinks and private absolute paths.
