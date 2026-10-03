# Repository README integration

Copy this complete folder to `viewer/task_explorer_v1/`. Keep the repository LICENSE unchanged. The existing top-level quick route preview can remain; add this compact section near it:

```md
## Explore the paper-level tasks

[Download/open the offline task explorer](viewer/task_explorer_v1/README.md) to choose a branch and inspect robot actions, objects, sample states, source evidence and recovery. No installation or server is needed after download.

Eight GitHub-readable route maps: [Chiral](viewer/task_explorer_v1/docs/chiral.md) · [Deconwolf](viewer/task_explorer_v1/docs/microscopy.md) · [Fibres](viewer/task_explorer_v1/docs/fibre.md) · [Thermoelectric](viewer/task_explorer_v1/docs/thermoelectric.md) · [diSPIM](viewer/task_explorer_v1/docs/dispim.md) · [Acoustics](viewer/task_explorer_v1/docs/acoustic.md) · [Perovskite](viewer/task_explorer_v1/docs/perovskite.md) · [Prismatic](viewer/task_explorer_v1/docs/prismatic.md)

The author/evaluator logical inspector contains 172 route/configuration records and 1,267 operation definitions across eight paper-level families. These are public task-design references, with source-reported stages, authored robot handling and unknowns distinguished. They are not executed robot trajectories or a new 3D storyboard. Loop bodies and repeated operations remain explicit; unknown loops are not expanded. Prismatic operation membership is governed by partial-order constraints, with nested condition/target coverage, independent campaign branches and conditional recovery.
```

All source links are pinned to the reviewed task snapshot [e27d456e2fe99bec9100cc37f7bcd68485504c2b](https://github.com/openags/ScienceGym/tree/e27d456e2fe99bec9100cc37f7bcd68485504c2b). GitHub displays `.html` as source, so link the guide for the offline viewer and the Markdown/SVG maps for immediate on-page inspection.
