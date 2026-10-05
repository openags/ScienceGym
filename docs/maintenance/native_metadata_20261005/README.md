# Native metadata maintenance, 2026-10-05

This bounded revision cleans factory/cloud UI path residue in 14 previously published native Blender files. The observed residue was low-severity metadata hygiene and portability debt; the audit found no evidence of user-specific paths, credentials or a compromise. This is not a universal secret-stripping guarantee.

## Current bytes and unchanged semantics

- `native_hashes.json` binds each historical native hash to its current hash and size
- The individual `*.cleanup.json` files record 48 changed schema-declared fixed buffers, totaling 2,297 changed decompressed bytes; hashes and offsets are disclosed, never recovered raw buffer contents
- Only `FileSelectParams.dir`, `FileSelectParams.file`, `Editing.act_imagedir` and `RenderData.pic` may change. All bytes outside the declared changed buffers are identical. Ordinary name tails and opaque character arrays are deliberately preserved
- `path_policy.json` records six explicit render-output exceptions: five generic factory temporary output directories become bundle-relative, and the cooling overview retains its intended filename at a portable relative location. All intentional relative paths remain unchanged
- The streams use native-compatible deterministic zstd compression. Eight native semantic snapshots are exactly equal; six differ only in the approved render-output filepath. No geometry, material, camera, lighting, render parameter, scientific fact, operation, qualification flag or design-family count changes
- GLB and preview bytes are unchanged. No rendering, hardware action, physical simulation or scientific reproduction is claimed

## Historical evidence and current binding

Original scientific/native/render/sanitization reviews retain their original meaning. `historical_review_scope.json` identifies old native hashes in those reviews. They are not retroactively treated as reviews of changed bytes. Exact old records replaced at current pair/freeze paths are preserved under `historical/` and indexed in `historical_current_records.json`. Woven's current native validation receipt was actually rerun, with its old receipt retained in that history.

Conformal and midinfrared current task asset pins, snapshots and pair receipts are regenerated and checked against current native bytes. Scattering's scene core, strict task export, two deterministic replacement archives and detached pair receipt are regenerated. The original released archives remain historical and unchanged. Replacement archives have distinct maintenance filenames and are not asserted to have been separately uploaded.

`afm_source_rebinding.json` explicitly binds the current AFM native hash to the geometry-equivalent source used by four historical carrier-extraction records. Those records, their original AFM source hash and attribution remain unchanged; no new extraction, asset-family credit or source-reuse claim is made.

The arcmorph and wetting independent viewer tests also contain aggregate package-byte pins. `aggregate_test_pin_lineage.json` retains old and current digests with unchanged file counts. Their viewer datasets are unchanged. Only conformal, midinfrared and scattering source-viewer datasets are rebuilt.

## Verification

The current-base checks pass 11/11 root groups, 587 source-viewer tests, 1,221 focused package/contract checks without skips and thirteen sanitizer regression tests. All 168 generated viewer outputs reproduce deterministically. A locally generated standalone export passes mocked-DOM coverage of 958 routes and 19,496 displayed occurrences; it is not committed or uploaded. Independent review covers all 14 native files and 303 dependency/scope checks. See `verification_summary.json`, `independent_native_audit.json`, `independent_dependency_audit.json`, `independent_scope_acceptance.json` and `published_base_revalidation.json`.

## Reproduction and limitations

The cleanup code is in `scripts/native_metadata/`; it uses the accepted QHA SDNA parser with a narrower four-field mutation policy. Install the optional `zstandard` Python dependency listed there. Run from the repository root:

```sh
python3 -B scripts/native_metadata/test_native_paths.py
python3 -B scripts/verify_release.py
```

The cleaner requires separate source and destination files plus an exact source SHA-256. Unsupported schemas, unterminated targeted strings, unapproved absolute render output paths, stale source pins and an existing destination, report/source/output aliases and existing report/snapshot files fail closed. It never saves through Blender. A later Blender save can repopulate UI metadata and invalidates the cleanup receipt.

For independent native inspection, use Blender 4.3.2 with `--factory-startup --disable-autoexec --threads 1 --python-exit-code 1` and the supplied `native_semantic_snapshot.py`, under identical flags before and after. Treat absolute paths in local snapshots as private audit evidence; only redacted equivalence receipts belong in the publication.

These checks cover native byte boundaries, static semantics, nominal contracts and source-viewer fidelity. They grant no stronger physical or scientific qualification.
