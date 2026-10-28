# Cary 5000: passive main sliding-lid cycle

A source-specific Cary 5000 is fixed on the workbench. The Panda grasps the
recessed front pull, opens the main lid through its selected 305 mm stroke,
releases it for one second, grasps it again and closes it. The full nominal
record lasts 164.014 simulated seconds. The cover has a passive sliding joint;
only the robot's bounded arm and finger actuators drive the motion.

The [asset](../../assets/cary_5000_v1/README.md) preserves the manufacturer's
main housing dimensions and distinguishes the main lid, removable front wall,
legacy extension base and extension cover. Its rear lid pocket is open in
both visual and collision geometry. The separately authored extension and
5 kg integrating-sphere module are not installed by this episode.

Unmeasured parameters are explicit: 1 N track friction, 0.5 N·s/m damping,
1200 kg/m³ cover density, 8 N closing command and a 20 N per-finger contact
limit. Contact pairs at the source finger faces use three-dimensional finite
face friction. The earlier mixed contact law produced asymmetric pad
compression and exceeded the force limit on reverse motion; those failed
records are retained. The corrected controller uses 2.5 mm, 0.4 s waypoints.

[Independent verification](runs/cary/verification.json) recomputes every
saved state's contact forces, continuous lid motion, numerical guards and
actuator ownership. It checks both released endpoints and the exact ordered
grasp/move/release sequence. The [suite](CARY_VERIFICATION.json) includes a
second initial arm state, missing pull, blocked slide and half-time-step run.
A missing pull must fail before grasp; the blocked physical slide must stop
before opening. Source snapshots and hashes distinguish accepted records from
later code changes.

The [recorded video](runs/cary/playback_manifest.json) presents the complete
trajectory in two chapters, with the end-effector view beside the instrument.
Media integrity checks remain separate from the physics receipt.

This accepts main-lid access only. Front-wall removal, extension installation,
accessory mounting, optical samples, cables and instrument configuration
remain obligations of the paper's optical workflows. The policy observes
simulator state rather than camera estimates. Whole-paper acceptance is 0/11.

```bash
python simulation/cooling_v1/check_cary_import.py
python simulation/cooling_v1/test_cary_suite.py --execute
python simulation/cooling_v1/verify_playback.py simulation/cooling_v1/runs/cary
```

The suite preserves old executions in history when `--execute` is specified.
Without that flag it verifies the exact stored records. A fresh execution
requires fresh rendering before the media verifier can pass.
