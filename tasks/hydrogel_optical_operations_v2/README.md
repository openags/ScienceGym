# Hydrogel optical micro-metastructures

Original ScienceGym task design for Zhang et al., Nature Materials (2023), DOI [10.1038/s41563-023-01649-3](https://doi.org/10.1038/s41563-023-01649-3).

## Deliverable

36 physical branches, 107 operation definitions and 53 source-coverage records describe the full preparation and measurement program. Read TASK_DESIGN.md first, then branches.json, operations.json and the source/unknown ledgers. The local schema is hydrogel_optical_task.v1; it does not claim universal compatibility with another package's validator.

The scope is abiotic optical materials. Chemical formulation, standalone gel curing, two-photon printing, solvent development, glass/spacer assembly, infiltration/UV cure, coverslip removal, chamber assembly and thermal processing are closed qualified services. Robot-facing contracts permit only retained-carrier movement, loading, handoff, readout and safe unloading. No real actuation interface exists.

## Source boundary

The upstream audit read the complete deposited main/Methods/captions, six main figure images, 22 SI pages with nineteen figures, seven workbooks and eight sampled keyframes from each of nine videos. Four Extended Data captions are read, but their images remain uninspected. Video 9 uses a separate 27,000-unit specimen and twenty-times-accelerated playback.

The Fig. 4l 20/50-mW label conflict, Fig. 3j wavelength/amplitude mapping conflict and other source ambiguities remain explicit gates. No missing geometry, acquisition setting, independent repeat count or result is invented. Source observations, authored contracts, unknowns and synthetic test evidence are separate.

## Checks

From this directory:

    python3 -B -m unittest discover -s tests -v
    python3 -B tests/verify_package.py
    python3 -B tests/verify_export.py

VERIFICATION.json and review/ record scope and outcomes. All checks are static or synthetic bookkeeping; they do not establish trustworthy production authority, robot feasibility, physical simulation, numerical reproduction, apparatus safety or scientific replication. No experiment was run.

## Export and actor visibility

EXPORT_ALLOWLIST.json is the exact original-file boundary, including SHA-256 payload hashes. Only agent_visible.json may be supplied directly to an actor. The rest is authoring/evaluator material. No publisher PDF, figure, video, workbook or source prose dump is included. Publication is performed only by the separately authorized parent workflow.
