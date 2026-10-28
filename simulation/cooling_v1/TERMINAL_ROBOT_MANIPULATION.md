# USB-TC robot wiring cycle

The [nominal record](runs/terminal/result.json) contains 148.949 seconds of
continuous robot physics and passes [43 independent checks](runs/terminal/verification.json).
The same 24 AWG extension is grasped, inserted, released into a passive clip,
clamped by a contact-driven screwdriver, pulled, unclamped, withdrawn and
returned to its original support. This record covers one terminal end.

The reconstruction uses the source-specific MCC USB-TC asset and selected
needle jaw extensions, an offset powered screwdriver and a two-position
passive wire clip. The full selected 0.6 m lead consists of a 42 mm rigid end
and a constrained string tail; cable bending and torsion are omitted. The
passive screw/captive plate model uses an inferred 0.5 mm pitch and selected
friction. The contacting screwdriver rotates through an actuator; the wire,
screw and pressure plate have no actuators or grasp welds.

Insertion reaches 4.994 mm while the wire is held. The gripper then opens,
and the passive clip retains the lead for driver access. Tightening stops
after an observed 4 N clamp load. After driver withdrawal, the robot regrips
the insulation and sustains a measured axial pull above 1 N for 0.3 seconds.
Independent saved-state checks find a 1.083 N peak and a maximum wire
displacement of 2.85 micrometres during that pull. The same robot loosens the
terminal, extracts the lead and returns its end within 0.297 mm of the
original support. These are selected-model results, not hardware measurements.

The independent verifier recomputes screw motion, contacts, clamp load,
driver load, cable strain, grip geometry and the complete ordered event chain.
It checks the archived input hashes and continuous 5 ms trace as well as the
absence of payload actuators and welds. Every saved cable edge remains within
0.048% of its rest length. The executor's finer 3 ms contact-gap guard is
explicitly separate from what a 5 ms archive can establish independently.

Removing the bit must fail when seating the driver in the physical slot;
removing the pressure plate must fail at the clamping operation. Those
records pass [23](runs/terminal_tests/missing_bit/verification.json) and
[25](runs/terminal_tests/missing_clamp/verification.json) counterexample checks.
The [passive mechanism jig](TERMINAL_MECHANISM.md) has additional independent
thread-friction, solver and terminal-bank tests. Full robot runs with a
perturbed initial arm state pass 43 checks. The halved-time-step run fails
the final regrasp: wire/pad axis error reaches 0.1053 rad against the unchanged
0.1 rad bound. Its failure is retained while the gentle-grasp controller is
being evaluated; full refinement acceptance is pending. The first gentle-grasp
candidate also fails the nominal and perturbed-state insertion approaches at
32.666 seconds: wire/pad axis errors reach 0.1015 and 0.1024 rad. Those
development results do not replace the accepted archived recordings.

The [two-chapter playback](runs/terminal/playback_manifest.json) covers the
entire episode at 12 fps, including initial approach and final return. Its
[10 media checks](runs/terminal/playback_verification.json) are separate from
the physical acceptance evidence.

The commands below exercise the current development controller. Acceptance of
the stored nominal recording applies to its archived source hashes, not to a
claim that the current candidate passes.

```bash
python simulation/cooling_v1/run_terminal.py --out runs/terminal_debug/reproduction
python simulation/cooling_v1/verify_terminal_robot.py simulation/cooling_v1/runs/terminal_debug/reproduction
python simulation/cooling_v1/render_device_episode.py simulation/cooling_v1/runs/terminal_debug/reproduction --kind terminal
python simulation/cooling_v1/verify_playback.py simulation/cooling_v1/runs/terminal_debug/reproduction
```

The paired thermocouple circuit, fine-wire transition, electrical continuity,
calibration handling and continuity between workstations remain required
before a complete paper branch can be accepted. The controller uses privileged
simulator observations. This record supplies no camera-policy qualification.
