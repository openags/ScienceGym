# Source-to-asset comparison

Source: Bonfanti et al., “Automatic design of mechanical metamaterial actuators,” Nature Communications, DOI 10.1038/s41467-020-17947-2, https://www.nature.com/articles/s41467-020-17947-2

This is a factual comparison, not a reproduction claim. The original source figure and Methods were inspected. No source pixels, figure geometry or research algorithm/code enter the asset package.

| Evidence / source role | Asset implementation | Boundary |
| --- | --- | --- |
| Methods: NinjaFlex TPU | Teal generic diamond lattice | Appearance only; no material model, source topology, compliance or optimized design |
| Methods: 0.4 mm nozzle and 0.8 × nozzle layer thickness | Metadata records 0.4 mm and derived 0.32 mm | No printer geometry, slicing, recipe, fabrication or physical qualification |
| Methods: fixed bottom holder | Generic block and two screws | Authored clamp dimensions/contact regions; no retention-force validation |
| Methods: 5 mm caliper-aided manual input | Authored parked stage plus separate exactly 5 mm visual reference segment | Static magnitude reference only; robotized stage is an interface invention; no movement, contact or deformation |
| Methods: initial and displaced camera images | Generic capped camera and empty before/after record console | No images captured; no optical calibration or acquisition adapter |
| Methods: image-processing displacement calculation | Targets, ruler and identity-bound metadata records | Author-selected targets, no source node IDs, calibrated pixel geometry or scientific output |
| Fig 2 visual | Generic diamond lattice deliberately differs from both source shapes | No human-design or optimized-design tracing; no source efficiency displayed |
| Fig 2/SI Fig 3 direction discrepancy | DIRECTION: HOLD panel, null source-to-scene map | Local scene axes do not choose a scientific direction branch |
| Fig 2/Movie 2 and SI Fig 3/Movie 3 mismatches | Separate factual conflict ledger | Original crossrefs and observed content are preserved; no silent repair |
| Existing original AFM carrier family | Fifteen unscaled meshes, empty carrier | Original provenance and exact source Blend hash retained; zero new asset credit; no fit assertion |

## Native and display dimensions

- The source reports 5 mm input; the native authored reference endpoint separation is 0.005 m, checked in Blender
- Main-scene ruler ticks are spaced by 0.001 m and span 0.060 m; these are authored geometry, not a metrological calibration
- Main generic lattice uses a 6 × 4 diamond pattern, 0.014 m pitch, 0.0014 m beams and 0.004 m extrusion. All are original choices, not measured paper dimensions
- The separate display lattice preserves geometric ratios at 10×. Its reference separation is 0.050 m and is explicitly labelled 5 mm source / 50 mm display
- All carrier, clamp, camera, stage, fixture, target and furniture geometry is authored or original-family reuse. Physical fit, force limits, contacts, handling poses and uncertainty remain unknown

## Direction evidence retained

The main text assigns orthogonal motion to Fig 2 and anti-parallel motion to Supplementary Fig 3. Fig 2's caption and visible arrows show anti-parallel down/up. Supplementary Fig 3's visible arrows show orthogonal down/left. Figure captions point to Movies 2 and 3 respectively, while observed Movie 2 is orthogonal and Movie 3 anti-parallel. This package records the conflicting evidence, retains an unresolved hold and does not amend the paper or choose an execution default.

## Visual inspection

All three final render views were opened and inspected at 1600 × 1100. The overview shows the seven apparatus roles, fixed-base lattice, empty carrier and direction HOLD. The handling view makes carrier identity and native reuse visible. The measurement close-up makes marker targets, authored ruler, stage gap and static 5 mm reference readable. The apparatus geometry and source boundary labels are rendered by Blender Cycles CPU, with no source image overlays. Render noise is visible at 48 samples; this does not affect the editable geometry or readable close-up markings.

## Additional source boundaries

C_PHYSICAL_RESULTS_POINTER retains the main Methods reference to Supplementary Fig 1 versus printed results shown in SI Fig 3. C_FORCE_PANEL_POINTER retains the force-scan 5c/5d prose/caption discrepancy, outside the selected displacement-metrology scope. U_ANGULAR_N is an unknown source exponent, not a resolved parameter. The separate source-code research-only terms and disclosed patent application do not provide commercial fabrication clearance; no source code is used and current patent status is unverified.
