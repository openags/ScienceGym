# Readiness Rubric and Pull Request Checklist

Report each applicable gate separately with scope, revision, evidence, reviewer and remaining blockers. These are recommended acceptance labels, not implemented status enums or automatic CI gates.

## Readiness rubric

- **Source indexed:** identity and lawful source links are recorded; this does not imply reading
- **Source inspected:** each inspected source has its own access and coverage record; absent or unread dependencies remain explicitly uninspected
- **Source complete for declared physical scope:** the full main article and every necessary source dependency were actually inspected, with no blocking missing source; scientific or geometry unknowns may still remain
- **Evidence extracted:** branch dispositions and source locators are complete for the claimed scope
- **Robot design reviewed:** preparation, operations, controls, lineage, observations, recovery and gaps are inspectable
- **Static checks passed:** named syntax/reference/bookkeeping tests passed; record their exact scope and skips
- **Display reviewed:** actual screenshots or browser review establish the stated visual properties; mock-DOM tests alone do not
- **Functionally validated:** named interaction/state/evaluator implementation passes positive and negative cases; distinguish simulated from hardware tests
- **Whole paper robot execution validated:** every mandatory physical branch, control and shared prerequisite in the declared paper scope completed with trusted event and lineage evidence in a named environment, with no unresolved required execution gate. A selected-route campaign qualifies only for episode execution, never this label
- **Scientific replication supported:** domain-specific materials, calibration, measurement and uncertainty evidence supports this separate scientific claim

Advancement is not automatic. Asset display can improve while task execution remains blocked. Count source records, families, branches, assets, storyboards and validated runs separately.

## Pull request checklist

- [ ] Linked issue identifies contribution track, owner and exact scope
- [ ] DOI/version or asset identity was checked for duplicates
- [ ] Source access, inspected scope and redistribution rights are recorded
- [ ] Source facts, authored choices, conflicts and unknowns remain distinct
- [ ] Whole-paper dispositions include preparation, controls and nonmanual work
- [ ] Hands-on steps identify actor, object, tool, station, interface and evidence
- [ ] Branches, repeats, destructive allocation and sample histories are consistent
- [ ] Actor-visible inputs exclude evaluator answers and future observations
- [ ] Asset scale, frames, states, affordances and provenance are documented where applicable
- [ ] Commands, results, screenshots and revision-specific receipts support only the claims made
- [ ] Gaps, unavailable checks, changed IDs and compatibility effects are stated
- [ ] No secrets, local-only paths, unauthorized source material or unsupported execution claims are included
