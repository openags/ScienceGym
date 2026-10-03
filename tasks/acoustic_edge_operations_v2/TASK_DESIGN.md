# Whole-paper acoustic edge-detection campaign

## Scope and evidence

The target is an auditable robot-task family derived from the complete experimental program in Molerón and Daraio (2015), DOI 10.1038/ncomms9037. The source reports passive airborne-acoustic edge imaging through a printed, five-resonator waveguide. This package covers shared fabrication and apparatus work, seven physical acquisition branches, their analyses and safe closure. The main’s six pages and all five supplementary pages have textual audit coverage. The main PDF is readable through retained lawful web-reader records but has no locally retained original-byte hash. Denied downloads were not retried.

The source’s dimensions and experiments are factual anchors. Robot grasps, carrier transport, interlocks, inspection, calibration gates, record contracts and causal sequencing are original task design. No source robot trajectory exists. The package does not claim that any proposed robot can perform these actions; no physical experiment, robot run or physics simulation has occurred.

## Campaign decomposition

Shared guide preparation starts with a work order and labelled stock, not a magically ready device. A complete qualified drawing must preserve five coupled resonators and the reported acoustic dimensions: narrow/wide square sides 7.5/22.5 mm and corresponding axial segment lengths 3/15 mm. Exterior walls, port details, material and printing settings are unknown. The robot loads stock/tray, reads back a bound print job, starts the enclosed machine, observes completion and safe release, unloads with supported grasps, performs qualified finishing and submits the guide to dimension/integrity inspection. Tool motion is performed by its controller; it is not credited as direct robot dexterity.

Each target has its own preparation route, material lot, complete drawing, qualified tooling and QC. The single edge and 32-mm plate are aluminium, and the rod is 10 mm wide, not specified as a 10-mm-diameter cylinder. The disc is 100-mm-diameter Plexiglas. The ETH object uses rigid thermoplastic; reported 15-mm widths and 10–15-mm spacings do not define the full contour or thickness. A photo is not an exact machining file. A future episode may supply inspected pre-existing targets, but that route must expose receipt, identity, handling and QC rather than inventing source manufacturing history.

The apparatus stage includes foam-panel handling, a vertical guide mount, on-axis source alignment, output absorber insertion, individual microphone installation, cable routing, qualified in-situ chain calibration using a transported standard, stage mounting/homing and final inspection. Reported apparatus anchors are 50-mm enclosure lining, a 22-mm Clarion SRE 212H speaker 280 mm before the inlet, and four 6.35-mm G.R.A.S. 40BD microphones at wall midpoints, flush with the interior, 20 mm past the final narrow section. Exact fixture geometry, absorber insertion and calibration recipe remain required inputs.

## Seven physical branches

1. `NO_OBJECT`: confirm an empty unobstructed inlet/source path and acquire a qualified frequency-response schedule
2. `HALF_APERTURE`: load an aluminium edge, align it approximately 1 mm from the input and verify half-aperture blockage, then acquire a matched frequency response
3. `SINGLE_EDGE_1D`: scan one aluminium plate edge at 7,740 Hz with 0.6-mm physical steps
4. `PLATE_32_1D`: separately load and scan the two edges of a 32-mm-wide aluminium plate
5. `ROD_10_1D`: separately load and scan the 10-mm-wide aluminium rod, retaining possible apparent-width bias
6. `DISC_2D`: scan the Plexiglas disc on a qualified 1.6-mm physical grid; the paper displays its upper half, so full-disc historical coverage is unknown
7. `ETH_2D`: separately prepare, load and scan the thermoplastic ETH target on the 1.6-mm physical grid

The full campaign requires all seven branches and the three control/comparison packages. The guide and calibrated rig can be reused when explicitly allocated and still valid; the paper does not establish exact historical specimen identities or reuse. The half-aperture and single-edge uses are not automatically one plate. Unknown technical-repeat counts cannot become zero, one, or a successful empty loop.

## Robot, instrument and transport contracts

`operations.json` defines reusable operations; it is not a mandatory single order. `dependencies.json` gives causal requirements plus branch-conditioned gates. Every repetition gets an occurrence key containing episode, branch, run, attempt, operation and iteration. The four microphone seats require four distinct installation occurrences. Each frequency or stage coordinate needs its own measured record. A current receipt cannot be borrowed from another guide, target, configuration, calibration or point.

Interstation movement uses supported, retained carriers with explicit origin, destination, detach, docking and identity evidence. A transfer is instantiated every time an item changes stations, even though the template appears once. Tethered rigs are not dragged. Robot handling includes support before clamp release, robust surface grasps, connector-body disconnection and protected sensor storage. Real masses, poses, collision paths and robot capabilities are unbound execution gates.

The robot requests stage coordinates through a controller. The Velmex mechanism performs stepping; position and settling readbacks precede pressure acquisition. An output-enable or scan-start receipt cannot stand in for raw data. Before approaching, unloading or reconfiguration, source-off and motion-stopped states must be observed. Dropped parts, clipping, reference loss, collision warnings, stale calibration and incomplete acquisition stop the affected branch, retain unsuccessful records and require qualified recovery. Recoveries create new attempts and version/QC changes where needed.

## Measurement and derivation

Every point retains four complex pressures with common reference, units, calibration, sensor serials and actual position/frequency. Magnitudes alone lose the phase information needed for modal separation. The reported formulas yield the plane-mode estimate from either opposing-pair sum divided by two, and two antisymmetric amplitudes from the respective opposing-pair differences divided by two. Both plane estimates are preserved. A discrepancy check is an authored quality measure with an unknown tolerance.

The paper’s Fig. 2c shows measured modal amplitudes, in arbitrary units, rather than an experimentally measured transmission matrix. Its sweep schedule, level, normalization and varying-frequency reference handling are not specified completely. The 7,740-Hz phase reference is an imaging anchor, not an all-frequency sweep recipe.

For imaging, physical object gap is reported as 1 mm. Absolute scan extents, origin, travel order, velocity, settling, averaging and tolerances remain supplied inputs. The 0.6-mm 1D and 1.6-mm 2D physical spacings must not be replaced by chart bounds. The finer 0.8-mm grid is linear display interpolation only. Missing or invalid raw points stay visible in a mask and cannot be manufactured by interpolation. Full and reduced display ranges are derived from the same raw data; the reported normalized (0.5,1) clipping is not a different acquisition.

Intensity definition, physical scaling, normalization and uncertainty must be explicit. A squared-amplitude proxy is not automatically calibrated acoustic power. Directional labels require a reconciled sensor/coordinate convention. Main prose and caption disagree around Fig. 4d; the package retains the conflict rather than silently rewriting attribution.

## Outcomes and numerical scope

Published peak counts, FWHM values and visual limitations are catalogued in `source_outcomes.json` and restricted to evaluator/author context. Three observed experimental resonances are distinct from five model resonances. A narrow peak for the 10-mm rod accompanies an oversized apparent object; it does not establish the same dimensional accuracy. The incomplete ETH lower-T-stem image and possible reflection artifacts preclude an expectation of perfect reconstructions.

The supplementary multimodal transmission route, trapped-eigenmode route and three COMSOL 1D comparisons are separate numerical coverage branches. None is a physical robot task or an implemented solver. The SI’s 13-element statement does not define the five-resonator model topology. Additional source notation issues concern zero-index modes, scattering block ordering/composition and axis-index conventions. Numerical implementation would require independent equation validation, complete topology, mesh/PML/convergence inputs and explicit authorization. The package does not repair equations or run models.

## Evaluation and readiness

The evaluator should score independent causal evidence, identity, complete declared coverage, truthful uncertainty and safe closure. It should accept equivalent valid routes and non-paper-trend measurements when procedure and records are sound. Literature-shaped plots without real records fail. `agent_visible.json` is a goal projection, not a route oracle. A future loader must enforce the actor allowlist; none is implemented here.

The Python suite validates static references and rejects synthetic malformed records, leakage, grid substitution, stale calibration, forged data classes, missing channels, incomplete schedules and unsafe transfer/release. Its fixture pressures are arbitrary invented values, not simulated sound. Self-reported dictionaries are not authenticated instrument receipts. Passing these tests proves neither a trusted runtime evaluator nor robot feasibility, calibration validity or scientific replication.

Completion at this release level means a source-bounded whole-paper design with explicit gaps and original tests. `STATUS.json` keeps exact replication, execution, assets, solver and trusted runtime readiness false. Parent review and exact-allowlist export are still required before any publication.

## Reviewed route alternatives and aborts

A manufactured target is released at its preparation station before carrier transfer to inspection. A supplied target follows receipt, carrier transfer and inspection without a fabricated machine process. Calibration is qualified in situ at the rig; no tethered rig transport or unrecorded microphone removal is implied. Calibration recipes are inputs, while actual standard readings and corrections are outputs. A blocked or failed setup can use ABORT_CLOSE, ARCHIVE and REPORT without inventing source-enable, measurement or normal teardown events. Unsafe closure remains explicitly unresolved.
