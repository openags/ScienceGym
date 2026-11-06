# G1 humanoid contact runtime

Latest station integration (6 November 2026): the [20-second approach to the
existing tool bench](runs/dex3_groot_station_approach_01/station_view/overview.mp4)
passes its [native walking review](runs/dex3_groot_station_approach_01/walking_review.json)
and [eight arrival checks](runs/dex3_groot_station_approach_01/waypoint_review.json).
Actual arrival error is 113.98 mm within the predeclared 150 mm station region;
maximum odometry error is 46.16 mm. The separate aisle waypoint trial also passes.
Neither run includes equipment manipulation or repeated navigation acceptance.

The new `station_pickup_actor.py` joins this arrival to a two-second stationary
controller transfer, eight-second coordinated waist/arm/hand preparation,
native-depth map registration and the visual tool-pickup actor. Its estimate is
initialized from encoders/IMU and odometry; physical state is never reset at a
handoff. All 13,161 recorded walking-prefix outputs match exactly, and the first
stationary torque solve is finite and within source limits. A fresh uninterrupted
`dex3_station_pickup_01` run stops at the preparation timeout before visual pickup.
Its [recorded encoder diagnosis](analysis/dex3_station_preparation_diagnosis_01/review.json)
finds only waist pitch outside the original 40 mrad target bound: 45.011 mrad,
with negligible remaining velocity. The constrained preparation controller now
weights waist-pitch tracking by three, preserving the same targets, physical
model and acceptance. Fresh `dex3_station_pickup_02` passes preparation and
native-depth registration, then stops at 27.600 s because the observed grasp
has no collision-screened arm path from the arrival stance. Its complete
sensor/controller and native physics replay match exactly, and contact bounds
pass, but the attempt fails because no pickup was executed.
The [sensor-prefix planning diagnosis](analysis/dex3_station_tool_planning_02/review.json)
reproduces all 27,601 motor outputs exactly. Three observation-supported pose
alternatives fail at that stance; a 60 mm forward stance screen yields a path.
The walker now accepts an explicit forward stopping distance, preserving the
original 60 mm default. Fresh `dex3_station_pickup_03` uses 5 mm, with the same
laboratory, physical acceptance and source limits. It finishes at 82.369 s
without a controller failure. All 82,370 isolated controller responses and
18 camera frames replay exactly, and source motor limits pass. Full native
physics reproduces the trajectory exactly but rejects finger/tray contact
during replacement, first exceeding the unchanged 20 micrometre bound at
75.8752 s. The joined review therefore fails despite successful arrival and
preparation. Its
[continuous station video](runs/dex3_station_pickup_03/station_view/overview.mp4)
shows walking, preparation, visual pickup, lift, replacement and withdrawal.
This failed attempt is not a physically accepted component or a paper branch.

`--station-carry` now composes the same sensor-based arrival with the carrying
actor. The [handoff diagnostic](analysis/dex3_station_carry_handoff_01/review.json)
matches 24,801 recorded commands, including the first carrying-actor response.
Its return reference is the sensed pickup stance. The independent evaluator
measures carrying displacement from that handoff, excluding preceding unloaded
travel; six reference-selection regression tests pass. Fresh
`dex3_station_carry_01` starts in the original aisle with carry08's contact
model and the separately declared 2 ms sole response. It reaches pickup and
lift, then stops at 86.622 s: the loaded-arm guard mistakes eight shallow
sole/floor support contacts (12.8–13.0 micrometres) for prohibited collisions.
The revised guard binds source-labelled architectural floors and official sole
geometries. Only upward sole support within the unchanged 1 mm bound is
permitted; six regression cases retain rejection of deeper contact, floor-side
contact, finger/floor contact, sole/bench contact and self-contact. The frozen
[sensor-prefix diagnostic](analysis/dex3_station_loaded_plan_02/review.json)
reproduces all 86,622 earlier responses exactly and finds a clear raise/retract
plan at the previous failure point. Fresh `dex3_station_carry_02` is running
from the original aisle; its physical model and acceptance are exactly unchanged.
Full physical review of the failed attempt continues; no qualification transfers.

The latest tool-force diagnostic reaches a closed tip gap for 1.711 s but loses
its grasp while reopening: relative drift grows from 9.756 mm at 72 s to
40.704 mm at 76 s. It fails, and its restored checkpoint cannot qualify a skill.
The [contact comparison](analysis/dex3_tool_contact_revision_01/review.json)
checks 30 invariants between that controller candidate and fresh
`dex3_tool_stroke_11`: initial state, controller prior, source geometry, masses,
friction, motor limits and physical acceptance remain identical. The new run
uses the explicit elliptic/10 impedance-ratio/0.99 hand-tool contact model
already exercised by carry08; this is an uncalibrated simulation model choice.
It starts from the original scene and requires its own full physical review.

Failed-controller replay now retains the last event list, matching the recorder
when a terminal error response omits events. The [separate revised review](runs/dex3_tool_stroke_10/controller_replay_revision_03.json)
reproduces all 71,573 responses and the complete event history with zero error;
the original failed review is preserved and the physical task still fails.
Legacy recordings explicitly report that their original result omitted an event
file digest. Future tool recordings pin it at recording time.

The [preparation geometry screen](analysis/dex3_station_handoff_screen_01/review.json)
rejects arm-only preparation because the hand intersects the hip; coordinated
waist/arm preparation clears all 41 static samples. Dynamic clearance remains
part of the new run's independent review.

Latest native walking result (6 November 2026): the
[13-second G1/Dex3 attempt](runs/dex3_groot_walking_05/overview.mp4)
passes all 18 [independent checks](runs/dex3_groot_walking_05/walking_review.json),
including source motor limits and exact sensor/controller/physics replay.
It travels 1.1022 m and stops; maximum sole penetration is 0.6584 mm under
the unchanged 1 mm bound. The plant uses the explicitly authored 2 ms
sole/floor pair response. This is one unloaded timed attempt, not repeated
walking qualification, carrying, navigation or a paper branch.
The fourth attempt passes contact checks but travels only 0.9971 m, below
the original 1 m requirement; its failed review is preserved. Encoder/IMU
odometry on that record has 29.91 mm maximum XY error. Separate sensor-based
waypoint and existing-tool-station approach trials have passed their single-run reviews.

Fresh carry08 now passes all 27 [native physical checks](runs/dex3_visual_carry_08/physical_review.json),
[isolated sensor/controller replay](runs/dex3_visual_carry_08/controller_replay.json)
and [source motor limits](runs/dex3_visual_carry_08/source_limit_review.json).
Its 146.731-second visual pickup, loaded out-and-back, release and empty-hand
return contains 72.401 s of held carrying, 98.91 mm maximum loaded base excursion,
both feet stepping, no contiguous loss of three-finger load and 5.727 mm maximum
tool/wrist translation drift. The authored out-and-back goal is only 120 mm;
this is one complete component attempt, not cross-station or repeated carrying
qualification. Its [publication boundary](runs/dex3_visual_carry_08/publication_status.json)
distinguishes available reports from raw replay files. Earlier failed carry07
and restored-state diagnostics remain separate evidence.
For tool use, a new optional two-joint-per-finger controller regulates
inferred inward load while retaining the own fingertip material point's
tangent position. Nine analytic Jacobians match independent finite
differences within 3.35e-10 m/rad. Its [native continuation fails](analysis/dex3_tool_cartesian_evaluation_01/review.json):
retention is lost before a qualified reopening. A [source-grasp workspace
screen](analysis/dex3_tool_stroke_workspace_01/review.json) finds only 1.3 mm of
coordinated inward travel for the old grasp, versus at least 3 mm for candidate 9
under the same joint margins and command excursion. Candidate 9 passes the new
initial-scene check. Its fresh visual pickup/stroke run stops at 71.272 s at
the legacy single-joint closure-direction guard. At the terminal encoder
state the two-joint Jacobians remain nonsingular. The guard now checks the active
control mode, including a 1 mm/rad minimum singular value and condition number
below 100 for coordinated control. The [sensor-prefix comparison](analysis/dex3_tool_coordinated_guard_02/review.json)
matches all 71,272 preceding commands exactly and produces a finite, source-bounded
command at the former stop. Fresh `dex3_tool_stroke_10` detects loss of
three-finger load at 71.571 s, then its abort encounters the legacy scalar
lever guard. It fails at 71.572 s. The load estimator now retains coordinated
coordinates through abort and release. An explicitly restored-state diagnostic
tests lower squeeze targets of [2.45, 1.1025, 1.3475] N, a doubled normal
admittance gain and a stricter 3% tracking band. The earlier native recording
closes the tips before reaching the 3 N target, then exceeds drift and
tip-contact limits. Physical gap, drift, contact, speed and dwell acceptance
remain unchanged. No successful tool use or fresh continuous recording is
inferred from that diagnostic.

Current execution update (6 November 2026): carry07's complete native replay
has finished. Its carrying, load continuity, return and release-support checks
pass, but hand/tray penetration and the separately checked thumb speed fail.
The [corrected lowering continuation](analysis/dex3_release_inset_checkpoint_01/result.json)
finishes without hand/tray contact and stays within hand limits. It is a
restored-state diagnostic; fresh uninterrupted carry08 now passes its separate
single-attempt review as recorded above.
The [supported ramped tool stroke](analysis/dex3_tool_supported_ramp_evaluation_01/review.json)
still loses retention during reopening and is not qualified.

Two fresh current-Dex3 trials of the earlier official Unitree walking policy
also fail. The [second native review](runs/dex3_official_walking_02/walking_review.json)
confirms exact physics and sensor/controller replay, but finds later self-contact,
a hand-speed violation, backwards drift and failure to stop. Its initial pose
passes the newly added collision gate. The first trial's open thumb intersected
the hip at time zero; its failed evidence remains available.
The alternative [official NVIDIA decoupled policies](locomotion_groot_policy/SOURCE.json)
are now downloaded with their pinned Git LFS hashes and licenses. The
[adapter comparison](analysis/groot_policy_adapter_01/review.json) matches
upstream features, history and output references exactly on 600 recorded sensor
packets, covering standing and walking modes. The first
[full-room native review](runs/dex3_groot_walking_01/walking_review.json)
now records 1.0065 m forward travel and a commanded stop. All checks except
the original 1 mm sole-contact penetration bound pass, including source motor
limits and exact controller/physics/sensor replay. The
[complete-body camera view](runs/dex3_groot_walking_01/visual_review_02/overview.mp4)
shows this failed trial without changing its trajectory.
The [second full review](runs/dex3_groot_walking_02/walking_review.json) also
fails sole penetration, with a 1.495 mm maximum and no other robot penetration.
Its geom-only contact revision has no physical effect: all 32 explicit
sole/floor pairs retain their original 4 ms response, and its trace is
byte-identical to the first run. The frozen revision's claim that physical
response changed is corrected by
[this separate diagnosis](analysis/dex3_sole_response_diagnosis_01/review.json).
The runner now edits the effective pairs and checks both compiled parameters
and actual first-contact parameters using a separate, discarded unactuated
probe. A fresh fourth run tests 2 ms pair response under the same acceptance
bounds. The third preparation stopped at an overly restrictive initial-contact
gate before any walking; exact tangency can have zero initial contacts.
The response is an authored simulation parameter, not a measured sole property.
Any manipulation on the revised plant also requires fresh qualification.
Neither interface agreement nor these walking videos qualify carrying,
navigation, or a paper branch.

The latest [59.09-second visual tool recording](runs/dex3_visual_grasp_04/overview.mp4)
passes all 18 [independent physical checks](runs/dex3_visual_grasp_04/physical_review.json),
[isolated controller replay](runs/dex3_visual_grasp_04/controller_replay.json) and
[source motor torque/speed checks](runs/dex3_visual_grasp_04/source_limit_review.json).
From the declared station posture, G1 observes the free tweezer in native RGB-D,
plans and executes its approach, then grips, lifts, lowers, releases and withdraws.
All 59,089 motor outputs and 17 camera frames replay exactly. The tool rises
25.08 mm and remains lifted without tray support for 1.97 s. Cameras are used
for initial localization; approach and holding use proprioception and inferred
motor-load feedback. This single attempt does not qualify tool use on a specimen,
carrying, randomized repeatability or a paper branch. The earlier
[23.58-second pregrasp trial](runs/dex3_tool_grasp_06/physical_review.json)
remains separate. The earlier walking/window run uses Inspire hands; that result
does not transfer automatically to the three-finger model. There remain
**0 of 11 qualified paper branches and 0 qualified complete campaigns**.

Free-tool actuation now has a separate optional squeeze/reopen controller and
[declared tip-gap contract](runs/dex3_tool_actuation_candidate_02/contract.json).
The first [restored-state trial](analysis/dex3_tool_actuation_checkpoint_01/result.json)
stops two milliseconds after squeezing starts: the balance solver returns
`AlmostSolved`, which remains rejected. An isolated diagnostic reproduces all
49,988 prior responses and the same failure, retaining the exact
[actor-owned balance problem](analysis/dex3_tool_actuation_balance_01/result.json).
The [numerical comparison](analysis/dex3_tool_actuation_balance_comparison_01/review.json)
finds a full-accuracy solution with finer KKT regularization/refinement, without
changing the objective, constraints or tolerances. `conic_balance.py` tries that
setting only after the original solve is rejected; infeasible results remain
rejected. The [second continuation](analysis/dex3_tool_actuation_checkpoint_02/result.json)
passes the old numerical stop but [fails tool actuation](analysis/dex3_tool_actuation_evaluation_02/review.json):
minimum squeezed gap is 1.402 mm versus the unchanged 0.5 mm bound, and the tool
migrates out of the grasp during reopening. Its own-force target event does
not establish tip closure. The next [prepared candidate](runs/dex3_tool_actuation_candidate_03/contract.json)
ramps the index/middle proximal references by -0.04 rad over 12 seconds while
the tool is still tray-supported, then requires a fresh load dwell before
lifting. Nonclosing joints retain own-motor load compensation, following the
carrying grasp design. The [third restored-state trial](analysis/dex3_tool_actuation_checkpoint_03/result.json)
has now finished and [fails independent actuation assessment](analysis/dex3_tool_actuation_evaluation_03/review.json):
the squeezed gap reaches only 1.636 mm, and reopening loses the grasp. Its
frozen contract incorrectly records a 0.15 Nm observer abort threshold; the
frozen preshape actor actually uses 0.3 Nm. This discrepancy remains disclosed;
the frozen contract is not rewritten and no qualification is granted.
`evaluate_tool_actuation_checkpoint.py` checks actual native tip separation,
tool retention, finger loads and closure/reopening dwell independently of the
actor's inferred loads. No successful tool stroke or specimen pickup is claimed.
The [held-tool camera inspection](analysis/dex3_held_tool_visibility_03/review.json)
also finds substantial head-camera occlusion after grasp; initial localization
is not evidence of visible tool tips during use. A separate
[kinematic inspection-pose screen](analysis/dex3_tool_inspection_pose_01/review.json)
finds 14 of 35 sampled paths within the original contact bounds. A 60 mm raise
and 0.5 rad wrist rotation increases visible tool pixels from 52 to 2,531.
That screen uses a retained state and a rigid-grasp hypothesis; it is neither
an executed motion nor online tool tracking. A subsequent [sensor-based physical
continuation](analysis/dex3_tool_inspection_checkpoint_01/result.json) executes
the inspection raise and wrist rotation, but detects no tool in any of its ten
inspection observations and loses three-finger load on return. Its 51 native
camera frames are retained. The earlier visibility prediction therefore does
not establish successful online observation or physical retention. This failed
continuation has not undergone independent full-physics replay.
The [retained-frame diagnosis](analysis/dex3_inspection_observation_diagnosis_03/review.json)
also identifies an appearance failure: visible tool pixels become substantially
brighter when the wrist turns, and the pickup detector's dark threshold rejects
them. A new held-tool detector removes surfaces explained by own-robot source
meshes, then fits remaining native depth points to tool CAD. All three inspected
frames produce candidates whose retained pixels associate with the tool; all
three robot-only negative frames reject detection. This is an offline test with
reconstructed proprioception, not exact sensor replay or a qualified full/tip
pose. The [second physical continuation](analysis/dex3_tool_inspection_checkpoint_02/result.json)
reports ten detections in ten native inspection observations, but still loses
the grasp during its return motion and finishes at 65.290 s with a failure.
The completed [independent review](analysis/dex3_tool_inspection_evaluation_02/review.json)
reproduces all 46 native camera frames and the ten detections. It nevertheless
fails attempt completion, the inspection/return sequence and contact bounds:
after slipping on return, the tool contacts the tray at 60.0087 s with 0.2587 mm
penetration, above the unchanged 0.25 mm bound. This validates bounded observation
within a failed continuation, not successful tool retention or a qualified skill.
Nonclosing-joint compensation
alone did not fix retention. A new supported-grasp candidate establishes the
carrying controller's 2.4/1.2/1.2 N inferred load targets before lifting, with
a -0.04 rad proximal preshape and explicit 0.25 rad driver reference envelope.
Original source joint margins and 4 N physical load bounds remain unchanged.
The [third continuation](analysis/dex3_tool_inspection_checkpoint_03/result.json)
replays 37,462 prior sensor responses exactly, reaches the inspection hold and
records ten detected observations. It triggers the original motor-load protection
on return at 71.043 s and finishes its abort sequence at 79.143 s. Its completed
[independent review](analysis/dex3_tool_inspection_evaluation_03/review.json)
reproduces the trajectory, all 36 native camera frames and ten detector results,
but fails completion, the return sequence and original contact bounds. The heel
contacts the bench beyond the bound at 71.101 s. Peak actual finger load is
2.604 N; the motor-load protection event must not be described as a measured
4 N contact-force violation. This is not a fresh continuous pickup or a successful
observation/return skill. Its complete trace is retained in three verified
32 MiB-or-smaller chunks, with restoration instructions in
[trace_archive.json](analysis/dex3_tool_inspection_checkpoint_03/trace_archive.json).

A new rigid-heel grasp keeps the middle finger on the original heel and uses
thumb/index contacts on the original spring arms. The first planar candidates
collide with the tray; a 6 mm inward placement also [fails natural support](analysis/dex3_heel_tool_support_01/review.json)
and is not adopted. The selected outward placement [passes a three-second
unactuated support run and exact replay](analysis/dex3_heel_yaw_support_01/review.json),
with both original tray rims supporting the tool and 0.108 mm maximum penetration.
The [settled-state fit](analysis/dex3_heel_grasp_fit_05/review.json) accepts 24 of
54 hand candidates, and [full-room authoring](runs/dex3_heel_tool_station_01/review.json)
finds three clear whole-body poses out of 100. The complete room and all compiled
tool/tray geometry and material properties are retained. The [opened initial
posture](runs/dex3_heel_pregrasp_01/review.json) is only a declared starting setup.
The first [fresh native-camera trial](runs/dex3_heel_visual_actuation_01/result.json)
stops at 2.8 s because the selected observed pose has no feasible grasp IK.
It performs no pickup. An optional planner now retains separately fitted
pose hypotheses consistent across four native frames, with the original
surface-quality and clearance limits. Two [isolated sensor replays](analysis/dex3_heel_ambiguity_replay_02/result.json)
reproduce all 2,800 earlier responses exactly, but neither recovers a feasible
approach at that stance. A [sensor-derived stance screen](analysis/dex3_heel_stance_screen_01/review.json)
finds alternatives; the [selected initial stance](runs/dex3_heel_observe_start_02/stance_selection.json)
changes X/Y by -40/-20 mm and retains elbow margin. This is an authored initial
condition, not executed locomotion. A second fresh pickup/squeeze/reopen/release
trial, `dex3_heel_visual_actuation_02`, finishes at 54.320 s with motor-load
protection during reopening. The [native recorded-shape diagnostic](analysis/dex3_heel_stroke_kinematics_02/review.json)
finds only 6.11 mm minimum squeezed gap and 0.984 rad tool/wrist rotation on
reopening; it does not evaluate contact forces. The [unchanged-stiffness screen](analysis/dex3_tool_mechanical_grasp_screen_01/review.json)
estimates 8.27–8.40 N thumb load for these heel grasps, above the original 4 N
bound. Original beam grasps estimate 2.41–2.94 N. These are small-deflection
design estimates, not measured commercial-tool properties or dynamic success.
A new original-beam candidate ramps squeeze/reopen targets over two seconds
and uses a 3 N thumb squeeze target, retaining all physical acceptance bounds.
No grasp, tool-use or paper-branch qualification transfers from preparation.
The native tool-stroke evaluator now supports replay from the original initial
state: a compact window restore lost the unattended cover sleeping cache and
failed the unchanged exact-state tolerance. That failure is retained separately.

The latest [140.13-second loaded recording](runs/dex3_visual_carry_03/overview.mp4)
contains continuous visual pickup, four outward steps, four return steps and
lowering to the tray. Its [execution result](runs/dex3_visual_carry_03/result.json)
fails on residual finger load during release. The route commands only 0.12 m
outward travel; it is not cross-station work. Source motor-limit checks and
isolated controller replay pass. The completed [independent physical review](runs/dex3_visual_carry_03/physical_review.json)
fails six checks: attempt completion, stable released support, route completion,
continuous loaded carry, base return and preload before lift. Its loaded-state
predicate is interrupted for 1.0067 s and native prelift loading lasts 0.4974 s,
below the required 0.5 s. Exact trajectory replay establishes reproducibility,
not task success. This run and the separate restored-state release probes grant
no carrying qualification.

The earlier [78.73-second loaded attempt](runs/dex3_visual_carry_02/overview.mp4)
starts from the same native-camera observation and reaches one walking step,
but [fails independent acceptance](runs/dex3_visual_carry_02/physical_review.json).
The recorded robot, sensor and camera states replay exactly. The right ankle
exceeds its source range by 3.35 mrad, tool-to-wrist displacement reaches 28.95 mm,
and the loaded out-and-back/release route is unfinished. The
[recorded-state diagnosis](runs/dex3_visual_carry_02/carry_state_diagnosis.json)
locates the ankle violation during stepping. Neither this failed run nor the
separate restored-checkpoint probes qualify carrying or a paper branch.

The [release posture diagnosis](analysis/dex3_release_posture_screen_02/review.json)
finds that restoring the middle proximal joint during opening pushes its distal
link toward the tweezer. `--release-preserve-posture` retains the four non-closing
finger references from release entry while opening the three closing drivers.
Candidate 05 changes this controller behavior only; its physical acceptance,
world, observations and loaded-route contract are unchanged from candidate 02.
It still requires a successful fresh uninterrupted run after the diagnostic.
Its [restored-state trial](analysis/dex3_release_checkpoint_05/result.json)
removes finger/tool contact but still fails because the thumb touches the tray.
The [native contact diagnosis](analysis/dex3_release_load_05/review.json)
attributes the remaining signed motor load to that contact. Candidate 06 combines
the retained posture with the existing signed release-load feedback; acceptance
is unchanged. Its [restored-state release trial](analysis/dex3_release_checkpoint_06/result.json)
finishes without an execution failure. A fresh continuous run,
[`dex3_visual_carry_04`](runs/dex3_visual_carry_04/result.json), has finished
143.789 s from the original initial state without a controller-reported failure;
its [independent physics review](runs/dex3_visual_carry_04/physical_review.json)
now fails contact bounds, carry-load continuity, base return, tool return and
prelift loading. Its pre-release controller is unchanged. No fresh carrying
success has been established.

The passive optical scene is now joined to the visual tool-start contract.
The [initial RGB-D coupon diagnostic](analysis/optical_coupon_observation_06/review.json)
reports 0.246 mm center error on one native frame. Four stable observations can
gate tool approach with `--observe-optical-coupon`; this does not establish
sample pickup, coating-side recognition or optical manipulation. Both optical
tool trials have finished 59.09 s of execution and passed isolated controller
replay. Their independent physical reviews now both fail `contact_bounds`:
the sample/tray startup contact exceeds the unchanged 20 micrometre limit
used by the operation evaluator. Passing the separate 250 micrometre asset
support limit does not qualify either operation run. The actual four-frame
[runtime coupon evaluation](analysis/optical_coupon_runtime_observation_01/review.json)
fails the 1 mm position requirement with 1.069 mm error. The static single-frame
result therefore does not qualify runtime localization. An offline camera-frame
diagnosis attributes much of the error to localization of the robot camera;
using evaluator truth for attribution is not an actor correction or a pass.

The subsequent static-map registration uses the same pixel-centre depth
sampling as the native camera and rejects distant correspondences from loose
objects. The [recorded-frame test](analysis/optical_coupon_map_observation_04/review.json)
passes with 0.300 mm coupon-centre error; its earlier failed variants are retained.
A new five-second [isolated observation run](runs/dex3_optical_registered_observation_01/result.json)
then passes [actual runtime localization](analysis/optical_coupon_runtime_observation_02/review.json)
at 0.249 mm and exact controller replay. That bounded run intentionally stops
before completing the tool operation; its duration failure is retained. A fresh
full tool trial, [`dex3_optical_visual_grasp_03`](runs/dex3_optical_visual_grasp_03/result.json),
has finished 59.610 s without a controller-reported failure; its independent
physics review now fails the original sample/tray startup contact bound.
The separately corrected support configuration is not a pass for this recording.
Its first offline localization evaluator failed to
import a missing scene-builder dependency, before producing an assessment.
The evaluator now uses the self-contained, pinned collision loader; the failed
invocation remains recorded separately from the
[new evaluation](analysis/optical_coupon_runtime_observation_04/review.json).
All five initial-localization checks pass on the full 59.610-second recording,
with 0.249 mm accepted centre error. This evaluates the initial accepted pose,
not later tracking or sample handling.
These results do not qualify later pose tracking or specimen manipulation.

The [carry failure attribution](analysis/dex3_carry_acceptance_03/review.json)
separates inadequate return clearance from native contact losses and initial
standing drift. `--tool-lift-height` makes the commanded lift explicit while
retaining physical thresholds; lowering starts from the actual commanded lift.
The 45 mm candidate's [restored-state diagnostic](analysis/dex3_carry_clearance_checkpoint_01/result.json)
executes lift and starts walking without failure. Return/release, preload and
base-return acceptance still require further work and a fresh continuous run.

An optional empty-hand return uses the original declared base position after
release and withdrawal. Its [first checkpoint diagnostic](analysis/dex3_carry_return_checkpoint_01/result.json)
fails because the approach guard incorrectly requires the original pregrasp
finger pose after release. The revised guard checks actual encoder-derived hand
geometry and native source self-contact; the original approach preshape gate
and independent acceptance bounds remain. The
[second checkpoint diagnostic](analysis/dex3_carry_return_checkpoint_02/result.json)
finishes without an execution failure and returns the actual base to 0.822 mm
of its original XY position. Its 135,101-packet pre-change sensor prefix remains
exact. This restored-state diagnostic still requires fresh uninterrupted
pickup/carry/release verification. The separate
[`--grip-force-deadband` diagnostic](analysis/dex3_carry_grip_checkpoint_01/result.json)
does not resolve the prelift contact failure: native loaded contact totals
0.498 s in the final 0.5 s window. It is not adopted as a successful fix.
The [`--loaded-hand-damping-scale 2` diagnostic](analysis/dex3_carry_damping_checkpoint_01/result.json)
also fails the unchanged prelift criterion: native loaded contact totals 0.497 s
in the final 0.5 s window. Its native force window is retained for failure
analysis. The conditional integrated carry-05 run was therefore not launched.
Neither candidate has established continuous carrying success.

The [native-state collision comparison](analysis/dex3_native_grip_collision_02/review.json)
reproduces the original carry-03 prelift states and its 25 lost-load samples.
Tighter native CCD and single-contact CCD retain the same 25 samples; the legacy
collider has 56. Independent [source-triangle distances](analysis/dex3_grip_gap_geometry_01/review.json)
confirm positive gaps of about 0.7 to 27 nanometres at the three inspected
missing-contact states, with contact immediately before and after. The earlier
unmatched-state comparison is explicitly invalidated and retained.
The steel tool's 0.9999 contact impedance overrides the finger material in those
interfaces. A new [prepared sensitivity candidate](runs/dex3_carry_compliant_candidate_01/contract.json)
uses 0.99 only on 141 explicit fingertip/tool pairs. Source geometry, masses,
joint dynamics, friction, zero contact margin/gap and all pre-existing pairs are
unchanged, as are the physical acceptance bounds. This is an uncalibrated
simulation compliance choice, not a measured hardware material claim.
[`dex3_visual_carry_06`](runs/dex3_visual_carry_06/result.json) executes the
original-state trial with the separately diagnosed 45 mm lift, release and
empty-hand-return corrections, but stops at 136.140 s during lowering when the
frozen old balance solver rejects `AlmostSolved`. The [captured failure](analysis/dex3_carry_balance_capture_01/result.json)
reproduces all 136,140 accepted sensor responses exactly. The existing strict
numerical retry solves that unchanged QP with stationarity residual 4.03e-8;
[regression](analysis/dex3_carry_balance_regression_01/review.json) retains the
infeasibility rejection and original physical constraints/tolerances. The
[candidate replay](analysis/dex3_carry_balance_replay_01/result.json) reproduces
the whole accepted prefix exactly and resolves the final rejected packet.
The [fresh carry-07 recording](runs/dex3_visual_carry_07/result.json) finishes
its pickup, outward/return steps, release and empty-hand base return at 146.731 s
without a controller error. It does not pass acceptance: the [source motor
review](runs/dex3_visual_carry_07/source_limit_review.json) finds 12.408 rad/s
at the right thumb distal joint, above its unchanged 12 rad/s source limit.
The completed [independent full contact replay](runs/dex3_visual_carry_07/physical_review.json)
fails only its contact-bound check: the index finger meets the tray rim while
lowering. The other carrying checks pass, and the native preview video is ready.
Neither the numerical repair nor sequence completion grants carrying qualification.
The withheld carry-05 attempt has not been relabelled as an execution.

Exact reference/holder/cap surfaces pass [all six component cases](analysis/pike_reference_support_09/review.json).
Their [full-room support test](analysis/optical_runtime_support_09/review.json)
fails because the cap does not remain supported by the original tabletop.
An exact tabletop surface candidate preserves the original bevels and visuals;
its source distance and gradient audits pass. The subsequent
[complete-room support test](analysis/optical_runtime_support_10/review.json)
passes for specimen, reference and cap, including intended bench contact and
the unchanged penetration/load bounds. Its
[specimen-velocity correction replay](analysis/optical_support_velocity_recheck_10/review.json)
also passes, with exact retained states. The resulting
[operation station](runs/dex3_optical_observe_start_02/review.json) preserves the
robot/tray/tool initial states and all source actuation. Its
[prepared isolated controller](runs/dex3_exact_optical_preparation_01/preparation.json)
and [initial rendering](runs/dex3_exact_optical_preparation_01/render_receipt.json)
are available; this preparation grants no robot handling qualification.
The subsequent [20 micrometre initial-gap proposal](analysis/optical_supported_staging_01/review.json)
was rejected before writing a replacement scene because native contact already
reported penetration at that pose. Resolving sample/tray startup contact remains
required before executing the new optical station under the operation bounds.
The [source-triangle diagnosis](analysis/optical_tray_clearance_01/review.json)
finds that the original centre-point height ignores the tray's sloped surface
under the specimen rim. The [new initial pose](analysis/optical_runtime_binding_11/binding.json)
aligns the copper back to the actual support triangle (1.343 degrees) and retains
a 20 micrometre clearance. Only this declared initial specimen pose changes;
the robot, tool, tray, other objects, contact settings and meshes remain exact.
Its [0.15-second startup check](analysis/optical_startup_screen_02/review.json)
passes the unchanged 20 micrometre operation bound with a 14.317 micrometre peak,
no optical-face contact and no external force. The full
[three-second support check](analysis/optical_runtime_support_11/review.json)
and [corrected-velocity replay](analysis/optical_support_velocity_recheck_11/review.json)
now pass with exact retained states. The 14.317 micrometre peak also satisfies
the unchanged stricter operation bound. The corrected
[operation station](runs/dex3_optical_observe_start_03/review.json) and
[isolated controller preparation](runs/dex3_exact_optical_preparation_02/preparation.json)
are rendered, not executed. The specimen's declared initial placement does not
count as robot handling, and these checks do not establish final room acceptance.
The [corrected support replay](analysis/optical_support_velocity_recheck_01/review.json)
checks the specimen's own velocity address, which the original evaluator
accidentally replaced with the cap address. All retained states replay exactly
and the corrected stability check passes. New station preparation requires this
addendum for support reports from the affected evaluator.

Tool execution and independent physics replay now load hash-pinned stateless
collision plugins without exposing the loader or plant model to the actor.
`process_tool_grasp_plugins.py` invokes the frozen renderer or motor-limit
checker for those runs. Its legacy renderer/checker sources remain unchanged.
The [native compatibility check](analysis/frozen_collision_plugin_runtime_01/review.json)
reproduces all states, accelerations, contacts and forces exactly over ten steps
in the actual five-plugin laboratory and rejects four altered-receipt cases.
This verifies the loading path, not a robot episode. Scene preparation and
rendering now use the frozen plugin wrapper and retain the corrected support
review in the run contract.

Candidate 07 tests compensation of the four non-closing finger joints using
their own filtered motor/inverse-dynamics residuals. Closing joints retain
their force servo. Optional body joint boundary damping adds acceleration
constraints to the balance QP; it does not modify physical joint limits.
The preload observer now requires 0.75 s before lift when selected; native
contact acceptance remains 0.5 s. These are controller hypotheses under test,
with unchanged source geometry, physics timestep, friction, actuator bounds
and independent acceptance. See `--carry-finger-load-compensation`,
`--carry-body-joint-damper` and `--carry-prelift-dwell` in `run_tool_grasp.py`.

The separate [99.66-second visual pickup](runs/dex3_visual_grasp_03/physical_review.json)
also passes its 18 independent physical checks, controller replay and source
motor limits. It uses the same authored initial scene as the shorter run;
these two executions are not randomized repeated-reliability acceptance.

The contact plant now also runs in the existing complete laboratory. The
[laboratory runtime](LABORATORY.md) imports the original room, furniture and
equipment, with G1 and the white tray as dynamic bodies. A separate
[passive FTIR device candidate](FTIR_DEVICE.md) adds contact-driven cover and
key diagnostics in that laboratory. One G1 sliding-window operation now passes
independent contact replay and post-operation visual confirmation; full cover
opening, loaded walking and the full paper campaign remain open.
The [laboratory recording page](../../viewer/cooling_lab_runtime_v1/index.html)
shows the resulting contact subtask with enforced actor access isolation. The
runtime guide records the namespace probes and independent packet-rejection
check. A separate 12-second unloaded walking and stationary-control handoff
recording advances 1.96 m, with independent replay and contact checks. It is
not yet joined to the tray sequence. Sensor calibration and general localization
remain open. The earlier independent workbench tests
below remain unchanged as development evidence.

The current [continuous FTIR measurement film](../../viewer/cooling_concept_v2/measurement_demo.html)
shows 9 minutes 1 second of tool collection, walking to the material bench,
carrying the witness back, gold-reference/sample operations and cleanup in the
full laboratory. Its [delivery record](../../viewer/cooling_concept_v2/measurement_delivery.json)
distinguishes the geometric review from unfinished physical qualification.
The [5 minute 33 second edition](../../viewer/cooling_concept_v2/measurement_demo.html?cut=brief)
retains both walking legs and all operation stages, with a synchronized room
map. The separate [117 second window recording](runs/ftir_slider_07/slider.mp4)
shows a physically executed push, withdrawal, camera confirmation and return.
Its [physical review](runs/ftir_slider_07/physical_slider_review.json) and
[native-sensor replay](runs/ftir_slider_07/visual_outcome_review.json) pass.
That recording starts at an authored station pose; it does not validate the
cross-station film's carrying or complete measurement sequence.

The newer [233.6-second continuous approach recording](runs/ftir_approach_11/slider.mp4)
executes a 1.020 m local aisle approach, sensor-derived station handoff, tactile
window push, withdrawal and native RGB-D outcome confirmation in the original
laboratory. Its [independent physical review](runs/ftir_approach_11/physical_slider_review.json)
and [complete sensor/controller replay](runs/ftir_approach_11/continuous_approach_review.json)
pass: all 116,801 motor outputs and 2,337 retained camera frames were replayed;
the final physical opening is 70.999 mm. The earlier replay stopped on a missing
`rtree` dependency; its failed report is retained under
`replay_attempts/missing_rtree_01/`. The restored environment and corrected
full-output coverage check do not alter the frozen actor or physical trajectory.
This is one local approach and operation, with no carrying, complete branch or
reliability qualification. The recording and timestamp controls are on the
[laboratory recording page](../../viewer/cooling_lab_runtime_v1/index.html).

The earlier workbench presentation contains **80.54 seconds of one uninterrupted simulation**: a standing G1 picks up a tray containing a preloaded laboratory spatula, transports it across the bench, places and releases it, observes it again, picks it up again, returns it to the source and retracts its hands. The same floating robot and objects remain in the scene throughout. This is **one carrier transport subtask**, not the complete directional-cooling paper demo. There are still **0 of 11 qualified paper branches, 0 qualified skills and 0 qualified campaigns**. Parallel scene/controller development is authorized; asset acceptance remains pending.

Serve the repository with `python simulation/cooling_v1/serve.py --port 8769 --bind 127.0.0.1` (including video range requests) and open <http://localhost:8769/viewer/cooling_demo_v1/index.html>. This older workbench page presents the recording, contact close-up, synchronized native head depth, event timeline, measured trajectory and independent verification. Its manipulation world is a **local test bench**, not the complete laboratory collision scene. The room and equipment review is linked separately.

## Full-laboratory tool development

`carry_tool_actor.py` extends the visual pickup with a loaded arm withdrawal,
short out-and-back stepping route and return to the observed source tray.
The hand keeps its motor-load feedback during the motion. Support-foot
kinematics replace the fixed-feet estimate during stepping; no physical root
or tool pose is reassigned. The rigid grasp transform is a collision-planning
hypothesis, not a physical attachment or measured slip pose.

The first [withdrawal screen](analysis/dex3_carry_handoff_01/review.json)
fails reach. The [revised screen](analysis/dex3_carry_handoff_02/review.json)
uses the official elbow range and a 0.6 rad wrist rotation: 51 sampled raised
poses and 51 withdrawal poses pass the arm/tool geometry guard. This fixed-base
screen is not loaded walking. Before the new stage, 50,988 recorded sensor
responses remain exact; separate regressions retain all
[23,581 default pickup outputs](analysis/dex3_carry_hooks_baseline_01/review.json)
and [10,141 default walking outputs](analysis/dex3_walking_hooks_baseline_01/review.json).

`run_tool_grasp.py --carry-distance 0.12` selects the isolated carrying actor
for an observed-approach station. Its distinct task contract requires actual
loaded base travel, both feet stepping, retained grip, return and released
support, in addition to the original continuous physical checks. Read that
run's own result and independent review before claiming any carrying outcome.
`probe_tool_carry_checkpoint.py` separately diagnoses the new control stage
from an explicitly restored recorded grasp after replaying the actor's sensor
history. Those checkpoint probes cannot count as continuous pickup/carry demos.

The first [checkpoint continuation](analysis/dex3_carry_checkpoint_01/result.json)
loses the tool during rotated withdrawal after 11.309 seconds, before stepping.
Its [sparse wrench diagnosis](analysis/dex3_carry_checkpoint_01/contact_wrench_diagnosis.json)
finds a late optimistic static requirement near 1.94 N peak finger force,
above the roughly 1.13 N actual thumb load. Sparse reconstructed forces are not
continuous replay or calibrated hardware forces. The next candidate adds an
observed preload stage (`--carry-thumb-force 2.4`) and rejects withdrawn arm
endpoints within 0.08 rad of the IK bounds. This changes motor commands and
planning only; source geometry, friction, dynamics and the 4 N development
acceptance bound remain. `--prepare-only` freezes an isolated candidate without
executing it, for checkpoint diagnostics before a new full continuous trial.

`build_tool_station.py` places the free passive tweezer and ordinary free tray
in the existing room with the complete G1. `runs/tool_station_04/review.json`
passes initial geometry, source inertia/contact preservation, actual bench
height, tray footprint and whole-robot collision checks. This is authored
initial staging; there is no robot placement or grasp credit. The original
optical attachment remains on the bench. The first proposed placement collided
with it; the corrected staging translates the robot/tool/tray by 0.35 m and
0.03 m in laboratory coordinates. Initial images are in that station folder.

`runs/tool_station_05` preserves this geometry while splitting the static room
architecture into smaller bodies for collision broad-phase rejection. The
bounded `analysis/tool_collision_partition_01` comparison retained identical
100-step zero-torque states and reduced measured runtime from 5.43 to 0.84 s.
A broader partition attempt ran out of collision-stack memory; a spatially
grouped variant changed the sampled trajectory. Those alternatives are retained
and are not the selected execution model. The short comparison does not qualify
standing, manipulation or a complete trajectory.

`run_tool_grasp.py` and `tool_grasp_actor.py` execute an isolated full-body
attempt from the declared pregrasp. Own-robot encoders and IMU feed a full-body
load predictor; arm motion compensates the change in the source pad midpoint
as the fingers close. Observed sustained opposing load gates a lift, hold,
lower and release attempt. The actor has no visual tool localization or
executed approach. `verify_tool_grasp.py` separately replays the frozen actor,
physics and native sensors and checks actual loaded lift, contact, tool closure
and released support. Read each attempt's result and review; no tool grasp,
paper branch or repeated-reliability qualification has been established.

The slow `runs/tool_grasp_01` baseline was explicitly interrupted after the
first 174 recorded monitor rows matched `tool_grasp_02` exactly through 1.73 s.
Its interruption record and partial monitor remain; its full in-memory trace
was not saved. `tool_grasp_02` is the separate attempt on the partitioned room,
not a continuation spliced onto that baseline.

`tool_grasp_02` ended after 13.955 simulated seconds with loss of opposing
finger load. Frozen controller replay and continuous physics/native-sensor
replay are exact, but the physical verdict fails: only 0.346 seconds of
bilateral contact, no held lift, and an initial sole-contact excursion beyond
the 1 mm bound. Recorded contacts lie on the finger housings, with an axial
separation of about 12.7 mm; the tool rotates and falls into the tray. See its
`final_review_summary.json`, contact diagnosis and recorded stills. An exact
replay of that failure is not a successful grasp.

### Official three-finger candidate

`fit_dex3_tweezer.py` uses the already pinned official Unitree three-finger
resource in `analysis/g1_dex3_comparison_01`. It fits original source exterior
points and checks the actual supported tool mesh, tray and bench plane.
`dex3_tweezer_fit_01` has no accepted placement; its palm lies below the tool.
Reversing the tool-axis orientation yields 23 local candidates in `_02`.
They are geometric proposals, not executed grasps.

The source visual mesh has a palm/thumb-1 assembly overlap throughout the
221 configurations in `dex3_thumb_interference_01`. It is disclosed rather
than removed. A separate issue in the earlier static-root inspection caused
extra native collision reports. The new `hand_self_check.xml` adds only a
free wrist, preserving the source collision geometry and dynamic parent
filtering. Native collision checks use the manufacturer's collision shapes;
original visual triangles still check external tool and tray intersections.

`build_dex3_tool_station.py` replaces the two official wrist/hand subtrees,
retaining the complete room, other body inertias, free tray and passive tool.
The model has 43 independent motors. The first three station searches fail
reach or collision checks. Rotating the authored tray/tool arrangement by
180 degrees produces five full-body static candidates in
`runs/dex3_tool_station_04`. This is a different initial arrangement, with
no executed rearrangement credit. `dex3_pregrasp_01` opens the chosen hand
before contact and passes initial bounds with no robot/tool contact; its
overview and contact images show the actual original laboratory.

`dex3_tool_grasp_01` fails after 0.129 seconds: gains transferred from the
previous hand cause severe finger oscillation and excessive contact. Its
controller and physical replay reproduce that failure. The subsequent actor
bounds proportional and damping gains using the robot-only coupled hand
inertia and the control period, without changing the plant's mass or armature.
Read the later attempt's own result and independent review before assigning
any execution outcome. This pickup test does not qualify squeezing the tool
on a specimen, perception, approach, carrying, a paper branch or reliability.

`dex3_tool_grasp_02` ends after 14.005 seconds without enough sustained load
to lift. Controller, physics and native sensor replay are exact. Contact and
released-support bounds pass, but the physical verdict fails, including a
3.635 mrad thumb distal-joint excursion beyond its source limit. Its separate
torque/speed check passes; that check does not cover position limits. The
verifier's write-time source-hash issue is documented and reconciled in
`verifier_runtime_provenance.json`, preserving the original report and every
physical metric. Future verifiers capture their hash at import and run from
a frozen source copy.

`dex3_tool_grasp_03` reaches the lift phase but loses the tool. The 16.993-second
attempt and exact-byte trace chunks are retained. Sparse wrench diagnostics
show marginal grip support during lift and infeasible static equilibrium at
the late slipped contact configuration; they are not continuous verification.
The full independent verdict must be read separately. A 4.730 mrad thumb
distal-joint excursion also excludes qualification.

The next setup, `dex3_tool_station_05` / `dex3_pregrasp_03`, selects a source
grasp with the thumb distal joint farther inside its limit, and restricts
authored elbow flexion to at least 0.15 rad inside the original source range.
One of 125 searched poses passes the initial scene checks. The new force
targets are explicit actor-prior inputs and pinned in each run contract;
the physical acceptance limits remain unchanged. Initial setup and controller
changes do not establish grasp success.

`analysis/dex3_device_sleep_02` tests native sleeping only for the unattended
instrument cover; the robot, tool, tray and instrument keys are never allowed
to sleep. A 0.2-second replay preserves all robot/tool/tray states bit for bit
and reduces measured wall time from 12.70 to 6.00 seconds. The separate
`dex3_cover_wake_02` diagnostic drops a free 20 g sphere onto the actual cover:
the sleeping cover wakes on contact, with a maximum 3.2 nm position difference
from the unslept baseline. This added sphere exists only in diagnostic files.
`dex3_pregrasp_04` binds the tested sleep configuration to the next authored
initial scene. Complete execution and independent replay remain required;
the short comparison does not qualify a grasp or a whole-device interaction.

`dex3_tool_grasp_04` and `_05` both lift the tool but fail the independent
released-support condition because a finger retains contact. The paired
sleeping/unslept full trajectories differ; the short sleeping diagnostic is
not a claim of identical full-run behavior. Each run's own physics replay is
exact. `_06` adds bounded extra finger opening, an encoder-derived residual-load
release gate and a 20 mm wrist withdrawal. All sixteen independent physical
checks pass, including actual held lift, released support, source joint limits
and bounded contact. Its frozen execution result remains the original
pre-evaluation record; the separate reviews contain the subsequent verdict.
No earlier failed trace or verdict is overwritten.

### Observation and approach integration

The next actor, `visual_tool_actor.py`, starts with its right arm parked clear
of the tool. Native head RGB-D, own encoders/IMU, unposed tool CAD and a
tool-local hand preshape supply localization and arm planning. Tool placement,
scene contact lists and earlier arm paths are excluded from the actor bundle.
The wrist/finger controller remains motor-driven with independent evaluation.

`analysis/dex3_observed_approach_01_evaluation` rejects the first geometric
proposal: the old source-mesh reader omitted the official hand's visual group 1.
The planner now explicitly includes both source visual groups and requires the
complete right hand and wrist. Further candidates retain failures caused by
surface clearance. Native depth now disables MSAA using the existing camera
helper, and planning uses connected depth-pixel surfaces rather than 2 mm
voxel boxes. No physical acceptance tolerance is relaxed.
`dex3_observed_approach_04_evaluation` passes 647 full-scene kinematic samples;
its one-pose tool estimate differs from evaluator truth by 0.220 mm and
0.060 degrees. These are development observations, not perception robustness
or controlled-motion qualification.

`runs/dex3_visual_grasp_01` ends at 3.2 seconds without moving toward the tool:
after settling, the proposed raised approach cannot satisfy its IK tolerance.
All 3,201 sensor/controller packets and 17 native RGB-D frames replay exactly;
the physical result remains a failed pickup with no held lift. The bounded
planner now tries several approach heights under the same source limits and
clearance checks. `dex3_visual_plan_diagnosis_02` finds a 30 mm raised route
from those same recorded inputs; that diagnostic does not execute the route.
Read each new continuous attempt's own independent reviews before claiming
visual approach, pickup or a complete experiment.

`dex3_visual_grasp_02` executes part of the approach, then holds a waypoint:
its wrist error settles to 0.056 mm while the joint-angle progress gate never
advances for four recorded seconds. A deliberate SIGINT at 17.5125 s preserves
the partial trajectory and the stagnation evidence. Motor limits pass; this
interruption is not a successful approach. The next actor gates progress using
wrist position/orientation feedback and checks the instantaneous observed right
arm against the current robot body and sensed environment. This arm guard does
not certify other-body self-contact or support; full-plant evaluation remains
required. Each earlier actor and its original gate remain frozen in its run.

## Reproduce

Use Python 3.11+, EGL-capable OpenGL and `requirements.txt`. Current sensor runs also require Linux with bubblewrap and enabled unprivileged namespaces; see [the runtime guide](LABORATORY.md). The workstation environment is `/tmp/sciencegym-sim-venv/bin/python`. Run from the repository root, choosing a new directory so evidence is not overwritten:

```sh
export OPENBLAS_NUM_THREADS=1
export MUJOCO_GL=egl
python simulation/g1_cooling_demo/run.py --out /tmp/g1-continuous-new --duration 100 --tray --closed-loop --return-to-source --com-align --payload --payload-kind spatula --grip-force 15
python simulation/g1_cooling_demo/verify_transport.py /tmp/g1-continuous-new
python simulation/g1_cooling_demo/render_continuous.py /tmp/g1-continuous-new --movie
python simulation/g1_cooling_demo/render_depth.py /tmp/g1-continuous-new
```

The selected episode is `runs/continuous_tool_transport/`. Inspect both `result.json` and `transport_verification.json`; completion is not qualification. Models in this selected directory reference repository-relative paths. Recorded source snapshots identify the exact run version; execute the current tools from the repository, not snapshots in isolation. A metadata-only defect reported an 18 N grip default instead of the 15 N actually passed to the actor; `metadata_correction.json` documents the source lines and original result hash. The original result remains intact. The current writer is fixed.

The previous 38-second initial-localization/timed-trajectory episode remains unchanged in `runs/delivery/` and can be reproduced with `--duration 38 --tray --sensor-actor`, followed by `verify.py` and `render.py --movie`.

## Robot, perception and control

The source-derived Unitree G1 29DoF rev1.0 / Inspire FTP model retains its 41 motors, hand mimic constraints, floating base and original hand collision components. Ordinary ground contact supports the robot. No root actuator, base weld, applied body support force, object reset or invisible grasp is used after initialization. Grip forces are converted to joint motor torques. This is a palm-contact grip; a dexterous finger-grasp policy has not been qualified.

A separate actor process receives only joint encoders, an idealized pelvis IMU, head depth and time. It estimates translation using fixed-foot kinematics. The depth tracker subtracts an estimated robot and known empty-bench background and observes a single carrier in a known workspace. It receives no object poses, segmentation, contact enumeration or evaluator predicates. These fixed-foot/background assumptions, camera calibration and process security are not qualified for a general laboratory.

The author-defined transport policy follows approach, grip, lift, transfer, place, release and retraction stages. Fresh depth observations gate lift confirmation, destination confirmation, placement and release before progression. After placement it estimates the carrier again for the return. Smooth COM alignment supports the off-center second grasp. The final retracted hand targets remain active for an eight-second stability hold. A failed visual gate terminates the episode; **safe recovery is not implemented**. No claim of autonomous paper-to-policy synthesis is made.

## Objects and assumptions

The tray is the existing Bürkle 4208-0022 reconstruction, 300 × 200 × 50 mm. Seeded CoACD decomposition approximates its hollow shell. The 1.2 mm sheet, steel density, inferred mass of approximately 0.951 kg, inertia, friction, compliance, approach offsets and stage times are engineering assumptions, not measured physical parameters.

The selected payload uses the existing Bürkle 5386-0041 spatula reconstruction, 150 × 9 × 3.5 mm. Mesh volume and assumed steel density produce approximately **9.3 g**. Its single convex collision approximation is unqualified. It starts inside the tray, so this episode earns **no robot loading credit**. The separate approximately 0.806 kg copper-stock trials failed; the spatula episode does not validate heavy carrying. Load compensation in copper trials changes commanded joint torques only and adds no physical support force.

## Evidence and limits

`trace.npz` records positions, velocities, motor commands and solver warm starts at 100 Hz, with 500 Hz physics. `sensor_observations.npz` records actor proprioception. `policy_observations.json` and result events retain the depth-based stage decisions. Head depth is recorded at 10 Hz as lossless float32 byte-plane chunks, with bitwise round-trip checks and per-chunk hashes.

`verify_transport.py` independently checks actual lifts, displacement, return accuracy, stable table placement, hand release, payload retention, fresh observed transition evidence and source hashes. It continuously replays recorded motor torques from the initial state without state correction and compares the physics trajectory. Rendering displays those recorded states at 1×, without scene resets or manufactured outcomes. `model_inputs.json` and `manifest.json` pin the selected episode's dependencies and outputs.

`extended_attempts.json` indexes all second-hour development attempts, including a model setup failure, grasp failures, heavy payload failures and failures after transport during parking. `attempts_extended/` retains their available models, snapshots, traces, sensor observations and depth. Legacy depth arrays are losslessly repacked, preserving their original SHA in encoding receipts. These changing controller versions must not be pooled into an acceptance success rate. Original diagnostic model paths can reference the workstation; the selected episode is the portable replay artifact. `attempt_archives/` and `attempts.json` retain the earlier sprint's records.

Full-demo work still includes accepted assets and room clearances, full laboratory dynamics, loaded carrying and walking, assembly, connectors, thin films, configuration changes, recovery and cleanup across all 11 paper branches. The contract requires at least 19/20 for skills, 9/10 per branch and three complete campaigns. These are not yet achieved. No hardware run or scientific-result reproduction is claimed.

The [release compensation diagnostic](analysis/dex3_release_decay_evaluation_01/review.json)
replays 134,131 original controller packets exactly, then decays the previous
own non-closing-joint compensation over 100 ms. In its 2.5 s restored window,
thumb distal peak speed is 0.690 rad/s versus the original 12.408 rad/s. All
seven hand source limits pass in that window, but the diagnostic fails exact
restored-state and pre-release equivalence because the compact state did not
preserve native sleep history. It therefore supplies a development lead, not
a carrying pass. A separate candidate stops lowering 4 mm above the original
wrist reference to address finger/tray contact; passive support, release and
all source/contact bounds remain independently required.

The first [3 N ramped beam-grasp diagnostic](analysis/dex3_tool_force_ramp_evaluation_01/review.json)
replays 49,988 prior controller responses exactly and reaches a 0.0154 mm tip
gap during squeezing. It nevertheless fails retained closure and reopening:
tool/wrist translation reaches 13.36 mm during squeezing and 29.69 mm overall,
and the own-contact-feature closing lever becomes invalid during reopening.
No force-bound relaxation is used. The next supported-preshape candidate applies
-0.04 rad proximal adjustment and a 0.25 rad reference envelope while the tray
still supports the tool, before the same 3 N/two-second stroke ramp.

The completed [native heel-stroke review](analysis/dex3_heel_tool_stroke_evaluation_03/review.json)
replays the original initial-state prefix and tool window with zero qpos/qvel
error. It fails completion, closure, reopening and absence of external tool
support. Peak finger force is 2.600 N; the earlier proxy protection event is not
proof of a 4 N physical finger-force violation. Full-run contact and controller
reviews also remain separate from this stroke check.

The [4 mm height-only release diagnostic](analysis/dex3_release_clearance_checkpoint_02/result.json)
finishes its control sequence but still fails the original 20 micrometre
hand/tray penetration bound, reaching 123.8 micrometres. A [recorded-contact
Jacobian diagnosis](analysis/dex3_carry_release_contact_direction_08/review.json)
identifies the index distal link against the tray's sloped rim; its separation
normal has substantial horizontal components. The next authored lowering
candidate adds +3/-3 mm world XY correction while retaining the 4 mm height
and 100 ms compensation decay. It is a diagnostic hypothesis, not executed
cross-station manipulation or accepted release.

The current WIP publication includes the carry06/carry07/heel02 preview movies,
frozen inputs, source snapshots and available reviews. Their raw full-run
sensor, controller and physics arrays remain local pending separate publication;
see each run's `publication_status.json`. This is not a complete downloadable
execution bundle or a final demo delivery. The diagnostic windows published
alongside them remain explicitly separate from fresh continuous execution.
