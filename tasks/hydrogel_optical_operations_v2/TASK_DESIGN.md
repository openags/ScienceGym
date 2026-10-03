# Hydrogel optical micro-metastructures: robot task design

## Scope and readiness

This package converts the experimental program of Zhang et al., Nature Materials (2023), DOI 10.1038/s41563-023-01649-3, into an original, inspectable ScienceGym design. It covers abiotic hydrogel mechanics, microfabrication, geometric reconfiguration and optical readout. The commercial gelatin-derived comparison resist is inert material; no living system, biological engineering or dissemination is in scope.

There are 36 physical branches and 107 operation definitions. The 53 coverage records enumerate six main figures, nineteen supplementary figures, four Extended Data captions, nine videos, eight Methods subsections and seven workbooks. FEA, analytical mechanics, fitted curves and the UV-lithography compatibility statement have separate nonmanual dispositions. Counts represent authored definitions and coverage records, never executed tasks or independent scientific samples.

The source audit read the complete deposited main text/Methods/captions and 22-page written SI, inspected six main figure images and nineteen SI figures, parsed seven workbooks and inspected eight temporal keyframes per video. Four Extended Data images remain visually uninspected. This is therefore a source-grounded design with an explicit visual gap, not a claim that every source dependency is complete. The task author used that audit and checked Methods titles in the deposited JATS; the package does not imply a second complete media review.

No physical simulation, numerical reproduction, robot execution, instrument actuation or experiment occurred. All fixture evidence is labeled synthetic. Assets, qualified service cards, geometry, grasp plans and production evidence authentication remain unimplemented.

## A complete preparation lineage

The route cannot start with an unexplained finished specimen. PREP_FORM keeps distinct hydrogel batches and qualified formulation identities. PREP_PRINT binds a supported glass substrate, resist, approved structure map and dose/orientation-map revision to a guarded fabrication job. Automatic substrate calibration must be evidenced by that service. PREP_DEVELOP preserves the material-specific development lineage: water, acetone and 2-propanol belong to different reported resist classes and cannot be interchanged under a generic solvent operation.

PREP_SPACER assembles the supported cover and spacer components into a capillary cell. The source describes a typical 214-micrometre bead diameter and a spacer-glue UV exposure; neither substitutes for a qualified fixture or cure card. PREP_CURE binds both the identified hydrogel batch and the printed structure to the infiltrated/cured composite. Source wavelength and duration are insufficient to establish UV dose or uniformity. Chemical formulation, infiltration, all UV exposure and solvent/waste contact remain inside closed qualified services.

PREP_COVER removes a separately identified cover while preserving the original substrate identity. The service must inspect damage, retained debris and composite continuity. PREP_CHAMBER adds the identified water observation chamber and its seal/leak evidence. PREP_RELEASE then requires a qualified thermal service and same-specimen optical evidence of self-peeling and free motion. Merely commanding or reading the reported 50-degree-Celsius release temperature does not establish release.

PREP_GEL_CURE first requires a closed, qualified UV cure of standalone hydrogel sheets. PREP_COUPON is then a separate laser-cut hydrogel coupon route for material characterization. It does not falsely require printed microstructures. The source's coupon scale is a reported geometry context, not a complete cutting job. Process parameters that are absent from the paper remain absent here.

## Robot/service separation

Each of seventeen services has six explicit phases: LOAD, VERIFY, HANDOFF, READOUT, UNLOAD and COMMIT. The robot handles retained closed carriers and reads qualified interfaces. It does not open material vessels, position loose beads, separate exposed glass, handle solvent, issue laser/UV commands, program thermal stages or run fabrication equipment.

Loading requires identified payload, carrier, fixture and safe exchange state. Verification binds the station, qualified job, input-card revision and calibration. Handoff transfers custody using an approved job identifier, with no recipe or device actuation supplied by this package. Readout obtains authoritative completion and raw-record references tied to specimen, version, condition, cycle and attempt. Unloading waits for isolation and release-to-handle. Commit advances lineage only from the service's accepted output; rejection preserves the failed attempt and quarantine state.

PLAN, MOVE, INSPECT, ARCHIVE and CLEAN add nonempty allocation, retained transport, own-specimen baseline, immutable records and service-owned waste/shutdown receipts. All coordinates, support limits and trajectories require qualified instance cards. A handoff receipt does not imply the robot carried out the enclosed process.

## Physical branches and comparisons

1. Hydrogel controls: PNIPAM, PNIPAM/PVA and LIHAM have separate provenance. HYDROGEL_CONTROLS compares transparency and deformation; HYDROGEL_TRANSMISSION retains the reported PNIPAM/LIHAM spectral comparison; MONOMER_SWEEP and COMPOSITION_SWEEP retain the reported concentration and ratio classes. Full per-condition recipes are missing, so components are not silently rescaled. RHEOMETRY requires its own geometry, loading and temperature qualification.
2. Beam characterization: BEAM_AFM, BEAM_POWER and BEAM_SPEED preserve dose and scan-speed series separately. A tested series is not a default printer setting. BEAM_LINEAGES distinguishes the SI's 15-mW beam from the main figure's 50-mW beam. Axial contraction, buckling wavelength, amplitude and rotation require registered observations and explicit pre-buckling missingness. Out-of-plane buckling is a measured alternative morphology, not a projection error to suppress.
3. Material comparison: RESIST_COMPARISON retains the inert soft comparison resist, DEGRAD INX N100 and IP-S with different development services. Compatibility across these examples is not evidence for arbitrary material substitution.
4. Crosses and square lattices: CROSS_MODES records one through six half-wave counts. SQUARE_LATTICES distinguishes the demonstrated chiral and achiral classes. INCOMPATIBLE_CONTROL preserves real spacing defects. LATTICE_CYCLES retains the separate 27-cycle history; every scheduled cycle is a record, including failed or excluded observations.
5. Geometry and scale: TRIANGULAR, CIRCLES and ANISOTROPIC_GRID preserve their distinct layouts. THREE_D keeps SEM architecture evidence and confocal reconstruction separate, with temperature, reconstruction and specimen identity retained. MICRO_SCALE and MACRO_SCALE have separate carrier/geometry needs. Caption support and sampled Video 8 do not erase the Extended Data visual gap.
6. Power image: POWER_IMAGE requires an approved input raster, power-map function and complete build revision. Neither an artistically plausible result nor an invented grayscale mapping counts. Connected printed crosses and enclosed regions are different objects for segmentation. IMAGE_CYCLES has 25 cycles, distinct from the square lattice's 27.
7. Polarized optics: POLAR_GRATING requires calibrated angular response. ANGLE_IMAGE_MAIN keeps the 100-by-100, 10,000-unit specimen separate from ANGLE_IMAGE_VIDEO's 150-by-180, 27,000-unit specimen. Illumination, exposure, background, polarizer/analyzer alignment and registration controls precede any concealment claim. Video 9 is played twenty times faster; its 18.88-second clip cannot be used as an experimental response time.
8. Dual encoding: DUAL_IMAGE requires a combined power-and-angle assignment, not a renamed power-only or orientation-only map. Ordinary and crossed-polarizer observations remain separate. The combined build function is unavailable, and Extended Data Fig. 4 remains visually uninspected.

Branch operation lists express required membership, not one inferred historical chronology. Every use receives its own branch/condition/cycle/service/attempt/phase occurrence. Dependency edges require upstream material lineage; they do not prove the same author specimen was reused. Instance planning must allocate material variants, same-specimen cycles, safe siblings and destructive reservations explicitly.

## Source conflicts and unknowns

source_conflicts.json preserves ten issues. Most consequentially, Fig. 4l reverses the 20/50-mW morphology labels relative to the narrative and Videos 5–6. No dose-to-target mapping can be programmed by choosing the preferred reading. Fig. 3j's wavelength/amplitude headers disagree with plotted interpretation; values and headers cannot be silently exchanged. Related position units, dimensionless-versus-percent headers, SI Fig. 16 panel/unit mapping, malformed PVA molecular weight and flattened equations retain independent gates.

The reported n values are feature/data-point counts unless independent batches are explicitly evidenced. Dense fitted lines are not additional measurements. A heated value labeled 0–360 in the Fig. 6f workbook is a single constant, not 361 independent readings. Workbook '--' and pre-buckling undefined quantities remain absent, not zero. Different reference lengths and swelling normalizations cannot be pooled as one contraction metric.

Twenty-two unknown cards cover apparatus/scene, sample allocation, closed processing, microscopy, metrology, analysis, image mapping, Extended Data visibility and model information. Unknowns have no executable defaults. Numerical values in source_outcomes.json are evaluator references and never universal acceptance thresholds. A qualified authored episode choice must remain identified as authored; it cannot retroactively correct the source.

## Evaluation and visibility

Only agent_visible.json is actor-visible in this design. It contains the general carrier-management goal, allowed actions and empty inventory/cards/observations placeholders. It has no source targets, expected morphology, future measurements or evaluator solution. Full contracts, branch graph, source findings and tests are authoring/evaluator materials. A future runtime must construct actor inputs from authorized instance cards and observations already acquired.

The verifier checks synthetic bookkeeping. Its trusted context is supplied independently from actor events in the intended interface, but cryptographic authority and a real event logger are not implemented. Tests create clearly marked authored fixtures; they do not generate scientific sensor values. This limitation is deliberate and must remain visible when these tests pass. PLAN is represented by context maps, INSPECT by control/lineage records, and ARCHIVE/CLEAN by synthetic completion receipts. The tests do not validate actual carrier paths, grasps, cleaning or physical inspections.

Acceptance requires the selected dependency closure, every condition/service/cycle cell, qualified cards, relevant control records, complete phase sequences and exact specimen/version/station/fixture/calibration bindings. Same-specimen cycle histories cannot be replaced by a new specimen without lineage. Unsafe exchange, missing optical release, failed receipts, missing archive or cleanup and source-target leakage reject completion. Whole-campaign mode additionally requires all 36 branches. Unknown repeats cannot be empty loops, zero, null or a fabricated source count.

## Validation and export

Run the package tests with Python 3.9 or newer:

    python3 -B -m unittest discover -s tests -v
    python3 -B tests/verify_package.py
    python3 -B tests/verify_export.py

Read VERIFICATION.json and review/ for exact tested scope. These checks do not validate instrument safety, object geometry, robot feasibility, scientific outcomes, production authority or physical dynamics.

EXPORT_ALLOWLIST.json enumerates every exportable original file and hashes each payload except itself. The exporter rejects additions, missing files, symlinks, path traversal, forbidden binary/source formats and hash mismatch. It never authorizes publication. No publisher PDF, image, movie, workbook, source-text dump, credential or local research path is included.
