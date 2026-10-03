# Contributing Paper Derived Robot Tasks

The output is an auditable description of a paper's physical experimental program. A protocol summary is only an input to that work. Start from source evidence and end with explicit robot actions, object histories and completion conditions.

## Establish source identity and permission

Claim a DOI-backed issue before extensive conversion. Record the title, authors, formal journal title, DOI, publisher URL, publication/version date and any correction, retraction or updated supplement found during inspection. Check whether a related preprint or existing family already covers the same work; link it and explain the incremental contribution.

List the main article, Methods, SI, relevant movies, data and code separately. Record the access method/date, which content was actually read, and exact figure, page or section locators. Hash files only when those exact bytes were obtained lawfully; a web-reader inspection must not acquire an invented PDF hash. Mark an absent supplement as missing, not inspected. Check linked corrections and supplement versions before freezing the evidence record.

Open access and redistribution rights are separate checks. Record each source's license and permitted reuse, including exceptions for third-party figures. Prefer concise paraphrases and locators. Do not commit publisher PDFs, screenshots, source text dumps or datasets merely because they were readable. The repository's Apache license does not relicense those materials.

## Map the whole reported program first

Inventory every experimental Methods section, result figure/panel and required supplement. For each, assign a disposition: physical branch, prerequisite, control, repeated acquisition, analysis-only, simulation/theory, external comparison, duplicate evidence, or excluded/gated with a reason. Link every physical branch to evidence and operation IDs. Include preparation and fabrication upstream of the headline measurement, as well as calibration, archiving and shutdown downstream.

Separate reported scientific facts from authored embodiment. A paper may establish that two components were joined without specifying the robot's fixture, grasp or attachment method. Those are authored choices or unresolved inputs, not source facts. Do not infer a historical serial identity, operator chronology, repeat count or complete manufacturing drawing from a schematic.

Build a dependency graph and branch inventory before expanding action sequences. Distinguish mandatory prerequisites from an illustrative order. Represent conditions and bounded repeats explicitly. Track independent specimens, repeated measurements of one specimen, time samples and repeated loading cycles separately. A curve with many points does not imply that many samples.

An operation-ID list may express branch membership rather than chronology; explain which it means. Repeated uses of one operation need distinct occurrence IDs or equivalent branch/iteration context so records cannot collapse separate actions. Unknown repeat counts must not become zero, one or a successful empty loop. Keep them gated until a qualified instance input supplies a bounded schedule.

Allocate destructive tests before scheduling reuse. A parent batch can yield identified sibling specimens; a destroyed specimen cannot reappear in a later measurement. Shared preparation, material variants, paired controls, failed attempts and reconfiguration need persistent identity. State campaign completion as required branches and comparison packages, not a sum of operation counts.

## Write observable robot operations

For every hands-on step, specify:

- **Identity and actor:** stable operation ID; robot, automated device or explicitly declared outside-scope actor
- **Resources:** manipulated objects and current versions, tools, source/target station, fixture and interface
- **Action and process:** physical robot actions separately from the device's automatic process and waiting
- **Preconditions:** correct inventory, current calibration, compatible state, qualified inputs, isolation and interlocks
- **Postconditions:** changed location, attachment, material/specimen state, component membership or acquired record
- **Evidence:** public readbacks or inspections and authoritative completion receipts; source evidence IDs and provenance class
- **Structure and failure:** dependencies, branch/loop context, unresolved gate IDs, detectable failures, safe stop and recovery

“Prepare sample” is insufficient. Describe retrieval, identification, supported transport, fixture loading, tool/interface use, setup verification, device start/readback, safe release, unloading and inspection where relevant. If the source omits parameters, name the input card needed. Do not invent recipes, tolerances or hazardous instructions to make the prose look complete.

Use a gap ledger with an ID, missing/conflicting information, source search performed, affected branches/operations, consequence, proposed resolution and owner if agreed. Distinguish a draft limitation from an execution gate. Unknowns can remain explicit in a reviewed design; operations requiring them cannot claim execution readiness. An unrelated branch can proceed if its dependency closure is complete.

## Use an existing package without assuming a universal schema

The cooling reference is `tasks/directional_cooling_operations_v2/`. Its files provide a practical model:

- `TASK_DESIGN.md` and `README.md`: scope, narrative, limitations and inspection instructions
- `provenance.json`, `source_access_audit.json`, `source_conflicts.json`: identity, evidence, access and disagreements
- `coverage_matrix.json`, `branches.json`, `nonmanual_scope.json`: coverage and dispositions
- `operations.json`, `dependencies.json`, `station_contracts.json`: action and station contracts
- `material_cards.json`, `lineage_contract.json`, `control_packages.json`: resources, histories and comparisons
- `unknown_parameters.json`, `episode_input_contract.json`, `asset_needs.json`: required inputs and unbuilt interfaces
- `agent_visible.json`, `evaluator_reference.json`, `mock_contract.json`, `source_outcomes.json`: visibility and evaluation boundaries
- `tests/`, `STATUS.json`, `VERIFICATION.json`: checks and scoped status receipts

For a new family, propose `tasks/<descriptive_family>_operations_v2/` in its issue and adapt this structure. The suffix is a naming example, not a schema compatibility guarantee. Remove irrelevant inherited content, replace every source identifier and describe the chosen schema/version in the README. Existing microscopy uses different names, including `agentgoal.json`, `initialstate.json` and `operation_sequences.json`; diSPIM uses uppercase filenames. Preserve existing contracts when extending them rather than renaming everything to imitate this guide.

## Worked contribution using cooling film assembly

In the current cooling package, `FILM` is a design-only operation at `WS_ASSEMBLY`. It depends on `LAYOUT`, manipulates two identified film sheets and a spacer ring, uses edge supports and qualified attachment tools, and produces a versioned two-layer cover. Its source evidence is `E_BUILD`/`E_FIXED`; fabrication and geometry gaps are `U_FAB`/`U_GEOM`. Robot handling is explicitly authored rather than a source-demonstrated trajectory.

A useful small PR would refine this contract and request its missing holder asset. Keep the two film IDs separate. Describe locating the supported ring, inspecting each sheet, presenting it at the declared support edges, attaching it to the correct spacer face under a qualified card, then checking the gap and integrity. These are proposed authored refinements, not newly recovered source instructions. Leave attachment force, tolerance and unsupported geometry unknown until qualified.

Add a successful synthetic bookkeeping case and negative cases for a missing second film, wrong film type, torn film and inspection tied to an old assembly version. Preserve failed attempts; a replacement sheet receives its own identity and increments the assembly version. Bind the future asset's support regions and attachment frames to `FILM`, and require downstream inspection before a valid run. This is a reviewable task-and-asset handoff even while manipulation and deformation are unimplemented.

## Protect the actor boundary and test the claim

The actor may receive the goal, current inventory, qualified operating cards and observations already acquired. It must not receive reference routes, hidden fault schedules, future measurements, literature target outcomes or evaluator answer keys. Authored mock output must be labeled and must not masquerade as measured science. An evaluator should check authoritative state and events, accepting equivalent valid routes rather than only one sequence.

Run from the repository root:

```sh
python3 -B -m json.tool tasks/directional_cooling_operations_v2/operations.json
python3 -B -m unittest discover -s tasks/directional_cooling_operations_v2/tests -v
python3 -B scripts/verify_release.py
```

The first command only parses/prints JSON. The second runs this package's static and synthetic-record tests. The third runs repository checks; it does not discover all package suites. Inspect unfamiliar test scripts before invoking them: some package entry points regenerate tracked reports. Record the command, environment, revision, result and limitations; preserve source-dependent skips as skips. Tests of synthetic bookkeeping do not establish a trusted runtime event logger, robot feasibility or scientific replication.
