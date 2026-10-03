# Thermo-responsive granular clamp: whole-paper robot task design

## Status and scientific scope

This is an original, source-grounded task-design draft for a human-like mobile laboratory robot. It covers the practical experiment families in [Han et al., Nature Communications 16, 2303 (2025)](https://www.nature.com/articles/s41467-025-57475-5), DOI 10.1038/s41467-025-57475-5, together with the material and measurement checks in its [supplement](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-025-57475-5/MediaObjects/41467_2025_57475_MOESM1_ESM.pdf). It is not a runnable robot policy, equipment procedure, physical feasibility assessment or claim of experimental reproduction.

The robot must create and handle actual specimens. Its responsibility includes retrieving stock, cutting rods, establishing traceable reference shapes, preparing PMMA components and printed nylon sticks, measuring and packing charges, using tools, moving supported objects between stations, mounting instruments, configuring and starting qualified jobs, reading actual status, recovering specimens, preserving raw measurements and cleaning up. A provided finished clamp does not satisfy the preparation obligations of a fabrication-inclusive episode.

The scientific setting is a granular clamp whose shape-memory rods respond to temperature. Thirteen selectable configurations account for the physical investigation:

1. Temperature and rod-fraction pull-out comparisons
2. Repeated pull-out, cooling and reinsertion on a declared packing
3. Rod aspect-ratio comparisons
4. Container-size comparisons
5. Glass/steel ball additions at fixed rod fraction
6. Rod/ball composition changes at fixed total fraction
7. Lot-linked DSC transition measurements
8. Single-rod bending and thermal-recovery measurements
9. Inclined-plane contact-friction measurements
10. XCT comparisons across selected physical states
11. XCT registration across declared thermal cycles
12. Contained load holding and cooling-triggered release
13. Extended load holding followed by contained release

These are experiment-family templates, not an invented full factorial matrix. Each episode receives a finite condition, specimen and acquisition manifest. Exact historical allocation, physical replicate counts and several source grids remain unresolved. `coverage_matrix.json` accounts for every main figure, SI Sections S1–S3, Figs. S1–S16, Table S1 and the two movie descriptions. Numerical model explanations are mapped separately rather than relabeled as robot measurements.

## A complete robot episode

For a selected pull-out campaign, the robot begins at the work-order desk. It reads the assigned conditions and control arms, reserves distinct object and packing identifiers, checks installed assets and transport paths, and records unresolved inputs. It does not silently choose missing machine speeds, sample counts, heating ramps or geometry tolerances.

At stock storage it identifies the actual wire, PMMA, PA12 feedstock, fasteners and any ball lots. At the guarded cutting station it retains the wire, uses a qualified cutter/fixture, recovers each rod or batch, separates debris, and checks dimensions and cut-end condition. Reference shape and lot processing history are verified. If the stock needs a shape-setting or recovery step, the robot mounts the rods in a qualified fixture, selects the independently supplied process, starts its device, reads back actual completion and retrieves the cooled material. No shape-setting temperature or dwell is inferred from the alloy's reported phase-transition temperatures.

For the clamp, the robot loads PMMA stock into qualified fabrication tooling, selects the assigned versioned drawing, checks retention and guards, requests the fabrication job, recovers the components after motion stops, and performs qualified finishing and inspection. For the stick, it loads qualified PA12 feedstock, selects the branch-specific print job, starts it, retrieves the safe build, removes supports or finishes it as specified, and measures the result. The fabrication machines own their internal motion; the robot owns all physical preparation and job interfaces. Missing fabrication methods and drawings remain explicit gates, not invisible pre-prepared inputs.

At preparation it cleans working surfaces using the resolved material-compatible method. It measures/counts the rod charge and optional balls, links them to the actual cavity and volume-fraction convention, packs with the qualified initialization method, fits the lid, uses the specified fastening interface, and checks containment. It supports the closed clamp and inserts the identified stick to the resolved depth at the qualified low-temperature state. Insertion-induced changes are recorded without claiming internal rod shapes that have not been observed.

For a hot arm it moves the supported assembly into the oven station, docks it, closes the guard, reads back the selected program and starts it. The oven performs heating autonomously. The robot reads actual thermal history and verifies the qualified condition, then retrieves the assembly with a heat-rated carrier. Elapsed time and controller setpoint are insufficient proof of sample temperature.

At the tensile station it mounts the container on the fixed lower interface and the stick on the moving upper interface. It checks alignment, retention, heating-pad placement, thermal observation, calibration and the selected acquisition program. Once guarded and ready, it starts the job, monitors actual readbacks and preserves the force, displacement, time and temperature records. The test machine performs controlled motion and sensing. The robot waits for stop, supports the descendants, releases fixtures, recovers the stick and clamp, and records the changed state.

After a qualified cool-down, a cyclic episode requires actual reinsertion of the same stick into the same declared packing before the next hot pull. A fresh packing receives a new identity. Lost particles, reopening or rearrangement are recorded; a cycle counter cannot disguise repacking. Every trial retains its attempt and validity record, including faults.

The robot submits acquired files to a declared analysis service, reviews quality and missingness, and obtains derived results with raw parents. It then returns retained stock, separates rejects/waste, cleans tools and fixtures, and reconciles a supported final location and disposition for every physical descendant. Matching the paper's trend or force is not a completion requirement. If a phase map is selected, the source-specific force classification uses the recorded single-rod mass and declared gravity convention; this derived label is not a certified load rating. Normalized XCT quantities retain the actual reference length/diameter and coordinate convention, and initial-state versus previous-cycle displacement references remain distinct.

## Interfaces, transport and actor boundaries

`operations.json` supplies an actor, manipulated objects/tools, source and target station, robot actions, device actions, interfaces, preconditions, completion state and evidence for each operation. `station_contracts.json` gives the station inventory and boundaries. These are authored requirements; the source did not report this robot workflow.

Every station change must instantiate a MOVE receipt: identify the object and its state at an observed origin support; select a qualified grasp/tool/carrier; release it from the source; maintain support/containment during transit; dock/retain it at the destination; observe final placement and update its unique current location. A route edge is not teleportation. Hot transit additionally retains actual thermal history and qualified handling/release limits. No gait, pose, grasp force, bolt torque, payload capability or room layout is invented.

Regulated heat, printing/cutting motion, crosshead movement, calorimeter scanning, X-ray acquisition and long-duration logging are device-owned processes. Robot setup/start/readback/unloading remain physical task obligations. Autonomous dwell is not continuous robot labor. This draft has performed none of those processes.

## Branch-specific preparation and measurement

### Contact and material checks

DSC uses a physically prepared, lot-linked subsample and reference pan. The robot prepares, weighs, loads, configures, starts, reads and unloads the actual pans. The reported transition values are scientific reference facts, not a scan program or future observations. Pan selection, sample mass, thermal schedule and extraction method remain qualified inputs.

The cantilever branch uses a separately identified single rod. The robot mounts a defined anchor length, applies and removes the qualified load, records residual bending, and obtains registered shape observations across measured thermal states. It does not borrow an unspecified load or span from the numerical schematic. The initial shape-setting question and the later mechanical bending/recovery experiment are different operations.

For friction, the robot builds a coupon with fixed rods or balls using a qualified adhesive and contact geometry, verifies its attachment and exposed contact surfaces, places an identified SMA-rod or stick slider, and equips a catch. It sets and verifies temperature, requests qualified inclination, detects first slip under the declared criterion, records angle and temperature, and recovers the slider. Rolling, coupon failure and ambiguous motion do not silently become static sliding coefficients. Adhesive choice, cure, tilt rate, temperature grid and repeat count are gates.

### Geometry and mixtures

Fixture and stick dimensions belong to condition identities. The aspect-ratio campaign has a distinct fixture definition from baseline thermal/packing/ball tests. The container-size campaign requires a complete drawing for every selected variant. The source's generic outside diameter cannot physically surround its largest listed inside diameter; `source_conflicts.json` preserves both facts and blocks the affected fabrication until resolved.

Mixture campaigns distinguish fixed rod fraction with added filler from fixed total fraction with changing rod/filler composition. Ball material and lot, rod count/mass, ball count/mass, actual cavity, inserted-stick treatment and fraction denominator are separate records. No guessed free-volume formula or nominal particle count is asserted to reproduce the source packing fraction. Glass/steel and rod-only controls remain explicit.

### XCT and cycle identity

The robot preserves the closed packing, transports and mounts it in a qualified thermal scan carrier, checks the shield/interlocks, reads the actual scan settings and sample temperature, starts the job, obtains actual records, and unloads only after exposure-off and access release. The source's 320 kV instrument description is not a complete scan prescription or proof of actual voltage.

Derived tip distance, inclination, coordinates, coordination and cycle displacement require calibrated segmentation, contact rules, registration and uncertainty. Rod identities are matched with evidence; table row order is not identity. Missing/merged rods stay visible. Scanned rods are not independent packing replicates.

XCT thermal cycling and cyclic mechanical pull-out are separate templates. Their complete joint scan/pull sequence is not supplied by the inspected text, so this design does not assume that every XCT cycle includes a pull-out. Cold and hot scans are separate acquired states, not relabeled copies. A future finite manifest must resolve this sequence.

### Demonstration and extended holding

The load demonstration uses a qualified anchor, hook/load, guard, catch/support and observation system. The robot attaches the load while supported, verifies containment and temperature, and withdraws support only under the qualified procedure. The fixture carries the load. The robot/device maintain custody and records; they restore support or stop under declared fault criteria. Cooling-triggered release occurs into the enclosed catch, followed by safe recovery.

The extended branch has a real long-duration device/logging dependency. The SI describes holding for longer than fifteen hours, but the inspected material does not provide the exact load, complete movie observations or a finite acceptance specification. Those must be resolved. A short mock timer is not actual duration evidence. Repeated pull-out cycles are not equivalent to continuous loaded holding, and peak pull-out force is not a certified hanging-load rating.

## Evidence, controls and unknowns

`source_parameters.json` contains cited numerical facts. `unknown_parameters.json` contains unresolved methods and values. Robot handling, guards, evidence contracts and recoveries are labeled authored translation. `source_outcomes.json` is reviewer-only historical comparison, never an observation file. An input-resolution receipt preserves its provider, units, evidence, applicability and qualification; an authored resolution does not become a source fact.

The source temperature rule for pull-out requires a maximum target deviation strictly below 2 °C. Records at or above that limit, or with insufficient thermal evidence, cannot pass the corresponding validity check. This draft adds no unsupported tolerance for other assays. Approximately fifteen minutes of heating is not proof of equilibrium. The word “slow” does not supply a pull speed. Five simulated packing configurations are not five physical repeats.

Controls cover thermal contrasts, geometry/packing consistency, apparatus calibration, same-packing cycles, mixtures, calorimetry references, matched bending states, contact pairs, XCT registration and load support. The manifest separates independent specimens/packings, repeated measurements, cycles, rod counts and derived comparisons. Missing source n remains unresolved. Invalid attempts remain in denominators or are excluded only by a declared, visible analysis rule.

`lineage_contract.json` links stocks, cut batches, fabrication jobs, fixtures, charges, packings, sticks, cycles, raw acquisitions and dispositions. DSC and bonded friction coupons are separate descendants. They cannot silently return to ordinary free-particle stock. All results have actual raw parents and versioned processing. Retries append evidence rather than overwrite it.

## Whole-paper and source-access boundary

The main article and validated eighteen-page SI were read. Source figures were not digitized. Movies S1/S2 and the Source Data workbook were not inspected; only movie descriptions were available. The public DEM repository link was identified, but code, license, complete solver inputs and reproducibility were not audited. `source_access_audit.json` states these limits. They remain dependencies for exact historical replication, without erasing the paper's broad physical task families.

The DEM model, simulated force chains/contact distributions, numerical parameter sweeps, theory sketches and literature parameter provenance are classified in `nonmanual_scope.json`. No simulation output becomes a physical observation. Proposed future particle shapes are not added as already reported experiments.

## Design checks and export boundary

Run `python -B tests/run_validation.py` from this directory for finite structural and synthetic adversarial checks. Independent review has its own report and exact scope. These checks do not validate mechanics, safe working limits, instrument authenticity, thermal/radiation qualification, physical feasibility or scientific reproduction. No runtime loader or evaluator implementation is claimed.

Only authored files in `EXPORT_ALLOWLIST.json` are eligible for parent-controlled publication. No publisher PDF, extracted text, figure pixels, movie, workbook or source-code copy is included. The article identifies [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/); this is independent task prose and factual attribution, not an adapted article or permission to redistribute source assets. The repository LICENSE is preserved. No remote write, viewer work, CAD generation, heating or equipment operation was performed.
