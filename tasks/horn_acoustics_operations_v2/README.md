# Horn-like acoustic metasurface task family

Gated, source-grounded whole-paper design for Ghaffarivardavagh et al., Nature Communications 9, 1349 (2018), DOI [10.1038/s41467-018-03839-z](https://doi.org/10.1038/s41467-018-03839-z).

Only cylindrical-to-plane conversion was physically measured. The paired conditions are without and with the focusing metasurface. Each condition has 190 spatial positions and ten technical readouts per position. The fifteen tabulated focusing geometries fill thirty mirrored design positions; printed part count and independent experimental replication are unspecified.

Forward focusing, beam splitting, transfer matrices, COMSOL and phase-amplitude comparisons remain nonphysical coverage. Table 2 is reference-only and is not repackaged as observations. This package contains original contracts, documentation and synthetic bookkeeping tests; no scientific simulation or robot execution.

Read TASK_DESIGN.md, operations.json, coverage_matrix.json and unknown_parameters.json. Run python3 -B -m unittest discover -s tests -v from this directory.

The completed design has 44 operation templates, five physical/prerequisite/closure branches, nine theory/numerical branches and seventeen unresolved input groups. 84 passing static and synthetic tests check complete paired campaigns, scoped occurrences, calibration, failed-readout retries, matched-state integrity and export identity. See review/independent_review.json and VERIFICATION.json for review and test limits.
