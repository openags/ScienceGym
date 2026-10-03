# Embedded Extrusion-Volumetric Printing: paper-level task family

## Scope and status

This is an independently authored, source-bounded ScienceGym experimental task-design family for Tisato et al., *Nature Communications* 16, 6730 (2025), DOI [10.1038/s41467-025-62057-6](https://doi.org/10.1038/s41467-025-62057-6). It represents the complete reported physical experimental program at task-template level, including preparation, instrument setup obligations, both printing routes, handling, controls and characterization. It is not an executed robot task, calibrated simulator, scientific solver or complete historical reproduction.

The full nine-page Version of Record and nine-page primary supplement were lawfully obtained and read; preflight visually inspected all pages. The main source is the University of Freiburg deposited Version of Record. A publisher identity redirect was not completed or retried. No paper PDFs, extracted article text or publisher images are exported. Source attribution and access facts are in `provenance.json`.

## What the family contains

Nineteen selectable configurations span five practical families:

1. Material development: paired Mat1/Mat2 rheology, photorheology and UV-Vis; bath R805 loading comparison
2. Positive EmVP: helix, targeted and area bellow examples, Thinker, loaded skeleton sphere, filament-reinforced hollow cylinder, diagonal lattice with CT surface comparison, pressure-actuated reinforced bellow
3. Negative EmVP: flat Y-junction/co-flow chip, cylindrical separate-channel chip, fine-needle channel demonstration
4. Controls: pure-VAM straight-channel resolution, pure-VAM positive-feature resolution, EMB3D filament/oozing microscopy, single-material versus combined cage comparison
5. Mechanics: printed Shore D coupons and separately cast tensile specimens

The reusable operation templates describe mobile researcher actions: retrieving labeled stock, weighing and aliquoting, carrying supported vials, docking and maintaining orientation, operating guarded equipment, removing and cleaning fragile prints, connecting fluid paths, mounting specimens and preserving raw records. Template counts are not robot action counts, durations or specimen counts.

## Real causal sequence, without artificial time inflation

A printing episode connects material identity and preparation to instrument and digital-input qualification, deposition or direct loading, aligned VAM exposure, extraction, cleaning, postcure and the selected characterization. The negative route additionally requires channel flushing before postcure. Material and measurement campaigns allocate their own batches, aliquots, specimens and repeated conditions.

The source printing times are minutes, not days. Supplementary Table 1 covers only EMB3D plus TVAM. It excludes preparation, transfer, washing, characterization and the reported five-minute postcure. This design does not invent waiting periods, conditioning days, extra assays or unrelated chores. Long horizon means a consequential chain of physical dependencies and record-preserving decisions. `dependencies.json` is a partial-order reference; equivalent lawful orders and grasp choices remain valid.

## Configured equipment is not reconstructed hardware

The source describes a custom Cartesian extrusion printer and an LCD-based volumetric printer. Motor, syringe, controller, wavelength and pixel-size descriptions are retained, together with the burden of obtaining a qualified installed machine. The work order must provide actual guarding, calibration, safe contacts, stops, coordinate transforms and instrument-readback interfaces.

Full construction drawings, mechanical CAD, wiring, firmware and optical calibration are not reconstructed. The cited earlier hardware publication and supplementary code were not executed. Projection generation and CT/surface analysis are provenance-checked external handoffs; no optical, mechanical, controller or scientific simulation runs here. A missing installed asset remains a visible gate, not a fictional successful setup.

## Source recipe and setting gates

The working recipes, mixing duration/speed, routine deposition settings, glass-vial capacity, common coordinate origins and characterization settings are preserved with source locators. Important missing inputs include:

- Acetone amount and solvent-fate handling
- Whether the reported CQ/EDAB percentage is each component or their combined amount
- Recipe mass-fraction basis, batch scale, actual vial fill and specimen allocation
- Geometry, safe gripping features, complete extrusion jobs and qualified projection stacks
- Complete exposure, alignment, shadowgram and instrument acceptance settings
- Wash/flush pressure and endpoints, postcure optical program, microscopy preparation, CT processing and mechanical-test details
- Historical replicate counts, exact analysis conventions and current-lot qualification criteria

An independently supplied authored value can enable an episode but cannot become a historical source fact. Nulls cannot be interpreted as zero, empty comparisons cannot count as completion and a no-op geometry is rejected. Some figure-only lists are verified: R805 legend levels are 2,4,8,12 percent; the exact denominator remains a recipe qualification issue. Pure-VAM straight-channel models are 2.00,1.50,1.00,0.50,0.30 mm in diameter and 4 mm long. Material identity for the pure-VAM resolution controls is not explicit; Mat2 is declared as an authored task selection, not a source fact.

## Handling and branch-specific interpretation

- The same vial's orientation and reference frame must persist between EMB3D and VAM. The source common origin is model XY center and model bottom in Z. No automatic alignment apparatus is invented
- Positive targeted and area deposition are distinct assignments. Uncured travel oozing is retained as an observation; it is not automatically a final-part failure because subsequent selective cure may omit it
- Negative channels use sacrificial PE3100. Washing and channel-specific clearance precede postcure. Needle diameter, CAD channel dimensions and actual CT measurements stay separate
- Single-material cage controls use direct VAM; the combined condition uses embedding. A single vial is not forced through both paths
- The pure-VAM negative control uses its reported image-based comparison; CT is not imposed as an extra task
- Printed hardness and cast tensile specimens have separate manufacture and test histories. Four hardness sites are within-sample measurements, not four independent specimens
- Sectioning, photorheological curing and destructive tensile tests change sample state. A specimen cannot silently reappear intact for a later condition

## Controls and records

`control_packages.json` defines nested condition coverage and matched factors. Every work order supplies finite specimen counts and schedules. Missing or invalid acquisitions remain in their assigned slots; retries append new attempts and retain earlier outcomes. Sample, batch, apparatus, calibration, job and analysis versions are carried into raw records.

`lineage_contract.json` distinguishes stock, batch, aliquot, vial, syringe, printed/cast part, section, offcut and waste. Every physical entity has one current location. Transfer completion requires independently observed release, supported transit and destination docking. Raw records are acquisition-linked and immutable; derived records cite actual raw parents, selection rules and processing parameters.

## Actor and evaluator separation

`agent_visible.json` is a selected-goal projection. The actor receives its work order, public material/condition cards, observable labels, calibrated controls and visible missing inputs. It does not receive the reference operation list, DAG, evaluator rules, hidden faults or paper outcomes as future measurements.

The public authoring repository may include evaluator documents for transparency. That does not authorize a runtime to mount the whole directory into the actor. `RELEASE_BOUNDARY.json` requires a fail-closed selected projection; no runtime loader is implemented here.

The evaluator uses independent object histories, instrument receipts and raw-record provenance. Narration, function names or agreement with paper trends are insufficient. Complete truthful work may disagree scientifically with the paper. Outcomes distinguish completion, partial work with a valid blocker, safe abort and contract failure. Faults must have a visible sign or an available public check.

## Source conflicts and nonmanual scope

`source_conflicts.json` preserves ambiguous recipes, swapped main-text recovery-panel references, inconsistent chip labels in the timing table, recovery-test terminology, the measurement-start versus illumination-start clock and the paper's use of “Hausdorff” for a mean Cloud-to-Mesh discrepancy. No paper result is an acceptance bound.

Supplementary optical intensity simulations and the literature comparison table are explicitly outside the physical task chain. Source Data, supplementary code and movies are referenced by the paper but not inspected in this packet. Acquisition-linked CT reconstruction and surface analysis are required handoffs, not invented raw results. These boundaries are indexed in `nonmanual_scope.json` and `coverage_matrix.json`.

## Verification and remaining implementation work

Independent source audit and standard-library structural/adversarial tests accompany the design. They check references, DAGs, unknown gates, condition coverage, actor/evaluator boundaries and representative invalid record histories. They do not prove physical feasibility, authenticate instrument measurements or validate a robot episode. Check the current `independent_review/REPORT.md` for exact results and source-byte verification status.

A future execution system still needs qualified installed assets, real geometry/jobs, resolved experiment inputs, embodied transport interfaces, an observation backend and a selected actor loader. No CAD, controller, robot world, force/optics engine or scientific backend is supplied. The deliverable is reviewable without inventing these missing pieces.

## Attribution

Silvio Tisato, Grace Vera, Qingchuan Song, Niloofar Nekoonam and Dorothea Helmer (2025). Article licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), subject to credit-line exceptions. Source-derived facts are paraphrased; robot and evaluation contracts are new interpretations. No author endorsement is implied. No repository license has been changed.
