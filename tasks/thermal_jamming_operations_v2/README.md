# Thermal-jamming experiment task draft

Start with [TASK_DESIGN.md](TASK_DESIGN.md). This authored whole-paper task design assigns real material preparation, fabrication handling, transport, tool use, device interfaces, measurement and cleanup to a mobile laboratory robot, while keeping autonomous device processes separate.

The design has thirteen configurations and explicit unknown-input gates. It is not a runnable controller, complete reproduction recipe or physical-feasibility claim. See `source_access_audit.json` and `source_conflicts.json` before using source parameters.

Validate with `python -B tests/run_validation.py`. See independent review for its finite scope. Only files named in `EXPORT_ALLOWLIST.json` may be exported. No remote publication or physical execution is performed here.
