# ScienceGym

**Long-horizon robot research tasks derived from full scientific papers.**

ScienceGym studies how to translate a paper's reported experimental program into tasks for an embodied research agent: preparing materials, moving samples between instruments, assembling apparatus, running controls and repeated measurements, preserving records, recovering from failures, and leaving the laboratory in a defined final state.

The unit of design is a **paper-level task family**. Its branches, dependencies, sample histories and measurement obligations determine what the agent must accomplish. An episode can cover a complete route or a control package; paper-level completion requires the full declared scope.

**Current release: eight reviewed task-design drafts; zero validated runnable whole-paper tasks.** The repository currently supports reading and inspecting static specifications. Task execution is future work.

## Embodied laboratory task demonstration

The R01 example binds a mobile humanoid, laboratory stations, manipulated objects and sample states to **26 reference-operation keyframes**. It shows stock collection, fabrication handoff, assembly, metrology, two authored loading cycles, archiving and cleanup. [Open the offline visual replay guide](viewer/embodied_r01/README.md).

[![Robot, equipment and objects during stock collection](viewer/embodied_r01/frames/01_FAB01.jpg)](viewer/embodied_r01/README.md)

[Assembly view](viewer/embodied_r01/frames/09_ASM04.jpg) · [Loading and specimen inspection](viewer/embodied_r01/frames/19_LOAD.jpg) · [Archive view](viewer/embodied_r01/frames/24_ARCHIVE.jpg).

This is an authored visual storyboard, not a physics simulation or robot execution. It covers the R01 branch, not all branches of the paper. Repeated unit placements are summarized in layer-completion views, not individual grasp trajectories. Source-supported stages, authored poses and unknowns remain distinguished.

### Thermoelectric module route

The PAIRED_TWO demonstration maps **66 reference-operation occurrences to 45 illustrated keyframes**: separate P/N preparation, cross-device processing, four individually tracked leg placements, module assembly, four measurement-boundary chapters, archiving and cleanup. [Open the offline visual replay guide](viewer/embodied_thermoelectric/README.md).

[![Robot assembling the third individually tracked thermoelectric leg](viewer/embodied_thermoelectric/frames/29_PLACE_P2.jpg)](viewer/embodied_thermoelectric/README.md)

[Whole route contact sheet](viewer/embodied_thermoelectric/keyframes_contact_sheet.jpg) · [Laboratory overview](viewer/embodied_thermoelectric/overview.jpg) · [Coverage and limitations](viewer/embodied_thermoelectric/loop_coverage.json).

These are authored static/kinematic states. Millimetre-scale leg geometry is explicitly enlarged 20× for inspection; physical grasp feasibility is not established. Repeated current/acquisition loops remain grouped with unknown grid values and counts. No scientific measurements or controller execution are supplied. This demonstration covers one selected route, not every branch of the paper.

## Explore the paper-level tasks

[Open the offline explorer guide](viewer/task_explorer_v1/README.md) to inspect branches, robot actions, objects, sample states, source evidence and recovery. Download the folder and open index.html locally; GitHub shows HTML as code rather than running it.

Seven visual route maps readable directly on GitHub: [Chiral](viewer/task_explorer_v1/docs/chiral.md) · [Deconwolf](viewer/task_explorer_v1/docs/microscopy.md) · [Fibres](viewer/task_explorer_v1/docs/fibre.md) · [Thermoelectric](viewer/task_explorer_v1/docs/thermoelectric.md) · [diSPIM](viewer/task_explorer_v1/docs/dispim.md) · [Acoustics](viewer/task_explorer_v1/docs/acoustic.md) · [Perovskite](viewer/task_explorer_v1/docs/perovskite.md).

These are task-design references, not executed robot trajectories. Nested loops, repeated operations and unresolved conditions remain explicit. [Verification and limitations](viewer/task_explorer_v1/VERIFICATION.md).

## Visual task routes

The first visual route shows every listed R01 operation and the complete chiral branch index. Dashed connectors represent the authored reference order, not an executed trajectory or a recovered author chronology. The seven-paper offline interactive explorer is available below.

[![Chiral metamaterials: complete R01 task route and branch index](docs/visualizations/chiral_r01.svg)](docs/visualizations/chiral_r01.svg)

## Why paper-level tasks?

Scientific work connects many individually simple actions across long intervals and multiple devices. A useful task must preserve those connections:

- **Whole reported routes:** preparation and fabrication, intermediate processing, characterization, measurement, archiving and cleanup
- **Branches and dependencies:** alternative material families, shared prerequisites and independent experiments, without inventing a single global chronology
- **Sample lineage:** batches, parent–child specimens, destructive siblings, reused samples and irreversible treatment histories
- **Cross-device manipulation:** carrying, loading, aligning, mounting, connecting and unloading the right object at each station
- **Controls and repetition:** paired conditions, repeated observations and same-specimen cycles kept distinct from independent samples
- **Recovery:** failed attempts remain in the record; damage, contamination or an invalid measurement cannot be erased by relabeling an object

ScienceGym's task layer specifies these obligations. [Hooke](https://github.com/RobotEurekaLab/Hooke) is the separate companion project for supporting laboratory scenes and assets. Asset requirements and bindings appear in the task packages, but a scene or addressable object alone does not establish an executable task.

## Task design

Each task family connects source evidence to operational requirements. Package schemas are still evolving; their filenames are not yet a uniform runtime API.

1. **Evidence and coverage.** Main text, Methods, figures and available supplementary materials are mapped to reported experimental branches. Theory, simulation and literature comparisons receive explicit dispositions rather than being turned into invented physical experiments.
2. **Goals and initial state.** The agent receives a selected goal, available objects, known constraints and observable interfaces. Preparation routes begin with appropriate starting resources, not silently completed specimens.
3. **Operations and dependencies.** Reference operations define required inputs, object-state transitions, device interactions and dependencies. Authored handling steps bridge gaps in the paper and are labeled separately from source facts.
4. **Lineage and records.** Measurements retain their specimen, condition, instrument and attempt identities. A repeated measurement is not automatically a new sample, and a split sample does not lose its parent history.
5. **Evaluation and recovery.** Evaluator-only reference routes, hidden states and acceptance rules remain separate from agent-facing goals. The intended evaluator accepts equivalent valid routes and checks recorded events and object states, rather than trusting an agent's declaration of success.

For a concrete example, inspect Deconwolf's [goal](tasks/microscopy_operations_v2/agentgoal.json), [initial state](tasks/microscopy_operations_v2/initialstate.json), [reference operations](tasks/microscopy_operations_v2/operation_sequences.json), [recovery design](tasks/microscopy_operations_v2/recovery_design.json) and [evaluator reference](tasks/microscopy_operations_v2/evaluator_reference.json). A future agent-facing loader must not expose the evaluator materials as task instructions.

### Scientific observations and task success

The designs allow explicitly labeled preset or mock scientific observations. This lets future task implementations study long-horizon operation without requiring a simulator to predict a paper's scientific result.

Reported literature values, authored mock outputs and unknown or invalid observations remain distinct. Matching a published number is not sufficient evidence of successful manipulation or acquisition. Conversely, a correctly obtained weak or negative result need not be an operational failure. Current preset contracts are specifications; they do not constitute an implemented scientific backend or a complete set of image fixtures.

## Included task families

The seven packages have undergone design review and static consistency checks. These are draft representations of reported scope, not human expert certification or completed robotic reproductions.

| Task family | Reported program represented | Entry point |
| --- | --- | --- |
| Chiral metamaterials | Material preparation and fabrication, assembly, geometry and boundary controls, loading cycles, observation and archiving | [Task design](tasks/chiral_operations_v2/TASK_DESIGN.md) |
| Deconwolf microscopy | Six preparation/imaging branches and seven source-data comparison branches, with paired acquisitions and data lineage | [Task design](tasks/microscopy_operations_v2/TASK_DESIGN.md) |
| Semiconductor fibres | Manufacturing routes, device preparation, characterization, measurement and application branches, including destructive sibling specimens | [Task design](tasks/fibre_operations_v2/TASK_DESIGN.md) |
| Thermoelectric devices | Material routes, interfaces and cutting directions, segmented and single-leg controls, module assembly, contact and thermal/electrical measurements | [Task design](tasks/thermoelectric_operations_v2/TASK_DESIGN.md) |
| diSPIM microscopy | Instrument assembly, three-camera alignment, reference calibration, routine sample preparation, dual-view acquisition and archiving | [Task design](tasks/dispim_operations_v2/TASK_DESIGN.md) |
| Helical acoustic metamaterials | Fabrication, transmission and pulse measurements, 40-cell lens assembly, field scans with and without obstacles, records and reset | [Task design](tasks/acoustic_operations_v2/TASK_DESIGN.md) |
| Perovskite solar modules | Precursor/control preparation, device and module fabrication, molecular/crystal/film assays, electrical measurement and ageing with persistent specimen histories | [Task design](tasks/perovskite_operations_v2/TASK_DESIGN.md) |
| Prismatic metamaterials | Cardboard demonstrators, cyclic compression, reach/release, hinge-material and array-thickness controls, selected configurations and bounded pneumatic work | [Task design](tasks/prismatic_operations_v2/TASK_DESIGN.md) |

All published task narratives and structured descriptions are in English. Structured specifications and source identifiers accompany each package.

The seven-paper logical explorer includes the perovskite design. The new prismatic family is available as a source-audited task-design package and is not yet integrated into that explorer. Its [independent contract tests](tasks/prismatic_operations_v2/tests/VALIDATION_REPORT.md) cover 40 public checks plus an optional primary-source-byte check. Embodied visual storyboards currently cover selected chiral and thermoelectric routes only. Configuration, branch and operation counts describe the representation; they are not counts of independent experiments or successful executions.

## Quick start: inspect a task

Start with the [Deconwolf task design](tasks/microscopy_operations_v2/TASK_DESIGN.md), then compare its agent-facing inputs with its coverage and recovery requirements.

From the repository root, Python 3's standard library can inspect the JSON without installing dependencies, downloading sources or changing files:

```sh
python3 -B -m json.tool tasks/microscopy_operations_v2/agentgoal.json
python3 -B -m json.tool tasks/microscopy_operations_v2/initialstate.json
python3 -B -m json.tool tasks/microscopy_operations_v2/paper_coverage.json
python3 -B -m json.tool tasks/microscopy_operations_v2/recovery_design.json
```

Run `python3 scripts/check_english.py` to check for untranslated CJK text, including escaped JSON values. This checks language hygiene, not translation accuracy.

These commands parse and print the specifications. They do not validate source completeness, run an episode or operate equipment. There is no supported whole-paper execution command in this release.

For a second perspective, inspect the fibre family's [lineage contract](tasks/fibre_operations_v2/lineage_contract.json), [control packages](tasks/fibre_operations_v2/control_packages.json) and [granularity gaps](tasks/fibre_operations_v2/granularity_gaps.json).

### Reproduce static release checks

With Python 3.9+ and Node.js available on `PATH`, run from the repository root:

```sh
python3 -B scripts/verify_release.py
```

No third-party Python or Node packages, network access, browser, renderer or hardware are required. The command does not rebuild the viewer or rewrite task files. It exits nonzero for missing prerequisites, missing required files, failed checks or skipped Python tests.

The command checks:

- All repository JSON outside tool/cache directories, including new task drafts, for valid syntax, duplicate keys and non-JSON numeric constants
- The existing English hygiene check and focused verifier regression tests
- The existing seven-family explorer tests with `SCIENCEGYM_TASKS` explicitly bound to this checkout's `tasks` directory, so source-comparison tests cannot silently skip
- JavaScript syntax and the explorer plus both embodied players' mocked-DOM tests
- All 71 storyboard frame images against their published render hashes, any per-frame image hashes, and applicable image-only export checksums, including overview/contact-sheet images

These are static consistency, display-contract and image-byte checks. Parsing a new task's JSON is not full schema or scientific review. Mocked-DOM tests do not test an actual browser, and none of these checks executes a robot task, validates physical feasibility, reproduces scientific results or establishes whole-paper completeness.

The older `scripts/verify_export.py` checks the original `EXPORT_MANIFEST.json` snapshot. That historical manifest is not an inventory of subsequent repository changes. The current release command parses historical receipts and verifies their applicable frozen image hashes, but does not assert that their old text hashes describe the current tree. Historical source-scene, mesh, video and other unbundled asset hashes are not revalidated.

## Status and next steps

The current milestone is **source-grounded task design**. Runtime state transitions, manipulation interfaces, navigation, trusted event logging and end-to-end evaluation still need implementation and validation. Some procedures use closed-service abstractions; their internal human microactions are not fully reconstructed. Missing scientific parameters, geometry, calibration and operational details remain explicit gaps.

Next steps are to implement selected complete episodes, bind the required Hooke assets and interactions, validate initial states and sample histories, and test both successful routes and recovery cases. Only then can executable coverage be assessed separately from design coverage.

Physical simulation is paused. No whole-paper robot execution or physical scientific reproduction is claimed. The work remains an early research prototype and does not establish publication-ready experimental evidence.

## Sources, release scope and licensing

Source locators, provenance and unresolved claims are recorded within each task package. Source-reported facts, interpretations and authored task mechanics must remain distinguishable. Access to a paper does not imply permission to redistribute its text, figures, videos or datasets.

This first public snapshot focuses on authored task specifications. It is not a complete mirror of the development archive: bulk binary scenes, asset exports and the early manuscript are not included while their publication and rights review is pending. Historical provenance references may identify resources that are not bundled. Original publisher source packets and scientific datasets are not supplied by this release.

ScienceGym is licensed under the [Apache License 2.0](LICENSE). Third-party publications, datasets and assets remain subject to their own licenses and notices; the project license does not relicense them. Obtain any required third-party materials from their lawful sources.

These specifications are research task designs, not approved laboratory SOPs or instructions to operate real equipment.
