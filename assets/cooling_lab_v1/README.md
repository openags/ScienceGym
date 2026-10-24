# Directional-cooling laboratory review

Current phase: asset and scene development. No owner acceptance, whole-body
clearance, sensor-only manipulation or complete paper campaign is claimed.

Serve the repository root and open `/viewer/lab_review_v1/index.html`.
The existing local server uses port 8769. The scene contains the complete
official G1 29DoF + Inspire FTP geometry, three ordinary tool types and a
selected OMAX ProtoMAX waterjet. Geometry sliders and the 47 per-point static
access postures are inspection tools, not physics-controlled robot actions.

The native G1 D435i now supplies nominal head RGB and ideal geometric depth
inspection views; the two D405 wrist views use an unaccepted mounting
candidate. Official Unitree STEP brackets and the clamp were converted without
rescaling. Exact triangle checks guided an above-wrist rotation that clears other links
at sampled finger poses. Clamp contact remains unresolved, so
these attachments are hidden by default and do not count as an installation.
The viewer can display them for fit review, and records separate attachment
conflicts at each station pose. D455 remains an optional bench reference.
Camera previews retain scene occluders even when the reviewer isolates an asset
or hides walls. They are ideal pinhole renderings, not calibrated observation
streams. See `assets/g1_sensor_rig_v1/README.md` for provenance and limits.

Eight Omega 5TC probes are staged separately, with catalogue-sized conductors
and inferred stored cable shape. They have no flexible or electrical model.

## Rebuild

Use the pinned geometry dependencies in `requirements.txt`; the existing
`/tmp/sciencegym-sim-venv` also contains Playwright for browser verification.

```bash
OPENBLAS_NUM_THREADS=1 /tmp/sciencegym-sim-venv/bin/python assets/cooling_lab_v1/rebuild_review.py
```

After serving the repository, include the local browser executable for visual
checks and refreshed screenshots:

```bash
OPENBLAS_NUM_THREADS=1 /tmp/sciencegym-sim-venv/bin/python assets/cooling_lab_v1/rebuild_review.py \
  --browser /tmp/sciencegym-browser/chrome-headless-shell-linux64/chrome-headless-shell
```

The rebuild runs source asset generators, the scene generator, static layout
checks, inventory/readiness reconciliation, source verification and negative
policy tests in dependency order. Browser checks are optional only for a
nonvisual rebuild; a changed review release needs renewed visual evidence.
It makes no source downloads and cannot silently switch robot models.

## Review artifacts

- `pilot_contract.json`: owner choices and future qualification targets.
- `scene.json`, `inventory.json`: exact models, placement, references and resource
  groups. Counts indicate candidate geometry, not accepted inventory completeness.
- `readiness.json`: manual-step resource crosswalk, compound resource decomposition,
  branch definitions and blockers. Quantity allocation is still incomplete.
- `ordinary_tools_sources.json`: inspected catalog facts and authored assumptions.
- `waterjet_sources.json`, `stock_sources.json`: selected fabrication-machine
  evidence, source conflicts, paper-derived sheet thickness and stock inferences.
- `assets/unitree_g1_inspire_v1/space.json`: source-derived body/hand bound
  at 129 restricted static poses, with exact official wrist transforms.
- `workspace_checks.json`: 47 separately tested palm-position targets, all with static position candidates, including proposed camera-clearance screening; records
  candidate joint coordinates, position errors, external obstacle conflicts and
  self-penetrations under the provisional collision model.
  Orientation, grasping, target-device internals, balance and paths are excluded.
  The Cary keyhole datum is preserved separately from an authored 80 mm upper
  palm approach; neither it nor the other approach offsets is a grasp frame.
- `hand_envelope.json`: historical H2/Dex5 sensitivity record, unused for G1.
- `acceptance_contract.json`: eight open review gates and their exact-revision
  evidence. Comments in the browser are not acceptance receipts.

Manufacturer images/documents are linked and hashed where locally inspected,
not redistributed. Instrument reconstructions are original; the selected G1,
hands and cameras use licensed official source meshes. The G1 integration
retains source inertials and wrist transforms but has provisional contact and
actuator parameters. Review view names follow asset axes, not calibrated photographs.

The active implementation plan is
`docs/pilots/DIRECTIONAL_COOLING_IMPLEMENTATION.md`. Existing Panda task inputs
and privileged-state body tests are historical references only.

The latest selection is G1 29DoF + Inspire FTP, under the owner's Unitree-body /
open-hand instruction. The lab now places that complete source-derived combination; H2 and Dex5-S
remain unplaced historical inventory references.
The official integrated candidate can be inspected at
`viewer/robot_resource_review_v1/index.html`. The 66 inventory rows include
three superseded robot/hand references; these are not additional required robots.
