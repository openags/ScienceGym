# Readiness Rubric and Pull Request Checklist

Report each applicable gate separately with scope, revision, evidence, reviewer and remaining blockers. The readiness names below are review labels, not implemented runtime enums or automatic CI gates. The equipment requirements in this checklist are mandatory manual acceptance gates for new equipment and substantive revisions.

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

## Pull request checklist

- [ ] Linked issue identifies contribution track, owner and exact scope
- [ ] DOI/version or asset identity was checked for duplicates
- [ ] Source access, inspected scope and redistribution rights are recorded
- [ ] Source facts, authored choices, conflicts and unknowns remain distinct
- [ ] Whole-paper dispositions include preparation, controls and nonmanual work
- [ ] Hands-on steps identify actor, object, tool, station, interface and evidence
- [ ] Omitted source handling is reconstructed into an explicit chain; inferences include basis, assumptions, alternatives and validation needs
- [ ] Branches, repeats, destructive allocation and sample histories are consistent
- [ ] Actor-visible inputs exclude evaluator answers and future observations
- [ ] Asset scale, frames, states, affordances and provenance are documented where applicable
- [ ] Equipment contributions satisfy every mandatory equipment review gate, with an evidence record and explicit decisions
- [ ] Commands, results, screenshots and revision-specific receipts support only the claims made
- [ ] Gaps, unavailable checks, changed IDs and compatibility effects are stated
- [ ] No secrets, local-only paths, unauthorized source material or unsupported execution claims are included
