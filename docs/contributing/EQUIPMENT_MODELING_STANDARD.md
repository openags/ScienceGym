# Equipment Reconstruction and Acceptance Standard

Effective 15 October 2026 for new equipment assets and substantive equipment revisions. These are required author and reviewer checks. They supplement the [asset guide](ASSET_GUIDE.md) and [readiness rubric](REVIEW_CHECKLIST.md); they are not a claim that existing assets satisfy this standard.

The target is a recognizable reconstruction of the actual experimental equipment, with the structures a robot must see, reach and operate. Commercial instruments must follow the identified real product. Custom apparatus must follow the paper's apparatus evidence and a documented reconstruction. Rendering quality, labels, file hashes and a generic instrument-shaped enclosure do not establish fidelity.

## 1. Identify equipment before modeling

Create an equipment inventory linked to the paper's branches and operation IDs. Record manufacturer, product family, exact model or part number, generation/revision, installed options, accessories and the paper/SI locator supporting that identity. Separate the instrument, objective, detector, stage, controller, fixtures and custom modifications; a brand name on one component does not identify the entire apparatus.

Check the publication-era configuration. A current successor product or a visually similar instrument must not silently replace the device used in the paper. If the model is not reported, search the paper, SI, videos and relevant cited methods, then compare available product generations. Record the evidence, selected reconstruction hypothesis, alternatives and confidence. An unresolved identity may support a labeled draft, but cannot pass acceptance as the identified commercial product.

## 2. Search for real product resources

Perform and record a resource search before creating substitute geometry. Prefer, in order:

1. Manufacturer product and archived product pages, manuals, installation/service documents, accessory lists and dimension drawings.
2. Manufacturer CAD/download portals and manufacturer-linked CAD distributors: STEP, IGES, native CAD or dimensioned DXF where available.
3. Official product photographs, demonstrations and installation videos showing front, sides, rear, sample access and operator controls.
4. Paper apparatus figures/videos, institutional equipment pages and documented distributor or used-equipment photographs to resolve missing views or discontinued models.

Record the query or portal inspected, URL, access date, model/revision match, relevant page/figure/time locator, what was obtained and unsuccessful searches. Distinguish an available resource from an inspected or downloaded resource. Record reuse terms for each item. Search/download availability alone does not grant permission to redistribute third-party CAD or images; references can remain external while original geometry is reconstructed from them.

If reusable CAD is available, inspect its units, assembly structure, options and completeness before adapting it. Otherwise reconstruct from dimensions and multiple views. Failure to find CAD calls for documented reconstruction, not an arbitrary replacement shell. Unseen features must be inferred and identified as such.

## 3. Reconstruct appearance and structure

Preserve the product's recognizable silhouette, proportions, component arrangement, materials/colors and visible task-relevant details. Model the actual arrangement of the base, frame, enclosure, working volume, sample stage, optical/mechanical heads, displays, controls, doors, handles, connectors, cable/tube routes and accessories where present. Distinguish the purchased device from custom adapters.

Use real physical scale and a consistent coordinate system. Keep a dimension ledger with units, source locators, uncertainty and the basis of each value: reported, manufacturer-specified, estimated from a referenced image, or authored inference. A dimension inferred from a photograph needs its scale reference and method. Do not report an inferred dimension as a manufacturer measurement. Enlarged explanatory models belong in separate views/assets and must never change the physical robot workspace.

Separate movable and removable parts. Define pivots, joint axes, travel, opening direction, attachment and release for doors, drawers, stages, clamps, covers, knobs and interchangeable components. A closed, loaded or assembled render must have corresponding open, empty or separated parts when the task requires those transitions.

Visual simplification is acceptable only when recorded and when it preserves both recognition and the relevant interaction. Decorative hidden internals can be omitted. Do not simplify away loading access, grasp surfaces, connector alignment, control readability, working clearance or a feature the robot must inspect. Text plaques may explain an asset to a reviewer; they cannot supply missing device geometry or replace the observations available to the robot.

## 4. Derive geometry from the robot operation chain

For every operation that uses the equipment, provide a mapping containing:

- Operation occurrence/branch, initial object and device state, robot motion/manipulation, tool and relevant part IDs.
- Approach direction, grasp/contact/support regions, loading pose, connection mates, release mechanism and required clearance.
- What the robot must perceive before and after acting: identity, alignment, seating, clamp/door state, readback or failure indication.
- Resulting component/sample/device state, sample lineage, observable completion condition and recovery/unloading path.
- Whether the interaction is only described, geometrically modeled, logically implemented or tested in a named backend, with evidence for the claimed level.

Walk through retrieval, transport, opening, loading, locating, fixing, connecting, setting controls, starting/monitoring, reading/recording, disconnecting, unloading and reset wherever needed. Include the actual work inside preparation or fabrication stages. An automated device process can remain device-owned after robot setup; manual work cannot disappear into a service box or completion receipt. Missing source handling detail requires a documented, physically coherent inferred sequence, as described in the [paper task guide](PAPER_TASK_GUIDE.md#reconstruct-omitted-physical-work).

Keep visual geometry, collision geometry, joints, interaction logic and observation interfaces separately identifiable. Collision/reachability and state-transition claims require their own tests. A model can pass reference comparison before execution is validated, but static poses and state labels do not prove manipulation.

## 5. Supply a comparison and review record

Use the [equipment review template](templates/equipment_modeling_review.example.json), or provide an equivalent record with an explicit field mapping. The template is an incomplete example, not a completed review. The evidence must be tied to the exact model files/revision being reviewed and include:

- Equipment identity, paper configuration, search log, inspected references, rights and unresolved alternatives.
- A part and dimension ledger distinguishing source facts, reconstruction inferences and unresolved parameters.
- Matched reference/model views: front, side, rear and every loading/control/connection surface the robot uses. Include overview scale, close-ups, relevant open/closed and loaded/empty states, and sample/robot context. If a reference view is unavailable, record the search and reconstruction assumption; the reviewer must state which fidelity claims remain unverified.
- A comparison table of silhouette/proportions, dimensions, component layout, materials/colors, interfaces and moving parts. Each row needs a locator, rendered view, discrepancy and resolution, with tolerances appropriate to the task and the precision of the reference. There is no universal percentage that proves fidelity.
- Operation-to-part coverage and a walkthrough of each required interaction at its claimed implementation level. Show access and clearances from useful robot viewpoints, not only a distant presentation camera.
- Exact reviewed file hashes, reviewer/date, separate identity, appearance, scale/structure and interaction decisions, remaining blockers and requested readiness.

A machine check can validate JSON, paths, hashes and declared coverage. It cannot establish that a model matches a product photograph, that the inferred apparatus is plausible, or that a robot can use it. A reviewer must inspect the references and model evidence. Do not infer an acceptance decision from a green static release check or populate a review with an automated approval.

## 6. Acceptance and blocking findings

New or substantively revised equipment must satisfy this standard before being accepted as a faithful equipment asset. A draft can be submitted and reviewed for further work, but its placeholders must be labeled and excluded from fidelity/interaction coverage claims. Review each equipment item, not just the overall scene.

Request changes or keep the relevant acceptance gate open for:

- Missing product identity or a substituted model/generation represented as the paper's device.
- No documented manufacturer/resource search, or missing references for the claimed appearance and structure.
- Generic boxes/cylinders or labels replacing the recognizable commercial device and its working parts.
- Distorted physical scale, mixed display/physical scales, or unmarked invented dimensions and interfaces.
- Missing or misplaced task-relevant doors, controls, ports, fixtures, sample access, moving parts or accessories.
- Omitted hands-on operations, inaccessible loading/connection paths, unexplained state changes, or parts appearing only after a mock completion.
- No reference/model comparison, unresolved discrepancies affecting the claim, or review evidence that describes different model bytes.
- A visual/static check being represented as functional, collision, reachability or experimental validation.

A genuinely unobserved feature can remain a labeled inference; a known task-critical mismatch cannot be cleared by adding an approximation disclaimer. Record each decision and limitation in the PR. Reference fidelity, interaction readiness and full task execution remain separate decisions.

## Existing packages

Historical static scenes, proxies, storyboards and frozen review receipts retain their original scope. This policy does not certify, rename or rewrite them. When revising one, create a new version with a new review record, audit its equipment against these gates and preserve the prior package's provenance. Do not count an untouched historical illustration as a device that passed the new standard. Publication and reuse rights still apply to all new references and geometry.
