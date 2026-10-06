# Frictional-fluid measurement: original whole-paper task design

A ScienceGym design based on Sandnes et al., Patterns and flow in frictional fluid dynamics, Nature Communications 2:288 (2011), DOI [10.1038/ncomms1289](https://pmc.ncbi.nlm.nih.gov/articles/PMC3104512/).

Nine source-program branches are represented by twelve original evidence routes, six stations, eight asset groups and 32 evidence-only scene anchors. The software validates documentation, identity, preparation/run lineage, clock/calibration associations, controls, failures and safe-service closeout. It implements no fluid dynamics, robot command, physical service or generated scientific evidence. The companion scene is an original visual proxy, not a calibrated apparatus.

All twenty qualification holds remain unresolved for physical use. Only agent_visible.json is actor-facing; the plan, source references, synthetic fixtures and receipts belong to a trusted evaluator. Passing the offline tests validates the specified bookkeeping cases only. It does not authenticate a service or inspect external raw files.

Run offline tests:

    python3 -B -m unittest discover -s tests -v
    python3 -B -m unittest discover -s review -p 'independent_*tests.py' -v
    python3 -B verify_pair.py ../frictional_scene_assets_v1

Read TASK_DESIGN.md, RELEASE_BOUNDARY.json and NOTICE.md before using the package. The source's coral-rate conflict and printed Boyle-law sign issue remain explicit. Viscosity scaling and high-filling granular fracture are required branches; external porous-medium comparisons remain attributed context.

The deliverable contains original authored contracts and factual annotations only. Source material remains under CC BY-NC-SA 3.0 and is not redistributed. No physical experiment, raw-data reproduction, fluid simulation or GitHub publication is claimed.
