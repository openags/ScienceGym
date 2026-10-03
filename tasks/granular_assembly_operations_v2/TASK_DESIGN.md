# Anti-repellent granular assembly: whole-paper mobile-robot task family

## Status and scientific boundary

This independently authored ScienceGym design represents the physical experimental program of Bae et al., *Self-assembly by anti-repellent structures for programming particles with momentum*, Nature Communications 15, 10794 (2024), [DOI 10.1038/s41467-024-54976-7](https://doi.org/10.1038/s41467-024-54976-7). It is a task-design draft, not a performed experiment, executable robot controller, scientific simulator or verified physical reconstruction.

The actor is a human-like mobile laboratory robot. It prepares materials and samples, picks up and carries supported objects, assembles fixtures, operates device interfaces, observes actual readbacks, unloads specimens, returns to measurements and cleans up. An instrument performs only its specified autonomous process. A roller turning, a UV chamber finishing or a microscope saving an image does not imply that the robot loaded, moved or recovered a specimen.

The source article is readable through its official web page; the 43-page SI and one-page movie descriptions were inspected. Key SI figures were visually checked. Five movies and the linked historical dataset remain unread. Their requiredness is assessed individually in `source_access_audit.json`; unread historical assets are not a blanket stop for a fresh, properly qualified acquisition task.

## What the experimental family covers

The configurations cover all reported practical themes, split into eight readable groups:

1. Surface controls: elastic flat NOA73, partially cured sticky film and patterned sticky traps
2. Fabrication and material/interface characterization: PDMS-blanket sandwich preparation, patterned traps, flat mechanical films, photo-DSC, indentation, pull-off, UV-dose/contact-area comparison and destructive interface microscopy
3. Dry assembly: a QR-patterned shaking demonstration, quantitative roller conditions, resin-transfer SEM/EDS and qualified reuse cycles
4. Collisions: free-fall capture/rebound on two cure states and collisions against already trapped beads before or after shape adaptation
5. Geometry: diameter/height effects, asymmetry, spacing-dependent packing/contact numbers, polydispersity and contact-location distributions
6. Authentication-related acquisition: same-key imaging across observation frames, shared-granule membership and provenance-linked feature/comparison analysis
7. Coating and stability: protective PDMS preparation/application, registered baseline imaging, separate contamination, drop, sonication and seven-day environmental branches, followed by matched reimaging
8. Extensions: two reported size endpoints, mixed glass/YSZ particles and custom hard/soft PUA particles, including the fluorescent soft-PUA condition

`branches.json` lists selected goals, conditions, controls and gates. `source_parameters.json` separates reported settings, count labels, figure-read points and outcomes. `coverage_matrix.json` covers main Figs. 1–7, SI Notes 1–8, Figs. S1–S28 and Tables 1–3, including explicit computational and literature-only scope. It does not claim a complete historical specimen allocation or a full factorial combination of every material, size and shape.

## A complete physical robot episode

For an assigned fresh trap-array episode, the robot first reads the finite work order, identifies actual stocks and qualifies the installed stations. It moves closed material vessels and slide components to a supported preparation area. After the missing preparation recipes have been supplied, it prepares the PDMS blanket, places a slide and spacer, dispenses NOA73, closes the prescribed sandwich and checks its label, orientation and gap. These are robot manipulation obligations, not unexplained prepared-sample inputs.

The robot carries the supported sandwich to the UV-patterning station, docks it, selects the versioned mask and qualified exposure, closes the guard and requests the job. The optical device performs illumination. The robot checks the actual receipt, retrieves the assembly, carries it to the contained rinse station, opens it with the qualified tool, develops the pattern with ethanol and collects the resin/solvent waste. It then transports the specimen to microscopy and verifies the actual traps against the assigned geometry.

At preparation, the robot tares and weighs the selected bead charge. At assembly, it loads the actual slide and particles into the identified tube, secures the qualified retention fixture, closes the tube and docks it on the assigned roller or holds it with the qualified shaking interface. The short shaking demonstration and the quantitative roller campaign are different routes. Actual motion, time and specimen identity are recorded; source plot values never become observations.

After motion stops, the robot undocks and opens the tube over a capture tray, recovers the slide and separates loose particles. At the contained clearing station it applies only the resolved removal method. If the selected condition requires shape adaptation, it transports the assembled array to flood UV, starts the qualified program and retrieves the sample after safe release. It carries the array back to microscopy, reidentifies its trap and particle sites, acquires actual images and submits those raw records to the declared analysis service. It finally returns, quarantines or disposes of every physical descendant and reconciles all records and waste.

Every station change instantiates the MOVE contract: source support, object identity, tool/carrier, release, supported transit, destination docking and observed placement. The particular gait, grasp, pose, force and room geometry must come from qualified assets. None is inferred from a paper photograph.

## Preparation and branch-specific physical responsibilities

- Flat-film tests require the robot to prepare actual labeled films using resolved substrate, dispensing and film-forming methods. It mounts them separately for indentation and pull-off; a plotted comparison is not evidence that one site can serve both assays
- Photo-DSC requires robot aliquoting, pan/reference preparation, device loading, acquisition and safe unloading. Its reported illumination condition is not automatically the trap-patterning calibration
- Collision tests include gated robot fabrication of the 3D-printed guide: loading qualified stock and a verified job, requesting the print, recovering and inspecting the part, and mounting it. They require separate target and impactor identities, distinct prechallenge imaging of retained beads, calibrated high-speed capture and impactor recovery. The Stage1 trapped-bead arm forbids prior postcure; the adapted arm requires postcure before impact. These are distinct machine-readable arm graphs
- Destructive interface and resin-transfer analysis requires robot bead removal, separately labeled trap remnants and removed beads, qualified SEM/EDS preparation, mounting and unloading. The original array becomes disassembled and cannot silently return as an intact authentication key
- Reuse requires qualified robot removal/reset and recorded trap damage at every cycle. The paper's reuse statement does not supply a stripping recipe, universal cure state or permission to reset observations
- Protective coating requires the robot to prepare and apply the specified PDMS batch, load any required cure equipment and establish optical readiness. The paper does not provide that recipe; its absence is a local preparation gate
- Stability challenges require robot preparation/loading of the selected contained fixture, baseline-to-post-test site registration, actual device exposure and retrieval. Powder exposure is contained; glass-substrate drops are enclosed. Four separate challenges are not invented as one cumulative sequence
- Custom PUA variants require robot preparation of the specified component/dye batch and operation of recipe-defined fabrication tooling. The fabrication method, exact shapes and Rhodamine B quantity must be supplied. A received finished-particle batch cannot count as robot-performed manufacturing

All these robot translations are authored task requirements. They do not claim that the source authors used a robot or that any proposed manipulation has been physically validated.

## Real duration and long-horizon dependencies

Most assembly operations are short. The source describes a ten-second shaking demonstration and seconds-scale roller observations. This design adds no artificial waiting days or unrelated chores to inflate horizon. Its ordinary horizon comes from consequential preparation, state changes, transport, device interfaces, controls and measurement lineage.

The environmental-stability branch genuinely specifies seven days at 70 °C and 50% relative humidity. That is a device dwell with persistent specimen custody, environmental logs and later robot retrieval. It is not seven days of continuous robot movement, nor can a short simulated receipt satisfy it. Ramp, excursion and return-to-imaging details remain qualified inputs.

## Known values versus unresolved inputs

Scientific settings are centralized with source locators in `source_parameters.json`. Relevant source examples include the standard 12 µm sandwich spacer; distinct 100 µm mechanical films; a 10 µm flat indenter; 50 mL assembly tubes; 5/10 g roller charges; figure-labeled 10/15/20 RPM; and the geometry and observation-frame comparisons. None supplies missing dimensions, recipes, handling pressures or measurement acceptance limits.

Thirty-one explicit input gates cover sample allocation, installed assets, bead lots, sandwich/blanket preparation, masks, UV calibration, solvent development, air removal, films, DSC, mechanics, dose interpretation, collision fixtures/cameras, motion sampling, imaging/registration, destructive preparation, reuse reset, PUF processing, PDMS coating, stability fixtures, size-specific designs, mixture composition custom PUA preparation and collision-guide fabrication. A gate blocks the dependent operation or selected condition; it does not erase completed work or invalidate unrelated branches.

An authored resolved value retains its provider, units, applicability and qualification receipt. It cannot become a historical source fact. Empty masks, missing geometry, null amounts and absent raw files never count as valid zero-valued inputs.

## Source discrepancies that must remain visible

The source gives nominal 1 mm glass beads but also a mean diameter of 489 ± 46 µm in the SI, alongside an approximately 500 µm radius-like vector scale. This design does not silently reinterpret the smaller number as a radius. Actual lots and measured distributions remain separate.

Other retained issues include the YSZ surface-energy mismatch between Note 8 and Table 2, the missing area denominator in the Fig. S6 caption versus its legend, Note 7's stability figure cross-reference, a symmetry-panel cross-reference, rotation-sensitivity wording and incomplete branch-specific cure histories. The two-minute mechanical-film postcure is not a universal array recipe. Details are in `source_conflicts.json`.

## Controls, repetitions and image identity

Finite condition and acquisition manifests are required. The N=10 label in roller plots does not establish ten independent physical specimens. Fifty stability contact points are not fifty samples. The 1230 count is a granule cohort; 200 four-granule keys yield 40,000 pair comparisons, not 40,000 independent experiments.

Time-series roller measurements must declare independent endpoint sampling or interruption/reimaging of the same specimen. Reimaging preserves slide, trap, granule, field, orientation and calibration identity. Dropped, missing, multioccupied, sidewall-bound and ambiguous sites remain in assigned slots. Retries append attempts and never overwrite earlier records.

Contact points derived from projected bead centers are estimates under the source's orthographic assumption. Registration, contact thresholds, angle wrapping and statistical implementation require declared methods. Synthetic rotated ellipses in the SI are a computational comparison, not a newly invented robot rotation experiment. Extreme encoding-capacity estimates are model-derived source outcomes, not experimentally enumerated key counts or security guarantees.

## Actor/evaluator separation and failure handling

The actor receives a selected goal, public condition/material cards, work order, qualified controls, visible object states and unresolved inputs. It does not receive the full route/evaluator answer, hidden faults or paper outcomes as future measurements. Public review files may include those references; a runtime must use a fail-closed selected projection. No runtime loader is supplied here.

An evaluator checks physical custody, preparation lineage, state-specific device receipts, control coverage and raw-record provenance. Complete truthful work may disagree with paper trends. Outcomes distinguish completion, partial work with a valid blocker, safe abort and contract failure.

Authored recoveries require stopping the affected device, preserving labels and raw evidence, observing the problem and making only a qualified bounded retry. Wrong materials are quarantined; insecure tubes are not started; unreadable images are retained and reacquired under a new attempt; lost contact sites are not deleted; chamber interruptions remain in exposure history. No robot is required to conceal a failed result to match the paper.

## Verification, access and release boundary

Run `python -B tests/run_validation.py` from this directory. Structural and synthetic adversarial checks validate references, gates, routes, arm-state constraints, source-count semantics, custody and evidence invariants. They do not validate physics, scientific analysis, instrument authenticity or robot feasibility. Independent review has its own report and exact scope.

No source PDF, extracted publisher text, figure, screenshot or movie is exported. The main article states [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/); this package contains original task prose and factual attribution, not an adapted article or a license grant for source assets. No repository LICENSE is changed. No remote publication, viewer or CAD work is performed in this draft.
