# Repository README integration

## Paired-design and bounded-subset views — 2026-10-04

The explorer now has **32 clearly scoped families: 29 paper-level designs + 3 bounded subsets**, **736 inspection records** and **2,857 operation definitions**. This is not 32 whole-paper designs or 32 runnable tasks. Zero validated runnable whole-paper tasks are claimed.

The four added views retain all 118 source JSON documents, 147 operation definitions and 52 source branch-array entries (including the flow and direction holds), plus one separate qualification hold, one session-teardown view and six conditional-recovery catalog views. Their 60 inspection records are navigation records, not additional experiments or independent specimens. The earlier 28 JSON/JS, SVG and Markdown family outputs remain byte-identical.

| Family scope | Family | Default inspection | All records | Map |
| --- | --- | --- | --- | --- |
| Paper-level design | Laser stabilization | QUALIFICATION_HOLD | [16 records](viewer/task_explorer_v1/docs/laser_control.md) | [SVG](viewer/task_explorer_v1/diagrams/laser_control.svg) |
| Bounded subset | Clean-water solar metrology | RECEIPT, navigation only | [15 records](viewer/task_explorer_v1/docs/solar_water.md) | [SVG](viewer/task_explorer_v1/diagrams/solar_water.svg) |
| Bounded subset | Sucrose optical metrology | FLOW_HOLD | [12 records](viewer/task_explorer_v1/docs/sucrose_metrology.md) | [SVG](viewer/task_explorer_v1/diagrams/sucrose_metrology.svg) |
| Bounded subset | Actuator displacement metrology | DIRECTION_HOLD | [17 records](viewer/task_explorer_v1/docs/actuator_metrology.md) | [SVG](viewer/task_explorer_v1/diagrams/actuator_metrology.svg) |

Laser preserves design-only versus closed-service branches, prepared-intake versus full-preparation lineage, three DFB identities and independent versus in-loop measurements. Sucrose preserves the unresolved flow conflict, three optical profiles, reference wavelength and separate session teardown. Actuator keeps source-direction qualification unresolved, signed coordinate projections, alternative numerical parents and prepared-intake boundaries. Solar stays clean-water/nonbiological with no potability or full-paper claim. Unknowns, exclusions, source access gaps, controls and immutable failure history remain exact.

The family selector and heading explicitly distinguish paper-level design from bounded subset. Every added source JSON is retained in the acceptance/reference context, all operations are inspectable, and original file hashes and immutable links remain available. Source inventories do not invent chronology, default settings, independent replicates, completed services or hardware authority.

Laser, sucrose and actuator views link the existing original 3D asset README and static renders. Solar has no paired original asset bundle in this pinned release. Links do not add interactive web physics, a simulator, device control or a new 3D storyboard. Sources/assets are pinned to [f803612db28652d2e2dd574d8039c36b7136f399](https://github.com/openags/ScienceGym/tree/f803612db28652d2e2dd574d8039c36b7136f399). All 32 task packages, all six asset bundles, both embodied players, scene bindings, LICENSE and scientific source bytes remain unchanged.

This viewer-only integration preserves every task, asset, storyboard, scene binding and license byte. Read `VERIFICATION.md` for the exact static/mock-DOM boundary; real-browser access remains previously denied.
