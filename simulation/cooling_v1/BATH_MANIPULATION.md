# A25 lid and AC150 controls

The [recorded episode](runs/bath/playback_manifest.json) contains 103.422 seconds
of continuous robot physics: grasp and lift the removable lid, transfer it to
two parking rails, press and release standby/escape/standby, retrieve the lid,
transfer its weight onto the bath rim, release the handle and retreat.
The [viewer](sample.html) provides event seeking and the complete video.

Two initial arm states pass 46 independent checks each. Removing the handle
rejects the grasp; limiting standby-key travel to 0.1 mm rejects the key press.
These counterexamples pass 22 and 29 checks of their expected failures. The
records and their source snapshots are under `runs/bath` and `runs/bath_tests`.

The bath and lid use the manufacturer-informed A25/AC150 reconstruction in
`assets/thermo_a25_ac150_v1`. AC150 is a selected controller assumption because
the paper names A25 without identifying its controller. The free folded lid
has an open underside and a graspable arched handle. Its steel and handle
masses are derived from reconstructed volume and selected densities. The
seven spring-return keys have separately modeled travel and contact geometry.
Their stiffness, travel, friction and the passive offset pusher are inferred
simulation choices, not measured commercial-device qualifications.

The executor observes lid pose, handle contacts, key travel and support forces.
Before releasing the lid, it confirms that the parking rails or bath carry
more than half its weight. At the bath it relaxes the grasp to 1 N so the lid
can seat without the wrist supporting or jamming it. After retreat, the lid
must be within 2 mm and 0.035 rad of its target, with at least 80% of its weight
on the intended support and no finger load. The independent verifier reloads
saved states, recomputes these forces, checks the event order and motion
continuity, and checks every saved 5 ms state for arm clearance and the 25 N
per-finger lid-contact limit. Solver exhaustion or a numerical warning fails
the live run.

No object actuator, grasp weld or runtime object-pose assignment transports
the lid. The robot starts with a passive pusher mounted to its hand; installing
or exchanging that tool is not part of this record. The dry-bath sequence does
not press the pump/heater start key. Physical key travel does not qualify the
controller's electronic state or temperature program.

Filling, drainage, copper-block handling, probe placement, wiring and calibration
remain separate obligations. This record does not accept the CALIBRATE branch
or any complete-paper branch. The separate load-handling candidate in
`run_bath_loading.py` retains development status until its geometry, task
profile and complete physical episode are independently accepted.

Reproduce in the environment described in [README.md](README.md):

```bash
python simulation/cooling_v1/test_bath_suite.py --execute
python simulation/cooling_v1/render_device_episode.py simulation/cooling_v1/runs/bath --kind bath
python simulation/cooling_v1/verify_playback.py simulation/cooling_v1/runs/bath
```

Omit `--execute` to recheck the existing four physical records without replacing
their traces. Existing outputs are archived by the executor before a rerun.
