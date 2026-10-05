# Microsphere microscopy: whole-paper task design

Original ScienceGym task design based on Wang et al., *Optical virtual imaging at 50 nm lateral resolution with a white-light nanoscope*, Nature Communications 2:218 (2011), [DOI 10.1038/ncomms1211](https://www.nature.com/articles/ncomms1211).

The package covers thirteen source branches through thirteen authored stages, seven stations and nine paired original asset groups. Its offline software validates receipt identity, preparation/custody lineage, controls, evidence classes, dependencies, bounded failures and safe-closeout bookkeeping. It exposes no laboratory, robot or simulator commands. This is one paper-level design; zero runnable whole-paper experiments or scientific reproductions are claimed.

All physical work remains HOLD_QUALIFICATION. Sixteen source/service input gaps remain explicit. Qualified closed services would be needed for preparation, sphere assembly/contact, optical acquisition, SEM reference and closeout. The source's illustrated 50 nm transmission example and text-only 50 nm reflection claim are different evidence categories. Reported outcomes never become generated measurements or success thresholds.

Only agent_visible.json is actor-facing. The evaluator owns independent receipts and the other files. Read TASK_DESIGN.md, RELEASE_BOUNDARY.json and NOTICE.md before use. The paired scene is illustrative, has 33 evidence-only anchors, and is not calibrated hardware geometry or an optical model.

Offline checks:

    python3 -B -m unittest discover -s tests -v
    python3 -B -m unittest discover -s review -p 'independent_task*tests.py' -v
    python3 -B tests/verify_package.py

Finite synthetic fixtures supply document identifiers and stand-in hashes, never images or scientific measurements. Passing them establishes only the stated bookkeeping properties. External service authentication, hardware safety, physical clearance and metrology remain outside this implementation.

Original authored materials use Apache-2.0. The paper is officially free to read but has restricted reuse rights; no unrestricted source-content reuse grant was established. No publisher PDFs, figures, extracted prose, traced geometry, source CAD/code or raw data are included.
