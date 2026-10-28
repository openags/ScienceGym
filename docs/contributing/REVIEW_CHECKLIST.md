# Readiness Rubric and Pull Request Checklist

Report each applicable gate separately with scope, revision, evidence, reviewer and remaining blockers. The readiness names below are review labels, not implemented runtime enums or automatic CI gates. The paper-conversion and equipment requirements in this checklist are mandatory manual acceptance gates for new conversions/assets and substantive revisions.

## Readiness rubric

- **Source indexed:** identity and lawful source links are recorded; this does not imply reading
- **Source inspected:** each inspected source has its own access and coverage record; absent or unread dependencies remain explicitly uninspected
- **Source complete for declared physical scope:** the full main article and every necessary source dependency were actually inspected, with no blocking missing source; scientific or geometry unknowns may still remain
- **Evidence extracted:** branch dispositions and source locators are complete for the claimed scope
- **Robot design reviewed:** preparation, operations, controls, lineage, observations, recovery and gaps are inspectable
- **Static checks passed:** named syntax/reference/bookkeeping tests passed; record their exact scope and skips
- **Display reviewed:** actual screenshots or browser review establish the stated visual properties; mock-DOM tests alone do not
- **Equipment reference fidelity reviewed:** the identified real product or documented custom apparatus matches the reviewed model's appearance, scale, parts and relevant configurations under the [equipment standard](EQUIPMENT_MODELING_STANDARD.md); recorded inferences, discrepancies and reviewer decisions support the exact claimed scope
- **Functionally validated:** named interaction/state/evaluator implementation passes positive and negative cases; distinguish simulated from hardware tests
- **Whole paper robot execution validated:** every mandatory physical branch, control and shared prerequisite in the declared paper scope completed with trusted event and lineage evidence in a named environment, with no unresolved required execution gate. A selected-route campaign qualifies only for episode execution, never this label
- **Scientific replication supported:** domain-specific materials, calibration, measurement and uncertainty evidence supports this separate scientific claim

Advancement is not automatic. Asset display can improve while task execution remains blocked. Count source records, families, branches, assets, storyboards and validated runs separately.

## Mandatory paper-conversion review

Apply the [conversion workflow](PAPER_TO_ROBOT_WORKFLOW.md) before accepting a new or substantively revised paper task as a complete reconstruction of its declared physical scope. Draft work may remain incomplete when explicitly labeled; file counts or JSON parsing cannot establish completeness.

Record these eight gates as PTR-01 through PTR-08 in the [conversion review record](templates/paper_task_review.example.json), or an explicitly mapped equivalent. Follow the [evidence and decision rules](PAPER_TO_ROBOT_WORKFLOW.md#7-record-acceptance-against-evidence): identify exact reviewed content, coverage denominators/exclusions, evidence locators, reviewer/date, blocking findings and affected gates after changes. A completed attempt is not necessarily a successful operation. Template placeholders and this checklist alone do not establish acceptance.

- [ ] Source inventory and coverage dispositions account for preparation, all declared experimental branches, controls/repeats, nonphysical work and closeout
- [ ] Required final states were traced backwards to resources and producers; initial inventory, causal prerequisites and resource/sample allocations support a valid plan
- [ ] Dependencies, exclusive/conditional branches, loops/reset and occurrence identities have explicit semantics; no invented source chronology or silently expanded repeat counts
- [ ] Operations expose perception, motion, manipulation and decisions, with objects/tools/stations, preconditions, observable effects, failure/recovery and source/inference/input classifications
- [ ] Branch walkthroughs retain specimen/component identity, actual transports, calibration/configuration validity and safe final disposition; closed services and mock events do not hide required hands-on work
- [ ] A package manifest maps the required artifact roles to actual files/pointers, schemas, versions and visibility; source packages and derived exports remain distinguishable
- [ ] Actor inputs exclude evaluator plans, hidden states, future records and literature outcomes; operation templates, instantiated episodes and campaign completion are distinct
- [ ] Viewer integration has an explicit adapter and source-equality tests where claimed; meaningful positive/negative checks and actual readiness decisions are recorded

Keep the planning/completeness gate open for missing action chains, states without producers, unexplained object creation/movement, unsupported specimen reuse, unbounded or silently skipped work, missing artifact roles or actor/evaluator leakage. A symbolic walkthrough supports design review only; it does not prove physical execution.

## Mandatory humanoid execution review

Apply the [current embodiment requirements](../PROJECT_VISION.md#humanoid-execution-target)
before crediting any new episode toward the final humanoid sample. Historical
Panda tests retain their original scope and confer no humanoid execution credit.

- [ ] Exact Unitree body and selected left/right hand variants, source revisions, licenses, mounting and control interfaces are pinned and qualified; publicly supported hands from other manufacturers are allowed under the owner's current selection policy
- [ ] Actual hand joints, contact geometry, masses, limits and tactile/observation assumptions are recorded; the humanoid is the physical actor
- [ ] Each step binds the acting/supporting hands, grasp, tool, fixture and observable support transfer; two-hand coordination and tool pickup/return are explicit
- [ ] Whole-body reach, self/environment collisions, standing support, load distribution and stability are checked throughout the recorded operation
- [ ] Continuous object and tool identities survive releases, handoffs, failures and station transfers without pose resets or hidden human work
- [ ] Independent physical verification, perturbation/fault cases and full-episode playback cover the declared humanoid scope; no arm-only receipt is counted as whole-body acceptance

## Mandatory equipment review

Apply these checks to every new or substantively revised equipment item, including assets-only PRs. Complete the [equipment review record](templates/equipment_modeling_review.example.json), or map equivalent evidence to every required category. A draft with missing evidence can be submitted for discussion; it cannot be accepted as faithful equipment or counted in accepted fidelity/interaction coverage. Historical static acceptance does not grant this new label.

- [ ] Manufacturer, exact model/part number, generation/options and paper configuration are identified with locators; custom parts and unresolved identities are separate
- [ ] A dated search log covers official product/manual/dimension/CAD resources and multiple real views, including unsuccessful searches and reuse rights
- [ ] Geometry follows the real device's silhouette, proportions, component layout, materials/colors and task-relevant details; a generic labeled shell is rejected
- [ ] Dimension evidence, physical/display scales, local frames, moving parts and every reconstruction inference are explicit
- [ ] Reference/model comparisons cover available front/side/rear views plus task access surfaces, controls, connectors, fixtures and relevant state variants; missing views and discrepancies have explicit reviewer dispositions
- [ ] The full hands-on chain maps to parts, motion/manipulation, observations and state changes; service boxes, mock receipts and appearing parts do not replace required actions
- [ ] Reviewers inspected the actual evidence and recorded separate identity, appearance, scale/structure and interaction decisions against exact model hashes, with date and blockers
- [ ] Static, functional, collision/reachability and scientific claims remain scoped to the checks actually performed

Request changes for a known task-critical mismatch, missing resource/identity evidence, distorted scale, absent operating parts or missing reference comparison. An "illustrative", "original" or "unqualified" disclaimer does not clear these findings. Record unresolved views/inferences without inventing evidence or approvals. Visual fidelity can pass while functional execution remains blocked, but neither a static check nor a review of documentation alone establishes visual fidelity.

## Laboratory scene review before pilot manipulation development

For the directional-cooling pilot, the owner explicitly requires acceptance of
all assets and laboratory scenes before new manipulation-sequence development.
Apply [section 7 of the equipment standard](EQUIPMENT_MODELING_STANDARD.md#7-whole-laboratory-asset-and-layout-acceptance).

- [ ] LAB-01: All required equipment, accessories, materials, tools, intermediate states and physical instance counts are reconciled against the paper scope
- [ ] LAB-02: Each asset has reviewed identity, source comparison, dimensions, parts, rights and marked reconstruction assumptions
- [ ] LAB-03: Indoor, fabrication/coating, calibration, optical, storage and outdoor requirements have explicit spatial dispositions and modeled supporting facilities
- [ ] LAB-04: The dimensioned plan agrees with physical-scale scene geometry, support capacities, doors, equipment states and service access
- [ ] LAB-05: Pinned full-body/hand and carried-load envelopes cover transit, turns, bilateral work and station approaches, with measured worst-case clearance and collisions
- [ ] LAB-06: Hazard controls, electrical/wet separation, cables/hoses, access/egress, emergency provisions and relevant manufacturer/site requirements have reviewed evidence
- [ ] LAB-07: Interactive scene views, asset comparisons, spatial reports and unresolved findings refer to exact reviewed content
- [ ] LAB-08: The owner has accepted the completed asset/scene revision; the decision, scope and date are recorded before manipulation development resumes

Missing geometry or unverified safety-critical spacing remains an open gate.
A body-only movement test, room screenshot or generated checklist does not
constitute acceptance of the laboratory.

## Pull request checklist

- [ ] Linked issue identifies contribution track, owner and exact scope
- [ ] DOI/version or asset identity was checked for duplicates
- [ ] Source access, inspected scope and redistribution rights are recorded
- [ ] Source facts, authored choices, conflicts and unknowns remain distinct
- [ ] Whole-paper dispositions include preparation, controls and nonmanual work
- [ ] Paper conversions satisfy the mandatory planning, artifact-role and processing review gates
- [ ] Hands-on steps identify actor, object, tool, station, interface and evidence
- [ ] Omitted source handling is reconstructed into an explicit chain; inferences include basis, assumptions, alternatives and validation needs
- [ ] Branches, repeats, destructive allocation and sample histories are consistent
- [ ] Actor-visible inputs exclude evaluator answers and future observations
- [ ] Asset scale, frames, states, affordances and provenance are documented where applicable
- [ ] Equipment contributions satisfy every mandatory equipment review gate, with an evidence record and explicit decisions
- [ ] Pilot scene contributions satisfy the laboratory review gates before new manipulation development resumes
- [ ] Commands, results, screenshots and revision-specific receipts support only the claims made
- [ ] Gaps, unavailable checks, changed IDs and compatibility effects are stated
- [ ] No secrets, local-only paths, unauthorized source material or unsupported execution claims are included
