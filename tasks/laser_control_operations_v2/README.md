# Laser stabilization task design

Original whole-paper design for DOI 10.1038/s41467-024-46319-3, with 15 scientific routes and an offline synthetic contract. Full PIC/PCB preparation, calibrated open-loop characterization, three DFB branches, independent comb heterodyne versus in-loop PSD, safe closure and a separate numerical SiN example are retained.

Start with `TASK_DESIGN.md`, `branches.json` and `asset_binding_plan.json`. Only `agent_visible.json` is actor context. Source outcomes and fixtures are evaluator-only. No laser/electrical actuation, fabrication, real experiment or scientific solver is implemented. Whole-paper execution is incomplete; design coverage and execution verification are separate.

Run `python -m unittest discover -s tests -v`, `python tests/verify_package.py`, and `python tests/verify_export.py` from this folder. Independent review status is recorded in `STATUS.json`.

Validation: 43 author tests and 45 independent tests pass. The 55 synthetic configurations include normal closure, lock-loss safe closure, damage quarantine and an unqualified hold. Independent checks rejected 2,970 cross-configuration replays and compared 150 integration cases with a high-precision oracle. The exact archive contains 41 original text/code files. These checks establish design and offline contract behavior only.
