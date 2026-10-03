# Acoustic wavefronts: whole-paper robot task design

## Scope and evidence

This original task family converts the full empirical and numerical scope of Xie et al. (2014), DOI [10.1038/ncomms6553](https://doi.org/10.1038/ncomms6553), into inspectable robot-operation contracts. The source basis is the complete five-page published-layout reprint on the corresponding author's Duke website and the complete five-page publisher supplement. The supplement includes Figures 1–6, Notes 1–2 and references. Source access is closed for task design; exact fabrication, numerical reproduction and historical reanalysis remain open because critical inputs and raw records were not supplied.

The task is not a chronological reconstruction of the researchers' actions. Its 69 operations are authored decomposition choices. A mobile human-like operator handles labeled stock, supports and assembles parts, carries arrays, mounts instruments, uses readable controls, inspects feedback, and commits records. A printer performs printing; a motorized stage moves the microphone; the source and DAQ emit and digitize pulses; analysis software computes fields and spectra. These device processes do not become robot hand motions. The task supplies contracts for those interfaces, not a working implementation.

The main article is all rights reserved and no separate CC license was identified for the SI. Only original descriptions, factual values, attribution and test code appear here. No source PDF, text extraction, figure, rendered publisher page, digitized curve or reconstructed raw dataset is included.

## Whole-paper branch map

Ten physical routes cover:

1. Fabrication and inspection of all six labyrinthine cell types
2. Two-layer assembly of the low- and high-gradient arrays
3. Parallel-plate guide, source, microphone, stage and DAQ preparation
4. Task-authored measurement-chain calibration and empty-guide qualification
5. Normal-incidence measurements without an array and with both gradient arrays
6. Low-gradient bandwidth comparison at 2800, 3000 and 3200 Hz
7. High-gradient incidence-angle sweep corresponding to the Figure 4a comparison
8. Radiation patterns at 5, 20 and 35 degrees
9. Near-interface field and spatial spectrum at 25 degrees
10. High-angle field map at 45 degrees for apparent negative refraction

Each source measurement route includes preparation dependencies, actual object movement, safe setup, raw acquisition, processing, disposition and terminal cleanup. Routes are sets of operation templates with scoped dependencies, not one mandatory serialized transcript. An episode can select a subset, but a single completed scan is never whole-paper completion. Whole-paper accounting also includes all eight nonmanual dispositions.

Numerical/theoretical leaves retain unit-cell retrieval, generalized refraction, lossless reflection, application of the source loss parameter, the main scattering comparison, corrugated-guide coupling, diffraction-order analysis, and the FEM comparison fields/spectra/radiation in main Figures 3b and 4a/b/c. Main Figure 2 maps and Figure 3a are measured. No extra physical corrugated-guide experiment is inferred.

## Parts, samples and fabrication

The source identifies ABS and fused-filament fabrication. SI Figure 1 depicts six spiral angles: 135, 180, 270, 450, 495 and 540 degrees. The outlines show 36 mm along the illustrated propagation direction and 25 mm across. It also gives a 150 mm array period and eight periods; the displayed transmission array has two layers. Eight times 150 mm implies a nominal 1.2 m span for the illustrated high-gradient array, which motivates a supported carrier. It does not establish the full mounting envelope or physical printed-part count.

These values do not define a printable solid. CAD, taper equations, wall/channel widths, out-of-plane fit, material grade, nozzle/layer/infill/support settings, thermal schedule, finishing and dimensional criteria remain null gates. The robot cannot manufacture exact source cells from a thumbnail outline. A prepared-component handoff is allowed only when explicitly declared, independently qualified and bound to the route's required identity/geometry scope; it is not evidence of historical fabrication.

The operator selects a labeled ABS lot and supported build carrier, transports them to the guarded printer, loads the qualified job and checks its geometry revision, stock, guard and ventilation. It starts the job once and monitors the autonomous cycle. A separate stopped-motion/cooldown/safe-release indication is required before opening and unloading. No common ABS temperature or assumed cooldown is substituted for a qualified process card.

Every unloaded part receives a unique entity ID tied to its lot, job and CAD revision. At inspection, the robot seats it on a supported datum and checks dimensions, fit, channel openness and wall condition. A dimensional disposition alone is not acceptance. The same cell/CAD revision must pass both dimensional and channel checks before entering assembly. Rejected parts go to a recorded quarantine dock; a replacement requires its own generation and predecessor record. Source-reported geometry does not provide an acceptance tolerance.

## Two-layer assembly and movement

At the indexed bench, the robot chooses the qualified low- or high-gradient recipe, lays out cell IDs by type/orientation, seats the support fixture, and places the first-layer cells one slot at a time. It verifies actual order and joins before placing the second layer from its own map. It then registers layers, inspects seams, secures the assembly in a supported carrier and checks the complete component graph. Only an accepted same-revision assembly receipt emits array_revision_qualified.

The source's approximately pi/6 adjacent-cell phase difference is not a full two-layer transmission table. Single-layer reflection and double-layer transmission must remain distinct. SI's high-gradient drawing does not establish the low-gradient construction recipe, layer registration/sealing details or interchangeable historical specimens.

Movement is explicit. The 14 transport routes connect stock, fabrication, inspection, assembly, calibration, guide, source/DAQ and archive docks. Before a move the operator verifies output-safe state, detached tethers, payload support, a qualified path and a clear destination. It carries or wheels the retained object, brakes, seats it on support, and rechecks the same IDs and condition before releasing. It never grasps thin acoustic walls or drags microphone leads. The inspection-to-assembly route supports inspected released arrays as well as individual accepted cells so reuse/rebuild is physically connected.

Routes have no invented coordinates, durations, grasp poses or load ratings. Robot reachability, collision envelopes, plate handling and long-span support remain engineering inputs. A source-informed task is not a demonstrated feasible trajectory.

## Apparatus and calibration

The source's guide plate separation is 50.8 mm. SI Figure 6 identifies 18 PUI AS07108PO-3-R loudspeakers, a Pyle PCA3 amplifier, a microphone with embedded preamplifier, NI PCI-6251 DAQ and a two-dimensional linear stage. It describes a broadband Gaussian pulse, spatial Gaussian amplitude and pointwise time acquisition. Full guide dimensions and terminations, source placement/weights/phases, probe model, sampling/trigger parameters and travel schedule are not recovered from those component names.

The operator supports and installs the plates and fixtures, verifies measured gap/datums, mounts the source on a qualified relative-incidence fixture, and connects labeled leads with output isolated. It seats the microphone, maps DAQ/reference channels, establishes strain relief, homes the stage and checks travel limits. Task-authored ambient sensors provide timestamped conditions for sound-speed and drift assessment. Their placement, cadence and uncertainty are required inputs.

Calibration is explicitly task-authored qualification around the reported apparatus. The paper does not establish a separate physical cell-by-cell phase calibration. The operator parks the stage, mutes the source, supports and disconnects the microphone through PROBE_RELEASE, then carries it to the calibration station. After identified reference checks and raw acquisition, the processing method can issue calibration_valid only when acceptance and sensor/channel/gain/time/geometry scope are satisfied. It then safely unloads, transports, remounts and reconnects the probe. Remounting triggers a scope check rather than blindly inheriting calibration.

Preparation routes hand over a verified current state. Their DISCONNECT, ARCHIVE and RESET operations are episode-terminal or explicit-release operations, not mandatory teardown before a dependent route. APPARATUS can therefore hand a prepared source/DAQ to QUALIFY_CHAIN; after calibration, SOURCE_WIRE and DAQ_WIRE verify current connections before acquisition. Cleanup still occurs at episode end or abort, and outstanding terminal work is recorded.

## Measurement conditions and scanning

The normal-incidence branch includes a genuinely empty array dock, the low-gradient specimen and the high-gradient specimen. Their labels are 0, 3.3 and 6.7 times 2pi rad/m at the 3000 Hz reference frequency. A zero-gradient simulation does not replace the empty physical reference. Nonzero-gradient records require actual sample and assembly-revision IDs; empty references require both fields to be null.

For each scheduled run the operator binds branch, specimen or empty state, condition, attempt, source program, grid and calibration/reference scope. It sets and locks relative incidence using a supplied mechanism, reads back the actual angle, and registers all coordinate transforms. The task does not assume the original apparatus rotated the array, rotated the source or steered electronically. Any of those would need qualification for a new implementation.

The main far-map caption gives source coordinate y=40 cm and an exit offset of 3.4 cm. These facts are not a complete scan grid. The near-interface route at 25 degrees requires its own origin, sampling, microphone-clearance and aliasing qualification; it cannot silently reuse the far map. Required coordinates, step size, velocity and settling thresholds remain supplied cards.

After checking current environment, waveform/gain/DAQ settings and scope-compatible reference, the operator arms bounded acquisition. The stage moves autonomously to the scheduled point, demonstrates the required settled position, and the source/DAQ emits and records the identified pulse. The raw trace includes actual position, angle, trigger, gain and clipping/dropout status. Quality checks classify it without editing the original bytes. Each attempt receives an immutable hash/receipt and the loop advances only through scheduled points and pulse repeats.

A scan can close as partial with every attempted trace retained, but FFT in the source-route path requires an accepted complete scheduled grid. Partial-field processing would be a separately labeled extension. A fault always permits MUTE, independently of scan completion. Retrying creates fresh attempt/record IDs and a predecessor link. It does not erase failures, change the result label or create a new independent specimen.

## Scientific processing and comparisons

The FFT contract preserves time-window, phase-reference, units, calibration and software lineage. Derived complex pressure remains available before display normalization. Beam-angle extraction uses a qualified method with uncertainty and can return ambiguity or no resolvable beam. Agreement with a source plot is never an acceptance predicate.

For the bandwidth branch, 2800/3000/3200 Hz views may be extracted from the same valid broadband scan. They share acquisition lineage and are not three independent experiments. The 3.3 gradient label identifies the specimen at 3000 Hz; it is not a constant-gradient assumption at every frequency. SI Figure 2 discusses approximately stable xi/k0 from the frequency-normalized phase response. Any prediction away from 3000 Hz therefore requires a qualified xi(f) model or response data. No source numeric angle/pattern tolerance is supplied.

For the Figure 3/4 routes, 3000 Hz is an explicitly task-authored reference-frequency assignment, inferred from the design/normal-incidence context. The plots, captions and inspected surrounding text do not directly establish the historical acquisition frequency. That value remains unknown; the source card must explicitly qualify the chosen frequency, and the task cannot claim exact historical frequency. Figure 2 and SI Figure 2 have explicit frequencies.

The oblique-sweep work order needs a nonempty angle schedule. The complete historical Figure 4a measurement schedule is plotted rather than tabulated and is not invented here. The explicitly reported 5, 20 and 35 degree pattern comparison, 25 degree near-field acquisition and 45 degree negative-refraction map remain separately identified conditions, not a universal five-angle sweep.

For Figure 4b-style comparison, measured display patterns were normalized using corresponding simulated maxima. The task keeps raw/calibrated amplitudes and records the identified model denominator separately. Such normalization cannot demonstrate absolute measured transmission, scattering or efficiency. If matching FEM output is missing, the comparison is blocked; no fabricated model array is supplied.

The near-field spatial transform records the along-surface coordinate, window, sampling and resolution. Its transverse wavenumber is compared with an ambient-based free-space value and the identified model. The source interprets the field as a driven localized surface response. It is not a freely propagating interface eigenmode. The 45 degree branch records signed geometry and apparent negative refraction; it does not establish a bulk negative material index.

## Numerical branch distinctions and source conflicts

All eight numerical/theoretical routes are specified and not run. Solver geometry, domain, material coefficients, mesh, boundaries, convergence and software revision are unresolved. The stated COMSOL and plane-wave radiation-boundary approach is not sufficient to reproduce source fields.

The generalized model contains the phase-gradient term; the diffraction extension adds nG*G. Source context distinguishes nG=0 and nG=-3 and critical-angle predictions near 13.7 and 31.6 degrees. Arcsin-domain failure is a nonpropagating model prediction, not a reason to clip an angle to a convenient value.

Main Figure 3c uses 20 and 10 degree numerical cases with scattered fractions 27.8% and 89.0%. SI Figure 4 labels its lossy illustration 25 degrees, while SI Note 1 also quotes 27.8%. These are preserved as distinct source-location/scenario identities. None is presented as a new measurement, and 20 and 25 degrees are not silently collapsed.

SI's loss index is 1-0.02i within the metasurface region and was selected against measured 10 degree transmission. This package applies it only as source context; it has not performed a fit. A new fit requires identified actual 10 degree data, an objective and a separate validation plan. Original fit traces are unavailable; newly acquired data would establish a new fit, not recover historical data.

The corrugated-guide branch is numerical-only: 20 degree incidence, 2.5 cm corrugation period and sound-hard boundaries. The source demonstration couples a driven mode to a structure supporting a propagating eigen-surface mode. It does not authorize an invented robot fabrication/acquisition route for a corrugated guide.

The author publications list has an apparent DOI typo; the linked paper, publisher and arXiv related DOI agree on ncomms6553. The published main/SI take precedence over the earlier arXiv version, which differs in broadband and driven-mode coverage.

## Repeats, identity, controls and failure handling

Work orders declare independently fabricated arrays, sessions, technical repeats, condition ordering, reuse and retry limits before acquisition. The initial empty baseline has record_role=baseline, null prior-reference fields, and a required current calibration/acquisition receipt. Its committed result can become a later reference. Specimen measurements require an existing compatible reference.

These counts are not supplied by the source and remain null in the reusable package. Cell types, layers, pixels, pulse repeats, frequencies and angles do not create independent specimen n.

Every report traces to physical cell IDs and assembly revision, current fixture/pose, source/DAQ program, calibration/reference scope, environment record and immutable raw hashes. Calibration and reference compatibility are reviewed scopes; a baseline does not need the same specimen because its empty state is the contrast, but instrument/frame/frequency conditions must fall within the qualified scope. Actual specimen state remains separately recorded. Replacing a cell, changing layer registration or rebuilding an array increments its assembly revision. Changed gain or probe mounting invalidates out-of-scope calibration and reference receipts.

Controls include source-supported empty/low/high normal incidence and frequency/angle contrasts, plus task-authored metrology, calibration, clipping, grid completeness, post-scan drift and post-run integrity checks. Their provenance is explicit. Checks do not smuggle in unreported tolerances or historical repeats.

Failure examples include wrong cell type/order, blocked channels, dimensional rejection, omitted second layer, changed gain, stale calibration, angle/readback mismatch, collision clearance, clipped pulses, missing grid points, cable tethering and failed safe release. The operator observes and records the fault, stops dependent outputs, supports/quarantines damaged objects, and obtains a qualified repair or reports a blocker. It does not repair the measurement by editing the condition label or excluding disagreeing outcomes.

## Completion, archive and evaluation limits

Before final teardown, all attempted raw data and setup changes are committed. The operator disables source output, verifies the stage stopped/parked, supports the array before unclamping, inspects it after removal, disconnects isolated leads without pulling cables, and transports retained parts to labeled archive bays. A no-acquisition preparation episode has an explicit empty acquisition allocation and still archives fabrication/inspection receipts; it is not a completed experiment.

Completion is per declared scope. Complete, partial, safe-abort and failed outcomes are distinct. Whole-paper accounting requires every physical and nonmanual family represented; stronger empirical completion requires all selected conditions and trusted preparation/cleanup evidence. Scientific disagreement is reported separately from procedural success.

The actor receives only goals, qualified runtime operating cards and current observations. The static allowlist contains only agent_visible.json; all source expectations, reference routes, authoring documents and evaluator checks are denied by default. No loader is implemented, so this boundary is a contract that a future integration must enforce.

The supplied Python code checks static structure, source/gate fidelity and synthetic receipt bookkeeping. Its test fixtures contain artificial IDs and hashes. They test rejection behavior, not physical observations. There is no authenticated hardware backend, live completion engine, acoustic solver, robot policy or certified scene. Passing these checks does not close the 15 unresolved execution gates.
