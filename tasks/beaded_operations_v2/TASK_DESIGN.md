# Beaded metamaterials: whole-paper long-horizon task design

Paper: Dreier, Jones, Plummer, Kosmrlj and Brun (2025), *Beaded metamaterials*, Nature Communications 16, 7899. [DOI 10.1038/s41467-025-61809-8](https://www.nature.com/articles/s41467-025-61809-8). [Supplementary information](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-025-61809-8/MediaObjects/41467_2025_61809_MOESM1_ESM.pdf).

## Deliverable and evidence boundary

This is an authored, reviewable task-design package for long-horizon mobile-robot work on inert bead/thread networks. It is not an executed experiment, robot controller, calibrated physical model, precise CAD reconstruction or reproduction certificate. The design covers the paper's practical families from stock receipt and weaving through loading, measurement, controls, image analysis, service handoffs and archiving. Numerical interpretation and demonstrations are distinguished from quantitative experiments.

The publisher main article and seven-page SI were lawfully readable in tool output. The main article's body, figure captions and Methods and all SI captions informed this design. A subsequent direct main-article download redirected to an identity-provider endpoint and was denied. That route was stopped without a retry or alternative access attempt. There is no local byte-complete publisher packet or verified current source hash. Main Tables 1 and 2 were not recovered as readable tables; raw supplementary data, movies, author CAD and software were not inspected. Old authored atlas material was used only as context, never as current source-byte verification. The separate source audit reports its own actual inspection scope.

Every detailed grasp, carrier, dock, interlock, force limit, reset, fixture interface, event schema and recovery below is task-authored. The paper supports macro procedures and specific reported values; it does not specify the authors' exact hand trajectories. Unknown execution-critical inputs are explicit gates. They block the affected future action, not creation of this honest design.

## Package navigation

The structured package contains 13 organizing families, 21 leaf configurations plus one campaign dispatcher, 70 operation templates and 35 unresolved input gates. A focused independent task-design review passed with no blocking findings; 42 author checks and 25 separate reviewer checks concern static contracts only.

- `branches.json` and `routes.json`: selectable experimental families and typed, condition-bound routes
- `operations.json` and `dependencies.json`: reusable physical and analysis operations, gates and causal order
- `provenance.json`: compact evidence catalog with source sections, figures and SI page locators
- `material_cards.json`, `source_conflicts.json`, `unknown_parameters.json`: reported values, contradictions and unresolved inputs
- `lineage_contract.json`, `control_packages.json`, `station_contracts.json`: object history, valid comparisons and actor/device boundaries
- `episode_input_contract.json`, `agent_visible.json`, `RELEASE_BOUNDARY.json`: public work-order inputs and actor/evaluator separation
- `coverage_matrix.json`, `nonmanual_scope.json`: complete disposition of practical, numerical and illustrative content
- `evaluator_reference.json`, `mock_contract.json`, `tests/`: independent checks and limits of static verification

A family or configuration is not a historical specimen. Cycle counts, rings, layers, pictured states and repeated tests must not be converted into independent specimen counts.

## Long-horizon embodied workflow

The campaign links records, labeled stock, a supported weaving bench, optional enclosed part-preparation service, mechanical test stations, imaging, a controlled electrical station and archive. The actor retrieves actual stock, checks labels and geometry, separates bead sets, identifies both thread ends, routes thread through indexed bead holes, closes each weave loop, checks the route, moves supported assemblies, installs fixtures, applies pretension, configures instruments with readback, acquires immutable records, unloads safely and resets the work area.

All station changes require carrier loading, a physical transport event and verified arrival. There is no teleportation, hidden replacement, preassembled-object appearance or label-only material change. Part-preparation transfers bind the actual input-stock and output-part IDs. Assembly collects bill-of-materials batches from their recorded locations, including prepared beads already at the weaving bench. The analysis station is a data-service role and never changes a specimen's physical location or custody. A beaded object remains supported while thread ends are transferred; loose tails and suspended masses are secured before movement. Hands are clear before motion or electrical energization. Source terms such as 'manually tensioned' remain source-reported macro operations with unknown numerical tension, not a license to invent a setpoint.

The assembly work order supplies a qualified topology graph: unique bead IDs, ordered thread passages and crossing directions, hole axes, shared beads, loop identities, termination points and the route of each free end. The actor reads the next passage, stabilizes the bead, aligns the end with the specified hole, feeds/pulls through without scraping or kinking beyond a supplied handling envelope, seats the bead and records verification. A jammed passage is inspected and backed out under support. Missing route geometry is a valid blocker. A source picture is not a complete executable weave pattern.

Received preassembled teaching objects are permitted only as an explicitly selected preparation scope. They require actual object, material, topology and outside-scope preparation receipts. They do not count as actor-performed weaving or complete paper fabrication.

## 1. Angle-weave swatches and tensioned-shell demonstrations

Main Fig. 1a illustrates angle-weave swatches with loop sizes n = 3 through 7. The design supports assembling supplied swatch patterns, recording planar versus nonplanar shape after an authorized tensioning step, releasing or fixing the ends according to the work order and documenting the actual shape. Overall swatch dimensions, bead counts, exact threading and preparation settings are not recovered.

Fig. 1b includes a half-dodecahedral shell made from 17 mm acrylic beads and steel rope and a separate 10 mm acrylic-bead/nitinol tomography example. The described shell model has 20 beads and five-bead building blocks. These are distinct material/size examples; the 17 mm and 10 mm cases cannot be merged into one specimen. The actor supports the untensioned shell, transfers the two free ends to the specified tensioning fixture, records out-of-plane formation, and fixes the ends only under the selected termination contract.

The adult-load photograph is an illustrative load-bearing demonstration, not a supplied safe human-loading protocol. No person is used as a test load in this task. A bounded mechanical surrogate may be supplied as a separately authored test with explicit fixture and force limits; it must be labeled as such. The paper does not supply a dancer mass, loading history or quantitative acceptance test.

## 2. Constant-pretension shell compression and motion tracking

Main Fig. 2 and Methods 'Dodecahedral shell' report two pulleys, a transparent acrylic stage, a 45-degree mirror, masses of 200–800 g attached to both thread ends, a printed PLA plate and an Instron 5940. Each tension trial has three compression cycles. Masses are per end; two equal masses do not imply a doubled thread tension. The exact tested mass list, load-cell configuration, compression speed, stroke, stopping criteria and acquisition settings are unresolved.

Nitinol is reported as 0.25 mm diameter. The nylon diameter conflicts between 1 mm in Results and 0.50 mm in the Fig. 2 caption. Neither is silently selected. A supplied, measured material card must resolve the actual episode's diameter while retaining the discrepancy. A task using that card is a declared implementation, not proof of the authors' diameter.

The actor installs and checks the clean fixture, places the supported shell, routes each tail through its pulley, attaches identified masses with their travel restrained, checks free travel and clears the test volume. Pretension mode, both mass IDs, actual measured/derived tension convention and initial shell geometry are recorded. Under-load tail relocation is not allowed. Any change in thread, end constraint, indenter, roughness, bead size or mounting creates a new condition signature.

Front and mirror-mediated bottom views are captured during force/displacement acquisition. Synchronization is anchored to the onset of plate motion. The source tracks one cycle; the selected cycle ID must be declared and retained, not chosen afterward to look most convincing. The actor verifies view calibration, bead identity and occlusion status before accepting centers. An analysis service may track points, but it must return trajectories, manual corrections, uncertainty and source frame references.

The reported dilation calculation uses the fitted circle through lower-ring centers, an average bead diameter measured across the holes of 9.2 mm, 10 lower-ring beads and five surrounding loops. That 9.2 mm value is not the bore diameter or a universal bead size. Three-dimensional coordinates combine front and bottom views, including the mean of their two x estimates. The source constructs altitudinal angles from selected bead-center vectors and computes a projected in-plane force. All raw coordinates and the coordinate convention are preserved. Singular or nearly singular angle projections are flagged instead of producing infinities or fabricated values.

Loading and return legs are separate records. The published motion plots omit the return path, but the underlying task retains it. Summaries may calculate extrema, hysteresis and fitted regimes only after the fitting windows, smoothing and cycle aggregation rules are declared. A desired superjamming result is not a completion requirement.

## 3. Shell control matrix and clamped-end loading

SI Fig. 2 (PDF page 3) reports distinct comparisons. These become separate, explicitly matched packages rather than a fabricated full factorial study:

- Plate versus 17 mm diameter columnar indenter on 10 mm frosted acrylic shells, with nitinol and nylon; reported pretension range 2.0–7.8 N
- Smooth versus frosted 10 mm acrylic beads with a plate indenter and both thread materials; reported range 2.0–7.8 N
- Bead-size comparison using smooth acetal spheres, nitinol and manually drilled holes intended to keep hole geometry consistent; reported range 2.0–9.8 N. Exact size list and hole geometry remain unresolved
- Manually pretensioned, clamped ends on 10 mm frosted acrylic shells with nitinol and nylon, loaded until failure in the source. Numerical initial pretension and a safe operational failure/abort definition are missing

An indenter exchange requires stopped motion, supported sample, physical tool removal/installation, identification and renewed alignment. Roughness and bead-size changes require actual bead changes and independent or versioned specimen histories. Drilling is an optional enclosed preparation-service handoff requiring qualified bead and bore drawings; no drill parameters or CAD are invented. A new thread cannot be substituted by relabeling an old one. Every route resolves required prepared-part roles before assembly. For drilled bead lots, custom fixtures and CT platforms, the robot either loads, receives and inspects a qualified preparation job or physically receives a qualified supplied part. Supplied preparation closes availability but does not earn robot-fabrication credit. Fixture parts are transported, placed, joined and checked before use.

The clamped branch cannot be treated as another hanging-mass condition or assigned infinite tension. It records imposed end constraints and measured initial state. A qualified endpoint and containment plan must be supplied before loading; an uncontrolled destructive test is not enabled by the source phrase 'until failure'. Damage terminates reuse unless a new specimen or explicitly qualified repair is introduced.

## 4. Fixed-ring friction and thread tensile characterization

The friction experiment fixes the beads while the thread slides. Main Fig. 3a–b, Methods and SI Fig. 1c describe n = 3, 4, 5 and 6 rings held between printed PLA pieces with hemispherical grooves. One end carries 50–500 g masses in 50 g increments through a pulley; the other reaches the tester through another pulley. The reported pull speed is 30 mm/s. That speed belongs to this experiment only and must not be copied into shell or dilation tests.

The actor verifies fixed bead positions and a unobstructed thread path, records mass and both-end conventions, performs each authorized pull, retains the full tension/displacement trace, safely unloads and inspects before another attempt. Replicate count, pull distance, plateau-selection window and pulley corrections are not supplied. The Results describes a tension difference, while the capstan expression and figure notation require careful interpretation of T, T0 and T*. Raw measured tension, applied-end tension and their difference are all stored. No friction coefficient is calculated until an explicit processing convention is bound.

Separate axial tests characterize nitinol and nylon at clamp spacings 10, 25, 50 and 100 mm, with three trials at each spacing. Gauge spacing is a condition; a trial is not evidence of a new specimen. Unique trial IDs are allocated across actual coupon identities so the source-comparison total is three per material and spacing, rather than three automatically assigned to every coupon. The source fits an elastic slope and uses E = s L0 / A, with fitted added stretching lengths of 13 mm per clamp for nitinol and 9 mm per clamp for nylon. These are the authors' fit parameters, not transferable hardware calibration. The actual area, gauge definition, fit window, rate and clamp behavior must be supplied or measured. The unresolved nylon diameter prevents an unqualified modulus calculation.

## 5. Free-ring dilation and ordered chain dilation

A free ring differs causally from the fixed friction ring: its beads must be able to move. Main Fig. 3c uses n = 3, 4 and 5, a spherical-tipped indenter with bead-matched radius, three cycles per pretension and a reported 2.0–9.8 N range. The source does not provide the full tension list or dilation speed. The actor verifies ring freedom, centers the correct tip, checks the geometry-specific contact reference and records complete loading/return cycles. Model-aligned displacement zero is a declared postprocessing choice, not a replacement for raw instrument zero.

The chain consists of 15 right-angle-weave rings of n = 4 with neighboring rings sharing one bead. Two thread ends are worked in alternating fashion through one continuous path. Shared beads have one physical identity referenced by two loop memberships. A topology-derived bead count is labeled as derived and is not asserted as a source specimen count. Source ordering is consequential: for each declared chain condition, dilate from the free-end ring i = 1 toward i = 15, with three cycles per ring. The same chain accumulates loading history and slack changes. The sequence cannot be randomized without becoming a new, explicitly authored variant.

The actor unloads and verifies safe indenter clearance before moving to the next ring. It preserves end orientation, ring IDs, pretension, prior cycles, slip marks and any topology change. An interrupted or damaging cycle remains in history. A repeat uses a new attempt ID; resetting or replacing the chain changes its state or identity and cannot be hidden. SI Fig. 5 (page 6) adds in-plane projected-force analysis at 2.0 N for both materials. The eight-cell tomography chain in SI Fig. 4 is a separate preparation from the 15-cell mechanical chain.

## 6. Elastomeric column compression/extension

Methods specifies a PRAW-4 square column with 11 layers of 12 mm acrylic beads, elastomeric thread, 92 mm rest length, manual tensioning and a knot. A custom PETG/acrylic/hardware fixture grips the end beads rather than the thread. The reported program includes three cycles with 35 mm extension and 23 mm compression at 30 mm/min. The exact motion order, dwell, starting reference and clamp dimensions remain inputs.

The actor assembles and checks each layer using the supplied route, records the knot and initial length, mounts both end-bead sets without pinching the thread, measures the neutral reference and runs the explicitly selected extension/compression order. It records both legs and unloading, bead contact/separation and integrity. A three-state tomography comparison uses jammed, neutral and stretched states but does not establish three independent specimens. Sample overlap with mechanical tests is unknown.

## 7. Electrically actuated SMA beam and bending controls

Methods specifies a PRAW-3 triangular beam, 31 layers, 6 mm acrylic beads, shape-memory nitinol, 125 mm rest length and metal crimps after manual tensioning. Three-point bending was performed at 30 mm/min, with nine off-state and twelve on-state cycles in the reported totals. The source describes 6 V selected as current reached a manufacturer-recommended 660 mA. These are reported conditions for the source wire, not safe electrical limits for an unspecified replacement.

The task requires the actual wire identity, measured resistance, supported thermal/current limits, electrical isolation, cooled-state criterion, bending span/tip/stroke and a state sequence. An authorized controlled electrical service verifies the program and provides readbacks; the actor mounts the beam, attaches identified leads with power off, confirms strain relief and clearance, requests one qualified state, records voltage/current and thermal-state evidence alongside force/displacement, then returns to power-off and confirmed cool before touching or disconnecting. Missing thermal or electrical qualification blocks energization, not the rest of the paper design.

Off and on tests remain separate conditions. Unique cycle IDs are assigned to actual specimen/state blocks; their campaign totals are nine off and twelve on. These totals are not multiplied by the number of allocated beams, and they do not imply paired trials or independent specimens. State order and thermal reset history are preserved. Fitted stiffness comparison requires declared linear windows; measured actuation or stiffness gains may differ from the source.

## 8. Catenary dome, cone inversion and egg-crate reconfiguration

The dome uses a software-generated catenary surface, equal-radius sphere packing, a triangular mesh connected to six neighbors and bead locations at face centers. Methods identifies 20 mm acrylic beads and waxed filamentous nylon, whereas Fig. 4d calls the cord waxed polyester. The exact surface, pattern and thread identity are unresolved. The design accepts a qualified external geometry file with its own provenance; it does not infer precise CAD from the photo. Under supported manual-like manipulation the actor records local deformation, releases contact, leaves the assembly under gravity and records the actual resting conformation. The number of stable shapes is not known or exhaustively tested.

For isolated cones, Results mentions central defects n = 3, 4 and 5, while SI Fig. 6 (page 7) supplies the explicit n = 4 measured example: nylon, manually pretensioned/tied ends, point loading of the central defect until inversion, and a moving average over four cycles. The n = 3 and n = 5 mentions are inventoried as source-mentioned variants without an equally recovered quantitative recipe. They are not silently assigned four-cycle data. Tip geometry, load direction/reset, extent of patch, support, rate and numerical pretension remain missing.

The egg-crate surface in Fig. 4e combines n = 4, 6 and 8 loops and small acrylic beads labeled R = 6 mm. That radius is not the SMA beam's 6 mm diameter. The caption and main text reverse the gray/white up/down mapping; the task records physical orientation relative to a measured surface normal, not inferred color names. The pictured i–iv states are examples, not four specimens or proof that all 2^m assignments are stable. The actor manipulates only supplied cone addresses, records neighboring responses, removes actuation and observes retention under declared supports and gravity. Failed or coupled changes remain valid observations.

## 9. Tomography handoffs and state lineage

The source names a Zeiss Xradia Versa 520 and Dragonfly visualization. SI Fig. 1e (page 2) gives material-specific preparation: nitinol ends manually tensioned and crimped; nylon manually tensioned, tied and glued against slip; thread passes through a polymeric platform and assemblies are glued to it after tensioning. This is more specific than the main Methods' general knot statement, so the selected CT preparation follows a resolved material-specific work order and preserves the difference. Platform fabrication may use PLA, PETG or acrylic, with exact assignment/dimensions and adhesive unspecified.

Separate selections cover shell, rings n = 3–5 for both thread types, an eight-cell nylon chain and the column's jammed/neutral/stretched states. An imaging state is not a new specimen. Gluing, crimping, cropping or changing a loaded fixture creates a preparation/state record. No automatic mechanical-to-CT specimen identity is assumed.

The actor prepares and labels the mounted object, hands it to a qualified enclosed imaging service, receives identity- and state-linked raw volume/scan receipts, and checks sample return. The device controls radiation generation, guarded scanning and interlocks; no autonomous access to an exposed X-ray source is part of this draft. Voxel size, energy, projections, exposure, reconstruction and in-situ force fixture settings remain qualified service inputs. The source uses cropped orthographic renders for nitinol and the column, and approximately 1 mm mean slabs for nylon ring/chain views. A slab thickness is not a voxel size.

## Controls, repetitions and causal bookkeeping

Whole-paper coverage is an inventory and route family, not a claim that every possible combination was tested. Each comparison package names matched factors, required changed factors, repetition semantics and unresolved confounders. Source ranges remain ranges until a public episode schedule is provided. Exact source counts are enforced only in their own scope: shell/ring/chain and column cycles, axial trials, SMA state totals and SI6 moving-average cycles. Unreported replicate counts remain null, never zero or an invented default.

Every object keeps component lots, thread path, termination mode and mounting version; every run keeps condition signature, instrument/calibration, time base, raw acquisition and complete failed-attempt history. Changing thread or glued mounting changes assembly version and may require a new specimen. Reusing a tested assembly retains accumulated slip, plasticity, damage and previous state. Independent replicates require distinct preparation identities, not repeated scans, rings or cycles.

Recovery begins with stopped actuation, supported object and observable safe state. Thread snags, crossed ends, moving pulleys, dropped beads, obstructed views, saturation, clip slip, thermal drift and mislabeled cells require diagnosis from public observations. Damaged components are quarantined. A valid blocker is reported specifically, with unfinished scope and evidence; it is never encoded as a successful empty loop.

## Analysis, evaluation and completion

The actor receives one selected goal, actual inventory, qualified public cards, safety/acceptance criteria and live feedback. It does not receive reference operation sequences, hidden fault states, expected result curves or future sensor values. The evaluator may use independent object locations, thread-passage graph, clamp and pulley state, fixture identifiers, instrument readbacks and immutable records. Narrative claims or operation IDs are insufficient proof.

Theoretical capstan, ring force-balance and shell projection calculations are analysis branches. Their idealizing assumptions and source ambiguities remain explicit. A new experiment's friction coefficient or modulus is estimated from its own measured data under a declared model; the source coefficients and outcomes are evaluator-only comparison context, not injected measurements or reward targets. A source inconsistency involving the shell projection's alpha convention is retained rather than resolved by silently changing the equation.

Acceptable terminal statuses are complete, partial_with_valid_blocker, safe_abort and failed. Scientific agreement is reported separately from procedural integrity. Correct honest records can pass procedure checks even if the paper's trend does not appear. A source-gap stop is useful behavior but not a completed physical experiment. Static validation here checks JSON references, typed loops, count semantics, export boundaries and mock-record logic; it cannot establish robot reachability, electrical/physical safety, device operability or material behavior.
