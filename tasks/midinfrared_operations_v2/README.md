# Mid-infrared operations v2

Original English ScienceGym whole-paper task-design package for [Wang et al. (2023)](https://doi.org/10.1038/s41467-023-36815-3). The accepted source review covers all nine main pages, twelve SI pages and eleven figures. Both movies were decoded and sampled; raw data and author-modified code remain unavailable.

The package contains 22 operation templates, eight experimental branches, five station contracts, thirteen asset families, twelve control packages and fourteen explicit unresolved-input cards. It preserves fabrication lineage, protected transfers, current-epoch optical/detector readiness, spatial mapping, all measurement branches, reconstruction dependencies, repeats and failure closeout.

This is an original design and finite synthetic-test artifact. It is not an executable robot controller, optical or physical simulation, fabrication drawing, safety-qualified procedure or scientific reproduction. The validated runnable whole-paper task count remains zero. Approximately 10 Hz is a source reference for analog 16x16 imaging only; it is never a photon-sparse performance claim.

Read TASK_DESIGN.md, RELEASE_BOUNDARY.json and unknown_parameters.json first. The scene is separately distributed as midinfrared_scene_assets_v1. Only agent_visible.json is designated actor context; filesystem/process isolation is unimplemented.

Run with Python 3 from this directory:

    PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
    PYTHONDONTWRITEBYTECODE=1 python tests/verify_package.py
    PYTHONDONTWRITEBYTECODE=1 python tests/verify_export.py
    PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s review -v

For the separate, finalized scene package, also run tests/verify_pairing.py with its directory as the sole argument. This verifies pinned bytes, concrete targets and all 44 world-space anchors.

Tests use synthetic IDs and arbitrary values. Passing tests establishes only the stated symbolic checks.
