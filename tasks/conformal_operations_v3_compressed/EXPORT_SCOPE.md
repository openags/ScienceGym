# Export boundary
The exact bounded UTF-8 inventory is hard-coded in tests/verify_export.py. EXPORT_ALLOWLIST.json binds byte count and SHA-256 for every other member. Source PDF, figures, media, archives, CAD and source code are excluded. Original scene binaries have their own separately reviewed release.

Unknown or missing files, aliases, symlinks, special entries, binary text, duplicate ZIP names, encryption and altered bytes are rejected. All files except agent_visible.json are reviewer/evaluator material; real operating-system isolation is not implemented. Every edit requires renewed manifests and verification.
