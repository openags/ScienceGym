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

## 7. Whole-laboratory asset and layout acceptance

The directional-cooling pilot follows the owner's asset-first review order:
complete and present its assets and laboratory scenes, obtain the owner's
acceptance of that exact revision, then develop the manipulation sequences.
Existing paper requirements identify needed objects, interfaces and access
states during this phase. Static poses, opening sweeps and clearance probes
may test the scene; they are not new manipulation episodes. This sequencing
does not require completed controllers as a prerequisite for asset review.

### Complete inventory and academic provenance

Account for all paper-required instruments, separate accessories, custom
apparatus, raw stock, intermediate specimens, tools, consumables, fixtures,
storage and supporting facilities. Reconcile the inventory against every
represented paper branch. Distinguish asset types from physical instance
counts, and split grouped resource descriptions before declaring completeness.
Two simultaneous apparatus or measurement channels require actual instance
allocations; a single attractive display model does not cover both.

A paper-derived experiment can use an authored robot laboratory. Identify its
room dimensions, furniture and layout as authored design unless sources
establish the historical arrangement. Preserve the paper's apparatus geometry,
experimental conditions and indoor/outdoor requirements. Keep evidence for
commercial models, photographs, CAD licenses, dimension uncertainty and source
conflicts alongside the assets. Preserve manufacturer geometry at physical
scale; adapt furniture and layout to the robot instead of resizing devices.

### Space for the whole humanoid

Review a dimensioned floor plan and the 3D scene together. Include walls,
columns, doors and their swings, thresholds, benches, under-bench structures,
storage, service routes and the approach to each station. Treat circulation,
turning, carrying, working, service access and emergency access as distinct
space requirements. Temporary carts, staged samples, open cabinets and
extended instrument components count as obstacles in the relevant state.

For each route and workstation, record:

- The pinned robot body and both hand models, posture/joint ranges, carried
  object or tool and any geometric uncertainty. A standing body silhouette
  alone is insufficient for movement clearance.
- A full-body swept envelope for entry, transit, turning, forward/backward
  departure, bilateral reaching and the largest relevant carried load. Show
  self/environment collisions and margins at elbows, fingers, torso, head,
  feet and the carried object. Sampled poses must disclose sampling density
  and interpolation assumptions; sparse keyframes do not prove continuous
  clearance.
- Clear widths/heights at bottlenecks and turns, support areas at workstations,
  door/lid/drawer sweeps and access to instrument controls, connectors, sample
  chambers and maintenance panels. Nominal bench spacing is not usable width.
- For each accepted clearance, the modeled envelope, added uncertainty margin,
  manufacturer requirement and applicable site requirement, with evidence and
  the worst-case state. Derive the selected dimension from these constraints;
  there is no universal aisle width for all humanoid laboratories.

Geometric clearance does not establish dynamic balance, stopping distance or
safe separation from people. Record the additional fault, falling and
protective-space assumptions needed for the chosen robot. Where the exact
hand, carrying geometry or stopping data is missing, conservative draft
envelopes may support layout work, but affected final gates remain open.

### Safe use and applicability

Maintain a scene risk register linking each relevant hazard to a physical
location, source, control, inspection evidence and residual limitation. Review
equipment support/bench and floor loads, stability, sharp edges, pinch points,
heated baths, water near electrical equipment, cable/hose routing, stored
chemicals and coatings, required exhaust, waste storage, emergency controls
and unobstructed access/egress. Separate fabrication/coating, wet calibration,
dry electrical/optical measurement and outdoor measurement where the process
requirements warrant it; do not combine all processes on a presentation table.
Specify roof-edge protection and access if a rooftop is selected. Protective
fixtures and warning labels must correspond to actual modeled provisions.

Check manufacturer installation/safety manuals and material safety data for
the selected configuration. Record site jurisdiction and relevant current
requirements before claiming regulatory compliance; the Singapore timezone
or language of a discussion does not establish the laboratory's location.
Scene review is a review of modeled design, not authorization to operate
physical equipment. Any necessary physical engineering or site safety review
remains a separate recorded requirement.

Reference register inspected on 23 October 2026:

- [ISO 12100:2010 official abstract](https://www.iso.org/standard/51528.html):
  machinery hazard identification, risk assessment and risk reduction provide
  the methodological reference. The full standard has not been reviewed in
  this update; citing its abstract does not establish conformance.
- [ISO 10218-2:2025 official scope](https://www.iso.org/standard/73934.html):
  concerns industrial robot applications and cells. Determine applicability
  to the selected humanoid laboratory explicitly; do not declare compliance
  based only on a robot model or simulation. Full text not reviewed here.
- [Stanford laboratory design considerations](https://ehs-library.stanford.edu/manual/laboratory-standard-design-guidelines/laboratory-design-considerations):
  a site-specific reference for unobstructed circulation, equipment service
  access and cart storage. Its jurisdictional dimensions are not adopted as
  universal humanoid clearance thresholds.

### Review package and decision

Supply the reconciled inventory, source/model comparisons for each asset,
dimensioned floor plan, interactive 3D inspection, station close-ups, relevant
open/closed states, robot and load envelopes, measured clearance/collision
reports, risk register and unresolved findings. Cite exact model and scene
hashes in the acceptance record, with reviewer, date and evidence for the
owner's decision. Automated checks may check geometry and records; they must
not manufacture that decision. A later asset, robot or layout change reopens
the affected gates. Accept only the declared asset/scene scope; runtime task
success and physical-site certification require their own evidence.

## Existing packages

Historical static scenes, proxies, storyboards and frozen review receipts retain their original scope. This policy does not certify, rename or rewrite them. When revising one, create a new version with a new review record, audit its equipment against these gates and preserve the prior package's provenance. Do not count an untouched historical illustration as a device that passed the new standard. Publication and reuse rights still apply to all new references and geometry.
