# Origami truss mechanical memory: paper-level long-horizon task family

Yasuda, Tachi, Lee and Yang, *Origami-based tunable truss structures for non-volatile mechanical memory operation*, Nature Communications 8, 962 (2017), [DOI 10.1038/s41467-017-00670-w](https://www.nature.com/articles/s41467-017-00670-w)

## Status, scope and evidence

This is a ScienceGym paper-level task-design draft, not an executable robot task or a report of a reproduced experiment. It covers preparation of modified triangulated cylindrical origami (TCO) trusses, comparison with a paper demonstrator, single-cell compression of three geometries, both bifurcation boundary conditions, instrumented and manual one-bit work, and both reported two-bit transitions. Ten selectable physical configurations and one whole-paper campaign share 55 reusable operation templates. The paper/model comparison and manual-motion details have a separately declared supplementary-movie evidence status.

The readable publisher main article and all 27 pages of the supplied Supplementary Information were read. SI Figures 2, 4, 6, 7, 9 and 10 were inspected as rendered pages. `source_access_audit.json` records retrieval and inspection separately. Full text, screenshots and movie bytes are excluded from the export. There is no need to acquire an inaccessible PDF when the corresponding text is readable lawfully.

Every reported practical family has a disposition. Mathematical modeling, parameter maps, proposed torque/frequency readout and conceptual planar/multi-bit extensions remain distinct nonmanual or proposed scope. In particular, SI Note 8's angular-perturbation curves are numerical, not extra measured physical trials.

No CAD, robot motion, physical simulation, fabrication job, calibration, trial count, raw experimental data or historical specimen lineage is invented. Missing execution inputs block the affected future action, not authoring of the rest of the task family. An assembled teaching object may be an explicitly supplied handoff; it cannot silently replace fabrication in a fabrication-required episode.

## Package structure and release boundary

- `branches.json` and `operations.json`: selectable routes, typed loops and reusable operations
- `dependencies.json`: causal requirements, loop scoping and actor/device handoffs
- `material_cards.json`, `station_contracts.json`, `lineage_contract.json`: physical inventory, station requirements and identity
- `control_packages.json`, `episode_input_contract.json`, `unknown_parameters.json`: controls and unresolved inputs
- `coverage_matrix.json`, `nonmanual_scope.json`, `provenance.json`, `source_outcomes.json`, `source_conflicts.json`: branch completeness and scientific grounding
- `agent_visible.json`, `evaluator_reference.json`, `mock_contract.json`, `RELEASE_BOUNDARY.json`: future public goal versus evaluator-only implementation/reference information
- `tests/`: static consistency and anti-shortcut checks, with no claim of physical validation

The actor sees one selected goal, actual initial inventory, supplied material/geometry/condition cards and public feedback. It does not receive hidden faults, expected scientific outcomes, future readings, evaluator assertions or a required reference action sequence. This is a design boundary, not an implemented runtime access-control system.

All fine hand motions, carriers, navigation, fastener tools, fixture-safe indications, calibration acceptance criteria, observation windows, cleanup and recovery are task-authored interfaces. They are not presented as the authors' exact hand movements.

## Long-horizon physical organization

The work connects stock, enclosed fabrication services, assembly, inspection, a horizontal compression station, a crank/memory station, records and archive. A robot would retrieve labeled material and parts, separate them in an indexed tray, load qualified fabrication jobs, receive and inspect parts, construct truss members and assemblies, transfer supported objects, configure actual boundary conditions, acquire attributable measurements, reconfigure between conditions, process records and leave samples and stations safe.

Each station change requires a supported carrier transfer, base movement and a verified destination dock. Hands retract before navigation. A specimen cannot be at two stations at once. Neither an object visibility toggle nor changing a label can create, transport or reconfigure a sample. Co-located observations during actuation/release do not require moving the specimen away from its fixture.

Fabrication is represented by enclosed, qualified station services. The robot performs loading, job binding, interlock/readback, output receipt and inspection; it does not improvise laser parameters or printer settings. Transparent inert training proxies, if later built, must retain these causal handling steps and label all output as mock.

## 1. Components, geometry and assembly

The source uses laser-cut acrylic polygons; printed polylactic-acid universal-joint parts; stainless-steel shafts of 3.18 mm diameter; and linear-spring truss members. The reported spring stiffness is 3.32 kN/m for monostable, bistable and zero-stiffness prototypes and 1.08 kN/m for the bifurcation prototype. These are source nominal values, not calibration certificates. Stock labels and measured or supplier qualification must distinguish them.

Four reported initial configurations are:

- Monostable: initial height 90 mm, initial twist 46 degrees
- Bistable: 150 mm, 40 degrees
- Zero-stiffness prototype: 140 mm, 92 degrees
- Bifurcation: 119 mm, 0 degrees

The stated original radius is R = 90 mm and the joint-separation correction angle is 9.7 degrees. The physical joint radius R-prime is a modified geometric quantity; it is not automatically the same as R. SI Eq. S11 defines their relation. The depicted polygon is pentagonal. A qualified geometry card must still supply all plate holes, separated joint positions, axial members, spring rest lengths, end attachments, part counts, clearances and tolerances. A schematic is not a manufacturing file.

The robot supports each polygon in an assembly jig, identifies the a/b member classes, seats shafts/springs and universal joints, joins only the specified endpoints and records every connection. It verifies the finished connectivity and initial height/twist against the supplied tolerances without forcing a twisted member into place. Numerical count 2n describes the model; a real bill of materials and its split joints remain required inputs.

SI Note 3 reports that applying grease improved agreement, particularly early in compression. Grease identity, quantity, application sites and before/after experimental design are absent. Record a supplied lubrication condition per joint/run and never pool dry and lubricated traces as one condition. A matched before/after lubrication study would be an authored extension, not a recovered paper branch.

A two-cell memory shares the middle polygon and uses opposite chiralities. A four-cell memory uses the sequence +46, -46, +46, -46 degrees from the left. Shared plates are single physical objects referenced by neighboring cell slots, not duplicate inventory entries. Combining or rebuilding assemblies creates a new assembly version with preserved component ancestry. The paper does not establish that its single-, two- and four-cell experiments reused the same physical parts.

## 2. Paper versus truss comparison

The SI description of Movie 1 reports a bistable paper model and a bistable truss model, with facet warping in the paper model. This is a physical demonstration family even though it is not a quantitative force-comparison experiment.

The route receives or constructs an identified paper object from a qualified crease/net card, prepares the matched truss reference and applies separately supplied bounded folding motions. Before manipulation, it verifies the camera/view and captures a baseline, then records continuously through folding and release. It records actual shape change, facet warping, contact limitations and released condition in both objects. Matching geometry must be explicitly supplied; the description's word 'bistable' is not enough to assign the numerical 150 mm/40 degree truss dimensions to the paper specimen. Paper stock, thickness, net, joining and manipulation details remain gaps unless an approved card supplies them.

No force/stiffness comparison, fatigue lifetime, cycle count or repeatability result may be inferred from the visual comparison. Sampled frames of official Movie 1 were inspected and corroborate hand-supported folding of the paper and truss objects. This is sampled-frame review, not a reconstruction of timing or calibrated motion. Movie inspection status remains separate from caption-supported facts.

## 3. Single-cell compression and low-stiffness comparison

Mount one accepted truss horizontally. The right polygon is fixed in translation and rotation; the left polygon is attached through a ball-bearing/shaft arrangement allowing translation and axial rotation while restricting bending. SI Note 3 names a BiSlider motor-driven linear stage (Velmex) and a LUX-B-50N-ID force sensor (Kyowa). Exact rig dimensions, calibration, force/displacement sampling, loading rate and motion limits are not reported.

The robot checks an empty fixture baseline, mounts and aligns the supported sample, verifies bearing freedom and force-sign convention, configures the supplied bounded compression program and clears the moving region. The device controls displacement and records force/displacement with timestamps and readback. Optional camera/angle sensing to verify boundary behavior is a task-authored observation channel, not a claimed original measured trace.

Three conditions preserve monostable, bistable and zero-stiffness geometries. Main Fig. 2 restricts experimental folding because members overlap: approximately 50% normalized compression for monostable/bistable and 15% for the highly twisted zero-stiffness object. These approximate observed ranges are not safety-authorized stroke commands. Stop at the qualified limit or detected impending contact, even if that prevents reproducing the plotted extent.

Compression is positive: u = h0 - h. Raw SI-unit force/displacement data are retained before deriving u/h0, F/(k h0) and integrated work normalized by k h0 squared. The reported energy curves were obtained by numerical integration of measured force/displacement. A declared baseline, integration rule, offset/sign handling and truncation policy are required; frictional work is not silently subtracted or asserted to be exact conservative elastic energy.

The low-stiffness comparison fits normalized force against normalized compression over 0.01 to 0.03, as reported in SI Figure 3/Note 3, avoiding the initial static-friction region. The three published slopes and ratios live only in `source_outcomes.json`. If a trace does not cover the full fit window, report the comparison incomplete. Model predictions cannot fill missing measured data.

The figures show mean curves and standard-deviation bands, but experimental trial and independent-specimen counts are not given. A future episode supplies its repetition plan. A repeated trace, repeated cycle and independent specimen are distinct identities. Standard deviation is unavailable with insufficient valid comparable repeats; it must not be fabricated from a single trace or the source plot. Unloading/reset is an authored safe closure unless explicitly included in the supplied acquisition plan; no complete cyclic hysteresis campaign is claimed by the paper.

## 4. Bifurcation with and without a rotational constraint

The 119 mm/0 degree prototype is tested in two physical fixtures/conditions. One uses a pair of stainless-steel guide shafts and linear bearings to constrain rotation while allowing axial movement. The other uses the free-rotation setup above. These are different verified boundary conditions, not two labels on one unchanged fixture.

At zero motion and a supported/de-energized state, the robot installs or removes the keyed guide assembly, checks seating/alignment and verifies the prescribed rotational freedom. Reconfiguration requires a new fixture configuration ID and fresh baseline. Separate matched specimens or explicit safe reuse are allowed when the episode states which; historical reuse is unknown.

The constrained condition measures the force path with suppressed rotation. Calling it an 'unstable branch' describes the unconstrained energy landscape; it does not mean the guide-supported apparatus is allowed to become mechanically unsafe. The free condition records the onset and direction of twisting and any force-curve change. The two possible twist signs are alternative physical outcomes. The actor must not secretly bias a sign or count two predicted stable branches as two observed trials. A supplied diagnostic criterion and measurement tolerance are required for a numerical bifurcation-point estimate.

## 5. One-bit memory: instrumented and manual routes

Join two 90 mm cells with +46/-46 degree initial twists. Fix the rightmost polygon and impose a total pair precompression of 45 mm while preserving leftmost rotational freedom. The source shows fixing the resulting distance with a bearing set screw. The task requires actual displacement/boundary readback and a qualified tightening procedure, not assumed retention after issuing a command. Stored axial precompression remains present during memory operation.

For the instrumented route, attach the crank, displacement-sensing target and force-sensor linkage in the supported safe state. SI Note 7 names an OFV-505 laser Doppler vibrometer (Polytec) to measure crank translation, converted to polygon rotation; the force sensor at the crank provides a torque calculation. Crank geometry and displacement-to-angle and force-to-torque transforms, signs, offsets and uncertainty are missing. A force sample times an invented constant arm length is not an acceptable torque trace.

After calibration and initial-state observation, command the supplied bounded angular sweep, retaining the underlying stage displacement and force readings as well as derived angle/torque. The SI Figure 7 measured curve demonstrates a forward transition from right cell folded ('0') to left cell folded ('1'). The main paper states switching can work in either direction; an exact measured reverse sweep is not established by that plot. A reverse attempt can be assigned as a clearly authored validation condition rather than asserted historical evidence.

For the separate manual-style operation route, a robot manipulates only qualified contact regions on the leftmost polygon/handle while the test station retains the axial constraint. It records the starting geometry, applied manipulation and released angular state. Sampled frames of official Movie 5 show labeled Bit=1 and Bit=0 during manual interaction, corroborating a qualitative reverse operation. Exact hand trajectories, duration and forces are not recovered. A robot's bounded grip/contact card is task-authored.

Non-volatility means the bit is retained without a continuing external torque. It does not mean the pair is unprecompressed or unsupported. For a future retention observation, leave the pair's axial distance fixed and remove external actuation torque. The instrumented route uses a qualified decoupler; the manual route releases the grip and verifies any powered linkage is absent or already released. Observe in place for a declared interval. A locked motor/crank holding the target angle cannot establish torque-free retention. If a safe torque-disengagement interface or duration is unavailable, report a retention-verification gap rather than claim a lifetime or non-volatile success.

## 6. Two-bit memory and the preparation/control handoff

Assemble four 90 mm cells with twists +46, -46, +46, -46 degrees. The first pair is the first bit and the second pair the second bit. Fix the rightmost polygon in translation and rotation. Apply pair precompressions of 50 mm and 47.5 mm respectively, and retain each specified pair distance throughout operation. These intentionally unequal settings are a coupled-system condition; using 45 mm from the one-bit setup would change the experiment.

The main paper describes individual angle readout with two non-contact laser Doppler vibrometers; SI Note 9 emphasizes crank/linear-stage control of phi1 and vibrometer readout of phi3. The instrument contract must declare actual channels and conversions instead of treating commanded phi1 as measured ground truth. Pair bits are determined by relative folding configurations and both polygon angles. The sign of phi1 alone is not a universal first-bit classifier because phi1 also changes during second-pair preparation.

The task has two mandatory selected routes, each with separate initialization, preparation/control epochs and raw records:

1. `TWO_BIT_00_TO_11`: verify '00', engage only the first-bit input, apply the monotonic rising segment of a trapezoidal waveform and observe both bits. The text reports phi1 moving from approximately -62 to +62 degrees, and the intermediate '10' followed by '11'. The second bit receives no direct excitation during this operation epoch. Do not infer a pulse duration from a movie playback clock.
2. `TWO_BIT_01_TO_10`: first establish '00' through the supplied safe reset; release the first-bit angular input, directly drive the second bit to prepare '01', and observe both angles. During preparation phi1 is unconstrained, so it can co-rotate without changing the first pair's relative bit state. Stop and disengage the preparation actuator, verify '01', then bind first-bit control. Apply an increasing-then-decreasing trapezoidal segment, beginning around phi1 = 0 degrees and lasting symbolic T/2. Observe the reported intermediate '11' and final '10'. Exact T, ramp/hold times, endpoint tolerances and sampled command program remain unknown.

Preparation is not an uncontrolled shortcut: the actuator target, free/held constraints and timestamps must show precisely when the second bit was directly driven. During the coupled test epoch, a second-bit drive would invalidate the claimed indirect response. Conversely, leaving the first actuator locked during input preparation changes the stated experiment.

The published first route ends at '11', whereas the second demonstration is described as starting from '00'. No safe return trajectory from the earlier final state is supplied. A campaign must insert a qualified reset or choose an independently initialized assembly and record that decision. It cannot continue directly from '11' while labeling it '00'.

Each route ends with torque-off verification when the supplied rig supports it, observation over the supplied window, and retention/reporting of any mismatch. Full reversible truth-table behavior, clock rate, endurance, long-term retention, noise immunity and experimentally implemented controlled-NOT logic are not claimed merely from these two demonstrations.

## Controls, lineage and failure handling

The core controls are verified geometry and spring class; actual unloaded/mounted baselines; declared joint/lubrication condition; free versus constrained rotation; matched comparison windows; pair precompression readback; active-actuator and free-input verification; initial/intermediate/final observations; and torque-on versus torque-off distinction. Added blank/zero/calibration checks are task-authored quality controls, not historical claims.

Specimen, component, assembly version, mount, condition, run, attempt and acquisition records remain separate. Every repair, guide change, lubrication change, chirality change and remount affects the appropriate lineage and condition signature. Failed or interrupted traces are preserved chronologically. Replacement means a new specimen or component ID; it does not overwrite the failed object. Repetition loops require positive supplied counts and cannot succeed by running zero iterations.

Recoverable faults include wrong spring stock, swapped cell chirality, mis-seated joints, guide interference, bearing friction, loose distance locks, sensor sign/zero errors, optical dropout, wrong actuator target, incomplete reset and transport obstruction. The response is stop, retain the current state and raw evidence, support/de-energize through the qualified safe-state procedure, inspect public feedback and resume only after verified repair and a fresh attempt. Do not push overlapping trusses, tighten against uncontrolled spring load or reach into a moving fixture. Damage is quarantined.

At completion, stop motion, retain the sample in support, disable optical emission as specified by the qualified laser station, restore the declared safe preload state with a controlled release sequence, disconnect only after safe readback, unload to its carrier, archive labels and records, return tools and unused stock, segregate damaged components and supplied lubricant waste, and inspect/reset stations. If safe unloading is unavailable, isolate the station and request intervention. Leaving a preloaded assembly unsupported is not cleanup.

## Evaluation and completion

Independent environment evidence must establish object location, component/connection graph, actual fixture constraints, measured initial geometry, stage settings/readback, channel mapping, acquisition receipts, calibration identities, condition signatures, actuator epochs and immutable raw records. Narration or invocation of an operation name cannot establish success.

Scientific outcomes and procedural validity are separate. Honest valid measurements that differ from source reference can pass the procedural task. Forcing expected curves, hiding friction, replacing observations with model output or changing bit labels to match the paper fails. Ambiguous state readout remains indeterminate; a source angle is not a universal threshold.

Completion states are `complete`, `partial_with_valid_blocker`, `safe_abort` and `failed`. A complete campaign requires each selected required physical condition to have valid attributable observations plus safe closure. Missing source inputs produce an explicit partial blocker, not a fictitious completed experiment. Static checks only establish internal consistency, not robot reachability, physical behavior, station safety or reproduction.
