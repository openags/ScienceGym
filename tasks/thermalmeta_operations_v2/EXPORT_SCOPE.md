# Original-only public export

The exact EXPORT_ALLOWLIST.json is the sole export authority. Packaging never uses an unrestricted directory wildcard. Files must be ordinary UTF-8 text from the listed original contracts, tests and review; unknown files, hidden files, symlinks, unsafe member paths, publisher/media/data formats, private absolute paths and secret-like strings are rejected.

CONTENT_MANIFEST.json hashes every allowlisted content file except itself and PAIR_SEAL.json. PAIR_SEAL.json pins both accepted content manifests and the identical shared scene binding. Excluding only those two envelope files avoids a circular reciprocal hash; each ZIP has its own externally reported SHA-256. An independent final archive review is a detached receipt, preventing review-after-seal edits from invalidating the package.

The task and scene archives are separate deliverables. This task archive does not copy the asset archive or source material. The paired scene contains original static semantic geometry, never qualified fabrication CAD or evidence of robot/physics execution.

The privacy scan is a bounded automated check, supplemented by independent inspection. A successful scan does not establish universal secret detection. Structural tests do not prove scientific validity or real-world safe operation.
