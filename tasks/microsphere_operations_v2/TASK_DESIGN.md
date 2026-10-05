# Whole-paper design: inert-target microsphere microscopy

## Objective and completion boundary

The actor assembles an auditable evidence workflow for the reported experiment family. It selects operation and evaluator-provided receipt IDs, preserves specimen and calibration identity, keeps controls and failures, and closes out all branches honestly. Task design completeness means that every route and source branch has an explicit disposition. It does not mean a laboratory experiment was run, the paper was reproduced, or 50 nm resolution was independently certified.

The accepted reading covers six main pages, seven supplementary pages, four main figures and six supplementary figures. This package uses the accepted reviewers' factual analysis; it does not claim the task author independently remeasured figures. The formal Nature Communications source is eligible at one paper-level count. Target families, sphere sizes, controls and models are not additional papers. The source is free to read at its official record, with 2011 Macmillan all-rights-reserved language and no established Creative Commons grant. All exported prose, contracts and code are original authored work.

## Source branches and evidence boundaries

- E01: grating transmission. Reported chromium-on-fused-silica grating has 360 nm lines, 130 nm gaps and 30 nm coating. The 4.74 micrometer sphere example reports a virtual plane 2.5 micrometers below the surface and 4.17x added magnification. These are context, not controller parameters or pass constants
- E02: gold/AAO transmission. The reported 20 nm experimental gold coating, 300 micrometer template and nominal 50 nm pores/spacing remain separate quantities. Approximately 8x magnification and the illustrated 50 nm claim belong here. Pore diameter, edge gap, pitch and virtual-image separation require distinct qualified definitions
- E03: Blu-ray reflection. Protective-layer removal is closed-service provenance only. The source body's 200 nm lines/100 nm gaps conflict with caption wording; the task does not silently pick a replacement geometry
- E04: star-pattern reflection. The 90 nm corner claim is source context. SbTe/GeSbTe composition conflicts and the unreported sphere diameter remain held. A 4.74 micrometer default is forbidden
- C01: bare and two half-ball SIL controls. Bare focus is independent. The 0.5 mm/80x and 2.5 mm/40x conditions remain distinct. Failure is legitimate. Blu-ray controls are illustrated; the all-target extension is text-only
- C02: 1, 3, 4.74, 10 and 50 micrometer size screen. Success/failure claims are text-only outside explicitly illustrated conditions. Small-view-window failure is practical, not a theoretical prohibition. No full target-by-mode-by-size matrix or repeat count is invented
- C03: claimed gold-coating contribution. Causal comparison requires a paired uncoated state or matched specimen and supporting evidence; the paper supplies no paired figure series
- E05: complex-shape transmission and 50 nm reflection claims. These remain source-context-only because the corresponding panels were not supplied
- C04: illustrated array coverage and proposed view combination. Multiple spheres do not establish independent repetitions, a calibrated mosaic or a working stitching algorithm
- N01–N04: index/size survey, SIL/sphere/surface field comparison, ray/field-enhancement analysis and Poynting-flow construction. Every model branch remains UNRUN. Experimental 20 nm gold differs from modeled 40 nm gold. Measured, heuristic and line-dependent magnifications never become one transfer model

Predicted higher-index/sub-20 nm performance and prospective biological applications are outside the practical task. No biological arm is implemented.

## Stations, carriers and preparation

ST01 receives documented inert material identities, stock lots, control lenses and protective carriers. ST02 represents a qualified preparation service. ST03 represents qualified contained sphere assembly or documented lens contact. ST04 accepts independent transmission/reflection optical receipts. ST05 is the closed SEM reference service. ST06 reviews evidence and source claims. ST07 records protected return, quarantine, containment and archive.

The route is substantive about specimen preparation: E01 needs a qualified grating geometry/surface certificate; E02 needs topology/spacing definitions and coated-template lineage; E03 needs disc/layer identity and post-removal integrity; E04 needs resolved film composition and traceable pattern identity. Preparation outputs are never assumed from requests. Operations for anodization, coating, beam/vacuum, laser processing, disc stripping and solvent handling are not exposed. Historical instrument and supplier names are attribution only.

Sphere-stock records distinguish all five nominal sizes, size distributions, chemistry and containment. No guessed concentration, dispensing volume, drying program, contact force, exposure, focus search or stage pose is supplied. Source-unreported values must remain absent or be separately qualified by an authorized service. Scene coupon dimensions and anchor locations are nominal illustration, never qualification.

## Authored stage DAG

The paper does not define a traceable experimental chronology; the following is an authored evidence-processing order. dependencies.json preserves the accepted route graph.

1. R01 registers source/version, rights boundary, deduplication and prospective repeat/metric/exclusion policy IDs
2. R02 identifies four target families, carriers, lots and surfaces. E04 may remain held while other families retain their records
3. R03 accepts finished-specimen certificates and creates parent-linked preparation states. Every physical operation remains behind a qualified service interface
4. R04 accepts SEM reference metadata, ROI maps, calibrations and a post-service state. SEM exposure is not presumed nonperturbing
5. R05 distinguishes sphere lots, contained stock and both SIL/objective compatibility receipts. The source star sphere diameter remains null
6. R06 creates sphere-contact child states from the reference-characterized baseline and explicit SIL-contact child states. Bare controls retain a separate uncoated state or documented matched specimen; a coated state cannot be relabeled bare
7. R07 accepts E01/E02 transmission records with specimen, state, ROI, independent focus, calibration and frame provenance
8. R08 accepts E03/E04 reflection records without promoting star composition or sphere size. Held optical evidence remains absent
9. R09 preserves bare and both SIL comparators, their separate focus records, objective differences, contact states and failed/unassessed outcomes
10. R10 retains C02/C03/C04/E05 evidence categories and missing data. Source claims do not become new measurements
11. R11 checks optical/SEM pairing, exact-state correspondence or explicitly limited equivalence, frozen metric policy, uncertainty and independent reviewer IDs. It cannot certify resolution
12. R12 inventories N01–N04 source methods with code_run, simulation_run and generated_data all false
13. R13 archives every preceding receipt hash, every failure event and every branch disposition. Held material stays quarantined. Unreceived material has null identifiers and not_received disposition

Receipt acceptance is digital contract acceptance. A held predecessor does not release a downstream physical-service stage. Review and closeout can still record complete dispositions with holds, avoiding deadlocks that would erase failed or missing work.

## Actor/evaluator separation

The actor action has exactly operation_id and evidence_id. Receipt payloads, source outcomes, qualifications and sensor truth cannot be supplied through that action. The independent evaluator injects an immutable copy of a receipt map at episode creation. The code snapshots input and returns copies; in-process private fields are not a security sandbox. Authenticity of external records is an explicit external prerequisite, not established by an ID or a synthetic hash.

Every receipt binds campaign, epoch, frozen plan, operation, semantic-core digest, exact dependency hashes, branch scope and qualification references. Unknown fields and operational numeric controls are rejected. Source reports and scene output cannot be selected as observation origins. Finite fixtures are labeled independent_fixture and their outcomes must be not_assessed. They contain no detector pixels or physical measurements.

All sixteen qualification groups are preserved in unknown_inputs.json. U01 preserves the original-only rights boundary and does not bar original authoring. U02–U16 cover stock, assembly, target geometry/composition, preparation, calibration, contact, controls, registration, metrics, repeats, text-only claims, model reproducibility and safe closeout. The fixture's synthetic qualification tokens only exercise software branches; they do not resolve those gaps in reality.

## Metrology, controls and repeats

FRAME_OBJECT, FRAME_VIRTUAL, FRAME_DETECTOR and FRAME_SEM are separate identities. Coordinates and detector scales require independent receipts; no identity transform or pixel-to-nanometer scale is invented. Optical objective magnification, added virtual magnification and detector scale are distinct. Scene world-space meters describe illustration layout, while nm/um/mm source facts are metadata with separate provenance.

Reference records and optical records require their own calibration and immutable stand-in/real raw-record hash. Pairing by filename, appearance or nearest time is prohibited. An exact correspondence claim must match specimen, state and ROI. Preparation and SEM change state; therefore the ordinary fixture uses an explicit documented-equivalence receipt and limitation instead of pretending exact same-state evidence.

Repeat counts, independent specimen/field definitions, ordering, day-to-day blocks, exclusion criteria and uncertainty budgets are not reported. A future owner must freeze their authored plan before acquisition. No multiple frames or spheres are automatically independent repeats. Failures and exclusions remain recorded. Metrics cannot be changed after plan freeze merely to fit the source headline. Bare and SIL failure outcomes remain valid records.

## Failure, bounded recovery and closeout

Malformed, foreign, stale, replayed, out-of-order or scope-mismatched proposals are rejected and appended to a hash-linked history. Each stage permits at most two digital validation attempts. This bound is an authored software rule, not a source experimental repeat count or authority for physical retries. Recovery needs separately issued qualified evidence; there is no numeric parameter search or tuning-until-success loop.

Missing identity, damage, contamination, uncertain contact/clearance, bad calibration, saturation, incomplete metadata, untraceable pairing, incompatible scales or rights restrictions require a hold. A new specimen or altered state needs a new identity and preserved parent history. Qualified closeout receipts cover safe equipment state, protective optics storage, particle/residue containment, service release and specimen archive/return/quarantine. No drain, waste or cleaning recipe is supplied.

All-held episodes can be closed as designs only, retaining missing specimens and unresolved branches. Whole-paper physical execution remains false. R13 cannot promote an earlier held, text-only or unrun branch, omit failed proposals, change specimen identity or discard raw-record hashes.

## Paired assets and reproducibility

shared_binding_contract.json is identical in task and scene. It defines nine asset roots, 33 evidence-only anchors, seven stations, thirteen routes, branch/material/state identities and coordinate-plane IDs. All anchors are semantic interfaces with physical actuation disabled. The scene includes generic carriers, inert target proxies, contained stock, separate SIL proxies, a microscope placeholder, closed services, coordinate overlays, evidence displays and closeout objects. Neither an illustrative surface nor a rendered view is measured resolution evidence.

A canonical shared-contract digest rejects semantic drift. The task and scene then pin curated immutable core manifests after independent acceptance. Reciprocal reference and final manifest files are excluded from core digests to avoid cycles, but covered by final package manifests. Sanitized ZIP export is allowlist-only, deterministic and checked for hashes, path traversal, symlinks, hidden/private metadata and unexpected binaries. The task contains original text/code only; no publisher media or copied CAD is packaged.
