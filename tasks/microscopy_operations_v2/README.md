# Microscopy operations v2

中文入口：[GUIDE_ZH.md](GUIDE_ZH.md)。 Detailed specification: [TASK_DESIGN.md](TASK_DESIGN.md).

One Deconwolf paper-wide task-design package: six preparation/imaging branches and seven source-data comparison branches. Unlike the earlier single-route contract, routine sample preparation, transport, mounting, controls, acquisition and cleanup are explicitly in scope. Missing source facts are labeled task bridges, not invented paper facts. Scientific outputs are preset by design; no physics is required.

Agent-facing files: `initialstate.json` and `agentgoal.json`. Keep `evaluator_reference.json` separate from the agent. The other JSON files specify source-bound operations, reusable geometry, authored affordances, preset observations, recovery and coverage.

No runtime or experimental success is claimed. No new CLI/test framework was added. Prior files are preserved.

Asset paths describe the original full-workspace layout. This public task-only snapshot does not include the referenced microscopy models or scenes, so those paths do not resolve here. The source-archive:/// locator in source_bindings is nonresolving historical provenance; raw publisher sources are not bundled. See ../../EXPORT_NOTES.md for current boundaries.
