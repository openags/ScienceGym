# Contributing Assets and Robot Interfaces

An asset should make a task-relevant object or interaction inspectable. A beautiful mesh without a usable loading surface, control, support or state contract is insufficient for a robot-task binding. Geometry, appearance and functionality have different readiness levels and should be reviewed separately.

## Choose a concrete need

Start from an existing `asset_needs.json`, asset requirement file or operation. Claim the asset or interface in an issue and name its intended operations. Current requirements are not installed assets. Some historical manifests point to unbundled scenes, meshes or videos; verify that a referenced file exists before promising it as an input.

Useful contributions include:

- **Devices:** instrument housing, sample chamber, loading tray, readable controls, ports, guards and status indicators
- **Materials and samples:** stock, separate components, intermediate and final specimens, parent/child identities and visible state variants
- **Fixtures and consumables:** holders, clamps, carriers, calibration references, expendable films, labels and replacement parts
- **Room and robot interfaces:** benches, clearances, docks, doors, storage/quarantine areas, tool mounts and supported grasp targets

Choose one interaction, such as loading a holder or replacing a cover, and show that a reviewer can understand its input state, action interface and output state. Whole-laboratory modeling is unnecessary for an initial asset PR.

## Proposed asset package contract

There is no universal asset loader, metadata schema or asset validator in the current release. The following layout and fields are a proposed review contract. Agree on location and format in the issue before adding large binaries. A possible new layout is `assets/<asset_id>/` with:

- `README.md`: purpose, task/operation links, inspection instructions, readiness and unresolved limits
- `asset_metadata.json`: identity/version, units/frames, provenance, dimensions, parts, states, affordances and collision declarations
- `geometry/`: original editable source and agreed exchange exports, with generation/export instructions where applicable
- `materials/`: permitted texture/material resources and appearance-state variants, if needed
- `evidence/`: screenshots of geometry, controls, collision proxies and representative task placement
- `LICENSES/` or an attribution record: per-file origin, license, required notices and changes

Copy [asset_metadata.example.json](templates/asset_metadata.example.json) as a starting record. It deliberately contains nulls and no geometry, so it is not submission-complete or execution-ready. Its field names and coordinate convention are proposals, not requirements enforced by the repository verifier.

An assets-only contribution need not implement a simulator. It must identify which geometry and interactions exist, which are metadata proposals and which remain unimplemented. A binding contribution additionally maps task IDs to concrete scene instances and validates that those names resolve.

## Identity and physical conventions

Use a stable asset ID plus version and distinct instance IDs in a scene. Distinguish the physical material/specimen identity from the shader that renders it. A gray shader cannot establish aluminum composition or measured optical properties. Record source dimensions and uncertainty separately from authored design dimensions; undocumented measurements remain unknown.

For new metadata, propose SI canonical units: metres for length, kilograms for mass, seconds for time and radians for angles, with explicit conversion from source units. Declare coordinate handedness, up/forward axes, origin datum, local frames, transform direction and rotation representation/order. Do not assume all existing packages already follow this convention. Document conversion at each import/export boundary.

Keep an explicit physical scale and display scale. A magnified visual part remains physically millimetre-scale in its task metadata. Do not use visual enlargement to claim gripper compatibility. Include a ruler or known-size reference in a screenshot, and record bounding dimensions. Explain pivots and joint limits for moving parts. Unverified mass, friction, compliance and contact parameters must not be presented as calibrated physics.

## Specify usable affordances and states

For each interaction, record its ID, associated part, local reference frame, allowed tool/gripper, support or grasp region, approach/access constraint, precondition, attach/actuate/release behavior, observable postcondition and failure/stop condition. Tie it to the task's operation IDs. Missing reachability or load limits remain gates.

Controls and connection ports need distinguishable identities, locations, direction/type, compatible mates, state/readback and an interaction mechanism. A painted button is visual geometry until a press interface exists. A cable graphic does not establish electrical connectivity. A fixture needs a supported loading pose, retention/release semantics and an observable seated state; name clearance requirements and unknown tolerances.

Represent relevant variants such as empty/loaded, open/closed, clamped/released, intact/torn, assembled/disassembled and quarantined. State which transitions are visually authored, logically implemented or unvalidated. Appearance should support legitimate inspection without exposing hidden fault labels or evaluator answers. Preserve sample identity across state changes; replacing a consumable creates a new component identity and appropriate assembly revision.

Declare visual mesh and collision representation separately. Document collision groups, simplified proxies, noncolliding decorative parts and intended contact/support surfaces. Collision metadata is still a design contract until tested in a selected backend. Do not add an unrequested physics dependency merely to contribute static geometry or screenshots.

## Provenance and licensing

Use original geometry or assets with verified permission for the intended redistribution. Record creator, exact source URL, retrieval date, license/version, modifications and attribution requirements per file. A manufacturer manual or product page can justify dimensions and interface layout without authorizing redistribution of its CAD, photographs, logos or textures. Link references instead of copying unlicensed pixels or meshes.

If creating a new mesh from measured or reported dimensions, describe it as an original authored approximation, cite its references and state unmodeled details. Do not label it manufacturer-certified or dimensionally exact without evidence. Check textures, fonts and embedded resources as well as mesh files. The project license applies only where contributors have the rights to grant it; preserve third-party notices and resolve uncertain rights before publication.

## Worked asset handoff for cooling film assembly

The current cooling `asset_needs.json` requests an assembly bench, film frames, a topology mat and dimensional inspection at `WS_ASSEMBLY`; it marks them `not_built`. A bounded original contribution could supply a supported spacer-ring holder and two distinguishable film instances for `FILM` and inspection. This is a proposed asset, not a claim that a holder already exists.

Model and label the ring support, film-edge support regions, opposite attachment faces and an inspection view. Use source-supported dimensions only where available; leave attachment tooling, tolerances and unresolved geometry gated. Supply intact and torn visual states and separate component IDs. Document whether the films are rigid visual placeholders or have any implemented deformation. A screenshot can establish visible placement, not tension, sealing, optical properties or feasible manipulation.

The task author reviews identity and version rules; the asset author reviews scale, frames and affordances; the integrator checks mappings and available observations. A later functional PR may implement attachment and replacement events. Keep those claims separate so a useful static asset can be accepted now.

## Evidence for review

Include an overview at correct scale, close-ups of each interaction point, labeled local axes/pivots, a collision-proxy view if supplied, and representative state variants. Show at least one placement in its intended task context. Record the viewer/tool version and reproducible opening or generation steps; do not claim software is installed for every contributor.

A reviewer should be able to locate each file, confirm rights, compare dimensions, identify controls and support regions, understand state changes and find unresolved gates. Include a manifest or hashes for exported binaries and state what was actually inspected. Do not copy a historical render receipt to certify new geometry. Functional acceptance additionally needs positive and negative interaction tests in a named implementation; static display acceptance does not.
