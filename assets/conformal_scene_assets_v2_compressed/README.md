# Conformal elasticity: original static laboratory assets

Twelve original asset families, 16 paired operations, nine whole-paper branches, an editable Blender file, a portable GLB and three genuine Blender Cycles CPU previews. This is a static visual and semantic prototype. No hardware operation, elastic simulation, robot trajectory, experimental acquisition or scientific reproduction has occurred. Completed-conversion increment: zero.

## Scientific basis and provenance

Scientific roles and selected nominal scalar dimensions come from Czajkowski, Coulais, van Hecke and Rocklin, *Conformal elasticity of mechanism-based metamaterials*, Nature Communications 13, 211 (2022), DOI [10.1038/s41467-021-27825-0](https://doi.org/10.1038/s41467-021-27825-0). The accepted source review read the final nine-page main and all sixteen written supplementary pages, including all ten notes and six supplementary figures. Three videos decoded and five frames per video were visually sampled; this was not exhaustive continuous viewing. Zenodo archive contents and source software remain unread and unexecuted.

All mesh shapes, labels, scene layout and materials are original. No publisher figure, photograph, plot, paper PDF, movie frame, third-party CAD, source mesh, source image texture, source scientific code or data archive is included. The numerical scope board is an independently designed symbolic display. It does not stand for physical boundary-actuation equipment.

## What is modeled

- A01: a static 48 by 10 array of 4.8 mm square extrusions, matching a 306 by 64 by 40 mm scalar envelope; a detached 0.2 mm hinge-width reference and build-receipt token
- A02: 480 original 3.6 mm square tracking pads, with illustrative grid identities
- A03: an independently drawn foot-like fixture parked beside the tester, a mount and inspection tag
- A04: a three-point bridge fixture proxy, mounted solely for a static display, with two supports and a center pusher
- A05: a generic guarded tester, fixture dock, load-axis/load-cell proxies, latch, interlock indicator, disarm/isolation and emergency-stop affordances
- A06: an original camera/lens shell at a source-reported 4 m optical-center-to-specimen-center distance, supported on a tripod
- A07: two generic LED-panel roles and a white background plane
- A08: a supported carrier with handles and a key, a static end-effector proxy, and distinct storage/recovery/quarantine and archive roles
- A09: closed qualified fabrication and contact-treatment service shells, intake docks and receipt ports
- A10: an original checker target, reference support and camera-calibration receipt port
- A11: separate campaign policy, synchronized acquisition, tracking, mask, fit, boundary inference, evaluation and policy ports
- A12: an explicitly symbolic unit-cell FEM, full-structure FEM, analytical theory and numerical spring-network scope board

The foot is parked and the bridge is displayed mounted. There is no simultaneous foot-and-bridge procedure. Static enclosure panels and control colors are illustrative geometry, not certified protective hardware or real machine state.

## Source-known versus authored versus unresolved

Native units are metres, right-handed with +Z up. Portable GLB uses the standard glTF Y-up export conversion. The display maps beam length to X, source height/extrusion to Y and source width to Z. This axis choice is an authored presentation convention, not a source-verified specimen-coordinate registration.

The beam retains the reported scalar envelope, count and square side. Squares alternate plus/minus 20 degrees solely for the original visualization. Pitches are chosen to fit the outer envelope while retaining each 4.8 mm side; they do not recover source CAD. No connecting hinges are modeled. The 0.2 mm hinge datum is a disconnected dimensional reference, not an actual mechanical connection. The beam is therefore not printable production geometry, a recovered rotating-square mechanism, or a mechanically continuous specimen. One pad per displayed square and the grid IDs are authored placements, not validated source correspondences.

The reported camera distance is represented geometrically. The source 6000 by 4000 image size, 200 mm lens identifier, F4 lens designation and LED roles remain metadata. Render-camera parameters and studio illumination are unrelated illustrative choices. No optical calibration, actual exposure setting or measured detection accuracy is inferred.

All fixture spans, contact radii, foot outline, carrier dimensions, grasp clearances, protective enclosures, robot reach, poses, loads, speeds, safety limits, collision envelopes and optical-axis registration require engineering and commissioning. Physical sample pretwist, actual manufacturing topology, materials/lot characterization, contact-treatment identity and conditioning also remain unresolved. The full U01–U16 execution-gap record is included. Do not use these meshes for fabrication or equipment control.

## Whole-paper and safety boundaries

Physical beam preparation and foot/bridge image acquisition are distinct from the paper's numerical and theoretical work. B04 and B05 FEM, B07 analytical theory and B08 spring-network simulation are symbolic, unexecuted scope. B06 keeps physical versus numerical data and nearest conformal fit versus boundary-only prediction distinct. There is no invented physical kagome apparatus, dipole/pure-shear fixture or boundary actuator.

Source linear dilation versus area-ratio, hinge-energy power, stress/gradient conventions, fit-offset handling and gradient-modulus inconsistencies remain in source_conflicts_snapshot.json. No silent formula correction or validated scientific solver is supplied. In particular det(C) alone cannot establish orientation preservation: positive det(F) and separately qualified global geometry validity are required. Local bounds do not certify global injectivity.

Unknown powder is never represented as an approved consumable and is not dispensed. Printing, postprocessing and contact treatment are closed qualified-service dependencies. There are no material recipes, machine commands, live APIs, controllers, animation, motion drivers, spring dynamics, FEM, cloth, fluid or rigid-body physics. Source strokes/rates are factual protocol metadata, not safety limits.

## Operation bindings and static guards

Asset roots are ASSET.A01 through ASSET.A12. Required semantic anchors use ANCHOR.Axx.role. All 32 operation anchors use ANCHOR.R01.primary/control through ANCHOR.R16.primary/control; each target is a concrete mesh owned by the declared primary asset. Exact selectors and cross-asset participation are in operation_binding_contract.json. S01–S08 remain source route roles; this original lab layout does not certify physical station coordinates.

semantic_controls.py is a pure in-memory test example. Its receipts are explicitly synthetic test labels with no authenticity, authority or physical meaning. It checks carrier support, forbidden pad/hinge grasps, exclusive docking, identity and epoch freshness, four qualification categories, capture readiness before the static arm state, unique run IDs, fixture-change re-entry, replacement/treatment preparation invalidation, recovery quarantine, fault retention and explicit safe-state closeout. It always rejects actual physical execution.

A static guard success is neither a robot action nor experiment validation. Unloading does not imply pristine sample condition. New branches require new docking and qualification; changed specimens or contact treatment require fresh upstream preparation. Fault records remain present even when successful analysis never occurs. Fits never receive a blanket source-outcome success threshold, and frames are not independent specimen repeats.

## Files and review

- geometry/conformal_lab.blend: editable native geometry with separate family roots, mesh labels, studio illumination and three render cameras
- geometry/conformal_lab.glb: portable original asset mesh and anchor hierarchy, with mesh text labels and semantic extras; no studio lights or render cameras
- evidence/overview.png: complete original laboratory layout, including the 4 m camera separation
- evidence/specimen.png: source scalar dimensions and original illustrative specimen detail, from a dedicated render camera placed inside the visual enclosure
- evidence/stations.png: guarded mechanics, closed services, supported custody and separate analysis/numerical-scope roles
- review: render provenance and independent native, GLB, pixel, package and adversarial semantic findings

Every preview is a genuine Cycles CPU rendering of the included geometry. PNG metadata is stripped without changing pixel values. The editable file has relative output paths and no imported images, embedded scripts or external asset dependencies. A sanitized allowlisted ZIP and SHA-256 manifest omit source artifacts, local logs, backups, caches and upload receipts.

## Rebuild

Use Blender 4.3 or newer: blender --background --threads 8 --python geometry/build_scene.py . Use --no-render to rebuild geometry only. Run python3 -m unittest discover -s tests for the 27 authored Python checks. The independent package audit script is run separately with --source-review and --paired-task directories; these inputs are accepted authored review/task packets, not publisher files. Paths resolve relative to this package. Render files should then pass sanitize_metadata.py and export_package.py. Independent Blender audit scripts are under tests.

Passing static checks establishes only the inspected files and implemented software guards. It does not establish machine safety, robot reach, validated mechanical topology, material properties, authentic service receipts, calibration, measurement acquisition, collision-free motion or scientific success.

## Compressed packaging revision

This revision uses Blender's official compressed native-file serialization to reduce transfer size. The entire native scene is independently compared with the prior accepted revision: geometry, object/anchor hierarchy, transforms, materials, render cameras, lights, world, settings and static properties are preserved. The portable GLB and all three preview PNGs remain byte-identical. This is the same static design and adds no paper or conversion credit. The matching task package is conformal_operations_v3_compressed.
