# Beaded metamaterials task-design package

Start with `TASK_DESIGN.md`. The structured design contains 13 source practical families, 22 configurations and 70 reusable operation templates, with typed routes in `routes.json`. It covers robot-performed preparation, bead/thread handling, fixtures, instrument setup, records and archive.

This is a source-bounded design, not physical execution, a simulator, precise CAD or a reproduction claim. Source tables, full geometry, some condition schedules and device settings are unresolved. No publisher text or figure pixels are packaged. The original repository LICENSE was not read, copied or changed by this work.

Run `python tests/validate_contract.py` for bounded static consistency checks. Validation does not establish physics, robot feasibility or device safety.

Independent focused review passed with no remaining blocking findings: 42 author checks independently rerun and 25 separate reviewer checks. Read `independent_task_review/REPORT.md` for scope and limits. These are task-design checks, not physical or source-pixel certification.
