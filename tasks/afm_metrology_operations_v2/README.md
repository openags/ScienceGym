# Cantilever-free AFM inert metrology

Original English ScienceGym task design for Cao et al., Nature Communications (2021), DOI [10.1038/s41467-020-20612-3](https://doi.org/10.1038/s41467-020-20612-3).

Eight bounded physical branches cover qualified inert-target custody, mount/level/contact calibration, intermittent-contact raster and line imaging, separate conventional-AFM cylinder mechanics/optics, readout and cleanup. Fabrication is represented by two gated qualified-service routes. Prefabricated arrays and configured instruments are initial preconditions, not proof of historical fabrication completion.

Read TASK_DESIGN.md, branches.json, operations.json and the source/unknown ledgers. The source's 0.5 mm versus 5 mm discrepancy and printed series-spring equation sign conflict remain explicit. Separate target/probe custody keeps calibration valid within an episode; final session teardown retrieves the retained probe and invalidates that calibration.

## Checks

    python3 -B -m unittest discover -s tests -v
    python3 -B tests/verify_package.py
    python3 -B tests/verify_export.py

These are static/synthetic contract and exact-file checks. No real robot action, physics, numerical reproduction or scientific replication occurred. See VERIFICATION.json and the independent review receipt for actual check status.

## Export

EXPORT_ALLOWLIST.json pins the exact original-file package. Only agent_visible.json may be supplied directly to an actor. No publisher source pixels, prose dumps, PDFs or raw experimental data are included. Any external publication belongs to the separately authorized parent workflow.
