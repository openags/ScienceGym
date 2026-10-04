# Original wetting-transition laboratory assets

An editable original static laboratory scene paired with the whole-paper **design** task for Gerber et al., [Wetting transitions in droplet drying on soft materials](https://www.nature.com/articles/s41467-019-12093-w), Nature Communications 10, 4776 (2019), DOI 10.1038/s41467-019-12093-w.

## Delivered

- `geometry/wetting_lab.blend`: two metric scenes, editable primitives and editable text
- `geometry/wetting_lab.glb`: twelve laboratory role groups, 61 canonical anchors, and concrete carriers, fixtures, instruments and receipt interfaces
- `geometry/wetting_dimension_references.glb`: a separate dimensional display with explicit, uniform 20× whole-slide and 1000× microscopy-crop scales
- `evidence/overview.png`, `handling.png`, `dimensions.png`: actual Blender Cycles CPU renders, not image-generated mockups
- `operation_bindings.json`: all 74 exact reviewed operation IDs, with task guards and geometry targets
- `semantic_controls.py`: local display/record-label review controls with permanently disabled actuation
- `review/`: actual native reopen and portable reimport tests, render receipts, independent visual review and sanitation evidence

## Physical and scientific meaning

The original bench contains formulation staging, protected storage, slide carriers and a separate companion-coupon placeholder, a sealed external patterning receipt interface, an environmental chamber, a water-pipette carrier, side optics, a guarded bottom microscope, a guarded mechanical tester, a guarded rheometer, provenance review and independently reachable closeout roles. An original static tool illustration approaches carrier tabs. It is not a calibrated robot, safe pose, toolpath or implemented manipulation.

Native reference slide solids preserve the source's nominal 24 mm diameter and 0.17 mm thickness; PDMS and CY layers preserve nominal 30 and 35 µm thickness. The separate 20× whole-slide reference uniformly enlarges diameter and all thicknesses. The 1000× microscopy crop uniformly enlarges its native coordinates; the 35 µm CY thickness is source-nominal, while lateral crop size, synthetic cap shape, example lattice pitch/count, point-role positions and arrow are authored illustrations. These are not observed results, reference images, measured droplet volume, tractions, or a reproduction of any source figure.

All fixture, carrier, coupon, enclosure and optical geometry is illustrative and unqualified. The approximate side-camera angle, micropipette opening range and scan sampling in the paper do not establish safe clearances or metrology. Carrier contact candidates and active-film, fragile-tip, slide and objective exclusions are separate annotations. Loose collision envelopes cover selected equipment only and are disabled; no collision, reachability, grasp-force, load-capacity or kinematic validation is claimed.

Source reference, raw-observation role, imputed-point role, inferred-reference role and model-derived role are labelled separately. No acquired data or fabricated successful telemetry is present. No source figures, CAD, artwork, movie frames, source raw data, source prose files or author code is included.

## Safety and semantic controls

Every device service is a static, permanently disabled proxy. The patterning interface is solely an external qualified patterned-substrate receipt and custody placeholder. Cadmium/quantum-dot synthesis, ink handling and high-voltage patterning are not implemented or described as a recipe. Safe handling, waste, gas control, fluorescence excitation, curing, mechanical tests and physical cleanup require independently qualified external services.

The eleven requested scene states can be previewed as labels. Names such as `qualified_patterned`, `acquiring` and `archived` are display-only and certify nothing. Record labels cannot verify a receipt, certify ageing, release a sample, generate observations, satisfy a real safety guard or establish scientific success. Safe-close review can always be requested, but a request is not safe-isolation evidence. The paired task owns stricter bounded offline evidence contracts; neither package controls hardware.

The bundled binding-contract files preserve the pre-build design snapshot, including pending availability fields. Delivered static availability is established by the inventory, resolved bindings and actual geometry checks; physical qualification stays false.

Source conflicts are retained as local holds, including 220/228 µm film thickness, traction-window conventions and conditional equilibrium interpretation. The 55 nL macro analysis origin is not applied to the smaller microscopy droplet. PDMS30:1's detection-limit branch stays separate from successful CY reconstruction. Repeated times, droplets, specimens and source experiment counts are not interchangeable independent replicates.

This is 12-group scene coverage and 74 symbolic task bindings. It contributes **zero validated runnable whole-paper tasks** and makes no physical or scientific reproduction claim.

## Reproduce and verify

With Blender 4.3.2 and Python 3.12+:

1. `python write_contracts.py`
2. `blender -b -t 6 --python geometry/build_scene.py`
3. `python complete_bindings.py`
4. `blender -b --python tests/verify_blend.py`
5. `blender -b --python tests/verify_glb_import.py`
6. `python sanitize_metadata.py`
7. `python tests/run_package_tests.py`
8. `python export_package.py`

The public ZIP follows the explicit allowlist. The hash manifest covers every public file other than itself. Native editability and portable loadability do not establish scientific accuracy or physical safety. Render compression can vary across platforms; the delivered receipts hash the exact delivered bytes. Original geometry and code are Apache-2.0; source attribution and Blender font notice are included.
