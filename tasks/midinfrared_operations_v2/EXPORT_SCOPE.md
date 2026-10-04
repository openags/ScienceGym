# Export boundary
Only the exact bounded UTF-8 inventory hard-coded in tests/verify_export.py is exported. EXPORT_ALLOWLIST.json binds byte count and SHA-256 for every other member. Source PDF, images, movies, notebooks, raw data, code, CAD and scene binaries are excluded. The original scene is separately released.

Unknown/missing files, path aliases, symlinks, special entries, binary text, duplicate ZIP names, encryption and changed bytes are rejected. The whole package is reviewer/evaluator material; actor access is documented as agent_visible.json only, without implemented operating-system isolation. Any edit requires a new manifest and renewed checks.
