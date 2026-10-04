# Cantilever-free AFM: inert metrology task design

## Purpose and completion claim

This original ScienceGym specification translates the physical measurement program in Cao et al., Nature Communications (2021), DOI [10.1038/s41467-020-20612-3](https://doi.org/10.1038/s41467-020-20612-3), into eight bounded, robot-facing task branches. The tasks concern inert silicon references and polymer/sapphire probe arrays. Every branch starts from qualified prefabricated inputs and a configured instrument.

Completion means a syntactically and semantically consistent **synthetic contract example**, or a reviewed **static task design**, depending on the reported check. It never means a historical experiment, real robot run, validated simulator, numerical reconstruction, complete fabrication recipe or scientific replication. The local schema is afm_metrology_task.v1; no universal compatibility claim is made.

## Physical branches

1. ARRAY_CAL: mount the array and flat silicon reference, level with force feedback, record released baseline, and collect contact calibration records
2. ARROW_RASTER: measure the registered arrow region on the inert topography target using intermittent-contact raster sampling
3. ARROW_LINE: collect a separate high-resolution line on the arrow target with the source-reported 100 nm lateral step
4. COMPLEX_RASTER: measure a distinct lines/pits/mesas region of the same target family
5. LEVER_CAL: acquire conventional-AFM thermal response and rigid-glass sensitivity records
6. CYLINDER_MECHANICS: localize cylindrical coupons and acquire centered force-distance records by actual radius allocation
7. SINGLE_OPTICS: acquire synchronized cylinder deformation and SI-specific optical-response records
8. OFF_CENTER: acquire off-center normal-loading optical profiles as a torque proxy

Parallel imaging and conventional-AFM coupon characterization use different qualified setups. The former reports a 10x Mitutoyo objective with NA 0.28; the latter reports a 10x Olympus objective and Nikon inverted microscope. A calibration cannot cross these setups or intensity definitions.

## Custody and calibration lifecycle

A retained probe and an exchanged target are different objects. At the parallel station, the conical array remains installed while flat reference and measurement targets are exchanged. At the coupon station, the conventional AFM lever remains installed while glass reference and cylindrical coupons are exchanged. Each has its own identity, carrier and mount version.

Calibration-branch tails retrieve and clean/store only the exchanged reference. They preserve the installed probe and its optical registration for dependent branches inside the same episode. After the final selected branch at each setup, a separate session teardown verifies release, retrieves and inspects the retained probe, invalidates the active calibration, archives custody and completes cleanup/storage. An archived calibration supports interpretation of its existing records; it is not an active calibration for a later episode.

The source gives no robot grasps, clamps, docking coordinates, sensor API or collision model. All such interfaces are authored requirements. There is no real-actuation adapter. Contact acquisition is a closed, qualified metrology service. The robot-facing design handles retained carriers, verifies identity and interlocks, requests named qualified jobs, reads records and closes custody.

## The central contact invariant

For every raster/line coordinate and every repositioned loading condition, lateral movement requires a current released-state observation. Acquisition requires confirmed stationary contact. Withdrawal is only a command acknowledgment; the next lateral move or handoff requires a separate force-release observation. Missing, stale, contradictory or unknown state causes a hold.

No numerical force limit, approach velocity, leveling tolerance, release threshold or dwell is inferred. These are unresolved qualified-input cards. The source's one-second imaging frame does not establish an exact contact dwell or a safe robot-control program.

## Preparation boundary

Two preparation routes describe the scientific roles of conical imaging arrays and cylindrical characterization coupons. The paper reports PDMS coating/cure, direct laser writing and reflective aluminum deposition. However, complete geometry/CAD, writing power/speed, development, detailed process setup and acceptance are missing. The qualified closed-service boundary is an authored integration abstraction, not a service interface provided by the authors.

A prefabricated qualified input can satisfy the bounded metrology route precondition. It cannot be used as evidence that fabrication was performed, that the entire historical route is complete, or that its missing recipe has been recovered. Preparation routes remain gated.

## Measurement and analysis boundaries

The source reports a 15 by 15 micrometer raster field, 1 micrometer raster spacing, 15 micrometer hexagonal pitch and 1088 probes. Exact endpoint convention, coordinate ordering, per-frame dwell, line extent and repeat allocation require qualification. The synthetic tests intentionally use short named schedules; they do not simulate or claim a complete source scan.

Raw AVI/force records, acquisition coordinates, accepted and failed attempts, target region, probe identities, setup/mount versions, calibration and processing parameters must remain linked. Reconstruction has separate contracts for center detection, intensity averaging, height conversion, stitching, height-offset correction, frame-offset removal and crosstalk correction. Source data and external MATLAB code were not acquired or executed. No reconstructed image is provided.

The four-probe repeatability analysis is not four independent specimen repetitions. Off-center indentation demonstrates an optical torque response; it does not establish a directly measured two-dimensional gradient map. COMSOL deformation/crosstalk, model precision, soft-substrate predictions, larger arrays and projected MHz bandwidth are numerical or prospective scope.

## Conflicts kept visible

- Main Results describe about 0.5 mm and a line span greater than 0.4 mm; Discussion states 5 mm. No historical geometry is silently corrected
- Model precision about 1 nm, single-probe optical estimate 6 nm and image precision 9 nm are distinct
- Empirical crosstalk correction 35% is separate from simulated 29%
- Main and SI optical metrics have different baseline handling and sign
- SI repeatability explicitly uses the arrow dataset, while the main paragraph follows its intricate-image discussion
- SI and main text describe different model-based soft-sample applicability thresholds
- Pixel inspection confirms SI Equation 15 prints k_eff minus k_c in the denominator. Under positive-stiffness series-spring assumptions this produces an inconsistent sign; interpretation remains gated instead of silently repaired

## Evaluation and recovery

Only agent_visible.json belongs in an actor context. Outcome values and fixture expectations are author/evaluator information. The mock contract checks exact phase/point order, dependency closure, qualified input presence, identity/version binding, distinct custody roles, state guards, raw-record binding, archive and cleanup, and final calibration invalidation.

Its environment records are authored synthetic fixtures. They are not authenticated device observations and can be forged by someone with evaluator access. Production authority is explicitly unsupported. Static/hash checks also do not supply production trust.

On failure, preserve the failed record and attempt, stop dependents, retain or quarantine the carrier, and require fresh qualification before a new attempt. The contract tests intentionally reject failed or damaged records as completion; they do not implement real recovery motion or automatic retry.

## Source and release coverage

The complete retained publisher-deposited main text, Methods, captions and fourteen written SI pages were read. Upstream audit visually inspected all SI pages; the conversion author additionally inspected SI page 8 for the equation conflict. Main figure pixels were not verified. The exported package contains original English prose, JSON, Python checks and review receipts only, without source pixels, source full text or source PDFs.
