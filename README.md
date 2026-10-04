# ScienceGym

**Long-horizon robot research tasks derived from scientific papers.**

ScienceGym studies how to translate a paper's reported experimental program into tasks for an embodied research agent: preparing materials, moving samples between instruments, assembling apparatus, running controls and repeated measurements, preserving records, recovering from failures, and leaving the laboratory in a defined final state.

The unit of design is a **paper-level task family**. Its branches, dependencies, sample histories and measurement obligations determine what the agent must accomplish. An episode can cover a complete route or a control package; paper-level completion requires the full declared scope.

**Current release: 28 reviewed paper-level task-design drafts, including partial-source gated drafts, plus 1 bounded nonbiological subset (29 packages total); zero validated runnable whole-paper tasks.** The repository currently supports reading and inspecting static specifications. Task execution is future work.

## Contribute a task or asset

Start with [CONTRIBUTING.md](CONTRIBUTING.md) to claim a paper or asset, choose a contribution track and prepare a reviewable pull request. Read the [project vision](docs/PROJECT_VISION.md), [paper task guide](docs/contributing/PAPER_TASK_GUIDE.md), [asset guide](docs/contributing/ASSET_GUIDE.md) and [readiness checklist](docs/contributing/REVIEW_CHECKLIST.md). Task and asset work can proceed in parallel while physical simulation is paused.

## Editable directional-cooling 3D assets

The [directional-cooling operations lab](assets/cooling_scene_assets_v1/README.md) adds original editable geometry for the [directional-cooling task design](tasks/directional_cooling_operations_v2/TASK_DESIGN.md): paired white/black device displays, a retained carrier and clamps, exploded-film handling views, backside heater/probe inspection, and authored logger/power and optical-instrument envelopes.

[![Original directional-cooling laboratory scene with paired device displays, sample-handling fixture and authored instrument envelopes](assets/cooling_scene_assets_v1/evidence/overview.png)](assets/cooling_scene_assets_v1/evidence/overview.png)

[Download the editable Blender scene](assets/cooling_scene_assets_v1/geometry/cooling_operations_lab.blend?raw=true) · [Download the whole-scene GLB](assets/cooling_scene_assets_v1/geometry/cooling_operations_lab.glb?raw=true) · [Download the handling-module GLB](assets/cooling_scene_assets_v1/geometry/cooling_handling_module.glb?raw=true)

[![Authored carrier and clamps, 50-times-thickness handling-film display, backside inspection coupon and six-probe storage rack](assets/cooling_scene_assets_v1/evidence/sample_handling.png)](assets/cooling_scene_assets_v1/evidence/sample_handling.png)

[![Authored optical-instrument envelope and logger/power consoles with demo-only controls and no acquisition or output](assets/cooling_scene_assets_v1/evidence/equipment_closeup.png)](assets/cooling_scene_assets_v1/evidence/equipment_closeup.png)

This package contains **8 distinct asset roots and 438 child parts**, including meshes, curves and text. These are scene-organization counts, not independent devices or collidable meshes; the handling GLB re-exports two existing roots. The [binding ledger](assets/cooling_scene_assets_v1/operation_bindings.json) accounts for all 56 task-operation IDs: **29 partial visual/semantic bindings, 27 not-built entries and zero fully implemented operations**. The existing 28 paper-level designs, one bounded subset and 28 viewer families are unchanged. Earlier asset inventories remain separate; no deduplicated repository-wide asset total is asserted.

The [local semantic controls](assets/cooling_scene_assets_v1/semantic_controls.py) and [native pose binder](assets/cooling_scene_assets_v1/geometry/apply_demo_state.py) demonstrate guarded carrier docking/lifting, coupled clamp and lid poses, handling-film removal/damage/replacement identity, reflector display offsets, demo logger readback, and optical configuration/reference placement. They supply no device I/O, measurements, thermal/radiative/optical/electrical model, collision/contact physics, robot feasibility or scientific execution. Static GLBs do not execute these Python controls.

The [dimension and provenance ledger](assets/cooling_scene_assets_v1/asset_metadata.json) separates reported component dimensions from authored fixtures, fit clearances, straight tracks, display poses and instrument envelopes. The **100 mm versus approximately 150 mm reflector-height conflict remains unresolved**: the physical target is null, while 150 mm is only a display choice. Sensor-position schematics exist, but qualified installation coordinates and tolerances remain unavailable; the six-probe rack is authored storage geometry. Paired-device films retain the reported 16 micrometre thickness at 1×; handling films and the lower torn representation enlarge thickness alone 50×. Display tabs are not qualified grasp tabs. Primitive helper-code reuse establishes no AFM hardware compatibility.

The [30-file publication allowlist](assets/cooling_scene_assets_v1/EXPORT_ALLOWLIST.json) contains one editable Blender scene, two static GLBs, three original CPU renders, scripts, contracts, licenses and review records. [Independent content review](assets/cooling_scene_assets_v1/review/independent_review.md) passed within the stated static-asset/local-state scope. Interiors and parts of the angle fixture are occluded in baseline views, and small captions may require zoom or metadata lookup. No publisher papers, figures, source CAD, private archives, backup scenes or duplicate asset ZIP are included.

## Editable AFM 3D assets

The [cantilever-free AFM operations lab](assets/afm_scene_assets_v1/README.md) adds original editable geometry for the [bounded inert-metrology task design](tasks/afm_metrology_operations_v2/TASK_DESIGN.md): parallel-imaging and characterization apparatus, probe and target assemblies, retained carriers, clamps and an authored grasp/access proxy.

[![Original AFM laboratory scene: parallel-imaging apparatus, characterization apparatus and retained sample carrier](assets/afm_scene_assets_v1/evidence/overview.png)](assets/afm_scene_assets_v1/evidence/overview.png)

[Download the editable Blender scene](assets/afm_scene_assets_v1/geometry/afm_operations_lab.blend?raw=true) · [Download the apparatus GLB](assets/afm_scene_assets_v1/geometry/afm_operations_lab.glb?raw=true) · [Download the magnified explainer GLB](assets/afm_scene_assets_v1/geometry/afm_magnified_explainer.glb?raw=true)

[![Magnified AFM microassembly and cylinder-coupon explainer; support slabs and exploded gaps are authored display geometry](assets/afm_scene_assets_v1/evidence/equipment_closeup.png)](assets/afm_scene_assets_v1/evidence/equipment_closeup.png)

[![Retained sample carrier, authored clamp interfaces and orange grasp proxy](assets/afm_scene_assets_v1/evidence/sample_handling.png)](assets/afm_scene_assets_v1/evidence/sample_handling.png)

This package contains **17 asset roots and 348 inventory parts**; these are scene-organization counts, not distinct laboratory devices. Fifteen mapped roots cover **23 distinct task-operation IDs** through [static semantic bindings](assets/afm_scene_assets_v1/operation_bindings.json). The local carrier/clamp guards and demonstration poses do not implement device control, calibrated measurements, collision or contact physics, robot reachability, or a runnable task. The existing paper-design, bounded-subset and viewer counts are unchanged. Earlier asset inventories remain separate; no deduplicated repository-wide asset total is asserted.

The [dimension and provenance ledger](assets/afm_scene_assets_v1/asset_metadata.json) distinguishes reported parameters, numerical-model dimensions and authored geometry. Device housings, fixtures, carriers, clearances and silicon target motifs are authored approximations, not manufacturer CAD or qualified replicas. Native microscopic parts use metres; the separate explainer enlarges cone/cylinder features 1000× while its support slabs, target relief and exploded gaps are authored display geometry. The 49-cone illustration is not the reported 1088-position array. The source's 0.5 mm versus 5 mm whole-array span conflict remains unresolved. The Mitutoyo 10× / NA 0.28 parallel configuration and Olympus 10× / NA unreported characterization configuration remain distinct.

The [30-file publication allowlist](assets/afm_scene_assets_v1/EXPORT_ALLOWLIST.json) contains one editable Blender file, two GLBs, three original CPU renders, scripts, contracts, licenses and review records. [Independent review](assets/afm_scene_assets_v1/review/independent_review.md) passed for static display with declared limitations. Package tests and Blender checks cover static geometry and local semantic/kinematic behavior only. No publisher papers, figures, private archives, backup scenes or duplicate asset ZIP are included.

## Embodied laboratory task demonstration

The R01 example binds a mobile humanoid, laboratory stations, manipulated objects and sample states to **26 reference-operation keyframes**. It shows stock collection, fabrication handoff, assembly, metrology, two authored loading cycles, archiving and cleanup. [Open the offline visual replay guide](viewer/embodied_r01/README.md).

[![Robot, equipment and objects during stock collection](viewer/embodied_r01/frames/01_FAB01.jpg)](viewer/embodied_r01/README.md)

[Assembly view](viewer/embodied_r01/frames/09_ASM04.jpg) · [Loading and specimen inspection](viewer/embodied_r01/frames/19_LOAD.jpg) · [Archive view](viewer/embodied_r01/frames/24_ARCHIVE.jpg).

This is an authored visual storyboard, not a physics simulation or robot execution. It covers the R01 branch, not all branches of the paper. Repeated unit placements are summarized in layer-completion views, not individual grasp trajectories. Source-supported stages, authored poses and unknowns remain distinguished.

### R01 task-scene binding audit

A [bounded mounting, observation and retrieval binding](scene_bindings/r01_mount_observe_retrieve_v1/README.md) now maps eleven R01 reference operations to existing scene objects, metadata ports, object-origin frames and intended sample states. A fresh, fixed-camera Blender CPU source inspection retains all occluding geometry. Static checks cover references, identity, units, display scale and camera declarations; a missing transport clip and unqualified physical/sensor interfaces remain explicit gates. This adds inspection evidence, not a third embodied route or a runnable episode.

### Thermoelectric module route

The PAIRED_TWO demonstration maps **66 reference-operation occurrences to 45 illustrated keyframes**: separate P/N preparation, cross-device processing, four individually tracked leg placements, module assembly, four measurement-boundary chapters, archiving and cleanup. [Open the offline visual replay guide](viewer/embodied_thermoelectric/README.md).

[![Robot assembling the third individually tracked thermoelectric leg](viewer/embodied_thermoelectric/frames/29_PLACE_P2.jpg)](viewer/embodied_thermoelectric/README.md)

[Whole route contact sheet](viewer/embodied_thermoelectric/keyframes_contact_sheet.jpg) · [Laboratory overview](viewer/embodied_thermoelectric/overview.jpg) · [Coverage and limitations](viewer/embodied_thermoelectric/loop_coverage.json).

These are authored static/kinematic states. Millimetre-scale leg geometry is explicitly enlarged 20× for inspection; physical grasp feasibility is not established. Repeated current/acquisition loops remain grouped with unknown grid values and counts. No scientific measurements or controller execution are supplied. This demonstration covers one selected route, not every branch of the paper.

## Explore the paper-level tasks

[Open the offline explorer guide](viewer/task_explorer_v1/README.md) to inspect branches, robot actions, objects, sample states, source evidence and recovery. Download the folder and open index.html locally; GitHub shows HTML as code rather than running it.

All twenty-eight task-design families now have visual route maps readable directly on GitHub: [Chiral](viewer/task_explorer_v1/docs/chiral.md) · [Deconwolf](viewer/task_explorer_v1/docs/microscopy.md) · [Fibres](viewer/task_explorer_v1/docs/fibre.md) · [Thermoelectric](viewer/task_explorer_v1/docs/thermoelectric.md) · [diSPIM](viewer/task_explorer_v1/docs/dispim.md) · [Acoustics](viewer/task_explorer_v1/docs/acoustic.md) · [Perovskite](viewer/task_explorer_v1/docs/perovskite.md) · [Prismatic](viewer/task_explorer_v1/docs/prismatic.md) · [EmVP](viewer/task_explorer_v1/docs/emvp.md) · [Directional cooling](viewer/task_explorer_v1/docs/cooling.md) · [Wavefront acoustics](viewer/task_explorer_v1/docs/wavefront.md) · [Bianisotropic acoustics](viewer/task_explorer_v1/docs/bianisotropic.md) · [Acoustic edge detection](viewer/task_explorer_v1/docs/edge.md) · [Origami memory](viewer/task_explorer_v1/docs/origami_memory.md) · [Ring origami](viewer/task_explorer_v1/docs/ring_origami.md) · [Mechanical backpropagation](viewer/task_explorer_v1/docs/mechanical_backprop.md) · [Granular assembly](viewer/task_explorer_v1/docs/granular_assembly.md) · [Beaded metamaterials](viewer/task_explorer_v1/docs/beaded.md) · [Thermal jamming](viewer/task_explorer_v1/docs/thermal_jamming.md) · [Horn acoustics](viewer/task_explorer_v1/docs/horn_acoustics.md) · [Reprogrammable mechanical logic](viewer/task_explorer_v1/docs/mechanical_logic.md) · [Cold-programmed shape morphing](viewer/task_explorer_v1/docs/cold_shape.md) · [Gear metamaterials](viewer/task_explorer_v1/docs/gear.md) · [Hydrogel optical metastructures](viewer/task_explorer_v1/docs/hydrogel_optical.md) · [Atmospheric optics](viewer/task_explorer_v1/docs/atmospheric_optics.md) · [Bounded AFM metrology](viewer/task_explorer_v1/docs/afm_metrology.md) · [Martian geophysics](viewer/task_explorer_v1/docs/martian_geophysics.md) · [3D transistor devices](viewer/task_explorer_v1/docs/transistor.md).

Gear and hydrogel add 77 inspection records and 176 operation definitions. Gear retains 18 physical branches, eight separate preparation recipes, seven numerical records, two derived-analysis obligations and two illustrative-only records. Hydrogel retains 36 physical branches and four separate numerical, theory, fit and compatibility dispositions. All 40 unresolved-input groups, 14 controls, 19 source conflicts and 19 gear specimen-family definitions remain explicit. These are representation counts, not specimen counts or completed experiments.

Gear recipes preserve their source-declared authored valid order, including repeated TRANSFER destinations; preparation and per-condition templates are not concatenated into historical specimen traces. The 5×6 micro Taiji build, 4×4 compression specimen, 5×5 actuation specimen and macro video demonstrator remain distinct. Planetary CAD and micro-geometry conflicts stay open. Fit-window variation is not between-specimen SD, finite shear stiffness is not periodic-cell modulus, and impact allocations remain terminal. Numerical operation references remain modeled and illustrative records never gain physical trial credit.

Hydrogel operation lists remain unordered membership under 40 branch-lineage dependencies and the six-phase order within each of 17 closed services. There is no inferred cross-service chronology or automatic Cartesian crossing of condition axes. Four Extended Data image sets remain uninspected, despite caption access. Power/data conflicts and missing cells remain explicit; the heated Fig. 6f record is a single constant, not 361 measured observations. Video 9 is accelerated 20 times and sampled frames are not full playback. Chemical, laser, UV and thermal work remains inside closed qualified services, with no executable hazardous recipes supplied.

Gear and hydrogel source links are pinned to [9e490ae5d3380121df7be1c18d4de35aac8508c5](https://github.com/openags/ScienceGym/tree/9e490ae5d3380121df7be1c18d4de35aac8508c5).

This author/evaluator logical inspector covers 676 inspection records and 2,710 operation definitions. These are task-design references, not executed robot trajectories or a new 3D storyboard. Nested loops, repeated operations and unresolved conditions remain explicit; unknown loops are not expanded. Prismatic operation membership follows partial-order constraints, with nested material/target and thickness/target coverage, independent campaign branches and conditional recovery. [Verification and limitations](viewer/task_explorer_v1/VERIFICATION.md).

Assembly views add 78 inspection records and 145 operation definitions: 60 physical configurations, one campaign dispatcher and 17 distinct numerical, analysis, external-input, device-owned or reference-scope records. Granular and thermal memberships preserve scoped causal edges, conditional gates, sample lineage and symbolic repeats. Beaded trees preserve all source sequences, exclusive preparation choices, loops and per-entry bindings. Received parts and preassembled objects do not earn robot fabrication credit. Source constants, numerical packings, cycles and pair comparisons do not supply missing independent physical specimen counts.

## Visual task routes

The first visual route shows every listed R01 operation and the complete chiral branch index. Dashed connectors represent the authored reference order, not an executed trajectory or a recovered author chronology. The twenty-eight-family offline interactive explorer is linked above.

[![Chiral metamaterials: complete R01 task route and branch index](docs/visualizations/chiral_r01.svg)](docs/visualizations/chiral_r01.svg)

## Why paper-level tasks?

Scientific work connects many individually simple actions across long intervals and multiple devices. A useful task must preserve those connections:

- **Whole reported routes:** preparation and fabrication, intermediate processing, characterization, measurement, archiving and cleanup
- **Branches and dependencies:** alternative material families, shared prerequisites and independent experiments, without inventing a single global chronology
- **Sample lineage:** batches, parent–child specimens, destructive siblings, reused samples and irreversible treatment histories
- **Cross-device manipulation:** carrying, loading, aligning, mounting, connecting and unloading the right object at each station
- **Controls and repetition:** paired conditions, repeated observations and same-specimen cycles kept distinct from independent samples
- **Recovery:** failed attempts remain in the record; damage, contamination or an invalid measurement cannot be erased by relabeling an object

ScienceGym is an independent project whose task layer specifies these obligations. Laboratory scene and asset requirements appear in its task packages. The bounded R01 static binding above is an initial integration check; runtime interactions and physical validation remain future work. A scene or addressable object alone does not establish an executable task.

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

The twenty-eight packages have undergone design review and static consistency checks. These are draft representations of reported scope, not human expert certification or completed robotic reproductions. The reprogrammable mechanical-logic (ReMM) package is a partial-source gated draft: its main figure panels and all nine supplementary movie contents remain uninspected, so source completeness is false.

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
| Embedded extrusion-volumetric printing | Material qualification, positive/negative printing, transfer and alignment, cleaning, optical/rheological/CT/mechanical comparisons and immutable sample records | [Task design](tasks/emvp_operations_v2/TASK_DESIGN.md) |
| Directional radiative cooling | Mobile-robot material preparation, assembly, sensor calibration, optical station handoffs, paired outdoor comparisons, modified-assembly checks and cleanup | [Task design](tasks/directional_cooling_operations_v2/TASK_DESIGN.md) |
| Anti-repellent granular assembly | Robot-led substrate and particle preparation, patterning-device handoffs, collision and assembly controls, imaging, material variants and sample recovery | [Task design](tasks/granular_assembly_operations_v2/TASK_DESIGN.md) |
| Origami mechanical memory | Robot fabrication and assembly, geometry and fixture configuration, compression and torque handoffs, one-bit/two-bit switching, sensing and preload release | [Task design](tasks/origami_memory_operations_v2/TASK_DESIGN.md) |
| Beaded metamaterials | Robot component preparation, bead/thread weaving, supported transfer, pretension and fixture setup, compression/dilation/bending comparisons, imaging and recovery | [Task design](tasks/beaded_operations_v2/TASK_DESIGN.md) |
| Thermal jamming | Robot rod and fixture preparation, packing, heated pull-out, cycling and friction controls, calorimetry, XCT and load-hold handoffs | [Task design](tasks/thermal_jamming_operations_v2/TASK_DESIGN.md) |
| Ring origami | Robot facet and crease fabrication, fine-fastener assembly, cardboard-array preparation, reconfiguration, compression, torsion inference and shape measurements | [Task design](tasks/ring_origami_operations_v2/TASK_DESIGN.md) |
| Mechanical backpropagation | Robot lattice fabrication handling, camera calibration, weight and string loading, paired gradient measurements and tests of fabricated trained networks | [Task design](tasks/mechanical_backprop_operations_v2/TASK_DESIGN.md) |
| Acoustic wavefront modulation | Robot sample and array preparation, guide assembly, calibration, reference and transmission measurements, normal/oblique controls, field scans and cleanup | [Task design](tasks/acoustic_wavefront_operations_v2/TASK_DESIGN.md) |
| Bianisotropic acoustic metasurfaces | Robot fabrication handling and panel assembly, guide preparation, calibration and paired reflection/transmission scans, with computational design branches kept separate | [Task design](tasks/bianisotropic_operations_v2/TASK_DESIGN.md) |
| Subwavelength acoustic edge detection | Robot guide fabrication handling, target preparation, four-channel rig assembly and calibration, reference/specimen sweeps, spatial scans and cleanup | [Task design](tasks/acoustic_edge_operations_v2/TASK_DESIGN.md) |
| Horn-like acoustic metasurfaces | Robot horn fabrication handling and mirrored-panel assembly, two-microphone calibration, paired cylindrical-to-plane field mapping, records and cleanup; forward focusing and beam splitting remain numerical | [Task design](tasks/horn_acoustics_operations_v2/TASK_DESIGN.md) |
| Reprogrammable mechanical logic (ReMM; partial-source) | Robot component and circuit preparation, reprogramming, electromagnetic and mechanical logic tests, defective routing, volatile storage and mesoscale fabrication, with uninspected source content and execution inputs explicitly gated | [Task design](tasks/mechanical_logic_operations_v2/TASK_DESIGN.md) |
| Cold-programmed shape morphing | Robot material and specimen custody, qualified-service printing and programming handoffs, mechanical/thermal characterization, shape-memory and hinge cycles, demonstrated shape families, electronics, micro-pipe and alternative-resin branches | [Task design](tasks/cold_shape_operations_v2/TASK_DESIGN.md) |
| Gear metamaterials | Eight preparation routes, nineteen specimen families, physical loading and impact branches, measured hysteresis, controls, immutable specimen lineage and qualified-input gates | [Task design](tasks/gear_operations_v2/TASK_DESIGN.md) |
| Hydrogel optical micro-metastructures | Qualified-service preparation, retained-carrier transfers, mechanical and optical characterization, condition-specific specimen histories, controls, thermal/optical readout, archive and safe closure | [Task design](tasks/hydrogel_optical_operations_v2/TASK_DESIGN.md) |
| Cantilever-free AFM inert metrology | Qualified inert-target and retained-probe custody, calibration, intermittent-contact raster/line imaging, separate cylinder characterization, readout and session teardown | [Task design](tasks/afm_metrology_operations_v2/TASK_DESIGN.md) |
| Atmospheric optics | Protected-component preparation and mount custody, calibrated observational acquisition, frame/data lineage, wavefront analysis and separately gated numerical branches | [Task design](tasks/atmospheric_optics_operations_v2/TASK_DESIGN.md) |
| Martian mineral physics | Qualified specimen and carrier custody, distinct synthesis and in situ/ex situ service branches, independent acoustic and X-ray readout, destructive recovery lineage, composition/mode characterization and separately gated numerical analysis | [Task design](tasks/martian_geophysics_operations_v2/TASK_DESIGN.md) |
| Three-dimensional integrated metal-oxide transistors | Qualified fabrication and carrier custody, source-defined device and failed-control branches, packaging, metrology, distinct electrical and stress histories, inverter netlists, retained readout and cleanup | [Task design](tasks/transistor_operations_v2/TASK_DESIGN.md) |

All published task narratives and structured descriptions are in English. Structured specifications and source identifiers accompany each package.

The earlier sixteen-paper logical-explorer expansion included perovskite, prismatic, EmVP, directional cooling, three acoustic designs and three mechanical designs. The mechanical views add 60 records and 160 definitions: 33 physical designs, 3 preparation views, 3 campaign records, 15 numerical/theoretical dispositions, 5 proposals/concepts and 1 derived-analysis disposition. Ring macro/concurrency and conditional-preparation trees and backprop forward/adjoint/transfer bindings stay intact. Numerical training is not physical self-updating hardware; ring torque remains semi-experimental, not directly measured. The acoustic views add 46 inspection records: 20 physical routes/leaves, 22 numerical/theoretical dispositions, three shared-preparation records and one source-defined campaign-accounting record. These record types remain separately labeled; campaign closure and mutually exclusive target-preparation choices are not merged into physical specimen histories. Prismatic contributes 12 route/configuration records and 49 operation definitions across seven practical families; the earlier paper-level families retain their semantics. Prismatic's [independent contract tests](tasks/prismatic_operations_v2/tests/VALIDATION_REPORT.md) cover 40 public checks plus an optional primary-source-byte check. Embodied visual storyboards currently cover selected chiral and thermoelectric routes only. Configuration, branch and operation counts describe the representation; they are not counts of independent experiments or successful executions.

EmVP is integrated as the ninth family, adding 19 configurations and 53 operation definitions. The logical inspector preserves its 15 comparison packages, 30 unresolved gates, source dependencies and three separately allocated cage-condition routes. Authored viewing order is not a robot action sequence, and comparison states/sites are not independent specimens. Its independent suite has 44 public checks plus one optional source-byte check; all 45 passed with the lawful source packet. Published package status records describe their authoring/validation snapshot, not a robot execution or a live GitHub deployment state.

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
- The bounded R01 task-scene binding audit and negative-fixture tests, including frozen source-inventory and CPU-render evidence hashes
- The explorer tests with `SCIENCEGYM_TASKS` explicitly bound to this checkout's `tasks` directory, so source-comparison tests cannot silently skip
- JavaScript syntax and the explorer plus both embodied players' mocked-DOM tests
- All 71 storyboard frame images against their published render hashes, any per-frame image hashes, and applicable image-only export checksums, including overview/contact-sheet images

These are static consistency, display-contract and image-byte checks. Parsing a new task's JSON is not full schema or scientific review. Mocked-DOM tests do not test an actual browser, and none of these checks executes a robot task, validates physical feasibility, reproduces scientific results or establishes whole-paper completeness.

The older `scripts/verify_export.py` checks the original `EXPORT_MANIFEST.json` snapshot. That historical manifest is not an inventory of subsequent repository changes. The current release command parses historical receipts and verifies their applicable frozen image hashes, but does not assert that their old text hashes describe the current tree. Historical source-scene, mesh, video and other unbundled asset hashes are not revalidated.

## Status and next steps

The current milestone is **source-grounded task design**. Runtime state transitions, manipulation interfaces, navigation, trusted event logging and end-to-end evaluation still need implementation and validation. Some procedures use closed-service abstractions; their internal human microactions are not fully reconstructed. Missing scientific parameters, geometry, calibration and operational details remain explicit gaps.

Next steps are to implement selected complete episodes, bind the required laboratory assets and interactions, validate initial states and sample histories, and test both successful routes and recovery cases. Only then can executable coverage be assessed separately from design coverage.

Physical simulation is paused. No whole-paper robot execution or physical scientific reproduction is claimed. The work remains an early research prototype and does not establish publication-ready experimental evidence.

## Sources, release scope and licensing

Source locators, provenance and unresolved claims are recorded within each task package. Source-reported facts, interpretations and authored task mechanics must remain distinguishable. Access to a paper does not imply permission to redistribute its text, figures, videos or datasets.

The original public snapshot focused on authored task specifications. The reviewed AFM and directional-cooling asset packages above now supply bounded sets of original editable geometry and rendered evidence. Other historical bulk scenes, asset exports and the early manuscript remain outside this repository while their publication and rights review is pending. This is not a complete mirror of the development archive; historical provenance references may identify resources that are not bundled. Original publisher source packets and scientific datasets are not supplied by this release.

ScienceGym is licensed under the [Apache License 2.0](LICENSE). Third-party publications, datasets and assets remain subject to their own licenses and notices; the project license does not relicense them. Obtain any required third-party materials from their lawful sources.

These specifications are research task designs, not approved laboratory SOPs or instructions to operate real equipment.

The directional-cooling design adds 56 explicit robot/device operation contracts across 11 physical route leaves. Its 38 static and synthetic-record checks passed independent review. It is integrated as the tenth family in the logical explorer, retaining six symbolic loops, fourteen unresolved input gates, conditional receipt dependencies, sample identities and required physical transport. Physical execution and thermal reproduction remain unverified.

The granular-assembly design contains 26 configurations, 42 robot/device operation templates and 31 explicit input gates. Its 35 author checks and 23 independent checks validate static design contracts only. It is integrated with 26 physical memberships and six separately labeled nonmanual views; historical movies/data and missing recipes remain explicit boundaries.

The origami-memory design contains 55 robot/device/analysis operation contracts and ten physical configurations plus a whole-paper campaign. All 29 static contract checks passed independent review. Numerical/proposed branches and unread supplementary movies remain separated from inspected physical evidence. It is integrated with ten physical views, campaign accounting and four separately labeled nonmanual dispositions.

The beaded-metamaterial design covers 13 practical families, 21 leaf configurations plus a campaign dispatcher, 70 robot/device operation templates, 15 control packages and 35 explicit input gates. Its 42 author checks and 25 independent checks passed. Source tables, geometry and some schedules remain unresolved. It is integrated with 21 physical leaf trees, one campaign dispatcher and eight separately labeled nonmanual views.

The thermal-jamming design adds 13 configurations, 33 robot-operation contracts and 27 unresolved-input gates. Its 25 author checks and 34 independent checks passed. Geometry conflicts, missing shape-setting inputs and XCT acquisition settings remain explicit. It is integrated with 13 physical memberships and three explicitly authored source-section navigation views.

The ring-origami design adds 14 physical branch templates, three preparation routes and 59 operations. Ten author tests and 48 independent checks passed. Semi-experimental torque remains tied to measured element data, while uninspected assembly-movie choreography and other execution inputs remain explicit gates. It is integrated with fourteen physical views, three preparation trees, campaign accounting and separate numerical, proposal and derived-analysis dispositions.

The mechanical-backpropagation design adds nine physical routes plus a campaign, 46 operations, ten explicit transfer contracts and 18 unresolved input gates. Its 43 static/symbolic tests and 37 independent checks passed. Numerical spring-constant updates and retraining remain separate from physical experiments. It is integrated using nine authoritative typed reference trees, independent campaign accounting and fourteen nonmanual dispositions; repeated forward/adjoint bindings remain distinct.

The acoustic-wavefront design adds 69 operations, ten physical routes, eight numerical/theoretical dispositions, fourteen transport routes and fifteen unresolved input gates. Its 82 static and synthetic-record tests passed. Historical Figure 3/4 acquisition frequencies remain unconfirmed; the 3000 Hz task reference assignment is explicitly authored. Corrugated coupling remains numerical-only. It is integrated into the logical explorer with a [source-bound inspection map](viewer/task_explorer_v1/docs/wavefront.md).

The bianisotropic-acoustics design adds 42 operation templates across fourteen design branches, twelve source-coverage families, eighteen unresolved input groups and seven control packages. Its standalone suite passes 48 checks and explicitly skips one optional private-source-byte check; all 49 pass when the lawful source packet is available. Only the 60-degree panel was physically tested in the paper; higher-angle designs and the COMSOL four-probe retrieval stay computational. It is integrated into the logical explorer with a [source-bound inspection map](viewer/task_explorer_v1/docs/bianisotropic.md).

The acoustic-edge-detection design adds 46 operation templates, seven physical acquisition branches, three numerical/theoretical branches, fourteen unknown-parameter groups and eight source-conflict records. All 62 static and synthetic-record tests passed. Main article and required supplementary text were inspected, while main-PDF bytes were not obtained and that hash remains null. It is integrated into the logical explorer with a [source-bound inspection map](viewer/task_explorer_v1/docs/edge.md).

These three acoustic packages add authored task contracts and checks, with no new scene, CAD or image assets, embodied visual routes, robot executions or scientific reproductions. Package verification and publication fields record their local authoring/review snapshots; they are not live repository deployment status.

The horn-like-acoustic-metasurface design adds 44 operation templates across five preparation, physical-measurement and closure branches, nine theory/numerical branches and seventeen unresolved input groups. All 84 static and synthetic-bookkeeping tests passed; independent review also rejected nine adversarial campaign mutations. Physical source evidence is limited to paired cylindrical-to-plane mapping without and with the focusing panel. Forward focusing, beam splitting and model comparisons remain numerical or theoretical. It is integrated with five physical preparation/measurement/closure views and nine separate numerical/theoretical views.

The reprogrammable-mechanical-logic (ReMM) design adds 55 operation contracts, fourteen physical-design routes, twelve nonmanual dispositions and fifteen unresolved execution gates. All 87 static and adversarial synthetic-bookkeeping tests passed independent review. This is a partial-source gated draft: the main narrative, Methods, captions and all seventeen supplementary pages were inspected, but main figure panels and all nine supplementary movie contents remain uninspected. Source completeness is false; passing contract checks does not close that gap. Numerical logic architectures and model settings remain separate from physical tests. It is integrated with fourteen physical memberships and twelve separately typed nonmanual dispositions, retaining the explicit source-completeness gap.

The cold-programmed-shape-morphing design adds 76 operation definitions, 32 physical branches, six numerical/analytical dispositions, nineteen unresolved gates, 24 transport contracts and seven loop types. All 86 author tests, 83 independent static checks and ten independent composition regressions passed. The full main article and twenty-page textual supplement were inspected; eight actual movies and the source-data workbook remain unread. Chemical preparation, printing, thermal/mechanical actuation and liquid-metal filling require closed, qualified services; safe operating cards, geometry and robot interfaces remain execution gates. It is integrated with 32 physical memberships and six numerical/analytical dispositions; two parameter-identification records have explicitly authored derived-fit navigation labels.

The three materials source packages above contain authored task contracts and checks. Their logical explorer integration completes coverage of the earlier 22 task designs. The two Nature Materials designs below subsequently brought the repository to 24 task designs, and their later explorer integration brought it to 24 viewer families. It adds no scene, CAD, image or other binary asset, embodied visual route, robot execution or scientific reproduction. Both embodied storyboards, bounded R01 scene binding and Apache 2.0 license remain unchanged. Source publications and source datasets are not bundled, and package verification fields describe local design-review snapshots rather than live deployment status.

Final material views add 78 inspection records and 175 operation definitions: 51 physical preparation, measurement or closure records, 20 numerical/theoretical records, two derived parameter-fit views, three explanatory references, one future proposal and one source-described extension. All 51 unresolved-input groups, 16 control records and 17 symbolic loop contracts remain intact. These are inspection-record counts, not additional task designs, independent specimens or completed experiments.

ReMM remains explicitly source-incomplete: source_complete is false, main figure panels and all nine movie contents remain uninspected. Cold-shape chemical preparation, printing, thermal/mechanical actuation and liquid-metal filling remain closed, qualified services. Its eight actual movies and source-data workbook remain unread. Derived parameter fits remain numerical/analytical source dispositions and never become independent validation. Horn paired physical maps remain distinct from numerical focusing, splitting and model comparisons; technical readouts do not supply independent replication.

Final material source links use [26f402e4be797a91edce8253e4ed45bed6e01e7c](https://github.com/openags/ScienceGym/tree/26f402e4be797a91edce8253e4ed45bed6e01e7c). Earlier nineteen generated family outputs, every task package, both embodied storyboards, scene bindings and repository LICENSE remain unchanged.


## New Nature Materials task-design packages

The [gear-metamaterials design](tasks/gear_operations_v2/TASK_DESIGN.md), based on [Nature Materials DOI 10.1038/s41563-022-01269-3](https://doi.org/10.1038/s41563-022-01269-3), adds 18 physical branch templates, 19 specimen families, eight preparation routes and 69 operation definitions. Seven numerical branches remain separate from physical scope. Measured hysteresis, controls, material and dimensional conflicts, specimen identity and qualified-input gates remain explicit. Its 65 author tests, 85 independent static checks, 40 adversarial probes and 1,178 structural mutations passed. These are static or synthetic bookkeeping checks only.

The [hydrogel optical micro-metastructure design](tasks/hydrogel_optical_operations_v2/TASK_DESIGN.md), based on [Nature Materials DOI 10.1038/s41563-023-01649-3](https://doi.org/10.1038/s41563-023-01649-3), adds 36 physical branches, 107 operation definitions, 53 source-coverage records, 22 unknown-parameter cards and 17 closed qualified services. Its 17 author unit-test methods and independent suites of 211 static checks, 43 adversarial probes, 158 structural mutations and 17 export-logic probes passed. Formulation, fabrication, solvent handling, UV/laser processing and thermal operations remain closed qualified services. Robot-facing contracts cover carrier movement, loading, handoff, readout and safe unloading; real actuation, trusted production evidence and actor isolation remain unimplemented.

Both designs use complete main text/Methods and written supplementary information inspected in their source audits. This is not complete inspection of all source media. Gear's five videos and hydrogel's nine videos were reviewed through eight sampled temporal keyframes each, not full motion or audio. Hydrogel's audit also inspected six main figure images, 22 supplementary pages with nineteen figures, and parsed seven workbooks; four Extended Data captions were read but their images remain uninspected. Hydrogel's entire-paper source-completeness flag remains false, and its main PDF was not acquired. Video 9 uses twenty-times-accelerated playback and a separate 27,000-unit specimen; clip duration and sampled frames do not establish experimental response time. The Fig. 4l 20/50-mW assignment and Fig. 3j wavelength/amplitude mapping conflicts remain unresolved gates.

The two exact export allowlists contain original authored Markdown, JSON and Python only: [gear](tasks/gear_operations_v2/EXPORT_ALLOWLIST.json) and [hydrogel](tasks/hydrogel_optical_operations_v2/EXPORT_ALLOWLIST.json). No publisher text dump, PDF, figure, movie, workbook, CAD, scene or other new binary asset is included. At the original two-package release, existing task packages, all 22 then-published explorer families, both embodied storyboards, bounded R01 scene binding and Apache 2.0 license were unchanged. The later gear/hydrogel explorer integration is described above; neither stage adds robot execution, physical simulation, numerical reproduction or scientific replication. Package review/publication fields describe local snapshots, not live deployment status.

Run the repository release checks above, then the new packages' read-only checks separately from the repository root:

```sh
(cd tasks/gear_operations_v2 && python3 -B verify_package.py && python3 -B -m unittest discover -s tests -v && python3 -B independent_review/check_static.py && python3 -B independent_review/probe_adversarial.py && python3 -B independent_review/probe_structural_mutations.py)
(cd tasks/hydrogel_optical_operations_v2 && python3 -B -m unittest discover -s tests -v && python3 -B tests/verify_package.py && python3 -B tests/verify_export.py)
```

The root verifier has eleven static/display check groups; its JSON parsing does not substitute for the package-specific checks. Hydrogel review scripts can regenerate receipt files and are therefore not part of the frozen package's read-only verification command. Successful checks preserve source and execution gates; they do not establish scientific completeness or operating safety.


## New AFM metrology and atmospheric-optics task designs

The [cantilever-free AFM inert-metrology design](tasks/afm_metrology_operations_v2/TASK_DESIGN.md), based on [Nature Communications DOI 10.1038/s41467-020-20612-3](https://doi.org/10.1038/s41467-020-20612-3), adds eight bounded physical branches and 27 operation definitions. Qualified prefabricated inert inputs, retained probe versus exchanged target custody, separate imaging and conventional-AFM setups, contact/release guards and final calibration invalidation remain explicit. Its two qualified-service preparation routes do not establish that fabrication occurred. The 0.5 mm/5 mm discrepancy and the printed series-spring denominator-sign conflict remain unresolved. The full retained main text, Methods, captions and fourteen written supplementary pages were inspected; main figure pixels were not verified, and source data and external MATLAB code were not acquired or executed. All 39 author test methods, 15 independent contract methods and seven independent export mutations passed.

The [atmospheric-optics design](tasks/atmospheric_optics_operations_v2/TASK_DESIGN.md), based on [Nature Photonics DOI 10.1038/s41566-024-01466-3](https://doi.org/10.1038/s41566-024-01466-3), adds eight route families, 28 branches, 196 operation definitions and 33 source-coverage records. Protected hardware custody, mounted leases, geometry calibration, timestamp-contiguous captures, chronological train/test partitions and train-only normalization remain distinct from numerical optics. The atmosphere is observed rather than handled as a specimen. Source parameter tensions, unassigned camera settings and the incomplete mapping of historical frame corpora remain open. Main scientific text, Methods, captions and all five written supplementary pages were read; supplementary table pages 3-5 were visually inspected. Main figure pixels remain uninspected and the main-byte identity hold remains active. All 21 author test methods, 18 independent contract methods and seven independent export mutations passed.

Those AFM and atmospheric-optics additions brought the repository to **26 task-design packages and 24 viewer families**, with the existing 541 inspection records and 2,189 viewer operation definitions unchanged. They add no viewer route, scene, CAD, image or other binary asset. Both embodied storyboards, the bounded R01 scene binding, all earlier task packages and the Apache 2.0 license remain byte-identical. Only each package's agent_visible.json may enter an actor context; other package files are author/evaluator material. The exact original-file export lists are [AFM](tasks/afm_metrology_operations_v2/EXPORT_ALLOWLIST.json) and [atmospheric optics](tasks/atmospheric_optics_operations_v2/EXPORT_ALLOWLIST.json). No publisher source file, full-text dump, figure, source dataset or private execution path is included.

From the repository root, run the root release checks and each new package's read-only checks:

```sh
python3 -B scripts/verify_release.py
(cd tasks/afm_metrology_operations_v2 && python3 -B -m unittest discover -s tests -v && python3 -B tests/verify_package.py && python3 -B tests/verify_export.py)
(cd tasks/atmospheric_optics_operations_v2 && python3 -B -m unittest discover -s tests -v && python3 -B tests/verify_package.py && python3 -B tests/verify_export.py)
```

All checks concern static design, exact-file integrity and visibly synthetic bookkeeping. They do not establish whole-paper source completeness, production observation authentication, apparatus safety, robot execution, physical simulation, numerical reproduction or scientific replication. Package review and publication fields remain local snapshot metadata rather than live deployment status.


## New Martian mineral-physics task design

The [Martian mineral-physics design](tasks/martian_geophysics_operations_v2/TASK_DESIGN.md), based on [Nature Geoscience DOI 10.1038/s41561-026-02104-z](https://doi.org/10.1038/s41561-026-02104-z), adds 38 branches and 254 operation definitions across all 13 audited source-route families. These counts describe task representations rather than specimens, successful experiments or executed trajectories. Qualified specimen/carrier custody, independent acoustic and X-ray evidence, destructive sectioning lineage, SEM/EPMA and phase-mode comparisons remain distinct from seven numerical-analysis branches. Pressure, thermal, gas, laser, radiation, cutting and instrument actions remain closed qualified services; the actor cannot supply actuator parameters or qualify a service.

The retained written main article and all 33 supplementary pages were read; six supplementary tables were inspected, with dense model grids traversed structurally rather than independently recomputed. The original main PDF and main/Extended Data figure pixels remain unavailable under the preserved access hold. All ten source discrepancies remain unresolved, including the temperature-correction sign and the disputed H5897/H5898 temperature assignment. Qualified pre-synthesis parent allocation stays an unresolved gate, the graphite route cannot inherit invented glass/pre-synthesis ancestry, and region-, method- and measurement-origin distinctions remain explicit. Published outcomes remain evaluator context and never serve as live measurements or completion targets.

That Martian mineral-physics addition brought the repository to **27 task-design packages and 24 viewer families**. The existing 541 inspection records and 2,189 viewer operation definitions, all 26 earlier packages, both embodied storyboards, bounded R01 scene binding, images, assets and Apache 2.0 license remain unchanged. The package adds no viewer, scene, CAD, image or other binary asset. Its [exact 46-file export allowlist](tasks/martian_geophysics_operations_v2/EXPORT_ALLOWLIST.json) contains only original English task design, contracts, synthetic checks and review records; publisher source files, full-text dumps, workbooks, figures and source datasets are excluded. Only agent_visible.json is eligible for an acting-agent context.

The author suite has 119 passing tests; independent source and contract suites have 12 and 83 passing tests, respectively. Structural and exact-export checks also pass. From the repository root:

```sh
python3 -B scripts/verify_release.py
(cd tasks/martian_geophysics_operations_v2 && python3 -B -m unittest discover -s tests -p 'test*.py' -v && python3 -B tests/verify_package.py && python3 -B review/test_independent_source.py && python3 -B review/test_independent_contract.py && python3 -B tests/verify_export.py)
```

These are static source-grounded design, synthetic bookkeeping and exact-file-integrity checks. They do not establish whole-paper source completeness, production service-signature verification, apparatus safety, robot execution, physical simulation, numerical reproduction or scientific replication. Real execution gates remain closed. Review and publication fields remain local snapshot metadata rather than live deployment status.


## New integrated metal-oxide transistor task design

The [three-dimensional integrated metal-oxide transistor design](tasks/transistor_operations_v2/TASK_DESIGN.md), based on [Nature Electronics DOI 10.1038/s41928-024-01205-0](https://doi.org/10.1038/s41928-024-01205-0), adds 24 branch designs across 17 source-route groups, 44 operation templates and a 72-layer inventory. Preparation and fabrication, failed controls, packaging, metrology, electrical acquisition, distinct stress histories, inverter reconfiguration, readout and cleanup retain their own lineage and prerequisites. These are task-representation counts; the operation templates do not enumerate completed robot trajectories. Chemical preparation, fabrication, deposition, lithography, cutting, ultrasonic bonding, electrical sourcing and thermal control remain closed qualified services.

The nine-page article and all 53 pages of its written supplement were read, with six main figures, 33 supplementary figures, six tables and eight supplementary sections accounted for. Selected equation, netlist, device-symbol, roughness-label and bonder-photograph panels received visual checks; raw experimental data were not acquired. All ten source conflicts remain qualification gates, including the 25/50 nm interstack-buffer discrepancy and printed ON/OFF, mobility and subthreshold-swing equations. No conventional correction or unreported setting is silently supplied. Ordinary and independently biased inverter netlists remain distinct; all 90 ordered inverter pairs are retained. Source observations remain evaluator-only and never prove task completion.

That transistor package addition brought the repository to **28 task-design packages and 24 viewer families**, before the cross-disciplinary viewer integration below. All 27 earlier task packages, 541 viewer inspection records, 2,189 viewer operation definitions, both embodied storyboards, bounded R01 scene binding, existing images/assets and Apache 2.0 license remain unchanged. The [exact 44-file export allowlist](tasks/transistor_operations_v2/EXPORT_ALLOWLIST.json) contains only original task descriptions, contracts, synthetic checks and review records. It adds no viewer, scene, CAD, image, source PDF, prose dump, raw experimental dataset or other binary asset. Only agent_visible.json is eligible for an acting-agent context.

All 81 author tests and 62 independent tests pass: 12 source-design checks, 32 adversarial lifecycle checks and 18 isolated export checks. Structural and exact-export checks also pass. The all-branch fixture accepts 3,994 synthetic events with a virtual clock and deliberately reduced population samples. It retains named controls and all ordered inverter pairs; it is not a long-term ageing experiment, a full source-population reproduction or a hardware safety controller. Numerical analysis remains a separately gated, unimplemented dependency.

From the repository root:

```sh
python3 -B scripts/verify_release.py
(cd tasks/transistor_operations_v2 && python3 -B -m unittest discover -s tests -v && python3 -B -m unittest discover -s review -v && python3 -B tests/verify_package.py && python3 -B tests/verify_export.py)
```

The checks concern original source-grounded design, synthetic schedule/receipt integrity and exact-file export. No real robot actuation, apparatus safety qualification, physics simulation, numerical reproduction or scientific replication is established. Source completeness for robot execution remains false; review/publication fields remain local snapshot metadata rather than live deployment status.

## Cross-disciplinary viewer integration — 2026-10-04

Four cross-disciplinary views add 135 inspection records and 521 operation definitions across 98 original source branches. The explorer now contains 28 families, 676 inspection records and 2,710 operation definitions. All 123 new source JSON documents, 91 unresolved-input groups, 53 control records and 34 source conflicts remain exact. These are representation counts, not additional papers, independent specimens or completed experiments. The prior 24 generated families remain byte-identical at 541 records and 2,189 definitions.

Atmospheric optics separates seven physical branches, thirteen observed-data/analysis branches and eight numerical branches. Mounted camera hardware stays under its lease while acquisition jobs and records move; computational TIS is not a piezo scan. Main figure pixels remain uninspected and the direct-byte identity hold remains active. AFM is bounded inert imaging/metrology, not full fabrication: eight branches retain the installed calibrated probe while exchanging targets, with two incomplete preparation contracts and a separate final session teardown that invalidates calibration. Martian geophysics retains 26 physical, four measurement-analysis, seven numerical and one data-curation branch; all pressure, heat, gas, laser, radiation and cutting operations stay within closed qualified facility services. Transistor operation inventories are explicitly unordered; exact lifecycle contracts preserve safe-zero evidence, separate cohorts and destructive daughters, elapsed-time/cooldown requirements, netlists and damage history. Typed frame, probe, region, stack, configuration, layer, population and numerical-sample counts never supply missing independent replicates. No source conflict, control setting, global chronology or completed service is invented.

All four new source pins use [990f98529182af0ddd03fba53587b0931630de96](https://github.com/openags/ScienceGym/tree/990f98529182af0ddd03fba53587b0931630de96). All 28 task packages, both embodied storyboards, scene bindings and LICENSE remain unchanged. No source assets, binary files, physics engine, actor loader, task runner or real execution is added.


## Bounded solar-water physical-measurement subset

The [solar-water physical-measurement subset](tasks/solar_water_operations_v2/TASK_DESIGN.md), based on [Nature Sustainability DOI 10.1038/s41893-020-0566-x](https://doi.org/10.1038/s41893-020-0566-x), adds 15 bounded branches and 34 operation templates for qualified prefabricated coupons, clean-water assemblies, physical optics, wicking, thermal and mass measurements, orientation, condensation bookkeeping and benign-only qualified maintenance. All 14 source conflicts remain explicit. Fabrication and hazardous chemistry stay within closed qualified-service boundaries without operational recipes.

This is **1 bounded nonbiological subset alongside the existing 28 paper-level task-design drafts: 29 packages total, not 29 whole-paper designs**. Its full_paper_complete flag is false. Biological operations, environmental or unknown contaminated-water handling, sanitation certification, potability and pathogen-efficacy claims are excluded. Source access or a successful synthetic check does not establish full-paper experimental coverage.

All 55 author tests and 19 independent tests pass. The all-branch fixture accepts 808 visibly synthetic events; it contains no scientific measurement values or physical time. Caller-owned synthetic receipt context does not establish production authentication or persistent retry/exposure-history enforcement. Qualification values, station adapters, geometry and independent experimental evidence remain absent. Literature outcomes remain evaluator annotations and never serve as robot success targets. Only agent_visible.json is eligible for an acting-agent context.

The [exact 40-file export allowlist](tasks/solar_water_operations_v2/EXPORT_ALLOWLIST.json) contains original Markdown, JSON and Python only. Its 39 payload files and manifest are copied unchanged from the independently approved bounded package. Publisher PDFs, source text dumps, figures, videos, datasets and other source assets are not included. Package review/publication fields describe the frozen local review snapshot rather than live deployment status.

The repository retains **28 viewer families, 676 inspection records and 2,710 viewer operation definitions**. This subset adds no explorer family, embodied route, scene, CAD, image or other binary asset. All 28 earlier task packages, the complete existing viewer, both embodied storyboards, bounded R01 scene binding and Apache 2.0 license remain byte-identical. No robot execution, apparatus qualification, physical simulation, numerical reproduction or scientific replication is established.

From the repository root, run the eleven static/display check groups and the bounded package checks separately:

```sh
python3 -B scripts/verify_release.py
(cd tasks/solar_water_operations_v2 && python3 -B -m unittest discover -s tests -v && python3 -B -m unittest discover -s review -v && python3 -B tests/verify_package.py && python3 -B tests/verify_export.py)
```
