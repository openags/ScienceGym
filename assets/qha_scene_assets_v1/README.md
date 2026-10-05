# Graphene quantum Hall arrays: original scene assets

Editable, natively compressed Blender scene, portable GLB and three genuine CPU-rendered previews for a service-mediated ScienceGym3D design review of He and colleagues, *Accurate graphene quantum Hall arrays for the new International System of Units*, Nature Communications 13, 6933 (2022), DOI [10.1038/s41467-022-34680-0](https://doi.org/10.1038/s41467-022-34680-0).

## Scope

This original visual package implements the eleven accepted asset groups and binds all fifteen route stages R00–R14 to 32 named, evidence-only anchors. It is a static, non-executable task-design illustration. No hardware, electrical model, scientific simulation or physical robot was operated. It does not validate a laboratory reproduction or report new measurements. Every physical interface, manipulation path, collision proxy, service envelope and support pose remains unqualified; actuation is disabled throughout.

## Files

- `geometry/qha_lab.blend`: compressed native scene, editable text, meshes, materials, lights, cameras and named anchors
- `geometry/qha_lab.glb`: self-contained geometry/material export with exact asset IDs and evidence-only anchor metadata; glTF uses its standard Y-up coordinate convention
- `previews/preview_01_overview.png`: whole lab design, protected carrier, passive robot, distinct services and return station
- `previews/preview_02_specimen.png`: enlarged logical map of one chip and topology explanation
- `previews/preview_03_services.png`: locked cryogenic and precision services, separate reference baths and evidence review panel
- `shared_binding_contract.json`: exact scene/task interface; root objects AS01–AS11, qualified inputs still unknown
- `scene_guards.py` and `tests/test_scene_guards.py`: side-effect-free semantic validation with disabled physical commands, not a hardware runtime
- Source snapshots: original annotations retaining every reported fact, conflict, unresolved input, route and service boundary
- `review/`: render receipts and independent acceptance evidence

The optional archive exporter uses Python zstandard for a compressed-native privacy check. Run guard checks with `python -m unittest discover -s tests`. Rebuild using Blender 4.3 or later with `blender -b --python geometry/build_scene.py`; renders use Cycles on CPU. Blender's bundled font stays editable in the native file; GLB labels are mesh geometry.

## Scientific identity and dimensions

There is one physical 7 × 7 mm source chip, represented inside the sealed protected carrier. Its z thickness is an illustrative 0.5 mm placeholder, explicitly unknown scientifically. The large two-color map is an explanatory object, not a second specimen or fabrication CAD. Each logical subarray has 118 parallel Hall elements, nominal R_K/236 (about 109 ohm). Their series combination contains 236 total elements, nominal R_K/118 (about 219 ohm). The small disk symbols are representative, not element counts. The Hall bar is a separate region on the same chip. No individual element is an independent specimen.

Source-reported geometry is partial: 150 micrometre element diameter, at least 120 nm NbN lead thickness, 50 micrometre lead width, six 15 micrometre contact prongs with 22 micrometre spacing, and 200 micrometre Hall-bar width. Those facts are retained as context; they are not enough to reconstruct exact source CAD. Other mesh dimensions, the transport corridor, carrier handles, robot reach and service exclusion zone are authored illustrations, not safe or qualified engineering dimensions.

The 100-ohm oil-bath reference and 12.9-kiloohm air-bath reference remain distinct assets and evidence identities. Neither is the on-chip Hall bar. Visual resemblance never authorizes reference substitution.

## Closed qualified services and holds

Microfabrication, chemicals, cryogens, pressure/vacuum, strong fields, energized connections and precision electrical operation are sealed specialist services. The scene contains receipt interfaces rather than operating controls. The robot stays a passive illustration and has only a protected-carrier grasp datum; no bare-chip grasp is permitted.

Eq 3 input representation, Eq 4 bin-size semantics and the supplemental repeated-edge comparison-loop expansion remain unresolved qualification holds. All 18 source conflicts and all unknowns are preserved verbatim in original review annotations. Blank/missing evidence labels never stand for a zero or a measured pass. No source plots, publisher figures, source CAD, raw data or author code are bundled or reconstructed. No fabricated electrical telemetry is supplied, and published outcomes are not success thresholds.

Safe return requires independent electrical, accessible-field, thermal/pressure, stopped/supported-motion and receiving-custody evidence. A green icon, command, timer or attractive render proves nothing about safety. The provider retains physical custody until independently accepted handoff; metadata checks cannot grant physical permission.

## Coordinate and reuse notes

Native coordinates are metres, right-handed, Z-up. glTF export uses standard Y-up. Assets are rooted at world origin for inspectable direct transforms; anchors are exact named empties parented to their asset roots. The public archive has an explicit allowlist and contains no temporary backups, cache, private filesystem paths, raw source documents or local execution logs.

Original project code and geometry use the repository's Apache-2.0 license. The source paper remains CC BY 4.0, with separate attribution to He and colleagues; no third-party source material is relicensed. No author endorsement is implied. See `LICENSES/ATTRIBUTION.md`.

## Strict-clean serialization revision

This is revision `qha_scene_assets_v2_clean` of the same logical asset package. Asset IDs, the shared task contract, scientific/source annotations, GLB and all three preview bytes are unchanged. The earlier local archive is preserved separately. The native file now has complete recognized fixed-width C-string buffers canonicalized, including bytes after the first NUL, and inactive file-browser/sequencer directories cleared. Active objects, geometry, materials, text, cameras, lighting, rendering and units were independently reopened and compared. No scientific result or operating permission changes.

`geometry/deep_native_buffers.py` parses the native SDNA schema, recursively scans fixed char arrays, records buffer hashes and ranges without disclosing contents, and fails closed on unsupported layouts or unclassified tails. Cleanup writes complete fields and verifies that all bytes outside declared fields stay identical. Public reports retain the deep scan, masked-byte equivalence and separate native reopen comparison.

Run `python geometry/deep_native_buffers.py scan geometry/qha_lab.blend --package-root . --report review/deep_buffer_scan.json` for the current file. After any subsequent native save, run `python geometry/finalize_native_buffers.py` before export, because file writers may repopulate inactive UI buffers. The build and native sanitizer invoke that finalization automatically after the last save. The strict exporter repeats the deep buffer check; a readable scene alone is not sufficient export acceptance.
