# Independent review and corrections

An independent source/evidence reviewer read the source audit, retained main text, SI text and relevant SI panels, reopened the canonical public HTML for the missing text range, inspected package contracts, and reran checks read-only. This is a design/evidence review, not laboratory or execution certification.

The review confirmed the physical/numerical boundaries, separately identified signal and memory populations, monostable AU versus bistable ReIM, two-row volatile storage, three-row switch limit, source incompleteness, and the stopped main PDF route.

Corrections applied:

- Retention baseline is post-write and before upstream release, from the same hold epoch
- SI Fig11 scale bars are acknowledged without treating them as complete dimensions or CAD
- Mechanical proof has its own MECH_CAL and MECH_READ rather than an electrical row-state dependency
- Terminal cleanup is included in branch operation membership and checked
- A parity bridge is either verified in an existing AU or installed as a declared one-for-two conversion; no implicit second bridge
- Full Boolean-case coverage is required for a complete truth-table route
- Both storage elements must belong to the checked specimen lineage; revision and quarantine apply to each
- Stored source cross-reference errors in SI Fig9/10 are noted rather than silently repaired into new evidence
- Actor inputs exclude expected outputs and reference documents

The final independent rerun passed all 87 tests, the static verifier, and the exact 33-file export/hash boundary. The reviewer found no remaining design-review blocker. Review-status metadata was subsequently finalized and hashes were regenerated; the final export verification is recorded in VERIFICATION.json.

Known implementation limits remain intentional: there is no live loader or authenticated event backend. Synthetic row checks establish event presence, row cardinality and limit flags, not complete contact-sequence physics. Declared continuity and prepared-handoff dictionaries are synthetic consistency evidence, not instrument authentication. No visual scene, model, measured hardware data or robot execution exists in this package.
