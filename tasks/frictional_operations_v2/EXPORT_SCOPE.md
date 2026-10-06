# Original-only export boundary

Export only files explicitly named in EXPORT_ALLOWLIST.json, with exact hashes verified against DELIVERABLE_MANIFEST.json. Paths must remain relative regular files; symlinks, special files, path traversal, caches, hidden files and undeclared members are rejected. The task archive contains no binary publisher assets, source extracts, operating recipes, device controls, tokens or private workspace paths. The original scene is delivered separately with its own audited native/GLB/media files.

The deterministic ZIP and its delivery receipt remain outside this allowlist. The manifest excludes its own bytes to avoid a self-reference cycle, but the exporter checks exact manifest schema, ordered path inventory and duplicate prohibition. Pair references are sealed only after both cores stabilize.
