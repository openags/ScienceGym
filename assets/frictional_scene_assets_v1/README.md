# Frictional-fluid original scene assets v1

Original editable Blender and embedded-only GLB for the ScienceGym evidence-first task translation of DOI [10.1038/ncomms1289](https://doi.org/10.1038/ncomms1289). This is an authored static laboratory illustration, with 12 routes, 6 stations, 8 asset groups and 32 exact evidence anchors. It is not fluid simulation, experimental data, qualified apparatus CAD, a pressure operating procedure, or a hardware execution.

## Files

- `geometry/frictional_lab.blend`: compressed, editable native Blender scene; all original labels are meshes with full text in custom properties
- `geometry/frictional_lab.glb`: embedded-only geometry/materials/cameras; no linked images or external resources
- `previews/`: three genuine CPU Cycles renders, 1500 × 1000, from overview, closed-service and evidence-review cameras
- `shared_binding_contract.json` and `semantic_core.json`: byte-identical shared task/scene identities, exact anchors, condition invariants and qualification boundaries
- `scene_manifest.json`: named objects, source-dimension metadata, exact anchors and static support contacts
- `scene_guards.py`: pure read-only request validation; successful inspection never provides physical authorization
- `review/`: authored checks and independent native, GLB, geometry, preview, guard and privacy audit results

## Physical and scientific boundary

All physical work remains HOLD_QUALIFICATION with U01–U20 unresolved. Closed preparation and measurement volumes are service-boundary proxies, without internal recipes, operative controls or device dispatch. The camera is below the accepted source-scale cell. Generic illumination, closed injection-service housing, contained stocks, carriers, quarantine and archive are original proxy shapes.

SOURCE_SCALE objects use reported 350 × 350 × 10 or 19 mm plate dimensions and a 200 × 300 × 0.5 mm channel. These facts do not specify tolerances, seal design, pressure ratings, robot reach or safe loads. All room, fixture and carrier dimensions are illustrative. Anchors are logical evidence selectors, not motion targets. Named A03/A08 carriers separately satisfy illustrative dock top 0.965 m plus half-height 0.035 m equals center 1.0 m.

Five authored morphology tokens represent fingers, bursts, coral, suspension and granular fracture as static categories. They were not traced from the source, computed from dynamics or accepted as measured outcomes. B01–B07 source experiments/control branches remain distinct; B08 is external comparison context, and B09 is unimplemented analytical context. High-phi granular fracture never means breaking the glass cell.

The coral label conflict remains 0.1 versus 1.0 ml/min with provenance; no value is assigned to an operating command. The apparent Boyle-law intermediate sign inconsistency remains unresolved, with no repaired numerical model. Normalized phi is not absolute volume fraction; reservoir volume is not total compliance; pump rate is not instantaneous burst flow; movie playback time is not experiment time. A sparse source grid is not a complete factorial schedule, and 20 local width measurements are not 20 independent preparations.

## Inspection and rebuilding

Open the native scene with Blender 4.3 or later, or import the GLB in a compatible viewer. Run `python -m unittest discover -s tests -p 'test_*.py'` for the pure metadata guards. `verify_pair.py` validates reciprocal frozen task/scene manifests using a supplied task directory. A service proposal always returns a qualification hold. `check_closeout` is a final aggregate R12 archive-metadata check only; its no-pending-jobs field does not gate per-job R11. Any completed or failed job may receive R11 safe closeout independently while other jobs remain open. Static contact checks establish only visual support, not physical collision correctness or calibrated robot compatibility.

`geometry/build_scene.py` generates original geometry and CPU previews in an unsealed working revision. `geometry/finalize_native.py` performs SDNA-aware inactive UI/path and post-NUL-tail sanitation, preserving scientific/render semantics. The native file is reopened before and after cleanup for deep semantic equivalence. Preview metadata is removed without changing PNG IDAT pixels. Approved archives are immutable: rebuild into a new revision rather than overwrite a sealed package.

## Rights

Original assets and code use the repository Apache-2.0 license. The paper and supplements retain separate CC BY-NC-SA 3.0 terms; third-party porous-medium imagery has separate provenance. No publisher PDF, source text, source figure, movie, extracted frame, third-party photograph, source CAD or source code is bundled. Numeric facts and original factual annotations are not an assertion of source-media rights clearance. See `LICENSES/ATTRIBUTION.md`.
