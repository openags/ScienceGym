# From this paper to robot experimental work

## Manipulation scope and starting state

The paper demonstrates solar-white and solar-black cooling devices using a
small reflector to block direct sunlight while retaining a view of the sky.
The robot task reconstructs the physical handling needed for fabrication, coating and assembly,
thermocouple calibration, optical characterization, outdoor environmental
measurement, paired stagnation and cooling-power measurements, a fixed-band/LDPE
variant, and thermal maps in three conditions. All eleven physical families are
retained as manipulation contexts. Instrument-internal processes and scientific
outputs are environment context; reproducing the reported cooling performance
is not the robot task's success criterion. Energy-balance models, COMSOL results and application concepts are
classified separately in `coverage_matrix.json` and `nonmanual_scope.json`.

Start with identified stock, instruments, tools and supported carriers. A disk,
film or finished assembly does not appear because a fabrication service returned
an evidence category. The reconstructed operator clamps and cuts stock, finishes
edges, inspects dimensions, labels parts, carries them, coats the disks, installs
the layers and connects the instruments. Device-owned cutting, scanning, heating
and logging are distinguished from robot manipulation in every reference step.

## Source, inference and operating inputs

The eight-page article and 25-page supplement were retrieved and inspected,
including all 13 figures. `source_inventory.json` gives exact URLs, content hashes
when bytes were obtained, actual review scope and missing raw data. Evidence IDs
point into those sources. Manufacturer instructions supplement omitted operating
details: for example, configure the USB-TC for K-type probes and satisfy its
30-minute warm-up requirement rather than retaining its J-type default.

Every newly reconstructed handling action is marked as an inference with a
physical rationale, alternatives and a validation obligation. Source-reported
dimensions and durations remain separate. The source's 100 mm schematic height
and approximately 150 mm textual height are not silently reconciled: the current
geometry chooses the textual emitter-to-reflector datum and retains the conflict.
Tool settings, tolerances, coating cure, PID gains and targets, robot kinematics,
weather eligibility and exact sample allocation are explicit episode inputs.
`selected_reconstruction.json` supplies 109 concrete selections across all 14
cards, including a rationale and source/inference distinction for every field.
`episode_inputs.py` checks and loads these simulation inputs. An inferred value
does not have to remain null merely because the paper omitted it. A selected
value is still distinct from a measured property or a successful execution.

Inferring an action is different from inventing a historical number. For example,
the reconstruction includes applying each of three paint coats and waiting for
intercoat and final cure conditions, but does not claim an unreported drying time.
The selected simulation uses an explicit virtual process timing; it does not
claim that this was the historical drying time or a qualified hardware recipe.

## Planning method

Work backward from each required physical result to the objects, states and
measurements that can produce it. Add preparation and cleanup producers, join
shared prerequisites, and keep alternatives and repetitions explicit. The graph
is a partial order; the included route is one inspectable reconstruction, not the
only permitted policy. Definition dependencies are in `dependencies.json` and
the concrete walkthrough is in `reference_plan.json`.

| Phase | Physical work and required connection |
| --- | --- |
| Preparation | Bind specimens, stock lots, session conditions, instruments, fixtures and missing inputs. Compute site/date-dependent track geometry before cutting it. |
| Fabrication | Clamp and cut copper, aluminum, PE, foam and acrylic; deburr, inspect and retain offcuts. Load, operate and unload the water-jet machine explicitly. |
| Coating | Mask and support each identified disk; prepare the can; apply and wait through three coat iterations; cure, inspect and unload. White and black identities remain distinct. |
| Assembly | Install base and frame, two foam disks, emitter, PE support, two film layers and spacer, shield, aperture plate and reflector track. Inspect actual component identities, layer count, clearance and attachment. |
| Calibration | Mount the bath copper block, reference RTD and K probes; connect DMM and USB-TC; configure/warm up; sweep supplied setpoints; fit individual corrections; unload, dry, attach and inspect. |
| Hemispherical spectra | Select direct samples or explicitly inferred matched-lot witnesses. Use compatible holders in Cary 5000/DRA-2500 and Nicolet 6700/IntegratIR, acquire references, mount, scan and unload every allocated material. |
| Angular spectra | Mount the 12-degree or variable-angle accessory; bind each angle and s/p polarization; reacquire a configuration-compatible reference; scan white/black specimens and preserve repeats. |
| Tracked stagnation | Carry the paired devices outdoors; install independent environment instruments; synchronize; retain PE films while removing metal lids after the five-minute baseline; adjust the reflector during the observation interval. |
| Cooling power | Return supported devices for isolated heater attachment and four-wire connections; re-inspect; operate independent white/black feedback loops; use 300-second plateaus and the final 120 seconds for the specified summary; verify outputs off. |
| Fixed band and LDPE | Verify heater outputs off; support the emitter and remove the heater before reusing the unheated configuration. Inspect probe/backside/insulation. Remove disk/track and nanoporous covers; install the band and two LDPE layers; increment configuration revision and inspect before another eligible outdoor session. |
| Thermal mapping | Restore the tracked configuration if the same white device is reused; attach six extra probes at declared surfaces; re-inspect; record seven channels for one hour in each of clear day, clear night and hazy noon conditions. |
| Closeout | Verify outputs stopped, support before disconnecting and releasing, transport to named storage, retain failed/partial attempts and raw-data parents, reconcile inventory and report every selected obligation. |

The optical witness route is a design hypothesis. A 127 mm cover ring is not
assumed to fit every spectrometer holder. Witness size, film spacing and batch
equivalence must be checked against the actual accessory; an appropriate direct
component fixture is an alternative. White/black witnesses are not whole cooling
assemblies teleported into an optical compartment.

## Repetitions, state and observations

`planner.py` expands a **software test fixture** into occurrences. The fixture's
three calibration setpoints, three PID targets, one technical repeat and two
tracking obligations are intentionally synthetic and not execution defaults.
The paper supplies three paint coats, seven displayed incidence angles with s/p
measurements, five-minute power plateaus, last-two-minute averaging, five-minute
weather sampling and three one-hour map conditions. Other acquisition cadences
must not inherit the weather cadence accidentally. The five-minute lid baseline
is source-supported for tracked stagnation; applying that timing to other branches
is explicitly a test-fixture inference. Total acquisition windows include any
baseline interval; the one-hour mapping window is not silently extended by five
minutes. The plan is an obligation expansion, not a wall-clock controller schedule.

Each occurrence carries an operation ID, branch, session, payload identities,
station, required step observations and loop bindings. Station changes insert
explicit supported transport. Object revisions invalidate assembly inspection
after film, reflector, heater or probe changes. Acquisition requires a current
inspection and calibration. Optical references bind the installed accessory and
configuration. Raw measurements must later bind actual files, timestamps, units,
instrument settings, calibrations, sample revisions and processing parents.

`solar_geometry.py` computes reflector-plane intersections from supplied
solar azimuth/elevation samples and checks finite-aperture shading against a sampled
solar disk. It catches insufficient reflector margin at low sun angles. It does not
generate an ephemeris. `selected_solar_path.py` supplies NREL SPA positions for the
explicitly selected Cambridge summer scenario, generates 241 one-minute track
commands, and checks the held positions and fixed-band envelope at one-second
intervals. This replaces an illustrative curve with a numerical design input;
mount occlusion, physical carriage motion and wind remain separate checks.

The symbolic replay checks selected invariants only. It does not observe the
world or infer that a grasp worked from a command. Planned events have empty
attempt lists and cannot establish physical success. Collision, reachability,
deformable-film handling and tool/fixture micro-transfers require implementation
against an actual robot and station configuration.

Recovery preserves failed attempts and last observed physical states. Torn film
requires supported replacement and new inspection; changed optical accessories
require new references; unknown heater state requires verified output-off before
transport. Missing or invalid data remains missing, rather than being filled with
paper results. A scientifically negative observation can be procedurally valid.

## Storage, processing and review boundary

`package.json` maps all 18 required artifact roles. Generated JSON is the portable
interchange contract; Python retains its authored decomposition, planner and
checks. `revision_origin.json` hashes the inherited v2 inputs. Native `.blend`,
`.glb`, part records, dimensions, research records and PNG inspection views live
in `assets/cooling_scene_assets_v2`. No proprietary vendor mesh or manual is
redistributed. Existing frozen explorer exports remain on v2 until a separately
tested adapter is ready; this is the same DOI and paper family.

The actor projection exposes selected goals, inventory, qualified inputs, current
observations and interfaces through an explicit allowlist. Reference routes,
future records, source outcomes and evaluator state are excluded. The reference
review package itself is trusted material, not an actor-safe export.

The eight conversion gates are recorded individually in `review.json`. They
remain partial where commercial geometry, action interfaces or physical checks
are missing. Passing static tests does not turn this pilot into a whole-paper
robot experiment or authorize treating the remaining papers as validated.

## Manipulation-focused revision, October 17

The intended product is the complete experiment task chain with its physical
manipulation work expanded. Scientific purpose, condition selection, perception,
waits and instrument processing remain in that chain. Numerical agreement with
the paper is not a prerequisite for accepting a manipulation task design; actual
scientific results require separately acquired observations.

Every manual step now names its target role, contact region, tool, support
transition, constraints, completion evidence and recovery. These are authored
interface specifications, not measured grasp poses. `interaction_contracts.json`
enumerates concrete geometry variants and missing parts, and
`manipulation_coverage.json` joins source obligations, all eleven branch routes,
operations and step definitions. The generated `MANIPULATION_REVIEW.md` is the
complete readable dossier. Parameter cards must bind actual instance identities
and qualify force, clearance, material/fixture and observation conditions.

The calibration block has an explicit drilling/finishing/inspection producer.
The bath is loaded and filled with displacement and drain closure checked.
Fine-wire compatibility is not assumed: Omega's 36 AWG probe leads fall outside
the USB-TC terminal's 16-30 AWG specification. A selected K-compatible transition
and independently retained extension must be qualified and included in the
calibration path. The numbered terminal map includes the reversed spatial pin
ordering on channels 4-7; geometric pitch remains inferred.

Angular incidence and polarization are set before the reference. The sample and
reference are exchanged through retained supports; scan only reads back the
accepted configuration. Changing either setting requires a fresh reference.
Opening the apparatus for probe/heater work explicitly retains the reflector,
aperture plate, shield and two-film cover before accessing the emitter. Changed
assemblies need a new inspection. SI Figure5's two near-axis insulation points
are treated as internal/layer-interface locations, with explicitly inferred
probe recesses and their additional thermal-path effects. Four further points
bind PE walls, shield and upper aperture plate. Display contact markers do not
qualify these recesses, attachments or physical access.

Source trace and design consistency, geometry fidelity, robot execution and
scientific reproduction have separate acceptance meanings. The remaining
fixture/tool and device-interface gaps keep this revision unaccepted as the
reusable manipulation template. A missing controller alone is not a reason to
hide a reconstructed physical operation behind a closed service.
