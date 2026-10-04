# Exact export and actor visibility boundary

EXPORT_ALLOWLIST.json lists every permitted package member and pins all members except itself by SHA-256 and byte count. Its own entry is excluded to avoid recursive hashing. A public ZIP includes exactly those members plus the allowlist. No recursive broad directory copy is permitted. Symlinks, caches, source content, source media, unexpected files and private absolute paths are excluded.

The public package is an auditable developer artifact. Public availability does not make all files actor context. The actor-visible allowlist is exactly agent_visible.json. Every other member, including evidence_map.json, source_outcomes.json, tests, review reports and this document, is evaluator/audit-only. Public synthetic fixtures offer no secrecy or authenticated trust; use separate qualified services for any real task.

Only the two prepared-specimen metrology branches and the direction-hold contract have executable synthetic lifecycle verification. Numerical and fabrication routes remain design contracts. Whole-paper completion and full-paper target-count eligibility are false.
