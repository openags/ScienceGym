# Arc-Morph operations v2

An original English ScienceGym task-design package for DOI [10.1038/s41467-025-57089-x](https://www.nature.com/articles/s41467-025-57089-x).

The package accounts for seven physical route families, 31 operation templates, 20 coverage records, 12 asset groups, 14 unresolved-input cards and 10 source conflicts. Four cardstock demonstrations each retain ground, rigid and shear state slots. Polymer preparation, an eight-configuration paired-view series and qualitative shear are separately represented.

This is a design and finite offline synthetic-test artifact. It is not a robot controller, physics simulation, fabrication drawing, safety-qualified procedure or scientific reproduction. The validated runnable whole-paper task count is zero. The single reported quantitative specimen is not converted into eight samples.

Read TASK_DESIGN.md, RELEASE_BOUNDARY.json and unknown_parameters.json first. The scene package is separately distributed as arcmorph_scene_assets_v1; exact semantic binding is in asset_binding_plan.json. The complete directory is reviewer/evaluator material. Only agent_visible.json is designated actor context, and production access isolation has not been implemented.

Run from this directory with Python 3:

    PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
    PYTHONDONTWRITEBYTECODE=1 python tests/verify_package.py
    PYTHONDONTWRITEBYTECODE=1 python tests/verify_export.py
    PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s review -v

Tests contain clearly synthetic IDs and values. No paper image, raw-data file or source notebook is needed or exported.
