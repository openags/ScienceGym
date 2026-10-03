# Explicit schema adapters and fidelity rules

The explorer does not infer one universal operation schema or invent a global task DAG. `build.py` has a dedicated adapter for each of the nine published packages. The previous eight families retain their source-schema semantics. The EmVP adapter adds 19 configuration records and 53 operation definitions, bringing the explorer totals to 191 and 1,320 respectively.

## Chiral

- Reads `operations.json`, each branch's `operation_sequence`, and `dependencies.json`
- Copies every route occurrence in order
- Includes declared branch independence, resource mutexes and comparison joins
- The explicit adjacency list is already represented by the exact branch sequences; its original file is linked rather than duplicated
- Source numeric result fixtures are available in the original branch JSON. They are not used as operational success targets

## Thermoelectric

- Uses `full_operation_sequence`, with phase material bindings and condition loops retained separately
- Preserves all repeated phases and the declared independent P/B or P/N partial-order freedom
- Keeps MOVE insertion and condition-grid iteration as explicit obligations; it does not invent inserted nodes or silently complete a grid

## Fibre

- Uses `full_operation_sequence` verbatim, including repeated P/N manufacturing prefixes
- Retains independent specimen/destructive sibling rules, object history, application cardinality and transport obligations
- A stored prefix is not treated as enough material to create eight objects unless its source contract says so

## Acoustic

- Combines explicit `prelude`, declared `phases`, and `epilogue` without expanding or removing loops
- Three step object schemas have dedicated handling: `loop_variable/values/body`, `set_condition/steps`, and `verify_condition/evidence`
- Every loop value binding and completion rule is retained verbatim. Unknown/null input references stay unresolved
- Partial-order constraints remain source-provided semantic predicates, not guessed operation-ID edges
- The complete practical route is the default preview. Shared microphone/source-chain exclusion is retained

## diSPIM

- Maps `OPERATIONS.json` fields explicitly, including `source_fact`, `authored_robot_handling`, source step numbers, repeat contracts and provenance kinds
- Uses all seven `BRANCHES.json` route templates; original stage branch entry/exit contracts remain in the dependency view
- Keeps P001/P004 occurrences distinct in the complete embryo route
- Imports the first complete route's completion evaluator and source-step coverage as reference contracts
- Preserves the accepted-manuscript version caveat and unresolved source issues

## Deconwolf microscopy

- Adapts each preparation step using its explicit precondition/output state, source parameters, transition evidence, unknowns and interaction macro
- Macro actions come from `interaction_design.json`, retained once per family and resolved when a step is opened
- Acquisition variants are grouped as obligations. This visual grouping does not invent order among variants; explicit `order` text remains in provenance. Branch-required and allowed-optional choices remain in the evaluator branch contract
- Each wet-lab branch includes the existing authored unload macro and its source-bound analysis list, following the original handling sequence
- IDs ending `__unload` and `__analysis`, and data IDs ending `__action_N`, are **inspector navigation IDs**, not extra paper-reported operations. This explains the 132 displayed operation definitions
- Data-workstation action lists are unordered obligations; no per-action state predicates are fabricated

## Compact encoding

`nodes` arrays contain either scalar operation IDs or typed group objects. A scalar repeated twice is two reference occurrences. Group objects retain `children` plus verbatim loop/phase metadata.

Repeated long operation values and route-detail values use `{ "$shared": N }` references to the family's `shared` array. This is lossless value pooling, not summarization. `app.js` decodes the pool before display. The JSON and local-script data payloads are identical after removing the assignment wrapper.

The adapter omits repeated raw records where their fields are already mapped and avoids copying large source-result fixtures that are not task actions. Exact raw record pointers and immutable file links remain visible. All robot-action lists, loop bodies, declared route occurrences and state/acceptance/recovery content used by this view are retained.

## Boundaries

This viewer cannot establish scientific correctness, practical safety, source completeness, actor information separation, task-loader validity or robot feasibility. It never mutates a sample state, emits an execution event or marks a branch complete. All reference/evaluator content is public for inspection and must be projected out of any future actor prompt.

## Perovskite solar modules

- Copies all 40 route templates and their 752 authored action definitions, including unexpanded condition and replicate obligations
- Preserves every top-level unknown ID; these are not nested under provenance in this schema
- Binds each action to its source service card using the longest matching service-ID prefix; complete service, material and condition records remain available
- Per-operation target-asset lists are absent in the source schema and are explicitly marked as such, not fabricated
- Retains all seven textual partial-order predicates as text. A predicate is not converted into an invented pair of operation-ID edges
- SPIN_MODULES is the default reference route. It does not establish completion of the entire paper
- The larger perovskite payload has a 1.5 MB guard because it retains 752 definitions and all detailed service/condition contracts; each earlier family retains its 200 kB guard

## Prismatic metamaterials

- The prismatic payload has a 400 kB guard because it retains complete evaluator/lineage/control/audit contracts plus independent campaign nesting; earlier family payload guards are unchanged
- Maps all 49 operation definitions and all 12 branch/configuration records across seven practical families. Complete working contracts are retained for author/evaluator inspection, including branch and dependency rules, episode inputs, lineage, controls, evaluator acceptance, station/material/asset requirements, unknowns, coverage and nonmanual scope, mock boundaries, provenance, source outcomes/conflicts, the independent source audit and release-boundary metadata. Remaining export/verification files retain pinned source links and checksums
- Preserves each original `operation_ids` list as **membership**, governed by explicit dependency edges and branch-stage predicates. The list is not a chronological route, a fixed robot trajectory or a universal specimen history
- Keeps source `loop_expansion` contracts and typed loop metadata, including joint/face setup loops, cyclic loading/unloading and nested target attempts. Unknown values/counts remain unresolved; they neither expand into invented occurrences nor count as successful empty loops
- Preserves the cube comparison's **material × target × attempt** nesting and the array comparison's **thickness × target × attempt** nesting. Flattening either into sibling loops would lose the required Cartesian coverage
- Treats `WHOLE_PAPER_PRACTICAL` as dispatch to eleven independent component branches, each with its own nested loops, sample identities and conditions. No cross-branch chronology is inferred, and the campaign's union of operation IDs is not executed as one sequence
- Keeps `QUARANTINE` separately labeled as **conditional recovery**. It remains an inspectable operation definition but is not inserted as a mandatory step in every branch
- Carries top-level operation unknown IDs, evidence IDs, pre/postconditions, authored action lists and recovery text without moving unknowns into source-reported facts. Reported source outcomes remain evaluator context and never become operational success targets
- Explicitly labels the absence of per-operation object-role lists in the source schema. Material cards and asset needs remain available as source contracts; they are not converted into invented per-operation target roles
- Preserves required transfer insertions, qualified-input gates, specimen allocation and reuse history, upstream fabrication/handoff requirements and incomplete/blocker status. The inspector does not satisfy any of these obligations
- Retains the actual-final-five-cycle aggregation contract, source conflicts and bounded pneumatic scope. Five summary cycles do not supply the unknown total cycle count; four reported pneumatic states do not establish four programs or specimens

The pinned source is [openags/ScienceGym at 293e32da790303c1a17131e036235f69a5f342e0](https://github.com/openags/ScienceGym/tree/293e32da790303c1a17131e036235f69a5f342e0). This is logical-inspector coverage only; it adds no task execution or new 3D storyboard.

## Embedded extrusion-volumetric printing (EmVP)

- Maps all 53 operation definitions and all 19 configurations across five practical families with an explicit adapter for the distinct EmVP schema. `label`, `station`, `physical_action`, `completion_evidence`, `required_unknowns` and `source_refs` are mapped directly. String provenance and operation kind are retained. Missing postconditions and object-role fields are labeled absent rather than fabricated
- Preserves the complete 44-edge dependency list, six conditional groups containing 25 edges, instantiation rules and per-occurrence predicates. Operation-list positions are source-authored viewing order only; no adjacent operation arrows are drawn. Conditional groups retain both their configuration scope and their condition predicate
- The cage comparison retains the exact Mat1-only, Mat2-only and combined-material subroutes, including condition-scoped input gates. The first two use direct VAM; the third uses embedding. All are required comparison conditions with separate allocations, not extra configurations or a serial path for one vial
- Retains all 15 comparison packages and their outer allocation / inner observation levels. These coverage contracts are separate from operation membership because the source does not supply per-dimension operation bodies. No manufacturing sequence is wrapped inside a state-observation loop
- Explicit condition axes, ordered same-specimen states, within-specimen hardness sites and null specimen counts remain unchanged. No cardinalities are expanded; missing values do not imply zero, one or successful empty work
- Retains all 30 unresolved gates, independent source audit, lineage, evaluator/actor boundaries, geometry and instrument qualification requirements, nonmanual handoffs, source conflicts, outcomes and status metadata. Source outcomes remain reference context and never become episode measurements or forced success targets
- Resolves source locators to the original MAIN/SI document metadata and links without copying paper pixels or source PDFs. Top-level and nested public JSON records retain immutable source links and SHA-256 checksums
- Uses a 400 kB payload guard; existing family guards are unchanged. The static SVG previews POSITIVE_HELIX; every configuration and comparison remains available in the Markdown and interactive reference inspector

This integration adds no simulator, loader, evaluator execution, actor projection, scientific solver or robot controller.
