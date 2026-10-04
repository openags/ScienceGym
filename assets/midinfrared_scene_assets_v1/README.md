# Mid-infrared single-pixel imaging: original protected laboratory assets

This package contains 13 original asset families, five station roles, 44 operation anchors for 22 proposed operations, an editable Blender scene, a portable GLB and three genuine CPU path-traced previews. It is an authored static geometry and interface prototype. It does not reproduce the source equipment, operate a robot, simulate photons, acquire measurements or establish scientific success.

## Source and originality

Scientific object and instrument roles come from Wang et al., *Mid-infrared single-pixel imaging at the single-photon level*, Nature Communications 14, 1073 (2023), DOI [10.1038/s41467-023-36815-3](https://pmc.ncbi.nlm.nih.gov/articles/PMC9968282/). The accepted review completely read the nine-page final main, twelve-page written supplement and one-page movie description. Both movies decoded cleanly and were visually sampled, not exhaustively inspected frame by frame. This asset authoring uses that accepted review. Raw data and author-modified reconstruction code were not obtained or read.

No publisher figure, photograph, traced sample outline, screenshot, movie, paper PDF, external mesh, CAD, source reconstruction code or model weights are included. Copper E/C/N/U cutouts and the silicon five-point-star role are independently designed meshes. They preserve source object roles without reproducing source pattern geometry. The four separate copper cassettes are authored interchangeable display examples; the source's copper sheet with four letters is not claimed to be four source samples. Example counts are never independent experimental n.

## Actual scene assets

- A01: four protected copper-mask cassettes with actual Boolean-cut transmission openings, candidate grip faces, keys, latch features, clear display covers and support posts
- A02: a protected silicon disc with a separate original star surface marking, edge support and orientation key
- A03: receiving/return/quarantine rack, inspection cradle, ID-reader shell, occupancy-sensor markers and custody ports
- A04: closed sample-fabrication service shell with dock, receipt port and reject bin
- A05: opaque closed optical service enclosure with an initially empty load dock, datum rails, latch and occupancy/interlock markers
- A06: distinct sealed source, pump, upconversion, analog-detector and photon-counter role shells with typed ports and detector-mode receipt interface
- A07: retained static target fixture inside a closed visual guard; no motor or trajectory
- A08: timing/data console with separate configuration, photon-path and encoding interfaces; no live telemetry
- A09: separate covered reference and blank carriers with candidate handles
- A10: independent reference-imaging camera-role shell, lens, support column and sample cradle
- A11: archive/evaluation console, analysis and manifest ports, branch ledger and failure-retention bin
- A12: supported transport cradle and static two-finger end-effector representation
- A13: a distinct spatial pump/SFG diagnostic-imaging service shell, sensor identity role and raw-map/registration ports

A13 cannot be substituted with A06's single-pixel bucket detector. The opaque optical enclosure deliberately contains no claimed optical layout, alignment recipe or beam geometry. Fabrication and optical work remain separate qualified service dependencies; a service receipt is not evidence that a robot performed the service's internal work.

## Dimensions, coordinate frames and qualification holds

Native units are metres, right-handed, +Z up. GLB uses standard glTF Y-up export with an import axis conversion. Exact nominal transforms and dimensions are recorded in asset_inventory.json; every anchor's world-space position and owner are in affordances.json. Asset roots are ASSET.A01 through ASSET.A13. Anchors are ANCHOR.R01.primary/control through ANCHOR.R22.primary/control.

Equipment sizes, laboratory layout, copper sheet thickness, carrier frames, handles, aperture outlines, support clearances and wafer radius are authored display dimensions. The silicon wafer uses the reported nominal 200 micrometre thickness, but its radius, star outline and carrier are authored. Etch depth/profile are unknown and not modeled; the star is a surface visual marking rather than a claimed etched geometry. Known optical wavelength, crystal, DMD and timing facts remain separate factual metadata. They do not qualify robot interfaces or fabrication dimensions.

All qualified poses, payload limits, friction, contact force, controller interfaces, optical calibration and collision bounds remain unresolved. Collision proxies are disabled and hidden. The native file has no rigid-body/cloth/fluid world, dynamics, joint constraints, animation, motion drivers, embedded scripts, live device controls or imported images. Visual guards and clear covers are not certified safety barriers. Studio illumination, copper appearance and silicon/cover materials are illustrative; no photons or measured signals are generated.

## Static interaction and paired task contract

operation_binding_contract.json and operation_bindings.json preserve R01–R22, A01–A13, S01–S05 and B01–B08. Each of 44 operation selectors resolves to a concrete mesh owned by its declared primary asset. R07 requires an object-removed dock and a distinct spatial-sensor receipt. R09/R17 share the load-dock role but have separate operation IDs and material/custody requirements. R20's metrology anchor is a representative repeat-plan interface: actual repeats must re-enter their original branch-specific anchors with fresh run records. It is not a single-location shortcut for all repeated acquisitions.

semantic_controls.py is a pure in-memory, reviewer-facing example. Its explicitly labeled test receipts have no external authenticity or physical meaning. It checks exclusive occupancy/leases, fresh detector epochs, same-epoch safe-access ordering, carrier identity, spatial-diagnostic dependency, material/mode matching, dynamic-plan dependency, quarantine and failure retention. It never calls Blender, a robot or equipment. Selecting an anchor or passing a static guard is not execution permission. Permanent physical-action rejection is tested.

The approximately 10 Hz source result belongs only to 16×16 dynamic analog imaging. The 32×32 analog branch is approximately 2.5 Hz; fourfold movie display speed is separate. No photon-counting branch inherits these rates. Mean photons per pulse is not total image dose; reconstructed grid is not spatial resolution. The task's complete raw-data, repeat, calibration and evaluator gates remain independent requirements.

## Files, previews and limits of review

geometry/midinfrared_lab.blend contains editable native objects and labels. geometry/midinfrared_lab.glb contains visible mesh/empty objects with portable mesh labels and extras, excluding disabled collision proxies, studio floor, render cameras and lights. The native file retains those supporting objects. The three previews are overview.png, samples.png and optics.png in evidence. They are genuine Blender Cycles CPU renderings of this original scene, not measured laboratory images or paper-derived figures.

Independent native reopening, fresh GLB reimport, pixel inspection and adversarial semantic checks are recorded in review. Passing them establishes only the inspected static artifacts and implemented software checks. It does not establish physical safety, robot reach, compatible optics, material quality, authentic service receipts, acquired data, source-result reproduction or conversion-completion credit.

## Rebuild and inspect

Use Blender 4.3 or newer: blender --background --threads 8 --python geometry/build_scene.py. Add --no-render to rebuild geometry only. Paths resolve relative to the package. Run python3 -m unittest discover -s tests for Python tests; independent Blender scripts in tests reopen the native and portable files. After actual rendering, run python3 sanitize_metadata.py. export_package.py creates a strict allowlisted archive and SHA-256 manifest. Local logs, backups, caches, input source files and upload receipts are excluded.

Original geometry and authoring code are Apache-2.0. See LICENSES/ATTRIBUTION.md and the Blender Bfont notice for portable glyph meshes. Earlier original ScienceGym asset packages informed naming, static-affordance and packaging conventions; no external source mesh was reused.
