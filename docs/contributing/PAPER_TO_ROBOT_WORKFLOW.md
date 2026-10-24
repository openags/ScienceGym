# Paper-to-Robot Task Conversion Workflow

This is the required authoring and handoff workflow for new paper conversions and substantive task-design revisions. It complements the [paper task guide](PAPER_TASK_GUIDE.md), [equipment standard](EQUIPMENT_MODELING_STANDARD.md) and [review checklist](REVIEW_CHECKLIST.md). It defines planning steps and saved artifact roles, not an installed automatic paper converter or a universal robot runtime API. Existing packages retain their filenames and semantics; map them to these roles rather than renaming frozen files.

The output is a complete, inspectable account of the physical work needed to perform the declared experimental program. It must expose robot perception, motion, manipulation and planning demands. Published scientific outcomes are reference context, never a substitute for an acquired observation or a success predicate that forces agreement with the paper.

The core deliverable is the paper-derived manipulation task chain. Preserve the
whole experimental sequence and its scientific conditions while expanding the
hands-on work: manipulated objects, contact regions, tools, retained support,
observable completion and recovery. Perception, planning, instrument processing,
waiting and analysis retain their causal roles without being counted as physical
manipulation. Acceptance of a task design is separate from qualified equipment
geometry, robot execution and reproduction of the paper's numerical results.
Do not require a physics simulator or successful scientific replication merely
to document a missing manipulation step; reconstruct that work with explicit
provenance and keep its actual implementation/validation status visible.

## 1. Conversion stages and reviewable outputs

| Stage | Author work | Saved output | Exit check |
| --- | --- | --- | --- |
| Source inventory | Identify the paper/version; inspect main text, Methods, necessary SI, figures and relevant media; record unavailable sources | Source identity, reading/access inventory and evidence locators | Every source has an honest inspected/missing scope; DOI duplicates and rights checked |
| Experimental coverage | Inventory experimental goals, preparation, conditions, controls, repeats, analysis and closeout; classify physical and nonphysical branches | Coverage matrix and branch inventory | Every declared source branch has a disposition and required completion scope |
| Resources and states | Identify materials, lots, specimen parents/children, tools, equipment configurations, fixtures, stations and consumables | Resource inventory, initial state and lineage contract | Initial objects are available or produced by explicit prerequisites; final specimens do not appear for free |
| Task planning | Work backwards from required final states, then resolve causal dependencies, resource constraints, alternatives and repeated work | Dependencies, branch/loop contracts and a valid reference plan | Every required state has a producer; all prerequisites can be supported by the initial state or prior work |
| Robot decomposition | Expand scientific stages into observable robot operations and the device-owned processes they enable | Operation records and reconstruction-inference ledger | The robot's movement, contact, perception and decisions are explicit; no missing hands-on work is hidden in a service |
| Bind and instantiate | Map operations to real equipment parts, scene states, tools and observation interfaces; specify condition/sample allocations | Asset bindings and episode input contract | Every required interaction has a binding or named blocker; unknown counts/settings remain unresolved inputs |
| Evaluate and review | Define trusted completion, negative cases, recovery and actor visibility; perform branch walkthroughs and applicable tests | Evaluator reference, actor projection, recovery and verification records | Valid alternatives, failures, hidden state and incomplete branches are handled honestly |
| Freeze and integrate | Version the task package, preserve its source files, add a lossless viewer adapter and verify derived exports | Package manifest, exact file hashes, viewer JSON/JS/SVG/Markdown and release records | References resolve, source semantics are preserved, claimed readiness matches evidence |

A package may remain a draft while source or execution inputs are unresolved. It must still enumerate the missing work and its consequences. Passing a later display or JSON check does not retroactively complete an earlier source, planning or manipulation gate.

## 2. Plan from experimental goals to robot actions

### Define the goal and work backwards

For each physical branch, write the required final laboratory, specimen and record states, including returned objects, released fixtures, archived data and cleanup. Treat each measurement/control as an obligation with a specimen, condition and calibration identity. Ask which operation produces each required state and which states and resources that operation consumes or requires. Continue until reaching the declared initial inventory or an explicit unresolved input.

Distinguish producing a specimen from merely declaring it available. A fabrication stage can create a child specimen only after its material, tooling, preparation and device process obligations have been represented. Track destructive tests, irreversible treatment, replacement parts and calibration invalidation while planning; later tasks cannot reuse an incompatible or consumed state.

### Build a partial order, then choose reference routes

Save a causal dependency graph with stable operation/occurrence IDs, required state predicates and the reasons for edges. Represent an AND prerequisite, an exclusive preparation alternative, a conditional recovery and a repeated acquisition explicitly. Shared preparation can support multiple branches; independent branches need no invented ordering. A reference route is one valid traversal for review, not the only permitted agent policy or the recovered historical human chronology.

Represent loops separately from the acyclic causal graph: record the loop body, variable, condition values or input-bound count, specimen reuse/reset rules and stopping condition. Give each actual branch/iteration/attempt a distinct occurrence identity when instantiated. Unknown repetitions must not silently become one pass or an empty successful loop.

Resolve resource feasibility before expanding routes. Track station/device capacity, exclusive leases, tool compatibility, carriers, available quantities, sample allocation, calibration/configuration validity and connected cables/tubes. Insert the actual transport, docking, mounting, reconfiguration, release and return operations needed at every station transition. A new station name in metadata does not move an object.

### Decompose until each physical action is inspectable

Use a hierarchy: paper campaign -> branch/control package -> experimental stage -> robot operation -> skill/substeps. Stop decomposition at the level where each operation has an identifiable manipulated object/interface, physical action, entry state, observable resulting state and failure response. Do not replace the task description with joint trajectories; exact controller paths can be added by an implementation after frames and geometry are established.

Describe the relevant capabilities explicitly:

- **Perception:** locate and identify the object/part, estimate pose, inspect alignment/seating, read controls/status and detect damage or failed completion.
- **Motion:** navigate or transport between stations, dock, select an approach, move the arm/tool and retract while preserving load support and clearance.
- **Manipulation:** grasp/release, open/close, insert/remove, align/mount/clamp, connect/disconnect, adjust controls and exchange tools or consumables.
- **Planning:** select a condition or valid alternative, allocate specimens/tools, preserve prerequisites and decide whether to proceed, repeat, recover or abort based on observations.

Split compound labels such as "prepare the material" or "mount and measure" until the required physical work is exposed. Distinguish human-like robot work, a configured device's automatic processing, waiting and data analysis. A closed service, receipt or already-completed sample cannot stand in for required robot work. Fully identify genuinely outside-scope work and reduce the declared scope accordingly.

### Fill omissions with traceable reconstruction

Infer omitted handling from experimental principles, actual device resources, geometry and physical constraints. Choose a coherent default implementation and record alternatives. Each inference needs a stable ID, basis, rationale, confidence, affected operations/assets and a validation/revision plan. Keep source facts, reconstruction inferences and unresolved inputs separate at step and parameter level. Unknown force, timing or geometric values can remain inputs to an explicit operation; their absence does not justify omitting the operation.

Simulate the plan symbolically by walking every required branch from the initial state to its declared final disposition. Check object existence, location, grasp/support, attachment, sample lineage, equipment configuration, measurement parents and resource availability at each transition. Retain failed attempts. Repair the plan when a required state has no producer, an object teleports, a fixture cannot be accessed, or recovery relies on the failed condition already being true. This reasoning exercise is not a physical simulation or an execution receipt.

## 3. Required operation content

Use the [operation example](templates/robot_operation.example.json) or an equivalent representation with an explicit field mapping. Every operation must identify:

| Category | Required content |
| --- | --- |
| Identity and scope | Operation ID, parent stage, branch/loop/attempt occurrence context and actor |
| Objects and interfaces | Manipulated entity/version, source/target station, tools, fixtures, equipment part IDs and local frames |
| Preconditions | Actual object/device/calibration/support/resource states required before starting |
| Action and capabilities | Concrete perception, motion and manipulation substeps; observation-conditioned decisions; separate device process/wait |
| Parameters and provenance | Source locators, inference IDs, unresolved input IDs, units and parameter basis |
| Effects | Object location, support/grasp, attachment, device/sample state and lineage changes |
| Completion | Observable predicates and trusted evidence needed to establish those effects |
| Failure and recovery | Detectable failure, stop/hold state, retained history, recovery prerequisite and bounded retry/abort behavior |
| Binding/readiness | Asset/part/skill bindings, implementation level, missing inputs and evidence for any execution claim |

The JSON example is an authored placement illustration with unresolved physical inputs, not a source-derived experiment or runnable controller. Its reference decomposition belongs to the trusted author/evaluator package. An actor receives only the selected task's permitted goals, observations and interfaces, never hidden predicates or the complete reference plan by accident.

## 4. Save the conversion as a versioned task package

Keep the canonical authored conversion under `tasks/<family>/`. Save prose in UTF-8 Markdown and structured records in JSON with explicit schema/version, stable IDs, units and provenance. The following filenames are recommended; their logical roles are required for the declared scope and can be combined or mapped to legacy files in `task_package.json`:

```text
tasks/<family>/
  README.md, TASK_DESIGN.md             # scope, planning explanation and walkthrough
  task_package.json                    # artifact roles, schemas, visibility and version
  source_inventory.json                # inspected sources, locators, facts and conflicts
  coverage_matrix.json                 # source program -> branch/stage/operation coverage
  resources.json, initial_state.json    # materials, equipment, tools, instances and start states
  operations.json                      # operation definitions and substep contracts
  dependencies.json, branches.json     # causal edges, choices, loops and reference plans
  reconstruction_inferences.json       # selected inferred steps/geometry and their basis
  lineage_contract.json                 # batches, samples, components and record ancestry
  control_packages.json, recovery.json  # controls/repeats and failure/closeout paths
  episode_input_contract.json          # instance allocations and unresolved input requirements
  asset_bindings.json                   # task IDs -> versioned scene/part/interface IDs
  agent_visible.json                   # deliberately filtered actor input specification
  evaluator_reference.json             # trusted states, checks and allowed alternative routes
  unknown_inputs.json                  # unresolved inputs, conflicts and affected work
  tests/, VERIFICATION.json            # checks, exact results, limitations and reviewed revision
```

Start the manifest from [paper_task_package.example.json](templates/paper_task_package.example.json). The template documents roles; nulls and example paths are not a complete package. Map each role to actual file paths, JSON pointers where files combine roles, schema identifiers and visibility. Declare excluded/nonapplicable roles with a reason and affected scope instead of silently dropping them. Use canonical units where possible and document conversions at package/scene boundaries.

Keep real instances separate from templates: an operation definition is reusable, whereas a branch/iteration/attempt occurrence binds a specific specimen, tool, station and condition. An episode declaration instantiates a selected route/control package using nonempty, bounded inputs. A campaign accounts for all mandatory branches, controls and shared prerequisites. Never infer completion or specimen counts from the number of definitions, displayed nodes or rendered frames.

Store equipment geometry and its own versioned review under `assets/<asset_package>/`; task bindings pin asset IDs/versions and relevant file hashes. Record which inputs are absent rather than using historical archive locators as local files. Record exact per-file hashes at a freeze; do not hash the manifest inside itself or claim a commit/publish result before it exists. Later corrections create a new revision and review rather than rewriting an earlier receipt.

## 5. Process, validate and publish the package

1. **Check authoring data.** Parse JSON strictly; resolve IDs, file references, units, schema mappings and provenance. Check causal edges for cycles after representing loops explicitly; verify branch/choice/loop semantics, initial inventory, lineage, resource constraints and reachable closeout. Walk all declared paths and record gaps. Required observations are conditions to verify, not prefilled observed states.
2. **Review source and reconstruction.** Check coverage against the actual inspected sources; review inferred handling, selected alternatives, omitted actions and real equipment references. A complete reconstruction claim requires explicit work across the whole declared physical scope, including preparation and recovery.
3. **Review evaluation and visibility.** Exercise meaningful positive/negative bookkeeping or implemented interaction cases: wrong specimen, missing prerequisite, stale calibration, failed mounting, missing control, invalid reuse and interrupted closeout. Keep expected outputs, literature outcomes, future measurements, hidden fault schedules and reference routes out of the actor projection. The current public explorer is author/evaluator material.
4. **Integrate a lossless viewer projection.** The original task files remain authoritative. Add/update an explicit adapter in `viewer/task_explorer_v1/`, register the family and package routing in `build.py`, wire its local data-script loading in `index.html`, and record the correct source pins/scope. Preserve exact operation/branch semantics and source pointers, and extend source-comparison and UI tests as needed. New schemas are not automatically supported. Never invent chronology, measured values or completed loops during normalization.
5. **Generate derived artifacts deliberately.** In a working copy, run `python3 -B viewer/task_explorer_v1/build.py --tasks tasks --only <registered-family-key>`. This writes normalized `data/<family>.json`, a `data/<family>.js` wrapper for local-file viewing, `diagrams/<family>.svg`, `docs/<family>.md` and release metadata. `--only` requires the other registered families' generated data to exist; perform an initial full build from the supported task sources when they are absent. Edit the source package/adapter, then regenerate; do not treat generated viewer records as the canonical task or as a safe actor input. Check the diff for unintended changes to other families.
6. **Verify and publish a scoped revision.** Run the relevant package and adapter tests, then `python3 -B scripts/verify_release.py`. Record actual commands, outcomes, skips, reviewed file hashes and separate readiness decisions in `VERIFICATION.json`/the PR. The release checker parses JSON and tests existing static/display contracts; it does not enforce every authoring role or prove plan feasibility, visual fidelity or robot execution. Publication is established by the actual repository commit.

Any future execution backend needs a separate actor loader, environment state, observation/action interface, controller/device implementation and trusted event/evaluator integration. Package and viewer preparation do not create that runtime. Tests of synthetic records stay distinct from simulated/hardware experiments.

## 6. Worked planning example: specimen mounting and acquisition

This is an authored inert-specimen illustration, not a reconstruction of a named paper. Assume a specimen starts on a supported storage tray, an empty fixture is on another station, and acquisition requires a seated/clamped specimen plus a valid instrument configuration.

Work backwards from an archived record linked to the correct specimen, a returned specimen, an empty/released fixture and an idle station. The reference path is: identify specimen and compatible fixture -> inspect destination/access -> retrieve and secure specimen -> transport/dock -> open fixture -> align and seat -> clamp -> inspect seating -> configure/verify instrument -> start/monitor acquisition -> archive raw-parent records -> stop/release -> unclamp/remove -> return specimen -> restore station. Explicitly transport the holder or other tools if their starting locations require it.

The causal rule is that acquisition requires verified seating and configuration; it is not merely the next item in a list. If seating inspection fails, retain the failed attempt and return to a supported realignment state before a bounded retry; do not issue a completion receipt or fabricate a measurement. A comparison condition needs its own occurrence, condition identity and any required specimen/reset allocation. Bind every object transition to parts and observations, then save the operations, dependency edges, loop/recovery records, source/inference classifications and final-state obligations in their package roles.

## 7. Record acceptance against evidence

The requirements above are manual acceptance requirements. Use [paper_task_review.example.json](templates/paper_task_review.example.json), or an explicitly mapped equivalent, to record the decision for an exact package revision. These templates are examples, not JSON Schema validators; the current release checker does not enforce their fields. A package must declare its actual field semantics and validation coverage. An unsupported or untested schema remains a named integration gap.

### Coverage and provenance must be auditable

Give each coverage obligation a stable ID, source/locator or linked inference, branch/condition context, scope disposition, mapped operation IDs and remaining gaps. Include preparation, controls, repeated work, records and closeout. Use `included_physical`, `included_nonphysical`, `excluded_with_reason` or `unresolved_scope` for dispositions, with an explicit mapping for legacy vocabulary. A disposition is not a completion state. For included physical work, separately record `not_reconstructed`, `partial` or `reconstructed_for_declared_scope`; the last requires an explicit chain including the inferred handling and review of its remaining inputs.

If reporting coverage, state the exact unit and denominator, and list the IDs behind the counts. Report separately: inventoried obligations, obligations with a disposition, reconstructed physical obligations, reviewed bindings and validated execution occurrences. List exclusions and unresolved scope beside the totals. Missing necessary sources prevent a whole-paper completeness claim even if all currently known obligations are mapped. Do not use operation counts as a completeness percentage or reduce the denominator silently when a difficult branch is deferred.

Classify each step and parameter independently as `source_reported`, `reconstruction_inference` or `unresolved_input` (or provide an equivalent field mapping). A source-reported setting does not make surrounding inferred handling source-reported. Every inference must link its physical/source basis, selected assumption, alternatives, affected IDs and proposed validation; a confidence label alone is insufficient. Keep competing source values and locators in a conflict record, explain any selected interpretation, and leave consequential unresolved conflicts as inputs. Never average conflicting settings or invent a numerical default merely to make a package parse or run.

### Gate decisions and blocking examples

Use `not_reviewed`, `pass`, `changes_required` or `not_applicable` per gate. A `pass` needs evidence locators, an actual reviewer/date and the reviewed revision. `not_applicable` needs a reason and the excluded claim; it cannot waive a requirement within the declared scope. A failed test, missing review or source-dependent skip must not become a pass. Draft acceptance can retain blockers with a reduced, explicit accepted scope.

| Gate | Evidence needed for the claimed scope | Example that blocks that claim |
| --- | --- | --- |
| PTR-01 Sources and coverage | Inspected-source inventory, obligation IDs/dispositions, exclusions and unresolved scope | Missing SI is counted as inspected; a control disappears from the denominator |
| PTR-02 Causal and resource plan | Initial/final predicates, producers, shared prerequisites, sample quantities and resource allocations | A fabricated specimen appears without preparation; two destructive tests reuse the same consumed specimen |
| PTR-03 Branches and occurrences | Explicit choices, conditional guards, scoped loops, reset/stop rules and distinct occurrence identities | Unknown repeat count becomes one; a zero-iteration loop satisfies a required acquisition |
| PTR-04 Operations and provenance | Concrete actions, observable success, supported failure states, parameter-level provenance and inference records | "Prepare sample" hides loading and setup; inferred contact force is presented as a paper fact |
| PTR-05 State and recovery walkthrough | Traces across required branches with state/lineage/resource transitions, failure recovery and closeout | An object teleports; a failed grasp is recovered by assuming the object is already held |
| PTR-06 Saved package contract | Resolvable role/path/pointer/schema/version/visibility mapping and declared exclusions | A template placeholder is treated as an actual file; generated viewer data replace the authored source |
| PTR-07 Evaluation and actor boundary | Completion predicates, projection rules, alternative-route treatment and leakage review | A future measurement or reference route reaches the actor; expected paper results determine success |
| PTR-08 Integration and validation | Actual relevant test results, source comparisons where integrated, separate readiness decisions and scoped blockers | Display checks are reported as robot validation; an unregistered schema is called viewer-supported |

Record walkthroughs by branch/condition with starting states, traversed operation/occurrence IDs, predicate producers, resource and lineage changes, final disposition and any first unsupported transition. Cover feasible conditional routes and failure/recovery obligations. For parameterized loops, review the body, reset invariant, stopping rule and permitted boundary cases; do not claim that finite design examples executed every possible allocation or condition. Actual campaign completion still requires evidence for every required instantiated occurrence.

An attempt ending is distinct from operation success. A failed inspection may finish the attempt but cannot satisfy the operation's success postconditions. Recovery starts from the observed failure state, identifies any unknown support/location/attachment state, and reacquires the necessary observations before further manipulation. Supply retry limits and stop/abort conditions as explicit qualified inputs when the source does not determine them. Where timing affects validity, record duration/expiry constraints and their basis rather than treating prerequisites as valid forever.

### Revision and readiness discipline

The review record identifies the base commit, reviewed content hashes, scope, reviewer/date, findings and separate decisions for source completeness, robot design, equipment fidelity, functional validation and whole-paper execution. Hash the reviewed input files; exclude the review record itself to avoid a self-hash. A later publication receipt can link the resulting commit without pretending that commit existed during review.

Changes to source interpretation, coverage, initial state, operation effects, dependencies, sample allocation, asset interfaces or actor visibility require impact analysis and re-review of affected gates and consumers. Preserve the earlier review and record supersession; do not carry its pass forward onto changed inputs. Unaffected evidence may be reused only with an explicit unchanged-content check and scope justification. A review of the standard or its templates does not certify any existing paper package, asset or robot run.
