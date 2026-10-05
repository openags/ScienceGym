# Thermal meta-devices: original paper-level task design

One authored ScienceGym task-design package for Li, Sigmund and Zhang, *Analytical realization of complex thermal meta-devices*, Nature Communications 15, 5527 (2024), DOI 10.1038/s41467-024-49630-1.

The 20-stage route covers separate family-specific preparation chains, three reference families in X/Y orientations, transient and steady evidence, calibration, controls, repeats, analysis, numerical-branch registration and service-owned safe closeout. It uses original semantic assets paired through exact IDs and content hashes.

This is an offline symbolic design and bookkeeping validator. It is not runnable laboratory automation, robot-motion qualification, a physical simulator or scientific reproduction. Fabrication, casting and thermal operation remain unimplemented closed qualified services. All numerical work is unexecuted. There are no new physical observations, publisher images, source arrays, source code or copied CAD.

Read TASK_DESIGN.md, RELEASE_BOUNDARY.json and the source/unknown registers before use. Only agent_visible.json is actor-facing; source outcomes are evaluator/reference material, never reward targets. Demo specimen and receipt IDs are invented bookkeeping tokens and are explicitly not physical objects.

Run the standard-library-only offline checks from the package root:

    python3 -B -m unittest discover -s tests -v
    python3 -B tests/verify_export.py

Independent review and pair sealing are recorded separately. Acceptance means one original paired paper-level design, not an executed or scientifically validated experiment.

Task content verification: 100 author and 48 independent test methods pass. All seven independently identified guard/export findings were corrected and rechecked. The independent report is under review/. Exact paired content digests are in PAIR_SEAL.json; each delivered archive has a detached final integrity review.
