# Directional-cooling laboratory review

Current phase: asset and scene development. No owner acceptance, whole-body
clearance, sensor-only manipulation or complete paper campaign is claimed.

Serve the repository root and open `/viewer/lab_review_v1/index.html`.
The existing local server uses port 8769. New candidate assets include separately
displayed Dex5-S Pro visual/kinematic reconstructions, three ordinary tool
types and a selected OMAX ProtoMAX waterjet. Geometry inspection sliders are
not physics-controlled robot actions.

The three camera candidates now use pinned manufacturer D455/D405 meshes with
their upstream license. They are separately displayed on the assembly bench;
H2 mounts, cables, calibration and sensor output are still absent.
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
- `hand_envelope.json`: static sensitivity bound for the authored hand chain at
  previously recorded body poses, including an explicitly assumed adapter margin.
  It does not qualify actual mounting, camera geometry, loads or movement.
- `acceptance_contract.json`: eight open review gates and their exact-revision
  evidence. Comments in the browser are not acceptance receipts.

Manufacturer images/documents are linked and hashed where locally inspected,
not redistributed. Instrument and hand reconstructions are original; added
camera geometry comes from the licensed manufacturer ROS meshes. The hand
package explicitly has no dynamics or verified H2 mounting model. Review view
names follow the asset axes and do not imply a calibrated photographic match.

The active implementation plan is
`docs/pilots/DIRECTIONAL_COOLING_IMPLEMENTATION.md`. Existing Panda task inputs
and privileged-state body tests are historical references only.

The latest selection is G1 29DoF + Inspire FTP, under the owner's Unitree-body /
open-hand instruction. The lab's H2 and Dex5-S assets remain previous-candidate
references until the new combination's installation and spatial audit are ready.
The official integrated candidate can be inspected at
`viewer/robot_resource_review_v1/index.html`. The 66 inventory rows include
three superseded robot/hand references; these are not additional required robots.
