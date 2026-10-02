# Explicit schema adapters and fidelity rules

The explorer does not infer one universal operation schema or invent a global task DAG. `build.py` has a dedicated adapter for each of the seven published packages.

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
