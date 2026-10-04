# Lockable origami: original static research roles

Editable Blender scene, two GLB exports, and three actual CPU renders paired with the whole-paper task design for DOI [10.1038/s41467-022-29484-1](https://doi.org/10.1038/s41467-022-29484-1).

The 11 asset groups and 53 metadata anchors cover all 60 task operation roles. Apparatus, carriers, positions, anchor transforms, materials and visual proportions are originally authored and unqualified. Source figures, source CAD, source code, datasets and source movie frames are not included.

## What the scene establishes

- The main scene uses metres. A native paperboard reference is 15 × 15 × 0.21 mm; its rectangular shape and 15 mm square span are authored references, not a source panel. A separate reference strip is 240 × 5 × 0.21 mm, matching the reported tensile strip dimensions but not mounted or qualified
- The second scene uniformly scales a rectangular coupon by 8×, including thickness. The 2 mm cut length is source-reported. “1.4 mm intervals” is preserved as unresolved source wording; drawing a 1.4 mm uncut gap and 0.15 mm slot width are explicit authored choices
- Three original four-panel open-chain snapshots preserve their own virtual centerline link lengths at 0°, 35° and 65°. Their angles are not the paper’s dihedral angle theta. They are not A2, AO, A3, A2O, O2 or O3, a bifurcation model, a closed cell, or a lock/contact simulation
- The native file preserves editable geometry and text. GLBs contain static converted meshes and metadata. The package contains no force, stiffness, collision, hinge-contact or robot-control implementation

## Closed services and holds

Laser cutting, folding, PVA bonding/cure qualification, reconfiguration, tensile/compression loading, band cutting under preload and DIC acquisition remain external qualified services. The displayed 12.5 kN load-cell rating is a source fact, never load permission. The machines are empty, guarded and disabled. Source locked states require face contact under compression; this scene does not claim unloaded self-support.

All ten source discrepancy/qualification records remain held; prominent geometry issues include: N18 tessellation angle, inconsistent N4 rigidity counts, and SI Table1 lock/flat color coding. Source geometry, contact tolerances, adhesive/cure parameters, fit, calibration, grasp poses and loaded retention remain unverified. The complete source audit establishes reading coverage, not reproducible CAD or execution readiness.

## Use and validation

Open geometry/lockable_origami_lab.blend in Blender4.3+. Main world: X right, Y back, Z up, unit scale1 m. JSON anchors and inventory use that Z-up basis; GLB uses standard glTF Y-up with (x,y,z) → (x,z,-y). Open geometry/lockable_origami_lab.glb or geometry/paperboard_reference_display.glb in a glTF2 viewer; the latter is explicitly 8× display geometry. Build with Blender in background using geometry/build_scene.py. Run Python unittest discovery in tests; native and reimport tests require Blender. Local state guards only manage caller-owned record labels, which are not evidence or authorization.

EXPORT_ALLOWLIST.json is the sole public-file contract. MANIFEST.sha256 excludes only itself. export_package.py creates a deterministic 36-file ZIP. Build logs, caches, backup files, local audit inputs and absolute workspace paths are excluded. Evidence images have PNG text metadata removed; the native file is checked for stored private paths and reopened after sanitation.
