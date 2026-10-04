# Wetting-transition task design

## Scope and trust boundary

Original contracts are authored task steps informed by source evidence; the paper is not a robot protocol. Reference-only facts, authored operations and missing qualification inputs are separate records. A service request cannot create a receipt. An actor may supply only event, operation and evidence IDs. Independent evaluator-selected records determine acceptance. Public fixtures provide no real-world authentication.

## Route contracts

### R00: Freeze source and cohort design

Source locators: E01, E06, E09, E10, E16. Applicable upstream routes: none.

- R00_O01: Pin source hashes and version; admit one paper-level task, not one task per plot.
- R00_O02: Create separate cohort plans for macro, thickness, mechanics, rheology, cTFM and phase-diagram studies.
- R00_O03: Freeze exclusion, uncertainty, calibration and analysis policies before observation.
- R00_O04: Keep source reference values in evaluator-only records; assign raw acquisition and service authority separately.

Required output records: design_revision, cohort_matrix, analysis_plan_hash, source_version_id.

Qualification hold: Unresolved local branches stay HOLD; no inferred 44-condition matrix or pseudo-independent timepoints.

### R01: Prepare PDMS film lineage

Source locators: E01. Applicable upstream routes: R00.

- R01_O01: Register commercial base and curing-agent lots, glass carrier IDs and material identity.
- R01_O02: Assign 9:1, 30:1 and 50:1 formulation branches; weigh and reconcile documented quantities in a qualified preparation service.
- R01_O03: Request closed mixing, degassing, coating and curing service for the selected branch.
- R01_O04: Accept completion only from independent service receipt; inspect coating dimensions, defects and carrier identity.
- R01_O05: Route separately fabricated mechanical coupons to the characterization lineage; do not assume slide films are tensile bars.

Required output records: formulation_ledger, process_receipt, film_id, thickness_measurement, coupon_parentage.

Qualification hold: Film thickness method, acceptance tolerances and mechanical-coupon fabrication remain unknown; no invented fully cured state.

### R02: Prepare CY film lineage

Source locators: E01. Applicable upstream routes: R00.

- R02_O01: Register the distinct A and B component lots and additive identity.
- R02_O02: Resolve mixture basis and additive accounting before submitting 5:6 or 9:10 branch to the preparation service.
- R02_O03: Request closed mixing, degassing, coating and curing with separately logged carrier identity.
- R02_O04: Inspect returned film and issue sample/coupon parent-child links.

Required output records: formulation_ledger, CY_process_receipt, film_id, thickness_measurement.

Qualification hold: CY mass/volume ratio basis and quality criteria must be qualified. This does not authorize unrelated chemical synthesis.

### R03: Age and qualify sample custody

Source locators: E02. Applicable upstream routes: R01, R02.

- R03_O01: Keep separate PDMS and CY dated custody records in clean, dry, dust-protected storage.
- R03_O02: Compare experiment age to the appropriate source age interval; select like-aged controls.
- R03_O03: Inspect surface contamination and damage without touching active regions.
- R03_O04: Release only qualified sample/spot IDs; quarantine rejected films rather than silently cleaning or recuring them.

Required output records: age_receipt, storage_log, surface_inspection, released_spot_map.

Qualification hold: Elapsed wall time alone is not proof of storage conditions or surface recovery; reuse after a previous droplet requires a qualified policy.

### R04: Characterize tensile response

Source locators: E03. Applicable upstream routes: R03.

- R04_O01: Receive traceable companion coupon and qualified geometry/gauge measurements.
- R04_O02: Mount in a closed tensile-test service with calibrated force and strain channels.
- R04_O03: Acquire PDMS9:1 and PDMS30:1 repeat series and separate available CY characterization.
- R04_O04: Fit the predeclared low-strain interval and label stress measure and specimen/repeat identities.
- R04_O05: Link literature-supplied moduli separately from newly measured coupon outcomes.

Required output records: coupon_measurements, calibration_ids, raw_tensile_traces, modulus_fit, repeat_ledger.

Qualification hold: No coupon dimensions, strain rate, gauge method or complete CY tensile data supplied. CY9:10 measured-versus-inherited language is unresolved.

### R05: Measure material relaxation

Source locators: E04. Applicable upstream routes: R03.

- R05_O01: Assign four material-specific strain/repeat cohorts to qualified companion coupons.
- R05_O02: Perform closed step-strain acquisition with recorded ramp, hold and baseline semantics.
- R05_O03: Preserve each unnormalized trace, time origin, stress measure and any normalization.
- R05_O04: Fit two Maxwell times and amplitude terms with versioned fitting policy.
- R05_O05: Select the short-time relaxation parameter for the paper comparison only after checking timescale applicability.

Required output records: relaxation_traces, step_input_log, fit_parameters, fit_uncertainty, repeat_identity.

Qualification hold: Source N does not specify distinct specimens; ramp/hold schedule and stress-normalization conventions need qualification.

### R06: Check rheology and modality limits

Source locators: E05, E15. Applicable upstream routes: R03.

- R06_O01: Receive PDMS50:1 and CY9:10 rheology specimens with geometry and age records.
- R06_O02: Mount in a calibrated closed rheometer and record strain, temperature and the qualified frequency schedule.
- R06_O03: Return storage/loss-modulus and viscosity results with units and instrument limits.
- R06_O04: Record whether a crossover is actually observed; do not fabricate a relaxation time when absent.
- R06_O05: Retain SI Table1 as a literature-only modality comparison; the physical PDMS30:1 detection-limit acquisition is a distinct R11 branch, not a rheometer result.

Required output records: rheology_raw_data, frequency_schedule, crossover_assessment, literature_modality_comparison_record.

Qualification hold: Rheometer geometry, environmental conditions and repeats are not supplied. SI Table1 comparisons are literature context, not extra local experiments.

### R07: Receive patterned microscope specimens

Source locators: E02, E08. Applicable upstream routes: R03.

- R07_O01: Submit qualified silicone specimen identity and a fiducial-pattern request to an external specialist service.
- R07_O02: Receive a sealed or otherwise qualified-safe patterned substrate with chain of custody, array map and material compatibility evidence.
- R07_O03: Verify surface identity, lattice metadata, pattern extent, adhesion and containment through approved observations.
- R07_O04: Keep synthesis, ink handling and high-voltage deposition absent from robot controls.

Required output records: patterned_sample_receipt, array_geometry, containment_receipt, service_qualification.

Qualification hold: Outsourced and unmodeled preparation; no operational quantum-dot synthesis or NanoDrip recipe. Missing receipt cannot be replaced with an agent assertion.

### R08: Qualify humidity and imaging station

Source locators: E06, E08. Applicable upstream routes: R00.

- R08_O01: Verify chamber, sample mount, dispensing, backlight, side camera, environmental sensors and isolated gas/optical services.
- R08_O02: Load spatial, angular, volume and timestamp calibrations for each camera and scan axis.
- R08_O03: Require a humidity-control service receipt with measured RH and temperature stability, flow/exhaust safety and dry/wet branch identity.
- R08_O04: Freeze side/bottom coordinate transforms and synchronization policy; verify focus and field of view before droplets.

Required output records: station_revision, calibration_bundle, environment_stability, coordinate_transforms, synchronization_test.

Qualification hold: Source sensor accuracy differs from plotted RH variation. Setpoint agreement is not accuracy. No gas, laser or stage operation permitted without qualified service.

### R09: Run rigid versus compliant drying

Source locators: E06, E12. Applicable upstream routes: R03, R08.

- R09_O01: Select PDMS9:1 or PDMS50:1 sample/spot with corresponding RH condition.
- R09_O02: Deposit a water droplet through qualified dispenser service, preserving placed volume and dispensing evidence.
- R09_O03: Acquire side-view history and environmental time series until an observed endpoint.
- R09_O04: Set analysis t0 at observed 55 nL crossing for this macro cohort, separately from dispensing start.
- R09_O05: Complete the six condition groups with nine reported independent measurements per displayed curve; preserve failed and excluded trials.
- R09_O06: Obtain or explicitly select a traceable smooth rigid-PDMS receding-angle control through a qualified measurement service. Record method, sample, environment and raw angular evidence; if only the paper value is available, mark it source-reference-only and keep the new-measurement gate held.

Required output records: droplet_id, placed_volume_record, side_images, environment_trace, volume_crossing_event, macro_condition_repeats, rigid_reference_theta_r_record, reference_angle_evidence_kind.

Qualification hold: Never apply 55 nL rule to microscopy droplets already smaller than that. Distinct droplets, spots and substrates are separate lineage levels. The receding-angle measurement method is not specified in the paper and cannot be silently inferred from an evaporation trace.

### R10: Test coating-thickness control

Source locators: E07. Applicable upstream routes: R03, R08.

- R10_O01: Create PDMS50:1 thickness subcohorts with measured thickness and matched age.
- R10_O02: Run slow and fast humidity cases with independent droplet records.
- R10_O03: Compare contact-angle versus normalized radius under a frozen analysis procedure.
- R10_O04: Carry the 220 versus 228 micrometre conflict as a branch-local hold until actual measured thickness is available.

Required output records: thickness_cohort_records, drying_traces, thickness_comparison.

Qualification hold: The reported high-thickness value is inconsistent; nominal preparation recipe for variant films and repeat count are unavailable.

### R11: Capture synchronized mesoscopic drying

Source locators: E08, E09, E15. Applicable upstream routes: R07, R08.

- R11_O01: Mount qualified patterned CY5:6 or CY9:10 sample for dynamic-wetting branches, or a separate patterned PDMS30:1 sample for the dedicated detection-limit branch; identify the branch and contact-line region.
- R11_O02: Place a distinct water droplet and record actual volume, material and actual RH, rather than silently substituting nominal targets.
- R11_O03: Acquire synchronized side view and timed z-stacks through a closed fluorescence service during evaporation.
- R11_O04: Keep scan start/end times and each focal-plane timestamp; reject motion-blurred or incomplete stacks under a qualified policy.
- R11_O05: Run CY9:10 and CY5:6 slow/fast branches; retain material, droplet and timepoint hierarchy.
- R11_O06: Acquire the SI Fig13-equivalent PDMS30:1 droplet and z-stack lineage through the same qualified patterning/imaging services, preserving unresolved ridge detection as an observed resolution limit rather than a successful shape reconstruction.

Required output records: side_images, z_stack_images, frame_timestamps, scan_metadata, droplet_condition_record, branch_type, PDMS30_1_detection_limit_acquisition, resolution_limit_assessment, detection_limit_report.

Qualification hold: No source-complete autofocus, photobleaching, marker-spacing, illumination-dose or image-QC tolerances supplied. Scan duration is not instantaneous acquisition.

### R12: Assemble four-material phase study

Source locators: E10. Applicable upstream routes: R03, R04, R05, R08.

- R12_O01: Create controlled drying cohorts for PDMS9:1, PDMS30:1, CY5:6 and CY9:10 across the recorded humidity range.
- R12_O02: Link every phase-map record to its observed contact radius, angle and material-specific characterization.
- R12_O03: Track the 44 reported individual drying experiments without inventing allocation across materials/humidities or assuming independence beyond the source statement.
- R12_O04: Distinguish repeated timepoints from independent droplets and avoid duplicate counting with the other figures.

Required output records: phase_cohort_ledger, raw_trace_links, characterization_links.

Qualification hold: Exact condition allocation of N44 is not recoverable from main/SI prose; source workbook remains numerically unread.

### R13: Reconstruct deformation and traction

Source locators: E11. Applicable upstream routes: R04, R05, R11.

- R13_O01: Preserve original z-stacks, apply versioned detection and fit marker centroids.
- R13_O02: Record reported manual missed-marker insertions and interpolated z coordinates as separate annotations, never direct observations.
- R13_O03: Match deformed and ideal array vertices under a one-to-one mapping, preserving array identity and boundary anchors.
- R13_O04: Infer unloaded placement through a qualified graph-relaxation implementation; never relabel the inferred field as a captured reference image.
- R13_O05: Send displacement field, material model and boundary conditions to an independently qualified inverse-FE service.

Required output records: detected_points, annotation_log, matching_map, inferred_reference, displacement_field, FE_input_output_receipt.

Qualification hold: Author code, full model parameters and numerical settings unavailable. Edges must be demonstrably suitable fixed references. Ogden modulus wording unresolved.

### R14: Analyze wetting mechanism and forces

Source locators: E12, E13, E14. Applicable upstream routes: R09, R11, R12, R13.

- R14_O01: Establish droplet-centred coordinates from a frozen contact-line selection and circle-fit policy.
- R14_O02: Compute angle/radius histories and derivative uncertainties; retain measured apparent angle, ridge-interface angle psi, qualified rigid reference theta_r, model angle theta_r minus psi, and residual theta_star minus that model angle as distinct quantities. Keep any paper-derived theta_r comparison explicitly source-reference-only.
- R14_O03: Fit the observed current placement field P1 with a separately registered ridge-shape fit to obtain the tangent angle psi. Separately fit Ur and Uz displacement fields near the contact line for the Fig6 analysis; do not use displacement-field tangents as the current-surface tangent. Preserve fit intervals and inward/outward sign conventions.
- R14_O04: Integrate qualified traction over a declared physical area and sector angle, then report normalized quantities with dimensional checks.
- R14_O05: Apply equilibrium surface-tension inference only as a labelled model comparison; retain strain-dependence assumptions and source conflicts.

Required output records: coordinate_transform, radius_angle_series, derivative_records, ridge_fits, traction_integral, model_comparison, theta_star_series, psi_series, theta_r_reference_link, theta_r_qs_series, residual_angle_series, normalized_contact_line_speed_series, reference_based_model_or_new_observation_flag, P1_ridge_shape_fit, P1_tangent_psi_provenance, Ur_displacement_fit, Uz_displacement_fit.

Qualification hold: Integration bound conflict, polar area factor, stress convention and surface-energy assumptions must be resolved before quantitative goldens. No observed depinning is claimed.

### R15: Close custody and archive evidence

Source locators: E16. Applicable upstream routes: R09, R10, R11, R12, R14.

- R15_O01: Return chamber and instruments to independently verified isolated state.
- R15_O02: Reconcile specimen, water and hazardous-fiducial custody; route patterned samples only through qualified containment/waste service.
- R15_O03: Archive raw data, exclusions, annotations, source versions and derived-result hashes without overwriting raw evidence.
- R15_O04: Report route-level status as completed observation, failed observation, unattempted, or held; never substitute source outcomes for new measurements.

Required output records: safe_state_receipt, custody_closeout, immutable_manifest, route_status_report.

Qualification hold: This closing/recovery design is authored; the paper does not report a complete shutdown, cleaning or waste workflow.

## Branch-local blocking and closeout

Conflict mappings target exact operation IDs and scope tags. Missing actual high-thickness metrology holds the high-thickness subcohort; it does not prohibit the normal 30 micrometre macro comparison. Missing pattern containment holds microscopy and descendants; unpatterned macroscopic work stays independently designable. Integration disputes block numerical traction interpretation, not raw image preservation. U24 prevents all actual robot execution, but does not defeat metadata-only bookkeeping or design. All 16 routes have immediate closeout edges. R15 archives a held record even when isolation is unknown; unknown isolation never permits sample removal.

## Lineage and independence

Mixed-material routes are campaign bundles, never a single specimen. Each operation carries explicit material scope and distinct constituent sample, spot and droplet identities with material-specific preparation ancestry. R11 separates CY dynamic-wetting records from PDMS30:1 detection-limit records; R09 rigid-angle reference admits only its rigid PDMS branch. Missing reference-angle qualification does not block independent macro acquisition, and missing original source data blocks only source-reanalysis claims.

Keep formulation batch, physical sample, surface spot, droplet, frame/stack, annotation and derived artifact identities distinct. Nine independent measurements per macro curve do not establish nine substrates. Four CY5:6 droplets / 24 timepoints and five CY9:10 droplets / 38 timepoints cannot be pooled as 62 independent droplets. Forty-four phase experiments have unresolved allocation/overlap; SI 27/6 are observation counts with unresolved independence. Tendencies or counts in source curves cannot fill a missing specimen ledger.

Ageing requires actual cure timestamps plus qualified storage custody. A synthetic timer or file mtime cannot qualify a specimen. Film samples and companion coupons have distinct geometry and IDs. Missing reuse/cleaning/disposal policies remain holds; failed attempts are never overwritten.

## Analysis and reference semantics

55 nL defines only the macro analysis origin when an actual recorded downward crossing exists. Microscopy retains placed volume and each scan/plane time, including its 49 nL example. RH setpoint, stability and accuracy are separate quantities. Raw coordinates, manually annotated detections, interpolated z values, inferred unloaded references and model-derived stress have separate evidence kinds. The P1 current-placement tangent used for psi is separate from Ur/Uz displacement fits. Source theta_r is a source-only model reference unless an independent receding-angle measurement is qualified. Equilibrium-based tension inference remains conditional.

No graph relaxation, FE inversion, material fitting, image segmentation or uncertainty solver is implemented. The synthetic algebra functions exist to test units and provenance, not to validate a scientific model. Traction-times-physical-area has units N; area convention and radial-window disputes must be independently disposed before a quantitative application.

## Assets

Every operation binds namespaced semantic anchors in the original static asset plan. Bench-scale carriers are separate from magnified microscopy geometry. Glass, film, marker and pipette dimensions are source references only; active films, droplets, marker points and pipette tips are not robot grasp targets. Original device casings are illustrative. No graphical shape creates a successful measurement, hardware qualification or receipt.

## Validation boundary

Sixty-four finite synthetic route/outcome fixtures exercise metadata completion, qualification hold, data hold and isolation hold for all 16 routes. They never certify real qualification, physical observations or source result agreement. Standalone author and independent hostile-mutation tests cover synthetic evidence integrity, scope, provenance and export sanitation. Passed checks do not establish a calibrated simulator, physical execution, hardware safety or scientific reproduction. The complete design remains subject to the ten source cautions and 25 missing inputs.

