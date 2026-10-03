# Prismatic metamaterials: paper-level long-horizon task family

Paper: Iniguez-Rabago, Li and Overvelde (2019), *Exploring multistability in prismatic metamaterials through local actuation*, [DOI 10.1038/s41467-019-13319-7](https://www.nature.com/articles/s41467-019-13319-7)

## Status and scope

This is a reviewable ScienceGym task-design draft. It contains 49 reusable operation templates, seven hands-on source families and 12 selectable task configurations, including a whole-paper campaign. It specifies long-horizon human-like mobile-robot work, measurements, controls, lineage, failure handling and evaluation boundaries. It does not implement or run a robot, physical simulation, printer, laser cutter, test machine, pneumatic source or scientific solver. There are no invented CAD files, calibrated grasps, source loading settings, author measurements or specimen counts.

The complete recovered publisher article HTML and primary 15-page SI were re-read. An independent source audit inspected main Figures 1–5 and SI Figures 1–9, recording 27 findings and 60 exact locators. Cached source hashes were checked. The previously identity-blocked main PDF was not requested or retried. Supplementary movies, original CAD, raw data and author code were not inspected. The pneumatic branch consequently remains a text-reported demonstration.

“Paper-level coverage” means every reported practical family has a task-design disposition and numerical/outlook sections are inventoried separately. It does not mean every physical recipe, transition trajectory or possible state has been recovered. Missing execution-critical inputs are explicit gates; authoring the symbolic task family is complete even while future execution is blocked.

## How to read the package

- `branches.json` selects families, geometries, conditions and typed loops
- `operations.json` contains human-like manipulation templates and recoveries; `dependencies.json` defines partial orders and data-binding rules
- `agent_visible.json` contains goal templates; `RELEASE_BOUNDARY.json` restricts release to one selected goal and its public inputs
- `lineage_contract.json` separates samples, parts, versions, states, attempts and cycles
- `station_contracts.json` and `asset_needs.json` describe unbuilt station/interface requirements
- `control_packages.json`, `mock_contract.json` and `evaluator_reference.json` specify controls, future inert-record contracts and independent evaluation
- `coverage_matrix.json` and `nonmanual_scope.json` show physical versus numerical/outlook scope
- `provenance.json`, `material_cards.json`, `source_outcomes.json`, `source_conflicts.json` and `unknown_parameters.json` retain scientific facts and limits
- `independent_source_audit/` records independently checked source claims and locators; `tests/` records static contract tests

All fine robot actions, carriers, docks, fixtures, safety feedback, observation windows, data conventions and recovery contracts are task-authored interfaces. Source support establishes macro operations and stated material/condition values, not the authors’ exact hand movements.

## Configurations and specimen semantics

The 12 selections are three cardboard geometries; PLA/Mylar cyclic compression; truncated-tetrahedron reach/release; cube hinge comparison; finite-array thickness comparison; finite-array boundary/long-period observations; two SI6 geometry comparisons; two-pouch demonstration; and the combined practical campaign.

A configuration is a task choice, not another paper or independent experiment. Seven source families do not establish seven historical specimens. A target label identifies a configuration to attempt, a cycle is a repeated measurement, a slot identifies an array child, and a specimen ID identifies a physical object. None can substitute for another.

The public work order must supply sample allocation and reuse policy. Reuse retains identity, assembly version, prior damage and a safe reset record. Replacement produces a new ID. Hinge replacement on the same body creates a new assembly version with old and new hinge identities; a separate comparison specimen has its own ID. The paper explicitly reports a second, thicker-sheet array, but most other historical specimen/reuse counts are unknown. The design does not invent them.

## Mobile workflow and ordinary manual work

A typical episode links stock storage, enclosed fabrication proxies, assembly, inspection, a test station, records and archive. The robot reads labels, fetches packaging and empty carriers, separates pieces into indexed mat pockets, supports thin parts while aligning them, closes attachments, checks seating, transports supported objects, operates controls with readback, records observations, unloads safely and resets stations.

Every physical station change requires an actual supported carrier transfer, mobile-base route and verified dock. Hands retract before base navigation; tethers are disconnected only under the station’s safe-state contract. One sample cannot occupy two stations. There is no “generate finished sample,” visibility toggle, teleportation or label-change substitute for handling.

Fabrication services may later be inert proxies, but their input loading, work-order selection, guard checks, output receipt, part inspection and joining remain real task events. Exact print/cut patterns and station mechanics are supplied qualified inputs. If they are absent, the robot reports a source-gap blocker rather than improvising a fabrication recipe.

Observation during release occurs in place. `WS_INSPECTION` in that stage denotes a co-located camera/inspection role; the robot must not transport or regrasp a relaxing sample and then claim an undisturbed release observation.

## 1. Cardboard demonstrators

Fig. 1 supplies three distinct templates: truncated tetrahedron, truncated cube and cuboctahedron. The reported square faces are 24 mm, cardboard thickness 0.4 mm, with double-sided-tape hinges. Those dimensions belong to the cardboard examples only.

The robot retrieves labeled cardboard and tape, loads a supplied cut pattern into the enclosed service, receives and inspects indexed pieces, places them in a topology-specific jig, aligns adjoining faces, applies tape while supporting the edges and verifies each joint. A complete joint manifest precedes an assembled-sample claim. It then performs only the bounded manipulations supplied by the target/contact card, records loaded and released shape observations, and archives the specimen.

The source does not provide a complete net, joint gap, tape grade, safe grasp path, force envelope or target transition history. Target count is supplied by the episode; the source pictures are not an exhaustive state list. These missing inputs stay unresolved.

## 2. PLA/Mylar cyclic compression

The named compression geometry is a cuboctahedron. Each face uses two printed PLA pieces, each 0.5 mm thick, with a laser-cut 50 micrometre Mylar sheet clamped between them. The source names Ultimaker 3 and Instron 5965L9510. It specifies displacement magnitude `sqrt(2) L` and averages the last five cycles with standard deviation. It does not supply absolute physical L, physical loading speed, load cell, full conditioning history or a complete fixture/acquisition recipe.

The robot loads geometry-specific print and cut jobs, receives numbered components, inspects them, supports each lower face half, aligns the hinge sheet, closes the matching half and records the complete joint graph. At compression it checks the unloaded fixture separately, aligns the stated opposing faces, secures the sample and records a mounted baseline.

The physical program is configured only after all supplied settings have units and readback. The 24 mm cardboard dimension cannot fill L. The model’s 1000 loading increments, stiffness ratios and strain constraints cannot fill physical rate, sampling, cycle count or safety limits.

Each cycle contains independently attributable loading and unloading legs, timestamps, force/displacement units and signs, sample/version, fixture/calibration and condition signature. Failures remain in chronological history. A changed mount, specimen version or program starts a new run. The robot stops motion before supporting and releasing the sample.

The summary uses the actual final five cycles of the declared completed run. It requires five complete, valid, same-condition loading/unloading pairs. An invalid final cycle makes the summary incomplete; selecting five earlier good cycles would conceal failure. A new explicitly declared continuation/run may later supply a valid window, but the previous history remains. The interpolation/alignment and population-versus-sample SD convention require a declared processing card. Five cycles are not five independent specimens.

## 3. Truncated-tetrahedron reachability and relaxation

This branch preserves all 17 Fig. 4 target labels. They are numerically identified targets associated with up to three simultaneous actuated hinges, not 17 fabricated specimens or a full search over all states. The physical prototype is described as using the previously reported PLA/Mylar fabrication method.

For each scheduled attempt, the robot records starting state and material/version, seats the supported sample, binds the target/contact card, performs bounded local manipulation, records the loaded shape, removes actuation and captures the post-release state over a declared window. Reaching a pose under load is different from retaining it. A finger-held or clamped pose cannot count as unloaded stability.

Valid outcomes include retained after release, relaxed to another configuration, returned to baseline, limit-constrained before reaching target, damaged and indeterminate. A safe reset and integrity check precede reuse; missing reset geometry blocks later attempts rather than erasing the previous state. Source expected outcomes are evaluator-only context and never target rewards.

The source reports seven direct matches, five release-relaxation cases and five stretch-limited cases. Its body text says i–v relax to vii/xi; independently inspected Fig. 4b arrows show i/ii/iii/v to xiii and iv to vii. Both assertions remain recorded. The design does not force a disputed destination.

## 4. Cube hinge-material comparison

The task compares the same eight model target labels under Mylar and 0.5 mm elastomeric hinge conditions. Source spelling is “silicon rubber”; product identity, modulus/hardness, attachment details and stretch limits are not supplied. The design does not silently normalize those unknowns into a material recipe.

The episode explicitly chooses separate matched specimens or supported hinge replacement on the same body. Replacement requires physical removal/archive of the old hinges, new hinge identities, connection records, a new assembly version and renewed baseline inspection. Changing a text label is insufficient. Any damaged or altered face creates a documented matching limitation.

Both material conditions retain every target attempt, release observation and failure. The source’s unreached stretch-limited and non-adjacent-face-crossing cases are represented. Crossing is an obstruction to record and stop at, never permission to push physical faces through each other. A source-reported six-state result is contextual evidence, not a scoring quota.

## 5. Finite arrays and thickness controls

The physical array is a 2 × 2 × 2 cuboctahedron assembly. A complete array contains eight distinct unit identities with slot coordinates and intercell joint records. These are children of one parent assembly, not eight independent experimental replicates. The source reports a 50 micrometre Mylar array and a second array with 125 micrometre sheets.

Array face material, full connectivity, absolute dimensions and boundary supports remain source gaps. `ARRAY_PREP` requires qualified unit-preparation receipts from an explicitly supplied route, or a declared outside-scope preassembled teaching-unit handoff. Neither means the paper supplied a complete recipe. Without those inputs, assembly is blocked.

The robot lays out units, supports neighbors in a jig, connects and checks each intercell joint, transports the array on multi-point support and attempts supplied target conditions. It records changed cell slots and support/boundary conditions. The thickness comparison uses separate identified assemblies and matched declared target/start/observation conditions; unresolved matching factors are reported.

Bulk-compatible, edge/corner-localized and longer-than-one-cell patterns remain distinct spatial observations. They cannot be collapsed into a periodic single-cell-model result. A separate boundary/long-period branch may reuse the thin array only through explicit retained lineage and reset. “No additional retained state” in the thicker array’s tested context does not mean no initial equilibrium or universal impossibility.

## 6. SI6 selected configuration comparisons

SI Fig. 6 displays 11 numbered selected model/physical configuration pairs for the truncated cube and 15 for the rhombicuboctahedron. Arabic labels 1–11 and 1–15 are used here, separately from Fig. 4 Roman labels. These are display inventories, not exhaustive unique-state totals, successful-attempt counts or independent specimen counts.

The robot binds each target-view card, captures actual loaded/released configurations and reports matched, ambiguous, unreachable and missing observations. Material, geometry and safe transition inputs require explicit qualification; the photos do not authorize inheriting PLA/Mylar or cardboard recipes. The episode can declare a source-gap preassembled teaching object, with its actual material and outside-scope fabrication receipt. That changes the task’s preparation scope, not the source facts.

## 7. Text-reported pneumatic demonstration

The Discussion reports a truncated tetrahedron, two pneumatic pouches and four stable states, citing Movie 6. No movie, pouch geometry, attachment map, pressure, flow, timing, reset path or state-command mapping was inspected. Two pouches plus four states does not establish a four-row Boolean truth table.

The design requires a qualified specimen/preparation receipt, two identified pouch components, attachment and channel diagrams, and a bounded program card. The robot supports the sample while attaching components, connects labeled channels with source off, checks strain relief and supplied feedback, reads back one program, clears moving regions, actuates, records the loaded state, vents both channels and records load-off/post-release observations. Both residual-pressure-safe indications are required before disconnecting.

Missing construction or program inputs block the affected stage. The task is not allowed to auto-complete four states from the textual claim. Its final report clearly distinguishes episode observations from the source’s limited report.

## Controls, repetitions and recovery

Each branch records precondition baselines and paired states appropriate to its question. Compression requires both path directions; tetrahedron requires loaded versus released; cube requires actual material conditions; arrays require thickness identities and spatial classes; SI6 requires target-view versus observed-view; pneumatic work requires command/readback versus load-off state.

Repetition counts other than the source five-cycle summary are supplied task inputs. Failed attempts cannot be deleted, relabeled or converted to zero-valued readings. A retry gets a fresh attempt ID and links the failed predecessor. A replacement gets new specimen identity. Condition changes create new signatures. Missing inputs block loops instead of becoming empty successful loops.

Recoverable faults include wrong stock, mis-seated parts, interrupted cycles, ambiguous pictures, swapped pouch channels and obstructed transport. Recovery stops output, supports the object, checks public feedback and resumes only after verified repair/reset. Irreversible damage is quarantined. If safe release is unavailable, the station is isolated and intervention requested; the robot does not reach into a hazardous fixture.

## Independent evaluation and completion

The actor receives one selected goal, actual initial inventory, public material/geometry/condition cards and current feedback. It does not receive reference operation sequences, scientific outcome tables, hidden faults, test assertions or future readings. The file boundary is specified; a runtime loader is not implemented.

The evaluator uses independent environment-side object locations, constraints, joins, port graphs, instrument readbacks, acquisition receipts and immutable raw records. Action names and agent narration alone do not establish success. Alternative valid orders and grasps are accepted when they satisfy causal and safety conditions. Faults must be observable or discoverable through available public checks.

Future inert fixtures, if built, must label their records as mock. Matching the paper does not compensate for missing manipulation or raw records. Complete honest records that differ from the paper can pass procedural evaluation. Outcomes are `complete`, `partial_with_valid_blocker`, `safe_abort` or `failed`, with scientific agreement reported separately. A correct source-gap stop is useful behavior but is not a completed experiment.

The static tests inspect package consistency and synthetic-record integrity only. They do not establish robot reachability, material behavior, physical safety or scientific reproduction.
