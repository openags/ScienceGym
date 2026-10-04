# Mechanical actuator metrology: original task design

Whole-paper route accounting and a bounded, offline synthetic prepared-specimen metrology contract for DOI 10.1038/s41467-020-17947-2. No source code, publisher artwork, hardware driver, fabrication recipe or physics solver is supplied. The physical workflow remains unqualified. Whole-paper completion is false.

Start with TASK_DESIGN.md and asset_binding_plan.json. Only agent_visible.json is actor context; source outcomes and fixture measurements remain evaluator-only.

Run `python -m unittest discover -s tests -v`, `python tests/verify_package.py` and `python tests/verify_export.py`. The public archive is an audit artifact, not actor context. There are no physical results or validated mechanics.

Independent review passed after fixing actor/evaluator projection and cross-configuration replay binding. Validation comprises 32 author tests, 33 independent tests and 49 authored synthetic lifecycle configurations. Fourteen scientific design routes are accounted for; only two metrology branches and one safe hold have executable synthetic lifecycle checks. Whole-paper target-count eligibility remains false.
