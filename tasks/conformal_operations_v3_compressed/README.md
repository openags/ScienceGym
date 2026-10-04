# Conformal operations v3: compressed-scene pairing

Original English ScienceGym whole-paper task-design package for [Czajkowski et al. (2022)](https://doi.org/10.1038/s41467-021-27825-0). Accepted source review covers nine main pages, sixteen written SI pages and the media-description sheet. All three movies were decoded and five frames from each visually sampled; Zenodo archive contents remain unread.

The package contains sixteen operation templates, nine branches, eight station contracts, twelve paired asset families, nine controls, sixteen unresolved-input groups and five preserved scientific conflict groups. Two branches are physical compression/decompression experiments. Numerical and theoretical branches are explicitly documented but unexecuted.

This is an original design with finite synthetic metadata tests. It is not an executable robot controller, mechanics simulation, fabrication drawing, safety-qualified procedure or scientific reproduction. One paper design is represented; the validated runnable whole-paper task count remains zero.

Read TASK_DESIGN.md, RELEASE_BOUNDARY.json and unknown_parameters.json first. The original scene is separately distributed as conformal_scene_assets_v2_compressed. Only agent_visible.json is designated actor context; filesystem isolation and real sensor authentication are unimplemented.

Run from this directory using Python 3:

    PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
    PYTHONDONTWRITEBYTECODE=1 python tests/verify_package.py
    PYTHONDONTWRITEBYTECODE=1 python tests/verify_export.py
    PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s review -v

Tests use arbitrary synthetic IDs and values. Passing establishes only the stated symbolic checks.

## Storage-only revision
This separate packaging revision pairs the unchanged task design with a losslessly compressed native Blender asset file. Semantic object IDs, operation anchors, scientific claims, execution gates and paper counts are unchanged. The earlier v2 archive and its Library delivery remain intact. This revision adds no paper or runnable-task count.
