# Reprogrammable mechanical logic: ScienceGym task-design draft

Original English ScienceGym contracts for Mei, Meng, Zhao and Chen, *A mechanical metamaterial with reprogrammable logical functions*, Nature Communications 12, 7234 (2021), DOI [10.1038/s41467-021-27608-7](https://doi.org/10.1038/s41467-021-27608-7).

PARTIAL SOURCE PACKET. Main narrative, Methods and captions are inspected; all 17 supplementary pages and movie descriptions are inspected. Main figure panels and all nine movie contents remain uninspected. The main PDF identity-redirect route is stopped. Source completeness is false. This is a gated design, not a robot-ready recipe, simulation or scientific replication.

The draft separates physical component tests, electromagnetic NOR/NOT/OR/AND, defective routing, volatile storage, mechanically loaded NOR and mesoscale fabrication from numerical NAND, half adder, planar architecture, crossovers and S-R latch. Geometry, electrical calibration, timing, fabrication recipes and robot interfaces remain unresolved execution inputs.

Use TASK_DESIGN.md and the JSON contracts for review. Only the explicit actor-visible schema is eligible for actor ingestion. Source figures, movies, PDFs and text dumps are excluded. No public write or physical execution was performed.

## Package and checks

- 55 reusable operation contracts; 14 physical-design routes
- 12 separately classified nonmanual dispositions
- 15 unresolved execution gates; 11 transport routes; 6 symbolic loops
- 87 static and adversarial synthetic-bookkeeping tests

Run from this directory with Python 3.9 or later:

```sh
python3 -B tests/verify_package.py
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
```

The schema is mechanical_logic_paper_task.v1, an original review contract without a runtime-loader compatibility claim. Passing checks establishes static consistency and synthetic record rejection, never apparatus safety, physics, authentic device evidence, robot feasibility or scientific replication. See REVIEW_NOTES.md and VERIFICATION.json for the independent review and scoped receipts.
