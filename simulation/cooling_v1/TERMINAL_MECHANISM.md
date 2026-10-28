# Passive USB-TC screw-clamp mechanism

Eight jig cases pass [independent verification](TERMINAL_MECHANISM_VERIFICATION.json).
The jig establishes a bounded contact-driven screw and wire-retention model;
it does not accept the robot wiring task or an electrical connection.

The selected model uses an unactuated screw, a translating captive plate and
an ideal 0.5 mm helical pitch. Only the contacting driver rotates. Its slot,
head counterbore, pressure plate and 24 AWG bare conductor have explicit contact
geometry. A freely moving 20 mm wire starts on a frictionless staging ledge.
There is no wire actuator or attachment weld. Dimensions, friction and the
thread approximation are inferred, not measured commercial-device properties.

The nominal test turns the bit until approximately 4 N of clamp force is
observed, retracts the bit, waits, and applies a recorded 1 N axial pull for one
second. The independent verifier reloads exact event states, recomputes forces
with the recorded applied load, and checks source hashes, thread/plate motion,
wire freedom and pull displacement. The selected displacement limit is 0.2 mm.
Both terminal banks, half time step and increased NoSlip iterations are checked.

Counterexamples remove the clamp, remove the bit, remove thread friction, or
use the regularized friction model without NoSlip correction. The last two
lose preload after driver withdrawal and pull out; all four are rejected.
This distinction matters: a nonzero friction coefficient alone did not prevent
slow thread creep. MuJoCo documents its friction approximation and corrective
solver in [friction](https://mujoco.readthedocs.io/en/latest/modeling.html#friction)
and [slow slippage](https://mujoco.readthedocs.io/en/latest/modeling.html#slow-slippage).
The selected 100 µs model uses three NoSlip iterations, compared against ten;
this bounded check does not establish indefinite preload retention.

Reproduce the jig and independent checks:

```bash
python simulation/cooling_v1/test_terminal_suite.py
python simulation/cooling_v1/verify_terminal_mechanism.py
```

The separate [robot cycle](TERMINAL_ROBOT_MANIPULATION.md) now has its own
148.949-second execution and independent evidence. Earlier failures remain
in ignored development directories. Its acceptance does not come from the
mechanism jig and does not accept the complete thermocouple path.
