# Export scope

Only files explicitly named by `EXPORT_ALLOWLIST.json` may be integrated into a later task release. All are original authored Markdown, JSON or Python. The allowlist records SHA-256 for every entry except itself; refresh hashes after an authorized content change.

Excluded: publisher/repository PDFs, source XML/text dumps, SI images and video pixels, source datasets, raw numerical records, fabricated measured traces, CAD/meshes, private research paths, authoring scripts, caches and temporary test output. Source URLs and actual acquired-byte hashes are citations, not redistribution of those bytes.

This local package makes no public write and changes no repository license. A downstream maintainer must run repository-level release checks after integration and preserve these readiness boundaries. Package checks do not establish repository CI, physical feasibility, safe equipment qualification, actual robot execution or scientific replication.
