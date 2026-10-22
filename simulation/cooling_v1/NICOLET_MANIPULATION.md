# Nicolet 6700 cover manipulation

The robot opens the hinged cover, releases it, regrips the handle, closes the
cover and withdraws. The accepted nominal record contains 54.080 seconds of
continuous joint-actuated physics. [The five-case suite](NICOLET_VERIFICATION.json)
includes a second initial arm state, a half-time-step run and physical
missing-handle and locked-hinge counterexamples.

## Geometry and provenance

The [original instrument asset](../../assets/nicolet_6700_v1/README.md) uses
the manufacturer envelope and sample-bay dimensions. The manufacturer's
user guide, printed pages 51 and 92, separates the hinged top, sliding sample
window and fixed front wall. These are distinct bodies in the simulation.
The earlier moving-front-wall approximation is not used.

Local hinge position, cover thickness, handle, density, friction and clearances
are inferred reconstruction parameters. The cover has 0.5 mm lateral running
clearance and 1 mm front-liner clearance. The passive hinge has selected
0.30 N m friction; its target open angle is -1.35 rad. The closed sliding window
has selected 0.6 N retention friction. Neither value is a measured property of
the instrument. These parameters and their source hashes are archived with
each execution.

## Contact execution and evidence

The Panda approaches the handle, closes its ordinary fingers and applies a
selected 12 N grip command. It follows the observed hinge trajectory while
checking bilateral handle contact and angular error. Before opening the jaws,
it gradually unloads the handle, then withdraws and observes one second of
unassisted retention. The reverse sequence closes the same cover in the same
world. Only the arm and gripper have actuators; there is no cover actuator,
grasp weld or live cover-pose assignment.

[The independent verifier](verify_nicolet.py) recomputes the saved cover angles,
window displacement, contacts, load bounds and final retention. It also checks
source/trace hashes, the continuous clock, numerical warnings and actuator
ownership. Nominal and second-state records each pass 28 checks. Removing
the handle and locking the hinge must fail at the corresponding physical
operation; those counterexamples pass 16 and 18 checks. The 0.5 ms refinement
passes 28 checks and changes the released cover angles by at most 0.000010 rad
relative to the 1 ms nominal run.

The [video](runs/nicolet/playback/chapter_01.mp4) replays all saved-state time
intervals at 12 fps, with an overview and tool close-up. Its separate
[media receipt](runs/nicolet/playback_verification.json) checks duration, frame
count, file identity and exact terminal-state presentation.

## Scope and reproduction

This accepts the selected hinged-cover cycle. Sliding-window operation,
optical accessory installation, connector mating, specimen handling and
optical acquisition remain separate obligations. The controller uses
simulator state rather than estimated camera observations. The whole-paper
branch count remains zero.

```bash
python simulation/cooling_v1/check_nicolet_import.py
python simulation/cooling_v1/test_nicolet_suite.py --execute
python simulation/cooling_v1/render_device_episode.py simulation/cooling_v1/runs/nicolet --kind nicolet
python simulation/cooling_v1/verify_playback.py simulation/cooling_v1/runs/nicolet
```

`--execute` archives previous runs before generating new ones. Without that
flag, the suite checks the existing exact records. Rendering refuses to
overwrite an existing presentation or render an unverified execution.
