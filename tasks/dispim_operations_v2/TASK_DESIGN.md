# Full-workflow long-horizon diSPIM robot task design

See `EXPORT_SCOPE.md` for the public-copy boundary. This directory is a reviewable task design; referenced source archives and Hooke assets are not bundled.

This design converts Kumar et al.'s diSPIM paper into a family of source-grounded, checkable robot tasks: manual installation and assembly, three-camera closed-loop alignment, reference-material preparation and quantitative calibration, followed by routine model-sample preparation, dual-view imaging, registration/reconstruction and closeout. The first route connects the entire workflow through embryo time-series archiving rather than starting with a prebuilt bead coverslip.

The current deliverable is a task design and requirements for later static assets. No real instruments or biological materials were used; no physics simulator, complete static asset set or repeat of the scientific experiment was produced. Success conditions must depend on visible task evidence and state histories. Results reported by the paper must not be presented as measurements from this task.

## Sources and versions

- Paper: Dual-view plane illumination microscopy for rapid and spatially isotropic imaging, Nature Protocols 9, 2555–2573, DOI 10.1038/nprot.2014.172
- The main text is the 36-page NIH/HHS accepted author manuscript hosted by MBL. It identifies itself as an author manuscript with a PMC availability date, not the publisher's version of record
- Publisher supplements comprise 43 pages of notes/tables, 10 separate supplementary-figure PDFs, 4 videos and 8 data archives
- Relevant nodes retain filenames, public URLs, page/step locators and existing SHA-256 values. Factual descriptions are newly written; the original PDFs, screenshots, videos, archives and source code are not redistributed in the asset package
- Earlier reading/hash records are source evidence. The authored design checked the main procedures and relevant SI; this does not independently reproduce all data

Source entry points: [publisher page](https://www.nature.com/articles/nprot.2014.172) and [public author manuscript](https://www.mbl.edu/sites/default/files/2022-12/diSPIM_Kumar_etal2014_NatureProtocols.pdf).

## First complete task

The robot can receive only this goal:

“Using the assigned virtual diSPIM components, routine materials and task manifest, deliver paired, traceable, quality-checked embryo dual-view time series and reconstruction results. Save raw data and required evidence, leave the instrument and bench in a safe closeout state, and explicitly report anything that cannot be verified.”

The goal reveals no correct knob sequence, fault labels or hidden grading state. The paper and component instructions may be available as references, while observation and manipulation remain the robot's responsibility.

### Initial state

The optical table is installed externally so that lifting a heavy table is not disguised as a routine robot action. The frame, lower observation path, dual-arm modules, optics, piezos, camera supports and cables are manipulable subassemblies on trays. The commercial-source option is the main-route entry; a custom source is an alternative. Coverslips, O-rings, routine reference materials and embryo-model tools await preparation rather than being completely prepared for the robot.

Camera and optical responses use explicitly labeled authored presets. Initial conditions may include diagnosable miswiring, decentering, focus offset, sheet-scan mismatch or sample-coverage problems. The robot sees only genuinely visible labels, images and indicators, not fault truth. The task connects to no real lasers, motors, pipettes, animals or cultures.

### Complete operation chain

1. Verify instrument identity, safety mode, bench, computing platform, three cameras and control channels
2. Install RAMM, the lower Z stage, mirror cubes, filters, tube lens, bottom camera and 10x air objective; confirm XY, F and Z roles
3. Assemble the marked-coverslip chamber and establish XY/Z references using bottom observation
4. Connect both scanners and check centering, iris and collimation; individually install dichroic assemblies, both objectives and piezos
5. Wire with power off, then check neutral settings and sensor readback; approach the reference coverslip with bounded motion and save F with its origin version
6. Prepare the bead layer and dye reference; raise the module before exchanging chambers and use bottom-view spots for coarse alignment
7. Install each camera's spacer tubes, mirror cube, tube lens and supports; establish clearance before rotating each camera and check each illumination arm against its opposing detection arm
8. Use bottom, A and B camera feedback for closed-loop confocality and ROI centering; save complete calibration and the bottom-view reference
9. Use bead scouting to distinguish collection defocus, sheet lead/lag, scale mismatch and aggregation; reacquire until evidence agrees in both arms
10. Obtain dual-view beads and same-settings dark backgrounds; select single beads, verify voxels/reslices and record lateral/axial PSFs. Then fix the collection plane, scan the sheet and check thickness at multiple positions in both arms
11. Represent routine worm observation, embryo isolation, mechanical capillary transfer, central adhesion and orientation fully with nonbiological models
12. Raise the module to exchange the embryo chamber and localize from below; separately check dual-view fields, illumination coverage and Z range, correcting with the corresponding controls while preserving synchronization
13. Verify focus, structure and signal in both views and obtain matching backgrounds; complete the manifest's paired timepoints without omitting an arm or overwriting existing data
14. Convert, order and merge volumes, crop and subtract backgrounds, retaining raw files and every derived result's lineage
15. Choose once, segmented or per-timepoint registration from drift across the full series; check A/B, axes, voxels, PSFs, resources and every timepoint pair
16. Inspect raw, transformed and reconstructed results. Return to strategy selection if late registration fails; attractive deconvolved images alone cannot establish success
17. Archive and verify by readback; stop acquisition/excitation, raise the module before removing the chamber, sort consumables, preserve unresolved issues and reset the bench

`FIRST_COMPLETE_ROUTE.json` contains 18 stage contracts and 82 macro-operation occurrences. Nodes may include repetition across arms, per-position sampling, timed waits and diagnostic loops; 82 is not a count of low-level robot actions or timesteps. Node counts do not generate additional paper credit.

## Full-paper family scope

`OPERATIONS.json` contains 92 macro operations. It maps main steps 1–95, all 24 substeps of 96A, all 25 substeps of 96B, and 97–106. Prerequisite material/tool preparation and authored closeout are labeled separately. `COVERAGE.json` checks mappings, not executability or scientific correctness.

`BRANCHES.json` contains 18 branches: initial platform checks; lower optical path; dual scanner/objective assembly; materials/chambers; three-camera alignment; bead synchronization diagnosis; PSF; sheet thickness across the field; embryo preparation; embryo time series; cell preparation; cell time series; conversion/preprocessing; registration/fusion; closeout; custom-excitation alternative; color modes; and theoretical design boundaries.

Seven templates cover:

- Initial assembly through the full embryo workflow
- A daily embryo task after qualified calibration exists
- Initial assembly through routine cell preparation and time series
- Dual-arm bead/sheet calibration followed by reconstruction and archiving
- Mismatch diagnosis and recovery on an existing instrument
- Reprocessing existing dual-view data and recovering from registration errors
- Passive custom-source topology using a checked control platform as prerequisite

The theoretical 10x optical option remains a reference boundary, not another demonstrated manual experiment. SI includes GFP 488 and mCherry 561 modes; this does not establish reported or implemented simultaneous dual-color biological validation.

## Translating manual procedures into robot actions

This is more than a sequence of GUI clicks. Cameras, mirror cubes, filters, O-rings, coverslips, screws, fibers, BNC cables, pipetting tools and chambers need independently graspable or adjustable parts. The minimum action vocabulary is identify, select, grasp, support, align, insert, connect, lock, loosen, rotate, translate within limits, block, use a pipetting proxy, wait, observe, compare, record and return.

Every operation records source steps/locators, source facts, authored robot handling, preconditions, postconditions, observable evidence, failure/recovery, asset references and unknown parameters. This supports checking what happened and why completion was accepted, rather than merely whether a final button was pressed.

Example one: sample exchange requires the trace “module raised, clearance visible, old chamber removed, new chamber installed, identity verified, bounded return.” Changing the sample name to embryo is not completion.

Example two: sheet/piezo diagnosis contains two different control experiments. Focus localization fixes the sheet and scans the collection plane; thickness measurement fixes the collection plane and scans the sheet. Reversing these roles changes feedback; they cannot share a universal success button.

Example three: incomplete embryo coverage may arise from lateral field, illumination range, acquisition depth or drift. The robot should choose its correction from dual-view evidence. The source explicitly warns against destroying calibrated Z-scan offsets to compensate for volume coverage.

## Three distinct information classes

### Source facts

Actual component identities, step relationships, interface semantics, observation patterns and illustrative paper parameters may be referenced. Two Nikon MRD07420 40x NA0.8 water-dipping objectives, two Hamamatsu Flash4.0 cameras, the lower Olympus 10x NA0.3 air objective and ProgRes camera must retain separate identities. Renaming existing Nikon TiE or iXon assets does not make them the paper's instrument.

`SOURCE_PARAMETER_REFERENCE.json` lists a small set of optical, sampling and timing examples and explicitly is not a hardware-control file. Paper PSFs and waist thicknesses are reference results, not values for the robot to fabricate.

### Authored handling

Tray positions, proxy interfaces, discrete locking states, bounded movement slots, virtual timers, mechanical-pipette substitutions, preset observations, completion evidence and closeout structure are authored. They must not be labeled source_reported. Every synthetic image, reading and preset reconstruction must be labeled authored_preset, while source reference material is source_reference; these categories must remain distinct.

### Unknown parameters

Robot model, hand size, workspace, real component CAD, threads, tightening torque, envelopes, actual origins, camera serial numbers, software drivers, stocks and real culture conditions are unknown. Keep them null or as named missing inputs. Unscaled assembly photographs, microscopy scale bars and tube-lens focal lengths do not establish mechanical dimensions. The design invents no precision for such quantities.

## Initialization, observations and the hidden evaluator

Initialization separately needs component/sample identities, installed/uninstalled relationships, calibration-history versions, a timepoint manifest, safety/power states, a small set of diagnosable faults and provenance-labeled observation resources. Randomize faults only among categories distinguishable from available observations.

The robot sees goals, labels, reference instructions, acquisition/processing interfaces, observations and saved history. The hidden evaluator holds the correct connection graph, fault seeds, allowed preset-response map, procedural constraints, collision exclusion zones and completion predicates. Do not put the full operation sequence or correct preset keys in the agent goal. Visible asset names must not contain answer labels such as “bad filter” or “correct knob.”

Preset camera responses may use a discrete parameter/structure lookup or newly authored images. Observations must be consistent: blocking A excitation affects its optical path; ROI changes affect the field; origin resets invalidate old coordinates; key calibration changes invalidate dependent acquisition qualification. This does not require claims of real optics or biological dynamics.

The files specify this mechanism but implement no response engine or physics simulation.

## Checkable termination conditions

A complete experimental route must satisfy all of the following:

- Critical subassemblies are connected, secured and identified, without substituting dual-arm or lower-path identities
- Dual-arm calibration has bottom-view and individual-arm evidence with traceable ROIs and F-origin versions
- Beads, matching backgrounds, PSF units and cross-field/dual-arm thickness evidence are complete
- Sample provenance, preparation, loading and orientation are recorded; prebuilt inputs do not count as completed prerequisite preparation
- Each requested timepoint has the correct A/B pair, or incompleteness is explicitly reported
- Processing preserves raw files and traces every result to background, crop, voxels, transform and processing configuration
- Registration checks cover the required time range rather than only the first frame
- Every image/reading has a clear provenance class, without fabricated measurements or scientific-reproduction claims
- Archives pass readback, acquisition/excitation are stopped, samples are safely removed and the bench is reset

Initially report hard gates and separate credit categories rather than a single aggregate score. Report assembly, procedure, observation-based diagnosis, data integrity, result credibility and closeout separately. Weights and pixel/motion tolerances are unvalidated and must be explicitly authored later; a paper's 20% or 0.7 mm example is not a universal acceptance rule.

Collisions, real hardware commands, mouth pipetting/open flames, silent data loss, wrong-arm pairing, fabricated source results and unauthorized source-media redistribution fail the task. Honest blocking on missing inputs or source contradictions is valid reporting, not experimental success.

## Long horizons and recovery

The paper places initial assembly/performance checks over several days, with separate preparation/acquisition and processing waits. The benchmark should preserve cross-stage memory, consumable state, timing, filenames, calibration versions and data pairing without forcing a static evaluation to wait real days.

Waits may be authored stage timers, explicitly representing neither real culture nor real acquisition. Save a checkpoint after each stage. Recovery must restore more than success labels: object positions, material consumption, origin versions, parameters, existing files and incomplete timepoints must persist. Interrupted acquisition retains only timepoints actually completed; reopening an interface must not fill missing data automatically.

Failure loops should cover miswiring; reversed/loose filters; centering/collimation interactions; spot overlap; confocality/ROI; bead focus, sheet lead/lag and scale mismatch; aggregation; abnormal thickness; drift; A/B coverage differences; filename conflicts; voxel/axis errors; time-dependent registration failure; and processing-memory warnings. Each loop chooses recovery from observations and repeats affected evidence collection.

## Biological and other risk boundaries

Routine beads, fluorescent dyes, common noninfectious model samples and microscopy are not removed merely because they involve biology. Embryo/cell preparation, loading and imaging remain in the family structure.

This deliverable authorizes no real animals, cells, genetic engineering, cultures or hazardous chemistry. Animal isolation uses nonbiological separable models; mouth pipetting is explicitly replaced by virtual mechanical aspiration/dispensing; flame-made picks and pulled capillaries use prefabricated safe tools; heavy installation is an external prerequisite; acid, heat and ethanol handling use closed empty containers/stage cards. These substitutions must not be claimed as unchanged replicas of source procedures.

The cell branch retains manual stages of cleaning, seeding, state checks, reporter-label handling, waiting, health/fluorescence checks and imaging-medium transition. Construct production is outside the design; a future runnable static scene receives qualified pre-labeled stocks and provides no sequences, engineering design, transfection optimization or real execution recipes. Pathogens, enhancement of dangerous biological functions and weaponization are outside the task.

Lasers, powered wiring, glass and real waste handling carry separate risks. This design uses exclusion zones, power-off states and safe substitutes. Real execution requires separate manufacturer/institutional procedures and professional validation.

## Do not erase source differences

- Main Figure1 says MS-2500; SI Table3 says IX-8102. Later static construction may choose a clearly labeled proxy, but cannot silently remove the conflict
- Main text and SI differ between 5 mm and 4 mm sample-marking squares
- Cell text gives 350 volumes, while its caption gives 351 timepoints
- The embryo examples of 14 hours, 1000 volumes and 60-second delay do not establish one reconciled duration; author the task timepoint manifest separately
- SI states 8 AO channels per card but also says AO0 through AO8; preserve the explicit mapping without inventing hardware
- A processed TIFF in Supplementary Data8 has not decoded successfully with the reader used. Raw A/B data were sampled historically; neither validation of the processed image nor source-file corruption is established
- Assembly diagrams are unscaled. Microscopy scale bars are not robot world coordinates

## Priorities for later static assets

`ASSET_REQUIREMENTS.json` lists 37 asset/sample classes and 7 newly authored observation-resource groups. Prioritize manipulable parts and states supporting the whole route rather than an attractive indivisible microscope shell:

1. Chambers, coverslips, O-rings, screws, tools and three observation streams
2. RAMM, F/Z/XY/CDZ, both objective/piezo assemblies, both scanners, three cameras and independent supports
3. Pluggable filter assemblies, spacer tubes, fibers/BNC, commercial launch and control ports
4. Bead/dye preparation, embryo models, mechanical-transfer tools and traceable cell-handling proxies
5. Newly drawn mode/parameter/image/registration interfaces and authored static diagnostic feedback
6. Traceable storage, archiving and closeout stations

Decompose each asset into operating surfaces, gripping surfaces, connection points, visible states and safety exclusion zones. Until geometry, robot adaptation and responses are validated, do not promote this to an implemented static scene, executable simulation, physical experiment or scientific reproduction. The directory defines interfaces for later work rather than replacing those validations.

## File index

- `FIRST_COMPLETE_ROUTE.json`: main-route goal, initial state, stage contracts, evaluator boundary and reference sequence
- `OPERATIONS.json`: 92 operation nodes with sources, pre/postconditions, evidence, recovery and unknowns
- `BRANCHES.json`: 18 family branches and 7 route templates
- `ASSET_REQUIREMENTS.json`: 37 asset/sample classes, manipulable decomposition and 7 new observation-resource groups
- `SOURCE_PARAMETER_REFERENCE.json`: source optical/timing examples for reference only
- `COVERAGE.json`: mapping of numbered steps/substeps and the previous 12 branches into the new family
- `agent_visible.json`: separate D-R01 goal/initial-state draft; required instance inputs remain null
- `RELEASE_BOUNDARY.json`: actor versus author/evaluator file boundary; no loader is implemented
- `DESIGN_GAPS.json`: unimplemented state invalidation, partial-completion routes, instance inputs and geometry requirements
- Historical `VALIDATION.json` and `AUTHORED_MANIFEST.json` are omitted to avoid reusing checks whose file bytes have changed
