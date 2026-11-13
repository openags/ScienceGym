# Ideal-tek AA.SA.T.6 passive tool candidate

This candidate is **not selected for the laboratory or qualified for robot
grasping**. It separates a source-based rest shape from the prescribed
deformation in the existing workflow movie. No existing laboratory asset,
movie or robot trial is changed by this directory.

The [manufacturer product page](https://www.ideal-tek.com/scheda.php?c=ptfe-coated-tweezers&f=8&idp=4384&l=3&m=search)
gives a 130 mm length, 11.5 mm width, 12.5 mm height, 8 mm unloaded tip opening,
0.5 × 0.4 mm tips and 18 g net mass. The
[product sheet](https://www.ideal-tek.com/public/upload/PDS/AA.SA.T.6.IT.pdf),
[SA material sheet](https://www.ideal-tek.com/public/files/SA%20Technical%20DataSheet.pdf)
and [T coating sheet](https://www.ideal-tek.com/public/files/T%20Technical%20DataSheet.pdf)
describe PTFE-coated steel. Material calculations use the source's nominal
316L density of 8,000 kg/m³ and Young's modulus of 200 GPa. These values do
not provide a calibrated assembled-tool force curve. Local PDF downloads
failed with HTTP 403; sources were read through web access. No manufacturer
PDF is redistributed.

Interior thickness, spring profile, coating contribution, damping and
pairwise friction are inferred. The rest geometry matches the listed
dimensions and nominal mass; this is not manufacturer CAD or an established
visual match to every detail. Each revision preserves its builder and source
manifest. The original revision-01 source snapshot contains an incorrect
cache description; the current `sources.json` corrects that provenance.

The first candidate used a single bending mode per arm with internal joint
couplings. Subsequent candidates use independent passive rotational springs
along segmented steel arms. They have no tool actuators, attachment welds or
runtime pose assignments. The contact-characterization fixture mounts the
heel, disables gravity, and uses two motorized spherical indenters. It is a
component test fixture, not robot execution or an allowable laboratory aid.

| Revision / contact fixture | Result |
| --- | --- |
| 01 | Coupled-mode model unstable before useful contact. |
| 02 | Distributed springs unstable at 2 ms; the highest mounted-heel mode is about 110 kHz. |
| 03 | Rayleigh damping and 0.5 ms step complete closure/release, but contact penetration reaches 1.485 mm and fails. |
| 04 | Stiffer contact at 0.5 ms becomes unstable. |
| 05 | At 0.1 ms, basic closure/release, penetration and exact replay checks pass. Additional hold review fails: contact chatters and the held tip gap varies by 2.169 mm. |
| 06 | A coarser four-segment model still fails hold stability, with 1.173 mm gap excursion. |
| 07 | Interrupted characterization; the incomplete record is retained. |
| Passive revision 07 / contact 08 | With the discrete integrator at 0.1 ms, closure/release and hold checks pass. Peak force is 2.850 N, minimum gap is 3.665 mm, and maximum contact penetration is 0.0242 mm. |
| Passive revisions 08–10 / contacts 09–11 | Changing only the step to 2, 0.5 or 0.2 ms fails the preregistered comparison. The two finer candidates are stable but exceed the 5% peak-force agreement gate. |
| Passive revision 11 / contact 12 | The finer 0.05 ms comparison passes: held-gap difference is 0.00109 mm and peak-force difference is 3.23% relative to contact 08. |

Fixture 05 closes the 8 mm opening to a minimum of 2.494 mm and returns to
8 mm. Maximum intended penetration is 0.209 mm; replay position and velocity
errors are zero. Its approximate peak linear bending stress is 130 MPa,
below the material sheet's 200 MPa minimum yield value, but this is not a
validated stress field. Its failed hold review overrides any interpretation
that these basic checks establish a usable grasp. The hold-quality gates were
introduced after observing chatter and are explicitly development checks.

The [time-step comparison](timestep_compatibility_04/review.json) supports the
0.1 ms mounted-heel component result against a finer step. It does not validate
spatial discretization, measured mechanics or the laboratory's 2 ms whole-robot
integrator. The full robot's integration settings have not been changed.

Two normal-gravity free-support checks retain the tool's free joint, with no
actuators or attachment equalities: [edge support](free_support_01/review.json)
and [broadside support](free_support_02/review.json). Both settle and replay
exactly; maximum support penetrations are 0.0250 and 0.0769 mm respectively.
These check rest stability on a plane, not placement on the actual workbench.

The source-hand search includes the wrist housing, finger joint limits, both
opposed tactile pads, and a 1 mm minimum support-plane clearance. Early fits
were rejected for table intersections or contact with the thumb housing.
[Refinement 06](hand_fit_06/review.json) retains one pregrasp with 1.121 mm
hand-to-plane clearance and pad gaps of 0.468 and 0.496 mm. This is a local
geometric candidate, not a qualified grip or full-arm path.

`check_source_hand_contact.py` develops closure/release tests using the actual
source hand, its six motors and scalar tactile observations, with a free tool
under gravity. The wrist is mounted for this component diagnostic; whole-body
balance, visual localization, pickup and carrying remain separate requirements.
The parent-filter report preserves the original robot's implicit adjacent-body
collision filtering after that mount and excludes no tool or support contacts.
The first complete [source-hand trial](source_hand_contact_03/review.json)
fails: the tool translates 17.609 mm, and the selected tactile pads do not form
a sustained opposed grip. Its retained contact diagnosis identifies forces on
the adjacent distal index/thumb phalanges before pad contact. A separate
`--feedback encoder_load` development mode declares those contact regions
before execution and estimates resisting torque from encoders, previous motor
commands and robot-only dynamics. It receives no plant contact force or object
identity and does not claim calibrated hardware force/current conversion.
The first encoder-load [trial 04](source_hand_contact_04/review.json) still
fails: 12.363 mm horizontal motion and only 0.799 mm tip closure. The
pose optimizer in `align_source_contact.py` then aligns the source contact
regions while checking the complete distal hand, wrist housing and plane.
[Alignment 02](hand_align_02/review.json) finds one candidate among 48 tested
targets. With the same controller, [trial 05](source_hand_contact_05/review.json)
reduces maximum horizontal motion to 3.708 mm, with 2.928 s of bilateral load
and zero physical/controller replay error. It still fails the unchanged
1 mm closure gate: closure is only 0.271 mm. The thumb moves substantially
upward while curling, and contact is lost before release. Neither test
demonstrates a stable held tool. Searches 03 and 04 add closure-direction
constraints and retain zero accepted flat-bench poses; this bounded search
does not prove that all flat-bench grasps are impossible.

[Laboratory reach screen 02](laboratory_reach_02/review.json) tests 144
base/tool-yaw/arm-seed combinations for the alignment-02 candidate in the
existing full G1 and laboratory model. Ten reach the palm target and nine
pass static contact bounds. Floor contact is identified through the frozen
laboratory import, not by treating every ankle/environment collision as a
sole contact. Tool insertion, entry/exit, balance and perception are untested.

`check_tray_support.py` investigates an ordinary Buerkle tray rim as a
possible initial tool support. Both tray and tool retain free joints and
gravity. Attempts 01–06 inherited tool contact defaults into the imported
tray and are invalid as source-preserving support tests; all records remain.
The corrected builder scopes tool defaults to the tool and checks all tray
contact parameters against the original compiled laboratory model. Attempt
07–09 show the tool slipping off a single edge, including an attempt that
starts without tool/rim penetration. A different declared arrangement spans
the tray's two existing corner rims. Attempt 10 settles there but fails its
5 mm initial-displacement gate, moving 8.444 mm. This failure is retained.
[Support 11](tray_support_11/review.json) and
[support 12](tray_support_12/review.json) continue the recorded settled
qpos, qvel and warm-start state for separate 3-second support windows. Both
pass: root displacement is about 0.003 mm per window, maximum penetration
0.000153 mm, and the two rims together support the 0.17658 N tool weight.
These are continuations of one settling attempt, not independent trials or
robot placements. Support 12 also distinguishes its original authoring-seed
clearance from the actual continued state's signed contact distance; the
support-11 contract's `compiled_tool_tray_initial_clearance_m` refers to the
authoring seed, not its continued initial state. No tray attachment or robot
fixture is introduced.

`support_geometry.py` verifies the support sources and supplies actual
compiled tray collision geometry to the offline hand fit. Search 05 is
interrupted after three rejected candidates to replace expensive obstacle
distance queries with conservative per-link convex proxies during search;
the original source hand triangles remain mandatory for final acceptance.
The source-hand diagnostic can now import the freely resting tray while
preserving its contact parameters. Grasping from this arrangement remains
unqualified until a new hand-contact execution and independent review finish.

The completed alignment searches 06 and 07 each reject all 48 candidates.
`search_opposed_grasp.py` therefore derives new postures from the source
finger kinematics rather than relying on the presentation film's hand poses.
Its accelerated hand FK matches the existing source FK at the checked joint
extremes and midpoint. Search 03 tests 324 intrinsic solves and finds one
distinct opposed fingertip configuration, but its 96 placements all fail
whole-hand/tool or support checks. Search 04 retains those rejected geometry
seeds explicitly. Search 05 opens the acting fingers before placement and
checks 288 placements. It retains 78 source-clear noncontact candidates;
none meets the tighter initial pinch/alignment gates. Searches 01 and 02
failed at startup; their frozen scripts, logs and failure records remain.

An explicit `--pregrasp-index` may use such a clear, inward-moving noncontact
start in a new physical closure experiment. It never relabels that seed as
an accepted pinch, and it does not relax any dynamic grasp requirement.
[Source-hand contact 06](source_hand_contact_06/review.json) exercises this
path with the original free tray and all its contact parameters preserved.
The 11-second run and full physical/controller replays finish exactly, but
the tool slips 25.834 mm horizontally and falls into the tray. Sustained
bilateral load, support penetration, retained position and released gap all
fail. Its global minimum-gap check also counted closure caused by the fall;
the retained report is not rewritten. The current verifier requires closure
under simultaneous allowed index/thumb load and bounds three-dimensional
tool translation, so a support impact cannot count as successful squeezing.
Initial and recorded 3/3.5/4-second views and the controller diagnostic are
retained with the failed attempt.

[Laboratory reach 03](laboratory_reach_03/review.json) finds six reachable,
statically clear full-G1 poses among 144 combinations for this new pregrasp.
It retains the full existing room and source floor classifications. The
proposed tool/tray placement, entering motion, balance and grasp are not
qualified by this reach screen.

The current hand controller intersects requested closure with source driver
limits. Optional `--detect-grip-loss` detects loss of previously established
encoder-derived opposing load and returns the fingers to their initial
posture, retaining a failure rather than continuing to close on an absent
tool. The thresholds are declared control assumptions, not calibrated
hardware force registers. [Trial 07](source_hand_contact_07/review.json)
detects lost opposing load and starts release at 4.017 s. The full physics,
motor and abort-event replays agree exactly. The grasp still fails, and the
new load-attributed closure check correctly rejects the fall-induced closure:
minimum gap under bilateral load is 7.834 mm.
Middle-finger searches 03–05 investigate an ordinary third-finger support
instead of adding an attachment or fixture. Search 04 did not recompute
the parent's positive tray-clearance bound for the moved middle finger;
search 05 adds that conservative hull-distance check and is the usable
geometry revision. It finds nine clear pregrasp candidates with the middle
finger 0.067–0.493 mm above a tool arm. Trial 08 uses candidate 3 and the
existing middle motor to hold its angle. Its completed review reports zero
middle-finger load and the same slip/fall, so it provides no supporting grasp.
Neither test grants pickup or branch qualification.

Trial 09 investigates `--balanced-closure`: source pad-center Jacobians and
measured hand encoders set equal 0.5 mm/s opposing motion and equal 0.6 N
estimated holding-force targets. The estimate uses only the robot's own
projected contact lever, not simulator contact forces or object coordinates;
it is not a calibrated hardware force model. A finite-difference check of the
motor-coupled pad Jacobians passes with maximum differences below
0.000000134 m/rad. The frozen trial-09 contract retains legacy fixed-rate
fields alongside the selected balanced profile; its separate clarification
identifies those inactive fields, and the current builder removes them when
the balanced profile is selected. [The completed trial](source_hand_contact_09/review.json)
keeps the tool supported, with 2.104 mm maximum translation, sub-micrometre
contact penetration and exact physical/controller replay. It still fails
sustained bilateral load and loaded tip closure. An additional replay of all
11,000 sensor packets reproduces the motor commands exactly and confirms zero
packets in the gripping state: the light-contact target was below a threshold
that had to be continuously exceeded to enter gripping. The corrected balanced
controller latches contact with a declared lower release threshold and holds
the light load bidirectionally while the opposite finger arrives.
[Trial 10](source_hand_contact_10/review.json) tests this change with the same
scene and physical acceptance thresholds. It enters the gripping phase, but
the tool again slides off its support: maximum translation is 57.256 mm,
and the actor begins its loss response at 5.367 s. Physical, motor, internal
contact-state and abort-event replays all agree exactly. No pickup is
qualified. The logged `gripping` field in this frozen trial is the latched
phase-entry flag, not evidence of continued contact after release or loss.
The next integration must test coordinated arm/finger motion using the full
G1; changing this mounted diagnostic's state transition is insufficient.

Additional numerical candidates are not selected automatically. The coarse
four-span discrete model (passive 12 / contact 13), elliptic friction cone
(passive 14 / contact 14), and longer contact response time (passive 15 /
contact 15) all pass the mounted component's basic and hold checks, but change
the contact-force response. Their parameters are inferred, not manufacturer
calibration. The original passive-07 hand trials remain the comparison;
the laboratory model and its integrator remain unchanged.
All failed fixtures are retained. Handheld operation, specimen retention,
spatial torsion and laboratory integration remain open.

From the repository root, use the simulation environment and fresh output
directories:

```sh
python assets/idealtek_aa_sa_t6_v1/build_passive.py /tmp/tweezer-new
python assets/idealtek_aa_sa_t6_v1/check_passive_contact.py /tmp/tweezer-new /tmp/tweezer-contact-new
python assets/idealtek_aa_sa_t6_v1/review_passive_hold.py /tmp/tweezer-new /tmp/tweezer-contact-new
```

Run the hold review even when investigating a failed initial contact review.
The default builder retains the older integration choice. Reproduce the stable
component candidate with `--integrator discrete --timestep .0001`; compare a
finer step before changing laboratory integration. No grasping or complete
paper-branch success is credited by these fixtures.
